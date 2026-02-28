"""
Structural Analyzer Module
Orchestrates document parsing, inter-block context enrichment, and rule application.
This is the central component for structure-aware analysis.
"""
import logging
import time
from typing import List, Dict, Any, Optional

from structural_parsing.parser_factory import StructuralParserFactory
from .block_processors import BlockProcessor
from .analysis_modes import AnalysisModeExecutor
from .base_types import AnalysisMode, create_analysis_result, create_error

from rules import get_registry

logger = logging.getLogger(__name__)

# Progress message constants to avoid duplication (Sonar S1192)
PROGRESS_MSG_CALCULATING_METRICS = 'Calculating metrics...'
PROGRESS_MSG_FINALIZING = 'Finalizing results...'

class StructuralAnalyzer:
    """
    Analyzes document content with full awareness of its structure,
    preventing structure-based false positives.
    Enhanced with validation pipeline integration for improved error quality.
    """
    def __init__(self, readability_analyzer, sentence_analyzer, 
                 statistics_calculator, suggestion_generator, 
                 rules_registry, nlp, enable_enhanced_validation: bool = True,
                 confidence_threshold: float = None):
        """Initializes the analyzer with all necessary components."""
        self.parser_factory = StructuralParserFactory()
        self.nlp = nlp
        self.statistics_calculator = statistics_calculator
        self.suggestion_generator = suggestion_generator
        
        # Enhanced validation configuration
        self.enable_enhanced_validation = False
        self.confidence_threshold = confidence_threshold
        
        # Initialize components (extracted to reduce cognitive complexity - Sonar S3776)
        self._initialize_rules_registry(rules_registry, confidence_threshold)
        
        self._initialize_validation_tracking()
        
        self._initialize_context_router()
        
        self.mode_executor = AnalysisModeExecutor(
            readability_analyzer,
            sentence_analyzer,
            self.rules_registry,
            nlp
        )
        

    def _initialize_rules_registry(self, rules_registry, confidence_threshold):
        """Initialize enhanced or standard rules registry."""
        if self.enable_enhanced_validation:
            try:
                self.rules_registry = get_registry(confidence_threshold=confidence_threshold)
                logger.info("✅ Enhanced validation enabled for StructuralAnalyzer")
            except Exception as e:
                logger.warning(f"Failed to initialize enhanced registry, falling back to standard: {e}")
                self.rules_registry = rules_registry
                self.enable_enhanced_validation = False
        else:
            self.rules_registry = rules_registry
            logger.info("ℹ️ Using standard validation for StructuralAnalyzer")

    def _initialize_validation_tracking(self):
        """Initialize validation performance tracking."""
        self.validation_performance = {
            'total_validations': 0,
            'validation_time': 0.0,
            'errors_filtered': 0,
            'confidence_stats': {'min': 1.0, 'max': 0.0, 'avg': 0.0}
        }

    def _initialize_context_router(self):
        """Initialize context router for content-type-aware validation."""
        self.context_router = None

    def analyze_with_blocks(self, text: str, format_hint: str, analysis_mode: AnalysisMode, content_type: str = None, progress_callback=None) -> Dict[str, Any]:
        """
        Parses a document, enriches blocks with structural context, runs analysis,
        and returns a structured result for the UI.
        
        Args:
            text: The document text to analyze
            format_hint: Format hint for the parser
            analysis_mode: The analysis mode to use
            content_type: User-selected content type (concept/procedure/reference) from UI
            progress_callback: Optional callback(step, status, detail, percent) for progress updates
        """
        def emit(step, status, detail, percent):
            if progress_callback:
                try:
                    progress_callback(step, status, detail, percent)
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")
        # CRITICAL: Extract content type from file FIRST (file takes precedence)
        file_content_type = self._extract_content_type_from_file(text)
        final_content_type = file_content_type if file_content_type else content_type
        
        # Extract document attributes for context routing
        doc_attributes = self._extract_document_attributes(text)
        if final_content_type:
            doc_attributes['_mod-docs-content-type'] = final_content_type
        
        # Get validation context from context router (strictness, thresholds, skip_rules, etc.)
        validation_context = {}
        if self.context_router:
            try:
                validation_context = self.context_router.get_validation_context(doc_attributes)
                logger.debug(f"Context router returned validation context: {validation_context}")
            except Exception as e:
                logger.warning(f"Context router failed, using default context: {e}")
        
        emit('parsing', 'Parsing document...', 'Extracting content blocks', 20)
        parse_result = self.parser_factory.parse(text, format_hint=format_hint)

        if not parse_result.success or not parse_result.document:
            return {
                'analysis': create_analysis_result(
                    errors=[create_error('system', 'Failed to parse document structure.', [])],
                    suggestions=[], statistics={}, technical_metrics={}, overall_score=0,
                    analysis_mode='error', spacy_available=bool(self.nlp), modular_rules_available=bool(self.rules_registry)
                ),
                'structural_blocks': [],
                'has_structure': False
            }

        # Use a temporary BlockProcessor to get a flattened list without running analysis yet.
        # This is a key change to fix the race condition.
        temp_processor = BlockProcessor(None, analysis_mode)
        flat_blocks = self._flatten_tree_only(temp_processor, parse_result.document)

        # Compute document-level character positions for each block
        self._compute_block_positions(flat_blocks, text)

        # **Step 2: Add Inter-Block Context** to the flattened list.
        self._add_inter_block_context(flat_blocks)

        # **Step 3: Now, run the final, context-aware analysis on each block.**
        emit('spacy_rules', 'Checking style rules...', 'Running 82 deterministic rules', 30)
        all_errors = []
        validation_start_time = time.time()
        
        for block in flat_blocks:
            context = getattr(block, 'context_info', block.get_context_info())
            
            # CRITICAL: Always use final_content_type (file wins over user selection)
            # Override even if context has lowercase value (from user), unless uppercase (from file)
            existing_type = context.get('content_type')
            if final_content_type:
                if not existing_type or (isinstance(existing_type, str) and existing_type.islower()):
                    context['content_type'] = final_content_type
            
            # Merge validation context from context router (strictness, thresholds, skip_rules, domain)
            if validation_context:
                context['validation_profile'] = validation_context.get('profile', {})
                context['strictness'] = validation_context.get('strictness', 'medium')
                context['domain'] = validation_context.get('domain', 'general')
                context['is_release_notes'] = validation_context.get('is_release_notes', False)
                # Pass skip_rules for rules that should be skipped based on content type
                if validation_context.get('profile', {}).get('skip_rules'):
                    context['skip_rules'] = validation_context['profile']['skip_rules']
            
            if not block.should_skip_analysis():
                content, source_map = block.get_text_content_with_source_map()

                # DLIST blocks have special handling - bypass content check
                is_dlist = hasattr(block, 'block_type') and str(block.block_type).endswith('DLIST')
                if is_dlist or (isinstance(content, str) and content.strip()):
                    # CRITICAL FIX: Ensure table cell context includes proper position information
                    if hasattr(block, 'block_type') and str(block.block_type).endswith('TABLE_CELL'):
                        # Add table cell specific context information
                        if hasattr(block, 'attributes') and hasattr(block.attributes, 'named_attributes'):
                            cell_attrs = block.attributes.named_attributes
                            context['table_row_index'] = cell_attrs.get('row_index', 999)
                            context['cell_index'] = cell_attrs.get('cell_index', 0)
                            context['is_table_cell'] = True

                    # Enhanced: Track validation performance
                    block_start_time = time.time()
                    errors = self.mode_executor.analyze_block_content(block, content, analysis_mode, context)
                    block_validation_time = time.time() - block_start_time

                    # Enhanced: Update validation performance metrics
                    self._update_validation_performance(errors, block_validation_time)

                    # Filter out false positives caused by attribute replacement.
                    # {prod} → 'placeholder' during text cleaning; rules should not
                    # flag the synthetic word 'placeholder'.
                    errors = [
                        e for e in errors
                        if e.get('flagged_text', '').strip().lower() != 'placeholder'
                    ]

                    # Convert cleaned-text spans to raw-text spans using source map
                    if source_map:
                        for error in errors:
                            if 'span' in error:
                                s, e = error['span']
                                if s < len(source_map) and e > 0:
                                    raw_s = source_map[s]
                                    raw_e = source_map[min(e - 1, len(source_map) - 1)] + 1
                                    error['raw_span'] = [raw_s, raw_e]

                    # Suppress overlapping errors: when two rules flag
                    # overlapping text, keep the higher-priority one.
                    errors = self._suppress_overlapping_errors(errors)

                    block._analysis_errors = errors
                    all_errors.extend(errors)

            # **NEW**: For table blocks, recursively analyze nested content (cells, lists, notes, etc.)
            # This ensures nested blocks are analyzed but not flattened as separate blocks
            if hasattr(block, 'block_type') and str(block.block_type).endswith('TABLE'):
                nested_errors = self._analyze_table_nested_content(block, analysis_mode)
                all_errors.extend(nested_errors)

        # Track total validation time
        total_validation_time = time.time() - validation_start_time
        self.validation_performance['validation_time'] += total_validation_time

        # **Step 4: Calculate statistics and technical metrics from the original text**
        emit('metrics_start', PROGRESS_MSG_CALCULATING_METRICS, 'Preparing text analysis', 85)
        sentences = self._split_sentences(text)
        paragraphs = self.statistics_calculator.split_paragraphs_safe(text)

        # Split metrics calculation into chunks with progress updates
        emit('metrics_statistics', PROGRESS_MSG_CALCULATING_METRICS, 'Computing document statistics', 87)
        statistics = self.statistics_calculator.calculate_comprehensive_statistics(
            text, sentences, paragraphs
        )

        emit('metrics_technical', PROGRESS_MSG_CALCULATING_METRICS, 'Analyzing readability scores', 90)
        technical_metrics = self.statistics_calculator.calculate_comprehensive_technical_metrics(
            text, sentences, all_errors
        )

        # Calculate engagement metrics using the AUTHORITATIVE MetricsCalculator
        emit('metrics_engagement', PROGRESS_MSG_CALCULATING_METRICS, 'Evaluating engagement factors', 93)
        engagement_metrics = self.statistics_calculator.calculate_engagement_metrics(text, statistics)
        
        # Add engagement metrics to technical_metrics for unified access
        technical_metrics['engagement_score'] = engagement_metrics.get('engagement_score', 0)
        technical_metrics['engagement_category'] = engagement_metrics.get('engagement_category', 'Unknown')
        technical_metrics['direct_address_percentage'] = engagement_metrics.get('direct_address_percentage', 0.0)
        technical_metrics['adverb_density'] = engagement_metrics.get('adverb_density', 0.0)
        technical_metrics['engagement_recommendations'] = engagement_metrics.get('recommendations', [])
        
        # Generate suggestions
        emit('metrics_finalizing', PROGRESS_MSG_FINALIZING, 'Generating recommendations', 96)
        suggestions = self.suggestion_generator.generate_suggestions(
            all_errors, statistics, technical_metrics
        )
        
        # Calculate overall score using AUTHORITATIVE MetricsCalculator
        overall_score = self._calculate_overall_score(
            all_errors, technical_metrics, statistics
        )
        
        emit('metrics_complete', 'Analysis complete!', 'Results ready', 98)

        structural_blocks_dict = [block.to_dict() for block in flat_blocks]

        # Collect code block ranges for frontend visual styling
        code_block_ranges = []
        for block in flat_blocks:
            block_type_str = str(getattr(block, 'block_type', '')).lower()
            if any(t in block_type_str for t in ['listing', 'literal', 'code_block', 'codeblock']):
                raw_len = len(block.raw_content or '') if hasattr(block, 'raw_content') else 0
                code_block_ranges.append({
                    'start_pos': getattr(block, 'start_pos', 0),
                    'end_pos': getattr(block, 'start_pos', 0) + raw_len
                })

        # Enhanced: Include validation statistics in the result
        analysis_result = create_analysis_result(
            errors=all_errors,
            suggestions=suggestions,
            statistics=statistics,
            technical_metrics=technical_metrics,
            overall_score=overall_score,
            analysis_mode=analysis_mode.value, 
            spacy_available=bool(self.nlp), 
            modular_rules_available=bool(self.rules_registry)
        )
        
        # Add unified metrics for consistent access (single source of truth)
        try:
            from pdf_reports.utils.metrics import MetricsCalculator
            analysis_result['unified_metrics'] = MetricsCalculator.get_unified_metrics({
                'statistics': statistics,
                'technical_writing_metrics': technical_metrics,
                'errors': all_errors
            })
            # Also add full engagement metrics object
            analysis_result['engagement_metrics'] = engagement_metrics
        except ImportError:
            logger.warning("MetricsCalculator not available for unified metrics")
            analysis_result['unified_metrics'] = None
            analysis_result['engagement_metrics'] = engagement_metrics
        
        # Enhanced: Add validation performance metrics
        if self.enable_enhanced_validation:
            analysis_result['validation_performance'] = self._get_validation_performance_summary()
            analysis_result['enhanced_validation_enabled'] = True
            analysis_result['confidence_threshold'] = self.confidence_threshold
            
            # Add enhanced error statistics
            enhanced_errors = [e for e in all_errors if self._is_enhanced_error(e)]
            analysis_result['enhanced_error_stats'] = {
                'total_errors': len(all_errors),
                'enhanced_errors': len(enhanced_errors),
                'enhancement_rate': len(enhanced_errors) / len(all_errors) if all_errors else 0.0
            }
        else:
            analysis_result['enhanced_validation_enabled'] = False
        
        # Add context router information to the result
        if validation_context:
            analysis_result['context_routing'] = {
                'content_type': validation_context.get('content_type'),
                'strictness': validation_context.get('strictness'),
                'domain': validation_context.get('domain'),
                'skip_rules': validation_context.get('profile', {}).get('skip_rules', [])
            }

        return {
            'analysis': analysis_result,
            'structural_blocks': structural_blocks_dict,
            'code_block_ranges': code_block_ranges,
            'has_structure': True
        }

    def _compute_block_positions(self, blocks, full_text):
        """Set start_pos for each block = character offset of raw_content in full_text."""
        if not full_text or not blocks:
            return

        line_offsets = self._build_line_offsets(full_text)
        last_pos = 0
        for block in blocks:
            last_pos = self._find_block_start_pos(block, full_text, line_offsets, last_pos)

    @staticmethod
    def _build_line_offsets(text):
        """Build a list mapping line index to character offset."""
        offsets = [0]
        for line in text.split('\n'):
            offsets.append(offsets[-1] + len(line) + 1)
        return offsets

    @staticmethod
    def _find_block_start_pos(block, full_text, line_offsets, last_pos):
        """Find and set the character start_pos for a single block. Returns updated last_pos."""
        raw = getattr(block, 'raw_content', '') or ''
        start_line = getattr(block, 'start_line', 0) or 0

        if not raw:
            block.start_pos = last_pos
            return last_pos

        first_line = raw.split('\n')[0]
        if not first_line:
            block.start_pos = last_pos
            return last_pos

        if start_line:
            line_idx = max(0, min(start_line - 1, len(line_offsets) - 1))
            line_start = line_offsets[line_idx]
            search_start = max(line_start, last_pos)
        else:
            # No line hint — search from last known position
            search_start = last_pos

        pos = full_text.find(first_line, search_start)
        if pos < 0 and start_line:
            pos = full_text.find(first_line, line_offsets[max(0, min(start_line - 1, len(line_offsets) - 1))])
        if pos < 0:
            pos = full_text.find(first_line)
        block.start_pos = pos if pos >= 0 else last_pos
        return block.start_pos

    _SEVERITY_RANK = {'high': 3, 'medium': 2, 'low': 1}

    @classmethod
    def _suppress_overlapping_errors(cls, errors):
        """Drop lower-priority errors whose spans overlap a higher-priority one.

        When two rules flag overlapping text (e.g. 'verbs' on "is supported"
        and 'global_audiences' on "not supported"), the user sees redundant
        cards for the same region.  Keep the higher-severity error; if tied,
        keep the more specific one (shorter span).
        """
        if len(errors) <= 1:
            return errors

        def _span(e):
            return tuple(e.get('span') or (0, 0))

        def _priority(e):
            sev = cls._SEVERITY_RANK.get(e.get('severity', 'low'), 1)
            s, end = _span(e)
            length = end - s
            # Higher severity first, then shorter span (more specific)
            return (-sev, length)

        # Sort so highest priority comes first
        ranked = sorted(enumerate(errors), key=lambda pair: _priority(pair[1]))

        kept_spans = []  # list of (start, end) for already-kept errors
        kept_indices = set()

        for idx, error in ranked:
            s, e = _span(error)
            if s == e == 0:
                # No span info — always keep
                kept_indices.add(idx)
                continue

            overlaps = False
            for ks, ke in kept_spans:
                if s < ke and e > ks:  # spans overlap
                    overlaps = True
                    break

            if not overlaps:
                kept_indices.add(idx)
                kept_spans.append((s, e))

        # Preserve original order
        return [e for i, e in enumerate(errors) if i in kept_indices]

    def _extract_content_type_from_file(self, text: str) -> Optional[str]:
        """Extract content type from file attribute (file takes precedence over user selection)."""
        import re
        
        match = re.search(r':_mod-docs-content-type:\s*(CONCEPT|PROCEDURE|REFERENCE|ASSEMBLY)', text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        
        match = re.search(r':_content-type:\s*(CONCEPT|PROCEDURE|REFERENCE|ASSEMBLY)', text, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        
        return None
    
    def _extract_document_attributes(self, text: str) -> Dict[str, str]:
        """
        Extract document attributes from AsciiDoc header for context routing.
        Returns a dictionary of attribute names to values.
        """
        import re
        
        attributes = {}
        
        # Extract title (first line starting with = )
        title_match = re.search(r'^=\s+(.+)$', text, re.MULTILINE)
        if title_match:
            attributes['title'] = title_match.group(1).strip()
        
        # Extract all AsciiDoc attributes in the header (format: :attribute-name: value)
        # Only look in the first 50 lines (document header area)
        header_lines = text.split('\n')[:50]
        header_text = '\n'.join(header_lines)
        
        attr_pattern = re.compile(r'^:([a-zA-Z_-]+):\s*(.*)$', re.MULTILINE)
        for match in attr_pattern.finditer(header_text):
            attr_name = match.group(1).strip()
            attr_value = match.group(2).strip()
            attributes[attr_name] = attr_value
        
        # Extract document ID from anchor format: [id="value"] or [[value]]
        id_match = re.search(r'^\[id=["\']([^"\']+)["\']\]', header_text, re.MULTILINE)
        if id_match:
            attributes['id'] = id_match.group(1).strip()
        else:
            # Also check for shorthand anchor format: [[anchor-id]]
            shorthand_match = re.search(r'^\[\[([^\]]+)\]\]', header_text, re.MULTILINE)
            if shorthand_match:
                attributes['id'] = shorthand_match.group(1).strip()
        
        return attributes
    
    def _flatten_tree_only(self, processor, root_node):
        """Uses the BlockProcessor's flattening logic without running analysis."""
        processor.flat_blocks = []
        processor._flatten_recursively(root_node)
        return processor.flat_blocks

    def _add_inter_block_context(self, flat_blocks: List[Any]):
        """
        Iterates through the flattened block list to add contextual information
        about neighboring blocks.
        
        Enhanced: Now also passes preceding_block_content to list blocks for 
        resource list detection (e.g., "For more information, see these resources:")
        """
        for i, current_block in enumerate(flat_blocks):
            context = current_block.get_context_info() if hasattr(current_block, 'get_context_info') else {}

            # Get preceding block info
            prev_block = flat_blocks[i - 1] if i > 0 else None
            prev_block_type = prev_block.block_type.value if prev_block and hasattr(prev_block, 'block_type') else None
            prev_block_content = ''
            if prev_block:
                prev_block_content = getattr(prev_block, 'content', '') or ''
                if not prev_block_content and hasattr(prev_block, 'get_text_content'):
                    prev_block_content = prev_block.get_text_content() or ''
            
            # Get next block info
            next_block = flat_blocks[i + 1] if (i + 1) < len(flat_blocks) else None
            next_block_type = next_block.block_type.value if next_block and hasattr(next_block, 'block_type') else None
            context['next_block_type'] = next_block_type

            is_list_intro = False
            if context.get('block_type') == 'paragraph' and getattr(current_block, 'content', '').strip().endswith(':'):
                if next_block_type in ['ulist', 'olist', 'dlist']:
                    is_list_intro = True
            
            context['is_list_introduction'] = is_list_intro
            
            # NEW: Add preceding block content to list blocks for resource list detection
            # This helps rules identify "see these additional resources:" lead-in patterns
            current_block_type = context.get('block_type', '')
            if current_block_type in ['ulist', 'olist', 'dlist', 'unordered_list_item', 'ordered_list_item']:
                context['preceding_block_content'] = prev_block_content
                context['preceding_block_type'] = prev_block_type
            
            current_block.context_info = context

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences safely."""
        try:
            if self.nlp:
                # Use the sentence analyzer from the mode executor
                from .sentence_analyzer import SentenceAnalyzer
                sentence_analyzer = SentenceAnalyzer()
                return sentence_analyzer.split_sentences_safe(text, self.nlp)
            else:
                # Ultimate fallback
                import re
                sentences = re.split(r'[.!?]+', text)
                return [s.strip() for s in sentences if s.strip()]
        except Exception as e:
            logger.error(f"Error splitting sentences: {e}")
            # Ultimate fallback
            import re
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]

    def _calculate_overall_score(self, errors: List[Dict[str, Any]], technical_metrics: Dict[str, Any], 
                               statistics: Dict[str, Any]) -> float:
        """
        Calculate overall style score using the AUTHORITATIVE MetricsCalculator.
        
        This method delegates to MetricsCalculator.calculate_overall_score() to ensure
        consistent scoring across the entire application (UI, PDF reports, database).
        """
        try:
            # Import the authoritative MetricsCalculator
            from pdf_reports.utils.metrics import MetricsCalculator
            
            # Build analysis_data structure expected by MetricsCalculator
            analysis_data = {
                'statistics': statistics,
                'technical_writing_metrics': technical_metrics,
                'errors': errors
            }
            
            # Use the authoritative scoring method
            return MetricsCalculator.calculate_overall_score(analysis_data)
            
        except ImportError:
            logger.warning("MetricsCalculator not available, using fallback scoring")
            # Fallback to simple scoring if import fails
            base_score = 85.0
            error_penalty = min(len(errors) * 5, 30)
            readability_score = technical_metrics.get('readability_score', 60.0)
            readability_penalty = (60 - readability_score) * 0.3 if readability_score < 60 else 0
            return max(0, min(100, base_score - error_penalty - readability_penalty))
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 50.0  # Safe default
    
    def _update_validation_performance(self, errors: List[Dict[str, Any]], validation_time: float):
        """Update validation performance metrics."""
        if not self.enable_enhanced_validation:
            return
        
        self.validation_performance['total_validations'] += 1
        self.validation_performance['validation_time'] += validation_time  # Add this block's validation time
        
        # Track confidence statistics for enhanced errors
        enhanced_errors = [e for e in errors if self._is_enhanced_error(e)]
        if enhanced_errors:
            confidences = [e.get('confidence_score', 0.0) for e in enhanced_errors if e.get('confidence_score') is not None]
            if confidences:
                self.validation_performance['confidence_stats']['min'] = min(self.validation_performance['confidence_stats']['min'], min(confidences))
                self.validation_performance['confidence_stats']['max'] = max(self.validation_performance['confidence_stats']['max'], max(confidences))
                
                # Update running average
                current_avg = self.validation_performance['confidence_stats']['avg']
                total_validations = self.validation_performance['total_validations']
                new_avg = sum(confidences) / len(confidences)
                self.validation_performance['confidence_stats']['avg'] = (current_avg * (total_validations - 1) + new_avg) / total_validations
    
    def _is_enhanced_error(self, error: Dict[str, Any]) -> bool:
        """Check if an error has enhanced validation data."""
        return error.get('enhanced_validation_available', False) or error.get('confidence_score') is not None
    
    def _get_validation_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of validation performance metrics."""
        performance = self.validation_performance.copy()
        
        # Add derived metrics
        if performance['total_validations'] > 0:
            performance['avg_validation_time'] = performance['validation_time'] / performance['total_validations']
        else:
            performance['avg_validation_time'] = 0.0
        
        # Get validation system statistics if available
        try:
            if hasattr(self.rules_registry, 'get_validation_stats'):
                registry_stats = self.rules_registry.get_validation_stats()
                performance['registry_stats'] = registry_stats
        except Exception as e:
            logger.debug(f"Could not get registry validation stats: {e}")
        
        return performance
    
    def _analyze_table_nested_content(self, table_block: Any, analysis_mode: AnalysisMode) -> List[Dict[str, Any]]:
        """
        Recursively analyze nested content within table cells (lists, notes, paragraphs).
        This ensures nested blocks are analyzed without being added as separate blocks in the UI.
        """
        all_nested_errors = []
        
        def analyze_block_recursively(block):
            """Recursively analyze a block and its children."""
            errors = []
            
            # Analyze the block itself if it has content
            if not block.should_skip_analysis():
                content = block.get_text_content()
                if isinstance(content, str) and content.strip():
                    context = block.get_context_info()
                    block_errors = self.mode_executor.analyze_block_content(block, content, analysis_mode, context)
                    block._analysis_errors = block_errors
                    errors.extend(block_errors)
            
            # Recursively analyze children
            if hasattr(block, 'children'):
                for child in block.children:
                    child_errors = analyze_block_recursively(child)
                    errors.extend(child_errors)
            
            return errors
        
        # Process all rows and cells
        if hasattr(table_block, 'children'):
            for row in table_block.children:
                if hasattr(row, 'children'):
                    for cell in row.children:
                        # Analyze the cell and all its nested content
                        cell_errors = analyze_block_recursively(cell)
                        all_nested_errors.extend(cell_errors)
        
        return all_nested_errors

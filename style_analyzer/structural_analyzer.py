"""
Structural Analysis Module
Handles block-aware analysis using document structure parsing.
"""

import logging
from typing import Dict, List, Any, Optional

try:
    from structural_parsing.parser_factory import StructuralParserFactory
    from structural_parsing.asciidoc.types import AsciiDocDocument, AsciiDocBlockType
    from structural_parsing.markdown.types import MarkdownDocument, MarkdownBlockType
    STRUCTURAL_PARSING_AVAILABLE = True
except ImportError:
    STRUCTURAL_PARSING_AVAILABLE = False

from .base_types import ErrorDict, AnalysisMode, AnalysisResult, create_analysis_result, create_error
from .block_processors import BlockProcessor
from .analysis_modes import AnalysisModeExecutor

logger = logging.getLogger(__name__)


class StructuralAnalyzer:
    """Handles document structure parsing and block-aware analysis."""
    
    def __init__(self, readability_analyzer, sentence_analyzer, statistics_calculator, 
                 suggestion_generator, rules_registry=None, nlp=None):
        """Initialize with analyzer components."""
        self.readability_analyzer = readability_analyzer
        self.sentence_analyzer = sentence_analyzer
        self.statistics_calculator = statistics_calculator
        self.suggestion_generator = suggestion_generator
        self.rules_registry = rules_registry
        self.nlp = nlp
        
        # Initialize structural parser factory if available
        self.parser_factory = None
        if STRUCTURAL_PARSING_AVAILABLE:
            try:
                self.parser_factory = StructuralParserFactory()
                logger.info("Structural parsing enabled - context-aware analysis available")
            except Exception as e:
                logger.warning(f"Failed to initialize structural parser: {e}")
                self.parser_factory = None
        
        # Initialize analysis mode executor
        self.mode_executor = AnalysisModeExecutor(
            readability_analyzer, sentence_analyzer, rules_registry, nlp
        )
    
    def analyze_with_structure(self, text: str, format_hint: str = 'auto', 
                             analysis_mode: AnalysisMode = AnalysisMode.SPACY_WITH_MODULAR_RULES) -> List[ErrorDict]:
        """Analyze document using structural information for context-aware analysis."""
        errors = []
        
        try:
            # Try structural parsing for context-aware analysis
            parsed_document = None
            if self.parser_factory:
                try:
                    # Ensure format_hint is a valid value and cast to Literal type
                    from typing import cast, Literal
                    if format_hint in ['asciidoc', 'markdown', 'auto']:
                        validated_hint = cast(Literal['asciidoc', 'markdown', 'auto'], format_hint)
                    else:
                        validated_hint = 'auto'
                    parse_result = self.parser_factory.parse(text, format_hint=validated_hint)
                    if parse_result.success:
                        parsed_document = parse_result.document
                        logger.info(f"Successfully parsed as {type(parsed_document).__name__}")
                except Exception as e:
                    logger.warning(f"Structural parsing failed, falling back to text analysis: {e}")
            
            # If structural parsing succeeded, use it for analysis
            if parsed_document:
                # Extract content blocks that should be analyzed
                content_blocks = BlockProcessor.get_analyzable_blocks(parsed_document)
                
                for block in content_blocks:
                    block_content = block.get_text_content()
                    if not block_content.strip():
                        continue
                    
                    # Apply context-specific analysis based on block type
                    block_context = block.get_context_info() if hasattr(block, 'get_context_info') else {}
                    block_errors = self.mode_executor.analyze_block_content(
                        block, block_content, analysis_mode, block_context
                    )
                    errors.extend(block_errors)
                
                logger.info(f"Structural analysis completed: {len(errors)} issues found across {len(content_blocks)} blocks")
            else:
                # Fall back to text-based analysis
                sentences = self._split_sentences(text)
                errors = self._analyze_without_structure(text, sentences, analysis_mode)
            
        except Exception as e:
            logger.error(f"Structural analysis failed: {e}")
            # Fall back to text-based analysis
            sentences = self._split_sentences(text)
            errors = self._analyze_without_structure(text, sentences, analysis_mode)
        
        return errors
    
    def analyze_with_blocks(self, text: str, format_hint: str = 'auto', 
                          analysis_mode: AnalysisMode = AnalysisMode.SPACY_WITH_MODULAR_RULES) -> Dict[str, Any]:
        """Perform block-aware analysis returning structured results with errors per block."""
        if not text or not text.strip():
            return {
                'analysis': create_analysis_result(
                    errors=[], suggestions=[], statistics={}, technical_metrics={},
                    overall_score=0, analysis_mode=AnalysisMode.NONE,
                    spacy_available=self.nlp is not None, 
                    modular_rules_available=self.rules_registry is not None
                ),
                'structural_blocks': [],
                'has_structure': False
            }
        
        try:
            # Try structural parsing for block-aware analysis
            parsed_document = None
            structural_blocks = []
            
            if self.parser_factory:
                try:
                    from typing import cast, Literal
                    if format_hint in ['asciidoc', 'markdown', 'auto']:
                        validated_hint = cast(Literal['asciidoc', 'markdown', 'auto'], format_hint)
                    else:
                        validated_hint = 'auto'
                    parse_result = self.parser_factory.parse(text, format_hint=validated_hint)
                    if parse_result.success:
                        parsed_document = parse_result.document
                        structural_blocks = self._create_structural_blocks_with_analysis(
                            parsed_document, analysis_mode
                        )
                        logger.info(f"Successfully created {len(structural_blocks)} structural blocks with individual analysis")
                except Exception as e:
                    logger.warning(f"Structural parsing failed, falling back to text analysis: {e}")
            
            # Collect all errors from blocks for overall analysis
            all_errors = []
            for block in structural_blocks:
                all_errors.extend(block.get('errors', []))
            
            # If no structural blocks, fall back to traditional analysis
            if not structural_blocks:
                logger.info("No structural blocks available, falling back to traditional analysis")
                sentences = self._split_sentences(text)
                all_errors = self._analyze_without_structure(text, sentences, analysis_mode)
            
            # Calculate overall statistics using full text
            sentences = self._split_sentences(text)
            paragraphs = self.statistics_calculator.split_paragraphs_safe(text)
            
            statistics = self.statistics_calculator.calculate_safe_statistics(
                text, sentences, paragraphs
            )
            
            technical_metrics = self.statistics_calculator.calculate_safe_technical_metrics(
                text, sentences, len(all_errors)
            )
            
            # Generate suggestions
            suggestions = self.suggestion_generator.generate_suggestions(
                all_errors, statistics, technical_metrics
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                all_errors, technical_metrics, statistics
            )
            
            # Create analysis result
            analysis = create_analysis_result(
                errors=all_errors,
                suggestions=suggestions,
                statistics=statistics,
                technical_metrics=technical_metrics,
                overall_score=overall_score,
                analysis_mode=analysis_mode,
                spacy_available=self.nlp is not None,
                modular_rules_available=self.rules_registry is not None
            )
            
            return {
                'analysis': analysis,
                'structural_blocks': structural_blocks,
                'has_structure': len(structural_blocks) > 0
            }
            
        except Exception as e:
            logger.error(f"Block-aware analysis failed: {e}")
            return {
                'analysis': create_analysis_result(
                    errors=[create_error(
                        error_type='system',
                        message=f'Analysis failed: {str(e)}',
                        suggestions=['Check text input and system configuration']
                    )],
                    suggestions=[],
                    statistics={},
                    technical_metrics={},
                    overall_score=0,
                    analysis_mode=AnalysisMode.ERROR,
                    spacy_available=self.nlp is not None,
                    modular_rules_available=self.rules_registry is not None
                ),
                'structural_blocks': [],
                'has_structure': False
            }
    
    def _create_structural_blocks_with_analysis(self, parsed_document, analysis_mode: AnalysisMode) -> List[Dict[str, Any]]:
        """Create structural blocks with individual analysis results."""
        structural_blocks = []
        
        try:
            # Get all blocks from the document and flatten hierarchy
            all_blocks = getattr(parsed_document, 'blocks', [])
            flattened_blocks = BlockProcessor.flatten_document_blocks(all_blocks)
            
            block_id = 0
            for block in flattened_blocks:
                # Get content, handling different block types appropriately
                content = BlockProcessor.get_block_display_content(block)
                
                # Skip blocks that truly have no content
                if not content.strip():
                    continue
                
                # Determine block type (check for synthetic type first)
                block_type = getattr(block, '_synthetic_block_type', block.block_type.value)
                
                # Create basic block info (children will be added after analysis)
                block_info = {
                    'block_id': block_id,
                    'block_type': block_type,
                    'content': content,
                    'raw_content': getattr(block, 'raw_content', ''),
                    'should_skip_analysis': block.should_skip_analysis() if hasattr(block, 'should_skip_analysis') else False,
                    'context': block.get_context_info() if hasattr(block, 'get_context_info') else {},
                    'level': getattr(block, 'level', 0),
                    'admonition_type': getattr(getattr(block, 'admonition_type', None), 'value', None) if getattr(block, 'admonition_type', None) else None,
                    'errors': []
                }
                
                # Analyze the block if it shouldn't be skipped
                if not block_info['should_skip_analysis']:
                    try:
                        block_errors = self.mode_executor.analyze_block_content(
                            block, block_info['content'], analysis_mode, block_info['context']
                        )
                        block_info['errors'] = block_errors
                        logger.debug(f"Block {block_id} ({block.block_type.value}): {len(block_errors)} errors found")
                    except Exception as e:
                        logger.error(f"Error analyzing block {block_id}: {e}")
                
                # Convert children to dict after analysis (so child errors are included)
                block_info['children'] = BlockProcessor.convert_children_to_dict(getattr(block, 'children', []))
                
                structural_blocks.append(block_info)
                block_id += 1
                
        except Exception as e:
            logger.error(f"Error creating structural blocks with analysis: {e}")
            
        return structural_blocks
    
    def _analyze_without_structure(self, text: str, sentences: List[str], analysis_mode: AnalysisMode) -> List[ErrorDict]:
        """Fall back to traditional text-based analysis."""
        errors = []
        
        if analysis_mode == AnalysisMode.SPACY_WITH_MODULAR_RULES:
            errors = self.mode_executor.analyze_spacy_with_modular_rules(text, sentences, None)
        elif analysis_mode == AnalysisMode.MODULAR_RULES_WITH_FALLBACKS:
            errors = self.mode_executor.analyze_modular_rules_with_fallbacks(text, sentences, None)
        elif analysis_mode == AnalysisMode.SPACY_LEGACY_ONLY:
            errors = self.mode_executor.analyze_spacy_legacy_only(text, sentences, None)
        elif analysis_mode == AnalysisMode.MINIMAL_SAFE_MODE:
            errors = self.mode_executor.analyze_minimal_safe_mode(text, sentences, None)
        else:
            # Error mode
            errors = [create_error(
                error_type='system',
                message='Analysis system could not determine safe analysis mode.',
                suggestions=['Check system configuration and dependencies']
            )]
        
        return errors
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences safely."""
        try:
            if self.nlp:
                return self.sentence_analyzer.split_sentences_safe(text, self.nlp)
            else:
                return self.sentence_analyzer.split_sentences_safe(text)
        except Exception as e:
            logger.error(f"Error splitting sentences: {e}")
            # Ultimate fallback
            import re
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_overall_score(self, errors: List[ErrorDict], technical_metrics: Dict[str, Any], 
                               statistics: Dict[str, Any]) -> float:
        """Calculate overall style score safely."""
        try:
            # Base score
            base_score = 85.0
            
            # Deduct points for errors
            error_penalty = min(len(errors) * 5, 30)  # Max 30 points penalty
            
            # Adjust for readability
            readability_score = technical_metrics.get('readability_score', 60.0)
            if readability_score < 60:
                readability_penalty = (60 - readability_score) * 0.3
            else:
                readability_penalty = 0
            
            # Final score
            final_score = base_score - error_penalty - readability_penalty
            
            # Ensure score is between 0 and 100
            return max(0, min(100, final_score))
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 50.0  # Safe default 
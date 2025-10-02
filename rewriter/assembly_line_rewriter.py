"""
Assembly Line Rewriter
Orchestrates the rewriting process using AI multi-shot prompting.
"""
import logging
import time
from typing import List, Dict, Any, Optional, Callable
from .prompts import PromptGenerator
from .generators import TextGenerator
from .processors import TextProcessor
from .evaluators import RewriteEvaluator
from .station_mapper import ErrorStationMapper
from .progress_tracker import WorldClassProgressTracker
from .surgical_snippet_processor import SurgicalSnippetProcessor

# Enhanced validation system integration
try:
    from validation.confidence.confidence_calculator import ConfidenceCalculator
    from validation.confidence.rule_reliability import get_rule_reliability_coefficient
    ENHANCED_VALIDATION_AVAILABLE = True
except ImportError:
    ENHANCED_VALIDATION_AVAILABLE = False

logger = logging.getLogger(__name__)

class AssemblyLineRewriter:
    """
    Orchestrates a multi-level, single-pass rewriting process.
    """
    # Shared instances to avoid repeated initialization
    _shared_prompt_generator = None
    _shared_evaluator = None
    _shared_surgical_processor = None
    
    def __init__(self, text_generator: TextGenerator, text_processor: TextProcessor, progress_callback: Optional[Callable] = None):
        self.text_generator = text_generator
        self.text_processor = text_processor
        self.progress_callback = progress_callback
        
        # Use shared instances to avoid repeated YAML loading
        if AssemblyLineRewriter._shared_prompt_generator is None:
            AssemblyLineRewriter._shared_prompt_generator = PromptGenerator()
            logger.info("🚀 Created shared PromptGenerator (with cached ExampleSelector)")
        if AssemblyLineRewriter._shared_evaluator is None:
            AssemblyLineRewriter._shared_evaluator = RewriteEvaluator()
            logger.info("🚀 Created shared RewriteEvaluator")
        if AssemblyLineRewriter._shared_surgical_processor is None:
            AssemblyLineRewriter._shared_surgical_processor = SurgicalSnippetProcessor(
                text_generator, AssemblyLineRewriter._shared_prompt_generator
            )
            logger.info("🔬 Created shared SurgicalSnippetProcessor")
            
        self.prompt_generator = AssemblyLineRewriter._shared_prompt_generator
        self.evaluator = AssemblyLineRewriter._shared_evaluator
        self.surgical_processor = AssemblyLineRewriter._shared_surgical_processor
        
        # Initialize enhanced validation system for intelligent consolidation
        self.enhanced_validation_enabled = ENHANCED_VALIDATION_AVAILABLE
        if self.enhanced_validation_enabled:
            try:
                self.confidence_calculator = ConfidenceCalculator()
                logger.info("🎯 Enhanced validation system initialized for intelligent consolidation")
            except Exception as e:
                logger.warning(f"Failed to initialize confidence calculator: {e}")
                self.enhanced_validation_enabled = False
        else:
            logger.info("⚠️ Enhanced validation system not available - using fallback consolidation logic")
        
        # Performance tracking for AI processing
        self.processing_stats = {
            'blocks_processed': 0,
            'errors_fixed': 0,
            'average_confidence': 0.0,
            'total_processing_time_ms': 0,
            # Error density heuristic metrics
            'holistic_mode_triggered': 0,
            'holistic_mode_successful': 0,
            'high_density_sentences_detected': 0,
            'max_density_encountered': 0.0,
            'density_analysis_time_ms': 0,
            'holistic_vs_surgical_ratio': 0.0
        }
        
        logger.debug(f"⚡ AI rewriter initialized with shared components")

    def _sort_errors_by_priority(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Sort errors by priority level for optimal processing order.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            Sorted list with highest priority errors first
        """
        if not errors:
            return errors
            
        # Priority mapping: higher numbers = higher priority
        priority_map = {
            'high': 3,
            'urgent': 3,
            'medium': 2,
            'low': 1
        }
        
        # Severity mapping as fallback
        severity_map = {
            'high': 3,
            'medium': 2,
            'low': 1
        }
        
        def get_priority_score(error: Dict[str, Any]) -> int:
            # Try priority field first
            priority = error.get('priority', '').lower()
            if priority in priority_map:
                return priority_map[priority]
                
            # Fall back to severity
            severity = error.get('severity', '').lower()
            if severity in severity_map:
                return severity_map[severity]
                
            # Default to medium priority
            return 2
        
        # Sort by priority score (descending) then by error type for consistency
        return sorted(errors, key=lambda x: (get_priority_score(x), x.get('type', '')), reverse=True)

    def apply_block_level_assembly_line_fixes(self, block_content: str, block_errors: List[Dict[str, Any]], block_type: str, session_id: str = None, block_id: str = None) -> Dict[str, Any]:
        """
        Apply AI fixes to a single structural block.
        NOW WITH REAL-TIME PROGRESS TRACKING!
        
        Args:
            block_content: The content of the specific block to rewrite
            block_errors: List of errors detected in this block
            block_type: Type of block (paragraph, heading, list, etc.)
            session_id: WebSocket session ID for progress updates
            block_id: UI block ID for progress tracking
            
        Returns:
            Dictionary with rewrite results
        """
        print(f"\n🔍 DEBUG ASSEMBLY LINE REWRITER:")
        print(f"   📋 Method called with:")
        print(f"      - block_content length: {len(block_content) if block_content else 0}")
        print(f"      - block_errors count: {len(block_errors) if block_errors else 0}")
        print(f"      - block_type: {block_type}")
        print(f"      - session_id: {session_id}")
        print(f"      - block_id: {block_id}")
        print(f"      - progress_callback: {self.progress_callback}")
        print(f"      - progress_callback type: {type(self.progress_callback)}")
        
        try:
            if not block_content or not block_content.strip():
                print(f"   ❌ Empty block content - returning empty result")
                return self._empty_result()
            
            if not block_errors:
                print(f"   ⚠️  No errors found - returning clean result")
                logger.info("No errors found for block, skipping rewrite.")
                return {
                    'rewritten_text': block_content,
                    'improvements': ['Block is already clean'],
                    'confidence': 1.0,
                    'errors_fixed': 0,
                    'applicable_stations': [],
                    'block_type': block_type,
                    'processing_method': 'no_errors_detected'
                }
            
            import time
            start_time = time.time()
            
            print(f"   🏭 Starting assembly line processing")
            logger.info(f"🏭 assembly line processing: {block_content[:50]}... with {len(block_errors)} errors")
            
            # Lightweight progress tracking initialization
            original_session_id = session_id
            if not block_id:
                block_id = f"block_{int(time.time())}"
            
            # Only create progress tracker if callback provided
            progress_tracker = None
            if self.progress_callback:
                progress_tracker = WorldClassProgressTracker(original_session_id, block_id, self.progress_callback)
                logger.debug("✅ WorldClassProgressTracker created")
            
            # Get applicable stations for multi-pass processing
            applicable_stations = self.get_applicable_stations(block_errors)
            
            if not applicable_stations:
                logger.warning("⚠️ No applicable stations found for error types")
                if progress_tracker:
                    progress_tracker.handle_error(Exception("No applicable stations found"), "Station Discovery")
                return {
                    'rewritten_text': block_content,
                    'improvements': ['No applicable stations found'],
                    'confidence': 0.0,
                    'errors_fixed': 0,
                    'applicable_stations': [],
                    'block_type': block_type,
                    'processing_method': 'no_stations_applicable'
                }
            
            # Initialize progress tracking only if enabled
            if progress_tracker:
                progress_tracker.initialize_multi_pass_processing(applicable_stations, total_passes=1)
            
            # Process through multi-pass assembly line with AI and progress tracking
            result = self._process_multipass_assembly_line(
                block_content, 
                block_errors, 
                applicable_stations, 
                block_type,
                progress_tracker
            )
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            self.processing_stats['total_processing_time_ms'] += processing_time
            
            # Complete tracking only if enabled
            performance_summary = None
            if progress_tracker:
                performance_summary = progress_tracker.complete_processing(
                    result.get('errors_fixed', 0),
                    result.get('improvements', [])
                )
            
            # Add block-specific metadata
            result.update({
                'applicable_stations': applicable_stations,
                'block_type': block_type,
                'original_errors': len(block_errors),
                'processing_time_ms': processing_time,
                'world_class_ai_used': True
            })
            
            # Add progress tracking data only if available
            if progress_tracker and performance_summary:
                result['progress_tracking'] = {
                    'performance_summary': performance_summary,
                    'metrics': progress_tracker.get_performance_metrics()
                }
            
            logger.info(f"🏆 assembly line processing complete: {result.get('errors_fixed', 0)}/{len(block_errors)} errors fixed in {processing_time}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            return {
                'rewritten_text': block_content,
                'improvements': [],
                'confidence': 0.0,
                'errors_fixed': 0,
                'applicable_stations': [],
                'block_type': block_type,
                'processing_method': 'ai_failed',
                'error': f'AI processing failed: {str(e)}'
            }

    def _get_errors_for_station(self, errors: List[Dict[str, Any]], station: str) -> List[Dict[str, Any]]:
        """Get errors that belong to a specific assembly line station."""
        return ErrorStationMapper.get_errors_for_station(errors, station)

    def _consolidate_instructions(self, station_errors: List[Dict[str, Any]], station: str = None) -> List[Dict[str, Any]]:
        """
        Consolidate conflicting instructions for the same text spans within a station.
        
        This prevents the LLM from receiving conflicting instructions like:
        - "Change 'will provide' to present tense" (Verbs rule)
        - "Replace 'will provide' with better word choice" (Conversational Style rule)
        
        Which could cause hallucinations like "overprovide".
        
        Args:
            station_errors: List of errors for this station
            station: Station name for logging context
            
        Returns:
            List of consolidated errors with conflicts resolved
        """
        if len(station_errors) <= 1:
            logger.debug(f"🔧 Consolidation: {len(station_errors)} error(s) - no consolidation needed")
            return station_errors
        
        logger.info(f"🔧 Starting instruction consolidation for {len(station_errors)} errors in {station} station")
        
        # Group errors by exact text span and flagged text
        span_groups = {}
        
        for error in station_errors:
            span_key = self._create_span_key(error)
            
            if span_key not in span_groups:
                span_groups[span_key] = []
            span_groups[span_key].append(error)
        
        logger.debug(f"🔧 Created {len(span_groups)} span groups from {len(station_errors)} errors")
        
        consolidated_errors = []
        total_conflicts_resolved = 0
        
        for span_key, error_group in span_groups.items():
            if len(error_group) == 1:
                # No conflict - keep single error
                consolidated_errors.append(error_group[0])
                logger.debug(f"🔧 Span '{span_key[:50]}...': No conflict (1 error)")
            else:
                # Conflict detected - resolve by priority
                primary_error = self._select_primary_error_for_span(error_group, station)
                consolidated_errors.append(primary_error)
                
                removed_types = [e.get('type', 'unknown') for e in error_group if e != primary_error]
                flagged_text = error_group[0].get('flagged_text', 'unknown')
                
                logger.info(f"🎯 CONFLICT RESOLVED: '{flagged_text}' - Prioritized '{primary_error.get('type')}' over {removed_types}")
                total_conflicts_resolved += len(error_group) - 1
                
                # Add consolidation metadata for debugging
                primary_error['consolidation_info'] = {
                    'was_consolidated': True,
                    'original_count': len(error_group),
                    'removed_types': removed_types,
                    'consolidation_reason': 'same_span_priority_resolution'
                }
        
        logger.info(f"🏆 Consolidation complete: {len(station_errors)} → {len(consolidated_errors)} errors ({total_conflicts_resolved} conflicts resolved)")
        
        return consolidated_errors
    
    def _create_span_key(self, error: Dict[str, Any]) -> str:
        """
        Create a unique key for grouping errors by text span.
        
        Uses both span coordinates and flagged text to ensure accurate grouping.
        """
        # Primary: Use span if available
        span = error.get('span')
        if span and isinstance(span, (list, tuple)) and len(span) == 2:
            span_part = f"span_{span[0]}_{span[1]}"
        else:
            span_part = "span_unknown"
        
        # Secondary: Use flagged text for additional precision
        flagged_text = error.get('flagged_text', '').strip().lower()
        if flagged_text:
            text_part = f"text_{flagged_text}"
        else:
            text_part = "text_unknown"
        
        # Combine both for precise matching
        return f"{span_part}_{text_part}"
    
    def _select_primary_error_for_span(self, error_group: List[Dict[str, Any]], station: str = None) -> Dict[str, Any]:
        """
        Select the primary error when multiple errors target the same span.
        
        Enhanced with your validation system:
        1. Uses ConfidenceCalculator for intelligent scoring
        2. Uses RuleReliabilityCalculator for evidence-based reliability
        3. Combines confidence + reliability + structural priorities
        
        Args:
            error_group: List of conflicting errors for the same span
            station: Station context for priority decisions
            
        Returns:
            The primary error that should be used
        """
        def get_enhanced_priority_score(error: Dict[str, Any]) -> tuple:
            error_type = error.get('type', 'unknown')
            
            if self.enhanced_validation_enabled:
                # Use your sophisticated validation system! 🎯
                try:
                    # Calculate confidence using your ConfidenceCalculator
                    confidence_score = self.confidence_calculator.calculate_confidence(error)
                    
                    # Get rule reliability from your RuleReliabilityCalculator  
                    reliability_coefficient = get_rule_reliability_coefficient(error_type)
                    
                    # Combine confidence and reliability for base score
                    base_score = confidence_score * reliability_coefficient * 100
                    
                    logger.debug(f"🧠 Enhanced scoring for {error_type}: confidence={confidence_score:.3f}, reliability={reliability_coefficient:.3f}, base={base_score:.1f}")
                    
                except Exception as e:
                    logger.debug(f"Enhanced validation failed for {error_type}, using fallback: {e}")
                    base_score = self._get_fallback_priority_score(error)
            else:
                # Fallback to original logic when validation system unavailable
                base_score = self._get_fallback_priority_score(error)
            
            # Apply structural priority boost (grammar rules still beat style rules)
            structural_boost = self._get_structural_priority_boost(error_type)
            
            # Apply suggestion quality bonus
            suggestion_bonus = self._get_suggestion_quality_bonus(error)
            
            # Apply message specificity bonus
            message_bonus = self._get_message_specificity_bonus(error)
            
            # Calculate final score
            final_score = base_score + structural_boost + suggestion_bonus + message_bonus
            
            logger.debug(f"🎯 Final priority for {error_type}: {final_score:.1f} (base={base_score:.1f}, struct={structural_boost}, sugg={suggestion_bonus}, msg={message_bonus})")
            
            # Return tuple for sorting: (final_score, has_suggestions, error_type for tie-breaking)
            suggestions = error.get('suggestions', [])
            return (final_score, len(suggestions), error_type)
        
        # Sort by priority (highest first) and return top error
        sorted_errors = sorted(error_group, key=get_enhanced_priority_score, reverse=True)
        primary_error = sorted_errors[0]
        
        # Add consolidation metadata
        if self.enhanced_validation_enabled:
            primary_error['consolidation_method'] = 'enhanced_validation'
        else:
            primary_error['consolidation_method'] = 'fallback_logic'
        
        logger.debug(f"🏆 Selected '{primary_error.get('type')}' as primary from {len(error_group)} conflicting errors using {primary_error['consolidation_method']}")
        
        return primary_error
    
    def _get_fallback_priority_score(self, error: Dict[str, Any]) -> float:
        """Fallback priority scoring when enhanced validation is unavailable."""
        error_type = error.get('type', 'unknown')
        severity = error.get('severity', 'low')
        
        # Original hardcoded logic as fallback
        grammar_structural_types = {
            'verbs': 100, 'ambiguity': 95, 'pronouns': 90,
            'passive_voice': 85, 'sentence_length': 80
        }
        grammar_priority = grammar_structural_types.get(error_type, 0)
        
        severity_scores = {
            'critical': 50, 'high': 40, 'medium': 30, 'low': 20, 'info': 10
        }
        severity_priority = severity_scores.get(severity.lower(), 20)
        
        return float(grammar_priority + severity_priority)
    
    def _get_structural_priority_boost(self, error_type: str) -> float:
        """Get structural priority boost for grammar/structural rules."""
        grammar_structural_types = {
            'verbs', 'ambiguity', 'pronouns', 'passive_voice', 'sentence_length'
        }
        if error_type in grammar_structural_types:
            return 25.0  # Grammar rules get boost
        
        style_types = {'conversational_style', 'tone', 'word_usage'}
        if error_type in style_types or any(style in error_type for style in style_types):
            return -15.0  # Style rules get penalty in conflicts
        
        return 0.0
    
    def _get_suggestion_quality_bonus(self, error: Dict[str, Any]) -> float:
        """Get bonus based on suggestion quality."""
        suggestions = error.get('suggestions', [])
        if not suggestions:
            return 0.0
        
        if any(len(s) > 10 for s in suggestions):  # Detailed suggestions
            return 10.0
        elif len(suggestions) > 0:  # Has suggestions
            return 5.0
        
        return 0.0
    
    def _get_message_specificity_bonus(self, error: Dict[str, Any]) -> float:
        """Get bonus based on message specificity."""
        message = error.get('message', '')
        if not message:
            return 0.0
        
        bonus = 0.0
        if 'example:' in message.lower() or '→' in message:
            bonus += 8.0  # Has examples
        if any(word in message.lower() for word in ['change', 'replace', 'use', 'consider']):
            bonus += 5.0  # Actionable message
        
        return bonus

    def _generate_station_preview(self, station: str, errors: List[Dict[str, Any]], processed_content: str) -> str:
        """Generate preview text showing what this station accomplished."""
        if not errors:
            return f"{self.get_station_display_name(station)}: No issues found"
        
        error_types = [error.get('type', 'unknown') for error in errors]
        
        # Generate specific preview based on station type
        if station == 'urgent':
            return f"Fixed {len(errors)} critical issue(s): {', '.join(set(error_types))}"
        elif station == 'high':
            if 'verbs' in error_types or 'passive_voice' in error_types:
                return f"Converted passive voice → active voice ({len(errors)} fix(es))"
            else:
                return f"Fixed {len(errors)} structural issue(s)"
        elif station == 'medium':
            if any('contractions' in et for et in error_types):
                return f"Expanded {len(errors)} contraction(s)"
            else:
                return f"Fixed {len(errors)} grammar issue(s)"
        elif station == 'low':
            return f"Applied {len(errors)} style improvement(s)"
        
        return f"Processed {len(errors)} issue(s)"
    
    def _validate_rewrite_quality(self, original_content: str, rewritten_content: str, 
                                original_errors: List[Dict[str, Any]]) -> List[str]:
        """
        Lightweight post-rewrite validation to catch AI-introduced problems.
        
        Focuses on:
        - New ambiguities introduced by AI
        - Vague actors ('system', 'application', 'software')
        - Loss of critical meaning
        - Performance cost: ~5ms (very fast rule-based checks)
        """
        concerns = []
        
        if not rewritten_content or rewritten_content == original_content:
            return concerns
        
        # VALIDATION 1: Detect vague/ambiguous actors introduced by AI
        vague_actors = ['the system', 'the application', 'the software', 'the program']
        original_lower = original_content.lower()
        rewritten_lower = rewritten_content.lower()
        
        for vague_actor in vague_actors:
            if vague_actor not in original_lower and vague_actor in rewritten_lower:
                concerns.append(f"Introduced vague actor: '{vague_actor}'")
        
        # VALIDATION 2: Check for new passive voice patterns 
        new_passive_patterns = ['is clicked', 'was clicked', 'are processed', 'were processed']
        for pattern in new_passive_patterns:
            if pattern not in original_lower and pattern in rewritten_lower:
                concerns.append(f"Introduced new passive voice: '{pattern}'")
        
        # VALIDATION 3: Generic pronoun proliferation
        generic_pronouns = ['this is', 'that is', 'it is', 'these are']
        for pronoun in generic_pronouns:
            original_count = original_lower.count(pronoun)
            rewritten_count = rewritten_lower.count(pronoun)
            if rewritten_count > original_count:
                concerns.append(f"Increased generic pronouns: '{pronoun}' ({original_count}→{rewritten_count})")
        
        # VALIDATION 4: Meaning preservation check (basic)
        # Check if critical keywords were lost
        if len(rewritten_content) < len(original_content) * 0.5:
            concerns.append("Significant content reduction - possible meaning loss")
        
        # VALIDATION 5: Actor specification check for verbs errors
        verb_errors = [e for e in original_errors if e.get('type') == 'verbs']
        if verb_errors:
            # For verb corrections, ensure we didn't just swap one ambiguity for another
            if any(word in rewritten_lower for word in ['system', 'application', 'software']):
                if not any(word in original_lower for word in ['system', 'application', 'software']):
                    concerns.append("Verb correction introduced generic technical actor")
        
        return concerns

    def get_applicable_stations(self, block_errors: List[Dict[str, Any]]) -> List[str]:
        """Return only assembly line stations needed for this block's errors."""
        error_types = [error.get('type', '') for error in block_errors]
        return ErrorStationMapper.get_applicable_stations(error_types)

    def get_station_display_name(self, station: str) -> str:
        """Get user-friendly display name for assembly line station."""
        return ErrorStationMapper.get_station_display_name(station)
    
    def _process_multipass_assembly_line(self, text: str, all_errors: List[Dict[str, Any]], 
                                       applicable_stations: List[str], block_type: str = "text",
                                       progress_tracker: WorldClassProgressTracker = None) -> Dict[str, Any]:
        """
        Process text through multi-pass assembly line with AI at each station.
        NOW WITH REAL-TIME PROGRESS TRACKING!
        
        Args:
            text: Original text to process
            all_errors: All detected errors
            applicable_stations: List of stations to process (in priority order)
            block_type: Type of content block
            progress_tracker: progress tracking system
            
        Returns:
            Dictionary with final results and per-pass statistics
        """
        if not applicable_stations:
            return {
                'rewritten_text': text,
                'original_text': text,
                'errors_fixed': 0,
                'confidence': 1.0,
                'processing_method': 'no_stations_needed',
                'pass_results': []
            }
        
        current_text = text
        total_errors_fixed = 0
        pass_results = []
        overall_confidence = 1.0
        
        logger.info(f"🏭 Multi-pass assembly line: {len(applicable_stations)} stations for {len(all_errors)} errors")
        
        # Start progress tracking only if enabled
        if progress_tracker:
            progress_tracker.start_pass(1, "AI Processing")
        
        # Process through each station in priority order
        for i, station in enumerate(applicable_stations, 1):
            station_errors = self._get_errors_for_station(all_errors, station)
            
            if not station_errors:
                continue  # Skip stations with no errors
            
            station_name = self.get_station_display_name(station)
            logger.info(f"🔧 Pass {i}/{len(applicable_stations)} - {station_name}: {len(station_errors)} errors")
            
            # Consolidate conflicting instructions within this station
            consolidated_errors = self._consolidate_instructions(station_errors, station)
            
            # Update error count after consolidation
            if len(consolidated_errors) != len(station_errors):
                logger.info(f"🎯 {station_name}: {len(station_errors)} → {len(consolidated_errors)} errors after consolidation")
            
            # Start station tracking only if enabled
            if progress_tracker:
                progress_tracker.start_station(station, station_name, len(consolidated_errors))
            
            # Apply AI for this station's consolidated errors  
            station_result = self._apply_world_class_ai_fixes(current_text, consolidated_errors, block_type, station, progress_tracker)
            
            if station_result.get('rewritten_text') and station_result['rewritten_text'] != current_text:
                # Success at this station
                current_text = station_result['rewritten_text']
                errors_fixed_this_pass = station_result.get('errors_fixed', 0)
                total_errors_fixed += errors_fixed_this_pass
                
                # Determine input text (original text for first pass, previous output for others)
                input_text = text if len(pass_results) == 0 else pass_results[-1]['output_text']
                
                improvements = station_result.get('improvements', [])
                
                # POST-REWRITE VALIDATION: Check for AI-introduced problems (for critical stations)
                validation_concerns = []
                if station in ['urgent', 'high']:  # Only validate critical fixes
                    validation_concerns = self._validate_rewrite_quality(
                        original_content=text, 
                        rewritten_content=current_text,
                        original_errors=station_errors
                    )
                    
                    # Log validation concerns
                    if validation_concerns:
                        logger.warning(f"⚠️ Validation concerns for {station_name}: {validation_concerns}")
                        
                        # Add validation concerns to improvements for visibility
                        validation_note = f"Validation concerns: {len(validation_concerns)} issue(s) detected"
                        improvements.append(validation_note)
                
                pass_results.append({
                    'station': station,
                    'station_name': station_name,
                    'errors_processed': len(station_errors),
                    'errors_fixed': errors_fixed_this_pass,
                    'confidence': station_result.get('confidence', 0.8),
                    'input_text': input_text,
                    'output_text': current_text,
                    'processing_method': station_result.get('processing_method', 'world_class_ai'),
                    'improvements': improvements,
                    'validation_concerns': validation_concerns
                })
                
                # Complete station tracking only if enabled  
                if progress_tracker:
                    progress_tracker.complete_station(station, station_name, errors_fixed_this_pass, improvements)
                
                # Update overall confidence (weighted average)
                overall_confidence = (overall_confidence + station_result.get('confidence', 0.8)) / 2
                
                logger.info(f"✅ {station_name}: {errors_fixed_this_pass} errors fixed, confidence: {station_result.get('confidence', 0.8):.2f}")
            else:
                # No changes at this station
                input_text = text if len(pass_results) == 0 else pass_results[-1]['output_text']
                
                pass_results.append({
                    'station': station,
                    'station_name': station_name,
                    'errors_processed': len(station_errors),
                    'errors_fixed': 0,
                    'confidence': 0.1,
                    'input_text': input_text,
                    'output_text': current_text,
                    'processing_method': 'ai_no_changes',
                    'improvements': [],
                    'validation_concerns': []  # No validation concerns when no changes made
                })
                
                # Complete station tracking only if enabled
                if progress_tracker:
                    progress_tracker.complete_station(station, station_name, 0, [])
                
                logger.warning(f"⚠️ {station_name}: No changes made")
        
        # Complete pass tracking only if enabled
        if progress_tracker:
            progress_tracker.complete_pass(1)
        
        # Calculate final confidence and statistics
        passes_with_changes = [p for p in pass_results if p['errors_fixed'] > 0]
        final_confidence = sum(p['confidence'] for p in passes_with_changes) / len(passes_with_changes) if passes_with_changes else 0.5
        
        # Collect all improvements from all stations
        all_improvements = []
        for pass_result in pass_results:
            all_improvements.extend(pass_result.get('improvements', []))
        
        return {
            'rewritten_text': current_text,
            'original_text': text,
            'errors_fixed': total_errors_fixed,
            'confidence': final_confidence,
            'processing_method': 'multipass_assembly_line_world_class',
            'passes_completed': len(applicable_stations),
            'passes_with_changes': len(passes_with_changes),
            'pass_results': pass_results,
            'improvements': all_improvements
        }

    def _apply_world_class_ai_fixes(self, text: str, errors: List[Dict[str, Any]], 
                                   block_type: str = "text", station: str = None, progress_tracker=None) -> Dict[str, Any]:
        """
        Apply optimal AI processing: surgical snippets for simple errors, full context for complex ones.
        
        HYBRID APPROACH:
        - Surgical snippet processing for self-contained errors (70-80% faster)
        - multi-shot prompting for complex contextual errors
        - Intelligent error routing based on complexity and span information
        
        Args:
            text: Original text to fix
            errors: List of detected errors for this station
            block_type: Type of content block for context
            station: Assembly line station (for focused prompting)
            
        Returns:
            Dictionary with corrected text and processing statistics
        """
        self.processing_stats['blocks_processed'] += 1
        
        if not errors:
            return {
                'rewritten_text': text,
                'original_text': text,
                'errors_fixed': 0,
                'confidence': 1.0,
                'processing_method': 'no_errors_detected'
            }
        
        try:
            # Analyze error density to determine processing strategy
            density_start_time = time.time()
            density_analysis = self._analyze_error_density(text, errors)
            density_time_ms = int((time.time() - density_start_time) * 1000)
            
            # Update density analysis metrics
            self.processing_stats['density_analysis_time_ms'] += density_time_ms
            self.processing_stats['max_density_encountered'] = max(
                self.processing_stats['max_density_encountered'],
                density_analysis['max_density']
            )
            self.processing_stats['high_density_sentences_detected'] += len(density_analysis['high_density_sentences'])
            
            if density_analysis['needs_holistic_rewrite']:
                # Use holistic rewriting for high-density error scenarios
                self.processing_stats['holistic_mode_triggered'] += 1
                
                logger.info(f"🚨 HIGH DENSITY DETECTED: {density_analysis['max_density']:.2f} density, {len(density_analysis['high_density_sentences'])} problematic sentences")
                logger.info(f"🔄 SWITCHING TO HOLISTIC MODE: {len(errors)} errors will be addressed comprehensively")
                
                holistic_result = self._apply_holistic_rewrite(text, errors, block_type, density_analysis, progress_tracker)
                
                # Track holistic mode success
                if holistic_result.get('errors_fixed', 0) > 0:
                    self.processing_stats['holistic_mode_successful'] += 1
                    logger.info(f"✅ HOLISTIC SUCCESS: Fixed {holistic_result['errors_fixed']} errors with {holistic_result['confidence']:.2f} confidence")
                else:
                    logger.warning(f"⚠️ HOLISTIC SUBOPTIMAL: {holistic_result.get('processing_method', 'unknown')} - {holistic_result.get('error', 'no changes')}")
                
                return holistic_result
            
            # Continue with normal hybrid processing for manageable error density
            logger.info(f"✅ NORMAL DENSITY: max {density_analysis['max_density']:.2f} - using hybrid surgical/contextual approach")
            logger.debug(f"📊 Density analysis completed in {density_time_ms}ms - {density_analysis['total_sentences']} sentences analyzed")
            
            # Route errors to surgical vs contextual processing
            surgical_errors = [e for e in errors if self.surgical_processor.is_surgical_candidate(e)]
            contextual_errors = [e for e in errors if not self.surgical_processor.is_surgical_candidate(e)]
            
            logger.info(f"🔬 Error routing: {len(surgical_errors)} surgical, {len(contextual_errors)} contextual")
            
            current_text = text
            total_errors_fixed = 0
            combined_improvements = []
            processing_methods = []
            combined_confidence = 1.0
            
            # PHASE 2: Process surgical errors first (fast, high-confidence fixes)
            if surgical_errors:
                surgical_result = self.surgical_processor.process_surgical_snippets(
                    current_text, surgical_errors, block_type, progress_tracker
                )
                
                if surgical_result.get('rewritten_text') != current_text:
                    current_text = surgical_result['rewritten_text']
                    total_errors_fixed += surgical_result.get('surgical_snippets_processed', 0)
                    combined_improvements.extend(surgical_result.get('improvements', []))
                    combined_confidence = surgical_result.get('confidence', 0.95)
                    processing_methods.append('surgical_snippets')
                    
                    logger.info(f"🚀 Surgical processing: {surgical_result.get('surgical_snippets_processed', 0)}/{len(surgical_errors)} fixed in {surgical_result.get('processing_time_ms', 0):.0f}ms")
            
            # PHASE 3: Process contextual errors with full AI pipeline
            if contextual_errors:
                complexity = self._assess_error_complexity(contextual_errors)
                
                if station:
                    # Station-focused prompt for multi-pass processing
                    station_name = self.get_station_display_name(station)
                    prompt = self.prompt_generator.create_station_focused_prompt(
                        current_text, contextual_errors, station, station_name, block_type
                    )
                    prompt_type = f'station_focused_{station}'
                elif complexity == 'high' or len(contextual_errors) > 3:
                    # Comprehensive prompting for complex cases
                    prompt = self.prompt_generator.create_world_class_multi_shot_prompt(
                        current_text, contextual_errors, block_type
                    )
                    prompt_type = 'world_class_comprehensive'
                else:
                    # Enhanced multi-shot prompting for moderate cases
                    prompt = self.prompt_generator.create_assembly_line_prompt(
                        current_text, contextual_errors, 1, block_type
                    )
                    prompt_type = 'enhanced_multi_shot'
                
                # Generate AI correction for contextual errors
                logger.debug(f"🧠 Sending {len(contextual_errors)} contextual errors to AI with prompt type: {prompt_type}")
                logger.debug(f"📝 Prompt preview (first 200 chars): {prompt[:200]}...")
                
                ai_result = self.text_generator.generate_text(prompt, current_text, use_case='assembly_line')
                
                logger.debug(f"🔍 AI result: {'✅ Success' if ai_result and ai_result.strip() else '❌ Empty/Failed'}")
                if ai_result:
                    logger.debug(f"📊 AI response length: {len(ai_result)} chars")
                    logger.debug(f"📝 AI response preview: {ai_result[:100]}{'...' if len(ai_result) > 100 else ''}")
                
                if ai_result and ai_result.strip() != current_text.strip():
                    # Successful contextual AI processing
                    current_text = self.text_processor.clean_generated_text(ai_result, current_text)
                    
                    contextual_errors_fixed = len(contextual_errors)
                    total_errors_fixed += contextual_errors_fixed
                    
                    # Calculate contextual confidence with processing result
                    contextual_confidence = self._calculate_ai_confidence(contextual_errors, complexity, {'processing_method': prompt_type})
                    
                    # Combine confidence (weighted by error count)
                    surgical_weight = len(surgical_errors) / len(errors)
                    contextual_weight = len(contextual_errors) / len(errors)
                    combined_confidence = (combined_confidence * surgical_weight + 
                                         contextual_confidence * contextual_weight)
                    
                    combined_improvements.append(f"Contextual AI fixes: {contextual_errors_fixed} errors")
                    processing_methods.append(f'contextual_ai_{prompt_type}')
                    
                    logger.info(f"🧠 Contextual AI: {contextual_errors_fixed} errors fixed")
            
            # PHASE 4: Final result compilation
            if current_text != text:
                # Update stats
                self.processing_stats['errors_fixed'] += total_errors_fixed
                
                # Determine processing method description
                if len(processing_methods) == 1:
                    processing_method = processing_methods[0]
                else:
                    processing_method = f"hybrid_{'+'.join(processing_methods)}"
                
                return {
                    'rewritten_text': current_text,
                    'original_text': text,
                    'errors_fixed': total_errors_fixed,
                    'confidence': min(0.98, combined_confidence),
                    'processing_method': processing_method,
                    'surgical_errors': len(surgical_errors),
                    'contextual_errors': len(contextual_errors),
                    'improvements': combined_improvements,
                    'hybrid_optimization': True
                }
            else:
                # No changes made
                logger.warning(f"No changes made for {len(errors)} errors (surgical: {len(surgical_errors)}, contextual: {len(contextual_errors)})")
                return {
                    'rewritten_text': text,
                    'original_text': text,
                    'errors_fixed': 0,
                    'confidence': 0.1,
                    'processing_method': 'hybrid_no_changes',
                    'surgical_errors': len(surgical_errors),
                    'contextual_errors': len(contextual_errors)
                }
                
        except Exception as e:
            logger.error(f"Hybrid AI processing failed: {e}")
            return {
                'rewritten_text': text,
                'original_text': text,
                'errors_fixed': 0,
                'confidence': 0.0,
                'processing_method': 'hybrid_failed',
                'error': str(e)
            }
    
    def _assess_error_complexity(self, errors: List[Dict[str, Any]]) -> str:
        """
        Assess the complexity of errors to determine optimal AI prompting strategy.
        
        Args:
            errors: List of errors to assess
            
        Returns:
            'low', 'medium', or 'high' complexity level
        """
        if not errors:
            return 'low'
        
        # High complexity indicators (need full context)
        high_complexity_types = {
            'ambiguity', 'passive_voice', 'sentence_length', 
            'legal_claims', 'tone', 'readability', 'subjunctive_mood',
            'pronouns', 'anthropomorphism'
        }
        
        # Medium complexity indicators  
        medium_complexity_types = {
            'word_usage_y', 'citations', 'headings',
            'word_usage_complex', 'technical_complex'
        }
        
        # SURGICAL SNIPPET candidates (self-contained, fast processing)
        surgical_types = {
            'contractions', 'prefixes', 'currency', 'abbreviations',
            'word_usage_simple', 'possessives', 'capitalization_simple',
            'punctuation_simple', 'technical_files_directories'
        }
        
        surgical_count = sum(1 for error in errors 
                           if self.surgical_processor.is_surgical_candidate(error))
        high_count = sum(1 for error in errors 
                        if error.get('type', '') in high_complexity_types)
        medium_count = sum(1 for error in errors 
                          if error.get('type', '') in medium_complexity_types)
        
        # Complexity scoring with surgical optimization potential
        if high_count > 0 or len(errors) > 4:
            return 'high'
        elif medium_count > 1 or len(errors) > 2:
            return 'medium' 
        elif surgical_count > 0:
            return 'surgical'  # NEW: Optimize for surgical snippet processing
        else:
            return 'low'
    
    def get_surgical_coverage_analysis(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get analysis of surgical processing coverage for given errors."""
        return self.surgical_processor.get_surgical_coverage_analysis(errors)
    
    def _analyze_error_density(self, text: str, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze error density per sentence to determine if holistic rewriting is needed.
        
        Args:
            text: Original text being analyzed
            errors: List of errors to analyze
            
        Returns:
            Dictionary with density analysis results
        """
        if not errors or not text or not text.strip():
            return {
                'max_density': 0,
                'high_density_sentences': [],
                'total_sentences': 0,
                'needs_holistic_rewrite': False,
                'analysis_method': 'empty_input'
            }
        
        # Split text into sentences for density analysis
        sentences = self._split_into_sentences(text)
        sentence_errors = {}
        
        # Group errors by sentence
        for error in errors:
            span = error.get('span')
            if not span or not isinstance(span, (list, tuple)) or len(span) < 2:
                continue
                
            error_start = span[0]
            sentence_index = self._find_sentence_for_span(error_start, text, sentences)
            
            if sentence_index not in sentence_errors:
                sentence_errors[sentence_index] = []
            sentence_errors[sentence_index].append(error)
        
        # Calculate density for each sentence
        sentence_densities = {}
        high_density_sentences = []
        max_density = 0
        
        for sentence_idx, sentence_error_list in sentence_errors.items():
            # Calculate weighted density (some error types are "heavier")
            weighted_density = self._calculate_weighted_error_density(sentence_error_list, sentences[sentence_idx] if sentence_idx < len(sentences) else "")
            sentence_densities[sentence_idx] = weighted_density
            
            if weighted_density > max_density:
                max_density = weighted_density
            
            # Check if this sentence exceeds the density threshold
            if self._exceeds_density_threshold(weighted_density, sentences[sentence_idx] if sentence_idx < len(sentences) else ""):
                high_density_sentences.append({
                    'sentence_index': sentence_idx,
                    'sentence_text': sentences[sentence_idx] if sentence_idx < len(sentences) else "",
                    'error_count': len(sentence_error_list),
                    'weighted_density': weighted_density,
                    'errors': sentence_error_list
                })
        
        # Determine if holistic rewrite is needed
        needs_holistic = len(high_density_sentences) > 0
        
        logger.info(f"🔍 Error density analysis: {len(sentences)} sentences, max density: {max_density:.2f}, {len(high_density_sentences)} high-density sentences")
        
        return {
            'max_density': max_density,
            'sentence_densities': sentence_densities,
            'high_density_sentences': high_density_sentences,
            'total_sentences': len(sentences),
            'needs_holistic_rewrite': needs_holistic,
            'analysis_method': 'weighted_sentence_density'
        }
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences for density analysis."""
        import re
        
        if not text or not text.strip():
            return []
        
        text = text.strip()
        
        # Simple sentence splitting (can be enhanced with spaCy later)
        # First, let's identify sentence boundaries more carefully
        sentence_pattern = r'([.!?]+)\s+'
        parts = re.split(sentence_pattern, text)
        
        sentences = []
        i = 0
        while i < len(parts):
            if i == len(parts) - 1:
                # Last part - might be a sentence without following punctuation split
                if parts[i].strip():
                    sentences.append(parts[i].strip())
                break
            elif i + 1 < len(parts) and re.match(r'[.!?]+', parts[i + 1]):
                # This part is followed by punctuation
                sentence = parts[i].strip() + parts[i + 1]
                if sentence.strip():
                    sentences.append(sentence)
                i += 2
            else:
                # This part is not followed by punctuation (shouldn't happen with our pattern)
                if parts[i].strip():
                    sentences.append(parts[i].strip())
                i += 1
        
        # Handle case where text doesn't end with punctuation
        if not re.search(r'[.!?]$', text) and sentences and not re.search(r'[.!?]$', sentences[-1]):
            # Original text doesn't end with punctuation, so don't add it
            pass
        
        return [s for s in sentences if s.strip()]
    
    def _find_sentence_for_span(self, span_start: int, text: str, sentences: List[str]) -> int:
        """Find which sentence index a character span belongs to."""
        if not sentences:
            return 0
            
        current_pos = 0
        for i, sentence in enumerate(sentences):
            sentence_end = current_pos + len(sentence)
            if span_start >= current_pos and span_start <= sentence_end:
                return i
            current_pos = sentence_end + 1  # Account for space between sentences
        
        # Fallback to last sentence if span is beyond text
        return max(0, len(sentences) - 1)
    
    def _calculate_weighted_error_density(self, errors: List[Dict[str, Any]], sentence: str) -> float:
        """
        Calculate weighted error density considering error type complexity.
        
        Args:
            errors: List of errors in this sentence
            sentence: The sentence text for length consideration
            
        Returns:
            Weighted density score
        """
        if not errors:
            return 0.0
        
        # Error type weights - some errors are more complex than others
        error_weights = {
            # High complexity errors (count as 2+ errors each)
            'ambiguity': 2.0,
            'passive_voice': 1.8,
            'sentence_length': 1.5,
            'pronouns': 1.5,
            'subjunctive_mood': 1.5,
            'verbs': 1.4,
            
            # Medium complexity errors  
            'word_usage_y': 1.2,
            'legal_claims': 1.3,
            'headings': 1.1,
            'tone': 1.2,
            
            # Simple errors (count as less than 1 error each)
            'contractions': 0.5,
            'possessives': 0.4,
            'capitalization': 0.4,
            'abbreviations': 0.3,
            'prefixes': 0.3,
            'currency': 0.2,
        }
        
        # Calculate weighted error count
        weighted_count = 0.0
        for error in errors:
            error_type = error.get('type', 'unknown')
            weight = error_weights.get(error_type, 1.0)  # Default weight is 1.0
            weighted_count += weight
        
        # Consider sentence length - longer sentences can handle more errors
        sentence_words = len(sentence.split()) if sentence else 10
        length_factor = max(0.5, min(2.0, sentence_words / 20.0))  # Scale between 0.5x and 2x
        
        # Final density = weighted_errors / length_factor
        density = weighted_count / length_factor
        
        logger.debug(f"🔢 Sentence density: {len(errors)} errors (weighted: {weighted_count:.1f}) / {sentence_words} words (factor: {length_factor:.2f}) = {density:.2f}")
        
        return density
    
    def _exceeds_density_threshold(self, weighted_density: float, sentence: str) -> bool:
        """
        Determine if a sentence's error density exceeds the threshold for holistic rewriting.
        
        Args:
            weighted_density: Calculated weighted density score
            sentence: The sentence text for additional context
            
        Returns:
            True if holistic rewriting should be used for this sentence
        """
        # Base threshold
        base_threshold = 3.0
        
        # Adjust threshold based on sentence characteristics
        sentence_words = len(sentence.split()) if sentence else 10
        
        # Very short sentences get lower threshold
        if sentence_words < 8:
            adjusted_threshold = base_threshold * 0.7
        # Very long sentences get higher threshold  
        elif sentence_words > 25:
            adjusted_threshold = base_threshold * 1.3
        else:
            adjusted_threshold = base_threshold
        
        exceeds = weighted_density > adjusted_threshold
        
        if exceeds:
            logger.info(f"🚨 High density detected: {weighted_density:.2f} > {adjusted_threshold:.2f} (sentence: {sentence_words} words)")
        
        return exceeds

    def _apply_holistic_rewrite(self, text: str, errors: List[Dict[str, Any]], 
                               block_type: str, density_analysis: Dict[str, Any],
                               progress_tracker=None) -> Dict[str, Any]:
        """
        Apply holistic rewriting for high error density scenarios.
        
        Instead of complex surgical instructions, this uses simplified prompts
        that give the AI high-level improvement goals, preventing confusion
        and producing more natural results.
        
        Args:
            text: Original text to rewrite
            errors: List of all errors detected
            block_type: Type of content block
            density_analysis: Results from error density analysis
            progress_tracker: Progress tracking instance
            
        Returns:
            Dictionary with holistic rewrite results
        """
        logger.info(f"🔄 Starting holistic rewrite for {len(density_analysis['high_density_sentences'])} high-density sentences")
        
        try:
            # For now, apply holistic rewrite to the entire text
            # Future enhancement: could process sentence-by-sentence for mixed scenarios
            high_density_errors = errors  # All errors for holistic consideration
            
            # Create holistic prompt focused on improvement goals rather than detailed instructions
            prompt = self.prompt_generator.create_holistic_rewrite_prompt(
                text, high_density_errors, block_type
            )
            
            logger.debug(f"🧠 Sending holistic rewrite prompt for {len(errors)} errors")
            logger.debug(f"📝 Holistic prompt preview: {prompt[:200]}...")
            
            # Generate AI correction using simplified holistic approach
            ai_result = self.text_generator.generate_text(prompt, text, use_case='holistic_rewrite')
            
            if ai_result and ai_result.strip() != text.strip():
                # Successful holistic rewrite
                current_text = self.text_processor.clean_generated_text(ai_result, text)
                
                # Calculate confidence for holistic approach
                holistic_confidence = self._calculate_holistic_confidence(
                    density_analysis, len(errors), ai_result != text
                )
                
                # Generate improvement description
                improvements = [
                    f"Holistic rewrite applied to high-density text (density: {density_analysis['max_density']:.2f})",
                    f"Addressed {len(errors)} errors with comprehensive rewriting approach",
                ]
                
                # Add specific improvement categories based on error types
                error_types = set(error.get('type', 'unknown') for error in errors)
                if any(et in ['passive_voice', 'ambiguity', 'verbs'] for et in error_types):
                    improvements.append("Improved clarity and active voice usage")
                if any(et in ['sentence_length', 'pronouns'] for et in error_types):
                    improvements.append("Enhanced sentence structure and clarity")
                if any(et.startswith('technical_') for et in error_types):
                    improvements.append("Standardized technical formatting")
                
                logger.info(f"✅ Holistic rewrite successful: {len(errors)} errors addressed with comprehensive approach")
                
                return {
                    'rewritten_text': current_text,
                    'original_text': text,
                    'errors_fixed': len(errors),  # Assume all errors were addressed holistically
                    'confidence': holistic_confidence,
                    'processing_method': 'holistic_rewrite',
                    'density_analysis': density_analysis,
                    'improvements': improvements,
                    'holistic_approach_used': True
                }
            else:
                # Holistic rewrite failed or produced no changes
                logger.warning(f"⚠️ Holistic rewrite produced no changes for high-density text")
                
                return {
                    'rewritten_text': text,
                    'original_text': text,
                    'errors_fixed': 0,
                    'confidence': 0.2,
                    'processing_method': 'holistic_no_changes',
                    'density_analysis': density_analysis,
                    'error': 'Holistic rewrite produced no improvements',
                    'holistic_approach_used': True
                }
                
        except Exception as e:
            logger.error(f"Holistic rewrite failed: {e}")
            return {
                'rewritten_text': text,
                'original_text': text,
                'errors_fixed': 0,
                'confidence': 0.0,
                'processing_method': 'holistic_failed',
                'density_analysis': density_analysis,
                'error': f'Holistic rewrite failed: {str(e)}',
                'holistic_approach_used': True
            }
    
    def _calculate_holistic_confidence(self, density_analysis: Dict[str, Any], 
                                     error_count: int, rewrite_successful: bool) -> float:
        """
        Calculate confidence score for holistic rewriting approach.
        
        Args:
            density_analysis: Results from density analysis
            error_count: Number of errors addressed
            rewrite_successful: Whether the rewrite produced changes
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        if not rewrite_successful:
            return 0.1
        
        # Base confidence for holistic approach is typically lower than surgical
        # but higher than complex multi-instruction prompts for high-density cases
        base_confidence = 0.82
        
        # Boost confidence based on error density (higher density = more justified holistic approach)
        density_boost = min(0.15, density_analysis.get('max_density', 0) / 10.0)
        
        # Boost confidence based on number of errors addressed
        if error_count <= 3:
            error_count_boost = 0.0
        elif error_count <= 6:
            error_count_boost = 0.05
        else:
            error_count_boost = 0.10  # High error count justifies holistic approach
        
        # Penalty if only a few high-density sentences (might have been better to handle surgically)
        high_density_sentences = len(density_analysis.get('high_density_sentences', []))
        if high_density_sentences == 1:
            sentence_penalty = 0.05  # Small penalty for single sentence
        else:
            sentence_penalty = 0.0
        
        final_confidence = base_confidence + density_boost + error_count_boost - sentence_penalty
        
        logger.debug(f"🎯 Holistic confidence: base={base_confidence:.2f} + density={density_boost:.2f} + errors={error_count_boost:.2f} - penalty={sentence_penalty:.2f} = {final_confidence:.2f}")
        
        return min(0.95, max(0.1, final_confidence))  # Clamp between 0.1 and 0.95

    def _calculate_ai_confidence(self, errors: List[Dict[str, Any]], complexity: str, processing_result: Dict[str, Any] = None) -> float:
        """Calculate reward-based confidence score for AI processing."""
        if not errors:
            return 1.0
        
        # ENHANCED Base confidence by complexity with surgical boost
        base_confidence = {
            'low': 0.96,      # Simple fixes with multi-shot examples (increased)
            'surgical': 0.99, # Surgical snippet fixes (ultra-high confidence - increased)
            'medium': 0.92,   # Moderate complexity (increased)
            'high': 0.87      # Complex reasoning required (increased)
        }.get(complexity, 0.90)
        
        # ENHANCED Processing method bonus with surgical rewards
        processing_bonus = 1.0
        if processing_result:
            method = processing_result.get('processing_method', '')
            surgical_count = processing_result.get('surgical_snippets_processed', 0)
            total_attempted = processing_result.get('surgical_snippets_attempted', 0)
            
            # Surgical processing success reward
            if 'surgical' in method and surgical_count > 0 and total_attempted > 0:
                surgical_success_rate = surgical_count / total_attempted
                processing_bonus = 1.15 + (surgical_success_rate * 0.05)  # 15-20% bonus
                logger.debug(f"🎖️ Surgical success reward: {surgical_success_rate:.2f} → {processing_bonus:.3f}x")
            elif 'world_class' in method:
                processing_bonus = 1.12  # 12% bonus for processing (increased)
            elif 'comprehensive' in method:
                processing_bonus = 1.08  # 8% bonus for comprehensive processing (increased)
            elif 'station_focused' in method:
                processing_bonus = 1.06  # 6% bonus for focused processing (increased)
        
        # REWARD-BASED Error count factor - MORE ERRORS FIXED = HIGHER CONFIDENCE
        if len(errors) <= 2:
            error_count_reward = 1.0  # Baseline for small fixes
        elif len(errors) <= 5:
            error_count_reward = 1.05  # 5% bonus for moderate error fixing
        elif len(errors) <= 8:
            error_count_reward = 1.10  # 10% bonus for substantial error fixing
        else:
            error_count_reward = 1.15  # 15% bonus for extensive error fixing
        
        # SUCCESS VALIDATION BONUS
        success_bonus = 1.0
        if processing_result:
            errors_fixed = processing_result.get('surgical_snippets_processed', 0) + processing_result.get('contextual_errors_fixed', 0)
            errors_attempted = len(errors)
            
            if errors_attempted > 0:
                fix_success_rate = errors_fixed / errors_attempted
                if fix_success_rate >= 0.9:  # 90%+ success rate
                    success_bonus = 1.08  # 8% bonus for high success rate
                elif fix_success_rate >= 0.7:  # 70%+ success rate
                    success_bonus = 1.05  # 5% bonus for good success rate
                logger.debug(f"🎯 Fix success reward: {fix_success_rate:.2f} → {success_bonus:.3f}x")
        
        # QUALITY VALIDATION BONUS
        quality_bonus = 1.0
        if processing_result:
            # Check for quality indicators
            has_improvements = len(processing_result.get('improvements', [])) > 0
            is_latency_optimized = processing_result.get('latency_optimized', False)
            has_processing_time = processing_result.get('processing_time_ms', 0) > 0
            
            if has_improvements and is_latency_optimized and has_processing_time:
                quality_bonus = 1.05  # 5% bonus for high-quality processing
                logger.debug(f"✨ Quality validation bonus: {quality_bonus:.3f}x")
        
        final_confidence = base_confidence * processing_bonus * error_count_reward * success_bonus * quality_bonus
        
        # Ensure we can reach 99-100% for excellent work
        return min(1.0, final_confidence)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics including error density heuristic metrics."""
        stats = {
            'blocks_processed': self.processing_stats['blocks_processed'],
            'total_errors_fixed': self.processing_stats['errors_fixed'],
            'total_processing_time_ms': self.processing_stats['total_processing_time_ms'],
            'average_confidence': self.processing_stats['average_confidence'],
            
            # Error density heuristic metrics
            'holistic_mode_triggered': self.processing_stats['holistic_mode_triggered'],
            'holistic_mode_successful': self.processing_stats['holistic_mode_successful'],
            'high_density_sentences_detected': self.processing_stats['high_density_sentences_detected'],
            'max_density_encountered': self.processing_stats['max_density_encountered'],
            'density_analysis_time_ms': self.processing_stats['density_analysis_time_ms'],
        }
        
        if stats['blocks_processed'] > 0:
            stats['errors_per_block'] = stats['total_errors_fixed'] / stats['blocks_processed']
            stats['average_processing_time_ms'] = stats['total_processing_time_ms'] / stats['blocks_processed']
            stats['average_density_analysis_time_ms'] = stats['density_analysis_time_ms'] / stats['blocks_processed']
            
            # Holistic mode effectiveness metrics
            if stats['holistic_mode_triggered'] > 0:
                stats['holistic_success_rate'] = stats['holistic_mode_successful'] / stats['holistic_mode_triggered']
                stats['holistic_mode_percentage'] = (stats['holistic_mode_triggered'] / stats['blocks_processed']) * 100
            else:
                stats['holistic_success_rate'] = 0.0
                stats['holistic_mode_percentage'] = 0.0
                
            # Calculate holistic vs surgical ratio if we have both
            surgical_blocks = stats['blocks_processed'] - stats['holistic_mode_triggered']
            if surgical_blocks > 0:
                stats['holistic_vs_surgical_ratio'] = stats['holistic_mode_triggered'] / surgical_blocks
            else:
                stats['holistic_vs_surgical_ratio'] = float('inf') if stats['holistic_mode_triggered'] > 0 else 0.0
        else:
            stats['errors_per_block'] = 0.0
            stats['average_processing_time_ms'] = 0.0
            stats['average_density_analysis_time_ms'] = 0.0
            stats['holistic_success_rate'] = 0.0
            stats['holistic_mode_percentage'] = 0.0
            stats['holistic_vs_surgical_ratio'] = 0.0
        
        return stats
    
    def get_error_density_insights(self) -> Dict[str, Any]:
        """
        Get insights about error density patterns for system optimization.
        
        Returns:
            Dictionary with density analysis insights and recommendations
        """
        stats = self.get_processing_stats()
        
        insights = {
            'density_threshold_effectiveness': 'unknown',
            'holistic_mode_frequency': 'low',
            'recommendations': [],
            'system_performance': {}
        }
        
        # Analyze holistic mode frequency
        if stats['holistic_mode_percentage'] > 20:
            insights['holistic_mode_frequency'] = 'high'
            insights['recommendations'].append('Consider raising density thresholds to reduce holistic mode usage')
        elif stats['holistic_mode_percentage'] > 10:
            insights['holistic_mode_frequency'] = 'moderate'
            insights['recommendations'].append('Monitor holistic mode success rate for optimization opportunities')
        else:
            insights['holistic_mode_frequency'] = 'low'
            insights['recommendations'].append('Current density thresholds appear well-tuned')
        
        # Analyze effectiveness
        if stats['holistic_success_rate'] > 0.8:
            insights['density_threshold_effectiveness'] = 'excellent'
            insights['recommendations'].append('Holistic mode is highly effective when triggered')
        elif stats['holistic_success_rate'] > 0.6:
            insights['density_threshold_effectiveness'] = 'good'
            insights['recommendations'].append('Consider fine-tuning holistic prompts for better success rate')
        else:
            insights['density_threshold_effectiveness'] = 'needs_improvement'
            insights['recommendations'].append('Review holistic rewrite prompt templates and error density calculations')
        
        # Performance insights
        insights['system_performance'] = {
            'density_analysis_overhead_ms': stats['average_density_analysis_time_ms'],
            'max_density_seen': stats['max_density_encountered'],
            'high_density_detection_rate': stats['high_density_sentences_detected'],
            'processing_efficiency': 'good' if stats['average_processing_time_ms'] < 2000 else 'needs_optimization'
        }
        
        return insights




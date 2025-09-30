"""
Assembly Line Rewriter
Orchestrates the rewriting process using world-class AI multi-shot prompting.
Simplified architecture with single AI-based processing pipeline.
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
        
        # Performance tracking for world-class AI processing
        self.processing_stats = {
            'blocks_processed': 0,
            'errors_fixed': 0,
            'average_confidence': 0.0,
            'total_processing_time_ms': 0
        }
        
        logger.debug(f"⚡ World-class AI rewriter initialized with shared components")

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
        Apply world-class AI fixes to a single structural block.
        NOW WITH WORLD-CLASS REAL-TIME PROGRESS TRACKING!
        
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
            
            print(f"   🏭 Starting world-class assembly line processing")
            logger.info(f"🏭 World-class assembly line processing: {block_content[:50]}... with {len(block_errors)} errors")
            
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
            
            # Process through multi-pass assembly line with world-class AI and progress tracking
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
            
            logger.info(f"🏆 World-class assembly line processing complete: {result.get('errors_fixed', 0)}/{len(block_errors)} errors fixed in {processing_time}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"World-class AI processing failed: {e}")
            return {
                'rewritten_text': block_content,
                'improvements': [],
                'confidence': 0.0,
                'errors_fixed': 0,
                'applicable_stations': [],
                'block_type': block_type,
                'processing_method': 'ai_failed',
                'error': f'World-class AI processing failed: {str(e)}'
            }

    def _get_errors_for_station(self, errors: List[Dict[str, Any]], station: str) -> List[Dict[str, Any]]:
        """Get errors that belong to a specific assembly line station."""
        return ErrorStationMapper.get_errors_for_station(errors, station)

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
        Process text through multi-pass assembly line with world-class AI at each station.
        NOW WITH WORLD-CLASS REAL-TIME PROGRESS TRACKING!
        
        Args:
            text: Original text to process
            all_errors: All detected errors
            applicable_stations: List of stations to process (in priority order)
            block_type: Type of content block
            progress_tracker: World-class progress tracking system
            
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
            progress_tracker.start_pass(1, "World-Class AI Processing")
        
        # Process through each station in priority order
        for i, station in enumerate(applicable_stations, 1):
            station_errors = self._get_errors_for_station(all_errors, station)
            
            if not station_errors:
                continue  # Skip stations with no errors
            
            station_name = self.get_station_display_name(station)
            logger.info(f"🔧 Pass {i}/{len(applicable_stations)} - {station_name}: {len(station_errors)} errors")
            
            # Start station tracking only if enabled
            if progress_tracker:
                progress_tracker.start_station(station, station_name, len(station_errors))
            
            # Apply world-class AI for this station's errors
            station_result = self._apply_world_class_ai_fixes(current_text, station_errors, block_type, station)
            
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
                                   block_type: str = "text", station: str = None) -> Dict[str, Any]:
        """
        Apply optimal AI processing: surgical snippets for simple errors, full context for complex ones.
        
        HYBRID APPROACH:
        - Surgical snippet processing for self-contained errors (70-80% faster)
        - World-class multi-shot prompting for complex contextual errors
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
            # PHASE 1: Separate surgical candidates from contextual errors
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
                    current_text, surgical_errors, block_type
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
                    # Comprehensive world-class prompting for complex cases
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
                ai_result = self.text_generator.generate_text(prompt, current_text)
                
                if ai_result and ai_result.strip() != current_text.strip():
                    # Successful contextual AI processing
                    current_text = self.text_processor.clean_generated_text(ai_result, current_text)
                    
                    contextual_errors_fixed = len(contextual_errors)
                    total_errors_fixed += contextual_errors_fixed
                    
                    # Calculate contextual confidence
                    contextual_confidence = self._calculate_ai_confidence(contextual_errors, complexity)
                    
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
    
    def _calculate_ai_confidence(self, errors: List[Dict[str, Any]], complexity: str) -> float:
        """Calculate confidence score for AI processing."""
        if not errors:
            return 1.0
        
        # Base confidence by complexity
        base_confidence = {
            'low': 0.95,      # Simple fixes with multi-shot examples
            'surgical': 0.98, # Surgical snippet fixes (very high confidence)
            'medium': 0.88,   # Moderate complexity 
            'high': 0.82      # Complex reasoning required
        }.get(complexity, 0.85)
        
        # Adjust for error count
        error_count_factor = max(0.7, 1.0 - (len(errors) - 1) * 0.05)
        
        return min(1.0, base_confidence * error_count_factor)
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get performance statistics for the AI processing system."""
        stats = {
            'blocks_processed': self.processing_stats['blocks_processed'],
            'total_errors_fixed': self.processing_stats['errors_fixed'],
            'total_processing_time_ms': self.processing_stats['total_processing_time_ms'],
            'average_confidence': self.processing_stats['average_confidence']
        }
        
        if stats['blocks_processed'] > 0:
            stats['errors_per_block'] = stats['total_errors_fixed'] / stats['blocks_processed']
            stats['average_processing_time_ms'] = stats['total_processing_time_ms'] / stats['blocks_processed']
        else:
            stats['errors_per_block'] = 0.0
            stats['average_processing_time_ms'] = 0.0
        
        return stats




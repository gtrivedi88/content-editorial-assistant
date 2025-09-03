"""
Assembly Line Rewriter
Orchestrates the rewriting process using world-class AI multi-shot prompting.
Simplified architecture with single AI-based processing pipeline.
"""
import logging
from typing import List, Dict, Any, Optional, Callable
from .prompts import PromptGenerator
from .generators import TextGenerator
from .processors import TextProcessor
from .evaluators import RewriteEvaluator
from .station_mapper import ErrorStationMapper

logger = logging.getLogger(__name__)

class AssemblyLineRewriter:
    """
    Orchestrates a multi-level, single-pass rewriting process.
    """
    def __init__(self, text_generator: TextGenerator, text_processor: TextProcessor, progress_callback: Optional[Callable] = None):
        self.text_generator = text_generator
        self.text_processor = text_processor
        self.progress_callback = progress_callback
        self.prompt_generator = PromptGenerator()
        self.evaluator = RewriteEvaluator()
        
        # Performance tracking for world-class AI processing
        self.processing_stats = {
            'blocks_processed': 0,
            'errors_fixed': 0,
            'average_confidence': 0.0,
            'total_processing_time_ms': 0
        }
        
        logger.info(f"🚀 World-class AI rewriter initialized: Multi-shot prompting with contextual examples")

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
        Simplified architecture with pure AI multi-shot prompting.
        
        Args:
            block_content: The content of the specific block to rewrite
            block_errors: List of errors detected in this block
            block_type: Type of block (paragraph, heading, list, etc.)
            session_id: WebSocket session ID for progress updates
            block_id: UI block ID for progress tracking
            
        Returns:
            Dictionary with rewrite results
        """
        try:
            if not block_content or not block_content.strip():
                return self._empty_result()
            
            if not block_errors:
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
            
            logger.info(f"🚀 World-class AI processing: {block_content[:50]}... with {len(block_errors)} errors")
            
            # Optional progress update for start
            if self.progress_callback:
                self.progress_callback('block_processing', 'AI Analysis Starting', 
                                     f'Processing {len(block_errors)} errors in {block_type}', 10)
            
            # Get applicable stations for multi-pass processing
            applicable_stations = self.get_applicable_stations(block_errors)
            
            # Process through multi-pass assembly line with world-class AI
            result = self._process_multipass_assembly_line(block_content, block_errors, applicable_stations, block_type)
            
            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)
            self.processing_stats['total_processing_time_ms'] += processing_time
            
            # Add block-specific metadata
            result.update({
                'applicable_stations': self.get_applicable_stations(block_errors),
                'block_type': block_type,
                'original_errors': len(block_errors),
                'processing_time_ms': processing_time,
                'world_class_ai_used': True
            })
            
            # Optional progress update for completion
            if self.progress_callback:
                errors_fixed = result.get('errors_fixed', 0)
                self.progress_callback('block_processing', 'AI Processing Complete', 
                                     f'Fixed {errors_fixed}/{len(block_errors)} errors in {block_type}', 100)
            
            logger.info(f"✅ World-class AI processing complete: {result.get('errors_fixed', 0)}/{len(block_errors)} errors fixed in {processing_time}ms")
            
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

    def _process_through_assembly_line_stations(self, content: str, errors: List[Dict[str, Any]], 
                                              stations: List[str], session_id: str, block_id: str, 
                                              block_type: str) -> Dict[str, Any]:
        """
        Process content through assembly line stations with live progress updates.
        """
        try:
            # Import here to avoid circular imports
            from app_modules.websocket_handlers import emit_station_progress_update
            
            current_content = content
            all_improvements = []
            total_errors_fixed = 0
            
            for i, station in enumerate(stations):
                station_name = self.get_station_display_name(station)
                
                # Get errors for this station
                station_errors = self._get_errors_for_station(errors, station)
                if not station_errors:
                    continue
                
                # Emit processing start for this station
                if session_id and block_id:
                    emit_station_progress_update(
                        session_id, block_id, station, 'processing',
                        preview_text=f"Processing {len(station_errors)} {station} issue(s)..."
                    )
                
                logger.info(f"🏭 Station {station_name}: Processing {len(station_errors)} errors")
                
                # Process errors through this station (simulate real assembly line work)
                import time
                time.sleep(0.5)  # Simulate processing time for live UI updates
                
                station_result = self.rewrite_sentence(current_content, station_errors, pass_number=1)
                
                # Update content for next station
                current_content = station_result.get('rewritten_text', current_content)
                all_improvements.extend(station_result.get('improvements', []))
                total_errors_fixed += station_result.get('errors_fixed', 0)
                
                # Generate preview text for UI
                preview_text = self._generate_station_preview(station, station_errors, current_content)
                
                # POST-REWRITE VALIDATION: Check for AI-introduced ambiguities (lightweight)
                validation_concerns = []
                if station in ['urgent', 'high']:  # Only validate critical fixes
                    validation_concerns = self._validate_rewrite_quality(
                        original_content=content, 
                        rewritten_content=current_content,
                        original_errors=station_errors
                    )
                
                # Emit completion for this station (include validation status)
                if session_id and block_id:
                    # Add validation warning to preview if concerns found
                    final_preview = preview_text
                    if validation_concerns:
                        final_preview += f" ⚠️ {len(validation_concerns)} validation concern(s)"
                    
                    emit_station_progress_update(
                        session_id, block_id, station, 'complete',
                        preview_text=final_preview
                    )
                
                logger.info(f"✅ Station {station_name}: Complete ({station_result.get('errors_fixed', 0)} fixes)")
                if validation_concerns:
                    logger.warning(f"⚠️ Validation concerns for {station_name}: {validation_concerns}")
            
            return {
                'rewritten_text': current_content,
                'improvements': all_improvements,
                'confidence': 0.85,  # High confidence for assembly line processing
                'errors_fixed': total_errors_fixed
            }
            
        except Exception as e:
            logger.error(f"Assembly line station processing failed: {e}")
            # Fallback to single-pass processing
            return self.rewrite_sentence(content, errors, pass_number=1)

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
                                       applicable_stations: List[str], block_type: str = "text") -> Dict[str, Any]:
        """
        Process text through multi-pass assembly line with world-class AI at each station.
        Each pass focuses on specific priority levels for better results.
        
        Args:
            text: Original text to process
            all_errors: All detected errors
            applicable_stations: List of stations to process (in priority order)
            block_type: Type of content block
            
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
        
        # Process through each station in priority order
        for i, station in enumerate(applicable_stations, 1):
            station_errors = self._get_errors_for_station(all_errors, station)
            
            if not station_errors:
                continue  # Skip stations with no errors
            
            logger.info(f"🔧 Pass {i}/{len(applicable_stations)} - {station} station: {len(station_errors)} errors")
            
            # Progress callback for each pass
            if self.progress_callback:
                station_name = self.get_station_display_name(station)
                progress = int((i / len(applicable_stations)) * 90)  # 90% max, leaving 10% for final
                self.progress_callback('station_processing', f'{station_name}', 
                                     f'Processing {len(station_errors)} errors', progress)
            
            # Apply world-class AI for this station's errors
            station_result = self._apply_world_class_ai_fixes(current_text, station_errors, block_type, station)
            
            if station_result.get('rewritten_text') and station_result['rewritten_text'] != current_text:
                # Success at this station
                current_text = station_result['rewritten_text']
                errors_fixed_this_pass = station_result.get('errors_fixed', 0)
                total_errors_fixed += errors_fixed_this_pass
                
                # Determine input text (original text for first pass, previous output for others)
                input_text = text if len(pass_results) == 0 else pass_results[-1]['output_text']
                
                pass_results.append({
                    'station': station,
                    'station_name': self.get_station_display_name(station),
                    'errors_processed': len(station_errors),
                    'errors_fixed': errors_fixed_this_pass,
                    'confidence': station_result.get('confidence', 0.8),
                    'input_text': input_text,
                    'output_text': current_text,
                    'processing_method': station_result.get('processing_method', 'world_class_ai')
                })
                
                # Update overall confidence (weighted average)
                overall_confidence = (overall_confidence + station_result.get('confidence', 0.8)) / 2
                
                logger.info(f"✅ {station} pass: {errors_fixed_this_pass} errors fixed, confidence: {station_result.get('confidence', 0.8):.2f}")
            else:
                # No changes at this station
                input_text = text if len(pass_results) == 0 else pass_results[-1]['output_text']
                
                pass_results.append({
                    'station': station,
                    'station_name': self.get_station_display_name(station),
                    'errors_processed': len(station_errors),
                    'errors_fixed': 0,
                    'confidence': 0.1,
                    'input_text': input_text,
                    'output_text': current_text,
                    'processing_method': 'ai_no_changes'
                })
                
                logger.warning(f"⚠️ {station} pass: No changes made")
        
        # Calculate final confidence and statistics
        passes_with_changes = [p for p in pass_results if p['errors_fixed'] > 0]
        final_confidence = sum(p['confidence'] for p in passes_with_changes) / len(passes_with_changes) if passes_with_changes else 0.5
        
        return {
            'rewritten_text': current_text,
            'original_text': text,
            'errors_fixed': total_errors_fixed,
            'confidence': final_confidence,
            'processing_method': 'multipass_assembly_line',
            'passes_completed': len(applicable_stations),
            'passes_with_changes': len(passes_with_changes),
            'pass_results': pass_results
        }

    def _apply_world_class_ai_fixes(self, text: str, errors: List[Dict[str, Any]], 
                                   block_type: str = "text", station: str = None) -> Dict[str, Any]:
        """
        Apply world-class AI multi-shot prompting to fix errors at a specific station.
        Creates focused, station-specific prompts for better results.
        
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
            # Assess complexity to choose optimal prompting strategy
            complexity = self._assess_error_complexity(errors)
            
            if station:
                # Create station-specific prompt for focused multi-pass processing
                station_name = self.get_station_display_name(station)
                prompt = self.prompt_generator.create_station_focused_prompt(
                    text, errors, station, station_name, block_type
                )
                prompt_type = f'station_focused_{station}'
            elif complexity == 'high' or len(errors) > 3:
                # Use comprehensive world-class prompting for complex cases
                prompt = self.prompt_generator.create_world_class_multi_shot_prompt(
                    text, errors, block_type
                )
                prompt_type = 'world_class_comprehensive'
            else:
                # Use enhanced multi-shot prompting for simpler cases
                prompt = self.prompt_generator.create_assembly_line_prompt(
                    text, errors, 1, block_type
                )
                prompt_type = 'enhanced_multi_shot'
            
            # Generate AI correction
            ai_result = self.text_generator.generate_text(prompt, text)
            
            if ai_result and ai_result.strip() != text.strip():
                # Successful AI processing
                final_text = self.text_processor.clean_generated_text(ai_result, text)
                
                # Calculate confidence based on complexity and error coverage
                confidence = self._calculate_ai_confidence(errors, complexity)
                
                # Update stats
                self.processing_stats['errors_fixed'] += len(errors)
                
                return {
                    'rewritten_text': final_text,
                    'original_text': text,
                    'errors_fixed': len(errors),
                    'confidence': confidence,
                    'processing_method': 'world_class_ai',
                    'prompt_type': prompt_type,
                    'complexity': complexity,
                    'error_count': len(errors)
                }
            else:
                # AI returned same text or failed
                logger.warning(f"AI processing returned unchanged text for {len(errors)} errors")
                return {
                    'rewritten_text': text,
                    'original_text': text,
                    'errors_fixed': 0,
                    'confidence': 0.1,
                    'processing_method': 'ai_no_changes',
                    'prompt_type': prompt_type,
                    'complexity': complexity
                }
                
        except Exception as e:
            logger.error(f"AI processing failed: {e}")
            return {
                'rewritten_text': text,
                'original_text': text,
                'errors_fixed': 0,
                'confidence': 0.0,
                'processing_method': 'ai_failed',
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
        
        # High complexity indicators
        high_complexity_types = {
            'ambiguity', 'passive_voice', 'sentence_length', 
            'legal_claims', 'tone', 'readability', 'subjunctive_mood'
        }
        
        # Medium complexity indicators  
        medium_complexity_types = {
            'word_usage_y', 'citations', 'anthropomorphism',
            'headings'  # Can be complex with technical terms
        }
        
        high_count = sum(1 for error in errors 
                        if error.get('type', '') in high_complexity_types)
        medium_count = sum(1 for error in errors 
                          if error.get('type', '') in medium_complexity_types)
        
        # Complexity scoring
        if high_count > 0 or len(errors) > 4:
            return 'high'
        elif medium_count > 1 or len(errors) > 2:
            return 'medium' 
        else:
            return 'low'
    
    def _calculate_ai_confidence(self, errors: List[Dict[str, Any]], complexity: str) -> float:
        """Calculate confidence score for AI processing."""
        if not errors:
            return 1.0
        
        # Base confidence by complexity
        base_confidence = {
            'low': 0.95,      # Simple fixes with multi-shot examples
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



    def _split_into_sentences(self, content: str) -> List[str]:
        """Split content into sentences using robust spaCy sentence segmentation."""
        try:
            import spacy
            # Try to load the existing spaCy model used elsewhere in the system
            nlp = spacy.load("en_core_web_sm")
            doc = nlp(content.strip())
            
            # Extract sentences using spaCy's robust sentence boundary detection
            sentences = [sent.text.strip() for sent in doc.sents if sent.text.strip()]
            return sentences
            
        except (ImportError, OSError) as e:
            # Fallback to regex if spaCy is not available
            import re
            logger.warning(f"spaCy not available, using regex fallback: {e}")
            sentences = re.split(r'(?<=[.!?])\s+', content.strip())
            return [s.strip() for s in sentences if s.strip()]
    
    def _get_errors_for_sentence(self, sentence: str, all_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter errors that apply to this specific sentence."""
        sentence_errors = []
        for error in all_errors:
            # Check if error applies to this sentence (simple matching)
            flagged_text = error.get('flagged_text', '')
            if not flagged_text or flagged_text.lower() in sentence.lower():
                sentence_errors.append(error)
        return sentence_errors

    def rewrite_sentence(self, sentence: str, errors: List[Dict[str, Any]], pass_number: int = 1) -> Dict[str, Any]:
        """
        Rewrites a single sentence using a comprehensive, single-pass approach.

        Args:
            sentence: The original sentence to rewrite.
            errors: A list of all errors found in the sentence.
            pass_number: The pass number (1 for initial fix, 2 for refinement).

        Returns:
            A dictionary containing the rewritten sentence and analysis.
        """
        if not sentence or not sentence.strip():
            return self._empty_result()

        if pass_number == 1:
            # First pass: Fix all specific errors in one go.
            return self._perform_first_pass(sentence, errors)
        else:
            # Second pass: Perform a holistic refinement.
            return self._perform_refinement_pass(sentence)

    def _perform_first_pass(self, sentence: str, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Handles the primary error-correction pass."""
        if not errors:
            logger.info("No errors found for sentence, skipping rewrite.")
            return {
                'rewritten_text': sentence,
                'improvements': [],
                'confidence': 1.0,
                'errors_fixed': 0
            }

        # Sort all errors by their priority level using our internal method.
        sorted_errors = self._sort_errors_by_priority(errors)
        
        # Create a single, comprehensive prompt with all sorted errors.
        prompt = self.prompt_generator.create_assembly_line_prompt(sentence, sorted_errors, pass_number=1)
        
        logger.debug(f"Generated single-pass prompt for sentence: {sentence}")
        
        # FIXED: Use correct method name and parameters
        ai_response = self.text_generator.generate_text(prompt, sentence)

        if not ai_response or not ai_response.strip():
            logger.warning("AI model returned an empty response.")
            return self._error_result(sentence, "AI model returned an empty response.")

        # FIXED: Use text processor to clean the response (integrates with OutputEnforcer)
        cleaned_response = self.text_processor.clean_generated_text(ai_response, sentence)

        # FIXED: Use correct method name and handle return value properly
        evaluation = self.evaluator.evaluate_rewrite_quality(sentence, cleaned_response, errors)

        return {
            'rewritten_text': cleaned_response,  # Use the cleaned response directly
            'improvements': evaluation.get('improvements', []),
            'confidence': evaluation.get('confidence', 0.75),
            'errors_fixed': len(sorted_errors)  # Count of errors we attempted to fix
        }

    def _perform_refinement_pass(self, sentence: str) -> Dict[str, Any]:
        """Handles the second, holistic refinement pass."""
        prompt = self.prompt_generator.create_assembly_line_prompt(sentence, [], pass_number=2)
        
        logger.debug(f"Generated refinement prompt for sentence: {sentence}")

        # FIXED: Use correct method name and parameters
        ai_response = self.text_generator.generate_text(prompt, sentence)

        if not ai_response or not ai_response.strip():
            logger.warning("AI model returned an empty response during refinement.")
            return self._error_result(sentence, "AI model returned an empty response during refinement.")

        # FIXED: Use text processor to clean the response (integrates with OutputEnforcer)
        cleaned_response = self.text_processor.clean_generated_text(ai_response, sentence)

        return {
            'rewritten_text': cleaned_response,
            'improvements': ["Holistic refinement for clarity and flow."],
            'confidence': 0.9,
            'errors_fixed': 0  # No specific errors are targeted in this pass
        }

    def _empty_result(self) -> Dict[str, Any]:
        """Returns a standard result for empty input."""
        return {'rewritten_text': '', 'improvements': [], 'confidence': 0.0, 'errors_fixed': 0}

    def _error_result(self, original_text: str, error_message: str) -> Dict[str, Any]:
        """Returns a standard result when an error occurs."""
        return {
            'rewritten_text': original_text,
            'improvements': [],
            'confidence': 0.0,
            'errors_fixed': 0,
            'error': error_message
        }

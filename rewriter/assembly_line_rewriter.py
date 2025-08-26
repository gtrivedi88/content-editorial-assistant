"""
Assembly Line Rewriter
Orchestrates the rewriting process by applying fixes in prioritized levels.
"""
import logging
from typing import List, Dict, Any, Optional, Callable
from .prompts import PromptGenerator
from .generators import TextGenerator
from .processors import TextProcessor
from .evaluators import RewriteEvaluator

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
        Apply assembly line fixes to a single structural block with live progress updates.
        
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
                    'block_type': block_type
                }
            
            # Get applicable stations for this block's errors
            applicable_stations = self.get_applicable_stations(block_errors)
            
            # Sort errors by priority for optimal processing order
            sorted_errors = self._sort_errors_by_priority(block_errors)
            
            # Process block content through assembly line with live station updates
            result = self._process_through_assembly_line_stations(
                block_content, sorted_errors, applicable_stations, 
                session_id, block_id, block_type
            )
            
            # Add block-specific metadata
            result.update({
                'applicable_stations': applicable_stations,
                'block_type': block_type,
                'original_errors': len(block_errors),
                'assembly_line_used': True
            })
            
            if self.progress_callback:
                self.progress_callback('block_processing', f'Block rewrite complete', 
                                     f'Fixed {result.get("errors_fixed", 0)} errors in {block_type}', 100)
            
            logger.info(f"✅ Block rewrite complete: {result.get('errors_fixed', 0)}/{len(block_errors)} errors fixed")
            
            return result
            
        except Exception as e:
            logger.error(f"Block assembly line processing failed: {e}")
            return {
                'rewritten_text': block_content,
                'improvements': [],
                'confidence': 0.0,
                'errors_fixed': 0,
                'applicable_stations': [],
                'block_type': block_type,
                'error': f'Block assembly line processing failed: {str(e)}'
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
        station_errors = []
        
        for error in errors:
            error_type = error.get('type', '')
            
            # Check if this error belongs to this station
            if station == 'urgent' and error_type in ['legal_claims', 'legal_company_names', 'legal_personal_information', 'inclusive_language', 'second_person']:
                station_errors.append(error)
            elif station == 'high' and error_type in ['passive_voice', 'sentence_length', 'subjunctive_mood', 'verbs', 'headings', 'ambiguity']:
                station_errors.append(error)
            elif station == 'medium' and (error_type.startswith('word_usage_') or error_type.startswith('technical_') or
                  error_type in ['contractions', 'spelling', 'terminology', 'anthropomorphism', 'capitalization', 'prefixes', 'plurals', 'abbreviations']):
                station_errors.append(error)
            elif station == 'low' and (error_type.startswith('punctuation_') or error_type.startswith('references_') or
                  error_type in ['tone', 'citations', 'currency']):
                station_errors.append(error)
        
        return station_errors

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
        
        stations_needed = set()
        
        for error in block_errors:
            error_type = error.get('type', '')
            
            # Map error types to assembly line stations based on assembly_line_config.yaml
            if error_type in ['legal_claims', 'legal_company_names', 'legal_personal_information', 'inclusive_language', 'second_person']:
                stations_needed.add('urgent')
            elif error_type in ['passive_voice', 'sentence_length', 'subjunctive_mood', 'verbs', 'headings', 'ambiguity']:
                stations_needed.add('high')
            elif (error_type.startswith('word_usage_') or error_type.startswith('technical_') or
                  error_type in ['contractions', 'spelling', 'terminology', 'anthropomorphism', 'capitalization', 'prefixes', 'plurals', 'abbreviations']):
                stations_needed.add('medium')
            elif (error_type.startswith('punctuation_') or error_type.startswith('references_') or
                  error_type in ['tone', 'citations', 'currency']):
                stations_needed.add('low')
        
        # Return in priority order
        priority_order = ['urgent', 'high', 'medium', 'low']
        return [station for station in priority_order if station in stations_needed]

    def get_station_display_name(self, station: str) -> str:
        """Get user-friendly display name for assembly line station."""
        
        station_names = {
            'urgent': 'Critical/Legal Pass',
            'high': 'Structural Pass', 
            'medium': 'Grammar Pass',
            'low': 'Style Pass'
        }
        
        return station_names.get(station, 'Processing Pass')



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

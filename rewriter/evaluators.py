"""
Evaluation Module
Handles confidence calculation and improvement extraction for AI rewrites.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Import enhanced confidence calculation system
try:
    from validation.confidence.confidence_calculator import ConfidenceCalculator
    ENHANCED_CONFIDENCE_AVAILABLE = True
except ImportError:
    ENHANCED_CONFIDENCE_AVAILABLE = False


class RewriteEvaluator:
    """Evaluates rewrite quality and extracts improvements.
    Cached confidence calculations."""
    
    def __init__(self):
        """Initialize the rewrite evaluator with performance optimizations."""
        if ENHANCED_CONFIDENCE_AVAILABLE:
            self.confidence_calculator = ConfidenceCalculator()
        else:
            self.confidence_calculator = None
        
        # Simple confidence cache for repeated calculations
        self._confidence_cache = {}
        self._cache_max_size = 100
    
    def calculate_confidence(self, original: str, rewritten: str, errors: List[Dict[str, Any]], 
                           use_ollama: bool = True, pass_number: int = 1) -> float:
        """Calculate confidence score for the rewrite using enhanced validation system.
        Cached calculations for similar inputs."""
        try:
            # Create cache key for similar calculations
            cache_key = self._create_confidence_cache_key(original, rewritten, errors, use_ollama, pass_number)
            
            if cache_key in self._confidence_cache:
                logger.debug("⚡ Using cached confidence calculation")
                return self._confidence_cache[cache_key]
            
            # Calculate confidence
            if self.confidence_calculator:
                confidence = self._calculate_enhanced_confidence(original, rewritten, errors, use_ollama, pass_number)
            else:
                confidence = self._calculate_fallback_confidence(original, rewritten, errors, use_ollama, pass_number)
            
            # Cache result (with size limit)
            if len(self._confidence_cache) >= self._cache_max_size:
                # Simple cache eviction: remove oldest entries
                oldest_keys = list(self._confidence_cache.keys())[:20]
                for key in oldest_keys:
                    del self._confidence_cache[key]
            
            self._confidence_cache[cache_key] = confidence
            return confidence
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5 if pass_number == 1 else 0.8
    
    def calculate_second_pass_confidence(self, first_pass: str, final_rewrite: str, 
                                       errors: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for second pass refinement."""
        try:
            # Use the enhanced confidence calculation for second pass
            return self.calculate_confidence(
                original=first_pass,
                rewritten=final_rewrite,
                errors=errors,
                use_ollama=True,  # Assume second pass uses reliable model
                pass_number=2
            )
            
        except Exception as e:
            logger.error(f"Error calculating second pass confidence: {e}")
            return 0.8  # Default high confidence for second pass
    
    def _calculate_enhanced_confidence(self, original: str, rewritten: str, errors: List[Dict[str, Any]], 
                                     use_ollama: bool, pass_number: int) -> float:
        """Calculate confidence using the enhanced ConfidenceCalculator system."""
        # Use normalized confidence calculation for rewrite quality assessment
        
        # Determine the primary rule type based on errors addressed
        rule_type = self._determine_primary_rule_type(errors)
        
        # Calculate normalized confidence for the rewritten text
        rewrite_confidence = self.confidence_calculator.calculate_normalized_confidence(
            text=rewritten,
            error_position=len(rewritten) // 2,  # Middle of text for general assessment
            rule_type=rule_type,
            content_type=None,  # Auto-detect content type
            base_confidence=0.5
        )
        
        # Apply rewrite-specific modifiers
        rewrite_confidence = self._apply_rewrite_modifiers(
            rewrite_confidence, original, rewritten, errors, use_ollama, pass_number
        )
        
        return max(0.0, min(1.0, rewrite_confidence))
    
    def _create_confidence_cache_key(self, original: str, rewritten: str, errors: List[Dict[str, Any]], 
                                   use_ollama: bool, pass_number: int) -> str:
        """Create a cache key for confidence calculations."""
        # Simple hashing based on text lengths and error count for performance
        error_types = tuple(sorted(error.get('type', '') for error in errors[:5]))  # Limit for performance
        return f"{len(original)}_{len(rewritten)}_{len(errors)}_{use_ollama}_{pass_number}_{hash(error_types) % 10000}"
    
    def _calculate_fallback_confidence(self, original: str, rewritten: str, errors: List[Dict[str, Any]], 
                                     use_ollama: bool, pass_number: int) -> float:
        """Fallback confidence calculation when enhanced system not available."""
        base_confidence = 0.6  # Conservative base confidence
        
        # Model quality modifier
        if use_ollama and rewritten != original:
            base_confidence += 0.2
        elif not use_ollama and rewritten != original:
            base_confidence += 0.1
        
        # Error count modifier
        if errors:
            base_confidence += min(0.1, len(errors) * 0.02)
        
        # Change penalty
        if rewritten == original:
            base_confidence -= 0.2
        
        # Pass number bonus
        if pass_number == 2:
            base_confidence += 0.1
            
        return max(0.0, min(1.0, base_confidence))
    
    def _determine_primary_rule_type(self, errors: List[Dict[str, Any]]) -> str:
        """Determine the primary rule type from addressed errors."""
        if not errors:
            return 'grammar'  # Default to grammar for general text improvement
        
        # Count rule types in errors
        rule_counts = {}
        for error in errors:
            rule_type = error.get('type', 'grammar')
            rule_counts[rule_type] = rule_counts.get(rule_type, 0) + 1
        
        # Return most common rule type
        return max(rule_counts, key=rule_counts.get) if rule_counts else 'grammar'
    
    def _apply_rewrite_modifiers(self, base_confidence: float, original: str, rewritten: str, 
                               errors: List[Dict[str, Any]], use_ollama: bool, pass_number: int) -> float:
        """Apply rewrite-specific confidence modifiers."""
        confidence = base_confidence
        
        # Model quality modifier (Ollama generally more reliable)
        if use_ollama and rewritten != original:
            confidence *= 1.2  # 20% boost for Ollama
        elif not use_ollama and rewritten != original:
            confidence *= 1.1  # 10% boost for external models
        
        # Change quality assessment
        if rewritten == original:
            confidence *= 0.7  # Penalize no changes
        else:
            # Length ratio quality check
            original_length = len(original.split())
            rewritten_length = len(rewritten.split())
            
            if original_length > 0:
                length_ratio = rewritten_length / original_length
                if 0.8 <= length_ratio <= 1.2:  # Reasonable length change
                    confidence *= 1.05  # Small boost for reasonable changes
                elif length_ratio > 1.5 or length_ratio < 0.5:  # Extreme changes
                    confidence *= 0.9  # Small penalty for extreme changes
        
        # Multi-pass bonus
        if pass_number == 2:
            confidence *= 1.1  # 10% boost for second pass refinement
        
        return confidence
    
    def extract_improvements(self, original: str, rewritten: str, errors: List[Dict[str, Any]]) -> List[str]:
        """Extract and describe the improvements made."""
        improvements = []
        
        original_words = len(original.split())
        rewritten_words = len(rewritten.split())
        
        if rewritten_words < original_words:
            improvements.append(f"Reduced word count from {original_words} to {rewritten_words}")
        
        error_types = set(error.get('type', '') for error in errors)
        
        if 'passive_voice' in error_types:
            improvements.append("Converted passive voice to active voice")
        
        if 'sentence_length' in error_types:
            improvements.append("Shortened overly long sentences")
        
        if 'conciseness' in error_types:
            improvements.append("Removed wordy phrases")
        
        if 'clarity' in error_types:
            improvements.append("Replaced complex words with simpler alternatives")
        
        if not improvements:
            improvements.append("Applied general style improvements")
        
        return improvements
    
    def extract_second_pass_improvements(self, first_rewrite: str, final_rewrite: str) -> List[str]:
        """Extract improvements made in the second pass."""
        improvements = []
        
        # Compare lengths
        first_words = len(first_rewrite.split())
        final_words = len(final_rewrite.split())
        
        if final_words < first_words:
            improvements.append(f"Second pass: Further reduced word count by {first_words - final_words} words")
        elif final_words > first_words:
            improvements.append(f"Second pass: Enhanced clarity with {final_words - first_words} additional words")
        
        # Check for structural improvements
        first_sentences = len([s for s in first_rewrite.split('.') if s.strip()])
        final_sentences = len([s for s in final_rewrite.split('.') if s.strip()])
        
        if final_sentences > first_sentences:
            improvements.append("Second pass: Improved sentence structure and flow")
        
        # Check for word choice improvements
        if first_rewrite.lower() != final_rewrite.lower():
            improvements.append("Second pass: Refined word choice and phrasing")
        
        # Default improvement if text changed
        if not improvements and first_rewrite != final_rewrite:
            improvements.append("Second pass: Applied additional polish and refinements")
        
        return improvements if improvements else ["Second pass: Minor refinements applied"]
    
    def analyze_changes(self, original: str, rewritten: str) -> Dict[str, Any]:
        """
        Analyze the changes made between original and rewritten text.
        
        Args:
            original: Original text
            rewritten: Rewritten text
            
        Returns:
            Dictionary with change analysis
        """
        analysis = {
            'word_count_change': 0,
            'sentence_count_change': 0,
            'length_ratio': 0.0,
            'significant_change': False,
            'structural_changes': []
        }
        
        try:
            # Word count analysis
            original_words = len(original.split())
            rewritten_words = len(rewritten.split())
            analysis['word_count_change'] = rewritten_words - original_words
            
            if original_words > 0:
                analysis['length_ratio'] = rewritten_words / original_words
            
            # Sentence count analysis
            original_sentences = len([s for s in original.split('.') if s.strip()])
            rewritten_sentences = len([s for s in rewritten.split('.') if s.strip()])
            analysis['sentence_count_change'] = rewritten_sentences - original_sentences
            
            # Determine if change is significant
            analysis['significant_change'] = (
                abs(analysis['word_count_change']) > 2 or
                analysis['sentence_count_change'] != 0 or
                original.lower().strip() != rewritten.lower().strip()
            )
            
            # Detect structural changes
            if analysis['word_count_change'] < -5:
                analysis['structural_changes'].append("Significant word reduction")
            elif analysis['word_count_change'] > 5:
                analysis['structural_changes'].append("Text expansion")
                
            if analysis['sentence_count_change'] > 0:
                analysis['structural_changes'].append("Sentence splitting")
            elif analysis['sentence_count_change'] < 0:
                analysis['structural_changes'].append("Sentence combining")
            
        except Exception as e:
            logger.error(f"Error analyzing changes: {e}")
        
        return analysis
    
    def evaluate_rewrite_quality(self, original: str, rewritten: str, errors: List[Dict[str, Any]], 
                                use_ollama: bool = True, pass_number: int = 1) -> Dict[str, Any]:
        """
        Comprehensive evaluation of rewrite quality with negative example intelligence.
        Understands when "no change" is the correct, high-quality response.
        
        Args:
            original: Original text
            rewritten: Rewritten text  
            errors: List of detected errors
            use_ollama: Whether Ollama was used
            pass_number: 1 for first pass, 2 for second pass
            
        Returns:
            Dictionary with comprehensive evaluation including no-change intelligence
        """
        try:
            # Check if this is a "no change" scenario and if it's appropriate
            no_change_evaluation = self._evaluate_no_change_appropriateness(original, rewritten, errors)
            
            confidence = self.calculate_confidence(original, rewritten, errors, use_ollama, pass_number)
            improvements = self.extract_improvements(original, rewritten, errors)
            changes = self.analyze_changes(original, rewritten)
            
            # Adjust evaluation for appropriate no-change scenarios
            if no_change_evaluation['is_no_change'] and no_change_evaluation['is_appropriate']:
                # Boost confidence for correctly identifying when not to change
                confidence = max(confidence, 0.85)
                improvements.extend(no_change_evaluation['reasoning'])
                changes['no_change_intelligence'] = True
            
            evaluation = {
                'confidence': confidence,
                'improvements': improvements,
                'changes_analysis': changes,
                'quality_score': self._calculate_quality_score(confidence, changes, errors),
                'pass_number': pass_number,
                'model_used': 'ollama' if use_ollama else 'huggingface',
                'no_change_analysis': no_change_evaluation
            }
            
            return evaluation
            
        except Exception as e:
            logger.error(f"Error evaluating rewrite quality: {e}")
            return {
                'confidence': 0.5,
                'improvements': ["Evaluation failed"],
                'changes_analysis': {},
                'quality_score': 0.5,
                'pass_number': pass_number,
                'model_used': 'unknown',
                'no_change_analysis': {'is_no_change': False, 'is_appropriate': False}
            }
    
    def _evaluate_no_change_appropriateness(self, original: str, rewritten: str, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate whether "no change" was the appropriate response using negative example intelligence.
        
        Returns:
            Dictionary with no-change analysis
        """
        is_no_change = original.strip() == rewritten.strip()
        
        if not is_no_change:
            return {'is_no_change': False, 'is_appropriate': False, 'reasoning': []}
        
        reasoning = []
        is_appropriate = False
        
        # Check for contextual appropriateness patterns
        original_lower = original.lower()
        
        # Pattern 1: Passive voice in appropriate contexts
        if any(error.get('type') == 'passive_voice' for error in errors):
            if any(pattern in original_lower for pattern in [
                'was corrupted', 'was designed', 'are performed', 'was completed',
                'was interrupted', 'are generated', 'is processed'
            ]):
                is_appropriate = True
                reasoning.append("Passive voice appropriate in technical/system context")
        
        # Pattern 2: Word usage in appropriate contexts  
        if any(error.get('type', '').startswith('word_usage') for error in errors):
            if 'simple solution' in original_lower or 'click the' in original_lower:
                is_appropriate = True
                reasoning.append("Word usage appropriate for UI instructions or comparisons")
        
        # Pattern 3: Second person in user-focused contexts
        if any(error.get('type') == 'second_person' for error in errors):
            if any(pattern in original_lower for pattern in [
                'you can customize', 'your data', 'if you encounter', 'your session'
            ]):
                is_appropriate = True
                reasoning.append("Second person necessary for user-specific instructions")
        
        # Pattern 4: Contractions in appropriate informal contexts
        if any(error.get('type') == 'contractions' for error in errors):
            if any(pattern in original_lower for pattern in [
                "we're here to help", "don't forget", "it's working"
            ]):
                is_appropriate = True  
                reasoning.append("Contractions appropriate for friendly, approachable tone")
        
        # Pattern 5: Technical formatting in conversational contexts
        if any(error.get('type', '').startswith('technical_') for error in errors):
            if '/etc/' in original and '`' not in original:
                is_appropriate = True
                reasoning.append("Informal file path formatting appropriate in conversational support")
        
        # Pattern 6: Tone in security/critical contexts  
        if any(error.get('type') == 'tone' for error in errors):
            if any(pattern in original_lower for pattern in [
                'absolutely critical', 'must complete', 'cannot be ignored'
            ]):
                is_appropriate = True
                reasoning.append("Strong tone appropriate for security warnings and critical instructions")
        
        return {
            'is_no_change': True,
            'is_appropriate': is_appropriate,
            'reasoning': reasoning,
            'patterns_detected': len(reasoning)
        }
    
    def _calculate_quality_score(self, confidence: float, changes: Dict[str, Any], 
                               errors: List[Dict[str, Any]]) -> float:
        """Calculate an overall quality score for the rewrite with no-change intelligence."""
        try:
            quality_score = confidence * 0.6  # Confidence contributes 60%
            
            # Special handling for appropriate no-change scenarios
            if changes.get('no_change_intelligence', False):
                # High score for correctly identifying when not to change
                return min(0.95, confidence * 1.1)
            
            # Bonus for making significant changes
            if changes.get('significant_change', False):
                quality_score += 0.2
            
            # Bonus based on number of errors addressed
            if errors:
                error_bonus = min(0.2, len(errors) * 0.05)
                quality_score += error_bonus
            
            # Penalty for extreme length changes
            length_ratio = changes.get('length_ratio', 1.0)
            if length_ratio > 2.0 or length_ratio < 0.3:
                quality_score -= 0.1
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 0.5 
"""
Evaluation Module
Handles confidence calculation and improvement extraction for AI rewrites.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class RewriteEvaluator:
    """Evaluates rewrite quality and extracts improvements."""
    
    def __init__(self):
        """Initialize the rewrite evaluator."""
        pass
    
    def calculate_confidence(self, original: str, rewritten: str, errors: List[Dict[str, Any]], 
                           use_ollama: bool = True, pass_number: int = 1) -> float:
        """Calculate confidence score for the rewrite."""
        try:
            if pass_number == 1:
                confidence = 0.7
            else:
                confidence = 0.7  # Start with higher confidence for second pass
                # Bonus for completing second pass
                confidence += 0.2
            
            # Higher confidence for Ollama (local model)
            if use_ollama and rewritten != original:
                confidence += 0.3
            elif not use_ollama and rewritten != original:
                confidence += 0.2
            
            # Adjust based on number of errors addressed
            if errors:
                confidence += min(0.1, len(errors) * 0.02)
            
            # Penalize if no changes were made
            if rewritten == original:
                confidence -= 0.3
            
            # Check length ratio
            original_length = len(original.split())
            rewritten_length = len(rewritten.split())
            
            if original_length > 0:
                length_ratio = rewritten_length / original_length
                if length_ratio > 1.5 or length_ratio < 0.5:
                    confidence -= 0.2
            
            # Additional bonus for second pass
            if pass_number == 2:
                confidence += 0.1
            
            return max(0.0, min(1.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating confidence: {e}")
            return 0.5 if pass_number == 1 else 0.8
    
    def calculate_second_pass_confidence(self, first_pass: str, final_rewrite: str, 
                                       errors: List[Dict[str, Any]]) -> float:
        """Calculate confidence score for second pass refinement."""
        try:
            base_confidence = 0.7  # Start with higher confidence for second pass
            
            # Bonus for completing second pass
            base_confidence += 0.2
            
            # Check if second pass made meaningful changes
            if final_rewrite != first_pass:
                base_confidence += 0.1
            
            # Adjust based on number of original errors addressed
            if errors:
                base_confidence += min(0.1, len(errors) * 0.02)
            
            return max(0.0, min(1.0, base_confidence))
            
        except Exception as e:
            logger.error(f"Error calculating second pass confidence: {e}")
            return 0.8  # Default high confidence for second pass
    
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
        Comprehensive evaluation of rewrite quality.
        
        Args:
            original: Original text
            rewritten: Rewritten text  
            errors: List of detected errors
            use_ollama: Whether Ollama was used
            pass_number: 1 for first pass, 2 for second pass
            
        Returns:
            Dictionary with comprehensive evaluation
        """
        try:
            confidence = self.calculate_confidence(original, rewritten, errors, use_ollama, pass_number)
            improvements = self.extract_improvements(original, rewritten, errors)
            changes = self.analyze_changes(original, rewritten)
            
            evaluation = {
                'confidence': confidence,
                'improvements': improvements,
                'changes_analysis': changes,
                'quality_score': self._calculate_quality_score(confidence, changes, errors),
                'pass_number': pass_number,
                'model_used': 'ollama' if use_ollama else 'huggingface'
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
                'model_used': 'unknown'
            }
    
    def _calculate_quality_score(self, confidence: float, changes: Dict[str, Any], 
                               errors: List[Dict[str, Any]]) -> float:
        """Calculate an overall quality score for the rewrite."""
        try:
            quality_score = confidence * 0.6  # Confidence contributes 60%
            
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
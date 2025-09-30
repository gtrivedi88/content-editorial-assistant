"""
Text Processing Module
Handles text cleaning, validation, and post-processing of AI-generated content.
"""

import logging
import re
from typing import List, Dict, Any
from .output_enforcer import create_output_enforcer

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles cleaning and post-processing of AI-generated text.
    Pre-compiled regex patterns."""
    
    # Pre-compile regex patterns for performance
    _regex_cache = {
        'wordy_patterns': {},
        'explanatory_patterns': [
            re.compile(r"(.+?)\s+No changes were made", re.IGNORECASE),
            re.compile(r"(.+?)\s+The heading", re.IGNORECASE),
            re.compile(r"(.+?)\s+This heading", re.IGNORECASE),
            re.compile(r"(.+?)\s+I have", re.IGNORECASE),
            re.compile(r"(.+?)\s+I've", re.IGNORECASE),
            re.compile(r"(.+?)\s+As requested", re.IGNORECASE),
            re.compile(r"(.+?)\s+Note:", re.IGNORECASE),
            re.compile(r"(.+?)\s+\(Note:", re.IGNORECASE),
            re.compile(r"(.+?)\s+already follows", re.IGNORECASE),
            re.compile(r"(.+?)\s+meets the", re.IGNORECASE),
            re.compile(r"(.+?)\s+since it meets", re.IGNORECASE),
        ],
        'whitespace': re.compile(r'\s+'),
    }
    
    def __init__(self):
        """Initialize the text processor with cached output enforcer."""
        self.output_enforcer = create_output_enforcer()
        
        # Pre-compile wordy replacements for performance
        if not self._regex_cache['wordy_patterns']:
            wordy_replacements = {
                'in order to': 'to',
                'due to the fact that': 'because',
                'at this point in time': 'now',
                'a large number of': 'many',
                'make a decision': 'decide',
                'for the purpose of': 'to',
                'in spite of the fact that': 'although'
            }
            for wordy, concise in wordy_replacements.items():
                pattern = r'\b' + re.escape(wordy) + r'\b'
                self._regex_cache['wordy_patterns'][wordy] = (re.compile(pattern, re.IGNORECASE), concise)
    
    def clean_generated_text(self, generated_text: str, original_text: str, 
                            use_structured: bool = True) -> str:
        """
        Clean AI response using intelligent output enforcer.
        Prevents chatter at source instead of filtering afterward.
        
        Args:
            generated_text: Raw AI response
            original_text: Original text for fallback
            use_structured: Whether response was requested in JSON format
            
        Returns:
            Clean corrected text
        """
        if not generated_text:
            logger.warning("Empty generated text")
            return original_text
        
        logger.info(f"🔧 Processing AI response: {len(generated_text)} chars vs original: {len(original_text)} chars")
        
        # Use output enforcer to extract clean response
        cleaned = self.output_enforcer.extract_clean_response(
            generated_text, 
            original_text, 
            use_structured=use_structured
        )
        
        logger.info(f"✅ Clean processing complete: '{cleaned[:100]}...'")
        return cleaned
    
    def rule_based_rewrite(self, content: str, errors: List[Dict[str, Any]]) -> str:
        """Fallback rule-based rewriting when AI models are not available."""
        rewritten = content
        
        try:
            # PERFORMANCE: Use pre-compiled regex patterns
            for wordy, (pattern, concise) in self._regex_cache['wordy_patterns'].items():
                rewritten = pattern.sub(concise, rewritten)
            
            # Apply error-specific fixes
            for error in errors:
                error_type = error.get('type', '')
                
                if error_type == 'clarity':
                    complex_replacements = {
                        'utilize': 'use',
                        'facilitate': 'help',
                        'demonstrate': 'show',
                        'implement': 'do',
                        'commence': 'start',
                        'terminate': 'end'
                    }
                    
                    for complex_word, simple_word in complex_replacements.items():
                        rewritten = re.sub(r'\b' + complex_word + r'\b', simple_word, rewritten, flags=re.IGNORECASE)
                
                elif error_type == 'sentence_length':
                    sentence = error.get('sentence', '')
                    if sentence and sentence in rewritten:
                        if ' and ' in sentence and len(sentence.split()) > 20:
                            parts = sentence.split(' and ', 1)
                            if len(parts) == 2:
                                new_sentence = f"{parts[0].strip()}. {parts[1].strip()}"
                                rewritten = rewritten.replace(sentence, new_sentence)
            
            return rewritten
            
        except Exception as e:
            logger.error(f"Rule-based rewrite failed: {e}")
            return content
    
    def _clean_heading_additions(self, cleaned_text: str, original_text: str) -> str:
        """
        Remove common AI additions to headings like 'Improved functionality'.
        
        Args:
            cleaned_text: The cleaned AI response
            original_text: The original heading text
            
        Returns:
            Heading with AI additions removed
        """
        try:
            # First, handle the specific case where AI adds explanations after the heading
            result = cleaned_text.strip()
            
            # PERFORMANCE: Use pre-compiled regex patterns
            for pattern in self._regex_cache['explanatory_patterns']:
                match = pattern.search(result)
                if match:
                    result = match.group(1).strip()
                    logger.debug(f"Extracted heading before explanation: '{result}'")
                    break
            
            # Common AI additions that should be removed from headings
            ai_additions = [
                'improved functionality',
                'enhanced functionality', 
                'better version',
                'improved version',
                'enhanced version',
                'updated content',
                'revised content',
                'optimized content',
                'clearer version',
                'professional version',
                'improved',
                'enhanced',
                'better',
                'updated',
                'revised',
                'optimized',
                'clearer'
            ]
            
            # Remove these additions from the end of headings
            for addition in ai_additions:
                # Remove from end (case insensitive)
                if result.lower().endswith(addition.lower()):
                    result = result[:-len(addition)].strip()
                
                # Remove from middle/end if preceded by space
                pattern = f" {addition}"
                if pattern.lower() in result.lower():
                    result = re.sub(pattern, '', result, flags=re.IGNORECASE).strip()
            
            # PERFORMANCE: Use pre-compiled regex for whitespace
            result = self._regex_cache['whitespace'].sub(' ', result).strip()
            
            # If we removed everything, return original
            if not result or len(result) < 2:
                return original_text
            
            logger.info(f"Cleaned heading: '{cleaned_text}' → '{result}'")
            return result
            
        except Exception as e:
            logger.error(f"Error cleaning heading additions: {e}")
            return cleaned_text
    
    def validate_text(self, text: str, original_text: str) -> Dict[str, Any]:
        """
        Validate processed text quality.
        
        Args:
            text: Processed text to validate
            original_text: Original text for comparison
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            'is_valid': True,
            'issues': [],
            'word_count_original': len(original_text.split()),
            'word_count_processed': len(text.split()),
            'length_ratio': 0.0
        }
        
        try:
            # Check minimum length
            if len(text.strip()) < 10:
                validation['is_valid'] = False
                validation['issues'].append("Text too short after processing")
            
            # Check if identical to original
            if text.lower().strip() == original_text.lower().strip():
                validation['issues'].append("No changes made to original text")
            
            # Calculate length ratio
            if validation['word_count_original'] > 0:
                validation['length_ratio'] = validation['word_count_processed'] / validation['word_count_original']
                
                # Check for extreme length changes
                if validation['length_ratio'] > 2.0:
                    validation['issues'].append("Text significantly expanded (may contain unwanted content)")
                elif validation['length_ratio'] < 0.3:
                    validation['issues'].append("Text significantly reduced (may have lost important content)")
            
            # Check for proper sentence endings
            if text and not text.endswith(('.', '!', '?')):
                validation['issues'].append("Text does not end with proper punctuation")
            
        except Exception as e:
            logger.error(f"Text validation failed: {e}")
            validation['is_valid'] = False
            validation['issues'].append(f"Validation error: {str(e)}")
        
        return validation 
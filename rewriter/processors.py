"""
Text Processing Module
Handles text cleaning, validation, and post-processing of AI-generated content.
"""

import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class TextProcessor:
    """Handles cleaning and post-processing of AI-generated text."""
    
    def __init__(self):
        """Initialize the text processor."""
        pass
    
    def clean_generated_text(self, generated_text: str, original_text: str) -> str:
        """Clean and validate generated text, extracting only the rewritten content."""
        if not generated_text:
            logger.warning("Empty generated text")
            return original_text
        
        cleaned = generated_text.strip()
        logger.info(f"Raw AI response: '{cleaned[:200]}...'")
        
        # Remove meta-commentary and explanations more aggressively
        
        # First, try to extract content between common delimiters
        # Look for patterns like "Here's the rewritten text:" or "Improved text:"
        content_patterns = [
            r"here's the rewritten text:\s*(.*?)(?:\n\*|\*|$)",
            r"improved text:\s*(.*?)(?:\n\*|\*|$)",  
            r"rewritten text:\s*(.*?)(?:\n\*|\*|$)",
            r"final version:\s*(.*?)(?:\n\*|\*|$)",
            r"polished version:\s*(.*?)(?:\n\*|\*|$)",
        ]
        
        for pattern in content_patterns:
            match = re.search(pattern, cleaned, re.IGNORECASE | re.DOTALL)
            if match:
                cleaned = match.group(1).strip()
                logger.info(f"Extracted content using pattern: '{pattern}'")
                break
        
        # Remove lines that start with bullets or asterisks (explanations)
        lines = cleaned.split('\n')
        content_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Skip lines that are clearly explanations or meta-commentary
            if (line.startswith('*') or 
                line.startswith('-') or 
                line.startswith('•') or
                line.lower().startswith('let me know') or
                line.lower().startswith('i ') or
                line.lower().startswith('converted') or
                line.lower().startswith('identified') or
                line.lower().startswith('replaced') or
                line.lower().startswith('clarified') or
                line.lower().startswith('note:') or
                line.lower().startswith('explanation:') or
                line.lower().startswith('changes made:') or
                'converted' in line.lower() and 'passive' in line.lower() or
                'replaced' in line.lower() and 'vague' in line.lower()):
                continue
            
            content_lines.append(line)
        
        if content_lines:
            cleaned = ' '.join(content_lines)
        
        # Remove common AI response prefixes
        prefixes_to_remove = [
            "here is the improved text:",
            "here's the improved text:",
            "improved text:",
            "rewritten text:",
            "revised text:",
            "the improved version:",
            "here is the rewrite:",
            "here's the rewrite:",
            "sure, here's",
            "certainly, here's",
            "here's a rewritten version:",
            "here's the rewritten text:",
            "rewritten:",
            "improved:",
            "final version:",
            "polished version:"
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
                break
        
        # Remove sentences that are clearly explanatory
        sentences = re.split(r'(?<=[.!?])\s+', cleaned)
        content_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            sentence_lower = sentence.lower()
            
            # Skip explanatory sentences
            explanatory_starts = [
                'note:', 'i\'ve', 'i have', 'i applied', 'i made', 'i converted',
                'i removed', 'i shortened', 'i replaced', 'this addresses',
                'these changes', 'the rewrite', 'as requested', 'per your',
                'let me know', 'if you\'d like', 'would you like', 'i can help',
                'here are the', 'the changes', 'improvements made', 'changes include'
            ]
            
            is_explanatory = any(sentence_lower.startswith(start) for start in explanatory_starts)
            
            # Also skip sentences that contain meta-commentary about the rewriting process
            meta_keywords = ['converted', 'identified', 'replaced', 'clarified', 'improved', 'rewritten', 'changed']
            has_meta_keywords = any(keyword in sentence_lower for keyword in meta_keywords)
            
            if not is_explanatory and not has_meta_keywords:
                content_sentences.append(sentence)
        
        if content_sentences:
            cleaned = ' '.join(content_sentences)
        
        # Remove any remaining artifacts
        cleaned = re.sub(r'\[insert[^\]]*\]', '', cleaned)  # Remove placeholder text like [insert specific examples]
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
        cleaned = cleaned.strip()
        
        logger.info(f"Cleaned AI response: '{cleaned[:200]}...'")
        
        # Validation
        if len(cleaned) < 5:
            logger.warning("Generated text too short after cleaning")
            return original_text
        
        # Check if it's meaningfully different from original
        if cleaned.lower().strip() == original_text.lower().strip():
            logger.warning("Generated text identical to original after cleaning")
            return original_text
        
        # Ensure proper sentence endings
        if cleaned and not cleaned.endswith(('.', '!', '?')):
            # Find the last complete sentence
            sentences = re.split(r'[.!?]+', cleaned)
            if len(sentences) > 1:
                # Take all complete sentences except the last incomplete one
                complete_sentences = sentences[:-1]
                if complete_sentences:
                    cleaned = '. '.join(complete_sentences) + '.'
        
        logger.info(f"Final cleaned text: '{cleaned}'")
        return cleaned
    
    def rule_based_rewrite(self, content: str, errors: List[Dict[str, Any]]) -> str:
        """Fallback rule-based rewriting when AI models are not available."""
        rewritten = content
        
        try:
            for error in errors:
                error_type = error.get('type', '')
                
                if error_type == 'conciseness':
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
                        rewritten = re.sub(r'\b' + re.escape(wordy) + r'\b', concise, rewritten, flags=re.IGNORECASE)
                
                elif error_type == 'clarity':
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
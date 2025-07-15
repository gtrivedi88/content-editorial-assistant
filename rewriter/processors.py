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
        logger.info(f"🔧 Processing raw AI response: '{cleaned[:100]}...'")
        logger.info(f"📊 Raw response length: {len(cleaned)} chars vs original: {len(original_text)} chars")
        
        # Remove meta-commentary and explanations more aggressively
        
        # First, try to extract content between common delimiters
        # Look for patterns like "Here's the rewritten text:" or "Improved text:"
        content_patterns = [
            r"corrected heading:\s*(.*?)(?:\s+No changes|\s+The|\s*$)",  # For heading prompts
            r"here is the rewritten heading:\s*(.*?)(?:\n\*|\*|$)",  # Specific pattern AI is using
            r"here's the rewritten heading:\s*(.*?)(?:\n\*|\*|$)",
            r"here is the corrected heading:\s*(.*?)(?:\n\*|\*|$)",
            r"here's the improved version:\s*(.*?)(?:\n\*|\*|$)",
            r"here is the improved version:\s*(.*?)(?:\n\*|\*|$)",
            r"certainly!\s*here's the rewrite:\s*(.*?)(?:\n\*|\*|$)",
            r"i'll help you improve this:\s*(.*?)(?:\n\*|\*|$)",
            r"let me rewrite this for you:\s*(.*?)(?:\n\*|\*|$)",
            r"here's the rewritten text:\s*(.*?)(?:\n\*|\*|$)",
            r"here is the rewritten text:\s*(.*?)(?:\n\*|\*|$)",
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
                line.lower().startswith('converted') or
                line.lower().startswith('identified') or
                line.lower().startswith('replaced') or
                line.lower().startswith('clarified') or
                line.lower().startswith('note:') or
                line.lower().startswith('explanation:') or
                line.lower().startswith('changes made:') or
                line.lower().startswith('improved heading:') or
                line.lower().startswith('better version:') or
                line.lower().startswith('enhanced:') or
                'converted' in line.lower() and 'passive' in line.lower() or
                'replaced' in line.lower() and 'vague' in line.lower()):
                continue
            
            content_lines.append(line)
        
        if content_lines:
            cleaned = ' '.join(content_lines)
        else:
            cleaned = ""  # All lines were filtered out
        
        # Remove common AI response prefixes
        prefixes_to_remove = [
            "here is the rewritten heading:",
            "here's the rewritten heading:",
            "here is the corrected heading:",
            "here's the corrected heading:",
            "here's the improved version:",
            "here is the improved version:",
            "certainly! here's the rewrite:",
            "i'll help you improve this:",
            "let me rewrite this for you:",
            "here is the improved text:",
            "here's the improved text:",
            "here is the rewritten text:",
            "here's the rewritten text:",
            "improved text:",
            "rewritten text:",
            "revised text:",
            "the improved version:",
            "here is the rewrite:",
            "here's the rewrite:",
            "sure, here's",
            "certainly, here's",
            "here's a rewritten version:",
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
            
            # Skip numbered explanations (1., 2., 3., etc.)
            if re.match(r'^\d+\.', sentence):
                continue
            
            # Skip explanatory sentences but be more selective
            explanatory_starts = [
                'note:', 'i\'ve', 'i have', 'i applied', 'i made', 'i converted',
                'i removed', 'i shortened', 'i replaced', 'this addresses',
                'these changes', 'the rewrite', 'as requested', 'per your',
                'let me know', 'if you\'d like', 'would you like', 'i can help',
                'here are the', 'the changes', 'improvements made', 'changes include',
                'critical:', 'important:', 'note that', 'i did not', 'i ensured',
                'i maintained', 'i used', 'i kept', 'i split', 'i toned'
            ]
            
            is_explanatory = any(sentence_lower.startswith(start) for start in explanatory_starts)
            
            # Also skip sentences that contain meta-commentary about the rewriting process
            meta_commentary_patterns = [
                r'\bthese changes address\b',
                r'\bthe rewrite maintains\b',
                r'\bby converting\b.*\bpassive voice\b',
                r'\bimproving clarity\b.*\breadability\b',
                r'\benhancing readability\b'
            ]
            
            has_meta_commentary = any(re.search(pattern, sentence_lower) for pattern in meta_commentary_patterns)
            
            # Skip sentences that sound like AI explanations
            ai_explanation_patterns = [
                r'\bi (did|have|used|kept|split|maintained|ensured|toned)\b',
                r'\bto avoid\b.*\b(guarantees|promises|claims)\b',
                r'\binstead of\b.*\boriginal\b',
                r'\bfor better\b.*\bclarity\b',
                r'\blevel of\b.*\bdetail\b.*\boriginal\b'
            ]
            
            has_ai_patterns = any(re.search(pattern, sentence_lower) for pattern in ai_explanation_patterns)
            
            if not is_explanatory and not has_meta_commentary and not has_ai_patterns:
                content_sentences.append(sentence)
        
        if content_sentences:
            cleaned = ' '.join(content_sentences)
        
        # Remove any remaining artifacts
        cleaned = re.sub(r'\[insert[^\]]*\]', '', cleaned)  # Remove placeholder text like [insert specific examples]
        cleaned = re.sub(r'\s+', ' ', cleaned)  # Normalize whitespace
        cleaned = cleaned.strip()
        
        logger.info(f"Cleaned AI response: '{cleaned[:200]}...'")
        
        # Validation (be less aggressive for short content like headings)
        if len(cleaned) < 3:
            logger.warning("Generated text too short after cleaning")
            return original_text
        
        # For very short content (like headings), be more lenient about changes
        if len(original_text.split()) <= 5:  # Short content like headings
            # Remove common AI additions to headings
            heading_cleaned = self._clean_heading_additions(cleaned, original_text)
            
            # Accept any reasonable change, even small ones
            if len(heading_cleaned.strip()) >= 2 and heading_cleaned.strip() != original_text.strip():
                logger.info(f"Accepting heading/short content change: '{original_text}' → '{heading_cleaned}'")
                return heading_cleaned
        
        # Check if it's meaningfully different from original (normal validation)
        if cleaned.lower().strip() == original_text.lower().strip():
            logger.warning("Generated text identical to original after cleaning")
            return original_text
        
        # Ensure proper sentence endings (but not for headings/short content)
        if cleaned and not cleaned.endswith(('.', '!', '?')) and len(original_text.split()) > 5:
            # Only add sentence endings to longer content, not headings
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
            # Always apply basic conciseness replacements
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
            
            # Extract text before explanatory phrases
            explanatory_patterns = [
                r"(.+?)\s+No changes were made",
                r"(.+?)\s+The heading",
                r"(.+?)\s+This heading",  
                r"(.+?)\s+I have",
                r"(.+?)\s+I've",
                r"(.+?)\s+As requested",
                r"(.+?)\s+Note:",
                r"(.+?)\s+\(Note:",
                r"(.+?)\s+already follows",
                r"(.+?)\s+meets the",
                r"(.+?)\s+since it meets",
                r"(.+?)\s+Let me explain",
                r"(.+?)\s+Here's why",
                r"(.+?)\s+The reason",
                r"(.+?)\s+I made the following changes:?",
                r"(.+?)\s+The changes made:?",
                r"(.+?)\s+Changes made:?",
                r"(.+?)\s+I applied",
                r"(.+?)\s+I removed",
                r"(.+?)\s+I fixed",
                r"(.+?)\s+Key changes:?",
                r"(.+?)\s+Main changes:?"
            ]
            
            for pattern in explanatory_patterns:
                match = re.search(pattern, result, re.IGNORECASE)
                if match:
                    result = match.group(1).strip()
                    logger.info(f"Extracted heading before explanation: '{result}'")
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
            
            # Clean up any duplicate spaces
            result = re.sub(r'\s+', ' ', result).strip()
            
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
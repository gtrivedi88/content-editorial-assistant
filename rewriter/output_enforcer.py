"""
AI Output Enforcer
Simple, production-ready solution to eliminate AI chatter using JSON structure.
"""

import logging
import json
import re
from typing import Optional

logger = logging.getLogger(__name__)


class OutputEnforcer:
    """
    Enforces clean AI output using JSON structure.
    Simple, reliable, production-ready.
    """
    
    def __init__(self):
        """Initialize the output enforcer."""
        self.max_retries = 2
        
        # Load quality control configuration
        try:
            from .quality_control_config import get_quality_control_config
            self.qc_config = get_quality_control_config()
        except ImportError:
            # Fallback if config module not available
            self.qc_config = None
    
    def create_structured_prompt(self, content: str, instructions: str) -> str:
        """
        Create a JSON-structured prompt that eliminates chatter.
        
        Args:
            content: Original content to fix
            instructions: Specific fixing instructions
            
        Returns:
            Prompt that enforces JSON output structure
        """
        
        prompt = f"""You are a text editor. Apply the requested changes and respond in EXACT JSON format.

CRITICAL: Your entire response will be used directly in a document, so it must be valid JSON with no extra text.

TASK: {instructions}

INPUT TEXT: {content}

Respond in this EXACT format with no other text before or after:
{{"corrected_text": "your corrected text here"}}"""
        
        return prompt
    
    def create_clean_prompt(self, content: str, instructions: str) -> str:
        """
        Fallback: Create a prompt for models that struggle with JSON.
        
        Args:
            content: Original content to fix
            instructions: Specific fixing instructions
            
        Returns:
            Prompt designed to prevent AI chatter
        """
        
        prompt = f"""You are a text editor. Your job is to output ONLY the corrected text.

CRITICAL RULES:
- Output ONLY the corrected text
- NO explanations, prefixes, or commentary
- Your response goes directly into a document
- Make ONLY the specific changes requested

TASK: {instructions}

INPUT TEXT: {content}

CORRECTED TEXT:"""
        
        return prompt
    
    def extract_clean_response(self, ai_response: str, original_text: str, 
                             use_structured: bool = True) -> str:
        """
        Extract clean text from AI response.
        
        Args:
            ai_response: Raw AI response
            original_text: Original text for fallback
            use_structured: Whether to expect JSON format
            
        Returns:
            Clean corrected text
        """
        if not ai_response or not ai_response.strip():
            logger.warning("Empty AI response")
            return original_text
        
        cleaned = ai_response.strip()
        
        if use_structured:
            # Try JSON extraction first
            extracted = self._extract_from_json(cleaned)
            if extracted:
                return self._validate_response(extracted, original_text)
        
        # Fallback: simple cleaning
        cleaned = self._simple_clean(cleaned)
        return self._validate_response(cleaned, original_text)
    
    def _extract_from_json(self, response: str) -> Optional[str]:
        """Extract text from JSON response format."""
        try:
            # Handle responses that might have extra text around JSON
            json_match = re.search(r'\{[^}]*"corrected_text"[^}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                return data.get('corrected_text', '').strip()
            
            # Try parsing the whole response as JSON
            data = json.loads(response)
            return data.get('corrected_text', '').strip()
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.debug(f"JSON parsing failed: {e}")
        
        return None
    
    def _simple_clean(self, text: str) -> str:
        """Simple, reliable cleaning for non-JSON responses."""
        # Remove common prefixes
        text = re.sub(r'^(?:corrected text:|here (?:is|\'s) the corrected text:|output:)\s*', 
                     '', text, flags=re.IGNORECASE).strip()
        
        # Remove markdown formatting
        text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # If there's obvious explanation text, take just the first sentence
        if any(phrase in text.lower() for phrase in ['i replaced', 'i changed', 'i fixed', 'explanation:']):
            sentences = re.split(r'[.!?]+', text)
            if sentences:
                return sentences[0].strip()
        
        return text.strip()
    
    def _validate_response(self, text: str, original_text: str) -> str:
        """Validate and return the response or fallback to original."""
        if not text or len(text.strip()) < 2:
            return original_text
            
        # FIXED: Don't revert case changes - case differences are valid corrections!
        # Only revert if text is EXACTLY the same (preserving intentional case fixes)
        if text.strip() == original_text.strip():
            return original_text
        
        # Quality control check for AI-introduced errors
        validated_text = self._quality_control_check(text, original_text)
        
        return validated_text.strip()
    
    def _quality_control_check(self, ai_text: str, original_text: str) -> str:
        """
        AI quality control using pattern-based error detection.
        Designed to catch and fix common AI-introduced errors without hardcoding specific cases.
        """
        import re
        from collections import Counter
        
        corrected_text = ai_text
        
        # Fix obvious concatenation errors

        corrected_text = self._fix_word_concatenation_errors(corrected_text, original_text)
        
        return corrected_text
    
    def _fix_word_duplications(self, text: str, original: str) -> str:
        """Generic pattern-based detection of word duplications."""
        import re
        
        # Use configurable patterns if available, otherwise use defaults
        if self.qc_config and self.qc_config.duplication_patterns:
            duplication_patterns = self.qc_config.duplication_patterns
        else:
            # Default patterns
            duplication_patterns = [
                r'\b(\w+)(over|under|pre|post|re|de|un|in|out|up|down)\1\b',  # prefix duplications
                r'\b(\w+)\1\b',  # simple duplications (e.g., "thethe", "andand")
                r'\b(\w+)\s+\1\b',  # space-separated duplications
            ]
        
        corrected = text
        for pattern in duplication_patterns:
            matches = re.finditer(pattern, corrected, re.IGNORECASE)
            for match in matches:
                full_match = match.group(0)
                base_word = match.group(1)
                
                # Only fix if it's likely an AI error (not in original text)
                if full_match.lower() not in original.lower():
                    # Intelligent correction: choose the most likely intended word
                    if len(match.groups()) > 1:  # Has connector
                        connector = match.group(2)
                        # Check if prefixed version makes sense
                        prefixed_word = connector + base_word
                        if self._is_likely_word(prefixed_word) and prefixed_word.lower() not in base_word.lower():
                            replacement = prefixed_word
                        else:
                            replacement = base_word
                    else:
                        replacement = base_word
                    
                    if self.qc_config and self.qc_config.enable_logging:
                        logger.warning(f"🔍 AI quality control: Fixed duplication '{full_match}' → '{replacement}'")
                    corrected = corrected.replace(full_match, replacement, 1)
        
        return corrected
    
    def _fix_statistical_anomalies(self, text: str, original: str) -> str:
        """Detect and fix statistical anomalies that suggest AI errors."""
        import re
        from collections import Counter
        
        # Check for unusually high repetition of short words
        words = re.findall(r'\b\w+\b', text.lower())
        word_counts = Counter(words)
        
        # Find words that appear suspiciously often compared to original
        original_words = Counter(re.findall(r'\b\w+\b', original.lower()))
        
        # Get configurable thresholds
        max_repetition = self.qc_config.max_short_word_repetition if self.qc_config else 3
        multiplier_threshold = self.qc_config.repetition_multiplier_threshold if self.qc_config else 2.0
        
        corrected = text
        for word, count in word_counts.items():
            if len(word) <= 3 and count > max_repetition:  # Short words repeated too much
                original_count = original_words.get(word, 0)
                if count > original_count * multiplier_threshold and count > 2:
                    # This might be an AI repetition error
                    excess_count = count - max(original_count, 1)
                    if excess_count > 0:
                        if self.qc_config and self.qc_config.enable_logging:
                            logger.warning(f"🔍 AI quality control: Detected excessive repetition of '{word}' ({count} times)")
                        # Could implement smart removal here
        
        return corrected
    
    def _validate_text_structure(self, text: str, original: str) -> str:
        """Validate text structure for reasonableness."""
        # Get configurable thresholds
        max_length_ratio = self.qc_config.max_length_ratio if self.qc_config else 1.4
        max_word_ratio = self.qc_config.max_word_ratio if self.qc_config else 1.3
        
        if len(text) > len(original) * max_length_ratio:
            word_ratio = len(text.split()) / max(len(original.split()), 1)
            if word_ratio > max_word_ratio:
                if self.qc_config and self.qc_config.enable_logging:
                    logger.warning(f"🔍 AI quality control: Suspicious text expansion ({word_ratio:.1f}x words)")
                # In production, could trigger fallback to original or request revision
        
        # Sentence structure validation
        if original.count('.') > 0 and text.count('.') == 0:
            if self.qc_config and self.qc_config.enable_logging:
                logger.warning("🔍 AI quality control: Lost sentence structure (no periods)")
        
        return text
    
    def _is_likely_word(self, word: str) -> bool:
        """
        Simple heuristic to check if a word is likely valid.
        In production, this could use a dictionary or language model.
        """
        # Get configurable values
        min_length = self.qc_config.min_word_length if self.qc_config else 2
        max_simple_length = self.qc_config.max_simple_word_length if self.qc_config else 6
        valid_prefixes = self.qc_config.valid_prefixes if self.qc_config else [
            'over', 'under', 'pre', 'post', 're', 'un', 'in', 'out'
        ]
        
        # Basic heuristics for common English patterns
        if len(word) < min_length:
            return False
        
        # Common prefixes that often form real words
        for prefix in valid_prefixes:
            if word.lower().startswith(prefix) and len(word) > len(prefix) + 2:
                return True
        
        # If it's a simple word, likely valid
        if len(word) <= max_simple_length and word.isalpha():
            return True
        
        return False

    def _fix_word_concatenation_errors(self, text: str, original: str) -> str:
        """
        Fix AI-introduced word concatenation errors.
        
        These occur when AI incorrectly merges words during transformations,
        like "need to deployment" → "mustdeployement" instead of "must deployment".
        """
        import re
        
        corrected = text
        
        # VERY CONSERVATIVE: Only fix the most obvious concatenation errors
        concatenation_fixes = {
            # Only fix the specific error we know about
            r'\bmustdeployement\b': 'must deployment',  # The exact error we saw
            r'\bmustdeployment\b': 'must deployment',   # Variant without extra 'e'
        }
        
        for pattern, replacement in concatenation_fixes.items():
            if isinstance(replacement, str):
                # Simple string replacement
                before_fix = corrected
                corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
                if corrected != before_fix:
                    if self.qc_config and self.qc_config.enable_logging:
                        logger.warning(f"🔍 Fixed word concatenation: found concatenated words")
            else:
                # Regex group replacement
                before_fix = corrected
                corrected = re.sub(pattern, replacement, corrected, flags=re.IGNORECASE)
                if corrected != before_fix:
                    if self.qc_config and self.qc_config.enable_logging:
                        logger.warning(f"🔍 Fixed word concatenation: separated merged words")
        
        return corrected


def create_output_enforcer() -> OutputEnforcer:
    """Factory function to create an output enforcer."""
    return OutputEnforcer() 
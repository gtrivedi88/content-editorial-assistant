"""
Word Usage Rule for words starting with 'Z'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ZWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'Z'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_z'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with Z-word patterns."""
        # Define word details for 'Z' words
        word_details = {
            "zero out": {"suggestion": "Use 'zero' as a verb.", "severity": "low"},
            "zero emissions": {"suggestion": "Avoid unsubstantiated environmental claims.", "severity": "high"},
            "zero trust": {"suggestion": "Write as two words, lowercase.", "severity": "low"},
            "zip": {"suggestion": "Avoid this term as it is a trademark. Use 'compress'.", "severity": "high"},
        }
        
        # Use base class method to setup patterns
        self._setup_word_patterns(nlp, word_details)

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)
        
        # Ensure patterns are initialized
        self._ensure_patterns_ready(nlp)

        # NEW ENHANCED APPROACH: Use base class PhraseMatcher functionality
        word_usage_errors = self._find_word_usage_errors(doc, "Review usage of the term")
        errors.extend(word_usage_errors)
        
        return errors

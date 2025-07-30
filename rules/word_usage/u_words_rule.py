"""
Word Usage Rule for words starting with 'U'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class UWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'U'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_u'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with U-word patterns."""
        # Define word details for 'U' words
        word_details = {
            "un-": {"suggestion": "Most words with the 'un-' prefix are not hyphenated (e.g., 'unnecessary').", "severity": "low"},
            "underbar": {"suggestion": "Use 'underscore'.", "severity": "medium"},
            "unselect": {"suggestion": "Use 'clear' for check boxes or 'deselect'.", "severity": "medium"},
            "up-to-date": {"suggestion": "Write as 'up to date' (no hyphens).", "severity": "low"},
            "user-friendly": {"suggestion": "Avoid subjective claims. Describe how the feature helps the user.", "severity": "high"},
            "user name": {"suggestion": "Use 'username' (one word).", "severity": "low"},
            "utilize": {"suggestion": "Use 'use'.", "severity": "medium"},
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

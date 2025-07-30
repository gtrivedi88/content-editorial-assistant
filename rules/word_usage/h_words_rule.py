"""
Word Usage Rule for words starting with 'H'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class HWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'H'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_h'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with H-word patterns."""
        # Define word details for 'H' words
        word_details = {
            "hamburger menu": {"suggestion": "Avoid food-related UI terms. Use the element's tooltip name or a generic term like 'main menu'.", "severity": "medium"},
            "hard copy": {"suggestion": "Use 'hardcopy' (one word).", "severity": "low"},
            "hard-coded": {"suggestion": "Write as 'hardcoded' (one word).", "severity": "low"},
            "have to": {"suggestion": "For mandatory actions, prefer 'must' or the imperative form.", "severity": "medium"},
            "health care": {"suggestion": "Use 'healthcare' (one word).", "severity": "low"},
            "help desk": {"suggestion": "Use 'helpdesk' (one word).", "severity": "low"},
            "high-availability": {"suggestion": "Write as 'high availability' (two words).", "severity": "low"},
            "high-level": {"suggestion": "Write as 'high level' (two words).", "severity": "low"},
            "hit": {"suggestion": "Do not use for keyboard actions. Use 'press' or 'type'.", "severity": "high"},
            "home page": {"suggestion": "Use 'homepage' (one word).", "severity": "low"},
            "host name": {"suggestion": "Use 'hostname' (one word).", "severity": "low"},
            "how-to": {"suggestion": "Use as a hyphenated adjective (e.g., 'how-to procedure'), not a noun.", "severity": "medium"},
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

"""
Word Usage Rule for words starting with 'O'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class OWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'O'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_o'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with O-word patterns."""
        # Define word details for 'O' words
        word_details = {
            "off of": {"suggestion": "Use 'off' or 'from'.", "severity": "medium"},
            "off-line": {"suggestion": "Use 'offline' (one word).", "severity": "low"},
            "OK": {"suggestion": "Use only to refer to a UI element label. Do not use 'okay'.", "severity": "medium"},
            "on-boarding": {"suggestion": "Use 'onboarding' (one word).", "severity": "low"},
            "on premise": {"suggestion": "Use 'on-premises' (adjective) or 'on premises' (adverb).", "severity": "medium"},
            "on the fly": {"suggestion": "Avoid jargon. Use 'dynamically' or 'during processing'.", "severity": "medium"},
            "orientate": {"suggestion": "Use 'orient'.", "severity": "low"},
            "our": {"suggestion": "Avoid first-person pronouns in technical content.", "severity": "medium"},
            "out-of-the-box": {"suggestion": "Use 'out of the box' (no hyphens).", "severity": "low"},
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

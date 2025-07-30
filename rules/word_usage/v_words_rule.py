"""
Word Usage Rule for words starting with 'V'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class VWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'V'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_v'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with V-word patterns."""
        # Define word details for 'V' words
        word_details = {
            "vanilla": {"suggestion": "Avoid jargon. Use 'basic', 'standard', or 'not customized'.", "severity": "medium"},
            "Velcro": {"suggestion": "This is a trademark. Use the generic term 'hook-and-loop fastener'.", "severity": "high"},
            "verbatim": {"suggestion": "Do not use as a noun. Use as an adjective or adverb.", "severity": "low"},
            "versus": {"suggestion": "Spell out 'versus'. Do not use 'vs.' or 'v.'.", "severity": "medium"},
            "via": {"suggestion": "Use to refer to routing data. For other contexts, 'by using' or 'through' might be clearer.", "severity": "low"},
            "vice versa": {"suggestion": "Write as shown (two words).", "severity": "low"},
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

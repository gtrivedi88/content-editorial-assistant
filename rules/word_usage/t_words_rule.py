"""
Word Usage Rule for words starting with 'T'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class TWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'T'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_t'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with T-word patterns."""
        # Define word details for 'T' words
        word_details = {
            "tap on": {"suggestion": "Omit 'on'. Use 'tap the icon'.", "severity": "medium"},
            "tarball": {"suggestion": "Use '.tar file'.", "severity": "medium"},
            "team room": {"suggestion": "Use 'teamroom' (one word).", "severity": "low"},
            "terminate": {"suggestion": "Prefer simpler terms like 'end' or 'stop'.", "severity": "low"},
            "thank you": {"suggestion": "Avoid in technical information.", "severity": "medium"},
            "that": {"suggestion": "Include 'that' in clauses for clarity, e.g., 'Verify that the service is running.'", "severity": "low"},
            "time frame": {"suggestion": "Use 'timeframe' (one word).", "severity": "low"},
            "time out": {"suggestion": "Use 'time out' (verb) and 'timeout' (noun/adjective).", "severity": "low"},
            "toast": {"suggestion": "Avoid food names for UI elements. Use 'notification'.", "severity": "medium"},
            "tool kit": {"suggestion": "Use 'toolkit' (one word).", "severity": "low"},
            "trade-off": {"suggestion": "Use 'tradeoff' (one word).", "severity": "low"},
            "transparent": {"suggestion": "Use with caution as it can be ambiguous (invisible or easy to understand).", "severity": "medium"},
            "tribe": {"suggestion": "Avoid this term. Use 'team' or 'squad'.", "severity": "high"},
            "try and": {"suggestion": "Use 'try to'.", "severity": "medium"},
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

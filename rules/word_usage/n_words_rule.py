"""
Word Usage Rule for words starting with 'N'.
Enhanced with spaCy PhraseMatcher for efficient pattern detection.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'N'.
    Enhanced with spaCy PhraseMatcher for efficient detection.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_n'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with N-word patterns."""
        # Define word details for 'N' words
        word_details = {
            "name space": {"suggestion": "Use 'namespace' (one word).", "severity": "low"},
            "native": {"suggestion": "Use with caution. Prefer more specific terms like 'local', 'basic', or 'default'.", "severity": "medium"},
            "need to": {"suggestion": "For mandatory actions, prefer 'must' or the imperative form (e.g., 'Back up your data').", "severity": "medium"},
            "new": {"suggestion": "Avoid using 'new' to describe products or features, as it becomes dated quickly.", "severity": "low"},
            "news feed": {"suggestion": "Write as 'newsfeed' (one word).", "severity": "low"},
            "no.": {"suggestion": "Do not use as an abbreviation for 'number' as it causes translation issues. Spell out 'number'.", "severity": "medium"},
            "non-English": {"suggestion": "Avoid. Use a more descriptive phrase like 'in languages other than English'.", "severity": "medium"},
            "notebook": {"suggestion": "Use 'notebook' for the UI element, but 'laptop' for the physical computer.", "severity": "low"},
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

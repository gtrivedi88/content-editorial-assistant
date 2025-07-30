"""
Word Usage Rule for words starting with 'Y'.
Enhanced with spaCy PhraseMatcher architecture (currently no patterns defined).
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class YWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'Y'.
    Enhanced with spaCy PhraseMatcher architecture (currently no patterns defined).
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_y'
    
    def _setup_patterns(self, nlp):
        """Initialize spaCy PhraseMatcher with Y-word patterns."""
        # Currently no specific Y-word usage rules are implemented.
        # The previous "your" rule was removed as it incorrectly flagged
        # general possessive pronouns, which are acceptable according to 
        # the IBM Style Guide. Possessives on abbreviations and trademarks
        # are handled by the possessives_rule.py instead.
        
        # No patterns to setup for Y words at this time
        word_details = {}
        self._setup_word_patterns(nlp, word_details)

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)
        
        # Ensure patterns are initialized (though empty)
        self._ensure_patterns_ready(nlp)

        # No Y-word patterns currently defined - return empty errors list
        return errors

"""
Word Usage Rule for words starting with 'Y'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class YWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'Y'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_y'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        # Currently no specific Y-word usage rules are implemented.
        # The previous "your" rule was removed as it incorrectly flagged
        # general possessive pronouns, which are acceptable according to 
        # the IBM Style Guide. Possessives on abbreviations and trademarks
        # are handled by the possessives_rule.py instead.
        
        return errors

"""
Word Usage Rule for words starting with 'X'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class XWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'X'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_x'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "XSA": {"suggestion": "Do not use. Use 'extended subarea addressing'.", "severity": "medium"},
            "xterm": {"suggestion": "Write as 'xterm' (lowercase).", "severity": "low"},
        }

        for i, sentence in enumerate(sentences):
            for word, details in word_map.items():
                if re.search(r'\b' + re.escape(word) + r'\b', sentence, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Review usage of the term '{word}'.",
                        suggestions=[details['suggestion']],
                        severity=details['severity']
                    ))
        return errors

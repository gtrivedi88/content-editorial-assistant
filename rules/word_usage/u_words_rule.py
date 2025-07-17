"""
Word Usage Rule for words starting with 'U'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class UWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'U'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_u'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "un-": {"suggestion": "Most words with the 'un-' prefix are not hyphenated (e.g., 'unnecessary').", "severity": "low"},
            "underbar": {"suggestion": "Use 'underscore'.", "severity": "medium"},
            "unselect": {"suggestion": "Use 'clear' for check boxes or 'deselect'.", "severity": "medium"},
            "up-to-date": {"suggestion": "Write as 'up to date' (no hyphens).", "severity": "low"},
            "user-friendly": {"suggestion": "Avoid subjective claims. Describe how the feature helps the user.", "severity": "high"},
            "user name": {"suggestion": "Use 'username' (one word).", "severity": "low"},
            "utilize": {"suggestion": "Use 'use'.", "severity": "medium"},
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

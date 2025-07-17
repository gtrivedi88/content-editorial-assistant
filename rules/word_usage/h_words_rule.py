"""
Word Usage Rule for words starting with 'H'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class HWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'H'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_h'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
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

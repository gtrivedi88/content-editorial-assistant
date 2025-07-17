"""
Word Usage Rule for words starting with 'W'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class WWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'W'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_w'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "w/": {"suggestion": "Spell out 'with'.", "severity": "medium"},
            "war room": {"suggestion": "Avoid military metaphors. Use 'command center' or 'operations center'.", "severity": "high"},
            "we": {"suggestion": "Avoid first-person pronouns in technical content.", "severity": "medium"},
            "web site": {"suggestion": "Use 'website' (one word).", "severity": "low"},
            "while": {"suggestion": "Use 'while' only to refer to time. For contrast, use 'although' or 'whereas'.", "severity": "medium"},
            "whitelist": {"suggestion": "Use inclusive language. Use 'allowlist'.", "severity": "high"},
            "Wi-Fi": {"suggestion": "Use 'Wi-Fi' for the certified technology and 'wifi' for a generic wireless connection.", "severity": "low"},
            "work station": {"suggestion": "Use 'workstation' (one word).", "severity": "low"},
            "world-wide": {"suggestion": "Use 'worldwide' (one word).", "severity": "low"},
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

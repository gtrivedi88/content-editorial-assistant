"""
Word Usage Rule for words starting with 'O'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class OWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'O'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_o'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
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

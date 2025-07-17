"""
Word Usage Rule for words starting with 'B'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class BWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'B'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_b'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "back-end": {"suggestion": "Write as 'back end' (noun) or use a more specific term like 'server'.", "severity": "low"},
            "back up": {"suggestion": "Use 'back up' (verb) and 'backup' (noun/adjective).", "severity": "low"},
            "backward compatible": {"suggestion": "Use 'compatible with earlier versions'.", "severity": "medium"},
            "bar code": {"suggestion": "Write as 'barcode'.", "severity": "low"},
            "below": {"suggestion": "Avoid relative locations. Use 'following' or 'in the next section'.", "severity": "medium"},
            "best practice": {"suggestion": "Use with caution. This is a subjective claim. Consider 'recommended practice'.", "severity": "high"},
            "beta": {"suggestion": "Use as an adjective (e.g., 'beta program'), not a noun.", "severity": "low"},
            "between": {"suggestion": "Do not use for ranges of numbers. Use an en dash (–) or 'from X to Y'.", "severity": "medium"},
            "blacklist": {"suggestion": "Use inclusive language. Use 'blocklist' instead.", "severity": "high"},
            "boot": {"suggestion": "Use 'start' or 'turn on' where possible.", "severity": "low"},
            "breadcrumb": {"suggestion": "Do not use 'BCT' as an abbreviation for 'breadcrumb trail'.", "severity": "low"},
            "built in": {"suggestion": "Hyphenate when used as an adjective before a noun: 'built-in'.", "severity": "low"},
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

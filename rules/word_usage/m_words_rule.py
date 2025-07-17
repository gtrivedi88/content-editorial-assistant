"""
Word Usage Rule for words starting with 'M'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class MWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'M'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_m'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "man-hour": {"suggestion": "Use inclusive language. Use 'person hour' or 'labor hour'.", "severity": "high"},
            "man day": {"suggestion": "Use inclusive language. Use 'person day'.", "severity": "high"},
            "master": {"suggestion": "Avoid when paired with 'slave'. Use 'primary', 'main', 'controller', or 'leader'.", "severity": "high"},
            "may": {"suggestion": "Use 'can' to indicate ability and 'might' to indicate possibility.", "severity": "medium"},
            "menu bar": {"suggestion": "Write as 'menubar' (one word).", "severity": "low"},
            "meta data": {"suggestion": "Write as 'metadata' (one word).", "severity": "low"},
            "methodology": {"suggestion": "Use only to refer to a group of methods. Often, 'method' is sufficient.", "severity": "low"},
            "migrate": {"suggestion": "Use correctly. 'Migrate' (move between systems) is not the same as 'upgrade' (new version) or 'port' (different OS).", "severity": "medium"},
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

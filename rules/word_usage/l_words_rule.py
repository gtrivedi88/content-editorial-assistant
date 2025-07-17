"""
Word Usage Rule for words starting with 'L'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class LWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'L'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_l'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "land and expand": {"suggestion": "Avoid this term due to colonial connotations. Use 'expansion strategy'.", "severity": "high"},
            "last name": {"suggestion": "Use the globally recognized term 'surname'.", "severity": "medium"},
            "leverage": {"suggestion": "Avoid in technical content; it does not translate well. Use 'use'.", "severity": "medium"},
            "licence": {"suggestion": "Use the spelling 'license'.", "severity": "low"},
            "lifecycle": {"suggestion": "Write as 'lifecycle' (one word).", "severity": "low"},
            "log on to": {"suggestion": "This is the correct form. Avoid 'log onto'.", "severity": "low"},
            "log off of": {"suggestion": "Use 'log off from'.", "severity": "medium"},
            "look and feel": {"suggestion": "Avoid this phrase. Be more specific about the UI characteristics.", "severity": "medium"},
            "lowercase": {"suggestion": "Write as 'lowercase' (one word).", "severity": "low"},
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

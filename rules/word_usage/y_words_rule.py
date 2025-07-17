"""
Word Usage Rule for words starting with 'Y'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class YWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'Y'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_y'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "you": {"suggestion": "Use second person ('you') to address the user directly. Avoid first person ('we', 'I').", "severity": "low"},
            "your": {"suggestion": "Use 'your' in reference to assets only after the user has customized them.", "severity": "medium"},
        }

        for i, sentence in enumerate(sentences):
            for word, details in word_map.items():
                if re.search(r'\b' + re.escape(word) + r'\b', sentence, re.IGNORECASE):
                    # This is a general guidance check, so it's best flagged for review.
                    if word == "your":
                         errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Review usage of the possessive pronoun '{word}'.",
                            suggestions=[details['suggestion']],
                            severity=details['severity']
                        ))
        return errors

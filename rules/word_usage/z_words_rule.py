"""
Word Usage Rule for words starting with 'Z'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class ZWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'Z'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_z'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "zero out": {"suggestion": "Use 'zero' as a verb.", "severity": "low"},
            "zero emissions": {"suggestion": "Avoid unsubstantiated environmental claims.", "severity": "high"},
            "zero trust": {"suggestion": "Write as two words, lowercase.", "severity": "low"},
            "zip": {"suggestion": "Avoid this term as it is a trademark. Use 'compress'.", "severity": "high"},
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

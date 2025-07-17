"""
Word Usage Rule for words starting with 'V'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class VWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'V'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_v'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "vanilla": {"suggestion": "Avoid jargon. Use 'basic', 'standard', or 'not customized'.", "severity": "medium"},
            "Velcro": {"suggestion": "This is a trademark. Use the generic term 'hook-and-loop fastener'.", "severity": "high"},
            "verbatim": {"suggestion": "Do not use as a noun. Use as an adjective or adverb.", "severity": "low"},
            "versus": {"suggestion": "Spell out 'versus'. Do not use 'vs.' or 'v.'.", "severity": "medium"},
            "via": {"suggestion": "Use to refer to routing data. For other contexts, 'by using' or 'through' might be clearer.", "severity": "low"},
            "vice versa": {"suggestion": "Write as shown (two words).", "severity": "low"},
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

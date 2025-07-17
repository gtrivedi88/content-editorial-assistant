"""
Word Usage Rule for words starting with 'Q'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class QWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'Q'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_q'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "Q&A": {"suggestion": "Write as 'Q&A' to mean 'question and answer'.", "severity": "low"},
            "quantum safe": {"suggestion": "Use 'quantum-safe' (hyphenated) as an adjective before a noun.", "severity": "low"},
            "quiesce": {"suggestion": "This is a valid technical term, but ensure it is used correctly (can be transitive or intransitive).", "severity": "low"},
            "quote": {"suggestion": "Do not use as a noun. Use 'quotation'. 'Quote' is a verb.", "severity": "medium"},
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

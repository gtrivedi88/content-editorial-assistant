"""
Word Usage Rule for words starting with 'R'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class RWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'R'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_r'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "read-only": {"suggestion": "Write as 'read-only' (hyphenated).", "severity": "low"},
            "real time": {"suggestion": "Use 'real-time' (hyphenated) as an adjective, and 'real time' (two words) as a noun.", "severity": "low"},
            "re-": {"suggestion": "Most words with the 're-' prefix are not hyphenated (e.g., 'reenter', 'reorder').", "severity": "low"},
            "Redbook": {"suggestion": "The correct term is 'IBM Redbooks publication'.", "severity": "high"},
            "refer to": {"suggestion": "For cross-references, prefer 'see'.", "severity": "low"},
            "respective": {"suggestion": "Avoid. Rewrite the sentence to be more direct.", "severity": "medium"},
            "roadmap": {"suggestion": "Write as 'roadmap' (one word).", "severity": "low"},
            "roll back": {"suggestion": "Use 'roll back' (verb) and 'rollback' (noun/adjective).", "severity": "low"},
            "run time": {"suggestion": "Use 'runtime' (one word) as an adjective, and 'run time' (two words) as a noun.", "severity": "low"},
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

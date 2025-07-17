"""
Word Usage Rule for words starting with 'I'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class IWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'I'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_i'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "i.e.": {"suggestion": "Use 'that is'.", "severity": "medium"},
            "IBMer": {"suggestion": "Use only in internal communications.", "severity": "high"},
            "inactivate": {"suggestion": "Use 'deactivate'.", "severity": "low"},
            "in as much as": {"suggestion": "Use 'because' or 'since'.", "severity": "medium"},
            "in-depth": {"suggestion": "Write as 'in depth' (two words).", "severity": "low"},
            "info": {"suggestion": "Avoid slang. Use 'information'.", "severity": "medium"},
            "in order to": {"suggestion": "Use the simpler term 'to'.", "severity": "low"},
            "input": {"suggestion": "Do not use as a verb. Use 'type' or 'enter'.", "severity": "medium"},
            "insure": {"suggestion": "Use 'ensure' to mean 'make sure'. 'Insure' relates to financial insurance.", "severity": "high"},
            "Internet": {"suggestion": "Use 'internet' (lowercase) unless part of a proper name like 'Internet of Things'.", "severity": "medium"},
            "invite": {"suggestion": "Do not use as a noun. Use 'invitation'.", "severity": "medium"},
            "issue": {"suggestion": "For commands, prefer 'run', 'type', or 'enter'.", "severity": "low"},
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

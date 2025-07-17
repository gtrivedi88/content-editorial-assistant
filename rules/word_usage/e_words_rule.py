"""
Word Usage Rule for words starting with 'E'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class EWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'E'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_e'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "e-business": {"suggestion": "Avoid. This term is outdated.", "severity": "high"},
            "e-mail": {"suggestion": "Use 'email' (one word).", "severity": "high"},
            "easy": {"suggestion": "Use with caution. This is a subjective claim.", "severity": "high"},
            "effortless": {"suggestion": "Use with caution. This is a subjective claim.", "severity": "high"},
            "e.g.": {"suggestion": "Use 'for example'.", "severity": "medium"},
            "enable": {"suggestion": "Focus on the user. Instead of 'this enables you to...', use 'you can...'.", "severity": "medium"},
            "end user": {"suggestion": "Use 'user' unless you need to differentiate types of users.", "severity": "low"},
            "engineer": {"suggestion": "Use only to refer to a person with an engineering degree. This is a legal requirement.", "severity": "high"},
            "ensure": {"suggestion": "Use 'ensure' to mean 'make sure'. Avoid suggesting a guarantee.", "severity": "medium"},
            "etc.": {"suggestion": "Avoid. Be specific or use 'and so on' for clear sequences.", "severity": "medium"},
            "evangelist": {"suggestion": "Avoid religious connotations. Use 'advocate' or 'influencer'.", "severity": "high"},
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

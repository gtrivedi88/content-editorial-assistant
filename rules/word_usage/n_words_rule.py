"""
Word Usage Rule for words starting with 'N'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class NWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'N'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_n'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        word_map = {
            "name space": {"suggestion": "Use 'namespace' (one word).", "severity": "low"},
            "native": {"suggestion": "Use with caution. Prefer more specific terms like 'local', 'basic', or 'default'.", "severity": "medium"},
            "need to": {"suggestion": "For mandatory actions, prefer 'must' or the imperative form (e.g., 'Back up your data').", "severity": "medium"},
            "new": {"suggestion": "Avoid using 'new' to describe products or features, as it becomes dated quickly.", "severity": "low"},
            "news feed": {"suggestion": "Write as 'newsfeed' (one word).", "severity": "low"},
            "no.": {"suggestion": "Do not use as an abbreviation for 'number' as it causes translation issues. Spell out 'number'.", "severity": "medium"},
            "non-English": {"suggestion": "Avoid. Use a more descriptive phrase like 'in languages other than English'.", "severity": "medium"},
            "notebook": {"suggestion": "Use 'notebook' for the UI element, but 'laptop' for the physical computer.", "severity": "low"},
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

"""
Word Usage Rule for words starting with 'A'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class AWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'A'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_a'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        # Linguistic Anchor: Dictionary of discouraged words and their suggestions.
        word_map = {
            "abort": {"suggestion": "Use 'cancel' or 'stop'.", "severity": "high"},
            "above": {"suggestion": "Avoid relative locations. Use 'previous' or 'preceding'.", "severity": "medium"},
            "action": {"suggestion": "Do not use as a verb. Use a more specific verb like 'run' or 'perform'.", "severity": "medium"},
            "ad hoc": {"suggestion": "Write as two words: 'ad hoc'.", "severity": "low"},
            "adviser": {"suggestion": "Use 'advisor'.", "severity": "low"},
            "afterwards": {"suggestion": "Use 'afterward'.", "severity": "low"},
            "allow": {"suggestion": "Focus on the user. Instead of 'the product allows you to...', use 'you can use the product to...'.", "severity": "medium"},
            "amongst": {"suggestion": "Use 'among'.", "severity": "low"},
            "and/or": {"suggestion": "Avoid 'and/or'. Use 'a or b', or 'a, b, or both'.", "severity": "medium"},
            "appear": {"suggestion": "Do not use for UI elements. Use 'open' or 'is displayed'.", "severity": "medium"},
            "architect": {"suggestion": "Do not use as a verb. Use 'design', 'plan', or 'structure'.", "severity": "high"},
            "asap": {"suggestion": "Avoid informal abbreviations. Use 'as soon as possible'.", "severity": "medium"},
        }

        for i, sentence in enumerate(sentences):
            for word, details in word_map.items():
                # Use regex for whole word matching, case-insensitive
                if re.search(r'\b' + re.escape(word) + r'\b', sentence, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Consider an alternative for the word '{word}'.",
                        suggestions=[details['suggestion']],
                        severity=details['severity']
                    ))
        return errors

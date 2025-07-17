"""
Word Usage Rule for special characters and numbers.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

class SpecialCharsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific special characters and numbers.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_special'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        # Using regex patterns as keys for more precise matching.
        pattern_map = {
            # Looks for a standalone #, not part of a word (like a hex code #FFFFFF or hashtag #style)
            r'(?<!\w)#(?!\w)': {"suggestion": "Use 'number sign' to refer to the # character. For hashtags, spell out if possible.", "severity": "low"},
            r'\b24/7\b': {"suggestion": "Avoid. Use '24x7' or descriptive wording like '24 hours a day, every day'.", "severity": "medium"},
            # Added rule for 0-9 based on fiscal period formatting
            r'\b[HQ][1-4]\b': {"suggestion": "For fiscal periods, the numeral should precede the letter (e.g., '1H', '2Q').", "severity": "medium"},
        }

        for i, sentence in enumerate(sentences):
            for pattern, details in pattern_map.items():
                # Find all occurrences of the pattern in the sentence
                matches = re.finditer(pattern, sentence, re.IGNORECASE)
                for match in matches:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Review usage of the term '{match.group()}'.",
                        suggestions=[details['suggestion']],
                        severity=details['severity']
                    ))
        return errors

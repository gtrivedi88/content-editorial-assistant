"""
Word Usage Rule for special characters and numbers.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class SpecialCharsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific special characters and numbers.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_special'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        pattern_map = {
            r'(?<!\w)#(?!\w)': {"suggestion": "Use 'number sign' to refer to the # character, or 'hash sign' for hashtags.", "severity": "low"},
            r'\b24/7\b': {"suggestion": "Avoid. Use '24x7' or descriptive wording like '24 hours a day, every day'.", "severity": "medium"},
            r'\b[HQ][1-4]\b': {"suggestion": "For fiscal periods, the numeral should precede the letter (e.g., '1H', '2Q').", "severity": "medium"},
        }

        for i, sent in enumerate(doc.sents):
            for pattern, details in pattern_map.items():
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Review usage of the term '{match.group()}'.",
                        suggestions=[details['suggestion']],
                        severity=details['severity'],
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors

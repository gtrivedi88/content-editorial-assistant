"""
Word Usage Rule for words starting with 'X'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class XWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'X'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_x'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        word_map = {
            "XSA": {"suggestion": "Do not use. Use 'extended subarea addressing'.", "severity": "medium"},
            "xterm": {"suggestion": "Write as 'xterm' (lowercase).", "severity": "low"},
        }

        for i, sent in enumerate(doc.sents):
            for word, details in word_map.items():
                for match in re.finditer(r'\b' + re.escape(word) + r'\b', sent.text): # Case-sensitive for these terms
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

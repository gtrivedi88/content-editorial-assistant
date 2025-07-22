"""
Word Usage Rule for words starting with 'Y'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class YWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'Y'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_y'

    def analyze(self, text: str, sentences: List[str], spacy_doc=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not spacy_doc:
            return errors
        doc = spacy_doc

        # This rule provides contextual advice, so it's a good candidate for a low-severity check.
        for i, sent in enumerate(doc.sents):
            for match in re.finditer(r'\b(your)\b', sent.text, re.IGNORECASE):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Review usage of the possessive pronoun 'your'.",
                    suggestions=["Use 'your' in reference to assets only after the user has customized them."],
                    severity='low',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
        return errors

"""
Word Usage Rule for words starting with 'U'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class UWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'U'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_u'

    def analyze(self, text: str, sentences: List[str], spacy_doc=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not spacy_doc:
            return errors
        doc = spacy_doc

        word_map = {
            "un-": {"suggestion": "Most words with the 'un-' prefix are not hyphenated (e.g., 'unnecessary').", "severity": "low"},
            "underbar": {"suggestion": "Use 'underscore'.", "severity": "medium"},
            "unselect": {"suggestion": "Use 'clear' for check boxes or 'deselect'.", "severity": "medium"},
            "up-to-date": {"suggestion": "Write as 'up to date' (no hyphens).", "severity": "low"},
            "user-friendly": {"suggestion": "Avoid subjective claims. Describe how the feature helps the user.", "severity": "high"},
            "user name": {"suggestion": "Use 'username' (one word).", "severity": "low"},
            "utilize": {"suggestion": "Use 'use'.", "severity": "medium"},
        }

        for i, sent in enumerate(doc.sents):
            for word, details in word_map.items():
                for match in re.finditer(r'\b' + re.escape(word) + r'\b', sent.text, re.IGNORECASE):
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

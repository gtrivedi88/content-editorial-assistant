"""
Word Usage Rule for words starting with 'O'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class OWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'O'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_o'

    def analyze(self, text: str, sentences: List[str], spacy_doc=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not spacy_doc:
            return errors
        doc = spacy_doc

        word_map = {
            "off of": {"suggestion": "Use 'off' or 'from'.", "severity": "medium"},
            "off-line": {"suggestion": "Use 'offline' (one word).", "severity": "low"},
            "OK": {"suggestion": "Use only to refer to a UI element label. Do not use 'okay'.", "severity": "medium"},
            "on-boarding": {"suggestion": "Use 'onboarding' (one word).", "severity": "low"},
            "on premise": {"suggestion": "Use 'on-premises' (adjective) or 'on premises' (adverb).", "severity": "medium"},
            "on the fly": {"suggestion": "Avoid jargon. Use 'dynamically' or 'during processing'.", "severity": "medium"},
            "orientate": {"suggestion": "Use 'orient'.", "severity": "low"},
            "our": {"suggestion": "Avoid first-person pronouns in technical content.", "severity": "medium"},
            "out-of-the-box": {"suggestion": "Use 'out of the box' (no hyphens).", "severity": "low"},
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

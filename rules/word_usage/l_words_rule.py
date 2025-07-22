"""
Word Usage Rule for words starting with 'L'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class LWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'L'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_l'

    def analyze(self, text: str, sentences: List[str], spacy_doc=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not spacy_doc:
            return errors
        doc = spacy_doc

        word_map = {
            "land and expand": {"suggestion": "Avoid this term due to colonial connotations. Use 'expansion strategy'.", "severity": "high"},
            "last name": {"suggestion": "Use the globally recognized term 'surname'.", "severity": "medium"},
            "leverage": {"suggestion": "Avoid in technical content; it does not translate well. Use 'use'.", "severity": "medium"},
            "licence": {"suggestion": "Use the spelling 'license'.", "severity": "low"},
            "lifecycle": {"suggestion": "Write as 'lifecycle' (one word).", "severity": "low"},
            "log on to": {"suggestion": "This is the correct form. Avoid 'log onto'.", "severity": "low"},
            "log off of": {"suggestion": "Use 'log off from'.", "severity": "medium"},
            "look and feel": {"suggestion": "Avoid this phrase. Be more specific about the UI characteristics.", "severity": "medium"},
            "lowercase": {"suggestion": "Write as 'lowercase' (one word).", "severity": "low"},
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

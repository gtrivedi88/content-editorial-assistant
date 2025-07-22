"""
Word Usage Rule for words starting with 'K'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class KWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'K'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_k'

    def analyze(self, text: str, sentences: List[str], spacy_doc=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not spacy_doc:
            return errors
        doc = spacy_doc

        word_map = {
            "kebab menu": {"suggestion": "Avoid food-related UI terms. Use the element's tooltip name or 'overflow menu'.", "severity": "medium"},
            "key": {"suggestion": "Do not use 'key' as a verb. Use 'type' or 'press'.", "severity": "medium"},
            "key ring": {"suggestion": "Use 'keyring' (one word).", "severity": "low"},
            "keystore": {"suggestion": "Write as 'keystore' (one word).", "severity": "low"},
            "keyword": {"suggestion": "Write as 'keyword' (one word).", "severity": "low"},
            "kick off": {"suggestion": "Avoid jargon. Use 'start'.", "severity": "medium"},
            "kill": {"suggestion": "Avoid this term unless documenting a UNIX system. Use 'end' or 'stop'.", "severity": "medium"},
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

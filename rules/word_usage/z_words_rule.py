"""
Word Usage Rule for words starting with 'Z'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ZWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'Z'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_z'

    def analyze(self, text: str, sentences: List[str], spacy_doc=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not spacy_doc:
            return errors
        doc = spacy_doc

        word_map = {
            "zero out": {"suggestion": "Use 'zero' as a verb.", "severity": "low"},
            "zero emissions": {"suggestion": "Avoid unsubstantiated environmental claims.", "severity": "high"},
            "zero trust": {"suggestion": "Write as two words, lowercase.", "severity": "low"},
            "zip": {"suggestion": "Avoid this term as it is a trademark. Use 'compress'.", "severity": "high"},
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

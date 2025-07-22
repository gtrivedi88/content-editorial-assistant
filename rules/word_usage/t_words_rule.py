"""
Word Usage Rule for words starting with 'T'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class TWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'T'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_t'

    def analyze(self, text: str, sentences: List[str], spacy_doc=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not spacy_doc:
            return errors
        doc = spacy_doc

        word_map = {
            "tap on": {"suggestion": "Omit 'on'. Use 'tap the icon'.", "severity": "medium"},
            "tarball": {"suggestion": "Use '.tar file'.", "severity": "medium"},
            "team room": {"suggestion": "Use 'teamroom' (one word).", "severity": "low"},
            "terminate": {"suggestion": "Prefer simpler terms like 'end' or 'stop'.", "severity": "low"},
            "thank you": {"suggestion": "Avoid in technical information.", "severity": "medium"},
            "that": {"suggestion": "Include 'that' in clauses for clarity, e.g., 'Verify that the service is running.'", "severity": "low"},
            "time frame": {"suggestion": "Use 'timeframe' (one word).", "severity": "low"},
            "time out": {"suggestion": "Use 'time out' (verb) and 'timeout' (noun/adjective).", "severity": "low"},
            "toast": {"suggestion": "Avoid food names for UI elements. Use 'notification'.", "severity": "medium"},
            "tool kit": {"suggestion": "Use 'toolkit' (one word).", "severity": "low"},
            "trade-off": {"suggestion": "Use 'tradeoff' (one word).", "severity": "low"},
            "transparent": {"suggestion": "Use with caution as it can be ambiguous (invisible or easy to understand).", "severity": "medium"},
            "tribe": {"suggestion": "Avoid this term. Use 'team' or 'squad'.", "severity": "high"},
            "try and": {"suggestion": "Use 'try to'.", "severity": "medium"},
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

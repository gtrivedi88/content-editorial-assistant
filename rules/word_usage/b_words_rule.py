"""
Word Usage Rule for words starting with 'B'.
"""
from typing import List, Dict, Any
from .base_word_usage_rule import BaseWordUsageRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class BWordsRule(BaseWordUsageRule):
    """
    Checks for the incorrect usage of specific words starting with 'B'.
    """
    def _get_rule_type(self) -> str:
        return 'word_usage_b'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        # Context-aware checks
        for token in doc:
            if token.lemma_ == "backup" and token.pos_ == "VERB":
                sent = token.sent
                # Find sentence index in document
                sentence_idx = list(doc.sents).index(sent)
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=sentence_idx,
                    message="Incorrect verb form: 'backup' should be 'back up'.",
                    suggestions=["Use 'back up' (two words) for the verb form."],
                    severity='medium',
                    span=(token.idx, token.idx + len(token.text)),
                    flagged_text=token.text
                ))
            if token.lemma_ == "back" and token.i + 1 < len(doc) and doc[token.i + 1].lemma_ == "up" and token.dep_ in ("compound", "amod"):
                sent = token.sent
                next_token = doc[token.i + 1]
                # Find sentence index in document
                sentence_idx = list(doc.sents).index(sent)
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=sentence_idx,
                    message="Incorrect noun/adjective form: 'back up' should be 'backup'.",
                    suggestions=["Use 'backup' (one word) for the noun or adjective form."],
                    severity='medium',
                    span=(token.idx, next_token.idx + len(next_token.text)),
                    flagged_text=f"{token.text} {next_token.text}"
                ))

        # General word map
        word_map = {
            "back-end": {"suggestion": "Write as 'back end' (noun) or use a more specific term like 'server'.", "severity": "low"},
            "backward compatible": {"suggestion": "Use 'compatible with earlier versions'.", "severity": "medium"},
            "bar code": {"suggestion": "Write as 'barcode'.", "severity": "low"},
            "below": {"suggestion": "Avoid relative locations. Use 'following' or 'in the next section'.", "severity": "medium"},
            "best practice": {"suggestion": "Use with caution. This is a subjective claim. Consider 'recommended practice'.", "severity": "high"},
            "beta": {"suggestion": "Use as an adjective (e.g., 'beta program'), not a noun.", "severity": "low"},
            "between": {"suggestion": "Do not use for ranges of numbers. Use an en dash (–) or 'from X to Y'.", "severity": "medium"},
            "blacklist": {"suggestion": "Use inclusive language. Use 'blocklist' instead.", "severity": "high"},
            "boot": {"suggestion": "Use 'start' or 'turn on' where possible.", "severity": "low"},
            "breadcrumb": {"suggestion": "Do not use 'BCT' as an abbreviation for 'breadcrumb trail'.", "severity": "low"},
            "built in": {"suggestion": "Hyphenate when used as an adjective before a noun: 'built-in'.", "severity": "low"},
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

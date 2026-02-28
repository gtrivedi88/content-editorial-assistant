"""
Ellipses Rule
Based on IBM Style Guide (p.127): Avoid using ellipses in text in most cases.
"""
import re
from typing import List, Dict, Any, Optional

from .base_punctuation_rule import BasePunctuationRule

# Matches the Unicode ellipsis character or three consecutive dots
_ELLIPSIS_RE = re.compile(r'\u2026|\.\.\.')

_SKIP_BLOCK_TYPES = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

_MESSAGE = (
    "Avoid using ellipses in technical information. "
    "Write complete phrases instead."
)

_SUGGESTIONS = [
    "Remove the ellipsis and write a complete sentence.",
    "If indicating omitted text in a quotation, use bracketed ellipsis [...].",
]


def _is_bracketed(sentence: str, start: int, end: int) -> bool:
    """Return True if the ellipsis is wrapped in brackets, e.g. [...]."""
    before = sentence[start - 1] if start > 0 else ''
    after = sentence[end] if end < len(sentence) else ''
    return before == '[' and after == ']'


class EllipsesRule(BasePunctuationRule):
    """Flags ellipsis usage in technical prose."""

    def _get_rule_type(self) -> str:
        return 'ellipses'

    def analyze(
        self,
        text: str,
        sentences: List[str],
        nlp=None,
        context: Optional[Dict[str, Any]] = None,
        spacy_doc=None,
    ) -> List[Dict[str, Any]]:
        context = context or {}

        if context.get('block_type') in _SKIP_BLOCK_TYPES:
            return []

        errors: List[Dict[str, Any]] = []

        for i, sentence in enumerate(sentences):
            for match in _ELLIPSIS_RE.finditer(sentence):
                if _is_bracketed(sentence, match.start(), match.end()):
                    continue

                error = self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=_MESSAGE,
                    suggestions=list(_SUGGESTIONS),
                    severity='low',
                    text=text,
                    context=context,
                    span=(match.start(), match.end()),
                    flagged_text=match.group(0),
                )
                if error is not None:
                    errors.append(error)

        return errors

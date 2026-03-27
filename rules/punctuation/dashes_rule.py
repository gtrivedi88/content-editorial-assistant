"""
Dashes Rule
Based on IBM Style Guide (p.125): Do not use em dashes in technical information.
Use commas, parentheses, or a colon instead. En dashes are acceptable for ranges.
"""
import re
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_punctuation_rule import BasePunctuationRule

# Matches the Unicode em dash character or two consecutive hyphens (common substitute)
_EM_DASH_RE = re.compile(r'\u2014|--')

_SKIP_BLOCK_TYPES = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

_MESSAGE = (
    "Do not use em dashes in technical information. "
    "Use commas, parentheses, or a colon instead."
)

_SUGGESTIONS = [
    "Replace the em dash with a comma, parentheses, or a colon.",
]


def _is_ascii_em_dash_fp(sentence: str, match: re.Match[str]) -> bool:
    """Return True if a ``--`` match is a CLI flag or multi-hyphen delimiter.

    Guards against false positives on:
    - CLI flags (``--enforce``, ``--verbose``)
    - AsciiDoc delimiters (``----``, ``---``)
    - Any multi-hyphen sequence that is not an em dash substitute

    Args:
        sentence: The sentence containing the match.
        match: The regex match object for ``--``.

    Returns:
        True if the match should be skipped.
    """
    start = match.start()
    end = match.end()
    if end < len(sentence) and sentence[end].isalpha():
        return True
    if end < len(sentence) and sentence[end] == '-':
        return True
    if start > 0 and sentence[start - 1] == '-':
        return True
    return False


class DashesRule(BasePunctuationRule):
    """Flags em dash usage in technical prose."""

    def _get_rule_type(self) -> str:
        return 'dashes'

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

        code_ranges = context.get("inline_code_ranges", [])
        errors: List[Dict[str, Any]] = []

        for i, sentence in enumerate(sentences):
            sent_start = text.find(sentence)
            for match in _EM_DASH_RE.finditer(sentence):
                if in_code_range(sent_start + match.start(), code_ranges):
                    continue
                if match.group(0) == '--' and _is_ascii_em_dash_fp(sentence, match):
                    continue
                error = self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=_MESSAGE,
                    suggestions=list(_SUGGESTIONS),
                    severity='medium',
                    text=text,
                    context=context,
                    span=(match.start(), match.end()),
                    flagged_text=match.group(0),
                )
                if error is not None:
                    errors.append(error)

        return errors

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

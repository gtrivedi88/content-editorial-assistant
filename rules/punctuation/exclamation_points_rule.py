"""
Exclamation Points Rule
Based on IBM Style Guide (p.128): Use exclamation points sparingly.
Avoid multiple exclamation points.
"""
import re
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_punctuation_rule import BasePunctuationRule

# Single exclamation point (not inside quotes)
_EXCLAMATION_RE = re.compile(r'!+')

# Quoted text pattern: "..." or '...'
_QUOTED_RE = re.compile(r"""(?:"[^"]*"|'[^']*')""")

_SKIP_BLOCK_TYPES = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

_MESSAGE = (
    "Avoid exclamation points in technical information. "
    "Rephrase for emphasis."
)

_MESSAGE_MULTIPLE = (
    "Do not use multiple exclamation points. "
    "Rephrase for emphasis or use a single period."
)

_SUGGESTIONS = [
    "Replace the exclamation point with a period.",
]

_SUGGESTIONS_MULTIPLE = [
    "Remove the extra exclamation points.",
    "Replace with a single period and rephrase for emphasis.",
]


def _remove_quoted_text(sentence: str) -> str:
    """Replace quoted spans with whitespace so they are not scanned."""
    return _QUOTED_RE.sub(lambda m: ' ' * len(m.group(0)), sentence)


class ExclamationPointsRule(BasePunctuationRule):
    """Flags exclamation point usage in technical prose."""

    def _get_rule_type(self) -> str:
        return 'exclamation_points'

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
            self._check_sentence(sentence, i, text, context,
                                 code_ranges, errors)
        return errors

    def _check_sentence(self, sentence, idx, text, context,
                        code_ranges, errors):
        """Scan a single sentence for exclamation point usage."""
        sent_start = text.find(sentence)
        cleaned = _remove_quoted_text(sentence)
        for match in _EXCLAMATION_RE.finditer(cleaned):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            is_multiple = len(match.group(0)) > 1
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=_MESSAGE_MULTIPLE if is_multiple else _MESSAGE,
                suggestions=list(
                    _SUGGESTIONS_MULTIPLE if is_multiple else _SUGGESTIONS
                ),
                severity='medium',
                text=text,
                context=context,
                span=(match.start(), match.end()),
                flagged_text=match.group(0),
            )
            if error is not None:
                errors.append(error)

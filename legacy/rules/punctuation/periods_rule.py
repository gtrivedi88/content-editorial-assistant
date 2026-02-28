"""
Periods Rule
Based on IBM Style Guide (p.133): Period usage rules.

Deterministic checks:
  1. Periods in uppercase abbreviations (e.g. "U.S.A." -> "USA").
  2. Duplicate periods ("..") that are likely typos.

Guards: skip code blocks, inline code, and legitimate abbreviations.
"""
import re
from typing import List, Dict, Any, Optional

from .base_punctuation_rule import BasePunctuationRule

# Block types that are never prose
_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

# Check 1: uppercase abbreviations with periods -- U.S.A., A.P.I., E.U.
_ABBREV_WITH_PERIODS = re.compile(r'\b([A-Z]\.(?:[A-Z]\.)+[A-Z]?\.?)\b')

# Abbreviations that legitimately keep periods
_LEGIT_ABBREVS = frozenset([
    'A.M.', 'P.M.', 'A.M', 'P.M',
    'U.S.', 'U.K.', 'U.S', 'U.K',
    'P.O.', 'P.O',
])

# Check 2: exactly two consecutive periods (not ellipsis which is three)
_DOUBLE_PERIOD = re.compile(r'\.\.(?!\.)')

# Guard: inline code spans
_INLINE_CODE = re.compile(r'`[^`]+`')


def _inline_code_ranges(text: str) -> List[tuple]:
    """Return (start, end) ranges for inline code spans."""
    return [(m.start(), m.end()) for m in _INLINE_CODE.finditer(text)]


def _in_ranges(pos: int, ranges: List[tuple]) -> bool:
    for start, end in ranges:
        if start <= pos < end:
            return True
    return False


class PeriodsRule(BasePunctuationRule):
    """Flag periods in abbreviations and duplicate periods."""

    def _get_rule_type(self) -> str:
        return 'periods'

    def analyze(
        self,
        text: str,
        sentences: List[str],
        nlp=None,
        context: Optional[Dict[str, Any]] = None,
        spacy_doc=None,
    ) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            code_ranges = _inline_code_ranges(sentence)
            self._check_abbreviation_periods(
                sentence, idx, text, context, code_ranges, errors,
            )
            self._check_duplicate_periods(
                sentence, idx, text, context, code_ranges, errors,
            )
        return errors

    # ------------------------------------------------------------------
    # Check 1 -- periods in uppercase abbreviations
    # ------------------------------------------------------------------
    def _check_abbreviation_periods(
        self, sentence: str, idx: int, text: str,
        context: Dict[str, Any], code_ranges: List[tuple],
        errors: List[Dict[str, Any]],
    ) -> None:
        for match in _ABBREV_WITH_PERIODS.finditer(sentence):
            if _in_ranges(match.start(), code_ranges):
                continue
            found = match.group(1)
            if found.upper().rstrip('.') + '.' in _LEGIT_ABBREVS:
                continue
            if found.upper().rstrip('.') in _LEGIT_ABBREVS:
                continue
            corrected = found.replace('.', '')
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Do not use periods in abbreviations: "
                    f"'{found}' -> '{corrected}'."
                ),
                suggestions=[
                    f"Write '{corrected}' instead of '{found}'.",
                    "Modern style guides prefer abbreviations without periods.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=found,
                span=(match.start(), match.end()),
            )
            if error is not None:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 -- duplicate periods
    # ------------------------------------------------------------------
    def _check_duplicate_periods(
        self, sentence: str, idx: int, text: str,
        context: Dict[str, Any], code_ranges: List[tuple],
        errors: List[Dict[str, Any]],
    ) -> None:
        for match in _DOUBLE_PERIOD.finditer(sentence):
            if _in_ranges(match.start(), code_ranges):
                continue
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message="Duplicate period detected. Use a single period.",
                suggestions=[
                    "Remove the extra period.",
                    "Use an ellipsis (...) if a trailing-off effect is intended.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error is not None:
                errors.append(error)

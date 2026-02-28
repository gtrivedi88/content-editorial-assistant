"""
Product Versions Rule — Deterministic regex-based detection.
IBM Style Guide (p. 233-234):
1. Do not prefix version numbers with "V.", "Version.", "R.", or "Release."
   Use just the version number.
2. Avoid prefixing with single letters "V" or "R" before a version number.

Guards: skip code blocks, inline code, git tags, and changelog entries.
"""
import re
from typing import List, Dict, Any, Optional

from .base_references_rule import BaseReferencesRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Check 1: Problematic prefixes with period (V.2.0, Version.3)
# These are always wrong per IBM Style.
_PREFIX_WITH_PERIOD = re.compile(
    r'\b(V|R|Ver|Version|Release)\.\s*(\d+(?:\.\d+)*)',
    re.IGNORECASE,
)

# Check 2: Single-letter prefixes without period (V2.0, R3.1)
# Flagged as moderate — prefer just the number.
_SINGLE_LETTER_PREFIX = re.compile(
    r'\b([VR])(\d+(?:\.\d+)*)\b',
)

# Check 3: Full-word prefix (Version 2.0, Release 3.1)
# Moderate — IBM Style prefers just the number in most contexts.
_WORD_PREFIX = re.compile(
    r'\b(Version|Release)\s+(\d+(?:\.\d+)*)\b',
    re.IGNORECASE,
)

# Guard: inline code spans
_INLINE_CODE = re.compile(r'`[^`]+`')

# Guard: git tag patterns (v1.2.3 is standard in git)
_GIT_TAG = re.compile(r'\bgit\b|\btag\b|\bbranch\b|\bcommit\b', re.IGNORECASE)

# Guard: changelog/release-notes context
_CHANGELOG = re.compile(r'\bchangelog\b|\brelease\s+notes?\b', re.IGNORECASE)


def _inline_code_ranges(text: str) -> List[tuple]:
    return [(m.start(), m.end()) for m in _INLINE_CODE.finditer(text)]


def _in_ranges(pos: int, ranges: List[tuple]) -> bool:
    for start, end in ranges:
        if start <= pos < end:
            return True
    return False


class ProductVersionsRule(BaseReferencesRule):
    """Flag incorrect version number prefixes."""

    def _get_rule_type(self) -> str:
        return 'references_product_versions'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            # Guard: skip git/changelog contexts
            if _GIT_TAG.search(sentence) or _CHANGELOG.search(sentence):
                continue

            code_ranges = _inline_code_ranges(sentence)
            self._check_prefix_with_period(sentence, idx, text, context, code_ranges, errors)
            self._check_single_letter_prefix(sentence, idx, text, context, code_ranges, errors)
            self._check_word_prefix(sentence, idx, text, context, code_ranges, errors)
        return errors

    # ------------------------------------------------------------------
    # Check 1 — prefix with period (V.2.0, Version.3)
    # ------------------------------------------------------------------
    def _check_prefix_with_period(self, sentence, idx, text, context,
                                  code_ranges, errors):
        for match in _PREFIX_WITH_PERIOD.finditer(sentence):
            if _in_ranges(match.start(), code_ranges):
                continue
            prefix = match.group(1)
            version = match.group(2)
            found = match.group(0)
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Do not use '{prefix}.' before version numbers. "
                    f"Write just the version number: '{version}'."
                ),
                suggestions=[
                    f"Write '{version}' instead of '{found}'.",
                    "IBM Style: use only the version number without a prefix.",
                ],
                severity='high',
                text=text,
                context=context,
                flagged_text=found,
                span=(match.start(), match.end()),
            )
            if error is not None:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 — single-letter prefix (V2.0, R3.1)
    # ------------------------------------------------------------------
    def _check_single_letter_prefix(self, sentence, idx, text, context,
                                    code_ranges, errors):
        for match in _SINGLE_LETTER_PREFIX.finditer(sentence):
            if _in_ranges(match.start(), code_ranges):
                continue
            prefix = match.group(1)
            version = match.group(2)
            found = match.group(0)
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Remove the '{prefix}' prefix from the version number. "
                    f"Write '{version}' instead of '{found}'."
                ),
                suggestions=[
                    f"Write '{version}' instead of '{found}'.",
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
    # Check 3 — full-word prefix (Version 2.0, Release 3.1)
    # ------------------------------------------------------------------
    def _check_word_prefix(self, sentence, idx, text, context,
                           code_ranges, errors):
        for match in _WORD_PREFIX.finditer(sentence):
            if _in_ranges(match.start(), code_ranges):
                continue
            full = match.group(0)
            prefix = match.group(1)
            version = match.group(2)

            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Consider removing '{prefix}' before the version number. "
                    f"IBM Style prefers just '{version}'."
                ),
                suggestions=[
                    f"Write '{version}' instead of '{full}'.",
                    f"Use the version number alone: '{version}'.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=full,
                span=(match.start(), match.end()),
            )
            if error is not None:
                errors.append(error)

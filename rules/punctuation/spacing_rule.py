"""
Spacing Rule
Deterministic checks for spacing violations in prose:
  1. Double spaces between words.
  2. Missing space after period, comma, colon, or semicolon.

Guards: skip code blocks, URLs, version numbers, file paths,
IP addresses, and decimal numbers.
"""
import re
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_punctuation_rule import BasePunctuationRule

# Block types that are never prose
_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

# --- Check 1: two or more consecutive spaces between non-whitespace ---
_DOUBLE_SPACE = re.compile(r'(?<=\S) {2,}(?=\S)')

# --- Check 2: missing space after sentence punctuation ---
# Matches . , : ; immediately followed by a word character that is NOT a digit
# or closing paren (avoids decimals, version numbers, time, smileys).
_MISSING_SPACE = re.compile(r'([.,:;])([A-Za-z])')

# --- Guard patterns (regions to skip entirely) ---
_URL_PATTERN = re.compile(r'https?://\S+|www\.\S+', re.IGNORECASE)
_VERSION_PATTERN = re.compile(r'\b\d+\.\d+(?:\.\d+)*\b')
_IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')
_DECIMAL_PATTERN = re.compile(r'\b\d+\.\d+\b')
_FILE_EXT_PATTERN = re.compile(
    r'\b[\w\-]+\.'
    r'(?:txt|md|yaml|yml|json|xml|html|css|js|ts|py|rb|go|rs|java|'
    r'c|cpp|h|sh|conf|cfg|ini|log|csv|sql|toml|adoc|rst)\b',
    re.IGNORECASE,
)
_DOTTED_IDENT = re.compile(
    r'\b[a-zA-Z_][\w]*(?:\.[\w]+){2,}\b'  # auth.secret.ref.name
)
_INLINE_CODE = re.compile(r'`[^`]+`')
_PATH_PATTERN = re.compile(r'(?:/[\w.\-]+){2,}')
_TIME_PATTERN = re.compile(r'\b\d{1,2}:\d{2}(?::\d{2})?\b')

# All guard patterns collected for merging
_GUARD_PATTERNS = [
    _URL_PATTERN, _VERSION_PATTERN, _IP_PATTERN, _DECIMAL_PATTERN,
    _FILE_EXT_PATTERN, _DOTTED_IDENT, _INLINE_CODE, _PATH_PATTERN,
    _TIME_PATTERN,
]


def _exclusion_ranges(text: str) -> List[tuple]:
    """Return sorted, merged (start, end) ranges that must be skipped."""
    raw: List[tuple] = []
    for pat in _GUARD_PATTERNS:
        for m in pat.finditer(text):
            raw.append((m.start(), m.end()))
    if not raw:
        return []
    raw.sort()
    merged = [raw[0]]
    for start, end in raw[1:]:
        prev_s, prev_e = merged[-1]
        if start <= prev_e:
            merged[-1] = (prev_s, max(prev_e, end))
        else:
            merged.append((start, end))
    return merged


def _in_exclusion(pos: int, ranges: List[tuple]) -> bool:
    for start, end in ranges:
        if start <= pos < end:
            return True
    return False


class SpacingRule(BasePunctuationRule):
    """Flag double spaces and missing spaces after punctuation."""

    def _get_rule_type(self) -> str:
        return 'spacing'

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

        code_ranges = context.get("inline_code_ranges", [])
        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            excl = _exclusion_ranges(sentence)
            sent_start = text.find(sentence)
            self._check_double_spaces(
                sentence, idx, text, context, excl, code_ranges,
                sent_start, errors,
            )
            self._check_missing_space(
                sentence, idx, text, context, excl, code_ranges,
                sent_start, errors,
            )
        return errors

    # ------------------------------------------------------------------
    # Check 1 -- double spaces
    # ------------------------------------------------------------------
    def _check_double_spaces(
        self, sentence: str, idx: int, text: str,
        context: Dict[str, Any], excl: List[tuple],
        code_ranges: list, sent_start: int,
        errors: List[Dict[str, Any]],
    ) -> None:
        for match in _DOUBLE_SPACE.finditer(sentence):
            if _in_exclusion(match.start(), excl):
                continue
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message="Remove extra spaces. Use a single space.",
                suggestions=["Replace multiple consecutive spaces with one space."],
                severity='low',
                text=text,
                context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error is not None:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 -- missing space after punctuation
    # ------------------------------------------------------------------
    def _check_missing_space(
        self, sentence: str, idx: int, text: str,
        context: Dict[str, Any], excl: List[tuple],
        code_ranges: list, sent_start: int,
        errors: List[Dict[str, Any]],
    ) -> None:
        for match in _MISSING_SPACE.finditer(sentence):
            if _in_exclusion(match.start(), excl):
                continue
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            punct = match.group(1)
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=f"Add a space after '{punct}'.",
                suggestions=[f"Insert a space between '{punct}' and the following word."],
                severity='medium',
                text=text,
                context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error is not None:
                errors.append(error)

"""
Notes Rule — Deterministic regex-based detection.
IBM Style Guide (p. 204-205): Note label formatting.

Checks:
  1. Note labels must be followed by a colon (e.g. "Note:" not "Note").
  2. "Recommendation" is not an approved label.

Approved labels: Note, Exception, Fast path, Important, Remember,
                 Requirement, Restriction, Tip, Attention, Caution,
                 Danger, Warning.

Guards: skip code blocks. Only fires on lines that START with a known label.
"""
import re
from typing import List, Dict, Any, Optional

from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

# Approved single-word labels (case-insensitive)
_SINGLE_LABELS = [
    'Note', 'Exception', 'Important', 'Remember', 'Requirement',
    'Restriction', 'Tip', 'Attention', 'Caution', 'Danger', 'Warning',
]
# Approved multi-word labels
_MULTI_LABELS = ['Fast path']

# Build regex: line starts with label, NOT followed by a colon
_SINGLE_PATTERN = re.compile(
    r'^(' + '|'.join(re.escape(l) for l in _SINGLE_LABELS) + r')\s',
    re.IGNORECASE | re.MULTILINE,
)
_MULTI_PATTERN = re.compile(
    r'^(' + '|'.join(re.escape(l) for l in _MULTI_LABELS) + r')\s',
    re.IGNORECASE | re.MULTILINE,
)

# Unapproved label: Recommendation
_RECOMMENDATION_RE = re.compile(r'^Recommendation\b', re.IGNORECASE | re.MULTILINE)


class NotesRule(BaseStructureRule):
    """Flag note labels missing a colon or using unapproved labels."""

    def _get_rule_type(self) -> str:
        return 'notes'

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
            stripped = sentence.strip()
            self._check_missing_colon(stripped, sentence, idx, text, context, errors)
            self._check_recommendation(stripped, sentence, idx, text, context, errors)
        return errors

    # ------------------------------------------------------------------
    # Check 1 — missing colon after approved label
    # ------------------------------------------------------------------
    def _check_missing_colon(self, stripped, sentence, idx, text, context, errors):
        for pattern in (_SINGLE_PATTERN, _MULTI_PATTERN):
            match = pattern.match(stripped)
            if not match:
                continue
            label = match.group(1)
            # Already has colon?
            after_label = stripped[len(label):]
            if after_label.startswith(':'):
                continue
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Note label '{label}' must be followed by a colon. "
                    f"Write '{label}:' instead."
                ),
                suggestions=[
                    f"Add a colon after '{label}' (e.g., '{label}: ...').",
                    "IBM Style Guide requires a colon after note labels.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=label,
                span=(0, len(label)),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 — "Recommendation" is not approved
    # ------------------------------------------------------------------
    def _check_recommendation(self, stripped, sentence, idx, text, context, errors):
        match = _RECOMMENDATION_RE.match(stripped)
        if not match:
            return
        found = match.group(0)
        error = self._create_error(
            sentence=sentence,
            sentence_index=idx,
            message=(
                f"'{found}' is not an approved note label. "
                "Use an approved label such as Note, Tip, Important, or Warning."
            ),
            suggestions=[
                "Replace 'Recommendation' with 'Tip:' or 'Note:'.",
                "Approved labels: Note, Important, Tip, Warning, Caution, etc.",
            ],
            severity='medium',
            text=text,
            context=context,
            flagged_text=found,
            span=(0, len(found)),
        )
        if error:
            errors.append(error)

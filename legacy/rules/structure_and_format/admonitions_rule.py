"""
Admonitions Rule — Deterministic context-based detection.
IBM Style Guide (p. 204-205): Approved admonition labels.

Checks:
  1. Only approved admonition labels are allowed.
  2. "Recommendation" is not an approved label.

Approved: NOTE, IMPORTANT, RESTRICTION, TIP, ATTENTION,
          CAUTION, DANGER, REQUIREMENT, EXCEPTION, FAST PATH,
          REMEMBER, WARNING.

Detection: only fires when block_type is 'admonition'.
Checks the admonition 'kind' from context against the approved list.
"""
from typing import List, Dict, Any, Optional

from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

_APPROVED_LABELS = frozenset([
    'NOTE', 'IMPORTANT', 'RESTRICTION', 'TIP', 'ATTENTION',
    'CAUTION', 'DANGER', 'REQUIREMENT', 'EXCEPTION',
    'FAST PATH', 'REMEMBER', 'WARNING',
])


class AdmonitionsRule(BaseStructureRule):
    """Flag unapproved admonition labels."""

    def _get_rule_type(self) -> str:
        return 'admonitions'

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

        # Only fire on admonition blocks
        if context.get('block_type') != 'admonition':
            return []

        kind = context.get('kind', '').strip().upper()
        if not kind:
            return []

        # Approved — no error
        if kind in _APPROVED_LABELS:
            return []

        errors: List[Dict[str, Any]] = []

        # Suggest closest match
        suggestion_label = self._closest_label(kind)
        suggestion_text = (
            f"Consider using '{suggestion_label}' instead of '{kind}'."
            if suggestion_label
            else "Use one of the approved labels: NOTE, IMPORTANT, TIP, WARNING, CAUTION, etc."
        )

        error = self._create_error(
            sentence=text,
            sentence_index=0,
            message=(
                f"'{kind}' is not an approved admonition label. "
                "Use an approved IBM Style Guide label."
            ),
            suggestions=[
                suggestion_text,
                "Approved: NOTE, IMPORTANT, TIP, WARNING, CAUTION, DANGER, "
                "RESTRICTION, REQUIREMENT, EXCEPTION, ATTENTION, REMEMBER, FAST PATH.",
            ],
            severity='medium',
            text=text,
            context=context,
            flagged_text=kind,
            span=(0, len(kind)),
        )
        if error:
            errors.append(error)

        return errors

    @staticmethod
    def _closest_label(kind: str) -> str:
        """Return the closest approved label by substring match, or empty string."""
        kind_lower = kind.lower()
        for label in _APPROVED_LABELS:
            if kind_lower in label.lower() or label.lower() in kind_lower:
                return label
        return ''

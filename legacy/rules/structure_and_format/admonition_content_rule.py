"""
Admonition Content Rule — Deterministic sentence-count detection.
IBM Style Guide (p. 204-205): Admonition brevity.

Checks:
  1. Notes should be short — flag if admonition content exceeds 3 sentences.

Detection: count sentences in admonition block.
Guards: only fires when block_type is 'admonition'.
"""
import re
from typing import List, Dict, Any, Optional

from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

# Maximum number of sentences recommended in an admonition
_MAX_SENTENCES = 3

# Simple sentence-boundary detection (period, exclamation, question mark
# followed by a space or end-of-string, but not after common abbreviations)
_SENTENCE_END = re.compile(r'[.!?](?:\s|$)')


class AdmonitionContentRule(BaseStructureRule):
    """Flag overly long admonition content."""

    def _get_rule_type(self) -> str:
        return 'admonition_content'

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

        # Count sentences — prefer the pre-split sentences list if available
        sentence_count = len(sentences) if sentences else len(_SENTENCE_END.findall(text))

        if sentence_count <= _MAX_SENTENCES:
            return []

        errors: List[Dict[str, Any]] = []
        error = self._create_error(
            sentence=text[:100] + '...' if len(text) > 100 else text,
            sentence_index=0,
            message=(
                f"This admonition contains {sentence_count} sentences. "
                f"Keep admonitions to {_MAX_SENTENCES} sentences or fewer."
            ),
            suggestions=[
                "Shorten the admonition to its essential point.",
                "Move detailed explanations to the main content.",
                "IBM Style Guide: notes and admonitions should be brief.",
            ],
            severity='low',
            text=text,
            context=context,
            flagged_text=f"{sentence_count} sentences",
            span=(0, len(text)),
        )
        if error:
            errors.append(error)

        return errors

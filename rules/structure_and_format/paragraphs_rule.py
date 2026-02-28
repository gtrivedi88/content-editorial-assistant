"""
Paragraphs Rule — Deterministic context-based detection.
IBM Style Guide (p. 206): Paragraph indentation.

Checks:
  1. Omit paragraph indentation — first line should be flush left.

Detection: only fires when the structural parser provides indent info
via context (node with indent > 0).
Guards: skip code/listing blocks. Very conservative — most documents
do not provide indent info.
"""
from typing import List, Dict, Any, Optional

from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])


class ParagraphsRule(BaseStructureRule):
    """Flag indented paragraphs that should be flush left."""

    def _get_rule_type(self) -> str:
        return 'paragraphs'

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

        # Require a structural node with indent info
        node = context.get('node')
        if not node:
            return []

        # Only check paragraph nodes
        node_type = getattr(node, 'node_type', '')
        if node_type != 'paragraph':
            return []

        indentation = getattr(node, 'indent', 0)
        if not indentation or indentation <= 0:
            return []

        errors: List[Dict[str, Any]] = []
        flagged = text[:indentation] if indentation <= len(text) else text
        error = self._create_error(
            sentence=sentences[0] if sentences else text,
            sentence_index=0,
            message=(
                f"Remove the {indentation}-space paragraph indentation. "
                "Paragraphs should be flush left."
            ),
            suggestions=[
                "Remove all leading whitespace from the paragraph.",
                "IBM Style Guide: omit paragraph indentation.",
            ],
            severity='low',
            text=text,
            context=context,
            flagged_text=flagged,
            span=(0, indentation),
        )
        if error:
            errors.append(error)

        return errors

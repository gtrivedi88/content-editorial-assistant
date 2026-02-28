"""
Indentation Rule — Deterministic regex-based detection.
IBM Style Guide — General formatting.

Checks:
  1. Do not mix tabs and spaces for indentation.

Detection: regex for mixed tab+space indentation at line start.
Guards: skip code blocks (mixed indent is valid in code).
Only fires on paragraph/text blocks.
"""
import re
from typing import List, Dict, Any, Optional

from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

# Mixed tabs and spaces at the start of a line
_MIXED_INDENT = re.compile(r'^(\t+ +| +\t+)', re.MULTILINE)


class IndentationRule(BaseStructureRule):
    """Flag mixed tab and space indentation."""

    def _get_rule_type(self) -> str:
        return 'indentation'

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
        for match in _MIXED_INDENT.finditer(text):
            indent_text = match.group(0)
            line = self._get_line(text, match.start())

            error = self._create_error(
                sentence=line,
                sentence_index=self._line_number(text, match.start()),
                message="Do not mix tabs and spaces for indentation.",
                suggestions=[
                    "Use either tabs or spaces consistently, not both.",
                    "Configure your editor to use a single indentation style.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=repr(indent_text),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

        return errors

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_line(text: str, pos: int) -> str:
        """Return the full line containing position *pos*."""
        start = text.rfind('\n', 0, pos)
        start = 0 if start == -1 else start + 1
        end = text.find('\n', pos)
        end = len(text) if end == -1 else end
        return text[start:end]

    @staticmethod
    def _line_number(text: str, pos: int) -> int:
        """Return the zero-based line number for *pos*."""
        return text[:pos].count('\n')

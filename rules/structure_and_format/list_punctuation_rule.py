"""
List Punctuation Rule — Deterministic regex-based detection.
IBM Style Guide (p. 197-199): List item punctuation.

Checks:
  1. Do not use a comma at the end of a list item.
  2. Do not use a semicolon at the end of a list item.

Guards: only fires on list block types. Skip code blocks.
"""
import re
from typing import List, Dict, Any, Optional

from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

_LIST_BLOCKS = frozenset([
    'ordered_list_item', 'unordered_list_item', 'list_item',
    'list_item_ordered', 'list_item_unordered',
])

# Trailing comma (ignoring whitespace at end)
_TRAILING_COMMA = re.compile(r',\s*$')

# Trailing semicolon (ignoring whitespace at end)
_TRAILING_SEMICOLON = re.compile(r';\s*$')


class ListPunctuationRule(BaseStructureRule):
    """Flag trailing commas or semicolons on list items."""

    def _get_rule_type(self) -> str:
        return 'list_punctuation'

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
        if context.get('block_type', '') not in _LIST_BLOCKS:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_trailing_comma(sentence, idx, text, context, errors)
            self._check_trailing_semicolon(sentence, idx, text, context, errors)
        return errors

    # ------------------------------------------------------------------
    # Check 1 — trailing comma
    # ------------------------------------------------------------------
    def _check_trailing_comma(self, sentence, idx, text, context, errors):
        match = _TRAILING_COMMA.search(sentence)
        if not match:
            return
        pos = match.start()
        error = self._create_error(
            sentence=sentence,
            sentence_index=idx,
            message="Do not use a comma at the end of a list item.",
            suggestions=[
                "Remove the trailing comma.",
                "Use a period if the item is a complete sentence, or no punctuation for fragments.",
            ],
            severity='low',
            text=text,
            context=context,
            flagged_text=',',
            span=(pos, pos + 1),
        )
        if error:
            errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 — trailing semicolon
    # ------------------------------------------------------------------
    def _check_trailing_semicolon(self, sentence, idx, text, context, errors):
        match = _TRAILING_SEMICOLON.search(sentence)
        if not match:
            return
        pos = match.start()
        error = self._create_error(
            sentence=sentence,
            sentence_index=idx,
            message="Do not use a semicolon at the end of a list item.",
            suggestions=[
                "Remove the trailing semicolon.",
                "Use a period if the item is a complete sentence, or no punctuation for fragments.",
            ],
            severity='low',
            text=text,
            context=context,
            flagged_text=';',
            span=(pos, pos + 1),
        )
        if error:
            errors.append(error)

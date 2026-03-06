"""
Lists Rule — Deterministic detection.
IBM Style Guide (p. 193-196): List formatting.

Checks:
  1. Capitalize the first word of each list item.
  2. Use "the following" not "these" to introduce a list.

Check 1: only on list item block types; skip items starting with code/commands.
Check 2: regex for "these" + colon pattern.
Guards: code block skip.
"""
import re
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

_LIST_BLOCKS = frozenset([
    'ordered_list_item', 'unordered_list_item', 'list_item',
    'list_item_ordered', 'list_item_unordered',
])

# "these" followed by optional words then a colon — introducing a list
_THESE_INTRO_RE = re.compile(
    r'\bthese\b(?:\s+\w+){0,4}\s*:', re.IGNORECASE
)

_INLINE_CODE = re.compile(r'`[^`]+`')

# Command-like token: all lowercase letters, digits, underscores, hyphens
_COMMAND_TOKEN_RE = re.compile(r'^[a-z][a-z0-9_\-]+$')


def _should_skip_capitalization(
    content: str, first_alpha_idx: int, text: str, context: Dict[str, Any],
) -> bool:
    """Return True if the list-item capitalization check should be skipped.

    Guards against false positives from inline code, command-like tokens,
    and content inside pre-computed inline code ranges.
    """
    # Guard: inline code ranges (backtick content already stripped by parser)
    code_ranges = context.get("inline_code_ranges", [])
    if code_ranges:
        content_offset = text.find(content)
        if content_offset < 0:
            content_offset = 0
        if in_code_range(content_offset + first_alpha_idx, code_ranges):
            return True

    # Guard: items starting with inline code backtick
    if content.startswith('`'):
        return True

    # Guard: command-like token (all lowercase + hyphens, length > 2)
    first_word = content.split()[0] if content.split() else ''
    if first_word and _COMMAND_TOKEN_RE.match(first_word) and len(first_word) > 2:
        return True

    return False


class ListsRule(BaseStructureRule):
    """Flag uncapitalized list items and 'these' as a list introducer."""

    def _get_rule_type(self) -> str:
        return 'lists'

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
        block_type = context.get('block_type', '')

        # Check 1: capitalization — only on list items
        if block_type in _LIST_BLOCKS:
            for idx, sentence in enumerate(sentences):
                self._check_capitalization(sentence, idx, text, context, errors)

        # Check 2: "these" introducing a list — applies to any block
        for idx, sentence in enumerate(sentences):
            self._check_these_intro(sentence, idx, text, context, errors)

        return errors

    # ------------------------------------------------------------------
    # Check 1 — first word of list item must be capitalized
    # ------------------------------------------------------------------
    def _check_capitalization(self, sentence, idx, text, context, errors):
        stripped = sentence.strip()
        if not stripped:
            return

        # Strip leading list markers like "- ", "* ", "1. "
        content = re.sub(r'^[\-\*\+\d.]+\s*', '', stripped)
        if not content:
            return

        # Find first alpha character
        first_alpha_idx = None
        for i, ch in enumerate(content):
            if ch.isalpha():
                first_alpha_idx = i
                break

        if first_alpha_idx is None:
            return

        first_char = content[first_alpha_idx]
        if not first_char.islower():
            return

        if _should_skip_capitalization(content, first_alpha_idx, text, context):
            return

        error = self._create_error(
            sentence=sentence,
            sentence_index=idx,
            message="Capitalize the first word of each list item.",
            suggestions=[
                f"Change '{first_char}' to '{first_char.upper()}'.",
                "IBM Style Guide requires capitalized list items.",
            ],
            severity='low',
            text=text,
            context=context,
            flagged_text=first_char,
            span=(first_alpha_idx, first_alpha_idx + 1),
        )
        if error:
            errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 — "these" introducing a list
    # ------------------------------------------------------------------
    def _check_these_intro(self, sentence, idx, text, context, errors):
        match = _THESE_INTRO_RE.search(sentence)
        if not match:
            return
        # Guard: skip if inside inline code
        code_spans = [(m.start(), m.end()) for m in _INLINE_CODE.finditer(sentence)]
        for s, e in code_spans:
            if s <= match.start() < e:
                return

        found = match.group(0)
        error = self._create_error(
            sentence=sentence,
            sentence_index=idx,
            message="Use 'the following' instead of 'these' to introduce a list.",
            suggestions=[
                "Replace 'these' with 'the following'.",
                "Example: 'Complete the following steps:' instead of "
                "'Complete these steps:'.",
            ],
            severity='low',
            text=text,
            context=context,
            flagged_text=found,
            span=(match.start(), match.end()),
        )
        if error:
            errors.append(error)

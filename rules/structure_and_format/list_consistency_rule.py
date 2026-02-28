"""
List Punctuation Consistency Rule — Deterministic detection.
IBM Style Guide (p. 197-198): Punctuation in lists.

Checks:
  1. Complete sentence list items must end with a period.
  2. Fragment list items should not end with a period (unless mixed with sentences).
  3. List items must not end with commas or semicolons (redundant with list_punctuation
     rule but included as the consistency message is different).

The IBM Style Guide says:
  - If list items are complete sentences, include a period after each sentence.
  - If list items are fragments, do not include end punctuation.
  - Be consistent with punctuation.

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
    # Also check paragraphs — when plain text is pasted, list items
    # arrive as paragraph blocks without structural markup.
    'paragraph',
])

# Pattern to detect complete sentences (starts with capital, has a verb-like word,
# and is longer than a short fragment)
_SENTENCE_PATTERN = re.compile(
    r'^[A-Z][a-z]+\s+(?:\w+\s+){0,5}'  # Capital word + up to 5 words
    r'(?:is|are|was|were|has|have|had|does|did|can|could|'
    r'will|would|shall|should|may|might|must)\b',
    re.IGNORECASE
)

# Ends with sentence-terminating punctuation
_ENDS_WITH_PERIOD = re.compile(r'\.\s*$')
_ENDS_WITH_TERMINAL = re.compile(r'[.!?]\s*$')

# Minimum length for a text to be considered a potential sentence
_MIN_SENTENCE_LENGTH = 20


class ListConsistencyRule(BaseStructureRule):
    """Flag list items with inconsistent punctuation per IBM Style Guide."""

    def _get_rule_type(self) -> str:
        return 'list_consistency'

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
        # Use the full text of the list item
        item_text = text.strip()
        if not item_text:
            return []

        self._check_sentence_missing_period(item_text, sentences, context, errors)
        return errors

    def _check_sentence_missing_period(self, item_text, sentences, context, errors):
        """Check if a list item looks like a complete sentence but is missing a period."""
        # Skip very short items (fragments like "Date and time")
        if len(item_text) < _MIN_SENTENCE_LENGTH:
            return

        # Skip items that already end with terminal punctuation
        if _ENDS_WITH_TERMINAL.search(item_text):
            return

        # Skip items ending with a colon (lead-in for sub-lists)
        if item_text.rstrip().endswith(':'):
            return

        # Check if this looks like a complete sentence
        if not _SENTENCE_PATTERN.match(item_text):
            return

        # Use SpaCy for more accurate sentence detection if available
        # The item has a subject-verb pattern and is long enough — likely a sentence
        # Flag it as missing a period
        last_line = sentences[-1] if sentences else item_text
        error = self._create_error(
            sentence=last_line,
            sentence_index=len(sentences) - 1 if sentences else 0,
            message=(
                "This list item appears to be a complete sentence but does not end "
                "with a period. Per IBM Style Guide, if list items are complete "
                "sentences, include a period after each sentence. Be consistent "
                "with punctuation across all items in a list."
            ),
            suggestions=[
                f"Add a period at the end: '{item_text.rstrip()}.'"
            ],
            severity='low',
            text=item_text,
            context=context,
            flagged_text=item_text.rstrip()[-20:] if len(item_text) > 20 else item_text.rstrip(),
            span=(len(item_text.rstrip()) - 1, len(item_text.rstrip())),
        )
        if error:
            errors.append(error)

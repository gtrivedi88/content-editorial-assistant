"""
List Parallelism Rule — Deterministic SpaCy-based detection.
IBM Style Guide (p. 196): Wording of list items.

"Use list items that are grammatically parallel. For example, do not mix
passive voice with active voice or declarative sentences with imperative
sentences."

Checks:
  1. List item starts with passive voice ("is/are/was/were + past participle").
     Flags it because IBM Style prefers active/imperative voice in lists.

Guards: only fires on list block types. Skip code blocks.
Uses SpaCy dependency parsing for accurate passive detection.
"""
from typing import List, Dict, Any, Optional

from .base_structure_rule import BaseStructureRule
from shared.spacy_singleton import get_spacy_model

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

_LIST_BLOCKS = frozenset([
    'ordered_list_item', 'unordered_list_item', 'list_item',
    'list_item_ordered', 'list_item_unordered',
])

# Auxiliary verbs that signal passive voice
_PASSIVE_AUX = frozenset(['is', 'are', 'was', 'were', 'be', 'been', 'being'])


class ListParallelismRule(BaseStructureRule):
    """Flag list items that use passive voice, breaking parallel structure."""

    def _get_rule_type(self) -> str:
        return 'list_parallelism'

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

        item_text = text.strip()
        if not item_text or len(item_text) < 10:
            return []

        errors: List[Dict[str, Any]] = []

        # Get or create SpaCy doc
        if spacy_doc is None:
            model = get_spacy_model()
            if model is None:
                return []
            spacy_doc = model(item_text)

        self._check_passive_voice(item_text, sentences, context, spacy_doc, errors)
        return errors

    def _check_passive_voice(self, item_text, sentences, context, doc, errors):
        """Detect passive voice in list items using SpaCy dependency parsing."""
        for token in doc:
            # Look for passive auxiliary ("nsubjpass" dependency or "auxpass")
            if token.dep_ == 'nsubjpass':
                # Found passive subject — this is passive voice
                # Find the main verb
                verb = token.head
                passive_phrase = f"{token.text} {verb.text}"

                # Build the flagged text span
                start = token.idx
                end = verb.idx + len(verb.text)

                sentence = sentences[0] if sentences else item_text
                error = self._create_error(
                    sentence=sentence,
                    sentence_index=0,
                    message=(
                        "This list item uses passive voice. Per IBM Style Guide, "
                        "use list items that are grammatically parallel. Do not "
                        "mix passive voice with active voice. Rewrite in active "
                        "or imperative voice to match other list items."
                    ),
                    suggestions=[
                        "Rewrite in active or imperative voice for parallel structure."
                    ],
                    severity='medium',
                    text=item_text,
                    context=context,
                    flagged_text=passive_phrase,
                    span=(start, end),
                )
                if error:
                    errors.append(error)
                return  # One flag per item is enough

            # Also check for "auxpass" dependency (alternate SpaCy label)
            if token.dep_ == 'auxpass' and token.text.lower() in _PASSIVE_AUX:
                verb = token.head
                aux_phrase = f"{token.text} {verb.text}"

                start = token.idx
                end = verb.idx + len(verb.text)

                sentence = sentences[0] if sentences else item_text
                error = self._create_error(
                    sentence=sentence,
                    sentence_index=0,
                    message=(
                        "This list item uses passive voice. Per IBM Style Guide, "
                        "use list items that are grammatically parallel. Do not "
                        "mix passive voice with active voice. Rewrite in active "
                        "or imperative voice to match other list items."
                    ),
                    suggestions=[
                        "Rewrite in active or imperative voice for parallel structure."
                    ],
                    severity='medium',
                    text=item_text,
                    context=context,
                    flagged_text=aux_phrase,
                    span=(start, end),
                )
                if error:
                    errors.append(error)
                return

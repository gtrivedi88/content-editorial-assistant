"""
Procedures Rule — Deterministic detection.
IBM Style Guide (p. 206-211): Procedure step guidelines.

Checks:
  1. Use ", and then" not just "then" to join steps in procedures.
  2. Do not use "please" in procedure steps.
  3. Procedure steps should begin with an imperative verb (SpaCy).

Guards: only applies to ordered_list_item / procedure block types + code block skip.
Check 3 only fires when SpaCy is available AND block_type is ordered_list_item.
"""
import re
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

_PROCEDURE_BLOCKS = frozenset([
    'ordered_list_item', 'list_item_ordered', 'list_item',
])

# Match "then" as a standalone word followed by whitespace
_THEN_RE = re.compile(r'\bthen\b(?=\s)', re.IGNORECASE)

# Already-correct pattern: ", and then"
_AND_THEN_RE = re.compile(r',\s+and\s+then\b', re.IGNORECASE)

_PLEASE_RE = re.compile(r'\bplease\b', re.IGNORECASE)

class ProceduresRule(BaseStructureRule):
    """Flag procedure step issues: 'then' usage, 'please', non-imperative starts."""

    def _get_rule_type(self) -> str:
        return 'procedures'

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

        block_type = context.get('block_type', '')
        is_procedure = block_type in _PROCEDURE_BLOCKS

        code_ranges = context.get("inline_code_ranges", []) if context else []
        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            sent_start = text.find(sentence)
            # Check 1 & 2 apply broadly but are most relevant in procedures
            self._check_then(sentence, idx, text, context, code_ranges, sent_start, errors)
            self._check_please(sentence, idx, text, context, code_ranges, sent_start, errors)
            # Check 3 only in ordered list items with SpaCy
            if is_procedure and nlp:
                self._check_imperative(sentence, idx, text, context, nlp, spacy_doc, errors)
        return errors

    # ------------------------------------------------------------------
    # Check 1 — ", and then" pattern
    # ------------------------------------------------------------------
    def _check_then(self, sentence, idx, text, context, code_ranges, sent_start, errors):
        for match in _THEN_RE.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            # Guard: skip if this "then" is already part of ", and then"
            if _AND_THEN_RE.search(sentence):
                continue
            found = match.group(0)
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message="In procedures, use ', and then' instead of 'then' between steps.",
                suggestions=[
                    "Replace 'then' with ', and then'.",
                    "Example: 'Click Start, and then select Settings'.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=found,
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 — "please" in procedure steps
    # ------------------------------------------------------------------
    def _check_please(self, sentence, idx, text, context, code_ranges, sent_start, errors):
        for match in _PLEASE_RE.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message="Do not use 'please' in procedure steps.",
                suggestions=[
                    "Remove 'please' and use a direct imperative verb.",
                    "Example: 'Enter your password' not 'Please enter your password'.",
                ],
                severity='low',
                text=text,
                context=context,
                flagged_text=match.group(0),
                span=(match.start(), match.end()),
            )
            if error:
                errors.append(error)

    # ------------------------------------------------------------------
    # Check 3 — imperative verb start (SpaCy required)
    # ------------------------------------------------------------------
    def _check_imperative(self, sentence, idx, text, context, nlp, spacy_doc, errors):
        doc = nlp(sentence)
        if not doc or len(doc) == 0:
            return
        first = doc[0]
        # Allow optional/conditional steps
        if first.lemma_.lower() in ('if', 'when', 'optional', 'optionally', 'unless', 'before', 'after'):
            return
        # Accept imperative (base verb at ROOT)
        if first.pos_ == 'VERB' and first.dep_ == 'ROOT' and first.tag_ == 'VB':
            return
        # Accept prepositional phrase starts ("In the console, ...")
        if first.pos_ in ('ADP', 'SCONJ') and first.dep_ in ('prep', 'mark', 'advmod'):
            return
        # Accept adverb-modified imperatives ("Optionally configure", "Manually set")
        if first.pos_ == 'ADV' and len(doc) > 1 and doc[1].pos_ == 'VERB':
            return
        # Accept "To + verb" pattern ("To configure the system, ...")
        if first.text.lower() == 'to' and len(doc) > 1 and doc[1].pos_ == 'VERB':
            return
        # Flag non-imperative starts
        error = self._create_error(
            sentence=sentence,
            sentence_index=idx,
            message="Procedure steps should begin with an imperative verb.",
            suggestions=[
                "Start with an action verb such as Click, Enter, Select, or Configure.",
                "IBM Style Guide requires imperative verbs for procedural steps.",
            ],
            severity='medium',
            text=text,
            context=context,
            flagged_text=first.text,
            span=(0, len(first.text)),
        )
        if error:
            errors.append(error)

"""
Names and Titles Rule — Deterministic SpaCy + regex detection.
IBM Style Guide (p. 228):
1. When referring to an individual with their job title, use
   headline-style capitalization regardless of word order.
   E.g., "President and CEO Arvind Krishna" (correct).
2. When using a job title standalone (without a person's name),
   use sentence-style case (lowercase).
   E.g., "the chief financial officer" (correct).

This rule focuses on the high-confidence check: standalone titles that
are incorrectly capitalized (e.g., "the President said" should be
"the president said" when no person name is nearby).

Guards: skip code blocks, skip when PERSON entity is adjacent.
"""
import re
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_references_rule import BaseReferencesRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Titles that should be lowercase when standalone (no person name nearby)
_TITLES = {
    'president', 'vice president', 'chief executive officer',
    'chief technology officer', 'chief financial officer',
    'chief operating officer', 'chief information officer',
    'chief marketing officer', 'chief data officer',
    'director', 'manager', 'supervisor',
    'professor', 'dean', 'chancellor',
}

# Determiners that signal standalone usage
_DETERMINERS = frozenset([
    'the', 'a', 'an', 'our', 'your', 'their', 'each', 'every', 'this', 'that',
])

# Title abbreviations (always capitalized, not checked)
_TITLE_ABBREVS = frozenset([
    'ceo', 'cto', 'cfo', 'coo', 'cio', 'cmo', 'cdo', 'vp',
])

class NamesAndTitlesRule(BaseReferencesRule):
    """Flag standalone professional titles that are incorrectly capitalized."""

    def _get_rule_type(self) -> str:
        return 'references_names_titles'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        code_ranges = context.get("inline_code_ranges", []) if context else []
        errors: List[Dict[str, Any]] = []

        for idx, sent in enumerate(doc.sents):
            self._check_standalone_title_caps(
                sent, idx, text, context, code_ranges, doc, errors,
            )
        return errors

    # ------------------------------------------------------------------
    # Check — standalone title incorrectly capitalized
    # ------------------------------------------------------------------
    def _check_standalone_title_caps(self, sent, idx, text, context,
                                     code_ranges, doc, errors):
        tokens = list(sent)
        for i, token in enumerate(tokens):
            # Only check capitalized words
            if not token.text[0].isupper():
                continue

            # Skip abbreviations (CEO, CTO, etc.)
            if token.text.lower() in _TITLE_ABBREVS:
                continue

            title_lower = token.text.lower()

            # Check single-word titles
            if title_lower not in _TITLES:
                # Also check two-word titles like "Vice President"
                if i + 1 < len(tokens):
                    two_word = (token.text + ' ' + tokens[i + 1].text).lower()
                    if two_word in _TITLES and tokens[i + 1].text[0].isupper():
                        if self._is_standalone(tokens, i, sent, doc):
                            if not in_code_range(token.idx, code_ranges):
                                found = token.text + ' ' + tokens[i + 1].text
                                self._add_title_error(
                                    found, sent.text, idx, text, context, errors,
                                    token.idx, token.idx + len(found),
                                )
                continue

            # Single-word title found — check if standalone
            if not self._is_standalone(tokens, i, sent, doc):
                continue

            if in_code_range(token.idx, code_ranges):
                continue

            self._add_title_error(
                token.text, sent.text, idx, text, context, errors,
                token.idx, token.idx + len(token.text),
            )

    def _is_standalone(self, tokens, title_idx, sent, doc) -> bool:
        """Return True if the title at title_idx is used standalone
        (no person name nearby)."""
        token = tokens[title_idx]

        # Check 1: preceded by a determiner -> standalone
        has_determiner = False
        if title_idx > 0:
            prev = tokens[title_idx - 1]
            if prev.text.lower() in _DETERMINERS:
                has_determiner = True

        if not has_determiner:
            return False

        # Check 2: no PERSON entity within 3 tokens -> standalone
        for ent in doc.ents:
            if ent.label_ != 'PERSON':
                continue
            # Check proximity: entity start/end vs title position
            dist = min(abs(ent.start - token.i), abs(ent.end - token.i))
            if dist <= 3:
                return False  # Person nearby — title with name, skip

        # Check 3: title at sentence start after "the" is likely standalone
        # but skip if next token is a proper noun (person name)
        if title_idx + 1 < len(tokens):
            next_tok = tokens[title_idx + 1]
            if next_tok.pos_ == 'PROPN' or next_tok.ent_type_ == 'PERSON':
                return False  # "the Director Smith" — with name

        return True

    def _add_title_error(self, found, sentence, idx, text, context,
                         errors, start, end):
        error = self._create_error(
            sentence=sentence,
            sentence_index=idx,
            message=(
                f"Use lowercase for standalone titles: "
                f"'{found}' -> '{found.lower()}'."
            ),
            suggestions=[
                f"Write '{found.lower()}' when the title is not used "
                f"with a person's name.",
                "Capitalize titles only when used with a specific person's name.",
            ],
            severity='medium',
            text=text,
            context=context,
            flagged_text=found,
            span=(start, end),
        )
        if error is not None:
            errors.append(error)

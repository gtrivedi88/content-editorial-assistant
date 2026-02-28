"""
Glossaries Rule — Deterministic detection with SpaCy NER.
IBM Style Guide (p. 181): Glossary term capitalization.

Checks:
  1. Do not capitalize glossary terms unless they are proper nouns.

Only fires when context has is_glossary=True. Needs SpaCy NER to detect
proper nouns. Very conservative — only flags clearly wrong cases.
Guards: skip code blocks.
"""
import re
from typing import List, Dict, Any, Optional

from .base_structure_rule import BaseStructureRule

_SKIP_BLOCKS = frozenset([
    'code_block', 'listing', 'literal', 'inline_code',
])

# Separator between term and definition
_TERM_DEF_RE = re.compile(r'^\s*([\w\s\-]+?)\s*(?:::|\s*:\s)\s*(.*)', re.DOTALL)


class GlossariesRule(BaseStructureRule):
    """Flag improperly capitalized glossary terms."""

    def _get_rule_type(self) -> str:
        return 'glossaries'

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

        # Only fire in glossary context
        if not context.get('is_glossary', False):
            return []

        # Require SpaCy for proper-noun detection
        if not nlp:
            return []

        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            self._check_term_capitalization(sentence, idx, text, context, nlp, errors)
        return errors

    # ------------------------------------------------------------------
    # Check 1 — glossary term should be lowercase unless proper noun
    # ------------------------------------------------------------------
    def _check_term_capitalization(self, sentence, idx, text, context, nlp, errors):
        match = _TERM_DEF_RE.match(sentence)
        if not match:
            return

        term = match.group(1).strip()
        if not term:
            return

        # Already lowercase — no problem
        if term == term.lower():
            return

        # All-caps or mixed-case acronym — skip (likely abbreviation)
        if term.isupper() and len(term) <= 6:
            return

        # SpaCy NER: check if every token is a proper noun
        doc = nlp(term)
        all_proper = all(tok.pos_ == 'PROPN' for tok in doc if tok.is_alpha)
        if all_proper:
            return

        # Has named entities — likely proper noun
        if doc.ents:
            return

        # Flag: capitalized but not proper noun
        error = self._create_error(
            sentence=sentence,
            sentence_index=idx,
            message=(
                f"Glossary term '{term}' should be lowercase unless "
                "it is a proper noun or acronym."
            ),
            suggestions=[
                f"Change '{term}' to '{term.lower()}'.",
                "IBM Style Guide: do not capitalize glossary terms "
                "unless they are proper nouns.",
            ],
            severity='medium',
            text=text,
            context=context,
            flagged_text=term,
            span=(sentence.find(term), sentence.find(term) + len(term)),
        )
        if error:
            errors.append(error)

"""
Oxford Comma Rule — Deterministic regex-based detection.
Source: Red Hat Vale OxfordComma rule.
IBM Style Guide: Use the serial (Oxford) comma before the conjunction
in a list of three or more items.

Example: "apples, oranges and bananas" → "apples, oranges, and bananas"
"""
import re
from typing import List, Dict, Any, Optional

from .base_punctuation_rule import BasePunctuationRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Match a list of 3+ items missing the Oxford comma before "and"/"or"
# Pattern: at least one "word," then "word and/or word" at end of sentence
_OXFORD_RE = re.compile(
    r'(?:[^\s,]+,\s+){1,}[^\s,]+\s+(?:and|or)\s+[^\s,]+[.?!]',
)


class OxfordCommaRule(BasePunctuationRule):
    """Flag lists of three or more items missing the Oxford comma."""

    def _get_rule_type(self) -> str:
        return 'oxford_comma'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        doc = spacy_doc if (spacy_doc is not None) else (nlp(text) if nlp else None)
        errors: List[Dict[str, Any]] = []

        if doc is not None:
            for i, sent in enumerate(doc.sents):
                self._check_sentence(sent.text, i, sent.start_char,
                                     text, context, errors)
        else:
            for i, sentence in enumerate(sentences):
                self._check_sentence(sentence, i, 0, text, context, errors)

        return errors

    def _check_sentence(self, sentence, idx, offset, text, context, errors):
        """Check a single sentence for missing Oxford comma."""
        for match in _OXFORD_RE.finditer(sentence):
            fragment = match.group(0)
            # Verify there's no comma before the conjunction
            conj_match = re.search(r',\s+(?:and|or)\s+', fragment)
            if conj_match:
                # Already has Oxford comma
                continue

            start = offset + match.start()
            end = offset + match.end()

            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=f"Use the Oxford comma in '{fragment}'.",
                suggestions=[
                    "Add a comma before 'and' or 'or' in a list of "
                    "three or more items."
                ],
                severity='low',
                text=text,
                context=context,
                flagged_text=fragment,
                span=(start, end),
            )
            if error:
                errors.append(error)

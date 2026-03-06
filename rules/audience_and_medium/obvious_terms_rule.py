"""
Obvious Terms Rule — Deterministic token list lookup.
Source: Red Hat Vale ObviousTerms rule.

Flags self-explanatory field descriptions that don't need to be documented,
such as "Password field", "Username field", etc.
"""
import re
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_audience_rule import BaseAudienceRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

_OBVIOUS_TERMS = [
    'Description field',
    'Mail field',
    'Name field',
    'Password field',
    'User field',
    'Username field',
]

_OBVIOUS_PATTERNS = [
    re.compile(r'\b' + re.escape(term) + r'\b', re.IGNORECASE)
    for term in _OBVIOUS_TERMS
]


class ObviousTermsRule(BaseAudienceRule):
    """Flag self-explanatory field descriptions that don't need documenting."""

    def _get_rule_type(self) -> str:
        return 'obvious_terms'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        code_ranges = context.get("inline_code_ranges", [])
        errors: List[Dict[str, Any]] = []

        if spacy_doc is not None:
            doc = spacy_doc
        elif nlp:
            doc = nlp(text)
        else:
            doc = None

        if doc is not None:
            for i, sent in enumerate(doc.sents):
                self._check_sent(sent.text, i, sent.start_char,
                                 text, context, code_ranges, errors)
        else:
            for i, sentence in enumerate(sentences):
                self._check_sent(sentence, i, 0,
                                 text, context, code_ranges, errors)

        return errors

    def _check_sent(self, sent_text: str, sent_index: int,
                    char_offset: int, text: str, context: Dict,
                    code_ranges: list,
                    errors: List[Dict[str, Any]]) -> None:
        """Check a single sentence for obvious term patterns."""
        for pattern in _OBVIOUS_PATTERNS:
            for match in pattern.finditer(sent_text):
                start = char_offset + match.start()
                if in_code_range(start, code_ranges):
                    continue
                found = match.group(0)
                end = char_offset + match.end()
                error = self._create_error(
                    sentence=sent_text,
                    sentence_index=sent_index,
                    message=(
                        f"Consider not documenting '{found}' "
                        f"because it is self-explanatory."
                    ),
                    suggestions=[
                        f"Remove the description of '{found}' or "
                        f"provide non-obvious details instead."
                    ],
                    severity='low',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(start, end),
                )
                if error:
                    errors.append(error)

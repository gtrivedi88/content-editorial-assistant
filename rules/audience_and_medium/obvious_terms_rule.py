"""
Obvious Terms Rule — Deterministic token list lookup.
Source: Red Hat Vale ObviousTerms rule.

Flags self-explanatory field descriptions that don't need to be documented,
such as "Password field", "Username field", etc.
"""
import re
from typing import List, Dict, Any, Optional

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

        doc = spacy_doc if (spacy_doc is not None) else (nlp(text) if nlp else None)
        errors: List[Dict[str, Any]] = []

        if doc is not None:
            for i, sent in enumerate(doc.sents):
                for pattern in _OBVIOUS_PATTERNS:
                    for match in pattern.finditer(sent.text):
                        found = match.group(0)
                        start = sent.start_char + match.start()
                        end = sent.start_char + match.end()
                        error = self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
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
        else:
            for i, sentence in enumerate(sentences):
                for pattern in _OBVIOUS_PATTERNS:
                    for match in pattern.finditer(sentence):
                        found = match.group(0)
                        error = self._create_error(
                            sentence=sentence,
                            sentence_index=i,
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
                            span=(match.start(), match.end()),
                        )
                        if error:
                            errors.append(error)

        return errors

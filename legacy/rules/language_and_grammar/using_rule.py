"""
Using Clarity Rule — SpaCy POS-based detection.
Source: Red Hat Vale Using rule.

Detects noun + "using" patterns and suggests "by using" for clarity.
For example: "Configure the server using the CLI" → "Configure the server by using the CLI"
"""
from typing import List, Dict, Any, Optional

from .base_language_rule import BaseLanguageRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

# Nouns POS tags that trigger the rule
_NOUN_TAGS = frozenset({'NN', 'NNP', 'NNPS', 'NNS'})


class UsingRule(BaseLanguageRule):
    """Flag 'using' after a noun where 'by using' would be clearer."""

    def _get_rule_type(self) -> str:
        return 'using_clarity'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []
        # Skip headings — "using" is common and acceptable there
        if context.get('block_type') == 'heading':
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors: List[Dict[str, Any]] = []

        for i, sent in enumerate(doc.sents):
            tokens = list(sent)
            for j, token in enumerate(tokens):
                if token.text.lower() != 'using':
                    continue
                if j == 0:
                    continue
                prev_token = tokens[j - 1]
                if prev_token.tag_ not in _NOUN_TAGS:
                    continue
                # Check that the previous-previous token isn't "by" already
                if j >= 2 and tokens[j - 2].text.lower() == 'by':
                    continue

                found = token.text
                start = token.idx
                end = token.idx + len(token.text)

                error = self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message=(
                        f"Use 'by using' instead of 'using' after a noun "
                        f"for clarity and grammatical correctness."
                    ),
                    suggestions=[f"Change '{prev_token.text} using' to "
                                 f"'{prev_token.text} by using'"],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(start, end),
                )
                if error:
                    errors.append(error)

        return errors

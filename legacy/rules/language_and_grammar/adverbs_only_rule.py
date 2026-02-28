"""
Adverbs-only Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Page 89): Place 'only' immediately before the word it modifies.
"""

from typing import List, Dict, Any, Optional
from .base_language_rule import BaseLanguageRule

# Citation auto-loaded from style_guides/ibm/ibm_style_mapping.yaml by BaseRule


class AdverbsOnlyRule(BaseLanguageRule):
    """Detects misplaced 'only' using SpaCy dependency parsing."""

    def __init__(self):
        super().__init__()

    def _get_rule_type(self) -> str:
        return 'adverbs_only'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in ['listing', 'literal', 'code_block', 'inline_code']:
            return []
        if not nlp and not spacy_doc:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for token in doc:
            if token.lower_ != 'only':
                continue
            if token.dep_ != 'advmod':
                continue

            # "only" modifies a verb — check if it should modify something else
            verb = token.head
            if verb.pos_ != 'VERB':
                continue

            # Look for a numeric or quantified object that "only" likely restricts
            restricted_element = None
            for child in verb.children:
                if child.dep_ in ('dobj', 'attr', 'nummod', 'npadvmod'):
                    # Check if there's a number or quantifier
                    for subchild in child.subtree:
                        if subchild.like_num or subchild.pos_ == 'NUM':
                            restricted_element = child
                            break
                    if restricted_element:
                        break

            if restricted_element is None:
                continue

            # "only" is before the verb but should be before the number/object
            if token.i < verb.i and restricted_element.i > verb.i:
                errors.append(self._create_error(
                    sentence=token.sent.text,
                    sentence_index=0,
                    message="Place 'only' immediately before the word it modifies.",
                    suggestions=[
                        f"Move 'only' closer to '{restricted_element.text}'. "
                        f"Example: '{verb.text} only {restricted_element.text}' instead of 'only {verb.text} {restricted_element.text}'."
                    ],
                    severity='low',
                    text=text,
                    context=context,
                    flagged_text='only',
                    span=(token.idx, token.idx + len(token.text))
                ))

        return errors

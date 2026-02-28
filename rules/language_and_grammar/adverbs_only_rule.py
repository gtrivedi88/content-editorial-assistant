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
            error = self._check_token(token, text, context)
            if error:
                errors.append(error)

        return errors

    def _check_token(
        self, token: Any, text: str, context: Any,
    ) -> Optional[Dict[str, Any]]:
        """Check whether 'only' is misplaced before a verb.

        Flags when 'only' modifies a verb but should modify the verb's
        object or a prepositional phrase complement instead.

        Args:
            token: SpaCy token to check.
            text: Full document text.
            context: Block-level context dict.

        Returns:
            Error dict if misplaced 'only' detected, None otherwise.
        """
        if token.lower_ != 'only':
            return None
        if token.dep_ != 'advmod':
            return None

        verb = token.head
        if verb.pos_ != 'VERB':
            return None

        restricted = self._find_restricted_element(verb)
        if restricted is None:
            return None

        # "only" is before the verb but should be before the object
        if token.i < verb.i and restricted.i > verb.i:
            return self._create_error(
                sentence=token.sent.text,
                sentence_index=0,
                message="Place 'only' immediately before the word it modifies.",
                suggestions=[
                    f"Move 'only' closer to '{restricted.text}'. "
                    f"Example: '{verb.text} only {restricted.text}' "
                    f"instead of 'only {verb.text} {restricted.text}'."
                ],
                severity='low',
                text=text,
                context=context,
                flagged_text='only',
                span=(token.idx, token.idx + len(token.text))
            )

        return None

    @staticmethod
    def _find_restricted_element(verb: Any) -> Any:
        """Find the element that 'only' most likely restricts.

        Checks for direct objects, prepositional complements, and
        numeric/quantified elements as restriction targets.

        Args:
            verb: The SpaCy verb token that 'only' modifies.

        Returns:
            The SpaCy token that 'only' should be placed before,
            or None if no clear restriction target is found.
        """
        for child in verb.children:
            if child.dep_ == 'dobj':
                return child
            if child.dep_ == 'prep':
                return child
            if child.dep_ in ('attr', 'nummod', 'npadvmod'):
                if _subtree_has_number(child):
                    return child

        return None


def _subtree_has_number(token: Any) -> bool:
    """Check if a token's subtree contains a numeric element.

    Args:
        token: SpaCy token whose subtree to check.

    Returns:
        True if any token in the subtree is numeric.
    """
    return any(t.like_num or t.pos_ == 'NUM' for t in token.subtree)

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

# Tools/commands where "noun using" is idiomatic — "by using" would add unnecessary words
_IDIOMATIC_USING_OBJECTS = frozenset({
    'rpm', 'pip', 'npm', 'yum', 'dnf', 'apt', 'brew', 'curl', 'wget',
    'git', 'make', 'cmake', 'maven', 'gradle', 'docker', 'podman',
    'kubectl', 'oc', 'helm', 'ansible', 'terraform',
})


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
        if context.get('block_type') == 'heading':
            return []
        if not nlp and spacy_doc is None:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors: List[Dict[str, Any]] = []

        for i, sent in enumerate(doc.sents):
            tokens = list(sent)
            for j, token in enumerate(tokens):
                error = self._check_token(tokens, j, token, sent, i, text, context)
                if error:
                    errors.append(error)

        return errors

    def _check_token(
        self, tokens: list, j: int, token: Any,
        sent: Any, sent_idx: int,
        text: str, context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Check a single token for the noun + 'using' pattern.

        Args:
            tokens: All tokens in the current sentence.
            j: Index of the current token in the sentence.
            token: The SpaCy token to check.
            sent: The SpaCy sentence span.
            sent_idx: Index of the sentence in the document.
            text: Full document text.
            context: Block-level context dict.

        Returns:
            Error dict if the pattern is found, None otherwise.
        """
        if token.text.lower() != 'using':
            return None
        if j == 0:
            return None
        prev_token = tokens[j - 1]
        if prev_token.tag_ not in _NOUN_TAGS:
            return None
        if j >= 2 and tokens[j - 2].text.lower() == 'by':
            return None

        # Guard: skip if next token is a tool/command name (idiomatic usage)
        if j + 1 < len(tokens) and tokens[j + 1].text.lower() in _IDIOMATIC_USING_OBJECTS:
            return None

        return self._create_error(
            sentence=sent.text,
            sentence_index=sent_idx,
            message=(
                "Use 'by using' instead of 'using' after a noun "
                "for clarity and grammatical correctness."
            ),
            suggestions=[
                f"Change '{prev_token.text} using' to "
                f"'{prev_token.text} by using'"
            ],
            severity='medium',
            text=text,
            context=context,
            flagged_text=token.text,
            span=(token.idx, token.idx + len(token.text)),
        )

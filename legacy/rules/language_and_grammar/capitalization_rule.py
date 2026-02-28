"""
Capitalization Rule
Based on IBM Style Guide topic: "Capitalization" (p.94)

Check 1: Proper nouns (PERSON, ORG, GPE) that are lowercase should be capitalized.
Check 2: Common nouns incorrectly capitalized mid-sentence should be lowercase.
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule


class CapitalizationRule(BaseLanguageRule):
    """Deterministic capitalization checker using SpaCy NER and POS tagging."""

    ENTITY_LABELS = {'PERSON', 'ORG', 'GPE'}

    LOWERCASE_CANDIDATES = {
        'operator', 'cluster', 'controller', 'driver', 'plugin', 'namespace',
        'service', 'deployment', 'pod', 'container', 'node', 'volume',
        'instance', 'server', 'client', 'user', 'admin', 'system',
        'network', 'storage', 'database', 'application', 'interface',
    }

    SKIP_BLOCK_TYPES = {'listing', 'literal', 'code_block', 'inline_code'}

    def _get_rule_type(self) -> str:
        return 'capitalization'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in self.SKIP_BLOCK_TYPES:
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for i, sent in enumerate(doc.sents):
            for token in sent:
                self._check_missing_capitalization(
                    token, sent, i, text, context, errors)
                self._check_incorrect_capitalization(
                    token, sent, doc, i, text, context, errors)

        return errors

    def _check_missing_capitalization(self, token, sent, sent_idx,
                                      text, context, errors):
        """Check 1: Named entities that should be capitalized."""
        if token.ent_type_ not in self.ENTITY_LABELS:
            return
        if token.ent_iob_ not in ('B', 'I'):
            return
        if len(token.text) <= 1 or not token.text[0].islower():
            return

        entity_desc = {
            'PERSON': "a person's name",
            'ORG': 'an organization name',
            'GPE': 'a geographic or political entity',
        }.get(token.ent_type_, 'a proper noun')

        error = self._create_error(
            sentence=sent.text,
            sentence_index=sent_idx,
            message=(f"'{token.text}' should be capitalized "
                     f"as it is {entity_desc}."),
            suggestions=[
                f"Change '{token.text}' to '{token.text.capitalize()}'",
            ],
            severity='medium',
            text=text,
            context=context,
            span=(token.idx, token.idx + len(token.text)),
            flagged_text=token.text,
        )
        if error:
            errors.append(error)

    def _check_incorrect_capitalization(self, token, sent, doc, sent_idx,
                                        text, context, errors):
        """Check 2: Words incorrectly capitalized mid-sentence."""
        if not self._should_be_lowercase(token, sent, doc):
            return

        error = self._create_error(
            sentence=sent.text,
            sentence_index=sent_idx,
            message=(f"'{token.text}' should be lowercase "
                     f"unless it is a specific product name."),
            suggestions=[
                f"Change '{token.text}' to '{token.text.lower()}'",
            ],
            severity='low',
            text=text,
            context=context,
            span=(token.idx, token.idx + len(token.text)),
            flagged_text=token.text,
        )
        if error:
            errors.append(error)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _should_be_lowercase(self, token, sent, doc) -> bool:
        """Return True if a mid-sentence capitalized word should be lowercase."""
        # Must start with an uppercase letter
        if not token.text or not token.text[0].isupper():
            return False

        # Skip sentence-start words
        if token.is_sent_start:
            return False

        # Skip recognized named entities
        if token.ent_type_ in ('PERSON', 'ORG', 'GPE', 'PRODUCT', 'EVENT', 'FAC'):
            return False

        # Skip proper nouns tagged by the POS tagger
        if token.pos_ == 'PROPN' and token.tag_ == 'NNP':
            return False

        # Skip acronyms (all caps, short)
        if token.text.isupper() and len(token.text) <= 6:
            return False

        # Skip camelCase or mixed case identifiers
        if any(c.isupper() for c in token.text[1:]) and any(c.islower() for c in token.text):
            return False

        # Only flag known generic terms
        if token.text.lower() not in self.LOWERCASE_CANDIDATES:
            return False

        # Skip if part of a multi-word product name
        if self._is_part_of_product_name(token, doc):
            return False

        return True

    def _is_part_of_product_name(self, token, doc) -> bool:
        """Return True if the token sits adjacent to other capitalized words."""
        if token.i > 0:
            prev = doc[token.i - 1]
            if (prev.text and prev.text[0].isupper()
                    and prev.text.lower() not in ('the', 'a', 'an')):
                return True

        if token.i < len(doc) - 1:
            nxt = doc[token.i + 1]
            if nxt.text and nxt.text[0].isupper():
                return True

        return False

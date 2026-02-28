"""
Possessives Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Page 106): Do not use possessive 's with abbreviations or product names.
Use a prepositional phrase instead (e.g., "the API's documentation" → "the documentation of the API").

Configuration loaded from config/possessives_config.yaml.
To add brand exceptions, edit the YAML file — no code changes needed.
"""
import os
import yaml
from typing import List, Dict, Any, Set
from .base_language_rule import BaseLanguageRule


def _load_config() -> Set[str]:
    """Load brand exceptions from YAML config."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'possessives_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return set(config.get('brand_exceptions', []))
    except (FileNotFoundError, yaml.YAMLError):
        return {'IBM'}


_BRAND_EXCEPTIONS = _load_config()


class PossessivesRule(BaseLanguageRule):
    """Detects possessive 's on abbreviations and suggests prepositional phrases."""

    def _get_rule_type(self) -> str:
        return 'possessives'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in (
            'listing', 'literal', 'code_block', 'inline_code',
        ):
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for sent_index, sent in enumerate(doc.sents):
            self._check_sentence(sent, sent_index, doc, text, context, errors)

        return errors

    def _check_sentence(self, sent, sent_index: int, doc,
                        text: str, context, errors: List[Dict[str, Any]]) -> None:
        """Find abbreviation possessives in a single sentence."""
        for token in sent:
            if token.text != "'s" or token.i == 0:
                continue

            prev = doc[token.i - 1]
            if not prev.is_upper or len(prev.text) <= 1:
                continue
            if prev.text in _BRAND_EXCEPTIONS:
                continue

            obj_text = self._find_possessed_object(doc, token.i)
            abbr = prev.text

            error = self._create_error(
                sentence=sent.text,
                sentence_index=sent_index,
                message=(
                    f"Do not use possessive 's with the abbreviation "
                    f"'{abbr}'. Use a prepositional phrase instead."
                ),
                suggestions=[
                    f"Change '{abbr}'s {obj_text}' to "
                    f"'the {obj_text} of {abbr}'",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=f"{abbr}'s",
                span=(prev.idx, token.idx + len(token.text)),
            )
            if error:
                errors.append(error)

    @staticmethod
    def _find_possessed_object(doc, possessive_idx: int) -> str:
        """Return the first content word after the possessive token."""
        for j in range(possessive_idx + 1, len(doc)):
            if not doc[j].is_punct and not doc[j].is_space:
                return doc[j].text
        return '[property]'

"""
Anthropomorphism Rule — Deterministic SpaCy-based detection.
IBM Style Guide (Page 90): Do not attribute human characteristics to non-human things.

Configuration loaded from config/anthropomorphism_config.yaml.
To add new terms, edit the YAML file — no code changes needed.
"""

import os
import yaml
from typing import List, Dict, Any, Optional, Set
from .base_language_rule import BaseLanguageRule

# Citation auto-loaded from style_guides/ibm/ibm_style_mapping.yaml by BaseRule


def _load_config() -> Dict[str, Any]:
    """Load anthropomorphism configuration from YAML."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'anthropomorphism_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()
ANTHROPOMORPHIC_VERBS: Set[str] = set(_CONFIG.get('anthropomorphic_verbs', []))
SAFE_TECHNICAL_VERBS: Set[str] = set(_CONFIG.get('safe_technical_verbs', []))
NON_HUMAN_INDICATORS: Set[str] = set(_CONFIG.get('non_human_indicators', []))


class AnthropomorphismRule(BaseLanguageRule):
    """Detects anthropomorphic language using SpaCy dependency parsing."""

    def __init__(self):
        super().__init__()

    def _get_rule_type(self) -> str:
        return 'anthropomorphism'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in ['listing', 'literal', 'code_block', 'inline_code']:
            return []
        if not nlp and not spacy_doc:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors = []

        for token in doc:
            error = self._check_token(token, text, context)
            if error is not None:
                errors.append(error)

        return errors

    def _check_token(
        self, token: Any, text: str, context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Check a single token for anthropomorphic verb usage.

        Args:
            token: SpaCy Token to evaluate.
            text: Full document text for error context.
            context: Rule context dict.

        Returns:
            Error dict if anthropomorphism detected, None otherwise.
        """
        if token.pos_ != 'VERB':
            return None
        if token.lemma_ not in ANTHROPOMORPHIC_VERBS:
            return None
        if token.lemma_ in SAFE_TECHNICAL_VERBS:
            return None

        subject = self._get_subject(token)
        if subject is None:
            return None
        # Skip cross-paragraph dependencies — SpaCy may link tokens
        # across newline boundaries that are logically separate sentences
        if self._spans_newline(text, subject, token):
            return None
        if not self._is_non_human(subject):
            return None

        return self._create_error(
            sentence=token.sent.text,
            sentence_index=0,
            message=f"Avoid anthropomorphism: '{subject.text}' cannot '{token.lemma_}'.",
            suggestions=[f"Rewrite without attributing human qualities to '{subject.text}'."],
            severity='medium',
            text=text,
            context=context,
            flagged_text=f"{subject.text} {token.text}",
            span=(subject.idx, token.idx + len(token.text))
        )

    @staticmethod
    def _spans_newline(text: str, subject: Any, verb: Any) -> bool:
        """Check whether subject and verb are separated by a newline.

        Args:
            text: Full document text.
            subject: SpaCy Token for the subject.
            verb: SpaCy Token for the verb.

        Returns:
            True if a newline appears between subject and verb positions.
        """
        start = min(subject.idx + len(subject.text), len(text))
        end = min(verb.idx, len(text))
        return '\n' in text[start:end]

    def _get_subject(self, verb_token):
        """Find the nominal subject of a verb via dependency tree."""
        for child in verb_token.children:
            if child.dep_ in ('nsubj', 'nsubjpass'):
                return child
        return None

    def _is_non_human(self, token) -> bool:
        """Check if a token refers to a non-human entity."""
        if token.ent_type_ in ('PERSON', 'NORP'):
            return False
        if token.lemma_.lower() in NON_HUMAN_INDICATORS:
            return True
        for child in token.children:
            if child.dep_ == 'compound' and child.lemma_.lower() in NON_HUMAN_INDICATORS:
                return True
        return False

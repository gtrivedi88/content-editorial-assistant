"""
Conversational Style Rule — Deterministic YAML-based detection.
IBM Style Guide: Use a conversational style. Avoid overly formal
or complex words when simpler alternatives exist.

Configuration loaded from config/conversational_vocabularies.yaml.
To add new formal->conversational pairs, edit the YAML file — no code changes needed.
"""
import os
import yaml
from typing import List, Dict, Any
from rules.base_rule import in_code_range
from .base_audience_rule import BaseAudienceRule


def _load_config() -> Dict[str, str]:
    """Load formal->conversational word mappings from YAML config."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'conversational_vocabularies.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}

    mappings = {}
    for _section, entries in config.get('formal_to_conversational', {}).items():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            if isinstance(entry, dict) and 'formal' in entry and 'conversational' in entry:
                mappings[entry['formal'].lower()] = entry['conversational']
    return mappings


_FORMAL_MAP = _load_config()


class ConversationalStyleRule(BaseAudienceRule):
    """Detects overly formal language and suggests conversational alternatives."""

    def _get_rule_type(self) -> str:
        return 'conversational_style'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in (
            'listing', 'literal', 'code_block', 'inline_code',
        ):
            return []

        # Guard: reference docs use formal language by design
        if context and context.get('content_type') == 'reference':
            return []

        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        code_ranges = context.get("inline_code_ranges", []) if context else []
        errors = []

        for i, sent in enumerate(doc.sents):
            self._check_sentence(sent, i, text, context, code_ranges, errors)

        return errors

    def _check_sentence(self, sent, sent_index: int, text: str,
                        context, code_ranges: list,
                        errors: List[Dict[str, Any]]) -> None:
        """Check a single sentence for overly formal tokens."""
        for token in sent:
            if in_code_range(token.idx, code_ranges):
                continue
            alternative = _FORMAL_MAP.get(token.lemma_.lower())
            if not alternative:
                continue

            error = self._create_error(
                sentence=sent.text,
                sentence_index=sent_index,
                message=(
                    f"Use '{alternative}' instead of "
                    f"'{token.text}' for a more conversational tone."
                ),
                suggestions=[
                    f"Change '{token.text}' to '{alternative}'",
                ],
                severity='low',
                text=text,
                context=context,
                flagged_text=token.text,
                span=(token.idx, token.idx + len(token.text)),
            )
            if error:
                errors.append(error)

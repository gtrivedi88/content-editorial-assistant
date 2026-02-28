"""
Simple Words Rule — Deterministic YAML lookup.
Suggest simpler alternatives for complex vocabulary.
"""
import os

import yaml
from typing import List, Dict, Any, Optional

from .base_word_usage_rule import BaseWordUsageRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> Dict[str, str]:
    """Load simple words map from YAML config."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'simple_words_config.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return config.get('simple_words', {})
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_TERM_MAP = _load_config()


class SimpleWordsRule(BaseWordUsageRule):
    """Suggest simpler alternatives for complex vocabulary."""

    def _get_rule_type(self) -> str:
        return 'simple_words'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        return self._match_terms(
            doc, text, _TERM_MAP, context,
            severity='low',
            message_fmt="Use simpler language. Consider using '{right}' instead of '{found}'.",
        )

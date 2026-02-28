"""
Q Words Rule — Deterministic YAML lookup.
IBM Style Guide (p.284-414): Word usage entries for letter Q.
"""
import os

import yaml
from typing import List, Dict, Any, Optional

from .base_word_usage_rule import BaseWordUsageRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> Dict[str, str]:
    """Load word usage map for letter Q from YAML config."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'word_usage_config.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return config.get('q', {})
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_TERM_MAP = _load_config()


class QWordsRule(BaseWordUsageRule):
    """Flag incorrect word usage for Q-words and suggest alternatives."""

    def _get_rule_type(self) -> str:
        return 'word_usage_q'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        return self._match_terms(doc, text, _TERM_MAP, context)

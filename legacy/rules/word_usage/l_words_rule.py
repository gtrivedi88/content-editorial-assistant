"""
L Words Rule — Deterministic YAML lookup.
IBM Style Guide (p.284-414): Word usage entries for letter L.
"""
import os
import re

import yaml
from typing import List, Dict, Any, Optional

from .base_word_usage_rule import BaseWordUsageRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> Dict[str, str]:
    """Load word usage map for letter L from YAML config."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'word_usage_config.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return config.get('l', {})
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_TERM_MAP = _load_config()


class LWordsRule(BaseWordUsageRule):
    """Flag incorrect word usage for L-words and suggest alternatives."""

    def _get_rule_type(self) -> str:
        return 'word_usage_l'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors: List[Dict[str, Any]] = []

        for i, sent in enumerate(doc.sents):
            for wrong, right in _TERM_MAP.items():
                pattern = r'\b' + re.escape(wrong) + r'\b'
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    found = match.group(0)
                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()

                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Use '{right}' instead of '{found}'.",
                        suggestions=[f"Change '{found}' to '{right}'"],
                        severity='medium',
                        text=text,
                        context=context,
                        flagged_text=found,
                        span=(start, end),
                    )
                    if error:
                        errors.append(error)

        return errors

"""
Do Not Use Terms Rule — Deterministic YAML lookup.
Flag terms that should not be used in technical documentation.
Source: Red Hat Vale DoNotUseTerms + IBM Style Guide.
"""
import os
import re

import yaml
from typing import List, Dict, Any, Optional

from .base_word_usage_rule import BaseWordUsageRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> Dict[str, Dict[str, str]]:
    """Load do-not-use terms map from YAML config."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'do_not_use_config.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return config.get('terms', {})
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_TERM_MAP = _load_config()


class DoNotUseTermsRule(BaseWordUsageRule):
    """Flag terms that should not be used in technical documentation."""

    def _get_rule_type(self) -> str:
        return 'do_not_use'

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
            protected_ranges = self._get_protected_ranges(sent.text)
            for term, info in _TERM_MAP.items():
                pattern = r'\b' + re.escape(term) + r'\b'
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    if self._is_in_protected_range(match.start(), match.end(), protected_ranges):
                        continue
                    found = match.group(0)
                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()

                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=info['message'],
                        suggestions=[],
                        severity='high',
                        text=text,
                        context=context,
                        flagged_text=found,
                        span=(start, end),
                    )
                    if error:
                        errors.append(error)

        return errors

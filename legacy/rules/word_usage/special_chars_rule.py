"""
Special Characters Rule — Deterministic YAML lookup.
IBM Style Guide (p.284-285): Special character and number usage entries.
Handles symbols, ordinals, and numeric formatting patterns.
"""
import os
import re

import yaml
from typing import List, Dict, Any, Optional

from .base_word_usage_rule import BaseWordUsageRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> Dict[str, str]:
    """Load special character term map from YAML config."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'word_usage_config.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return config.get('special', {})
    except (FileNotFoundError, yaml.YAMLError):
        return {}


def _build_patterns(term_map: Dict[str, str]) -> List[tuple]:
    """Pre-compile regex patterns for all terms."""
    compiled = []
    for wrong, right in term_map.items():
        if any(c.isalnum() for c in wrong):
            pat = re.compile(r'\b' + re.escape(wrong) + r'\b')
        else:
            pat = re.compile(re.escape(wrong))
        compiled.append((wrong, right, pat))
    return compiled


_TERM_MAP = _load_config()
_PATTERNS = _build_patterns(_TERM_MAP)


class SpecialCharsRule(BaseWordUsageRule):
    """Flag incorrect special character and number usage."""

    def _get_rule_type(self) -> str:
        return 'word_usage_special'

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
            self._check_sent(sent, i, text, context, errors)

        return errors

    def _check_sent(self, sent, idx, text, context, errors):
        """Check a single sentence against all special character patterns."""
        for _wrong, right, pattern in _PATTERNS:
            for match in pattern.finditer(sent.text):
                found = match.group(0)
                error = self._create_error(
                    sentence=sent.text,
                    sentence_index=idx,
                    message=f"Use '{right}' instead of '{found}'.",
                    suggestions=[f"Change '{found}' to '{right}'"],
                    severity='medium',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(sent.start_char + match.start(),
                          sent.start_char + match.end()),
                )
                if error:
                    errors.append(error)

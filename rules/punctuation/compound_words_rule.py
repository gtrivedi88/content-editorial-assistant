"""
Compound Words Rule — Deterministic YAML lookup.
Flag incorrect compound word and hyphenation forms.
Source: Red Hat Vale Hyphens rule + IBM Style Guide.
"""
import os
import re

import yaml
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_punctuation_rule import BasePunctuationRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> Dict[str, str]:
    """Load compound words map from YAML config."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'compound_words_config.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return config.get('compound_words', {})
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_TERM_MAP = _load_config()


class CompoundWordsRule(BasePunctuationRule):
    """Flag incorrect compound word and hyphenation forms."""

    def _get_rule_type(self) -> str:
        return 'compound_words'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        code_ranges = context.get("inline_code_ranges", [])
        errors: List[Dict[str, Any]] = []

        for i, sent in enumerate(doc.sents):
            self._check_sentence(sent, i, text, context, code_ranges,
                                 errors)
        return errors

    def _check_sentence(self, sent, idx, text, context, code_ranges,
                        errors):
        """Check a single SpaCy sentence for compound word violations."""
        for wrong, right in _TERM_MAP.items():
            pattern = r'\b' + re.escape(wrong) + r'\b'
            for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                found = match.group(0)
                start = sent.start_char + match.start()
                if in_code_range(start, code_ranges):
                    continue
                end = sent.start_char + match.end()
                error = self._create_error(
                    sentence=sent.text,
                    sentence_index=idx,
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

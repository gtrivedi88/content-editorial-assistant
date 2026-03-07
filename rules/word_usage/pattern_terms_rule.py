"""
Pattern Terms Rule — Regex-guarded word usage checks.
Handles terms that need lookbehinds/lookaheads to avoid false positives.
Loads from the 'pattern_terms' section of word_usage_config.yaml.
"""
import os
import re
from typing import List, Dict, Any, Optional

import yaml

from .base_word_usage_rule import BaseWordUsageRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_pattern_terms() -> List[Dict[str, Any]]:
    """Load pattern_terms from word_usage_config.yaml."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'word_usage_config.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            return config.get('pattern_terms', [])
    except (FileNotFoundError, yaml.YAMLError):
        return []


def _compile_patterns(terms: List[Dict[str, Any]]) -> List[tuple]:
    """Pre-compile regex patterns for all pattern terms."""
    compiled = []
    for entry in terms:
        wrong = entry.get('wrong', '')
        right = entry.get('right', '')
        pattern_str = entry.get('pattern', r'\b' + re.escape(wrong) + r'\b')
        try:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            compiled.append((wrong, right, pattern))
        except re.error:
            continue
    return compiled


_PATTERN_TERMS = _load_pattern_terms()
_COMPILED = _compile_patterns(_PATTERN_TERMS)


class PatternTermsRule(BaseWordUsageRule):
    """Flag word usage issues that require regex guards."""

    def _get_rule_type(self) -> str:
        return 'word_usage_pattern'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        """Analyze text for pattern-guarded word usage violations."""
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []
        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors: List[Dict[str, Any]] = []

        for i, sent in enumerate(doc.sents):
            protected_ranges = self._get_protected_ranges(sent.text)
            for _wrong, right, pattern in _COMPILED:
                for match in pattern.finditer(sent.text):
                    if self._is_in_protected_range(
                        match.start(), match.end(), protected_ranges
                    ):
                        continue
                    found = match.group(0)
                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
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

        return errors

"""
Product Names Rule — Deterministic YAML lookup (case-sensitive).
Enforce correct capitalization for product and technology names.
Source: Red Hat Vale CaseSensitiveTerms rule.
"""
import os
import re
import logging

import yaml
from typing import List, Dict, Any, Optional

from .base_word_usage_rule import BaseWordUsageRule

logger = logging.getLogger(__name__)

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])


def _load_config() -> tuple:
    """Load simple_terms and regex_terms from YAML config."""
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'product_names_config.yaml',
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f) or {}
            simple = config.get('simple_terms', {})
            regex = config.get('regex_terms', {})
            return simple, regex
    except (FileNotFoundError, yaml.YAMLError) as exc:
        logger.warning("Failed to load product_names_config.yaml: %s", exc)
        return {}, {}


_SIMPLE_TERMS, _REGEX_TERMS = _load_config()

# Pre-compile simple term patterns (case-sensitive, word boundary)
_SIMPLE_PATTERNS = []
for wrong, right in _SIMPLE_TERMS.items():
    try:
        pattern = re.compile(r'\b' + re.escape(wrong) + r'\b')
        _SIMPLE_PATTERNS.append((pattern, wrong, right))
    except re.error as exc:
        logger.warning("Invalid simple pattern for '%s': %s", wrong, exc)

# Pre-compile regex term patterns (case-sensitive, no word boundary added)
_REGEX_PATTERNS = []
for pattern_str, right in _REGEX_TERMS.items():
    try:
        pattern = re.compile(pattern_str)
        _REGEX_PATTERNS.append((pattern, right))
    except re.error as exc:
        logger.warning("Invalid regex pattern '%s': %s", pattern_str, exc)


class ProductNamesRule(BaseWordUsageRule):
    """Enforce correct capitalization for product and technology names."""

    def _get_rule_type(self) -> str:
        return 'product_names'

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

            # Check simple_terms (case-sensitive word boundary match)
            for pattern, wrong, right in _SIMPLE_PATTERNS:
                for match in pattern.finditer(sent.text):
                    found = match.group(0)
                    if found == right:
                        continue
                    if self._is_in_protected_range(match.start(), match.end(), protected_ranges):
                        continue
                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()

                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=(
                            f"Use '{right}' instead of '{found}'. "
                            f"Ensure correct capitalization."
                        ),
                        suggestions=[f"Change '{found}' to '{right}'"],
                        severity='medium',
                        text=text,
                        context=context,
                        flagged_text=found,
                        span=(start, end),
                    )
                    if error:
                        errors.append(error)

            # Check regex_terms (complex patterns with lookbehind/lookahead)
            for pattern, right in _REGEX_PATTERNS:
                for match in pattern.finditer(sent.text):
                    found = match.group(0)
                    if found == right:
                        continue
                    if self._is_in_protected_range(match.start(), match.end(), protected_ranges):
                        continue
                    start = sent.start_char + match.start()
                    end = sent.start_char + match.end()

                    error = self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=(
                            f"Use '{right}' instead of '{found}'. "
                            f"Ensure correct capitalization."
                        ),
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

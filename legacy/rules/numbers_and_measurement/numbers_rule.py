"""
Numbers Rule — Deterministic regex-based detection.
IBM Style Guide (Page 150): Format numbers correctly.
1. Use comma separators for numbers with 4+ digits (1000 -> 1,000)
2. Use leading zero for decimals less than 1 (.5 -> 0.5)
Configuration loaded from config/number_formatting.yaml.
"""
import os
import re

import yaml
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule

def _load_config():
    config_path = os.path.join(
        os.path.dirname(__file__), 'config', 'number_formatting.yaml'
    )
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}

_CONFIG = _load_config()

# Regex: 4+ digit integer without commas (word-boundary delimited)
_THOUSANDS_RE = re.compile(r'\b(\d{4,})\b')
# Regex: decimal without leading zero (e.g. .5, .75)
_LEADING_ZERO_RE = re.compile(r'(?<![.\d])\.(\d+)\b')

# Guards for thousands-separator check
_HEX_RE = re.compile(r'0x[0-9a-fA-F]+')
_VERSION_RE = re.compile(r'\d+\.\d+\.\d+')
_YEAR_RE = re.compile(r'\b(19|20)\d{2}\b')
_IP_RE = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')
_PORT_RE = re.compile(r'(?i)(?:port|:)\s*\d{4,5}\b')

_CODE_BLOCK_TYPES = frozenset([
    'listing', 'literal', 'code_block', 'inline_code',
])


def _collect_guard_spans(sent_text):
    """Collect character spans of hex, version, and IP patterns to skip."""
    spans = set()
    for regex in (_HEX_RE, _VERSION_RE, _IP_RE):
        for m in regex.finditer(sent_text):
            spans.add(m.span())
    return spans


def _span_inside_any(start, end, guard_spans):
    """Return True if (start, end) falls inside any guard span."""
    return any(gs <= start and end <= ge for gs, ge in guard_spans)


class NumbersRule(BaseNumbersRule):
    """Checks for missing comma separators and missing leading zeros."""

    def _get_rule_type(self) -> str:
        return 'numbers_general'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        # Skip code blocks entirely
        if context and context.get('block_type') in _CODE_BLOCK_TYPES:
            return []

        errors: List[Dict[str, Any]] = []
        if not nlp:
            return errors

        doc = spacy_doc if spacy_doc is not None else nlp(text)

        for i, sent in enumerate(doc.sents):
            sent_text = sent.text
            self._check_thousands(sent_text, sent.start_char, i, errors, text, context)
            self._check_leading_zero(sent_text, sent.start_char, i, errors, text, context)

        return errors

    # ------------------------------------------------------------------
    # Check 1: Thousands separators
    # ------------------------------------------------------------------
    def _check_thousands(self, sent_text, sent_offset, sent_idx,
                         errors, text, context):
        guard_spans = _collect_guard_spans(sent_text)

        for match in _THOUSANDS_RE.finditer(sent_text):
            number = match.group(0)
            start, end = match.start(), match.end()

            if self._is_guarded_number(number, start, end, sent_text, guard_spans):
                continue

            formatted = f"{int(number):,}"
            span = (sent_offset + start, sent_offset + end)
            message = (
                f"Use comma separators for numbers with 4 or more digits: "
                f"'{number}' \u2192 '{formatted}'."
            )
            error = self._create_error(
                sentence=sent_text,
                sentence_index=sent_idx,
                message=message,
                suggestions=[f"Change '{number}' to '{formatted}'."],
                severity='medium',
                text=text,
                context=context,
                span=span,
                flagged_text=number,
            )
            if error:
                errors.append(error)

    @staticmethod
    def _is_guarded_number(number, start, end, sent_text, guard_spans):
        """Return True if the number should be skipped (false positive)."""
        if _span_inside_any(start, end, guard_spans):
            return True
        if _YEAR_RE.fullmatch(number):
            return True
        if _PORT_RE.search(sent_text[max(0, start - 6):end]):
            return True
        return False

    # ------------------------------------------------------------------
    # Check 2: Leading zeros
    # ------------------------------------------------------------------
    def _check_leading_zero(self, sent_text, sent_offset, sent_idx,
                            errors, text, context):
        for match in _LEADING_ZERO_RE.finditer(sent_text):
            found = match.group(0)  # e.g. ".5"
            start, end = match.start(), match.end()
            span = (sent_offset + start, sent_offset + end)
            corrected = f"0{found}"
            message = (
                f"Add a leading zero before the decimal point: "
                f"'{found}' \u2192 '{corrected}'."
            )
            error = self._create_error(
                sentence=sent_text,
                sentence_index=sent_idx,
                message=message,
                suggestions=[f"Change '{found}' to '{corrected}'."],
                severity='medium',
                text=text,
                context=context,
                span=span,
                flagged_text=found,
            )
            if error:
                errors.append(error)

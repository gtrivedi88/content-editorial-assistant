"""
Dates and Times Rule
Based on IBM Style Guide topic: "Dates and times" (p.144)

Two deterministic checks:
1. Ambiguous all-numeric dates (e.g., 12/25/2023) -> suggest "25 December 2023"
2. Incorrect AM/PM formats (e.g., 11.30AM, 11:30 a.m.) -> suggest "11:30 AM"

Patterns and messages loaded from config/date_time_formats.yaml.
"""

import os
import re
from typing import List, Dict, Any

import yaml

from .base_numbers_rule import BaseNumbersRule

_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'config', 'date_time_formats.yaml'
)


def _load_config() -> Dict[str, Any]:
    """Load date/time format config from YAML."""
    with open(_CONFIG_PATH, 'r', encoding='utf-8') as fh:
        return yaml.safe_load(fh)


_CFG = _load_config()

_AMBIGUOUS_DATE_RE = re.compile(_CFG['ambiguous_date']['pattern'])
_ISO_8601_RE = re.compile(_CFG['iso_8601']['pattern'])
_VERSION_RE = re.compile(_CFG['version_number']['pattern'])
_INCORRECT_AMPM_RE = re.compile(_CFG['incorrect_ampm']['pattern'])
_CORRECT_AMPM_RE = re.compile(_CFG['incorrect_ampm']['correct_ampm'])

_CODE_BLOCK_TYPES = frozenset([
    'listing', 'literal', 'code_block', 'inline_code',
])


class DatesAndTimesRule(BaseNumbersRule):
    """Check for ambiguous date formats and incorrect AM/PM formatting."""

    def _get_rule_type(self) -> str:
        return 'dates_and_times'

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def analyze(
        self,
        text: str,
        sentences: List[str],
        nlp=None,
        context=None,
        spacy_doc=None,
    ) -> List[Dict[str, Any]]:
        """Return a list of date/time formatting violations."""
        context = context or {}

        # Guard: skip code blocks entirely
        if context.get('block_type') in _CODE_BLOCK_TYPES:
            return []

        if not nlp:
            return []

        doc = spacy_doc if spacy_doc is not None else nlp(text)
        errors: List[Dict[str, Any]] = []

        for sent_idx, sent in enumerate(doc.sents):
            sent_text = sent.text
            errors.extend(self._check_ambiguous_dates(sent_text, sent_idx, sent, context))
            errors.extend(self._check_ampm_format(sent_text, sent_idx, sent, context))

        return errors

    # ------------------------------------------------------------------
    # Check 1 — ambiguous all-numeric dates
    # ------------------------------------------------------------------

    def _check_ambiguous_dates(
        self, sent_text: str, sent_idx: int, sent, context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for match in _AMBIGUOUS_DATE_RE.finditer(sent_text):
            found = match.group(0)

            # Guard: skip ISO 8601 (YYYY-MM-DD)
            if _ISO_8601_RE.fullmatch(found):
                continue

            # Guard: skip version numbers (1.2.3)
            if _VERSION_RE.fullmatch(found):
                continue

            msg = _CFG['ambiguous_date']['message'].format(found=found)
            error = self._create_error(
                sentence=sent_text,
                sentence_index=sent_idx,
                message=msg,
                suggestions=["Use 'day month year' format (e.g., '2 December 2021')."],
                severity=_CFG['ambiguous_date']['severity'],
                context=context,
                span=[sent.start_char + match.start(), sent.start_char + match.end()],
                flagged_text=found,
            )
            if error:
                results.append(error)
        return results

    # ------------------------------------------------------------------
    # Check 2 — incorrect AM/PM format
    # ------------------------------------------------------------------

    def _check_ampm_format(
        self, sent_text: str, sent_idx: int, sent, context: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for match in _INCORRECT_AMPM_RE.finditer(sent_text):
            found = match.group(0)

            # Guard: skip if already correct (e.g., "11:30 AM")
            if _CORRECT_AMPM_RE.fullmatch(found):
                continue

            msg = _CFG['incorrect_ampm']['message'].format(found=found)
            error = self._create_error(
                sentence=sent_text,
                sentence_index=sent_idx,
                message=msg,
                suggestions=["Use colon separator, uppercase AM/PM with a space (e.g., '11:30 AM')."],
                severity=_CFG['incorrect_ampm']['severity'],
                context=context,
                span=[sent.start_char + match.start(), sent.start_char + match.end()],
                flagged_text=found,
            )
            if error:
                results.append(error)
        return results

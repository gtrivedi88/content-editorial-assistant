"""
Numerals versus Words Rule
IBM Style Guide (p.157): "Always use words for the first number
if it occurs at the beginning of a sentence."

Checks for numerals at the start of a sentence and suggests spelling them out.
"""

import os
import re
import yaml
from typing import List, Dict, Any, Optional
from .base_numbers_rule import BaseNumbersRule

_LEADING_NUMERAL_RE = re.compile(r'^(\d+(?:\.\d+)?)\b')
_VERSION_RE = re.compile(r'^\d+\.\d+')
_MEASUREMENT_UNIT_RE = re.compile(
    r'\s*(?:GB|MB|KB|TB|PB|GiB|MiB|KiB|TiB|'
    r'ms|ns|us|μs|Hz|GHz|MHz|kHz|'
    r'px|em|rem|pt|cm|mm|m|km|in|ft|'
    r'%|°|Gbps|Mbps|Kbps|bps|rpm)\b',
)


class NumeralsVsWordsRule(BaseNumbersRule):
    """Flag sentences that begin with a bare numeral."""

    _config = None

    def _get_rule_type(self) -> str:
        return 'numerals_vs_words'

    @classmethod
    def _load_config(cls) -> Dict[str, Any]:
        """Load and cache the YAML configuration file."""
        if cls._config is None:
            path = os.path.join(
                os.path.dirname(__file__), 'config',
                'numerals_vs_words.yaml'
            )
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    cls._config = yaml.safe_load(f) or {}
            except (OSError, yaml.YAMLError):
                cls._config = {}
        return cls._config

    @staticmethod
    def _is_skippable_numeral(found: str, stripped: str, end_pos: int) -> bool:
        """Check whether a leading numeral is a measurement or version number.

        Args:
            found: The matched numeral string.
            stripped: The whitespace-stripped sentence.
            end_pos: End position of the numeral match in stripped.

        Returns:
            True if the numeral should be skipped (measurement unit or version).
        """
        rest_of_sent = stripped[end_pos:]
        if _MEASUREMENT_UNIT_RE.match(rest_of_sent):
            return True
        if _VERSION_RE.match(found):
            return True
        return False

    def analyze(self, text: str, sentences: List[str],
                nlp=None, context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        """Analyze sentences for numerals at the start.

        Args:
            text: Full document text.
            sentences: Pre-split sentence list.
            nlp: SpaCy language model (unused).
            context: Analysis context dict (optional).
            spacy_doc: Pre-built SpaCy Doc (unused).

        Returns:
            List of error dicts for sentences starting with numerals.
        """
        cfg = self._load_config()
        skip_types = cfg.get('skip_block_types', [])
        numeral_words = cfg.get('numeral_words', {})
        list_patterns = [
            re.compile(p) for p in cfg.get('list_item_patterns', [])
        ]

        if context and context.get('block_type') in skip_types:
            return []

        errors: List[Dict[str, Any]] = []

        for i, sent in enumerate(sentences):
            stripped = sent.lstrip()
            if not stripped:
                continue

            if any(p.match(stripped) for p in list_patterns):
                continue

            m = _LEADING_NUMERAL_RE.match(stripped)
            if not m:
                continue

            found = m.group(1)
            if self._is_skippable_numeral(found, stripped, m.end()):
                continue

            suggestion = numeral_words.get(found)
            hint = (
                f"Spell out the number: '{suggestion} ...'"
                if suggestion
                else "Rephrase so the sentence does not start with a numeral."
            )

            error = self._create_error(
                sentence=sent,
                sentence_index=i,
                message=(
                    f"Do not start a sentence with a numeral. "
                    f"Spell out the number or rephrase: '{found}'."
                ),
                suggestions=[hint],
                severity='medium',
                text=text,
                context=context,
                flagged_text=found,
                span=(sent.index(found), sent.index(found) + len(found)),
            )
            if error:
                errors.append(error)

        return errors

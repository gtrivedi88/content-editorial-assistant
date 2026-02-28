"""
Currency Rule
Based on IBM Style Guide topic: "Currency"

Two checks:
1. Ambiguous currency symbols ($, EUR, GBP) without ISO code context.
2. Letter multipliers (4M, 10K, 2B) instead of spelled-out words.
"""

import os
import re
from typing import List, Dict, Any

import yaml

from .base_numbers_rule import BaseNumbersRule

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config', 'currency_patterns.yaml')


def _load_config():
    """Load currency patterns from YAML once."""
    with open(_CONFIG_PATH, 'r', encoding='utf-8') as fh:
        return yaml.safe_load(fh)


_CFG = _load_config()

# Build symbol lookup: {"$": "USD", ...}
_SYMBOL_TO_ISO = {
    entry['symbol']: entry['iso_code']
    for entry in _CFG.get('currency_symbols', {}).get('major_currencies', [])
}

# Build multiplier lookup: {"K": "thousand", ...}
_MULTIPLIER_WORD = {
    entry['multiplier'].upper(): entry['alternatives'][0]
    for entry in _CFG.get('currency_multipliers', {}).get('letter_multipliers', [])
    if entry.get('alternatives')
}

# Regex: currency symbol followed by a number (e.g. $100, EUR500.00)
_SYMBOL_RE = re.compile(
    r'([\$\u20ac\u00a3\u00a5])\s?(\d[\d,.]*)',  # $, EUR, GBP, JPY
)

# Regex: number followed by a letter multiplier (e.g. 4M, 10K, 2.5B)
_MULTIPLIER_RE = re.compile(
    r'(\d[\d,.]*)\s?([KMBkmb])\b',
)

# ISO codes that, when adjacent, mean the symbol is already qualified
_ISO_CODES = {entry['iso_code'] for entry in
              _CFG.get('currency_symbols', {}).get('major_currencies', [])}

_CODE_BLOCK_TYPES = frozenset([
    'listing', 'literal', 'code_block', 'inline_code', 'literal_block',
])


class CurrencyRule(BaseNumbersRule):
    """Check currency formatting: prefer ISO codes over symbols,
    spell out multipliers instead of letter abbreviations."""

    def _get_rule_type(self) -> str:
        return 'numbers_currency'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        if context and context.get('block_type') in _CODE_BLOCK_TYPES:
            return []

        errors: List[Dict[str, Any]] = []

        for idx, sentence in enumerate(sentences):
            errors.extend(self._check_symbols(sentence, idx, text, context))
            errors.extend(self._check_multipliers(sentence, idx, text, context))

        return errors

    # ------------------------------------------------------------------
    # Check 1: ambiguous currency symbols without ISO qualifier
    # ------------------------------------------------------------------
    def _check_symbols(self, sentence: str, idx: int,
                       text: str, context) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for m in _SYMBOL_RE.finditer(sentence):
            symbol = m.group(1)
            iso = _SYMBOL_TO_ISO.get(symbol)
            if not iso:
                continue
            # Skip if the sentence already contains the ISO code
            if iso in sentence:
                continue
            flagged = m.group(0)
            amount = m.group(2)
            msg = (f"Use ISO currency code instead of symbol: "
                   f"specify '{iso} {amount}' instead of '{flagged}'.")
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=msg,
                suggestions=[f"Replace '{flagged}' with '{iso} {amount}'."],
                severity='medium',
                text=text,
                context=context,
                flagged_text=flagged,
            )
            if error:
                results.append(error)
        return results

    # ------------------------------------------------------------------
    # Check 2: letter multipliers (K, M, B)
    # ------------------------------------------------------------------
    def _check_multipliers(self, sentence: str, idx: int,
                           text: str, context) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for m in _MULTIPLIER_RE.finditer(sentence):
            number = m.group(1)
            letter = m.group(2).upper()
            word = _MULTIPLIER_WORD.get(letter)
            if not word:
                continue
            flagged = m.group(0)
            msg = (f"Do not abbreviate '{word}' to '{letter}'. "
                   f"Write '{number} {word}' instead.")
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=msg,
                suggestions=[f"Replace '{flagged}' with '{number} {word}'."],
                severity='medium',
                text=text,
                context=context,
                flagged_text=flagged,
            )
            if error:
                results.append(error)
        return results

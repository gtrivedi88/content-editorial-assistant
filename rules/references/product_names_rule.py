"""
Product and Service Names Rule — Deterministic YAML-lookup + regex detection.
IBM Style Guide (p. 228-232):
1. Do not change the form or representation of a product name,
   including its capitalization or punctuation.
2. Do not use the possessive form of brand or product names.
3. Do not abbreviate product names unless approved.

Guards: skip code blocks, inline code, and quoted text.
"""
import os
import re
import yaml
from typing import List, Dict, Any, Optional

from rules.base_rule import in_code_range
from .base_references_rule import BaseReferencesRule

_SKIP_BLOCKS = frozenset(['code_block', 'listing', 'literal', 'inline_code'])

def _load_config() -> Dict[str, Any]:
    """Load product names config from YAML."""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'product_names_config.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


_CONFIG = _load_config()

# Check 1: Product name misspellings (wrong capitalization)
_MISSPELLINGS: Dict[str, str] = _CONFIG.get('product_misspellings', {})

# Check 2: Prohibited product abbreviations
_PROHIBITED_ABBREVS: Dict[str, str] = _CONFIG.get('prohibited_abbreviations', {})

# Check 3: Known IBM products for possessive check
_IBM_PRODUCTS: List[str] = _CONFIG.get('ibm_products', [])

# Build regex for possessive check: "Watson's", "WebSphere's", etc.
_POSSESSIVE_RE = None
if _IBM_PRODUCTS:
    _products_pattern = '|'.join(re.escape(p) for p in _IBM_PRODUCTS)
    _POSSESSIVE_RE = re.compile(
        r"\b(" + _products_pattern + r")'s\b"
    )


def _in_quotes(pos: int, text: str) -> bool:
    """Check if position is inside quotation marks."""
    for pattern in [r'"([^"]*)"', r"'([^']*)'"]:
        for m in re.finditer(pattern, text):
            if m.start() <= pos < m.end():
                return True
    return False


class ProductNamesRule(BaseReferencesRule):
    """Flag product name misspellings, prohibited abbreviations,
    and possessive forms of brand names."""

    def _get_rule_type(self) -> str:
        return 'references_product_names'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context: Optional[Dict[str, Any]] = None,
                spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}
        if context.get('block_type') in _SKIP_BLOCKS:
            return []

        code_ranges = context.get("inline_code_ranges", []) if context else []
        errors: List[Dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            sent_start = text.find(sentence)
            self._check_misspellings(sentence, idx, text, context, code_ranges, sent_start, errors)
            self._check_prohibited_abbreviations(sentence, idx, text, context, code_ranges, sent_start, errors)
            self._check_possessive_form(sentence, idx, text, context, code_ranges, sent_start, errors)
        return errors

    # ------------------------------------------------------------------
    # Check 1 — product name misspellings
    # ------------------------------------------------------------------
    def _check_misspellings(self, sentence, idx, text, context,
                            code_ranges, sent_start, errors):
        for wrong, correct in _MISSPELLINGS.items():
            # Case-sensitive match — the misspelling keys are specific forms
            pattern = re.compile(r'\b' + re.escape(wrong) + r'\b')
            for match in pattern.finditer(sentence):
                if in_code_range(sent_start + match.start(), code_ranges):
                    continue
                if _in_quotes(match.start(), sentence):
                    continue
                found = match.group(0)
                # Don't flag if the text already matches the correct form
                if found == correct:
                    continue
                error = self._create_error(
                    sentence=sentence,
                    sentence_index=idx,
                    message=(
                        f"Use the correct product name capitalization: "
                        f"'{found}' -> '{correct}'."
                    ),
                    suggestions=[
                        f"Write '{correct}' instead of '{found}'.",
                        "Do not change the capitalization or punctuation of product names.",
                    ],
                    severity='high',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(match.start(), match.end()),
                )
                if error is not None:
                    errors.append(error)

    # ------------------------------------------------------------------
    # Check 2 — prohibited product abbreviations
    # ------------------------------------------------------------------
    def _check_prohibited_abbreviations(self, sentence, idx, text, context,
                                        code_ranges, sent_start, errors):
        for abbrev, full_name in _PROHIBITED_ABBREVS.items():
            pattern = re.compile(r'\b' + re.escape(abbrev) + r'\b')
            for match in pattern.finditer(sentence):
                if in_code_range(sent_start + match.start(), code_ranges):
                    continue
                if _in_quotes(match.start(), sentence):
                    continue
                found = match.group(0)
                error = self._create_error(
                    sentence=sentence,
                    sentence_index=idx,
                    message=(
                        f"Do not abbreviate product names: "
                        f"'{found}' -> '{full_name}'."
                    ),
                    suggestions=[
                        f"Write '{full_name}' instead of '{found}'.",
                        "Do not abbreviate product, brand, or service names.",
                    ],
                    severity='high',
                    text=text,
                    context=context,
                    flagged_text=found,
                    span=(match.start(), match.end()),
                )
                if error is not None:
                    errors.append(error)

    # ------------------------------------------------------------------
    # Check 3 — possessive form of brand/product names
    # ------------------------------------------------------------------
    def _check_possessive_form(self, sentence, idx, text, context,
                               code_ranges, sent_start, errors):
        if _POSSESSIVE_RE is None:
            return
        for match in _POSSESSIVE_RE.finditer(sentence):
            if in_code_range(sent_start + match.start(), code_ranges):
                continue
            if _in_quotes(match.start(), sentence):
                continue
            product = match.group(1)
            found = match.group(0)
            error = self._create_error(
                sentence=sentence,
                sentence_index=idx,
                message=(
                    f"Do not use the possessive form of product names: "
                    f"'{found}'. Rephrase to avoid the possessive."
                ),
                suggestions=[
                    f"Rephrase: 'the {product} feature' instead of '{found} feature'.",
                    f"Use 'in {product}' or 'the {product}' instead of the possessive.",
                ],
                severity='medium',
                text=text,
                context=context,
                flagged_text=found,
                span=(match.start(), match.end()),
            )
            if error is not None:
                errors.append(error)

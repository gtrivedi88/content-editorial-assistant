"""
Units of Measurement Rule
IBM Style Guide (p.161): Place a space between the number and the unit.
"100 mm" not "100mm".
"""

import os
import re
from typing import List, Dict, Any

import yaml

from .base_numbers_rule import BaseNumbersRule

_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), '..', '..', 'config', 'measurement_units.yaml'
)


def _load_units() -> List[str]:
    """Load unit abbreviations from config/measurement_units.yaml."""
    with open(_CONFIG_PATH, 'r', encoding='utf-8') as fh:
        data = yaml.safe_load(fh)
    units: List[str] = []
    for category_units in data.values():
        if isinstance(category_units, list):
            units.extend(str(u) for u in category_units)
    # Sort longest-first so the regex is greedy on longer abbreviations.
    units.sort(key=len, reverse=True)
    return units


# Pre-compile the pattern once at module load.
_UNITS = _load_units()
_UNITS_RE = re.compile(
    r'(\d+(?:\.\d+)?)(' + '|'.join(re.escape(u) for u in _UNITS) + r')\b'
)

# CSS / web units that should be ignored even outside explicit code blocks.
_CSS_UNITS = frozenset(['px', 'em', 'rem', 'vw', 'vh', 'vmin', 'vmax', 'ch', 'ex', 'pt'])


class UnitsOfMeasurementRule(BaseNumbersRule):
    """Check for a missing space between a number and its unit of measurement."""

    def _get_rule_type(self) -> str:
        return 'units_of_measurement'

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        context = context or {}

        # Guard: skip code blocks entirely.
        if context.get('block_type') in (
            'listing', 'literal', 'code_block', 'inline_code'
        ):
            return []

        errors: List[Dict[str, Any]] = []

        for idx, sentence in enumerate(sentences):
            for match in _UNITS_RE.finditer(sentence):
                number = match.group(1)
                unit = match.group(2)
                found = match.group(0)

                # Guard: skip CSS-like values (e.g. "10px", "2em").
                if unit.lower() in _CSS_UNITS:
                    continue

                corrected = f"{number} {unit}"
                message = (
                    f"Add a space between the number and the unit: "
                    f"'{found}' \u2192 '{corrected}'."
                )

                error = self._create_error(
                    sentence=sentence,
                    sentence_index=idx,
                    message=message,
                    suggestions=[corrected],
                    severity='medium',
                    text=text,
                    context=context,
                    span=[match.start(), match.end()],
                    flagged_text=found,
                )
                if error is not None:
                    errors.append(error)

        return errors

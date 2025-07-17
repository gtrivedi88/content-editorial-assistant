"""
Units of Measurement Rule
Based on IBM Style Guide topic: "Units of measurement"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

class UnitsOfMeasurementRule(BaseNumbersRule):
    """
    Checks for correct formatting of units of measurement, such as ensuring
    a space between the number and the unit abbreviation.
    """
    def _get_rule_type(self) -> str:
        return 'numbers_units_of_measurement'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for unit of measurement formatting errors.
        """
        errors = []
        # Regex to find a number immediately followed by a common unit, with no space.
        no_space_pattern = re.compile(r'\b\d+(mm|cm|m|km|mg|g|kg|ms|s|min|hr|Hz|MHz|GHz|KB|MB|GB|TB)\b')

        for i, sentence in enumerate(sentences):
            matches = no_space_pattern.finditer(sentence)
            for match in matches:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=f"Missing space between number and unit of measurement: '{match.group()}'.",
                    suggestions=["Insert a space between the number and the unit (e.g., '600 MHz')."],
                    severity='medium'
                ))
        return errors

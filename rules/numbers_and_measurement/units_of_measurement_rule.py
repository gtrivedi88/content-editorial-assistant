"""
Units of Measurement Rule
Based on IBM Style Guide topic: "Units of measurement"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

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
        if not nlp:
            return errors
        doc = nlp(text)
        
        no_space_pattern = re.compile(r'\b\d+(mm|cm|m|km|mg|g|kg|ms|s|min|hr|Hz|MHz|GHz|KB|MB|GB|TB)\b')

        for i, sent in enumerate(doc.sents):
            for match in no_space_pattern.finditer(sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message=f"Missing space between number and unit of measurement: '{match.group()}'.",
                    suggestions=["Insert a space between the number and the unit (e.g., '600 MHz')."],
                    severity='medium',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
        return errors

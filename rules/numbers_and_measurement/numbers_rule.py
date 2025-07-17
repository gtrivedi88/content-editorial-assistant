"""
Numbers Rule
Based on IBM Style Guide topic: "Numbers"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

class NumbersRule(BaseNumbersRule):
    """
    Checks for general number formatting issues, such as missing comma
    separators and incorrect decimal formatting.
    """
    def _get_rule_type(self) -> str:
        return 'numbers_general'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for number formatting violations.
        """
        errors = []
        # Regex to find numbers with 5 or more digits without commas
        no_comma_pattern = re.compile(r'\b\d{5,}\b')
        # Regex to find decimals starting with a dot without a leading zero
        leading_decimal_pattern = re.compile(r'\s\.\d+')

        for i, sentence in enumerate(sentences):
            # Guideline: Use a comma to separate groups of three numerals.
            # This rule simplifies by checking for any long number string without commas.
            if no_comma_pattern.search(sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Large numbers should use commas as thousands separators.",
                    suggestions=["Add commas to numbers with five or more digits (e.g., '10,999')."],
                    severity='medium'
                ))

            # Guideline: Put a 0 in front of the decimal separator for values less than 1.
            if leading_decimal_pattern.search(sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Decimal values less than 1 should have a leading zero.",
                    suggestions=["Add a '0' before the decimal point (e.g., '0.25')."],
                    severity='medium'
                ))
        return errors

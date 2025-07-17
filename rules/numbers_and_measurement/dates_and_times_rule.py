"""
Dates and Times Rule
Based on IBM Style Guide topic: "Dates and times"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

class DatesAndTimesRule(BaseNumbersRule):
    """
    Checks for correct and internationally understandable date and time formats.
    """
    def _get_rule_type(self) -> str:
        return 'numbers_dates_times'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for common date and time formatting errors.
        """
        errors = []
        # Regex for numeric-only dates like 9/12/2023 or 2023-12-09
        numeric_date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
        # Regex for incorrect AM/PM formats
        am_pm_pattern = re.compile(r'\b\d{1,2}:\d{2}\s?(A\.M\.|p\.m\.|am|pm)\b')

        for i, sentence in enumerate(sentences):
            # Guideline: Avoid all-numeric date representations.
            if numeric_date_pattern.search(sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid all-numeric date formats to prevent international confusion.",
                    suggestions=["Use the format '14 July 2020'."],
                    severity='high'
                ))

            # Guideline: Use uppercase AM and PM with no periods.
            if am_pm_pattern.search(sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Use 'AM' or 'PM' (uppercase, no periods) for time.",
                    suggestions=["Replace incorrect variations like 'a.m.' or 'pm' with 'AM' or 'PM'."],
                    severity='medium'
                ))
        return errors

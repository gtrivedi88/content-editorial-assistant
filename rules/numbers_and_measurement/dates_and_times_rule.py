"""
Dates and Times Rule
Based on IBM Style Guide topic: "Dates and times"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class DatesAndTimesRule(BaseNumbersRule):
    """
    Checks for correct and internationally understandable date and time formats.
    """
    def _get_rule_type(self) -> str:
        return 'dates_and_times'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for common date and time formatting errors.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        numeric_date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
        am_pm_pattern = re.compile(r'\b\d{1,2}:\d{2}\s?(A\.M\.|p\.m\.|am|pm)\b')

        for i, sent in enumerate(doc.sents):
            # Guideline: Avoid all-numeric date representations.
            for match in numeric_date_pattern.finditer(sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Avoid all-numeric date formats to prevent international confusion.",
                    suggestions=["Use the format '14 July 2020'."],
                    severity='high',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))

            # Guideline: Use uppercase AM and PM with no periods.
            for match in am_pm_pattern.finditer(sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Use 'AM' or 'PM' (uppercase, no periods) for time.",
                    suggestions=["Replace incorrect variations like 'a.m.' or 'pm' with 'AM' or 'PM'."],
                    severity='medium',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
        return errors

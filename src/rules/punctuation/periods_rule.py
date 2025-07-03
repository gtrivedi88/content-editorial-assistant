"""
Periods Rule
Based on IBM Style Guide topic: "Periods"
"""
from typing import List, Dict, Any
import re
from .base_punctuation_rule import BasePunctuationRule

class PeriodsRule(BasePunctuationRule):
    """
    Checks for incorrect use of periods, such as in uppercase abbreviations.
    """
    def _get_rule_type(self) -> str:
        return 'periods'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        # Rule: Omit periods in uppercase abbreviations.
        # This regex finds patterns like U.S.A. or I.B.M.
        pattern = re.compile(r'\b(?:[A-Z]\.){2,}')
        
        for i, sentence in enumerate(sentences):
            for match in pattern.finditer(sentence):
                abbreviation = match.group(0)
                suggestion = abbreviation.replace('.', '')
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message=f"Avoid periods in the uppercase abbreviation '{abbreviation}'.",
                    suggestions=[f"Use '{suggestion}' instead."],
                    severity='low'
                ))
        return errors

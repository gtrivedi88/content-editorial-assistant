"""
Exclamation Points Rule
Based on IBM Style Guide topic: "Exclamation points"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class ExclamationPointsRule(BasePunctuationRule):
    """
    Checks for exclamation points, which should be avoided.
    """
    def _get_rule_type(self) -> str:
        return 'exclamation_points'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        for i, sentence in enumerate(sentences):
            if '!' in sentence:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid exclamation points in technical writing.",
                    suggestions=["Replace the exclamation point with a period."],
                    severity='low'
                ))
        return errors

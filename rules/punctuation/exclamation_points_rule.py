"""
Exclamation Points Rule
Based on IBM Style Guide topic: "Exclamation points"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class ExclamationPointsRule(BasePunctuationRule):
    """
    Checks for exclamation points, which should be avoided in technical writing
    according to the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'exclamation_points'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of exclamation points.
        """
        errors = []
        # The IBM Style Guide is direct: "Avoid exclamation points where a primarily
        # functional tone is appropriate." For technical documentation, this means
        # their presence is almost always a style violation. Therefore, a simple
        # and robust check for the character is the most reliable approach.
        for i, sentence in enumerate(sentences):
            if '!' in sentence:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid exclamation points in technical writing to maintain a professional tone.",
                    suggestions=["Replace the exclamation point with a period."],
                    severity='low'
                ))
        return errors

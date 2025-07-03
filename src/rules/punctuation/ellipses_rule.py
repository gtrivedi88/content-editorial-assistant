"""
Ellipses Rule
Based on IBM Style Guide topic: "Ellipses"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class EllipsesRule(BasePunctuationRule):
    """
    Checks for the use of ellipses, which should be avoided in general text.
    """
    def _get_rule_type(self) -> str:
        return 'ellipses'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        for i, sentence in enumerate(sentences):
            if '...' in sentence:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid using ellipses (...) in technical writing.",
                    suggestions=["If text is omitted, explain it. If it's for a pause, rewrite for a more formal tone."],
                    severity='low'
                ))
        return errors

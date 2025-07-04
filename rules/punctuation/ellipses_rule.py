"""
Ellipses Rule
Based on IBM Style Guide topic: "Ellipses"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class EllipsesRule(BasePunctuationRule):
    """
    Checks for the use of ellipses, which should be avoided in general text
    according to the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'ellipses'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of ellipses.
        """
        errors = []
        # The IBM Style Guide is direct: "Avoid using ellipses in text in most cases."
        # For technical documentation, their use for indicating a pause is discouraged.
        # Therefore, a simple and robust check for the character sequence is sufficient.
        for i, sentence in enumerate(sentences):
            if '...' in sentence:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid using ellipses (...) in technical writing.",
                    suggestions=["If text is omitted from a quote, this may be acceptable. Otherwise, if used for a pause, rewrite for a more formal and direct tone."],
                    severity='low'
                ))
        return errors

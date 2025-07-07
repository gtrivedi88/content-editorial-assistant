"""
Semicolons Rule
Based on IBM Style Guide topic: "Semicolons"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class SemicolonsRule(BasePunctuationRule):
    """
    Checks for semicolons, which are discouraged in technical writing by the
    IBM Style Guide in favor of shorter, clearer sentences.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'semicolons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of semicolons.
        """
        errors = []
        if not nlp:
            # This rule requires tokenization to be robust.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            # The IBM Style Guide advises against semicolons for clarity.
            # Therefore, we check for the presence of the semicolon token itself.
            # This is more reliable than a simple string search, as it won't be
            # confused by HTML entities or other special characters.
            if any(token.text == ';' for token in doc):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid semicolons in technical writing to improve clarity.",
                    suggestions=["Consider rewriting the sentence as two separate, shorter sentences."],
                    severity='low'
                ))
        return errors

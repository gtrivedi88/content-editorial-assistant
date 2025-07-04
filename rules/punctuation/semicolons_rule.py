"""
Semicolons Rule
Based on IBM Style Guide topic: "Semicolons"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class SemicolonsRule(BasePunctuationRule):
    """
    Checks for semicolons, which are often better replaced by shorter sentences.
    """
    def _get_rule_type(self) -> str:
        return 'semicolons'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        for i, sentence in enumerate(sentences):
            if ';' in sentence:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid semicolons in technical writing to improve clarity.",
                    suggestions=["Consider rewriting the sentence as two separate, shorter sentences."],
                    severity='low'
                ))
        return errors

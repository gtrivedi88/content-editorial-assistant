"""
Dashes Rule
Based on IBM Style Guide topic: "Dashes"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class DashesRule(BasePunctuationRule):
    """
    Checks for the use of em dashes, which are discouraged in technical info.
    """
    def _get_rule_type(self) -> str:
        return 'dashes'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            if '—' in sentence: # Check for em dash character
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid em dashes (—) in technical writing.",
                    suggestions=["Rewrite the sentence using commas, parentheses, or a colon instead."],
                    severity='medium'
                ))
        return errors

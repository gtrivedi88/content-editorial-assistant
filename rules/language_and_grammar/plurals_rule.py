"""
Plurals Rule
Based on IBM Style Guide topic: "Plurals"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class PluralsRule(BaseLanguageRule):
    """
    Checks for incorrect pluralization, such as using "(s)".
    """
    def _get_rule_type(self) -> str:
        return 'plurals'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        for i, sentence in enumerate(sentences):
            # Linguistic Anchor: The pattern "(s)" is explicitly forbidden.
            if "(s)" in sentence:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid using '(s)' to indicate a plural.",
                    suggestions=["Rewrite the sentence to use either the singular or plural form, or use a phrase like 'one or more'." ],
                    severity='medium'
                ))
        return errors

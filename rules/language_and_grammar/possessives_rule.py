"""
Possessives Rule
Based on IBM Style Guide topic: "Possessives"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class PossessivesRule(BaseLanguageRule):
    """
    Checks for incorrect use of possessives, such as with abbreviations.
    """
    def _get_rule_type(self) -> str:
        return 'possessives'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # Rule: Do not use 's to show the possessive form of an abbreviation.
                if token.text == "'s" and token.i > 0:
                    prev_token = doc[token.i - 1]
                    # Linguistic Anchor: Check if the preceding token is an abbreviation (all caps).
                    if prev_token.is_upper and len(prev_token.text) > 1:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Avoid using the possessive ''s' with the abbreviation '{prev_token.text}'.",
                            suggestions=[f"Rewrite using a prepositional phrase, such as 'the properties of {prev_token.text}'."],
                            severity='medium'
                        ))
        return errors

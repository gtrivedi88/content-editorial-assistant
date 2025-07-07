"""
Possessives Rule
Based on IBM Style Guide topic: "Possessives"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class PossessivesRule(BaseLanguageRule):
    """
    Checks for incorrect use of possessives, specifically flagging the use
    of apostrophe-s with uppercase abbreviations.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'possessives'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for incorrect possessive constructions with abbreviations.
        """
        errors = []
        if not nlp:
            # This rule requires tokenization and part-of-speech tagging.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # The rule triggers when it finds a token for the possessive 's.
                if token.text == "'s":
                    
                    # --- Context-Aware Check ---
                    # To avoid false positives, we check the preceding token.
                    if token.i > 0:
                        prev_token = doc[token.i - 1]
                        
                        # Linguistic Anchor: An uppercase word with more than one letter
                        # is a strong indicator of an abbreviation (e.g., API, HTML, GUI).
                        is_abbreviation = prev_token.is_upper and len(prev_token.text) > 1

                        if is_abbreviation:
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message=f"Avoid using the possessive ''s' with the abbreviation '{prev_token.text}'.",
                                suggestions=[f"Rewrite the phrase to use a preposition. For example, instead of '{prev_token.text}'s properties', write 'the properties of {prev_token.text}'."],
                                severity='medium'
                            ))
        return errors

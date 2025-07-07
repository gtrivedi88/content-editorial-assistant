"""
Periods Rule
Based on IBM Style Guide topic: "Periods"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class PeriodsRule(BasePunctuationRule):
    """
    Checks for incorrect use of periods, focusing on the rule to omit
    periods from within uppercase abbreviations.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'periods'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for periods within uppercase abbreviations.
        """
        errors = []
        if not nlp:
            # This rule requires tokenization and part-of-speech tagging.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # The rule triggers when a period token is found.
                if token.text == '.':
                    # --- Context-Aware Check ---
                    # To avoid false positives, we check the surrounding tokens to see
                    # if they match the pattern of an abbreviation like U.S.A.
                    if token.i > 0 and token.i < len(doc) - 1:
                        prev_token = doc[token.i - 1]
                        next_token = doc[token.i + 1]
                        
                        # Linguistic Anchor: The pattern for this error is a single uppercase
                        # letter, followed by a period, followed by another single uppercase letter.
                        is_abbreviation_pattern = (
                            prev_token.is_upper and len(prev_token.text) == 1 and
                            next_token.is_upper and len(next_token.text) == 1
                        )

                        if is_abbreviation_pattern:
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message="Avoid using periods within uppercase abbreviations.",
                                suggestions=["Remove the periods from the abbreviation (e.g., 'USA' instead of 'U.S.A.')."],
                                severity='low'
                            ))
        return errors

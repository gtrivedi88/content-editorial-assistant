"""
Prepositions Rule
Based on IBM Style Guide topic: "Prepositions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class PrepositionsRule(BaseLanguageRule):
    """
    Checks for sentences that may be overly complex due to a high number
    of prepositional phrases.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'prepositions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for an excessive number of prepositions.
        """
        errors = []
        if not nlp:
            # This rule requires Part-of-Speech tagging.
            return errors

        # Linguistic Anchor: A threshold for what constitutes "too many" prepositions.
        # This can be adjusted, but 4 is a reasonable starting point.
        PREPOSITION_THRESHOLD = 4

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # Use SpaCy's POS tagging to count the prepositions in the sentence.
            # The 'ADP' tag covers prepositions and postpositions.
            prepositions = [token for token in doc if token.pos_ == 'ADP']
            
            if len(prepositions) > PREPOSITION_THRESHOLD:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence contains a high number of prepositions, which may indicate a complex or unclear structure.",
                    suggestions=["Consider rewriting to simplify the sentence structure. For example, 'The report is a list of the status of all of the event monitors for this process' could become 'The report lists the current status of all event monitors for this process'."],
                    severity='low'
                ))
        return errors

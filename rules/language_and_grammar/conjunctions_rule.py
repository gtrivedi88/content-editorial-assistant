"""
Conjunctions Rule
Based on IBM Style Guide topic: "Conjunctions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class ConjunctionsRule(BaseLanguageRule):
    """
    Checks for misuse of certain subordinating conjunctions.
    """
    def _get_rule_type(self) -> str:
        return 'conjunctions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        
        # Linguistic Anchor: Conjunctions with specific usage rules in IBM Style.
        conjunction_checks = {
            'since': "Use 'since' only to refer to time, not as a synonym for 'because'.",
            'while': "Use 'while' only to refer to time, not as a synonym for 'although'.",
            'as': "Avoid using 'as' to mean 'because'; it can be ambiguous."
        }

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                if token.lemma_ in conjunction_checks:
                    # A simple check flags the word for review. A more advanced check
                    # would analyze the dependency parse to infer meaning.
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Potential misuse of the conjunction '{token.text}'.",
                        suggestions=[conjunction_checks[token.lemma_]],
                        severity='low'
                    ))
        return errors

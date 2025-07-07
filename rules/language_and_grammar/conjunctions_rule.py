"""
Conjunctions Rule
Based on IBM Style Guide topic: "Conjunctions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class ConjunctionsRule(BaseLanguageRule):
    """
    Checks for misuse of certain subordinating conjunctions using dependency
    parsing to understand the word's function in the sentence.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'conjunctions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for potentially ambiguous conjunctions.
        """
        errors = []
        if not nlp:
            # This rule requires dependency parsing for context.
            return errors
        
        # Linguistic Anchor: A dictionary of conjunctions with specific usage rules.
        conjunction_checks = {
            'since': "Use 'since' only to refer to time, not as a synonym for 'because'.",
            'while': "Use 'while' only to refer to time, not as a synonym for 'although' or 'though'.",
            'as': "Avoid using 'as' to mean 'because'; it can be ambiguous."
        }

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                if token.lemma_ in conjunction_checks:
                    
                    # --- Context-Aware Check ---
                    # The dependency label 'mark' identifies a subordinating conjunction.
                    # This is the context where 'as', 'since', and 'while' can be
                    # ambiguous. We ignore other uses (e.g., 'as' as a preposition)
                    # to prevent false positives.
                    if token.dep_ == 'mark':
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Potential misuse of the conjunction '{token.text}'.",
                            suggestions=[conjunction_checks[token.lemma_]],
                            severity='low'
                        ))
        return errors
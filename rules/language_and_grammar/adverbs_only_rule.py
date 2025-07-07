"""
Adverbs - only Rule
Based on IBM Style Guide topic: "Adverbs - only"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class AdverbsOnlyRule(BaseLanguageRule):
    """
    Checks for the word "only" and advises the user to review its placement
    to ensure the meaning of the sentence is clear and unambiguous.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'adverbs_only'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of the word "only".
        """
        errors = []
        if not nlp:
            # This rule requires tokenization.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # Linguistic Anchor: The target is the adverb "only".
                # Because its correct placement is semantic, we flag it for review
                # rather than attempting to auto-correct it, which prevents false positives.
                if token.lemma_ == 'only':
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="The word 'only' can be ambiguous depending on its placement.",
                        suggestions=["To ensure clarity, review the sentence and place 'only' immediately before the word or phrase it is intended to modify."],
                        severity='low'
                    ))
        return errors

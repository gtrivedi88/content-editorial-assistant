"""
Contractions Rule
Based on IBM Style Guide topic: "Contractions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class ContractionsRule(BaseLanguageRule):
    """
    Identifies contractions (e.g., "don't", "it's"). While the IBM Style
    Guide permits them, this rule flags them for review, as they may not be
    appropriate for all contexts, especially highly formal documentation.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'contractions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of contractions.
        """
        errors = []
        if not nlp:
            # This rule requires tokenization.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # Linguistic Anchor: A contraction is a token that contains an
                # apostrophe but is not the simple possessive 's.
                if "'" in token.text and token.text.lower() != "'s":
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Contraction '{token.text}' used.",
                        suggestions=["Consider spelling out the contraction (e.g., 'do not' instead of 'don't') for a more formal tone, especially in reference or legal documentation."],
                        severity='low'
                    ))
        return errors

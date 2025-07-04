"""
Contractions Rule
Based on IBM Style Guide topic: "Contractions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class ContractionsRule(BaseLanguageRule):
    """
    Identifies contractions. While IBM Style permits them, it's useful to
    be able to flag them for review in more formal contexts.
    """
    def _get_rule_type(self) -> str:
        return 'contractions'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # A simple linguistic anchor: Contractions contain an apostrophe.
                if "'" in token.text and token.text.lower() != "'s": # Exclude possessives
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Contraction '{token.text}' used.",
                        suggestions=["Consider spelling out the contraction (e.g., 'do not' instead of 'don't') for a more formal tone."],
                        severity='low'
                    ))
        return errors

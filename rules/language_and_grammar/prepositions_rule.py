"""
Prepositions Rule
Based on IBM Style Guide topic: "Prepositions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class PrepositionsRule(BaseLanguageRule):
    """
    Checks for potentially cluttered sentences with too many prepositions.
    """
    def _get_rule_type(self) -> str:
        return 'prepositions'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            # Linguistic Anchor: The Part-of-Speech tag for prepositions is ADP.
            prepositions = [token for token in doc if token.pos_ == 'ADP']
            
            # Heuristic: A sentence with a high number of prepositions might be overly complex.
            if len(prepositions) > 4:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence contains a high number of prepositions, which may indicate a complex or unclear structure.",
                    suggestions=["Consider rewriting to simplify the sentence structure."],
                    severity='low'
                ))
        return errors

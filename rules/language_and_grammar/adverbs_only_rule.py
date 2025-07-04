"""
Adverbs - only Rule
Based on IBM Style Guide topic: "Adverbs - only"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class AdverbsOnlyRule(BaseLanguageRule):
    """
    Checks for potentially misplaced "only" adverbs. The placement of "only"
    can significantly change the meaning of a sentence.
    """
    def _get_rule_type(self) -> str:
        return 'adverbs_only'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                if token.lemma_ == 'only':
                    # This is a complex semantic issue. The best approach for a style
                    # checker is to flag it for human review.
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="The word 'only' can be ambiguous. Please review its placement.",
                        suggestions=["Ensure 'only' is placed immediately before the word or phrase it is intended to modify."],
                        severity='low'
                    ))
        return errors

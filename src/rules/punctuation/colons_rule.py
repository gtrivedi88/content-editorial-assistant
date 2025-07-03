"""
Colons Rule
Based on IBM Style Guide topic: "Colons"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class ColonsRule(BasePunctuationRule):
    """
    Checks for incorrect colon usage.
    """
    def _get_rule_type(self) -> str:
        return 'colons'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                if token.text == ':':
                    if token.i > 0 and doc[token.i - 1].pos_ == "VERB":
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message="Incorrect colon usage: A colon should not directly follow a verb.",
                            suggestions=["Remove the colon.", "Rewrite to introduce the list with a complete clause."],
                            severity='medium'
                        ))
        return errors

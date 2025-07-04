"""
Slashes Rule
Based on IBM Style Guide topic: "Slashes"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class SlashesRule(BasePunctuationRule):
    """
    Checks for the ambiguous use of slashes to mean "and/or".
    """
    def _get_rule_type(self) -> str:
        return 'slashes'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                if token.text == '/' and token.i > 0 and token.i < len(doc) - 1:
                    # Linguistic Anchor: Check if the slash is between two nouns or adjectives,
                    # a common pattern for "and/or" usage.
                    if doc[token.i - 1].pos_ in ["NOUN", "ADJ", "PROPN"] and doc[token.i + 1].pos_ in ["NOUN", "ADJ", "PROPN"]:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message="Avoid using a slash (/) to mean 'and/or'.",
                            suggestions=["Clarify the meaning by using 'and', 'or', or by rewriting the sentence."],
                            severity='medium'
                        ))
        return errors

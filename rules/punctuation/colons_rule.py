"""
Colons Rule
Based on IBM Style Guide topic: "Colons"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class ColonsRule(BasePunctuationRule):
    """
    Checks for incorrect colon usage using dependency parsing to understand
    the colon's grammatical function.
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
                    # Rule: Do not use a colon to separate a verb from its objects.
                    # A more robust check using dependency parsing.
                    # If the colon's head is a verb and the colon has a direct object as a child,
                    # it's likely an incorrect usage.
                    if token.head.pos_ == "VERB":
                        children_deps = {child.dep_ for child in token.children}
                        if 'dobj' in children_deps or 'pobj' in children_deps:
                             errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message="Incorrect colon usage: A colon should not separate a verb from its objects.",
                                suggestions=["Remove the colon.", "Rewrite the sentence to introduce the list with a complete clause like '...includes the following items:'."],
                                severity='medium'
                            ))
        return errors

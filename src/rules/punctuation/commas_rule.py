"""
Commas Rule
Based on IBM Style Guide topic: "Commas"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class CommasRule(BasePunctuationRule):
    """
    Checks for the required use of the serial (Oxford) comma.
    """
    def _get_rule_type(self) -> str:
        return 'commas'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        
        conjunctions = {'and', 'or'}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                if token.lemma_ in conjunctions and token.dep_ == 'cc':
                    head = token.head
                    siblings = [child for child in head.children if child.dep_ == 'conj']
                    
                    if len(siblings) >= 1:
                        prev_token = doc[token.i - 1]
                        if prev_token.pos_ in ["NOUN", "ADJ", "PROPN"] and doc[token.i - 2].text != ',':
                             errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message="Missing serial (Oxford) comma before conjunction in a list.",
                                suggestions=[f"Add a comma before '{token.text}'."],
                                severity='high'
                            ))
        return errors

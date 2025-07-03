"""
Parentheses Rule
Based on IBM Style Guide topic: "Parentheses"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class ParenthesesRule(BasePunctuationRule):
    """
    Checks for incorrect punctuation within or around parentheses.
    """
    def _get_rule_type(self) -> str:
        return 'parentheses'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                if token.text == ')':
                    # Rule: Do not place a period inside parentheses if the parenthetical
                    # text is not a complete sentence.
                    if token.i > 1 and doc[token.i - 1].text == '.':
                        # Check if the text inside parens is a full sentence
                        is_full_sentence = False
                        for j in range(token.i - 2, 0, -1):
                            if doc[j].text == '(':
                                if doc[j+1].is_sent_start or doc[j+1].is_title:
                                    is_full_sentence = True
                                break
                        if not is_full_sentence:
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message="Incorrect punctuation: A period should be outside the parentheses for a fragment.",
                                suggestions=["Move the period to after the closing parenthesis."],
                                severity='low'
                            ))
        return errors

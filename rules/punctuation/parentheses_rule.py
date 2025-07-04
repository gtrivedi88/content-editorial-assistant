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
                        # More robust check for a full sentence inside the parentheses
                        is_full_sentence = False
                        paren_start_index = -1
                        for j in range(token.i - 2, -1, -1):
                            if doc[j].text == '(':
                                paren_start_index = j
                                break
                        
                        if paren_start_index != -1:
                            # Check if the content inside parens has a subject and a root verb
                            has_subject = any(t.dep_ in ('nsubj', 'nsubjpass') for t in doc[paren_start_index+1:token.i-1])
                            has_root = any(t.dep_ == 'ROOT' for t in doc[paren_start_index+1:token.i-1])
                            if has_subject and has_root:
                                is_full_sentence = True

                        if not is_full_sentence:
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message="Incorrect punctuation: A period should be outside the parentheses for a fragment.",
                                suggestions=["Move the period to after the closing parenthesis."],
                                severity='low'
                            ))
        return errors

"""
Parentheses Rule
Based on IBM Style Guide topic: "Parentheses"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class ParenthesesRule(BasePunctuationRule):
    """
    Checks for incorrect punctuation within or around parentheses, using
    dependency parsing to determine if the parenthetical content is a
    complete sentence.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'parentheses'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for incorrect punctuation with parentheses.
        """
        errors = []
        if not nlp:
            # This rule requires dependency parsing, so NLP is essential.
            return errors
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # The rule triggers when a closing parenthesis is found.
                if token.text == ')':
                    # Check for the common error: a period placed inside the
                    # parenthesis when the content is just a fragment.
                    if token.i > 1 and doc[token.i - 1].text == '.':
                        
                        # --- Context-Aware Check ---
                        # To avoid a false positive, we must determine if the text inside
                        # the parentheses is a complete sentence.
                        is_full_sentence = False
                        paren_start_index = -1
                        # Look backwards from the closing parenthesis to find the opening one.
                        for j in range(token.i - 2, -1, -1):
                            if doc[j].text == '(':
                                paren_start_index = j
                                break
                        
                        if paren_start_index != -1:
                            # Linguistic Anchor: A complete sentence has a subject and a root verb.
                            # We analyze the dependency parse of the tokens inside the parentheses.
                            paren_content = doc[paren_start_index + 1 : token.i - 1]
                            has_subject = any(t.dep_ in ('nsubj', 'nsubjpass') for t in paren_content)
                            has_root_verb = any(t.dep_ == 'ROOT' for t in paren_content)
                            
                            if has_subject and has_root_verb:
                                is_full_sentence = True

                        # If the content is NOT a full sentence, it's an error.
                        if not is_full_sentence:
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message="Incorrect punctuation: A period should be placed outside the parentheses for a fragment.",
                                suggestions=["Move the period to after the closing parenthesis."],
                                severity='low'
                            ))
        return errors
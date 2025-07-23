"""
Parentheses Rule
Based on IBM Style Guide topic: "Parentheses"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ParenthesesRule(BasePunctuationRule):
    """
    Checks for incorrect punctuation within or around parentheses, using
    dependency parsing to determine if the parenthetical content is a
    complete sentence.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'punctuation_parentheses'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for incorrect punctuation with parentheses.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.text == ')':
                    # Check for the common error: a period inside the parenthesis of a fragment.
                    if token.i > sent.start + 1 and sent.doc[token.i - 1].text == '.':
                        
                        is_full_sentence = False
                        paren_start_index = -1
                        for j in range(token.i - 2, sent.start -1, -1):
                            if sent.doc[j].text == '(':
                                paren_start_index = j
                                break
                        
                        if paren_start_index != -1:
                            # Linguistic Anchor: A complete sentence has a subject and a root verb.
                            paren_content = sent.doc[paren_start_index + 1 : token.i - 1]
                            has_subject = any(t.dep_ in ('nsubj', 'nsubjpass') for t in paren_content)
                            has_root_verb = any(t.dep_ == 'ROOT' for t in paren_content)
                            
                            if has_subject and has_root_verb:
                                is_full_sentence = True

                        if not is_full_sentence:
                            flagged_token = sent.doc[token.i - 1]
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message="Incorrect punctuation: A period should be placed outside the parentheses for a fragment.",
                                suggestions=["Move the period to after the closing parenthesis."],
                                severity='low',
                                span=(flagged_token.idx, flagged_token.idx + len(flagged_token.text)),
                                flagged_text=flagged_token.text
                            ))
        return errors

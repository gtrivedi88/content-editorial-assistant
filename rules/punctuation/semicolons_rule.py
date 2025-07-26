"""
Semicolons Rule (Accurate)
Based on IBM Style Guide topic: "Semicolons"
"""
from typing import List, Dict, Any
from ..base_rule import BaseRule # Assuming a base_rule.py in the parent 'rules' directory

class SemicolonsRule(BaseRule):
    """
    Checks for the use of semicolons and advises against them in technical writing.
    """
    def _get_rule_type(self) -> str:
        return 'semicolons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        
        for i, sent_text in enumerate(sentences):
            if ';' in sent_text:
                errors.append(self._create_error(
                    sentence=sent_text,
                    sentence_index=i,
                    message="Avoid semicolons in technical writing to improve clarity.",
                    suggestions=["Consider rewriting the sentence as two separate, shorter sentences."],
                    severity='low'
                ))
        return errors

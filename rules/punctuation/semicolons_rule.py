"""
Semicolons Rule (Accurate)
Based on IBM Style Guide topic: "Semicolons"
"""
from typing import List, Dict, Any
from ..base_rule import BaseRule

class SemicolonsRule(BaseRule):
    """
    Checks for the use of semicolons and advises against them in technical writing.
    """
    def _get_rule_type(self) -> str:
        return 'semicolons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        
        for i, sent_text in enumerate(sentences):
            # PRIORITY 1 FIX: This rule is simple and accurate. It checks if a semicolon
            # character is present in the sentence text. If it's not there, the rule
            # does nothing, completely eliminating the false positive.
            if ';' in sent_text:
                errors.append(self._create_error(
                    sentence=sent_text,
                    sentence_index=i,
                    message="Avoid semicolons in technical writing to improve clarity.",
                    suggestions=["Consider rewriting the sentence as two separate, shorter sentences."],
                    severity='low'
                ))
        return errors

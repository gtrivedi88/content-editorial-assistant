"""
Semicolons Rule
Based on IBM Style Guide topic: "Semicolons"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class SemicolonsRule(BasePunctuationRule):
    """
    Checks for semicolons, which are discouraged in technical writing by the
    IBM Style Guide in favor of shorter, clearer sentences.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'semicolons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of semicolons.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        # The IBM Style Guide advises against semicolons for clarity.
        for i, sent in enumerate(doc.sents):
            for match in re.finditer(r';', sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Avoid semicolons in technical writing to improve clarity.",
                    suggestions=["Consider rewriting the sentence as two separate, shorter sentences."],
                    severity='low',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
        return errors

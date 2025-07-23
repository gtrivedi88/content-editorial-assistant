"""
Ellipses Rule
Based on IBM Style Guide topic: "Ellipses"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class EllipsesRule(BasePunctuationRule):
    """
    Checks for the use of ellipses, which should be avoided in general text
    according to the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'punctuation_ellipses'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of ellipses.
        """
        errors = []
        if not nlp:
            return errors
        
        doc = nlp(text)
        # The IBM Style Guide is direct: "Avoid using ellipses in text in most cases."
        # A simple and robust check for the character sequence is sufficient.
        for i, sent in enumerate(doc.sents):
            for match in re.finditer(r'\.\.\.', sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Avoid using ellipses (...) in technical writing.",
                    suggestions=["If text is omitted from a quote, this may be acceptable. Otherwise, if used for a pause, rewrite for a more formal and direct tone."],
                    severity='low',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
        return errors

"""
Exclamation Points Rule
Based on IBM Style Guide topic: "Exclamation points"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ExclamationPointsRule(BasePunctuationRule):
    """
    Checks for exclamation points, which should be avoided in technical writing
    according to the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'exclamation_points'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of exclamation points.
        """
        errors = []
        if not nlp:
            return errors
            
        doc = nlp(text)
        # For technical documentation, their presence is almost always a style violation.
        for i, sent in enumerate(doc.sents):
            for match in re.finditer(r'!', sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Avoid exclamation points in technical writing to maintain a professional tone.",
                    suggestions=["Replace the exclamation point with a period."],
                    severity='low',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
        return errors

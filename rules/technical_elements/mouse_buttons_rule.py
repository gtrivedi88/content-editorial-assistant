"""
Mouse Buttons Rule
Based on IBM Style Guide topic: "Mouse buttons"
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class MouseButtonsRule(BaseTechnicalRule):
    """
    Checks for the incorrect use of the preposition "on" with mouse actions.
    """
    def _get_rule_type(self) -> str:
        return 'technical_mouse_buttons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text to find phrases like "click on".
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        for i, sent in enumerate(doc.sents):
            for match in re.finditer(r'\bclick on\b', sent.text, re.IGNORECASE):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Do not use the preposition 'on' with mouse actions.",
                    suggestions=["Remove 'on' after 'click'. For example, write 'Click Save' instead of 'Click on Save'."],
                    severity='high',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))
        return errors

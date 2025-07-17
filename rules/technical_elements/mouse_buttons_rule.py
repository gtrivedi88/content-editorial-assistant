"""
Mouse Buttons Rule
Based on IBM Style Guide topic: "Mouse buttons"
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule

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
        for i, sentence in enumerate(sentences):
            # Linguistic Anchor: Find the specific phrase "click on".
            if "click on" in sentence.lower():
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Do not use the preposition 'on' with mouse actions.",
                    suggestions=["Remove 'on' after 'click'. For example, write 'Click Save' instead of 'Click on Save'."],
                    severity='high'
                ))
        return errors

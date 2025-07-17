"""
Keyboard Keys Rule
Based on IBM Style Guide topic: "Keyboard keys"
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
import re

class KeyboardKeysRule(BaseTechnicalRule):
    """
    Checks for correct formatting of keyboard keys and key combinations.
    """
    def _get_rule_type(self) -> str:
        return 'technical_keyboard_keys'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for keyboard key formatting errors.
        """
        errors = []
        # Regex to find key combinations not separated by a plus sign
        key_combo_pattern = re.compile(r'\b(Ctrl|Alt|Shift)\s+[A-Za-z0-9]+\b')
        key_names = {"enter", "shift", "alt", "ctrl", "esc", "tab", "return", "backspace"}

        for i, sentence in enumerate(sentences):
            if key_combo_pattern.search(sentence):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Use a plus sign (+) with no spaces to separate key names in a combination.",
                    suggestions=["For example, write 'Ctrl+Alt+Del' instead of 'Ctrl Alt Del'."],
                    severity='medium'
                ))

            # Check for lowercase key names
            for word in sentence.split():
                if word.lower().strip(".,") in key_names and not word[0].isupper():
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Keyboard key name '{word}' should be capitalized.",
                        suggestions=[f"Use initial capitals for key names, e.g., '{word.capitalize()}'."],
                        severity='medium'
                    ))
        return errors

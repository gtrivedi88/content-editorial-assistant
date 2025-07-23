"""
Keyboard Keys Rule
Based on IBM Style Guide topic: "Keyboard keys"
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

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
        if not nlp:
            return errors
        doc = nlp(text)

        key_combo_pattern = re.compile(r'\b(Ctrl|Alt|Shift)\s+[A-Za-z0-9]+\b')
        key_names = {"enter", "shift", "alt", "ctrl", "esc", "tab", "return", "backspace"}

        for i, sent in enumerate(doc.sents):
            for match in key_combo_pattern.finditer(sent.text):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Use a plus sign (+) with no spaces to separate key names in a combination.",
                    suggestions=["For example, write 'Ctrl+Alt+Del' instead of 'Ctrl Alt Del'."],
                    severity='medium',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))

            # Check for lowercase key names
            for token in sent:
                if token.lemma_.lower() in key_names and token.is_lower:
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Keyboard key name '{token.text}' should be capitalized.",
                        suggestions=[f"Use initial capitals for key names, e.g., '{token.text.capitalize()}'."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors

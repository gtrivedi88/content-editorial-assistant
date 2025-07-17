"""
UI Elements Rule
Based on IBM Style Guide topic: "UI elements"
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule

class UIElementsRule(BaseTechnicalRule):
    """
    Checks for correct verb usage with specific UI elements.
    """
    def _get_rule_type(self) -> str:
        return 'technical_ui_elements'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text to ensure correct verbs are used for UI elements.
        """
        errors = []
        if not nlp:
            return errors

        # Linguistic Anchor: Map of UI element nouns to their allowed verbs.
        ui_verb_map = {
            "checkbox": {"select", "clear"},
            "radio button": {"select"},
            "field": {"type", "enter", "specify"},
            "list": {"select"},
            "menu": {"click"},
            "button": {"click"},
            "icon": {"click"}
        }

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                ui_element = None
                if token.lemma_ in ui_verb_map:
                    ui_element = token.lemma_
                elif f"{token.lemma_} {doc[token.i + 1].lemma_}" in ui_verb_map if token.i + 1 < len(doc) else False:
                    ui_element = f"{token.lemma_} {doc[token.i + 1].lemma_}"

                if ui_element:
                    # Find the verb acting on this UI element
                    verb = token.head
                    if verb.pos_ == 'VERB' and verb.lemma_ not in ui_verb_map[ui_element]:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Incorrect verb '{verb.text}' used for '{ui_element}'.",
                            suggestions=[f"Use one of the approved verbs for '{ui_element}': {', '.join(ui_verb_map[ui_element])}."],
                            severity='medium'
                        ))
        return errors

"""
Anthropomorphism Rule
Based on IBM Style Guide topic: "Anthropomorphism"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class AnthropomorphismRule(BaseLanguageRule):
    """
    Checks for instances where inanimate objects are given human characteristics.
    """
    def _get_rule_type(self) -> str:
        return 'anthropomorphism'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        # Linguistic Anchor: Verbs that often imply human thought or action.
        human_verbs = {'thinks', 'knows', 'believes', 'wants', 'sees', 'asks', 'tells', 'allows', 'lets', 'permits'}
        # Linguistic Anchor: Nouns representing inanimate technical objects.
        inanimate_subjects = {'system', 'application', 'program', 'module', 'server', 'window', 'interface'}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # Check if a human-like verb has an inanimate subject.
                if token.lemma_ in human_verbs:
                    subject = [child for child in token.children if child.dep_ == 'nsubj']
                    if subject and subject[0].lemma_ in inanimate_subjects:
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Anthropomorphism: The {subject[0].text} '{token.text}' like a person.",
                            suggestions=["Rewrite the sentence to focus on the user's action (e.g., 'You can use the system to...')."],
                            severity='low'
                        ))
        return errors

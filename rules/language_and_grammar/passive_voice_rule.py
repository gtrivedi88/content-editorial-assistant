"""
Passive Voice Rule
Based on IBM Style Guide topic: "Verbs: Voice"
"""
from typing import List, Dict, Any
# Fix relative import issue by using absolute import
try:
    from .base_language_rule import BaseLanguageRule
except ImportError:
    try:
        from rules.language_and_grammar.base_language_rule import BaseLanguageRule
    except ImportError:
        from base_language_rule import BaseLanguageRule

class PassiveVoiceRule(BaseLanguageRule):
    """
    Checks for sentences written in the passive voice and suggests rewriting
    them in the active voice for clarity and directness.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'passive_voice'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for passive voice constructions.
        """
        errors = []
        if not nlp:
            # This rule requires dependency parsing, so NLP is essential.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # Linguistic Anchor: The presence of a passive nominal subject ('nsubjpass')
            # or a passive auxiliary ('auxpass') are strong indicators of passive voice.
            has_passive_subject = any(token.dep_ == 'nsubjpass' for token in doc)
            has_passive_aux = any(token.dep_ == 'auxpass' for token in doc)

            if has_passive_subject or has_passive_aux:
                # Further checks could be added here to ignore acceptable passive voice,
                # such as when the actor is unknown or unimportant (e.g., "The file was saved.").
                # For a style checker, flagging all instances for review is a safe default.
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence may be in the passive voice.",
                    suggestions=["Consider rewriting in the active voice to be more direct. For example, change 'The button was clicked by the user' to 'The user clicked the button'."],
                    severity='medium'
                ))
        return errors

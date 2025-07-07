"""
Verbs Rule (Corrected for False Positives)
Based on IBM Style Guide topic: "Verbs"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class VerbsRule(BaseLanguageRule):
    """
    Checks for verb-related style issues. This version has been corrected
    to reduce false positives in the tense-checking logic.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'verbs'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for passive voice and incorrect tense.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # --- Rule 1: Passive Voice Check (Robust) ---
            # This logic is accurate and remains unchanged.
            has_passive_subject = any(token.dep_ == 'nsubjpass' for token in doc)
            has_passive_aux = any(token.dep_ == 'auxpass' for token in doc)

            if has_passive_subject and has_passive_aux:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence may be in the passive voice.",
                    suggestions=["Consider rewriting in the active voice to be more direct. For example, change 'The button was clicked by the user' to 'The user clicked the button'."],
                    severity='medium'
                ))

            # --- Rule 2: Tense Check (Corrected Logic) ---
            # This check now focuses only on the main verb of the sentence to avoid
            # incorrectly flagging past participles in present-tense constructions.
            root_verb = None
            for token in doc:
                # Find the root of the dependency tree, ensure it's a verb
                if token.dep_ == 'ROOT' and token.pos_ == 'VERB':
                    root_verb = token
                    break
            
            has_past_tense = False
            if root_verb and root_verb.morph.get("Tense") == ["Past"]:
                has_past_tense = True

            has_future_tense = any(token.lemma_ == "will" for token in doc)
            
            if has_past_tense or has_future_tense:
                 errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence may not be in the preferred present tense.",
                    suggestions=["Use present tense to describe product behavior and instructions (e.g., 'The system processes data' instead of 'The system will process data')."],
                    severity='low'
                ))
        return errors

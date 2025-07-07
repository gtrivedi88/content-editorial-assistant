"""
Verbs Rule
Based on IBM Style Guide topic: "Verbs"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class VerbsRule(BaseLanguageRule):
    """
    Checks for verb-related style issues, specifically focusing on the
    use of passive voice and non-present tense, as per the IBM Style Guide.
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
            # This rule requires dependency parsing and morphology.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # --- Rule 1: Passive Voice Check (Robust) ---
            # Linguistic Anchor: A true passive construction requires both a passive
            # subject ('nsubjpass') and a passive auxiliary verb ('auxpass').
            # This combination is a highly reliable indicator and avoids flagging
            # simple linking verbs (e.g., "the system is ready").
            has_passive_subject = any(token.dep_ == 'nsubjpass' for token in doc)
            has_passive_aux = any(token.dep_ == 'auxpass' for token in doc)

            if has_passive_subject and has_passive_aux:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence may be in the passive voice.",
                    suggestions=["Consider rewriting in the active voice to be more direct and clear. For example, change 'The button was clicked by the user' to 'The user clicked the button'."],
                    severity='medium'
                ))

            # --- Rule 2: Tense Check (General Guideline) ---
            # The style guide prefers present tense for instructions and descriptions.
            # This check flags past or future tense for review.
            has_past_tense = any(token.morph.get("Tense") == ["Past"] for token in doc)
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

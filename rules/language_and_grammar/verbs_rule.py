"""
Verbs Rule (Enhanced)
Based on IBM Style Guide topic: "Verbs"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class VerbsRule(BaseLanguageRule):
    """
    Checks for verb-related style issues. This enhanced version provides
    a more accurate check for passive voice to reduce false positives.
    The check for tense remains as a general guideline.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'verbs'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for passive voice and non-present tense.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # --- Passive Voice Check (More Robust) ---
            # Linguistic Anchor: A true passive construction requires a passive
            # subject ('nsubjpass') AND a passive auxiliary verb ('auxpass').
            # This prevents flagging simple linking verbs like "is".
            has_passive_subject = any(token.dep_ == 'nsubjpass' for token in doc)
            has_passive_aux = any(token.dep_ == 'auxpass' for token in doc)

            if has_passive_subject and has_passive_aux:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence may be in passive voice.",
                    suggestions=["Consider rewriting in active voice for clarity and directness."],
                    severity='medium'
                ))

            # --- Tense Check (General Guideline) ---
            # This check remains a heuristic, as determining the "correct" tense
            # is highly contextual.
            has_past_tense = any(token.morph.get("Tense") == ["Past"] for token in doc)
            has_future_tense = any(token.lemma_ == "will" for token in doc)
            
            # Avoid flagging past tense in common, acceptable phrases.
            if has_past_tense and "was added" not in sentence.lower() and "was created" not in sentence.lower():
                 errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence may not be in the preferred present tense.",
                    suggestions=["Use present tense to describe product behavior and instructions."],
                    severity='low'
                ))
        return errors

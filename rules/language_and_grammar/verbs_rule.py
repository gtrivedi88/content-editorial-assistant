"""
Verbs Rule
Based on IBM Style Guide topic: "Verbs"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class VerbsRule(BaseLanguageRule):
    """
    Checks for verb-related style issues, such as passive voice and incorrect tense.
    """
    def _get_rule_type(self) -> str:
        return 'verbs'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # Check for passive voice
            is_passive = any(token.dep_ == 'nsubjpass' for token in doc)
            if is_passive:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence may be in passive voice.",
                    suggestions=["Consider rewriting in active voice for clarity and directness."],
                    severity='medium'
                ))

            # Check for incorrect tense (prefer present)
            has_past_tense = any(token.morph.get("Tense") == ["Past"] for token in doc)
            has_future_tense = any(token.lemma_ == "will" for token in doc)
            if has_past_tense or has_future_tense:
                 errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Sentence may not be in the preferred present tense.",
                    suggestions=["Use present tense to describe product behavior and instructions."],
                    severity='low'
                ))
        return errors

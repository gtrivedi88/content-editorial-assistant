"""
Pronouns Rule (Updated)
Based on IBM Style Guide topic: "Pronouns"

This rule has been updated to focus only on gender-neutrality and
clarity, to avoid overlapping with the more specific second_person_rule.py.
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class PronounsRule(BaseLanguageRule):
    """
    Checks for pronoun usage, focusing on flagging ambiguous or
    gendered language to promote inclusivity.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'pronouns'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for gender-specific pronouns.
        """
        errors = []
        if not nlp:
            return errors
        
        # Linguistic Anchor: This list now only contains gendered pronouns.
        # The check for first-person pronouns (we, our) has been removed
        # to prevent redundant errors with second_person_rule.py.
        gendered_pronouns = {'he', 'him', 'his', 'she', 'her'}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # Flag gendered pronouns, suggest gender-neutral alternatives.
                if token.lemma_.lower() in gendered_pronouns:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Gender-specific pronoun '{token.text}' used.",
                        suggestions=["Use gender-neutral language. Consider rewriting with 'they' or addressing the user directly with 'you'."],
                        severity='medium'
                    ))
        return errors
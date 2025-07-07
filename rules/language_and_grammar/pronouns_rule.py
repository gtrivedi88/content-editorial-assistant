"""
Pronouns Rule
Based on IBM Style Guide topic: "Pronouns"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class PronounsRule(BaseLanguageRule):
    """
    Checks for pronoun usage, focusing on flagging gender-specific language
    to promote inclusivity, as per the IBM Style Guide. This rule intentionally
    does not check for first-person voice to avoid redundant errors with the
    more specific second_person_rule.py.
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
            # This rule requires tokenization and lemmatization.
            return errors
        
        # Linguistic Anchor: A set of gender-specific pronoun lemmas.
        # This list intentionally excludes first-person pronouns.
        gendered_pronouns = {'he', 'him', 'his', 'she', 'her'}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # Flag gendered pronouns and suggest gender-neutral alternatives.
                if token.lemma_.lower() in gendered_pronouns:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Gender-specific pronoun '{token.text}' used.",
                        suggestions=["Use gender-neutral language. Consider rewriting with 'they' or addressing the user directly with 'you'."],
                        severity='medium'
                    ))
        return errors

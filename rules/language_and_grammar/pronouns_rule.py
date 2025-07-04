"""
Pronouns Rule
Based on IBM Style Guide topic: "Pronouns"
This rule is a more generalized version of the second_person_rule,
focusing on all pronoun-related style issues.
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class PronounsRule(BaseLanguageRule):
    """
    Checks for pronoun usage, encouraging second person and flagging
    ambiguous or gendered language.
    """
    def _get_rule_type(self) -> str:
        return 'pronouns'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        
        # Linguistic Anchors
        first_person = {'i', 'we', 'us', 'me', 'my', 'our'}
        gendered_pronouns = {'he', 'him', 'his', 'she', 'her'}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # Flag first-person usage
                if token.lemma_ in first_person:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"First-person pronoun '{token.text}' used.",
                        suggestions=["Rewrite in the second person ('you') to address the user directly."],
                        severity='high'
                    ))
                
                # Flag gendered pronouns, suggest gender-neutral alternatives
                elif token.lemma_ in gendered_pronouns:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Gender-specific pronoun '{token.text}' used.",
                        suggestions=["Use gender-neutral language. Consider rewriting with 'they' or addressing the user directly with 'you'."],
                        severity='medium'
                    ))
        return errors
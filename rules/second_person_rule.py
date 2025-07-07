"""
Second Person Rule (Context-Aware)
Based on IBM Style Guide topic: "Verbs: Person"
"""
from typing import List, Dict, Any
from .language_and_grammar.base_language_rule import BaseLanguageRule

class SecondPersonRule(BaseLanguageRule):
    """
    Checks for the use of first-person voice ("we", "our") and third-person
    substitutes ("the user"), suggesting the second person ("you"). This
    enhanced version ignores common compound nouns to prevent false positives.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'second_person'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for first-person pronouns and third-person substitutes.
        """
        errors = []
        if not nlp:
            return errors
        
        first_person_pronouns = {'i', 'we', 'us', 'me', 'my', 'our'}
        user_substitutes = {'user', 'administrator', 'developer'}
        # Linguistic Anchor: Words that form common compound nouns with "user".
        compound_noun_followers = {'interface', 'id', 'account', 'profile', 'name'}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for j, token in enumerate(doc):
                # Check for first-person pronouns
                if token.lemma_.lower() in first_person_pronouns:
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
                        message=f"Consider using 'you' instead of '{token.text}' to directly address the user.",
                        suggestions=["Rewrite in the second person ('you') to focus on the user's actions."],
                        severity='high'
                    ))
                # Check for third-person substitutes, but ignore them if they are part of a compound noun.
                elif token.lemma_ in user_substitutes:
                    is_compound = False
                    if j < len(doc) - 1:
                        next_token = doc[j + 1]
                        if next_token.lemma_.lower() in compound_noun_followers:
                            is_compound = True
                    
                    if not is_compound:
                        errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message=f"Consider using 'you' instead of '{token.text}' to directly address the user.",
                            suggestions=["Address the user directly with 'you' for a more engaging tone."],
                            severity='medium'
                        ))
        return errors

"""
Articles Rule (Enhanced)
Based on IBM Style Guide topic: "Articles"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class ArticlesRule(BaseLanguageRule):
    """
    Checks for common article errors, such as using 'a' vs 'an'. This
    enhanced version uses a more reliable method to check for vowel sounds
    and handles common exceptions.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'articles'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for incorrect 'a'/'an' usage.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for j, token in enumerate(doc):
                if token.lower_ in ['a', 'an'] and j < len(doc) - 1:
                    next_token = doc[j + 1]
                    
                    # Use a more robust check for vowel sounds that handles exceptions.
                    starts_with_vowel_sound = self._starts_with_vowel_sound(next_token.text)

                    if token.lower_ == 'a' and starts_with_vowel_sound:
                        errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message=f"Incorrect article usage: Use 'an' before a vowel sound.",
                            suggestions=[f"Change 'a {next_token.text}' to 'an {next_token.text}'."],
                            severity='medium'
                        ))
                    elif token.lower_ == 'an' and not starts_with_vowel_sound:
                         errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message=f"Incorrect article usage: Use 'a' before a consonant sound.",
                            suggestions=[f"Change 'an {next_token.text}' to 'a {next_token.text}'."],
                            severity='medium'
                        ))
        return errors

    def _starts_with_vowel_sound(self, word: str) -> bool:
        """
        A more robust check for whether a word starts with a vowel sound.
        Includes common exceptions.
        """
        word_lower = word.lower()
        
        # Linguistic Anchor: Exceptions where 'u' makes a consonant 'y' sound.
        if word_lower.startswith(('user', 'unit', 'one', 'uniform')):
            return False
            
        # Linguistic Anchor: Exceptions where a silent 'h' makes a vowel sound.
        if word_lower.startswith(('hour', 'honest', 'honor')):
            return True

        # General rule for vowels.
        return word_lower[0] in 'aeiou'

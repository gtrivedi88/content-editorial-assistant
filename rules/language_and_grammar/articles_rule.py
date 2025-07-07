"""
Articles Rule (Enhanced)
Based on IBM Style Guide topic: "Articles"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class ArticlesRule(BaseLanguageRule):
    """
    Checks for common article errors, such as incorrect 'a' vs 'an' usage
    and potentially missing articles before singular countable nouns.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'articles'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for incorrect or missing articles.
        """
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for j, token in enumerate(doc):
                # --- Rule 1: Check for 'a' vs 'an' ---
                if token.lower_ in ['a', 'an'] and j < len(doc) - 1:
                    next_token = doc[j + 1]
                    # Use a helper with linguistic anchors to check for vowel sounds.
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
                
                # --- Rule 2: Check for potentially missing articles ---
                # This is a heuristic and should be low severity to avoid false positives.
                if self._is_missing_article_candidate(token):
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
                        message=f"Potentially missing article before the noun '{token.text}'.",
                        suggestions=["Singular countable nouns usually require an article (a/an/the). Please review."],
                        severity='low'
                    ))

        return errors

    def _starts_with_vowel_sound(self, word: str) -> bool:
        """
        A more robust check for whether a word starts with a vowel sound.
        It uses linguistic anchors to handle common exceptions.
        """
        word_lower = word.lower()
        
        # Linguistic Anchor: Exceptions where 'u' makes a consonant 'y' sound.
        if word_lower.startswith(('user', 'unit', 'one', 'uniform', 'utility', 'unique')):
            return False
            
        # Linguistic Anchor: Exceptions where a silent 'h' makes a vowel sound.
        if word_lower.startswith(('hour', 'honest', 'honor', 'heir')):
            return True

        # General rule for vowels.
        return word_lower[0] in 'aeiou'

    def _is_missing_article_candidate(self, token) -> bool:
        """
        Uses dependency parsing to check if a singular countable noun might
        be missing a determiner (like 'a', 'an', or 'the').
        """
        # Linguistic Anchor: We are looking for singular, common nouns.
        if token.pos_ == 'NOUN' and token.morph.get("Number") == ["Sing"]:
            # We ignore proper nouns as they often don't need articles.
            if token.tag_ == 'NN':
                # Check the dependency parse. If the noun has no determiner ('det')
                # or possessive ('poss') child, it might be missing an article.
                has_determiner = any(child.dep_ in ('det', 'poss') for child in token.children)
                if not has_determiner:
                    # This is a strong candidate for a missing article.
                    return True
        return False

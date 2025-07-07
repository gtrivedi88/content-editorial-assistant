"""
Articles Rule (Final Corrected Version)
Based on IBM Style Guide topic: "Articles"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class ArticlesRule(BaseLanguageRule):
    """
    Checks for common article errors. This version has been corrected to
    eliminate false positives, especially those caused by incorrect parsing
    of ungrammatical source text.
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
                    starts_with_vowel_sound = self._starts_with_vowel_sound(next_token.text)

                    if token.lower_ == 'a' and starts_with_vowel_sound:
                        errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message=f"Incorrect article usage: Use 'an' before '{next_token.text}'.",
                            suggestions=[f"Change 'a {next_token.text}' to 'an {next_token.text}'."],
                            severity='medium'
                        ))
                    elif token.lower_ == 'an' and not starts_with_vowel_sound:
                         errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message=f"Incorrect article usage: Use 'a' before '{next_token.text}'.",
                            suggestions=[f"Change 'an {next_token.text}' to 'a {next_token.text}'."],
                            severity='medium'
                        ))
                
                # --- Rule 2: Check for potentially missing articles (Final Logic) ---
                if self._is_missing_article_candidate(token, doc):
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
                        message=f"Potentially missing article before the noun '{token.text}'.",
                        suggestions=["Singular countable nouns acting as the main subject or object often require an article (a/an/the). Please review."],
                        severity='low'
                    ))

        return errors

    def _starts_with_vowel_sound(self, word: str) -> bool:
        """
        A robust check for whether a word starts with a vowel sound.
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

    def _is_missing_article_candidate(self, token, doc) -> bool:
        """
        A highly conservative check for missing articles. This function is designed
        to be defensive against NLP parsing errors on ungrammatical text to
        prevent false positives.
        """
        # --- Condition 0: Guard against misidentified verbs. ---
        # If the token is preceded by "to", it's almost certainly an infinitive verb,
        # regardless of what the POS tagger might say due to bad grammar.
        # This check is crucial for fixing the "configure" false positive.
        if token.i > 0 and doc[token.i - 1].lower_ == 'to':
            return False

        # --- Condition 1: The token must NOT be part of a compound noun. ---
        if token.dep_ == 'compound':
            return False

        # --- Condition 2: The token must be a singular common noun. ---
        if token.pos_ == 'NOUN' and token.tag_ == 'NN':
            
            # --- Condition 3: The noun must NOT already have a determiner. ---
            has_determiner = any(child.dep_ in ('det', 'poss') for child in token.children)
            if has_determiner:
                return False

            # --- Condition 4: The noun should be a subject or object. ---
            is_subject_or_object = token.dep_ in ('nsubj', 'dobj', 'pobj')
            if is_subject_or_object:
                # --- Condition 5: Add exclusions for common abstract nouns. ---
                if token.lemma_ in ['access', 'permission', 'information', 'guidance', 'storage', 'software', 'security', 'support']:
                    return False
                
                return True

        return False

"""
Articles Rule (with True Linguistic Analysis)
Based on IBM Style Guide topic: "Articles"
"""
from typing import List, Dict, Any
# We will use a lightweight, specialized library for grammatical inflection
# to determine if a noun is countable.
# You would need to add this to your project: pip install pyinflect
import pyinflect
from .base_language_rule import BaseLanguageRule

class ArticlesRule(BaseLanguageRule):
    """
    Checks for common article errors. This version uses true linguistic
    analysis to distinguish between countable and uncountable (mass) nouns,
    eliminating the need for a hard-coded exclusion list.
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
                # Rule 1: 'a' vs 'an' (This logic is already robust)
                if token.lower_ in ['a', 'an'] and j < len(doc) - 1:
                    next_token = doc[j + 1]
                    if self._is_incorrect_article_usage(token, next_token):
                        errors.append(self._create_error(
                            sentence=sentence, sentence_index=i,
                            message=f"Incorrect article usage: Use '{'an' if self._starts_with_vowel_sound(next_token.text) else 'a'}' before '{next_token.text}'.",
                            suggestions=[f"Change '{token.text} {next_token.text}' to '{'an' if self._starts_with_vowel_sound(next_token.text) else 'a'} {next_token.text}'."],
                            severity='medium'
                        ))
                
                # Rule 2: Missing Articles (with new linguistic check)
                if self._is_missing_article_candidate(token, doc):
                    errors.append(self._create_error(
                        sentence=sentence, sentence_index=i,
                        message=f"Potentially missing article before the noun '{token.text}'.",
                        suggestions=["Singular countable nouns often require an article (a/an/the). Please review."],
                        severity='low'
                    ))
        return errors

    def _starts_with_vowel_sound(self, word: str) -> bool:
        """A robust check for whether a word starts with a vowel sound."""
        word_lower = word.lower()
        if word_lower.startswith(('user', 'unit', 'one', 'uniform')):
            return False
        if word_lower.startswith(('hour', 'honest', 'honor')):
            return True
        return word_lower[0] in 'aeiou'

    def _is_incorrect_article_usage(self, article_token, next_token) -> bool:
        """Helper to consolidate 'a' vs 'an' logic."""
        starts_with_vowel = self._starts_with_vowel_sound(next_token.text)
        if article_token.lower_ == 'a' and starts_with_vowel:
            return True
        if article_token.lower_ == 'an' and not starts_with_vowel:
            return True
        return False

    def _is_uncountable(self, token) -> bool:
        """
        Determines if a noun is uncountable (a mass noun) using pyinflect.
        This is the core of the new, more intelligent logic.
        """
        # Get the lemma (base form) of the noun
        lemma = token.lemma_
        
        # Use pyinflect to get the plural form (NNS tag)
        plural_form = pyinflect.getInflection(lemma, 'NNS')
        
        # If there is no plural form, it's an uncountable/mass noun.
        # This correctly identifies "content", "information", "software", etc.
        return plural_form is None

    def _is_missing_article_candidate(self, token, doc) -> bool:
        """
        A highly accurate check for missing articles that uses linguistic
        analysis to avoid flagging uncountable nouns.
        """
        # Basic checks for efficiency
        if token.dep_ == 'compound' or (token.i > 0 and doc[token.i - 1].lower_ == 'to'):
            return False

        # Check if it's a singular common noun
        if token.pos_ == 'NOUN' and token.tag_ == 'NN':
            # Check if it already has a determiner
            if any(child.dep_ in ('det', 'poss') for child in token.children):
                return False
            
            # THE KEY FIX: Check if the noun is uncountable. If so, it doesn't need an article.
            if self._is_uncountable(token):
                return False

            # Only flag if it's a subject or object
            if token.dep_ in ('nsubj', 'dobj', 'pobj'):
                return True

        return False

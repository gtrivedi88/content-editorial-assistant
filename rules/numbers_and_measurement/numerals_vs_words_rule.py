"""
Numerals versus Words Rule
Based on IBM Style Guide topic: "Numerals versus words"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule

class NumeralsVsWordsRule(BaseNumbersRule):
    """
    Checks for consistency in using numerals versus words for numbers,
    especially for numbers under 10.
    """
    def _get_rule_type(self) -> str:
        return 'numbers_numerals_vs_words'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text to detect inconsistent usage of numerals and words for small numbers.
        """
        errors = []
        if not nlp:
            return errors

        words_under_10 = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine"}
        numerals_under_10 = {"1", "2", "3", "4", "5", "6", "7", "8", "9"}

        found_words = False
        found_numerals = False

        for sentence in sentences:
            doc = nlp(sentence)
            for token in doc:
                if token.lemma_.lower() in words_under_10:
                    found_words = True
                if token.text in numerals_under_10:
                    # Linguistic Anchor: Ensure it's not part of a version number or measurement.
                    if token.head.lemma_.lower() not in ["version", "release", "chapter", "figure", "table", "page"] and not token.head.like_url:
                         found_numerals = True

        # If both styles are found in the text, flag an inconsistency.
        if found_words and found_numerals:
            errors.append(self._create_error(
                sentence=text, # Report on the whole text
                sentence_index=0,
                message="Inconsistent use of numerals and words for numbers under 10.",
                suggestions=["Choose one style for numbers under 10 (either numerals or words) and apply it consistently throughout the document."],
                severity='low'
            ))
        return errors

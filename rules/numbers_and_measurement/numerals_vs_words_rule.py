"""
Numerals versus Words Rule
Based on IBM Style Guide topic: "Numerals versus words"
"""
from typing import List, Dict, Any
from .base_numbers_rule import BaseNumbersRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NumeralsVsWordsRule(BaseNumbersRule):
    """
    Checks for consistency in using numerals versus words for numbers,
    especially for numbers under 10.
    """
    def _get_rule_type(self) -> str:
        return 'numerals_vs_words'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text to detect inconsistent usage of numerals and words for small numbers.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        words_under_10 = {"one", "two", "three", "four", "five", "six", "seven", "eight", "nine"}
        
        found_words = False
        found_numerals = False

        for token in doc:
            if token.lemma_.lower() in words_under_10:
                found_words = True
            if token.like_num and 0 < int(token.text) < 10:
                 if token.head.lemma_.lower() not in ["version", "release", "chapter", "figure", "table", "page"]:
                     found_numerals = True
        
        # If both styles are found, flag an inconsistency on the first occurrence of a spelled-out number.
        if found_words and found_numerals:
            for i, sent in enumerate(doc.sents):
                for token in sent:
                    if token.lemma_.lower() in words_under_10:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message="Inconsistent use of numerals and words for numbers under 10.",
                            suggestions=["Choose one style for numbers under 10 (either numerals or words) and apply it consistently. Numerals are generally preferred."],
                            severity='low',
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
                        # Only flag the first occurrence to avoid clutter
                        return errors
        return errors

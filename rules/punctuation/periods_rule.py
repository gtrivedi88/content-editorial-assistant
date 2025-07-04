"""
Periods Rule
Based on IBM Style Guide topic: "Periods"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class PeriodsRule(BasePunctuationRule):
    """
    Checks for incorrect use of periods, such as in uppercase abbreviations.
    """
    def _get_rule_type(self) -> str:
        return 'periods'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # Rule: Omit periods in uppercase abbreviations.
                # Find patterns like U.S.A. by checking for sequences of single
                # uppercase letters followed by periods.
                if token.text == '.' and token.i > 0 and token.i < len(doc) -1:
                    prev_token = doc[token.i - 1]
                    next_token = doc[token.i + 1]
                    # Check for pattern like: [UPPER] . [UPPER]
                    if prev_token.is_upper and len(prev_token.text) == 1 and next_token.is_upper and len(next_token.text) == 1:
                         errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message=f"Avoid periods in the uppercase abbreviation.",
                            suggestions=["Remove the periods from the abbreviation (e.g., 'USA' instead of 'U.S.A.')."],
                            severity='low'
                        ))
        return errors

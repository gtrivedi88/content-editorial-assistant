"""
Periods Rule
Based on IBM Style Guide topic: "Periods"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PeriodsRule(BasePunctuationRule):
    """
    Checks for incorrect use of periods, focusing on the rule to omit
    periods from within uppercase abbreviations.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'periods'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for periods within uppercase abbreviations.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.text == '.':
                    if token.i > sent.start and token.i < sent.end - 1:
                        prev_token = sent.doc[token.i - 1]
                        next_token = sent.doc[token.i + 1]
                        
                        # Linguistic Anchor: Pattern is a single uppercase letter,
                        # followed by a period, followed by another single uppercase letter.
                        is_abbreviation_pattern = (
                            prev_token.is_upper and len(prev_token.text) == 1 and
                            next_token.is_upper and len(next_token.text) == 1
                        )

                        if is_abbreviation_pattern:
                            flagged_text = f"{prev_token.text}.{next_token.text}"
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message="Avoid using periods within uppercase abbreviations.",
                                suggestions=["Remove the periods from the abbreviation (e.g., 'USA' instead of 'U.S.A.')."],
                                severity='low',
                                span=(prev_token.idx, next_token.idx + len(next_token.text)),
                                flagged_text=flagged_text
                            ))
        return errors

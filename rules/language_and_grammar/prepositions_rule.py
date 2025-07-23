"""
Prepositions Rule
Based on IBM Style Guide topic: "Prepositions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PrepositionsRule(BaseLanguageRule):
    """
    Checks for sentences that may be overly complex due to a high number
    of prepositional phrases.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'prepositions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for an excessive number of prepositions.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        PREPOSITION_THRESHOLD = 4

        for i, sent in enumerate(doc.sents):
            # Use SpaCy's POS tagging to count the prepositions (ADP).
            prepositions = [token for token in sent if token.pos_ == 'ADP']
            
            if len(prepositions) > PREPOSITION_THRESHOLD:
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Sentence contains a high number of prepositions, which may indicate a complex or unclear structure.",
                    suggestions=["Consider rewriting to simplify the sentence structure. For example, 'The report is a list of the status of all of the event monitors for this process' could become 'The report lists the current status of all event monitors for this process'."],
                    severity='low',
                    span=(sent.start_char, sent.end_char),
                    flagged_text=sent.text
                ))
        return errors

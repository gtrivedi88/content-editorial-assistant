"""
Plurals Rule
Based on IBM Style Guide topic: "Plurals"
"""
import re
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class PluralsRule(BaseLanguageRule):
    """
    Checks for several common pluralization errors, including the use of "(s)",
    and using plural nouns as adjectives.
    """
    def _get_rule_type(self) -> str:
        return 'plurals'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for pluralization errors.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        for i, sent in enumerate(doc.sents):
            # Rule 1: Avoid using "(s)" to indicate plural
            for match in re.finditer(r'\w+\(s\)', sent.text, re.IGNORECASE):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Avoid using '(s)' to indicate a plural.",
                    suggestions=["Rewrite the sentence to use either the singular or plural form, or use a phrase like 'one or more'."],
                    severity='medium',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))

            # Rule 2: Avoid using plural nouns as adjectives
            for token in sent:
                if token.tag_ == 'NNS' and token.dep_ == 'compound':
                    if token.lemma_ != token.lower_:
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=f"Potential misuse of a plural noun '{token.text}' as an adjective.",
                            suggestions=[f"Consider using the singular form '{token.lemma_}' when a noun modifies another noun."],
                            severity='low',
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors

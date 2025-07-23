"""
Programming Elements Rule
Based on IBM Style Guide topic: "Programming elements"
"""
from typing import List, Dict, Any
from .base_technical_rule import BaseTechnicalRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ProgrammingElementsRule(BaseTechnicalRule):
    """
    Checks for the incorrect use of programming keywords as verbs.
    """
    def _get_rule_type(self) -> str:
        return 'technical_programming_elements'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text to find programming keywords used as verbs.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        keywords = {"drop", "create", "select", "insert", "update", "delete"}

        for i, sent in enumerate(doc.sents):
            for token in sent:
                # Linguistic Anchor: Check if a known keyword is tagged as a verb.
                if token.lemma_.lower() in keywords and token.pos_ == 'VERB':
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Do not use the programming keyword '{token.text}' as a verb.",
                        suggestions=[f"Rewrite the sentence to use the keyword as a noun, e.g., 'To delete an object, issue the DROP statement.'"],
                        severity='high',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors

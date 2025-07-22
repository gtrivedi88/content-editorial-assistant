"""
Citations and References Rule
Based on IBM Style Guide topic: "Citations and references"
"""
from typing import List, Dict, Any
from .base_references_rule import BaseReferencesRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CitationsRule(BaseReferencesRule):
    """
    Checks for incorrect formatting of citations and links, such as the
    use of "Click here" and incorrect capitalization of cited elements.
    """
    def _get_rule_type(self) -> str:
        return 'references_citations'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for citation and linking errors.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        
        # --- Rule 1: Problematic Link Text ---
        # Linguistic Anchor: Find imperative verbs like "click" followed by "here".
        for i, sent in enumerate(doc.sents):
            for match in re.finditer(r'\b(click|see|go)\s+here\b', sent.text, re.IGNORECASE):
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message="Avoid using generic link text like 'Click here'. The link text should be meaningful.",
                    suggestions=["Rewrite the link to describe its destination, e.g., 'For more information, see the Installation Guide.'"],
                    severity='high',
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=match.group(0)
                ))

        # --- Rule 2: Incorrect Reference Capitalization ---
        # Linguistic Anchor: Find common reference nouns (chapter, figure) that are capitalized
        # when they should be lowercase in cross-references.
        reference_nouns = {"Chapter", "Appendix", "Figure", "Table", "Section"}
        for token in doc:
            if token.text in reference_nouns:
                # Check context: if it's followed by a number, it's likely a cross-reference
                # that should be lowercase.
                if token.i + 1 < len(doc) and doc[token.i + 1].like_num:
                    sent = token.sent
                    sent_index = list(doc.sents).index(sent)
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=sent_index,
                        message="References to document parts like 'chapter' or 'figure' should be lowercase in cross-references.",
                        suggestions=[f"Use lowercase for the reference type, e.g., 'see {token.text.lower()} 9'."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))
        return errors

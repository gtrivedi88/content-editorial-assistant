"""
Names and Titles Rule
Based on IBM Style Guide topic: "Names and titles"
"""
from typing import List, Dict, Any
from .base_references_rule import BaseReferencesRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class NamesAndTitlesRule(BaseReferencesRule):
    """
    Checks for correct capitalization of professional titles, distinguishing
    between titles used with names versus standalone usage.
    """
    def _get_rule_type(self) -> str:
        return 'references_names_titles'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for incorrect capitalization of professional titles.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        professional_titles = {"ceo", "director", "manager", "president", "officer", "engineer"}

        for i, sent in enumerate(doc.sents):
            for token in sent:
                if token.lemma_.lower() in professional_titles:
                    # Linguistic Anchor: Check if the title is part of a person's name (appositional modifier).
                    is_with_name = token.head.ent_type_ == 'PERSON' and token.dep_ == 'appos'

                    # Rule: Titles with names should be capitalized.
                    if is_with_name and not token.is_title:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=i,
                            message=f"Professional title '{token.text}' should be capitalized when used with a name.",
                            suggestions=[f"Capitalize the title: '{token.text.title()}'."],
                            severity='medium',
                            text=text,  # Enhanced: Pass full text for better confidence analysis
                            context=context,  # Enhanced: Pass context for domain-specific validation
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
                    
                    # Rule: Standalone titles should be lowercase.
                    elif not is_with_name and token.is_title:
                        errors.append(self._create_error(
                            sentence=sent.text, sentence_index=i,
                            message=f"Standalone professional title '{token.text}' should be lowercase.",
                            suggestions=[f"Use lowercase for the title: '{token.text.lower()}'."],
                            severity='medium',
                            text=text,  # Enhanced: Pass full text for better confidence analysis
                            context=context,  # Enhanced: Pass context for domain-specific validation
                            span=(token.idx, token.idx + len(token.text)),
                            flagged_text=token.text
                        ))
        return errors

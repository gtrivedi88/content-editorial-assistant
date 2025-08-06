"""
Company Names Rule
Based on IBM Style Guide topic: "Company names"
"""
from typing import List, Dict, Any
from .base_legal_rule import BaseLegalRule

class CompanyNamesRule(BaseLegalRule):
    """
    Checks that company names are referred to by their full legal name
    where appropriate.
    """
    def _get_rule_type(self) -> str:
        return 'legal_company_names'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text to find company names that might be missing a legal suffix.
        """
        errors = []
        if not nlp:
            return errors

        # Linguistic Anchor: A dictionary of known companies and their legal suffixes.
        # This list would be expanded in a real system.
        companies = {"Oracle", "Microsoft", "Red Hat"}
        suffixes = {"Corp", "Corporation", "Inc", "Incorporated"}

        doc = nlp(text)
        for ent in doc.ents:
            # Check if an ORG entity is a known company missing its suffix.
            if ent.label_ == 'ORG' and ent.text in companies:
                # Check if the next token is a legal suffix.
                if ent.end >= len(doc) or doc[ent.end].text.strip('.') not in suffixes:
                    errors.append(self._create_error(
                        sentence=ent.sent.text,
                        sentence_index=sentences.index(ent.sent.text) if ent.sent.text in sentences else -1,
                        message=f"Company name '{ent.text}' should be written with its full legal name on first use.",
                        suggestions=[f"Use the full company name, such as '{ent.text} Corporation'."],
                        severity='low',
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context  # Enhanced: Pass context for domain-specific validation
                    ))
        return errors

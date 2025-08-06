"""
Geographic Locations Rule
Based on IBM Style Guide topic: "Geographic locations"
"""
from typing import List, Dict, Any
from .base_references_rule import BaseReferencesRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class GeographicLocationsRule(BaseReferencesRule):
    """
    Uses SpaCy's Named Entity Recognition (NER) to check for correct
    capitalization of geographic locations.
    """
    def _get_rule_type(self) -> str:
        return 'references_geographic_locations'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text to find improperly capitalized geographic locations.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for ent in sent.ents:
                # Linguistic Anchor: Check for geographic entities (GPE, LOC, FAC).
                if ent.label_ in ['GPE', 'LOC', 'FAC']:
                    # Rule: Geographic locations should be properly capitalized (title case).
                    if not all(token.is_title or not token.is_alpha for token in ent):
                        errors.append(self._create_error(
                            sentence=sent.text,
                            sentence_index=i,
                            message=f"Geographic location '{ent.text}' may have incorrect capitalization.",
                            suggestions=[f"Ensure all parts of the location name are capitalized correctly (e.g., '{ent.text.title()}')."],
                            severity='medium',
                            text=text,  # Enhanced: Pass full text for better confidence analysis
                            context=context,  # Enhanced: Pass context for domain-specific validation
                            span=(ent.start_char, ent.end_char),
                            flagged_text=ent.text
                        ))
        return errors

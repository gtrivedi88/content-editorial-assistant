"""
Capitalization Rule (Corrected for False Positives)
Based on IBM Style Guide topic: "Capitalization"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class CapitalizationRule(BaseLanguageRule):
    """
    Checks for incorrect capitalization, specifically focusing on the
    over-capitalization of common nouns within a sentence.
    """
    def _get_rule_type(self) -> str:
        return 'capitalization'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        # ENTERPRISE CONTEXT INTELLIGENCE: Get content classification
        content_classification = self._get_content_classification(text, context, nlp)
        
        doc = nlp(text)

        for i, sent in enumerate(doc.sents):
            for token in sent:
                # Rule 1: Unnecessary capitalization
                if token.is_title and not self._should_be_capitalized_morphological(token, doc, content_classification):
                    errors.append(self._create_error(
                        sentence=sent.text, sentence_index=i,
                        message=f"Unnecessary capitalization of the common noun '{token.text}'.",
                        suggestions=["Common nouns should be lowercase unless they are part of a proper name or at the beginning of a sentence."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))

                # Rule 2: Missing capitalization for proper nouns
                if token.is_lower and self._should_be_capitalized_proper_morphological(token, doc):
                    errors.append(self._create_error(
                        sentence=sent.text, sentence_index=i,
                        message=f"'{token.text}' should be capitalized as it appears to be a proper noun.",
                        suggestions=[f"Capitalize '{token.text}' to '{token.text.capitalize()}'."],
                        severity='medium',
                        span=(token.idx, token.idx + len(token.text)),
                        flagged_text=token.text
                    ))

        return errors

    def _should_be_capitalized_morphological(self, token, doc, content_classification: str) -> bool:
        """Pure morphological logic using SpaCy linguistic anchors."""
        
        # LINGUISTIC ANCHOR 1: Sentence position analysis
        if token.is_sent_start or (token.i > 0 and doc[token.i - 1].is_punct):
            return True
        
        # LINGUISTIC ANCHOR 2: SpaCy POS-based proper noun detection
        if token.pos_ == 'PROPN':
            return True
            
        # LINGUISTIC ANCHOR 3: Named entity recognition
        if token.ent_type_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'LANGUAGE']:
            return True
            
        # LINGUISTIC ANCHOR 4: Technical compound detection in appropriate contexts
        if content_classification in ['technical_identifier', 'topic_heading', 'navigation_label']:
            # Use dependency parsing to detect compounds
            if token.dep_ == 'compound' or any(child.dep_ == 'compound' for child in token.children):
                # Check if this is part of a technical compound through morphology
                if self._has_technical_morphology(token):
                    return True
                    
        # LINGUISTIC ANCHOR 5: Morphological patterns for months/days
        if token.morph and 'proper' in str(token.morph).lower():
            return True
        
        return False
    
    def _should_be_capitalized_proper_morphological(self, token, doc) -> bool:
        """Use SpaCy morphological features to detect proper nouns that should be capitalized."""
        
        # LINGUISTIC ANCHOR 1: SpaCy named entity detection
        if token.ent_type_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT', 'LANGUAGE']:
            return True
            
        # LINGUISTIC ANCHOR 2: SpaCy POS tagging indicates proper noun
        if token.pos_ == 'PROPN':
            return True
            
        # LINGUISTIC ANCHOR 3: Morphological proper noun indicators
        if token.morph and any(feature in str(token.morph) for feature in ['Proper', 'NNP']):
            return True
            
        return False

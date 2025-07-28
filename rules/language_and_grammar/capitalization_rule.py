"""
Capitalization Rule
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
    Checks for missing capitalization in text.
    Comprehensive rule processing using the SpaCy engine for linguistic accuracy.
    """
    def _get_rule_type(self) -> str:
        return 'capitalization'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors

        # Skip analysis for content that was originally inline formatted (code, emphasis, etc.)
        if context and context.get('contains_inline_formatting'):
            return errors

        # ENTERPRISE CONTEXT INTELLIGENCE: Get content classification
        content_classification = self._get_content_classification(text, context, nlp)
        
        doc = nlp(text)

        # LINGUISTIC ANCHOR: Use spaCy sentence segmentation for precise analysis
        for i, sent in enumerate(doc.sents):
            for token in sent:
                # Rule 1: Check for proper nouns that should be capitalized
                if self._should_be_capitalized_morphological(token, doc, content_classification):
                    if token.text.islower():
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
            
        # LINGUISTIC ANCHOR 4: Morphological patterns for months/days
        if token.morph and 'proper' in str(token.morph).lower():
            return True
        
        return False

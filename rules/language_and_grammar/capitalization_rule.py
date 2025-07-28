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
        """
        Ultra-conservative morphological logic using SpaCy linguistic anchors.
        Only flags high-confidence proper nouns to avoid false positives.
        """
        
        # EXCEPTION CHECK: Never flag words in the exception list
        if self._is_excepted(token.text):
            return False
        
        # LINGUISTIC ANCHOR 1: High-confidence Named Entity Recognition ONLY
        # This is the primary and most reliable signal for proper nouns
        if token.ent_type_ in ['PERSON', 'ORG', 'GPE', 'PRODUCT']:
            # Additional confidence check: ensure it's not a misclassified common word
            # and has proper noun characteristics
            if (len(token.text) > 1 and  # Skip single characters
                not token.text.lower() in ['user', 'data', 'file', 'system', 'admin', 'guest', 'client', 'server'] and
                # Entity should have some proper noun indicators
                (token.text[0].isupper() or  # Already properly capitalized
                 token.ent_iob_ in ['B', 'I'])):  # Strong entity boundary signal
                return True
        
        # LINGUISTIC ANCHOR 2: Very conservative sentence start logic
        # Only for clear proper nouns at sentence start that are definitely names
        if token.is_sent_start and len(token.text) > 1:
            # Must be explicitly tagged as a named entity with strong confidence
            if (token.ent_type_ in ['PERSON', 'ORG', 'GPE'] and 
                token.text[0].islower() and
                not self._is_excepted(token.text)):
                return True
                
        # LINGUISTIC ANCHOR 3: Proper noun sequences (like "New York")
        # Only trigger for clear multi-word proper nouns  
        if (token.i > 0 and 
            doc[token.i - 1].ent_type_ in ['PERSON', 'ORG', 'GPE'] and  # Previous token is a named entity
            token.ent_type_ == doc[token.i - 1].ent_type_ and  # Same entity type
            token.text[0].islower() and
            not self._is_excepted(token.text)):
            return True
        
        return False

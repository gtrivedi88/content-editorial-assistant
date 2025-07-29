"""
Product and Service Names Rule
Based on IBM Style Guide topic: "Product and service names"
"""
from typing import List, Dict, Any
from .base_references_rule import BaseReferencesRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ProductNamesRule(BaseReferencesRule):
    """
    Checks for correct usage of product names, focusing on the requirement
    to include 'IBM' on the first mention.
    """
    def _get_rule_type(self) -> str:
        return 'references_product_names'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for product naming violations.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        known_products = {}  # Track first mention of products

        for i, sent in enumerate(doc.sents):
            for ent in sent.ents:
                # Linguistic Anchor: Identify product entities.
                if ent.label_ == 'PRODUCT':
                    product_name = ent.text
                    
                    # CONTEXT FILTER: Skip UI elements and common false positives
                    if self._is_ui_element_or_false_positive(ent, doc):
                        continue
                    
                    # Rule: First reference must be preceded by "IBM".
                    if product_name not in known_products:
                        known_products[product_name] = True
                        
                        # Check if the token before the entity is "IBM".
                        if ent.start == 0 or doc[ent.start - 1].text != 'IBM':
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message=f"The first mention of a product, '{product_name}', should be preceded by 'IBM'.",
                                suggestions=[f"Use the full name 'IBM {product_name}' for the first reference."],
                                severity='high',
                                span=(ent.start_char, ent.end_char),
                                flagged_text=ent.text
                            ))
        return errors
    
    def _is_ui_element_or_false_positive(self, entity, doc):
        """
        LINGUISTIC ANCHOR: Uses SpaCy dependency parsing to detect UI elements.
        Checks if PRODUCT entity has syntactic relationships indicating UI context.
        """
        # LINGUISTIC ANCHOR 1: Dependency analysis for UI context
        # Check if entity is modified by or modifies UI-related terms
        for token in entity:
            # Check syntactic children (compounds, modifiers)
            for child in token.children:
                if child.lemma_.lower() in ['button', 'menu', 'dialog', 'window', 'field', 'tab']:
                    return True
            
            # Check syntactic head (what this token modifies)
            if token.head.lemma_.lower() in ['button', 'menu', 'dialog', 'window', 'field', 'tab']:
                return True
        
        # LINGUISTIC ANCHOR 2: Verbal context analysis  
        # Check if entity is object of UI action verbs
        sent = entity.sent
        for token in sent:
            if (token.pos_ == 'VERB' and 
                token.lemma_.lower() in ['click', 'press', 'tap', 'select'] and
                any(child == entity[0] for child in token.children if child.dep_ in ['dobj', 'pobj'])):
                return True
        
        return False

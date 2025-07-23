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

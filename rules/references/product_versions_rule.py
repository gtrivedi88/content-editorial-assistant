"""
Product Versions Rule
Based on IBM Style Guide topic: "Product versions"
"""
from typing import List, Dict, Any
from .base_references_rule import BaseReferencesRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ProductVersionsRule(BaseReferencesRule):
    """
    Checks for incorrect formatting of product version numbers, such as
    the use of 'V.' or 'Version' prefixes.
    """
    def _get_rule_type(self) -> str:
        return 'references_product_versions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for product version formatting errors.
        """
        errors = []
        if not nlp:
            return errors

        doc = nlp(text)
        
        # Linguistic Anchor: Find invalid version prefixes followed by a number.
        version_prefix_pattern = re.compile(r'\b(V|R|Version|Release)\.?\s*(\d+(\.\d+)*)\b', re.IGNORECASE)

        for i, sent in enumerate(doc.sents):
            for match in version_prefix_pattern.finditer(sent.text):
                full_match = match.group(0)
                version_number = match.group(2)
                errors.append(self._create_error(
                    sentence=sent.text,
                    sentence_index=i,
                    message=f"Avoid using version identifiers like 'V' or 'Version'. Use only the number.",
                    suggestions=[f"Refer to the version as just '{version_number}'."],
                    severity='medium',
                    text=text,  # Enhanced: Pass full text for better confidence analysis
                    context=context,  # Enhanced: Pass context for domain-specific validation
                    span=(sent.start_char + match.start(), sent.start_char + match.end()),
                    flagged_text=full_match
                ))
        return errors

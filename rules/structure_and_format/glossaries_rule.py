"""
Glossaries Rule
Based on IBM Style Guide topic: "Glossaries"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule
import re

class GlossariesRule(BaseStructureRule):
    """
    Checks for basic glossary formatting. It ensures that glossary terms are
    lowercase (unless they are proper nouns) and that definitions start
    with a capital letter, adhering to the style guide's conventions for clarity.
    """
    def _get_rule_type(self) -> str:
        return 'structure_format_glossaries'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for glossary formatting issues.
        Note: This rule requires a clear context that it's analyzing a glossary.
        """
        errors = []
        # This rule is highly context-dependent and assumes it's analyzing a glossary.
        # A simple heuristic is to look for definition list patterns.
        # A more robust solution would rely on semantic document structure (e.g., DITA, specific Markdown).
        if not nlp or not context or 'is_glossary' not in context:
            return errors

        # Heuristic: Find lines that look like "term - definition" or "term: definition"
        for i, sentence in enumerate(sentences):
            # Regex to find a potential term and definition
            match = re.match(r'^\s*([\w\s-]+?)\s*[:—-]\s*(.*)', sentence)
            if match:
                term, definition = match.groups()
                term = term.strip()
                definition = definition.strip()

                if not term or not definition:
                    continue

                # Linguistic Anchor: Check if the term is a proper noun.
                term_doc = nlp(term)
                is_proper_noun = all(tok.pos_ == 'PROPN' for tok in term_doc)

                # Rule: Use lowercase for glossary terms unless a term is a proper noun.
                if not is_proper_noun and not term.islower():
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Glossary term '{term}' should be lowercase unless it is a proper noun.",
                        suggestions=[f"Change '{term}' to '{term.lower()}'."],
                        severity='medium'
                    ))

                # Rule: Use sentence-style capitalization for glossary definitions.
                if not definition[0].isupper():
                     errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Glossary definitions should start with a capital letter.",
                        suggestions=["Capitalize the first word of the definition."],
                        severity='medium'
                    ))
        return errors

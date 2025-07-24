"""
Glossaries Rule
Based on IBM Style Guide topic: "Glossaries"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class GlossariesRule(BaseStructureRule):
    """
    Checks for basic glossary formatting, ensuring terms are lowercase
    (unless proper nouns) and definitions are capitalized.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'glossaries'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text for glossary formatting issues.
        """
        errors = []
        if not nlp or not context or not context.get('is_glossary', False):
            return errors

        for i, sentence in enumerate(sentences):
            match = re.match(r'^\s*([\w\s-]+?)\s*[:—-]\s*(.*)', sentence)
            if match:
                term, definition = match.groups()
                term = term.strip()
                definition = definition.strip()

                if not term or not definition:
                    continue

                term_doc = nlp(term)
                is_proper_noun = all(tok.pos_ == 'PROPN' for tok in term_doc)

                if not is_proper_noun and not term.islower():
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Glossary term '{term}' should be lowercase unless it is a proper noun.",
                        suggestions=[f"Change '{term}' to '{term.lower()}'."],
                        severity='medium',
                        span=(sentence.find(term), sentence.find(term) + len(term)),
                        flagged_text=term
                    ))

                if not definition[0].isupper():
                     errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="Glossary definitions should start with a capital letter.",
                        suggestions=["Capitalize the first word of the definition."],
                        severity='medium',
                        span=(sentence.find(definition), sentence.find(definition) + len(definition)),
                        flagged_text=definition
                    ))
        return errors

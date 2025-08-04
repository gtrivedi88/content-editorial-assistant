"""
Spelling Rule
Based on IBM Style Guide topic: "Spelling"
"""
from typing import List, Dict, Any
import re
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class SpellingRule(BaseLanguageRule):
    """
    Checks for common non-US spellings and suggests the preferred US spelling,
    as required by the IBM Style Guide.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'spelling'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for common non-US English spellings.
        """
        errors = []
        if not nlp:
            return errors
        doc = nlp(text)

        spelling_map = {
            "centre": "center", "colour": "color", "flavour": "flavor",
            "licence": "license", "organise": "organize", "analyse": "analyze",
            "catalogue": "catalog", "dialogue": "dialog", "grey": "gray",
            "behaviour": "behavior", "programme": "program",
        }

        for i, sent in enumerate(doc.sents):
            for non_us, us_spelling in spelling_map.items():
                pattern = r'\b' + re.escape(non_us) + r'\b'
                for match in re.finditer(pattern, sent.text, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sent.text,
                        sentence_index=i,
                        message=f"Non-US spelling used for '{match.group()}'.",
                        suggestions=[f"IBM Style prefers US spelling. Use '{us_spelling}' instead."],
                        severity='medium',
                        text=text,  # Enhanced: Pass full text for better confidence analysis
                        context=context,  # Enhanced: Pass context for domain-specific validation
                        span=(sent.start_char + match.start(), sent.start_char + match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors

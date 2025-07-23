"""
Messages Rule
Based on IBM Style Guide topic: "Messages"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule
import re

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class MessagesRule(BaseStructureRule):
    """
    Checks for common style issues in error, warning, and informational messages,
    such as the use of exaggerated or unhelpful language.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'structure_format_messages'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text that is likely a system message for style violations.
        """
        errors = []
        
        # Linguistic Anchor: Exaggerated adjectives discouraged in messages.
        exaggerated_adjectives = {'catastrophic', 'fatal', 'illegal'}

        for i, sentence in enumerate(sentences):
            for word in exaggerated_adjectives:
                # Use word boundaries for accurate matching.
                for match in re.finditer(rf'\b{word}\b', sentence, re.IGNORECASE):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Avoid using exaggerated adjectives like '{match.group(0)}' in messages.",
                        suggestions=["Focus on the problem and the solution, not the severity. For example, instead of 'A fatal error occurred', state 'The application could not connect to the database'."],
                        severity='medium',
                        span=(match.start(), match.end()),
                        flagged_text=match.group(0)
                    ))
        return errors

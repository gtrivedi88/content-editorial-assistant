"""
Messages Rule
Based on IBM Style Guide topic: "Messages"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class MessagesRule(BaseStructureRule):
    """
    Checks for common style issues in error, warning, and informational messages.
    """
    def _get_rule_type(self) -> str:
        return 'messages'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Linguistic Anchor: Discouraged words in error messages.
        exaggerated_adjectives = {'catastrophic', 'fatal', 'illegal'}

        for i, sentence in enumerate(sentences):
            # Rule: Avoid exaggerated or overly alarming adjectives.
            for word in exaggerated_adjectives:
                if word in sentence.lower():
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Avoid using exaggerated adjectives like '{word}' in messages.",
                        suggestions=["Focus on the problem and the solution, not the severity. For example, instead of 'A fatal error occurred', state 'The application could not connect to the database'."],
                        severity='medium'
                    ))
        return errors

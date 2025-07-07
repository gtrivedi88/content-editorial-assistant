"""
Messages Rule
Based on IBM Style Guide topic: "Messages"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class MessagesRule(BaseStructureRule):
    """
    Checks for common style issues in error, warning, and informational messages,
    such as the use of exaggerated or unhelpful language.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'messages'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes text that is likely a system message for style violations.
        """
        errors = []
        
        # Linguistic Anchor: A set of exaggerated adjectives that are discouraged
        # in messages according to the IBM Style Guide.
        exaggerated_adjectives = {'catastrophic', 'fatal', 'illegal'}

        for i, sentence in enumerate(sentences):
            # Rule: Avoid exaggerated or overly alarming adjectives.
            # We check the sentence for the presence of these specific words.
            # This is a reliable check as these words are almost never appropriate
            # in technical user-facing messages.
            for word in exaggerated_adjectives:
                # Using word boundaries (\b) to ensure we match whole words only.
                if f" {word} " in f" {sentence.lower()} ":
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Avoid using exaggerated adjectives like '{word}' in messages.",
                        suggestions=["Focus on the problem and the solution, not the severity. For example, instead of 'A fatal error occurred', state 'The application could not connect to the database'."],
                        severity='medium'
                    ))
        return errors

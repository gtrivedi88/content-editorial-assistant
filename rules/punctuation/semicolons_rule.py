"""
Semicolons Rule
Based on IBM Style Guide topic: "Semicolons"
"""
from typing import List, Dict, Any
from rules.punctuation.base_punctuation_rule import BasePunctuationRule

class SemicolonsRule(BasePunctuationRule):
    """
    Checks for semicolons, which are discouraged in technical writing by the
    IBM Style Guide in favor of shorter, clearer sentences.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'semicolons'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the presence of semicolons.
        """
        errors = []
        # The IBM Style Guide is direct: "Use a semicolon to separate independent
        # clauses or items in a series that has internal punctuation. If a sentence
        # is complex, difficult to read, or longer than 32 words, consider
        # rewriting it, separating it into multiple sentences..."
        # For a style checker, flagging any semicolon for review is the most
        # reliable way to enforce this principle of clarity and simplicity.
        for i, sentence in enumerate(sentences):
            if ';' in sentence:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Avoid semicolons in technical writing to improve clarity.",
                    suggestions=["Consider rewriting the sentence as two separate, shorter sentences."],
                    severity='low'
                ))
        return errors
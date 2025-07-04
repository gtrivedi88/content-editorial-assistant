"""
Slashes Rule
Based on IBM Style Guide topic: "Slashes"
"""
from typing import List, Dict, Any
from rules.punctuation.base_punctuation_rule import BasePunctuationRule

class SlashesRule(BasePunctuationRule):
    """
    Checks for the ambiguous use of slashes to mean "and/or", using
    Part-of-Speech tagging to identify the grammatical context.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'slashes'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the ambiguous use of the slash character.
        """
        errors = []
        if not nlp:
            # This rule requires Part-of-Speech tagging for context.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # The rule triggers when a slash character is found.
                if token.text == '/':
                    # --- Context-Aware Check ---
                    # To avoid false positives in URLs or file paths, we check the
                    # grammatical context. The ambiguous "and/or" usage typically
                    # occurs between two nouns or two adjectives.
                    if token.i > 0 and token.i < len(doc) - 1:
                        prev_token = doc[token.i - 1]
                        next_token = doc[token.i + 1]
                        
                        # Linguistic Anchor: The pattern for this error is a noun/adjective
                        # followed by a slash, followed by another noun/adjective.
                        is_ambiguous_slash_pattern = (
                            prev_token.pos_ in ["NOUN", "ADJ", "PROPN"] and
                            next_token.pos_ in ["NOUN", "ADJ", "PROPN"]
                        )

                        if is_ambiguous_slash_pattern:
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message="Avoid using a slash (/) to mean 'and/or' as it can be ambiguous.",
                                suggestions=["Clarify the meaning by rewriting the sentence to use 'and', 'or', or 'and or'. For example, instead of 'Insert the CD/DVD', write 'Insert the CD or DVD'."],
                                severity='medium'
                            ))
        return errors
"""
Slashes Rule
Based on IBM Style Guide topic: "Slashes"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class SlashesRule(BasePunctuationRule):
    """
    Checks for the ambiguous use of slashes to mean "and/or", using
    Part-of-Speech tagging to identify the grammatical context.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'punctuation_slashes'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for the ambiguous use of the slash character.
        """
        errors = []
        if not nlp:
            # This rule requires Part-of-Speech tagging for context.
            return errors

        doc = nlp(text)
        for i, sent in enumerate(doc.sents):
            for token in sent:
                # The rule triggers when a slash character is found.
                if token.text == '/':
                    # --- Context-Aware Check ---
                    # To avoid false positives in URLs or file paths, we check the
                    # grammatical context. The ambiguous "and/or" usage typically
                    # occurs between two nouns, adjectives, or proper nouns.
                    if token.i > sent.start and token.i < sent.end - 1:
                        prev_token = doc[token.i - 1]
                        next_token = doc[token.i + 1]
                        
                        # Linguistic Anchor: The pattern for this error is a noun/adjective
                        # followed by a slash, followed by another noun/adjective.
                        is_ambiguous_slash_pattern = (
                            prev_token.pos_ in ["NOUN", "ADJ", "PROPN"] and
                            next_token.pos_ in ["NOUN", "ADJ", "PROPN"]
                        )

                        if is_ambiguous_slash_pattern:
                            flagged_text = f"{prev_token.text}/{next_token.text}"
                            errors.append(self._create_error(
                                sentence=sent.text,
                                sentence_index=i,
                                message="Avoid using a slash (/) to mean 'and/or' as it can be ambiguous.",
                                suggestions=["Clarify the meaning by rewriting the sentence to use 'and', 'or', or 'and or'. For example, instead of 'Insert the CD/DVD', write 'Insert the CD or DVD'."],
                                severity='medium',
                                span=(prev_token.idx, next_token.idx + len(next_token.text)),
                                flagged_text=flagged_text
                            ))
        return errors

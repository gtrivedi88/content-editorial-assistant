"""
Hyphens Rule
Based on IBM Style Guide topics: "Hyphens" and "Prefixes"
"""
from typing import List, Dict, Any
from .base_punctuation_rule import BasePunctuationRule

class HyphensRule(BasePunctuationRule):
    """
    Checks for incorrect hyphenation, focusing on common prefixes that
    the IBM Style Guide specifies should be "closed" (unhyphenated).
    This rule uses linguistic anchors for prefixes and handles documented
    exceptions to reduce false positives.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'hyphens'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for incorrect hyphenation with common prefixes.
        """
        errors = []
        if not nlp:
            # This rule requires tokenization and part-of-speech tagging.
            return errors
        
        # Linguistic Anchor: A set of common prefixes that should be closed
        # (not hyphenated) according to the IBM Style Guide.
        closed_prefixes = {"pre", "post", "multi", "non", "inter", "intra", "re"}

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # The core logic triggers when a hyphen character is found.
                if token.text == '-':
                    # Ensure the hyphen is not at the start or end of the sentence.
                    if token.i > 0 and token.i < len(doc) - 1:
                        prefix_token = doc[token.i - 1]
                        word_token = doc[token.i + 1]
                        
                        # Check if the word before the hyphen is one of our target prefixes.
                        if prefix_token.lemma_ in closed_prefixes:
                            
                            # --- Context-Aware Edge Case Handling ---
                            # These checks prevent false positives by accounting for
                            # specific exceptions mentioned in the style guide.

                            # Exception 1: The prefix 're' is often hyphenated before a
                            # word starting with 'e' to avoid ambiguity (e.g., re-enter).
                            if prefix_token.lemma_ == "re" and word_token.lemma_.startswith("e"):
                                continue 
                            
                            # Exception 2: The prefix 'multi' has specific listed exceptions
                            # where a hyphen is correct (e.g., multi-agent).
                            if prefix_token.lemma_ == "multi" and word_token.lemma_ in ["agent", "core", "instance"]:
                                continue

                            # If no exceptions are met, flag the hyphenated prefix as an error.
                            errors.append(self._create_error(
                                sentence=sentence,
                                sentence_index=i,
                                message=f"Incorrect hyphenation with prefix '{prefix_token.text}'. IBM Style prefers closed prefixes.",
                                suggestions=[f"Consider removing the hyphen to form '{prefix_token.text}{word_token.text}'."],
                                severity='medium'
                            ))
        return errors

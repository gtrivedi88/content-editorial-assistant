"""
Colons Rule
Based on IBM Style Guide topic: "Colons"
"""
from typing import List, Dict, Any
from rules.punctuation.base_punctuation_rule import BasePunctuationRule

class ColonsRule(BasePunctuationRule):
    """
    Checks for incorrect colon usage using dependency parsing to understand
    the colon's grammatical function. It identifies when a colon is used
    incorrectly after an incomplete clause or verb, while ignoring
    legitimate uses like time expressions, ratios, and titles.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'colons'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for various colon usage violations.
        """
        errors = []
        
        # Context-aware analysis: Skip analysis for AsciiDoc attribute entries
        if context and context.get('block_type') == 'attribute_entry':
            return errors  # Skip analysis for attributes like :author: Jane Doe
        
        if not nlp:
            # This rule requires dependency parsing, so NLP is essential.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                if token.text == ':':
                    # First, check if the colon is used in a legitimate context
                    # that we should ignore. This prevents false positives.
                    if self._is_legitimate_context(token, doc):
                        continue

                    # If not a legitimate context, check for common errors.
                    # The main rule: A colon must follow a complete independent clause.
                    if not self._is_preceded_by_complete_clause(token, doc):
                        errors.append(self._create_error(
                            sentence=sentence,
                            sentence_index=i,
                            message="Incorrect colon usage: A colon must be preceded by a complete clause.",
                            suggestions=["Rewrite the text before the colon to form a complete sentence.", "Remove the colon if it is not introducing a list, quote, or explanation."],
                            severity='high'
                        ))

        return errors

    def _is_legitimate_context(self, colon_token, doc) -> bool:
        """
        Uses linguistic anchors to identify legitimate colon contexts that should be ignored.
        This is the primary method for reducing false positives.
        """
        # Linguistic Anchor: Time expressions (e.g., 3:30 PM)
        if colon_token.i > 0 and colon_token.i < len(doc) - 1:
            prev_token = doc[colon_token.i - 1]
            next_token = doc[colon_token.i + 1]
            if prev_token.like_num and next_token.like_num:
                return True # Likely a time or ratio

        # Linguistic Anchor: Technical paths or URLs (e.g., http:)
        if "http" in colon_token.head.text.lower():
            return True

        # Linguistic Anchor: Title/subtitle patterns (e.g., "Chapter 1: Getting Started")
        if colon_token.head.pos_ in ("NOUN", "PROPN") and colon_token.head.is_title:
             if colon_token.i < len(doc) - 1 and doc[colon_token.i + 1].is_title:
                return True

        return False

    def _is_preceded_by_complete_clause(self, colon_token, doc) -> bool:
        """
        Checks if the tokens before the colon form a complete independent clause.
        A complete clause must have a subject and a verb.
        """
        if colon_token.i == 0:
            return False

        # Analyze the part of the sentence before the colon.
        clause_before_colon = doc[:colon_token.i]

        # Linguistic Anchor: A complete clause has a subject and a root verb.
        # We look for a nominal subject ('nsubj') and the main verb of the clause ('ROOT').
        has_subject = any(token.dep_ == 'nsubj' for token in clause_before_colon)
        has_root_verb = any(token.dep_ == 'ROOT' for token in clause_before_colon)
        
        # Also check for a common error pattern: a verb directly preceding the colon.
        verb_before_colon = doc[colon_token.i - 1].pos_ == "VERB"

        # A complete clause has a subject and verb, and doesn't end with the verb
        # that the colon is separating from its object.
        return has_subject and has_root_verb and not verb_before_colon

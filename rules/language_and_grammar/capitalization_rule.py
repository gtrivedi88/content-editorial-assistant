"""
Capitalization Rule (Corrected for False Positives)
Based on IBM Style Guide topic: "Capitalization"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

class CapitalizationRule(BaseLanguageRule):
    """
    Checks for incorrect capitalization, specifically focusing on the
    over-capitalization of common nouns within a sentence, while ignoring
    the correctly capitalized first word.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'capitalization'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences for unnecessary capitalization of common nouns.
        """
        errors = []
        if not nlp:
            return errors

        # This rule is particularly important for 'paragraph', 'list_item', and 'table_cell' blocks.
        block_type = context.get('block_type', 'paragraph') if context else 'paragraph'
        
        # In headings, different rules apply, so we can be less strict here or handle it in a dedicated headings_rule.
        if block_type == 'heading':
            # For now, we'll skip this check on headings to avoid conflicts with headline-style checks.
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            for token in doc:
                # --- Condition 1: Check if the token is a common noun. ---
                # We look for common nouns (NN), not proper nouns (NNP).
                is_common_noun = token.pos_ == 'NOUN' and token.tag_ == 'NN'

                # --- Condition 2: Check if it's capitalized. ---
                # 'is_title' checks for title-case capitalization.
                is_capitalized = token.is_title

                # --- Condition 3 (The Fix): Check that it is NOT the first word. ---
                # The first word of a sentence is always allowed to be capitalized.
                is_not_first_word = token.i > 0

                if is_common_noun and is_capitalized and is_not_first_word:
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Unnecessary capitalization of the common noun '{token.text}'.",
                        suggestions=["Common nouns should be lowercase unless they are part of a proper name or at the beginning of a sentence."],
                        severity='low'
                    ))
        return errors


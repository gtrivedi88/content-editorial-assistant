"""
Procedures Rule
Based on IBM Style Guide topic: "Procedures"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class ProceduresRule(BaseStructureRule):
    """
    Checks for style issues in procedural steps. This rule uses dependency
    parsing to identify procedural contexts and ensures that steps begin
    with an imperative verb, while correctly handling optional and
    conditional steps to reduce false positives.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'procedures'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes list items to check if they are valid procedural steps.
        """
        errors = []
        if not nlp or not context:
            return errors

        # Get block type from context (parsers use 'block_type' key)
        block_type = context.get('block_type', '')
        
        # This rule applies to both ordered and unordered list items
        # since procedures can be in either format
        if block_type not in ['list_item_ordered', 'list_item_unordered', 'list_item']:
            return errors

        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            if not doc:
                continue

            # The core check: does the step start with a command verb?
            if not self._is_valid_procedural_step(doc):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="Procedural steps should begin with a strong, imperative verb.",
                    suggestions=["Rewrite the step to start with a command verb (e.g., 'Click', 'Enter', 'Select')."],
                    severity='medium'
                ))
        return errors

    def _is_valid_procedural_step(self, doc) -> bool:
        """
        Checks if a sentence is a valid procedural step. A valid step either
        starts with an imperative verb or is a valid optional/conditional step.
        """
        if not doc:
            return False
            
        first_token = doc[0]

        # --- Context-Aware Edge Case Handling ---

        # Edge Case 1: Handle optional steps, which are valid.
        # Linguistic Anchor: The word "Optional".
        if first_token.text.lower() == 'optional':
            return True

        # Edge Case 2: Handle conditional steps, which are valid.
        # Linguistic Anchor: The word "If".
        if first_token.lemma_.lower() == 'if':
            return True

        # Main Rule: The step should start with an imperative verb.
        # Linguistic Anchor: In SpaCy's dependency parse, the root of an
        # imperative sentence is the verb itself.
        is_imperative = (first_token.pos_ == 'VERB' and first_token.dep_ == 'ROOT')

        return is_imperative

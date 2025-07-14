"""
Procedures Rule (Modular-Aware)
Based on IBM Style Guide topic: "Procedures"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class ProceduresRule(BaseStructureRule):
    """
    Checks that steps within a Procedure topic begin with an imperative verb.
    This rule is now context-aware and only activates for Procedure topics.
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

        # --- CONTEXT CHECK: Only run this rule inside a Procedure topic ---
        topic_type = context.get('topic_type')
        if topic_type != 'Procedure':
            return errors # Do not run this rule on Concept or Reference topics.

        block_type = context.get('block_type', '')
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
                    message="Steps in a procedure should begin with a strong, imperative verb.",
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

        # Allow optional steps
        if first_token.text.lower() == 'optional':
            return True

        # Allow conditional steps
        if first_token.lemma_.lower() == 'if':
            return True

        # Main Rule: The step should start with an imperative verb.
        is_imperative = (first_token.pos_ == 'VERB' and first_token.dep_ == 'ROOT')

        return is_imperative

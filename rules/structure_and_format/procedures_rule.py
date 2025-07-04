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

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        """
        Analyzes sentences to find and validate procedural steps.
        """
        errors = []
        if not nlp or len(sentences) < 2:
            return errors

        # --- Context-Aware Analysis ---
        # Instead of checking every sentence, we first look for linguistic cues
        # that indicate a procedure is being introduced.
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            
            # If a sentence introduces a procedure, we analyze the *following* sentences as steps.
            if self._is_procedural_lead_in(doc):
                # Analyze the next few sentences as potential steps of the procedure.
                # In a real application, this would be more robust if it could see
                # document structure (like numbered lists).
                steps_to_check = sentences[i+1 : i+4] # Check up to 3 subsequent steps
                for step_index, step_sentence in enumerate(steps_to_check):
                    step_doc = nlp(step_sentence)
                    # The core check: does the step start with a command verb?
                    if not self._is_valid_procedural_step(step_doc):
                        errors.append(self._create_error(
                            sentence=step_sentence,
                            sentence_index=i + 1 + step_index,
                            message="Procedural steps should begin with a strong, imperative verb.",
                            suggestions=["Rewrite the step to start with a command verb (e.g., 'Click', 'Enter', 'Select')."],
                            severity='medium'
                        ))
        return errors

    def _is_procedural_lead_in(self, doc) -> bool:
        """
        Uses linguistic anchors to identify sentences that introduce a procedure.
        """
        sentence_text = doc.text.lower()
        # Linguistic Anchor: Common phrases that introduce a list of steps.
        lead_in_phrases = [
            "complete the following steps",
            "follow these steps",
            "to install the product",
            "to configure the system",
            "perform the following tasks"
        ]
        if any(phrase in sentence_text for phrase in lead_in_phrases):
            return True
        
        # An infinitive phrase at the start of a sentence often introduces a procedure.
        if doc[0].pos_ == "PART" and doc[0].text.lower() == "to" and doc[1].pos_ == "VERB":
            return True

        return False

    def _is_valid_procedural_step(self, doc) -> bool:
        """

        Checks if a sentence is a valid procedural step. A valid step either
        starts with an imperative verb or is a valid optional/conditional step.
        """
        first_token = doc[0]

        # Edge Case 1: Handle optional steps, which are valid.
        if first_token.text.lower() == 'optional':
            return True

        # Edge Case 2: Handle conditional steps, which are valid.
        if first_token.lemma_.lower() == 'if':
            return True

        # Main Rule: The step should start with an imperative verb.
        # Linguistic Anchor: In SpaCy's dependency parse, the root of an
        # imperative sentence is the verb itself.
        is_imperative = (first_token.pos_ == 'VERB' and first_token.dep_ == 'ROOT')

        return is_imperative

"""
Notes Rule
Based on IBM Style Guide topic: "Notes"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class NotesRule(BaseStructureRule):
    """
    Checks for style issues within admonition blocks (like [NOTE], [WARNING]).
    This rule verifies the use of correct labels and ensures the content is
    a complete sentence for clarity.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'notes'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the content of a block identified by the parser as an 'admonition'.
        """
        errors = []
        # This rule only applies to blocks explicitly parsed as admonitions.
        if not nlp or not context or context.get('block_type') != 'admonition':
            return errors

        admonition_kind = context.get('kind', '').upper()
        
        # --- Rule 1: Check for Valid Admonition Labels ---
        # Linguistic Anchor: A set of approved labels from the IBM Style Guide.
        approved_labels = {
            'NOTE', 'IMPORTANT', 'RESTRICTION', 'TIP', 'ATTENTION', 
            'CAUTION', 'DANGER', 'REQUIREMENT', 'EXCEPTION', 'FAST PATH', 'REMEMBER'
        }

        if admonition_kind and admonition_kind not in approved_labels:
            errors.append(self._create_error(
                sentence=text,
                sentence_index=0,
                message=f"Invalid admonition label '[{admonition_kind}]' used.",
                suggestions=[f"Use one of the approved labels from the IBM Style Guide, such as 'NOTE', 'IMPORTANT', or 'WARNING'."],
                severity='medium'
            ))

        # --- Rule 2: Check if Admonition Content is a Complete Sentence ---
        # The content of a note should be a clear, complete thought.
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            if not self._is_complete_sentence(doc):
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i,
                    message="The content of the note may not be a complete sentence.",
                    suggestions=["Ensure the text within the note forms a complete, standalone sentence for clarity."],
                    severity='low'
                ))

        return errors

    def _is_complete_sentence(self, doc) -> bool:
        """
        Uses dependency parsing to check if the text forms a complete sentence.
        A complete sentence must have a root and typically a subject.
        """
        if not doc or len(doc) < 2:
            return False
            
        # Linguistic Anchor: A complete sentence has a root verb.
        has_root = any(token.dep_ == 'ROOT' for token in doc)
        
        # Check for a subject, which is typical for a complete sentence.
        has_subject = any(token.dep_ in ('nsubj', 'nsubjpass', 'csubj') for token in doc)
        
        # Imperative sentences (common in notes) might not have an explicit subject,
        # but their root is a verb.
        is_imperative = doc[0].pos_ == 'VERB' and doc[0].dep_ == 'ROOT'

        return has_root and (has_subject or is_imperative)

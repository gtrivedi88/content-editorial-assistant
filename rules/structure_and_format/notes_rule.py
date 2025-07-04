"""
Notes Rule
Based on IBM Style Guide topic: "Notes"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class NotesRule(BaseStructureRule):
    """
    Checks for correct formatting of notes, such as ensuring the
    label is followed by a colon.
    """
    def _get_rule_type(self) -> str:
        return 'notes'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Linguistic Anchor: Common labels for notes.
        note_labels = {'Note', 'Important', 'Restriction', 'Tip', 'Attention', 'Requirement', 'Exception', 'Fast path', 'Remember'}

        for i, sentence in enumerate(sentences):
            words = sentence.split()
            # Check if the first word is a known note label.
            if len(words) > 1 and words[0] in note_labels:
                # Rule: The label should be followed by a colon.
                if not words[0].endswith(':'):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"The note label '{words[0]}' should be followed by a colon.",
                        suggestions=[f"Add a colon after the label: '{words[0]}:'."],
                        severity='low'
                    ))
        return errors


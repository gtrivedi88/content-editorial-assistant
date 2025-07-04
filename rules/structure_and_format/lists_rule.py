"""
Lists Rule
Based on IBM Style Guide topic: "Lists"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class ListsRule(BaseStructureRule):
    """
    Checks for style issues in lists, with a focus on ensuring
    grammatical parallelism between list items.
    """
    def _get_rule_type(self) -> str:
        return 'lists'

    def analyze(self, text: str, sentences: List[str], nlp=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp or len(sentences) < 2:
            return errors

        # This rule assumes that a sequence of short, related sentences forms a list.
        # A more advanced system would use document structure (like Markdown list markers).
        
        # Check for parallelism by comparing the part-of-speech of the first word.
        first_item_pos = nlp(sentences[0])[0].pos_
        
        for i, sentence in enumerate(sentences[1:]):
            doc = nlp(sentence)
            if not doc: continue
            current_item_pos = doc[0].pos_
            
            # Linguistic Anchor: Parallel items should start with the same part of speech
            # (e.g., all verbs for a procedure, all nouns for a list of features).
            if current_item_pos != first_item_pos:
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i + 1,
                    message="List items may not be grammatically parallel.",
                    suggestions=[f"Ensure all items in a list start with the same part of speech. The first item appears to be a '{first_item_pos}', while this item appears to be a '{current_item_pos}'."],
                    severity='medium'
                ))
        return errors
"""
Lists Rule
Based on IBM Style Guide topic: "Lists"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

class ListsRule(BaseStructureRule):
    """
    Checks for style issues in lists, with a focus on ensuring
    grammatical parallelism between list items. This rule analyzes all
    items in a list block to ensure they share a consistent structure.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'lists'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes a block of list items for grammatical parallelism.
        
        This method assumes it receives all items of a single list in the
        `sentences` argument, which is made possible by the structural parser.
        """
        errors = []
        
        # This rule requires at least two list items to compare for parallelism.
        if not nlp or len(sentences) < 2:
            return errors

        # --- Consolidated Parallelism Analysis ---
        
        # 1. Establish the grammatical pattern from the first list item.
        first_item_doc = nlp(sentences[0])
        if not first_item_doc:
            return [] # Cannot establish a pattern if the first item is empty.
        
        # Linguistic Anchor: The Part-of-Speech of the first token sets the pattern.
        pattern_pos = first_item_doc[0].pos_

        # 2. Iterate through the rest of the list items and check for any deviation.
        for i, sentence in enumerate(sentences[1:]):
            doc = nlp(sentence)
            if not doc: continue
            
            current_item_pos = doc[0].pos_
            
            # 3. If any item's POS doesn't match the established pattern, flag ONE error and stop.
            if current_item_pos != pattern_pos:
                return [self._create_error(
                    sentence=text, # Report the error on the whole block of text
                    sentence_index=0, 
                    message="List items are not grammatically parallel.",
                    suggestions=[f"The first item starts with a '{pattern_pos}', but a later item starts with a '{current_item_pos}'. Please rewrite the items to have a consistent grammatical structure."],
                    severity='medium'
                )]
        
        # If the loop completes without finding any non-parallel items, return no errors.
        return []

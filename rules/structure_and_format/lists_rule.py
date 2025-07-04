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

        # --- Parallelism Analysis ---
        
        # 1. Establish the grammatical pattern from the first list item.
        #    The "pattern" is the Part-of-Speech of the first word (e.g., NOUN, VERB).
        first_item_doc = nlp(sentences[0])
        if not first_item_doc:
            return errors # Cannot establish a pattern if the first item is empty.
        
        # Linguistic Anchor: The Part-of-Speech of the first token sets the pattern.
        pattern_pos = first_item_doc[0].pos_

        # 2. Iterate through the rest of the list items and compare them to the pattern.
        for i, sentence in enumerate(sentences[1:]):
            doc = nlp(sentence)
            if not doc: continue
            
            current_item_pos = doc[0].pos_
            
            # 3. If the POS of the current item doesn't match the established pattern,
            #    it's a parallelism error.
            if current_item_pos != pattern_pos:
                errors.append(self._create_error(
                    sentence=sentence,
                    # The sentence_index needs to be offset by 1 because we start from the second item.
                    sentence_index=i + 1, 
                    message="List items are not grammatically parallel.",
                    suggestions=[f"This item appears to start with a '{current_item_pos}', but the list's pattern was established as '{pattern_pos}' by the first item. Please rewrite the items to have a consistent structure."],
                    severity='medium'
                ))
        
        return errors
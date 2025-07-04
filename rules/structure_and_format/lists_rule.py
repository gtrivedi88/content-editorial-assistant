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

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        
        # Context-aware analysis: Only analyze if we know this is a list item
        if not context or context.get('block_type') not in ['list_item', 'list_item_ordered', 'list_item_unordered']:
            return errors  # Skip analysis if not a list item
            
        if not nlp or len(sentences) < 1:
            return errors

        # Since we know this is a list item, we can focus on analyzing the content
        # rather than trying to detect if it's a list
        
        # For now, we'll store the first item's structure to compare with subsequent items
        # This would ideally be done at the document level, but for now we'll implement
        # a simplified version that works with the current sentence-by-sentence analysis
        
        # Rule: List items should be grammatically parallel
        # This rule is most effective when applied across multiple list items
        # Since we're analyzing individual list items, we'll focus on internal consistency
        
        for i, sentence in enumerate(sentences):
            doc = nlp(sentence)
            if not doc: continue
            
            # Check if list item has consistent structure
            # For example, if it starts with a verb, it should maintain that pattern
            first_token = doc[0]
            
            # Rule: List items should not mix different grammatical structures
            # This is a simplified check - a full implementation would compare across all items
            if first_token.pos_ == 'VERB' and first_token.dep_ == 'ROOT':
                # This is an imperative-style list item
                # Check if it maintains consistent imperative structure
                if any(token.pos_ == 'PRON' and token.dep_ == 'nsubj' for token in doc):
                    errors.append(self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message="List item mixes imperative and declarative styles.",
                        suggestions=["Maintain consistent grammatical structure across list items. Use either all imperative verbs or all declarative statements."],
                        severity='medium'
                    ))
        
        return errors
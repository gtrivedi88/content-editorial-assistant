"""
Lists Rule (Modular-Ready)
Based on IBM Style Guide topic: "Lists"
"""
from typing import List, Dict, Any, Optional
from .base_structure_rule import BaseStructureRule

class ListsRule(BaseStructureRule):
    """
    Checks for style issues in lists, with a focus on ensuring
    grammatical parallelism between list items. This rule is inherently
    compatible with the modular documentation strategy.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'lists'

    def _get_grammatical_form(self, doc: Any) -> str:
        """
        Analyzes a SpaCy doc object and determines its grammatical form.
        This logic correctly distinguishes between sentences, commands, etc.
        """
        if not doc or len(doc) == 0:
            return "EMPTY"

        # Check for imperative form (correct for Procedure topics)
        if doc[0].pos_ == 'VERB' and doc[0].tag_ == 'VB':
            return "IMPERATIVE_PHRASE"
            
        # Check for gerund phrase
        if doc[0].pos_ == 'VERB' and doc[0].tag_ == 'VBG':
            return "GERUND_PHRASE"

        # Check if it's a full declarative sentence (common in Concept topics)
        has_subject = any(token.dep_ in ('nsubj', 'nsubjpass') for token in doc)
        if has_subject:
            return "SENTENCE"

        # Default to noun phrase (common in Reference topics)
        return "NOUN_PHRASE"


    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes a block of list items for grammatical parallelism.
        This method works universally across all topic types because it
        infers the required pattern from the first item.
        """
        if not nlp or len(sentences) < 2:
            return []
        
        first_item_doc = nlp(sentences[0])
        if not first_item_doc:
            return []
        
        pattern_form = self._get_grammatical_form(first_item_doc)
        
        for i, sentence in enumerate(sentences[1:]):
            doc = nlp(sentence)
            if not doc:
                continue
            
            current_item_form = self._get_grammatical_form(doc)
            
            if current_item_form != pattern_form:
                return [self._create_error(
                    sentence=text,
                    sentence_index=0, 
                    message="List items are not grammatically parallel.",
                    suggestions=[f"The first list item appears to be a '{pattern_form}', but a later item is a '{current_item_form}'. Please rewrite all items to have a consistent grammatical structure."],
                    severity='high'
                )]
        
        return []

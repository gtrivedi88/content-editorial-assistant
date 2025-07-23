"""
Lists Rule (Modular-Ready)
Based on IBM Style Guide topic: "Lists"
"""
from typing import List, Dict, Any
from .base_structure_rule import BaseStructureRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ListsRule(BaseStructureRule):
    """
    Checks for style issues in lists, with a focus on ensuring
    grammatical parallelism between list items.
    """
    def _get_rule_type(self) -> str:
        """Returns the unique identifier for this rule."""
        return 'structure_format_lists'

    def _get_grammatical_form(self, doc: Doc) -> str:
        """
        Analyzes a SpaCy doc object and determines its grammatical form.
        """
        if not doc or len(doc) == 0:
            return "EMPTY"

        # Linguistic Anchors for different grammatical forms
        if doc[0].pos_ == 'VERB' and doc[0].tag_ == 'VB':
            return "Imperative Phrase"
        if doc[0].pos_ == 'VERB' and doc[0].tag_ == 'VBG':
            return "Gerund Phrase"
        if any(token.dep_ in ('nsubj', 'nsubjpass') for token in doc):
            return "Sentence"
        return "Noun Phrase"

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes a block of list items for grammatical parallelism.
        """
        errors = []
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
                errors.append(self._create_error(
                    sentence=sentence,
                    sentence_index=i + 1,
                    message="List items are not grammatically parallel.",
                    suggestions=[f"The first list item is a '{pattern_form}', but this item is a '{current_item_form}'. Rewrite all items to have a consistent grammatical structure."],
                    severity='high',
                    span=(0, len(sentence)),
                    flagged_text=sentence
                ))
        
        return errors

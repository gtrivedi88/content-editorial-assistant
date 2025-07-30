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
        return 'lists'

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

        # CRITICAL FIX: Skip lists analysis for individual list items to prevent false positives
        if context and context.get('exclude_list_rules'):
            return []

        # ENTERPRISE CONTEXT INTELLIGENCE: Check if this is parallelism analysis only
        if context and context.get('parallelism_analysis_only'):
            # Only check parallelism, skip other list-related rules
            return self._analyze_parallelism_only(sentences, nlp)
        
        # ENTERPRISE CONTEXT INTELLIGENCE: Check if lists rules should apply
        content_classification = self._get_content_classification(text, context, nlp)
        should_apply = self._should_apply_rule(self._get_rule_category(), content_classification)
        
        if not should_apply:
            return errors
        
        return self._analyze_parallelism_only(sentences, nlp)
    
    def _analyze_parallelism_only(self, sentences: List[str], nlp) -> List[Dict[str, Any]]:
        """Analyze only grammatical parallelism to prevent rule duplication."""
        errors = []
        
        first_item_doc = nlp(sentences[0])
        if not first_item_doc:
            return []
        
        pattern_form = self._get_grammatical_form(first_item_doc)
        non_parallel_items = []
        
        for i, sentence in enumerate(sentences[1:]):
            doc = nlp(sentence)
            if not doc:
                continue
            
            current_item_form = self._get_grammatical_form(doc)
            
            if current_item_form != pattern_form:
                non_parallel_items.append({
                    'index': i + 1,
                    'text': sentence,
                    'form': current_item_form
                })
        
        # Create a single consolidated error if there are non-parallel items
        if non_parallel_items:
            # Determine which items to highlight - use the first non-parallel item
            first_non_parallel = non_parallel_items[0]
            
            # Create a comprehensive suggestion that covers all non-parallel items
            if len(non_parallel_items) == 1:
                suggestion = f"The first list item is a '{pattern_form}', but this item is a '{first_non_parallel['form']}'. Rewrite all items to have a consistent grammatical structure."
            else:
                forms_found = set(item['form'] for item in non_parallel_items)
                forms_list = "', '".join(forms_found)
                suggestion = f"The first list item is a '{pattern_form}', but other items use different forms: '{forms_list}'. Rewrite all items to have a consistent grammatical structure."
            
            errors.append(self._create_error(
                sentence=first_non_parallel['text'],
                sentence_index=first_non_parallel['index'],
                message="List items are not grammatically parallel.",
                suggestions=[suggestion],
                severity='high',
                span=(0, len(first_non_parallel['text'])),
                flagged_text=first_non_parallel['text']
            ))
        
        return errors

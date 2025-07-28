"""
Conjunctions Rule (Enhanced for Accuracy)
Based on IBM Style Guide topic: "Conjunctions"
"""
from typing import List, Dict, Any
from .base_language_rule import BaseLanguageRule

try:
    from spacy.tokens import Doc
except ImportError:
    Doc = None

class ConjunctionsRule(BaseLanguageRule):
    """
    Checks for conjunction-related issues, including accurate comma splice detection.
    """
    def _get_rule_type(self) -> str:
        return 'conjunctions'

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        errors = []
        if not nlp:
            return errors
        
        for i, sent_text in enumerate(sentences):
            if not sent_text.strip() or ',' not in sent_text:
                continue
            
            doc = nlp(sent_text)

            # --- PRIORITY 1 FIX: High-Accuracy Comma Splice Detection ---
            # This logic checks for a comma that connects two independent clauses.
            # It does this by looking for a comma token where both its head and a child
            # are verbs, which is a strong indicator of a comma splice.
            for token in doc:
                if token.text == ',':
                    # Check if the comma is connecting two verbs (potential clauses)
                    head = token.head
                    children = [child for child in token.children if child.pos_ == 'VERB']
                    
                    if head.pos_ == 'VERB' and len(children) > 0:
                        # Further check: ensure there's no coordinating conjunction
                        if not any(child.dep_ == 'cc' for child in head.children):
                             errors.append(self._create_error(
                                sentence=sent_text,
                                sentence_index=i,
                                message="Potential comma splice: two independent clauses may be joined by only a comma.",
                                suggestions=["Use a period to create two separate sentences, use a semicolon, or add a coordinating conjunction (like 'and', 'but', 'or')."],
                                severity='medium',
                                flagged_text=sent_text
                            ))
                             # Break after finding one potential splice per sentence to avoid noise
                             break
        return errors

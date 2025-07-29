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

            # --- IMPROVED COMMA SPLICE DETECTION ---
            # Look for commas that separate independent clauses
            comma_splice_detected = self._detect_comma_splice(doc, sent_text)
            if comma_splice_detected:
                errors.append(self._create_error(
                    sentence=sent_text,
                    sentence_index=i,
                    message="Comma splice detected: two independent clauses are joined by only a comma.",
                    suggestions=["Use a period to create two separate sentences, use a semicolon, or add a coordinating conjunction (like 'and', 'but', 'or')."],
                    severity='medium',
                    flagged_text=sent_text
                ))
        return errors
    
    def _detect_comma_splice(self, doc, sent_text: str) -> bool:
        """
        Improved comma splice detection that looks for independent clauses on both sides of a comma.
        """
        # Find comma positions
        comma_positions = []
        for token in doc:
            if token.text == ',':
                comma_positions.append(token.i)
        
        if not comma_positions:
            return False
        
        for comma_idx in comma_positions:
            comma_token = doc[comma_idx]
            
            # Skip if this comma is part of a list or has coordinating conjunction nearby
            if self._is_list_comma(doc, comma_idx) or self._has_coordinating_conjunction_nearby(doc, comma_idx):
                continue
            
            # Check for independent clauses on both sides of the comma
            left_clause = self._has_independent_clause_before(doc, comma_idx)
            right_clause = self._has_independent_clause_after(doc, comma_idx)
            
            if left_clause and right_clause:
                return True
        
        return False
    
    def _has_independent_clause_before(self, doc, comma_idx: int) -> bool:
        """Check if there's an independent clause before the comma."""
        # Look for a verb (VERB or AUX) with a subject before the comma
        for i in range(comma_idx - 1, -1, -1):
            token = doc[i]
            if token.pos_ in ['VERB', 'AUX']:
                # Check if this verb has a subject
                if self._has_subject(token):
                    return True
        return False
    
    def _has_independent_clause_after(self, doc, comma_idx: int) -> bool:
        """Check if there's an independent clause after the comma."""
        # Look for a verb (VERB or AUX) with a subject after the comma
        for i in range(comma_idx + 1, len(doc)):
            token = doc[i]
            if token.pos_ in ['VERB', 'AUX']:
                # Check if this verb has a subject
                if self._has_subject(token):
                    return True
        return False
    
    def _has_subject(self, verb_token) -> bool:
        """Check if a verb has a subject, indicating it's part of an independent clause."""
        # Look for nsubj (nominal subject) or nsubjpass (passive nominal subject) dependencies
        for child in verb_token.children:
            if child.dep_ in ['nsubj', 'nsubjpass']:
                return True
        
        # Also check if the verb itself is a subject of another verb (for complex structures)
        if verb_token.dep_ in ['nsubj', 'nsubjpass']:
            return True
            
        return False
    
    def _is_list_comma(self, doc, comma_idx: int) -> bool:
        """Check if this comma is part of a list (not a comma splice)."""
        # Simple heuristic: if there are multiple commas or conjunctions nearby, likely a list
        comma_count = sum(1 for token in doc if token.text == ',')
        if comma_count > 1:
            return True
        
        # Check for list patterns like "A, B, and C"
        if comma_idx + 2 < len(doc):
            next_token = doc[comma_idx + 1]
            next_next_token = doc[comma_idx + 2]
            if next_token.text.lower() in ['and', 'or'] or next_next_token.text.lower() in ['and', 'or']:
                return True
        
        return False
    
    def _has_coordinating_conjunction_nearby(self, doc, comma_idx: int) -> bool:
        """Check if there's a coordinating conjunction near the comma."""
        # Check a few tokens before and after the comma
        for i in range(max(0, comma_idx - 2), min(len(doc), comma_idx + 3)):
            if i != comma_idx and doc[i].pos_ == 'CCONJ':  # Coordinating conjunction
                return True
        return False

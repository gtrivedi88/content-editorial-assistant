"""
Base Punctuation Rule
A base class that all specific punctuation rules will inherit from.
This ensures a consistent interface for all rules.
"""

from typing import List, Dict, Any, Optional

# A generic base rule to be inherited from a central location
# in a real application. The # type: ignore comments prevent the
# static type checker from getting confused by the fallback class.
try:
    from ..base_rule import BaseRule  # type: ignore
except ImportError:
    class BaseRule:  # type: ignore
        def _get_rule_type(self) -> str:
            return 'base'
        def _create_error(self, sentence: str, sentence_index: int, message: str, 
                         suggestions: List[str], severity: str = 'medium', 
                         text: Optional[str] = None, context: Optional[Dict[str, Any]] = None,
                         **extra_data) -> Dict[str, Any]:
            """Fallback _create_error implementation when main BaseRule import fails."""
            # Create basic error structure for fallback scenarios
            error = {
                'type': getattr(self, 'rule_type', 'unknown'),
                'message': str(message),
                'suggestions': [str(s) for s in suggestions],
                'sentence': str(sentence),
                'sentence_index': int(sentence_index),
                'severity': severity,
                'enhanced_validation_available': False  # Mark as fallback
            }
            
            # Add required Level 2 Enhanced Validation fields
            if text is not None:
                error['text'] = text
            if context is not None:
                error['context'] = context
            
            # Add any extra data
            error.update(extra_data)
            return error


class BasePunctuationRule(BaseRule):
    """
    Abstract base class for all punctuation rules.
    Enhanced with evidence-based analysis methods and common punctuation context clues.
    """

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for a specific punctuation violation.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement the analyze method.")

    # === COMMON PUNCTUATION EVIDENCE METHODS ===

    def _apply_zero_false_positive_guards_punctuation(self, token, context: Dict[str, Any]) -> bool:
        """
        Apply surgical zero false positive guards for punctuation rules.
        Returns True if token should be ignored (no evidence).
        """
        # Code blocks have different punctuation rules
        if context and context.get('block_type') in ['code_block', 'inline_code', 'literal_block']:
            return True
        
        # URLs and file paths have their own punctuation
        if hasattr(token, 'like_url') and token.like_url:
            return True
        
        # Don't flag punctuation in technical identifiers
        if hasattr(token, 'text') and ('/' in token.text or '\\' in token.text):
            return True
        
        # Email addresses have their own punctuation rules
        if hasattr(token, 'like_email') and token.like_email:
            return True
        
        return False

    def _apply_common_linguistic_clues_punctuation(self, evidence_score: float, token, sentence) -> float:
        """
        Apply common linguistic clues for punctuation analysis.
        """
        # Punctuation at sentence boundaries is usually correct
        if hasattr(token, 'is_sent_start') and token.is_sent_start:
            evidence_score -= 0.2
        if hasattr(token, 'is_sent_end') and token.is_sent_end:
            evidence_score -= 0.2
        
        # Punctuation in quotes often follows different rules
        if self._is_token_in_quotes(token, sentence):
            evidence_score -= 0.1
        
        return evidence_score

    def _apply_common_structural_clues_punctuation(self, evidence_score: float, token, context: Dict[str, Any]) -> float:
        """
        Apply common structural clues for punctuation analysis.
        """
        block_type = context.get('block_type', 'paragraph')
        
        # Headings may have different punctuation conventions
        if block_type in ['heading', 'title']:
            evidence_score -= 0.2
        
        # Lists may use punctuation differently
        elif block_type in ['ordered_list_item', 'unordered_list_item']:
            evidence_score -= 0.1
        
        # Tables often abbreviate and use different punctuation
        elif block_type in ['table_cell', 'table_header']:
            evidence_score -= 0.1
        
        # Citations and references may follow different rules
        elif block_type in ['citation', 'reference', 'bibliography']:
            evidence_score -= 0.1
        
        return evidence_score

    def _apply_common_semantic_clues_punctuation(self, evidence_score: float, token, context: Dict[str, Any]) -> float:
        """
        Apply common semantic clues for punctuation analysis.
        """
        content_type = context.get('content_type', 'general')
        
        # Technical writing may use punctuation differently
        if content_type == 'technical':
            evidence_score -= 0.1
        
        # Academic writing has specific punctuation conventions
        elif content_type == 'academic':
            evidence_score -= 0.05
        
        # Legal writing is very strict about punctuation
        elif content_type == 'legal':
            evidence_score += 0.1
        
        return evidence_score

    def _is_token_in_quotes(self, token, sentence) -> bool:
        """
        Check if a token appears within quotation marks.
        """
        if not hasattr(sentence, '__iter__'):
            return False
        
        token_idx = getattr(token, 'i', -1)
        if token_idx == -1:
            return False
        
        # Look for quote pairs around the token
        quote_chars = ['"', "'", '"', '"', ''', ''']
        in_quotes = False
        
        for sent_token in sentence:
            if hasattr(sent_token, 'text') and sent_token.text in quote_chars:
                in_quotes = not in_quotes
            elif hasattr(sent_token, 'i') and sent_token.i == token_idx:
                return in_quotes
        
        return False

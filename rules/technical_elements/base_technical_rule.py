"""
Base Technical Elements Rule
A base class that all specific technical element rules will inherit from.
This ensures a consistent interface for all rules in this category.
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
            # Add any extra data
            error.update(extra_data)
            return error


class BaseTechnicalRule(BaseRule):
    """
    Abstract base class for all technical element rules.
    It defines the common interface for analyzing text.
    """

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for a specific technical element violation.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement the analyze method.")

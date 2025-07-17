"""
Base Word Usage Rule
A base class that all specific word usage rules will inherit from.
"""

from typing import List, Dict, Any

# A generic base rule to be inherited from a central location
# in a real application. The # type: ignore comments prevent the
# static type checker from getting confused by the fallback class.
try:
    from ..base_rule import BaseRule  # type: ignore
except ImportError:
    class BaseRule:  # type: ignore
        def _get_rule_type(self) -> str:
            return 'base'
        def _create_error(self, **kwargs) -> Dict[str, Any]:
            return kwargs


class BaseWordUsageRule(BaseRule):
    """
    Abstract base class for all word usage rules.
    It defines the common interface for analyzing text for specific word violations.
    """

    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """
        Analyzes the text for specific word usage violations.
        This method must be implemented by all subclasses.
        """
        raise NotImplementedError("Subclasses must implement the analyze method.")

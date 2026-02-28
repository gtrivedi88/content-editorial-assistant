"""
Base Legal Information Rule
Abstract base class that all legal/compliance rules inherit from.
"""
from typing import List, Dict, Any, Optional

try:
    from ..base_rule import BaseRule  # type: ignore
except ImportError:
    class BaseRule:  # type: ignore
        def _get_rule_type(self) -> str:
            return 'base'

        def _create_error(self, sentence: str, sentence_index: int, message: str,
                          suggestions: List[str], severity: str = 'medium',
                          text: Optional[str] = None,
                          context: Optional[Dict[str, Any]] = None,
                          **extra_data) -> Dict[str, Any]:
            """Fallback _create_error when main BaseRule import fails."""
            error = {
                'type': getattr(self, 'rule_type', 'unknown'),
                'message': str(message),
                'suggestions': [str(s) for s in suggestions],
                'sentence': str(sentence),
                'sentence_index': int(sentence_index),
                'severity': severity,
            }
            error.update(extra_data)
            return error


class BaseLegalRule(BaseRule):
    """Abstract base class for all legal information rules."""

    def analyze(self, text: str, sentences: List[str], nlp=None,
                context=None, spacy_doc=None) -> List[Dict[str, Any]]:
        """Analyze text for legal/compliance violations."""
        raise NotImplementedError("Subclasses must implement the analyze method.")

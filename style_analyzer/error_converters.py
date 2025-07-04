"""
Error Conversion Utilities
Handles conversion between different error formats used in the style analyzer.
"""

import logging
from typing import Dict, Any

from .base_types import ErrorDict, AnalysisMethod, create_error

logger = logging.getLogger(__name__)


class ErrorConverter:
    """Utility class for converting between different error formats."""
    
    @staticmethod
    def convert_rules_error(rules_error: Dict[str, Any]) -> ErrorDict:
        """Convert rules system error to our standardized error format."""
        try:
            # Extract information from rules error
            error_type = rules_error.get('type', 'unknown')
            message = rules_error.get('message', 'Unknown error')
            suggestions = rules_error.get('suggestions', [])
            severity = rules_error.get('severity', 'low')
            sentence = rules_error.get('sentence', '')
            sentence_index = rules_error.get('sentence_index', -1)
            
            # Create standardized error
            return create_error(
                error_type=error_type,
                message=message,
                suggestions=suggestions,
                severity=severity,
                sentence=sentence,
                sentence_index=sentence_index,
                confidence=0.85,  # High confidence for rules-based detection
                analysis_method=AnalysisMethod.SPACY_ENHANCED
            )
        except Exception as e:
            logger.error(f"Error converting rules error: {e}")
            return create_error(
                error_type='system',
                message=f'Error processing rule: {str(e)}',
                suggestions=['Check rule implementation']
            ) 
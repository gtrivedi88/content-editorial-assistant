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
            subtype = rules_error.get('subtype')  # Preserve subtype for ambiguity errors
            message = rules_error.get('message', 'Unknown error')
            suggestions = rules_error.get('suggestions', [])
            severity = rules_error.get('severity', 'low')
            sentence = rules_error.get('sentence', '')
            sentence_index = rules_error.get('sentence_index', -1)
            
            # Create standardized error with all fields preserved
            error_dict = {
                'type': error_type,
                'message': message,
                'suggestions': suggestions,
                'severity': severity,
                'confidence': 0.85,  # High confidence for rules-based detection
                'analysis_method': 'spacy_enhanced'
            }
            
            # Add optional fields if provided
            if sentence:
                error_dict['sentence'] = sentence
            if sentence_index >= 0:
                error_dict['sentence_index'] = sentence_index
            if subtype:
                error_dict['subtype'] = subtype
            
            # Preserve any additional fields from the original error
            for key, value in rules_error.items():
                if key not in error_dict and key not in ['type', 'subtype', 'message', 'suggestions', 'severity', 'sentence', 'sentence_index']:
                    error_dict[key] = value
            
            return error_dict
        except Exception as e:
            logger.error(f"Error converting rules error: {e}")
            return create_error(
                error_type='system',
                message=f'Error processing rule: {str(e)}',
                suggestions=['Check rule implementation']
            ) 
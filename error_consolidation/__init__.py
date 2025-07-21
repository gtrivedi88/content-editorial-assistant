"""
Error Consolidation System

A comprehensive system for consolidating overlapping and duplicate style errors
to provide cleaner, more actionable feedback to users.

This system addresses the issue where multiple rules detect the same text spans
and create duplicate or conflicting error messages.
"""

from .consolidator import ErrorConsolidator
from .text_span_analyzer import TextSpanAnalyzer
from .rule_priority import RulePriorityManager
from .message_merger import MessageMerger

__version__ = "1.0.0"

__all__ = [
    'ErrorConsolidator',
    'TextSpanAnalyzer', 
    'RulePriorityManager',
    'MessageMerger'
]

# Convenience function for easy integration
def consolidate_errors(errors, priority_config=None):
    """
    Consolidate a list of errors using the default configuration.
    
    Args:
        errors: List of error dictionaries to consolidate
        priority_config: Optional custom priority configuration
        
    Returns:
        List of consolidated error dictionaries
    """
    consolidator = ErrorConsolidator(priority_config)
    return consolidator.consolidate(errors) 
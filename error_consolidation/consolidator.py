"""
Error Consolidator

Main class that orchestrates the error consolidation process by analyzing text spans,
applying rule priorities, and merging overlapping/duplicate errors into consolidated
error messages.
"""

from typing import List, Dict, Any, Optional, Set
from .text_span_analyzer import TextSpanAnalyzer, SpanGroup
from .rule_priority import RulePriorityManager  
from .message_merger import MessageMerger


class ErrorConsolidator:
    """
    Main consolidator that coordinates the error consolidation process.
    """
    
    def __init__(self, priority_config_path: Optional[str] = None):
        """
        Initialize the error consolidator.
        
        Args:
            priority_config_path: Optional path to custom priority configuration
        """
        self.span_analyzer = TextSpanAnalyzer()
        self.priority_manager = RulePriorityManager(priority_config_path)
        self.message_merger = MessageMerger()
        
        # Statistics for analysis
        self.stats = {
            'total_errors_input': 0,
            'total_errors_output': 0,
            'consolidation_groups': 0,
            'errors_merged': 0
        }
    
    def consolidate(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidate overlapping and duplicate errors into cleaner error messages.
        
        Args:
            errors: List of error dictionaries from style analysis
            
        Returns:
            List of consolidated error dictionaries
        """
        if not errors:
            return []
        
        # Reset statistics
        self.stats['total_errors_input'] = len(errors)
        self.stats['consolidation_groups'] = 0
        self.stats['errors_merged'] = 0
        
        # Step 1: Add text spans to errors and identify consolidation opportunities
        errors_with_spans = self._prepare_errors_for_analysis(errors)
        
        # Step 2: Analyze text spans to find overlapping/related groups
        span_groups = self.span_analyzer.analyze_spans(errors_with_spans)
        self.stats['consolidation_groups'] = len(span_groups)
        
        # Step 3: Consolidate errors within each group
        consolidated_errors = self._consolidate_span_groups(span_groups, errors_with_spans)
        
        # Step 4: Add any non-consolidated errors (those not in any group)
        unconsolidated_errors = self._get_unconsolidated_errors(span_groups, errors_with_spans)
        consolidated_errors.extend(unconsolidated_errors)
        
        # Step 5: Sort final errors by sentence position and severity
        final_errors = self._sort_and_finalize_errors(consolidated_errors)
        
        self.stats['total_errors_output'] = len(final_errors)
        self.stats['errors_merged'] = self.stats['total_errors_input'] - self.stats['total_errors_output']
        
        return final_errors
    
    def get_consolidation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the last consolidation operation.
        
        Returns:
            Dictionary with consolidation statistics
        """
        return self.stats.copy()
    
    def _prepare_errors_for_analysis(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare errors for span analysis by ensuring required fields."""
        prepared_errors = []
        
        for i, error in enumerate(errors):
            prepared_error = error.copy()
            
            # Ensure error has an ID for tracking
            if 'error_id' not in prepared_error:
                prepared_error['error_id'] = f"error_{i}"
            
            # Extract and store text segment if not already present
            if 'text_segment' not in prepared_error:
                text_segment = self._extract_text_segment_from_error(prepared_error)
                if text_segment:
                    prepared_error['text_segment'] = text_segment
            
            prepared_errors.append(prepared_error)
        
        return prepared_errors
    
    def _extract_text_segment_from_error(self, error: Dict[str, Any]) -> str:
        """Extract problematic text segment from error message or other fields."""
        # Look for various possible fields containing the problematic text
        for field in ['text_segment', 'segment', 'problematic_text', 'matched_text']:
            if field in error and error[field]:
                return str(error[field]).strip()
        
        # Try to extract from message using common patterns
        message = error.get('message', '')
        
        # Pattern: "Problematic X: 'text'" or "X: 'text'"
        import re
        match = re.search(r"['\"](.*?)['\"]", message)
        if match:
            return match.group(1)
        
        # Pattern: mentions of specific words that are problematic
        if 'click' in message.lower():
            if 'click here' in message.lower():
                return 'click here'
            elif 'click on' in message.lower():
                return 'click on'
            else:
                return 'click'
        
        return ""
    
    def _consolidate_span_groups(self, span_groups: List[SpanGroup], 
                               errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Consolidate errors within each span group."""
        consolidated_errors = []
        
        for span_group in span_groups:
            if len(span_group.errors) <= 1:
                # No consolidation needed for single errors
                if span_group.errors:
                    consolidated_errors.append(span_group.errors[0])
                continue
            
            # Get rule types involved in this consolidation
            rule_types = [error.get('type', error.get('error_type', 'unknown')) for error in span_group.errors]
            
            # Determine primary rule and consolidation strategy
            primary_rule = self.priority_manager.determine_primary_rule(rule_types)
            consolidation_strategy = self.priority_manager.get_consolidation_strategy(rule_types)
            
            # Merge the error messages and suggestions
            consolidated_error = self.message_merger.merge_messages(
                span_group, primary_rule, consolidation_strategy
            )
            
            if consolidated_error:
                consolidated_errors.append(consolidated_error)
        
        return consolidated_errors
    
    def _get_unconsolidated_errors(self, span_groups: List[SpanGroup], 
                                 errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get errors that were not part of any consolidation group."""
        # Collect error IDs that were consolidated
        consolidated_error_ids = set()
        for span_group in span_groups:
            for error in span_group.errors:
                error_id = error.get('error_id', '')
                if error_id:
                    consolidated_error_ids.add(error_id)
        
        # Find errors not in any group
        unconsolidated = []
        for error in errors:
            error_id = error.get('error_id', '')
            if error_id not in consolidated_error_ids:
                # Remove internal fields before returning
                clean_error = {k: v for k, v in error.items() if not k.startswith('_') and k != 'error_id'}
                unconsolidated.append(clean_error)
        
        return unconsolidated
    
    def _sort_and_finalize_errors(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort errors by position and severity, and clean up internal fields."""
        if not errors:
            return []
        
        # Sort by sentence index first, then by severity
        severity_order = {'high': 3, 'medium': 2, 'low': 1}
        
        def sort_key(error):
            sentence_index = error.get('sentence_index', 0)
            severity = error.get('severity', 'medium')
            severity_score = severity_order.get(severity, 2)
            return (sentence_index, -severity_score)  # Negative for descending severity
        
        sorted_errors = sorted(errors, key=sort_key)
        
        # Clean up internal fields
        final_errors = []
        for error in sorted_errors:
            clean_error = {k: v for k, v in error.items() 
                          if not k.startswith('_') and k not in ['error_id']}
            final_errors.append(clean_error)
        
        return final_errors
    
    def preview_consolidation(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Preview what consolidation would do without actually consolidating.
        
        Args:
            errors: List of error dictionaries
            
        Returns:
            Dictionary with preview information
        """
        if not errors:
            return {
                'input_count': 0,
                'predicted_output_count': 0,
                'consolidation_groups': [],
                'reduction_percentage': 0
            }
        
        # Prepare errors and analyze spans
        errors_with_spans = self._prepare_errors_for_analysis(errors)
        span_groups = self.span_analyzer.analyze_spans(errors_with_spans)
        
        # Calculate what would be consolidated
        consolidation_groups = []
        errors_that_would_be_consolidated = set()
        
        for span_group in span_groups:
            if len(span_group.errors) > 1:
                group_info = {
                    'text_span': span_group.dominant_span.text,
                    'consolidation_type': span_group.consolidation_type,
                    'error_count': len(span_group.errors),
                    'rule_types': [error.get('type', error.get('error_type', 'unknown')) for error in span_group.errors],
                    'sentence_index': span_group.dominant_span.sentence_index
                }
                consolidation_groups.append(group_info)
                
                for error in span_group.errors:
                    error_id = error.get('error_id', '')
                    if error_id:
                        errors_that_would_be_consolidated.add(error_id)
        
        # Calculate predicted output count
        errors_merged = len(errors_that_would_be_consolidated)
        consolidation_count = len(consolidation_groups)
        predicted_output_count = len(errors) - errors_merged + consolidation_count
        
        reduction_percentage = 0
        if len(errors) > 0:
            reduction_percentage = round((errors_merged / len(errors)) * 100, 1)
        
        return {
            'input_count': len(errors),
            'predicted_output_count': predicted_output_count,
            'consolidation_groups': consolidation_groups,
            'errors_merged': errors_merged,
            'reduction_percentage': reduction_percentage
        } 
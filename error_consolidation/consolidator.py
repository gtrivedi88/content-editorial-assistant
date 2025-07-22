"""
Error Consolidator

Main class that orchestrates the error consolidation process by analyzing text spans,
applying rule priorities, and merging overlapping/duplicate errors.
"""

from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict

class ErrorConsolidator:
    """
    Main consolidator that coordinates the error consolidation process.
    It groups errors by their exact text span and merges them.
    """
    
    def __init__(self, priority_config: Optional[Dict] = None):
        """
        Initializes the error consolidator.
        """
        # A simple severity map for prioritization.
        self.severity_map = {'high': 3, 'medium': 2, 'low': 1}
        self.stats = {}

    def consolidate(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidates a list of errors based on their text span.
        
        This logic is now much simpler and more robust. It groups errors
        that flag the exact same text span and merges them into a single,
        prioritized error report.
        """
        if not errors:
            return []

        self.stats['total_errors_input'] = len(errors)
        
        # Group errors by their unique span (sentence index + start/end chars)
        errors_by_span = defaultdict(list)
        unconsolidatable_errors = []

        for error in errors:
            # IMPORTANT: The rule MUST provide a 'span' tuple.
            # If not, the error cannot be consolidated.
            if 'span' in error and isinstance(error['span'], tuple):
                span_key = (error.get('sentence_index', -1), error['span'][0], error['span'][1])
                errors_by_span[span_key].append(error)
            else:
                unconsolidatable_errors.append(error)

        # Process each group of overlapping errors
        consolidated_errors = []
        for span_key, grouped_errors in errors_by_span.items():
            if len(grouped_errors) == 1:
                # No consolidation needed for single errors
                consolidated_errors.append(grouped_errors[0])
            else:
                # Merge the group into a single error
                consolidated_errors.append(self._merge_error_group(grouped_errors))
        
        # Add back any errors that couldn't be consolidated
        consolidated_errors.extend(unconsolidatable_errors)
        
        # Final sort for consistent output
        final_errors = sorted(consolidated_errors, key=lambda e: (e.get('sentence_index', 0), e.get('span', (0,0))[0]))
        
        self.stats['total_errors_output'] = len(final_errors)
        self.stats['errors_merged'] = self.stats['total_errors_input'] - self.stats['total_errors_output']
        
        return final_errors

    def _merge_error_group(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merges a list of errors that share the same text span into one.
        """
        # Prioritize the error with the highest severity
        primary_error = max(group, key=lambda e: self.severity_map.get(e.get('severity', 'low'), 0))
        
        # Create a copy to avoid modifying the original
        merged_error = primary_error.copy()
        
        # Consolidate suggestions and rule types from all errors in the group
        all_suggestions = set()
        all_rule_types = set()
        
        for error in group:
            all_rule_types.add(error.get('rule', 'unknown'))
            if 'suggestions' in error and isinstance(error['suggestions'], list):
                all_suggestions.update(error['suggestions'])
        
        merged_error['suggestions'] = sorted(list(all_suggestions))
        
        # Add a field to show that this error was consolidated
        merged_error['consolidated_from'] = sorted(list(all_rule_types))
        
        # Create a more informative message
        merged_error['message'] = f"{primary_error['message']} (Consolidated from {len(group)} rules)"
        
        return merged_error

    def get_consolidation_stats(self) -> Dict[str, Any]:
        """
        Returns statistics about the last consolidation operation.
        """
        return self.stats

    def preview_consolidation(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes a list of errors and returns a report on what would be consolidated
        without actually performing the merge. Useful for debugging.
        """
        if not errors:
            return {'input_count': 0, 'predicted_output_count': 0, 'consolidation_groups': []}

        errors_by_span = defaultdict(list)
        unconsolidatable_count = 0

        for error in errors:
            if 'span' in error and isinstance(error['span'], tuple):
                span_key = (error.get('sentence_index', -1), error['span'][0], error['span'][1])
                errors_by_span[span_key].append(error)
            else:
                unconsolidatable_count += 1
        
        consolidation_groups = []
        num_to_be_merged = 0
        num_of_groups = 0

        for span_key, group in errors_by_span.items():
            if len(group) > 1:
                num_of_groups += 1
                num_to_be_merged += len(group)
                group_info = {
                    'text_span': group[0].get('flagged_text', ''),
                    'sentence_index': span_key[0],
                    'span': (span_key[1], span_key[2]),
                    'rule_types': sorted([e.get('rule', 'unknown') for e in group]),
                    'count': len(group)
                }
                consolidation_groups.append(group_info)

        predicted_output_count = (len(errors) - num_to_be_merged) + num_of_groups
        
        return {
            'input_count': len(errors),
            'predicted_output_count': predicted_output_count,
            'consolidation_groups': consolidation_groups
        }

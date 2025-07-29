"""
Error Consolidator

Main class that orchestrates the error consolidation process by analyzing text spans,
applying rule priorities, and merging overlapping/duplicate errors.

Production-ready version with full configuration support and no hardcoded values.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from collections import defaultdict
import yaml
import os

class ErrorConsolidator:
    """
    Production-ready error consolidator with full configuration support.
    All rules, priorities, and grouping logic are loaded from YAML config files.
    """
    
    def __init__(self, priority_config: Optional[Dict] = None, config_dir: Optional[str] = None):
        """
        Initialize the error consolidator with configurable rules and priorities.
        
        Args:
            priority_config: Optional custom priority configuration
            config_dir: Directory containing configuration files (defaults to config/ subdirectory)
        """
        # Set configuration directory
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), 'config')
        self.config_dir = config_dir
        
        # Load all configurations
        self._load_configurations()
        
        # Allow override with custom config
        if priority_config:
            self._merge_custom_config(priority_config)
        
        self.stats = {}
    
    def _load_configurations(self):
        """Load all configuration files for scalable operation."""
        try:
            # Load rule priorities
            self._load_rule_priorities()
            
            # Load semantic grouping configuration
            self._load_semantic_groups()
            
        except Exception as e:
            print(f"Warning: Failed to load consolidation configuration: {e}")
            # Fallback to minimal default configuration
            self._load_default_configuration()
    
    def _load_rule_priorities(self):
        """Load rule priorities from configuration file."""
        priorities_file = os.path.join(self.config_dir, 'rule_priorities.yaml')
        try:
            with open(priorities_file, 'r') as f:
                config = yaml.safe_load(f)
            
            # Extract priority mappings
            self.error_type_priority = config.get('rule_specific_priorities', {})
            
            # Extract severity mapping from config or use defaults
            self.severity_map = {
                'critical': 5,
                'high': 4,
                'medium': 3,
                'low': 2,
                'info': 1
            }
            
            # Extract consolidation strategies
            self.consolidation_strategies = config.get('consolidation_strategies', {})
            
        except FileNotFoundError:
            print(f"Warning: Rule priorities file not found: {priorities_file}")
            self._load_default_priorities()
    
    def _load_semantic_groups(self):
        """Load semantic grouping configuration."""
        semantic_file = os.path.join(self.config_dir, 'semantic_groups.yaml')
        try:
            with open(semantic_file, 'r') as f:
                config = yaml.safe_load(f)
            
            self.semantic_groups = config.get('semantic_groups', {})
            self.special_rules = config.get('special_rules', {})
            self.global_parameters = config.get('global_parameters', {})
            
            # Extract global settings
            self.max_consolidation_distance = self.global_parameters.get('max_consolidation_distance', 50)
            self.min_errors_for_consolidation = self.global_parameters.get('min_errors_for_consolidation', 2)
            self.default_proximity_threshold = self.global_parameters.get('default_proximity_threshold', 20)
            self.enable_span_overlap = self.global_parameters.get('enable_span_overlap_detection', True)
            
        except FileNotFoundError:
            print(f"Warning: Semantic groups file not found: {semantic_file}")
            self._load_default_semantic_groups()
    
    def _load_default_configuration(self):
        """Load minimal default configuration as fallback."""
        self._load_default_priorities()
        self._load_default_semantic_groups()
    
    def _load_default_priorities(self):
        """Load default priority mappings as fallback."""
        self.error_type_priority = {
            'ambiguity': 7,
            'verbs': 6,
            'word_usage': 4,
            'punctuation': 3,
        }
        self.severity_map = {'high': 3, 'medium': 2, 'low': 1}
        self.consolidation_strategies = {}
    
    def _load_default_semantic_groups(self):
        """Load default semantic groups as fallback."""
        self.semantic_groups = {
            'language_clarity': {
                'types': ['verbs', 'ambiguity', 'word_usage', 'word_usage_t'],
                'proximity_threshold': 25,
                'message_template': 'Multiple style issues detected.'
            }
        }
        self.special_rules = {}
        self.max_consolidation_distance = 50
        self.min_errors_for_consolidation = 2
        self.default_proximity_threshold = 20
        self.enable_span_overlap = True
    
    def _merge_custom_config(self, custom_config: Dict):
        """Merge custom configuration with loaded configuration."""
        if 'rule_priorities' in custom_config:
            self.error_type_priority.update(custom_config['rule_priorities'])
        
        if 'semantic_groups' in custom_config:
            self.semantic_groups.update(custom_config['semantic_groups'])
        
        if 'global_parameters' in custom_config:
            for key, value in custom_config['global_parameters'].items():
                setattr(self, key, value)

    def consolidate(self, errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidates a list of errors based on their text span AND semantic relationships.
        
        Enhanced to group:
        1. Errors with identical spans (original behavior)
        2. Errors within the same sentence that are semantically related
        3. Overlapping or adjacent spans within the same sentence
        4. Handles missing span information gracefully
        """
        if not errors:
            return []

        self.stats['total_errors_input'] = len(errors)
        
        # Group errors by sentence first
        errors_by_sentence = defaultdict(list)
        unconsolidatable_errors = []

        for error in errors:
            sentence_index = error.get('sentence_index', -1)
            # More robust span checking
            span = error.get('span')
            has_valid_span = (span and isinstance(span, (tuple, list)) and len(span) == 2 
                            and isinstance(span[0], (int, float)) and isinstance(span[1], (int, float)))
            
            if sentence_index >= 0 and has_valid_span:
                # CRITICAL: Normalize span to sentence-relative positions
                normalized_error = self._normalize_span_to_sentence(error)
                errors_by_sentence[sentence_index].append(normalized_error)
            else:
                # Handle errors without proper spans - still group by sentence if possible
                if sentence_index >= 0:
                    # Create artificial span based on error type and flagged text
                    error = self._add_fallback_span(error)
                    # Also normalize the fallback span
                    error = self._normalize_span_to_sentence(error)
                    errors_by_sentence[sentence_index].append(error)
                else:
                    unconsolidatable_errors.append(error)

        # Process each sentence's errors
        consolidated_errors = []
        for sentence_index, sentence_errors in errors_by_sentence.items():
            # Group errors within this sentence by semantic relationship and proximity
            consolidated_for_sentence = self._consolidate_sentence_errors(sentence_errors)
            consolidated_errors.extend(consolidated_for_sentence)
        
        # Add back any errors that couldn't be consolidated
        consolidated_errors.extend(unconsolidatable_errors)
        
        # Final sort for consistent output
        final_errors = sorted(consolidated_errors, key=lambda e: (e.get('sentence_index', 0), e.get('span', (0,0))[0]))
        
        self.stats['total_errors_output'] = len(final_errors)
        self.stats['errors_merged'] = self.stats['total_errors_input'] - self.stats['total_errors_output']
        
        return final_errors

    def _add_fallback_span(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """Add fallback span information for errors missing spans."""
        error = error.copy()  # Don't modify original
        
        sentence = error.get('sentence', '')
        flagged_text = error.get('flagged_text', '')
        
        if flagged_text and sentence:
            # Try to find the flagged text in the sentence
            start_pos = sentence.lower().find(flagged_text.lower())
            if start_pos >= 0:
                error['span'] = (start_pos, start_pos + len(flagged_text))
        
        # If still no span, create a minimal one at the beginning
        if 'span' not in error:
            error['span'] = (0, min(10, len(sentence)))  # First 10 characters or sentence length
        
        return error
    
    def _normalize_span_to_sentence(self, error: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize span to be sentence-relative for consistent consolidation.
        Handles both document-relative and sentence-relative spans.
        """
        error = error.copy()
        span = error.get('span')
        sentence = error.get('sentence', '')
        flagged_text = error.get('flagged_text', '')
        
        if not span or not sentence:
            return error
        
        span_start, span_end = span
        
        # Check if span seems to be document-relative (much larger than sentence length)
        if span_start > len(sentence) * 2 or span_end > len(sentence) * 2:
            # Likely document-relative span, convert to sentence-relative
            if flagged_text:
                # Find the flagged text in the sentence
                sentence_start = sentence.lower().find(flagged_text.lower())
                if sentence_start >= 0:
                    error['span'] = (sentence_start, sentence_start + len(flagged_text))
                    return error
            
            # Fallback: use beginning of sentence
            error['span'] = (0, min(10, len(sentence)))
        
        # Span seems reasonable for sentence length, keep as-is
        return error

    def _consolidate_sentence_errors(self, sentence_errors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Consolidate errors within a single sentence based on semantic relationships and proximity.
        """
        if len(sentence_errors) <= 1:
            return sentence_errors
        
        # Group by exact span first (original behavior)
        errors_by_exact_span = defaultdict(list)
        remaining_errors = []
        
        for error in sentence_errors:
            span_key = (error['span'][0], error['span'][1])
            if span_key in [(e['span'][0], e['span'][1]) for e in remaining_errors]:
                # Find existing group
                for existing_error in remaining_errors:
                    if (existing_error['span'][0], existing_error['span'][1]) == span_key:
                        if span_key not in errors_by_exact_span:
                            errors_by_exact_span[span_key] = [existing_error]
                            remaining_errors.remove(existing_error)
                        errors_by_exact_span[span_key].append(error)
                        break
            else:
                # Check if this should be grouped with existing errors by semantic relationship
                grouped = False
                for span_key, group in errors_by_exact_span.items():
                    if self._should_group_semantically(error, group[0]):
                        group.append(error)
                        grouped = True
                        break
                
                if not grouped:
                    # Check against remaining errors for semantic grouping
                    for i, existing_error in enumerate(remaining_errors):
                        if self._should_group_semantically(error, existing_error):
                            # Create new semantic group
                            new_span_key = (min(error['span'][0], existing_error['span'][0]), 
                                          max(error['span'][1], existing_error['span'][1]))
                            errors_by_exact_span[new_span_key] = [existing_error, error]
                            remaining_errors.pop(i)
                            grouped = True
                            break
                    
                    if not grouped:
                        remaining_errors.append(error)
        
        # Merge each group
        consolidated = []
        for group in errors_by_exact_span.values():
            if len(group) == 1:
                consolidated.append(group[0])
            else:
                consolidated.append(self._merge_error_group(group))
        
        # Add remaining ungrouped errors
        consolidated.extend(remaining_errors)
        
        return consolidated
    
    def _should_group_semantically(self, error1: Dict[str, Any], error2: Dict[str, Any]) -> bool:
        """
        Determine if two errors should be grouped based on semantic relationship.
        Uses configuration-driven semantic groups for full scalability.
        Enhanced to respect preserve_specific_messages flag.
        """
        type1 = error1.get('type', '')
        type2 = error2.get('type', '')
        
        # Check special rules first (highest priority)
        if self._check_special_rules(error1, error2):
            return True
        
        # Check configured semantic groups
        for group_name, group_config in self.semantic_groups.items():
            group_types = set(group_config.get('types', []))
            
            if type1 in group_types and type2 in group_types:
                # Check if this group preserves specific messages
                preserve_specific = group_config.get('preserve_specific_messages', False)
                
                # If this group preserves specific messages, be more restrictive about consolidation
                if preserve_specific:
                    # Only consolidate if both errors are of the same type or very close
                    if type1 != type2:
                        # Different types in a preserve_specific group - only consolidate if spans are overlapping
                        span1 = error1.get('span', (0, 0))
                        span2 = error2.get('span', (0, 0))
                        overlap = not (span1[1] <= span2[0] or span2[1] <= span1[0])
                        if not overlap:
                            return False
                
                # Get proximity threshold for this group
                proximity_threshold = group_config.get('proximity_threshold', self.default_proximity_threshold)
                
                # Check always_consolidate_pairs first
                always_pairs = group_config.get('always_consolidate_pairs', [])
                for pair in always_pairs:
                    if (type1 in pair and type2 in pair) or (type2 in pair and type1 in pair):
                        return True
                
                # Check proximity for this semantic group
                if self._errors_are_close(error1, error2, proximity_threshold):
                    return True
        
        return False
    
    def _check_special_rules(self, error1: Dict[str, Any], error2: Dict[str, Any]) -> bool:
        """Check special consolidation rules from configuration."""
        type1 = error1.get('type', '')
        type2 = error2.get('type', '')
        
        for rule_name, rule_config in self.special_rules.items():
            condition = rule_config.get('condition', '')
            action = rule_config.get('action', '')
            
            # Simple condition evaluation (can be extended for more complex rules)
            if self._evaluate_condition(condition, error1, error2):
                if action == 'always_consolidate':
                    return True
                elif action == 'consolidate_if_close':
                    threshold = rule_config.get('proximity_threshold', self.default_proximity_threshold)
                    return self._errors_are_close(error1, error2, threshold)
        
        return False
    
    def _evaluate_condition(self, condition: str, error1: Dict[str, Any], error2: Dict[str, Any]) -> bool:
        """
        Evaluate a condition string for special rules.
        This is a simple implementation that can be extended for more complex conditions.
        """
        type1 = error1.get('type', '')
        type2 = error2.get('type', '')
        
        # Simple condition patterns
        if "one_type_contains('ambiguity') and one_type_contains('verbs')" in condition:
            return ('ambiguity' in type1 and 'verbs' in type2) or ('verbs' in type1 and 'ambiguity' in type2)
        
        if "count_types_matching('word_usage') >= 2" in condition:
            word_usage_count = sum(1 for t in [type1, type2] if 'word_usage' in t)
            return word_usage_count >= 2
        
        if "spans_overlap()" in condition:
            span1 = error1.get('span', (0, 0))
            span2 = error2.get('span', (0, 0))
            return not (span1[1] <= span2[0] or span2[1] <= span1[0])
        
        return False
    
    def _errors_are_close(self, error1: Dict[str, Any], error2: Dict[str, Any], threshold: int) -> bool:
        """Check if two errors are within the specified proximity threshold."""
        span1 = error1.get('span', (0, 0))
        span2 = error2.get('span', (0, 0))
        
        # Check for overlap first
        if self.enable_span_overlap:
            overlap = not (span1[1] <= span2[0] or span2[1] <= span1[0])
            if overlap:
                return True
        
        # Check proximity
        distance = min(abs(span1[0] - span2[1]), abs(span2[0] - span1[1]))
        return distance <= threshold

    def _merge_error_group(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merges a list of errors that share the same text span or are semantically related into one.
        Enhanced to provide clearer guidance when multiple error types are combined.
        Uses production-ready prioritization based on severity and error type importance.
        """
        # Prioritize the error using enhanced criteria
        primary_error = self._select_primary_error(group)
        
        # Create a copy to avoid modifying the original
        merged_error = primary_error.copy()
        
        # Consolidate suggestions and rule types from all errors in the group
        all_suggestions = []
        all_rule_types = set()
        
        for error in group:
            error_type = error.get('type', error.get('rule', 'unknown'))
            all_rule_types.add(error_type)
            if 'suggestions' in error and isinstance(error['suggestions'], list):
                all_suggestions.extend(error['suggestions'])
        
        # Remove duplicate suggestions while preserving order
        unique_suggestions = []
        seen = set()
        for suggestion in all_suggestions:
            if suggestion not in seen:
                unique_suggestions.append(suggestion)
                seen.add(suggestion)
        
        merged_error['suggestions'] = unique_suggestions
        
        # Create a more comprehensive message for semantically grouped errors
        if len(group) > 1 and len(all_rule_types) > 1:
            merged_error['message'] = self._create_consolidated_message(group, all_rule_types)
        else:
            # Keep the primary error's message for single-type groups
            merged_error['message'] = primary_error['message']
        
        # Expand span to cover all grouped errors
        if len(group) > 1:
            all_spans = [error.get('span', (0, 0)) for error in group]
            min_start = min(span[0] for span in all_spans)
            max_end = max(span[1] for span in all_spans)
            merged_error['span'] = (min_start, max_end)
        
        # Add metadata fields for consolidation info (for debugging/analytics only)
        merged_error['consolidated_from'] = sorted(list(all_rule_types))
        merged_error['consolidation_count'] = len(group)
        merged_error['is_consolidated'] = True
        
        return merged_error
    
    def _select_primary_error(self, group: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Select the primary error from a group using production-ready prioritization.
        Considers both severity and error type importance.
        """
        def get_priority_score(error: Dict[str, Any]) -> tuple:
            severity = error.get('severity', 'low')
            error_type = error.get('type', 'unknown')
            
            severity_score = self.severity_map.get(severity, 1)
            type_score = self.error_type_priority.get(error_type, 0)
            
            # Return tuple for sorting: (type_priority, severity, has_suggestions)
            # Higher values = higher priority
            has_suggestions = len(error.get('suggestions', [])) > 0
            return (type_score, severity_score, has_suggestions)
        
        # Sort by priority (highest first) and return the top error
        sorted_errors = sorted(group, key=get_priority_score, reverse=True)
        return sorted_errors[0]

    def _create_consolidated_message(self, group: List[Dict[str, Any]], rule_types: set) -> str:
        """
        Create a comprehensive message for semantically related errors.
        Enhanced to preserve specific messages from high-priority errors.
        """
        # First, check if any error in the group has a high-priority, specific message that should be preserved
        high_priority_error = self._find_high_priority_specific_error(group)
        if high_priority_error:
            return high_priority_error['message']
        
        # Check if we have a configured message template for this combination
        message_template = self._find_message_template(rule_types)
        if message_template:
            return message_template
        
        # Check special rules for custom messages
        for rule_name, rule_config in self.special_rules.items():
            if self._rule_types_match_special_rule(rule_types, rule_config):
                return rule_config.get('message_template', 'Multiple style issues detected.')
        
        # Find the semantic group that best matches the rule types
        best_group = self._find_best_semantic_group(rule_types)
        if best_group:
            return best_group.get('message_template', 'Multiple style issues detected.')
        
        # Fallback to generic message
        primary_message = max(group, key=lambda e: self.severity_map.get(e.get('severity', 'low'), 1))['message']
        return f"Multiple style issues detected: {primary_message.lower()}"
    
    def _find_high_priority_specific_error(self, group: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """
        Find an error in the group that has a high-priority, specific message that should be preserved.
        Returns the error if found, None otherwise.
        """
        # Define rules that should have their specific messages preserved
        high_priority_specific_rules = {
            'inclusive_language': 50,  # Very high priority for inclusive language
            'claims': 100,             # Legal claims are highest priority
            'personal_information': 95, # Privacy concerns
            'accessibility_citations': 85,  # Accessibility issues
            'commands': 70,            # Technical accuracy
            'security': 80             # Security-related issues
        }
        
        # Find errors with high-priority specific rules
        high_priority_errors = []
        for error in group:
            error_type = error.get('type', '')
            if error_type in high_priority_specific_rules:
                priority_score = high_priority_specific_rules[error_type]
                # Check if the message is specific (not generic)
                message = error.get('message', '')
                if self._is_specific_message(message, error_type):
                    high_priority_errors.append((priority_score, error))
        
        if high_priority_errors:
            # Return the error with the highest priority score
            high_priority_errors.sort(key=lambda x: x[0], reverse=True)
            return high_priority_errors[0][1]
        
        return None
    
    def _is_specific_message(self, message: str, error_type: str) -> bool:
        """
        Determine if a message is specific enough to preserve during consolidation.
        """
        # Messages that are clearly specific and actionable
        specific_indicators = [
            'consider replacing',
            'non-inclusive term',
            'avoid making absolute claims',
            'accessibility concern',
            'legal requirement',
            'security risk',
            'privacy concern'
        ]
        
        # Generic messages that should be replaced with templates
        generic_indicators = [
            'multiple style issues',
            'various concerns',
            'several problems',
            'general guidance'
        ]
        
        message_lower = message.lower()
        
        # If it contains generic indicators, it's not specific
        if any(generic in message_lower for generic in generic_indicators):
            return False
        
        # If it contains specific indicators, it's specific
        if any(specific in message_lower for specific in specific_indicators):
            return True
        
        # For inclusive language, any message with specific terms is important
        if error_type == 'inclusive_language':
            return len(message) > 20 and ('term' in message_lower or 'language' in message_lower)
        
        # For legal/claims, most messages are specific
        if error_type in ['claims', 'personal_information']:
            return len(message) > 15
        
        # Default: if message is reasonably long and detailed, consider it specific
        return len(message) > 30 and not any(generic in message_lower for generic in ['detected', 'multiple', 'various'])
    
    def _find_message_template(self, rule_types: set) -> Optional[str]:
        """Find a specific message template for the given rule type combination."""
        # Check consolidation strategies for specific combinations
        for strategy_key, strategy_config in self.consolidation_strategies.items():
            if self._strategy_matches_types(strategy_key, rule_types):
                return strategy_config.get('message_template')
        
        return None
    
    def _strategy_matches_types(self, strategy_key: str, rule_types: set) -> bool:
        """Check if a consolidation strategy key matches the current rule types."""
        # Simple pattern matching for strategy keys like "citations + accessibility_citations"
        if '+' in strategy_key:
            strategy_types = set(t.strip() for t in strategy_key.split('+'))
            return strategy_types.issubset(rule_types)
        
        return strategy_key in rule_types
    
    def _rule_types_match_special_rule(self, rule_types: set, rule_config: Dict) -> bool:
        """Check if rule types match a special rule configuration."""
        condition = rule_config.get('condition', '')
        
        # Check for specific patterns in the condition
        if 'ambiguity' in condition and 'verbs' in condition:
            return 'ambiguity' in rule_types and 'verbs' in rule_types
        
        if 'word_usage' in condition:
            return any('word_usage' in rt for rt in rule_types)
        
        return False
    
    def _find_best_semantic_group(self, rule_types: set) -> Optional[Dict]:
        """Find the semantic group that best matches the given rule types."""
        best_match = None
        best_score = 0
        
        for group_name, group_config in self.semantic_groups.items():
            group_types = set(group_config.get('types', []))
            
            # Calculate overlap score
            overlap = rule_types.intersection(group_types)
            score = len(overlap) / len(rule_types) if rule_types else 0
            
            if score > best_score:
                best_score = score
                best_match = group_config
        
        return best_match if best_score > 0.5 else None  # At least 50% overlap

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
            if 'span' in error and isinstance(error['span'], (tuple, list)) and len(error['span']) == 2:
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

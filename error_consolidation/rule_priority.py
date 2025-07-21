"""
Rule Priority Manager

Manages rule priorities and determines consolidation strategies when multiple rules
detect the same text spans.
"""

import yaml
import os
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path


class RulePriorityManager:
    """
    Manages rule priorities and consolidation strategies for overlapping errors.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize with rule priority configuration.
        
        Args:
            config_path: Path to custom priority configuration file
        """
        self.config = self._load_config(config_path)
        self.category_priorities = self.config.get('category_priorities', [])
        self.rule_priorities = self.config.get('rule_specific_priorities', {})
        self.consolidation_strategies = self.config.get('consolidation_strategies', {})
        self.message_patterns = self.config.get('message_patterns', {})
        self.severity_escalation = self.config.get('severity_escalation', {})
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load priority configuration from YAML file."""
        if config_path is None:
            # Use default config file in this package
            config_path = Path(__file__).parent / 'config' / 'rule_priorities.yaml'
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Warning: Could not load priority config from {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Provide fallback configuration if config file is unavailable."""
        return {
            'category_priorities': [
                'legal_information', 'accessibility', 'technical_elements',
                'references', 'language_and_grammar', 'structure_and_format'
            ],
            'rule_specific_priorities': {
                'claims': 100, 'accessibility_citations': 85, 'citations': 55,
                'mouse_buttons': 60, 'word_usage': 2
            },
            'consolidation_strategies': {},
            'message_patterns': {},
            'severity_escalation': {
                'multiple_medium': 'high',
                'high_plus_any': 'high',
                'low_plus_medium': 'medium'
            }
        }
    
    def get_rule_priority(self, rule_type: str) -> int:
        """
        Get the priority score for a specific rule type.
        
        Args:
            rule_type: The rule type identifier
            
        Returns:
            Priority score (higher = more important)
        """
        # First check specific rule priorities
        if rule_type in self.rule_priorities:
            return self.rule_priorities[rule_type]
        
        # Then check category priorities
        for i, category in enumerate(self.category_priorities):
            if category in rule_type or rule_type.startswith(category):
                # Higher category priority = higher score
                return len(self.category_priorities) - i
        
        # Default priority for unknown rules
        return 1
    
    def determine_primary_rule(self, rule_types: List[str]) -> str:
        """
        Determine which rule should be the primary one when consolidating.
        
        Args:
            rule_types: List of rule types involved in consolidation
            
        Returns:
            The rule type that should take precedence
        """
        if not rule_types:
            return ""
        
        if len(rule_types) == 1:
            return rule_types[0]
        
        # Check for specific consolidation strategies first
        strategy_key = self._get_strategy_key(rule_types)
        if strategy_key in self.consolidation_strategies:
            return self.consolidation_strategies[strategy_key].get('primary_rule', rule_types[0])
        
        # Fall back to priority-based selection
        return max(rule_types, key=self.get_rule_priority)
    
    def get_consolidation_strategy(self, rule_types: List[str]) -> Dict[str, Any]:
        """
        Get the consolidation strategy for a combination of rule types.
        
        Args:
            rule_types: List of rule types to consolidate
            
        Returns:
            Dictionary containing consolidation strategy details
        """
        if len(rule_types) <= 1:
            return {'strategy': 'single_rule', 'primary_rule': rule_types[0] if rule_types else ''}
        
        # Check for specific strategy
        strategy_key = self._get_strategy_key(rule_types)
        if strategy_key in self.consolidation_strategies:
            return self.consolidation_strategies[strategy_key]
        
        # Default strategy based on rule categories
        primary_rule = self.determine_primary_rule(rule_types)
        return {
            'primary_rule': primary_rule,
            'strategy': 'priority_based_merge',
            'message_template': '{primary_issue} with additional concerns'
        }
    
    def _get_strategy_key(self, rule_types: List[str]) -> str:
        """Generate a key for looking up consolidation strategies."""
        # Sort rule types to make key order-independent
        sorted_rules = sorted(rule_types)
        
        # Try exact match first
        exact_key = ' + '.join(sorted_rules)
        if exact_key in self.consolidation_strategies:
            return exact_key
        
        # Try pattern matching (e.g., "citations + *")
        for rule in sorted_rules:
            pattern_key = f"{rule} + *"
            if pattern_key in self.consolidation_strategies:
                return pattern_key
        
        # Try category-based patterns
        categories = [self._get_rule_category(rule) for rule in sorted_rules]
        category_key = ' + '.join(sorted(set(categories)))
        if category_key in self.consolidation_strategies:
            return category_key
        
        return exact_key  # Return exact key even if not found
    
    def _get_rule_category(self, rule_type: str) -> str:
        """Determine the category of a rule type."""
        for category in self.category_priorities:
            if category in rule_type or rule_type.startswith(category.replace('_', '')):
                return category
        return 'unknown'
    
    def escalate_severity(self, severities: List[str]) -> str:
        """
        Determine the appropriate severity level when consolidating multiple errors.
        
        Args:
            severities: List of severity levels from individual errors
            
        Returns:
            Consolidated severity level
        """
        if not severities:
            return 'medium'
        
        if len(severities) == 1:
            return severities[0]
        
        # Count each severity level
        severity_counts = {'low': 0, 'medium': 0, 'high': 0}
        for severity in severities:
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Apply escalation rules
        if severity_counts['high'] > 0:
            return 'high'  # Any high severity escalates to high
        
        if severity_counts['medium'] >= 2:
            # Multiple medium errors escalate to high
            return self.severity_escalation.get('multiple_medium', 'high')
        
        if severity_counts['medium'] > 0 and severity_counts['low'] > 0:
            # Medium + low = medium
            return self.severity_escalation.get('low_plus_medium', 'medium')
        
        if severity_counts['medium'] > 0:
            return 'medium'
        
        return 'low'  # All low severities remain low
    
    def get_message_pattern(self, consolidation_type: str) -> Dict[str, str]:
        """
        Get message pattern for a specific consolidation type.
        
        Args:
            consolidation_type: Type of consolidation (overlap, nested, adjacent, etc.)
            
        Returns:
            Dictionary with template and suggestion merger strategy
        """
        pattern_key = f"{consolidation_type}_text_spans"
        if pattern_key in self.message_patterns:
            return self.message_patterns[pattern_key]
        
        # Default patterns
        default_patterns = {
            'overlapping_text_spans': {
                'template': '{primary_issue} in "{text_span}"',
                'suggestion_merger': 'combine_and_prioritize'
            },
            'nested_text_spans': {
                'template': '{comprehensive_issue} affecting "{outer_span}"',
                'suggestion_merger': 'use_most_comprehensive'
            },
            'adjacent_text_spans': {
                'template': '{combined_issue} in consecutive elements',
                'suggestion_merger': 'merge_sequential_fixes'
            }
        }
        
        return default_patterns.get(pattern_key, {
            'template': '{primary_issue} with related concerns',
            'suggestion_merger': 'combine_and_prioritize'
        }) 
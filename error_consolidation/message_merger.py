"""
Message Merger

Intelligently combines error messages and suggestions from multiple overlapping errors
into a single, coherent error message with comprehensive suggestions.
"""

import re
from typing import List, Dict, Any, Set, Tuple
from .text_span_analyzer import SpanGroup, TextSpan


class MessageMerger:
    """
    Handles intelligent merging of error messages and suggestions.
    """
    
    def __init__(self):
        self.common_phrases = {
            'problematic', 'use', 'avoid', 'consider', 'replace', 'remove', 'add',
            'improve', 'ensure', 'check', 'verify', 'provide', 'specify'
        }
    
    def merge_messages(self, span_group: SpanGroup, primary_rule: str,
                       consolidation_strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge messages and suggestions from multiple errors within a span group.
        Enhanced to provide multiple fix options for nested spans.
        """
        rule_types = [error['type'] for error in span_group.errors]
        messages = [error['message'] for error in span_group.errors]
        suggestion_lists = [error.get('suggestions', []) for error in span_group.errors]
        severities = [error.get('severity', 'medium') for error in span_group.errors]
        
        # Create consolidated message
        consolidated_message = self._create_consolidated_message(
            span_group, rule_types, messages, consolidation_strategy
        )
        
        # Enhanced suggestion merging for nested spans
        merged_suggestions = self._merge_suggestions_with_options(
            suggestion_lists, consolidation_strategy.get('message_merger', 'combine_and_prioritize'),
            span_group
        )
        
        # Determine final severity
        consolidated_severity = self._determine_severity(severities, consolidation_strategy)
        
        # Build consolidated error
        consolidated_error = {
            'type': span_group.errors[0]['type'],  # Use primary error type
            'message': consolidated_message,
            'suggestions': merged_suggestions,
            'severity': consolidated_severity,
            'sentence': span_group.errors[0]['sentence'],
            'sentence_index': span_group.errors[0]['sentence_index'],
            'consolidated_from': rule_types,
            'consolidation_type': span_group.consolidation_type,
            'text_span': span_group.dominant_span.text
        }
        
        # Add multiple fix options for nested spans
        if span_group.consolidation_type == 'nested' and len(span_group.spans) > 1:
            consolidated_error['fix_options'] = self._generate_fix_options(span_group)
        
        return consolidated_error
    
    def _create_consolidated_message(self, span_group: SpanGroup, rule_types: List[str], 
                                   messages: List[str], strategy: Dict[str, Any]) -> str:
        """Create a consolidated error message from multiple messages."""
        
        # Use message template from strategy if available
        template = strategy.get('message_template', '')
        if template:
            return self._apply_message_template(template, span_group, rule_types, messages)
        
        # Default consolidation logic
        primary_message = messages[0] if messages else ""
        text_span = span_group.dominant_span.text
        
        # Identify the core issue types
        issue_types = self._extract_issue_types(messages)
        
        if span_group.consolidation_type == 'nested':
            return f"Multiple issues affecting '{text_span}': {', '.join(issue_types)}"
        elif span_group.consolidation_type == 'overlap':
            return f"Overlapping issues in '{text_span}': {', '.join(issue_types)}"
        elif span_group.consolidation_type == 'adjacent':
            return f"Sequential issues in '{text_span}' and adjacent text"
        else:
            return f"Multiple style issues in '{text_span}': {', '.join(issue_types)}"
    
    def _apply_message_template(self, template: str, span_group: SpanGroup, 
                              rule_types: List[str], messages: List[str]) -> str:
        """Apply a message template with context substitution."""
        substitutions = {
            'text_span': span_group.dominant_span.text,
            'outer_span': span_group.dominant_span.text,  # For nested spans
            'primary_issue': self._extract_primary_issue(messages[0]) if messages else "Style issue",
            'comprehensive_issue': self._extract_comprehensive_issue(messages),
            'combined_issue': self._extract_combined_issue(messages),
            'rule_types': ', '.join(rule_types)
        }
        
        # Replace template variables
        result = template
        for key, value in substitutions.items():
            result = result.replace(f'{{{key}}}', str(value))
        
        return result
    
    def _extract_issue_types(self, messages: List[str]) -> List[str]:
        """Extract the core issue types from error messages."""
        issue_types = []
        
        for message in messages:
            # Common patterns in error messages
            if 'accessibility' in message.lower():
                issue_types.append('accessibility concern')
            elif 'link text' in message.lower():
                issue_types.append('link text issue')
            elif 'preposition' in message.lower():
                issue_types.append('grammar issue')
            elif 'anthropomorph' in message.lower():
                issue_types.append('anthropomorphism')
            elif 'click' in message.lower():
                issue_types.append('interaction terminology')
            else:
                # Extract the first noun phrase after ":" if present
                if ':' in message:
                    issue_part = message.split(':')[0].strip()
                    issue_types.append(issue_part.lower())
                else:
                    # Extract first few words as issue type
                    words = message.split()[:3]
                    issue_types.append(' '.join(words).lower())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_types = []
        for issue_type in issue_types:
            if issue_type not in seen:
                unique_types.append(issue_type)
                seen.add(issue_type)
        
        return unique_types[:3]  # Limit to 3 most important issues
    
    def _extract_primary_issue(self, message: str) -> str:
        """Extract the primary issue description from a message."""
        # Remove common prefixes
        message = re.sub(r'^(Problematic|Accessibility concern|Grammar issue):\s*', '', message)
        
        # Extract the main issue (usually the first sentence)
        sentences = message.split('.')
        if sentences:
            return sentences[0].strip()
        
        return message.strip()
    
    def _extract_comprehensive_issue(self, messages: List[str]) -> str:
        """Extract a comprehensive issue description covering all messages."""
        primary_issues = [self._extract_primary_issue(msg) for msg in messages]
        
        # Combine unique issues
        unique_issues = []
        for issue in primary_issues:
            if issue and issue not in unique_issues:
                unique_issues.append(issue)
        
        if len(unique_issues) == 1:
            return unique_issues[0]
        elif len(unique_issues) == 2:
            return f"{unique_issues[0]} and {unique_issues[1]}"
        else:
            return f"{', '.join(unique_issues[:-1])}, and {unique_issues[-1]}"
    
    def _extract_combined_issue(self, messages: List[str]) -> str:
        """Extract a combined issue description for adjacent/related errors."""
        issue_types = self._extract_issue_types(messages)
        
        if len(issue_types) <= 1:
            return issue_types[0] if issue_types else "Style issue"
        
        # Create a natural combination
        return f"{' and '.join(issue_types)} problems"
    
    def _merge_suggestions(self, suggestion_lists: List[List[str]], 
                          merger_strategy: str) -> List[str]:
        """
        Merge suggestion lists using the specified strategy.
        
        Args:
            suggestion_lists: List of suggestion lists from different errors
            merger_strategy: Strategy for merging ('combine_and_prioritize', 
                           'use_most_comprehensive', 'merge_sequential_fixes')
            
        Returns:
            Merged list of suggestions
        """
        if not suggestion_lists:
            return []
        
        # Filter out empty suggestion lists
        non_empty_lists = [suggestions for suggestions in suggestion_lists if suggestions]
        
        if not non_empty_lists:
            return []
        
        if len(non_empty_lists) == 1:
            return non_empty_lists[0]
        
        if merger_strategy == 'use_most_comprehensive':
            # Use the suggestion list with the most detailed suggestions
            return max(non_empty_lists, key=lambda lst: sum(len(s) for s in lst))
        
        elif merger_strategy == 'merge_sequential_fixes':
            # Combine suggestions in logical sequence
            return self._merge_sequential_suggestions(non_empty_lists)
        
        else:  # Default: 'combine_and_prioritize'
            return self._combine_and_prioritize_suggestions(non_empty_lists)
    
    def _combine_and_prioritize_suggestions(self, suggestion_lists: List[List[str]]) -> List[str]:
        """Combine suggestions while removing duplicates and prioritizing."""
        all_suggestions = []
        seen_content = set()
        
        # Flatten all suggestions
        for suggestions in suggestion_lists:
            for suggestion in suggestions:
                # Normalize suggestion text for duplicate detection
                normalized = self._normalize_suggestion(suggestion)
                if normalized not in seen_content:
                    all_suggestions.append(suggestion)
                    seen_content.add(normalized)
        
        # Prioritize suggestions (accessibility and technical first)
        return self._prioritize_suggestions(all_suggestions)
    
    def _merge_sequential_suggestions(self, suggestion_lists: List[List[str]]) -> List[str]:
        """Merge suggestions in a logical sequence."""
        # Take the first suggestion from each list, then remaining suggestions
        merged = []
        
        # Add primary suggestions first
        for suggestions in suggestion_lists:
            if suggestions:
                merged.append(suggestions[0])
        
        # Add secondary suggestions
        for suggestions in suggestion_lists:
            for suggestion in suggestions[1:]:
                if suggestion not in merged:
                    merged.append(suggestion)
        
        return merged[:3]  # Limit to 3 suggestions max
    
    def _normalize_suggestion(self, suggestion: str) -> str:
        """Normalize suggestion text for duplicate detection."""
        # Remove common prefixes and normalize
        normalized = suggestion.lower().strip()
        normalized = re.sub(r'^(try|consider|use|avoid|replace|remove):\s*', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize whitespace
        return normalized
    
    def _prioritize_suggestions(self, suggestions: List[str]) -> List[str]:
        """Prioritize suggestions by importance and specificity."""
        if len(suggestions) <= 3:
            return suggestions
        
        # Score suggestions by priority keywords
        scored_suggestions = []
        for suggestion in suggestions:
            score = self._score_suggestion(suggestion)
            scored_suggestions.append((score, suggestion))
        
        # Sort by score (highest first) and take top 3
        scored_suggestions.sort(key=lambda x: x[0], reverse=True)
        return [suggestion for _, suggestion in scored_suggestions[:3]]
    
    def _score_suggestion(self, suggestion: str) -> int:
        """Score a suggestion based on priority keywords."""
        score = 0
        suggestion_lower = suggestion.lower()
        
        # High priority keywords
        if any(word in suggestion_lower for word in ['accessibility', 'screen reader', 'keyboard']):
            score += 10
        if any(word in suggestion_lower for word in ['security', 'privacy', 'legal']):
            score += 9
        if any(word in suggestion_lower for word in ['technical', 'specific', 'context']):
            score += 8
        
        # Medium priority keywords
        if any(word in suggestion_lower for word in ['descriptive', 'clear', 'precise']):
            score += 5
        if any(word in suggestion_lower for word in ['replace', 'rewrite', 'change']):
            score += 4
        
        # Length bonus for more detailed suggestions
        if len(suggestion) > 50:
            score += 2
        
        return score
    
    def _determine_severity(self, severities: List[str], consolidation_strategy: Dict[str, Any]) -> str:
        """Determine consolidated severity level."""
        if not severities:
            return 'medium'
        
        # Convert severity levels to numeric values for comparison
        severity_values = {'low': 1, 'medium': 2, 'high': 3}
        numeric_severities = [severity_values.get(sev, 2) for sev in severities]
        
        # Use the highest severity, but escalate if multiple medium/high
        max_severity = max(numeric_severities)
        medium_high_count = sum(1 for sev in numeric_severities if sev >= 2)
        
        if max_severity >= 3 or medium_high_count >= 2:
            return 'high'
        elif max_severity >= 2:
            return 'medium'
        else:
            return 'low'
    
    def _find_primary_error(self, errors: List[Dict[str, Any]], primary_rule: str) -> Dict[str, Any]:
        """Find the error that corresponds to the primary rule."""
        for error in errors:
            if error.get('type') == primary_rule:
                return error
        
        # Fallback to first error if primary rule not found
        return errors[0] if errors else {} 

    def _merge_suggestions_with_options(self, suggestion_lists: List[List[str]], 
                                       merger_strategy: str, span_group: SpanGroup) -> List[str]:
        """
        Enhanced suggestion merging that can provide multiple fix strategies.
        """
        # For nested spans, we want to provide both quick and comprehensive fixes
        if span_group.consolidation_type == 'nested' and len(span_group.spans) > 1:
            return self._create_layered_suggestions(suggestion_lists, span_group)
        
        # Otherwise use the standard merging
        return self._merge_suggestions(suggestion_lists, merger_strategy)
    
    def _create_layered_suggestions(self, suggestion_lists: List[List[str]], 
                                   span_group: SpanGroup) -> List[str]:
        """
        Create layered suggestions for nested spans, offering both quick and comprehensive fixes.
        """
        layered_suggestions = []
        
        # Sort spans by length (shortest to longest for progressive fixes)
        sorted_spans = sorted(span_group.spans, key=lambda s: len(s.text))
        
        # Quick fix (smallest span)
        if len(sorted_spans) >= 1:
            quick_span = sorted_spans[0]
            quick_suggestions = self._get_suggestions_for_span(suggestion_lists, span_group, quick_span)
            if quick_suggestions:
                layered_suggestions.append(f"Quick fix: {quick_suggestions[0]}")
        
        # Comprehensive fix (largest span)
        if len(sorted_spans) >= 2:
            comprehensive_span = sorted_spans[-1]
            comprehensive_suggestions = self._get_suggestions_for_span(suggestion_lists, span_group, comprehensive_span)
            if comprehensive_suggestions:
                layered_suggestions.append(f"Comprehensive fix: {comprehensive_suggestions[0]}")
        
        # Add any remaining unique suggestions
        all_unique_suggestions = set()
        for suggestions in suggestion_lists:
            all_unique_suggestions.update(suggestions)
        
        for suggestion in all_unique_suggestions:
            if not any(suggestion.lower() in existing.lower() for existing in layered_suggestions):
                layered_suggestions.append(suggestion)
        
        return layered_suggestions[:5]  # Limit to top 5 suggestions
    
    def _get_suggestions_for_span(self, suggestion_lists: List[List[str]], 
                                 span_group: SpanGroup, target_span: TextSpan) -> List[str]:
        """
        Get suggestions that are most relevant to a specific span.
        """
        # Find errors that contain this span
        relevant_suggestions = []
        
        for i, error in enumerate(span_group.errors):
            if i < len(suggestion_lists):
                # Check if this error's text matches or contains the target span
                error_text = error.get('text_segment', '').lower()
                if target_span.text.lower() in error_text or error_text in target_span.text.lower():
                    relevant_suggestions.extend(suggestion_lists[i])
        
        return list(dict.fromkeys(relevant_suggestions))  # Remove duplicates while preserving order
    
    def _generate_fix_options(self, span_group: SpanGroup) -> List[Dict[str, Any]]:
        """
        Generate multiple fix options for nested spans.
        """
        fix_options = []
        
        # Sort spans by length for progressive fix options
        sorted_spans = sorted(span_group.spans, key=lambda s: len(s.text))
        
        for i, span in enumerate(sorted_spans):
            option_type = "quick" if i == 0 else "comprehensive" if i == len(sorted_spans) - 1 else "intermediate"
            
            # Get relevant suggestions for this span
            relevant_errors = [error for error in span_group.errors 
                             if span.text.lower() in error.get('message', '').lower()]
            
            if relevant_errors:
                fix_options.append({
                    'type': option_type,
                    'text_span': span.text,
                    'description': f"Fix '{span.text}' specifically",
                    'suggestions': relevant_errors[0].get('suggestions', [])[:2],  # Top 2 suggestions
                    'scope': 'minimal' if option_type == 'quick' else 'comprehensive'
                })
        
        return fix_options 
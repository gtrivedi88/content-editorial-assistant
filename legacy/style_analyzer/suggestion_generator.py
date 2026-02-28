"""
Suggestion Generator Module
Generates safe and helpful suggestions based on analysis results.
Designed to provide actionable feedback without false positives.
"""

import logging
from typing import List, Dict, Any, Optional

from .base_types import (
    SuggestionDict, ErrorDict, StatisticsDict, TechnicalMetricsDict,
    create_suggestion, DEFAULT_RULES
)

logger = logging.getLogger(__name__)


class SuggestionGenerator:
    """Generates safe suggestions based on analysis results."""
    
    def __init__(self, rules: Optional[dict] = None):
        """Initialize suggestion generator with rules."""
        self.rules = rules or DEFAULT_RULES.copy()
    
    def generate_suggestions(
        self, 
        errors: List[ErrorDict], 
        statistics: StatisticsDict, 
        technical_metrics: TechnicalMetricsDict
    ) -> List[SuggestionDict]:
        """Generate safe suggestions based on analysis results."""
        suggestions = []
        
        try:
            # Generate error-based suggestions
            error_suggestions = self._generate_error_suggestions(errors)
            suggestions.extend(error_suggestions)
            
            # Generate statistics-based suggestions
            stats_suggestions = self._generate_statistics_suggestions(statistics)
            suggestions.extend(stats_suggestions)
            
            # Generate technical metrics suggestions
            metrics_suggestions = self._generate_metrics_suggestions(technical_metrics)
            suggestions.extend(metrics_suggestions)
            
            # Generate general improvement suggestions
            general_suggestions = self._generate_general_suggestions(
                errors, statistics, technical_metrics
            )
            suggestions.extend(general_suggestions)
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            # Return basic safety suggestion
            suggestions = [create_suggestion(
                suggestion_type='general',
                message='Review your text for clarity and readability.',
                priority='medium'
            )]
        
        return suggestions
    
    def _generate_error_suggestions(self, errors: List[ErrorDict]) -> List[SuggestionDict]:
        """Generate suggestions based on specific errors found."""
        suggestions = []
        
        if not errors:
            return suggestions
        
        try:
            # Count error types
            error_types = {}
            for error in errors:
                error_type = error.get('type', 'unknown')
                error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Generate suggestions based on error patterns
            if error_types.get('sentence_length', 0) > 2:
                suggestions.append(create_suggestion(
                    suggestion_type='sentence_length',
                    message='Consider breaking long sentences into shorter ones for better readability.',
                    priority='medium'
                ))
            
            if error_types.get('readability', 0) > 0:
                suggestions.append(create_suggestion(
                    suggestion_type='readability',
                    message='Consider using simpler language and shorter sentences.',
                    priority='high'
                ))
            
            if error_types.get('passive_voice', 0) > 1:
                suggestions.append(create_suggestion(
                    suggestion_type='passive_voice',
                    message='Consider using active voice for clearer, more direct writing.',
                    priority='medium'
                ))
            
            if error_types.get('complexity', 0) > 1:
                suggestions.append(create_suggestion(
                    suggestion_type='complexity',
                    message='Consider simplifying complex sentences and technical language.',
                    priority='medium'
                ))
            
        except Exception as e:
            logger.error(f"Error generating error suggestions: {e}")
        
        return suggestions
    
    def _generate_statistics_suggestions(self, statistics: StatisticsDict) -> List[SuggestionDict]:
        """Generate suggestions based on text statistics."""
        suggestions = []
        
        if not statistics:
            return suggestions
        
        try:
            # Check sentence length variety
            sentence_variety = statistics.get('sentence_length_variety', 0.5)
            if sentence_variety < 0.3:
                suggestions.append(create_suggestion(
                    suggestion_type='sentence_variety',
                    message='Consider varying your sentence lengths for better flow.',
                    priority='low'
                ))
            
            # Check average sentence length
            avg_sentence_length = statistics.get('avg_sentence_length', 0)
            if avg_sentence_length > 25:
                suggestions.append(create_suggestion(
                    suggestion_type='sentence_length',
                    message='Your sentences are averaging over 25 words. Consider breaking them up.',
                    priority='medium'
                ))
            
            # Check paragraph length
            avg_paragraph_length = statistics.get('avg_paragraph_length', 0)
            if avg_paragraph_length > 150:
                suggestions.append(create_suggestion(
                    suggestion_type='paragraph_length',
                    message='Consider breaking long paragraphs into shorter ones.',
                    priority='low'
                ))
            
            # Check word count for substantial content
            word_count = statistics.get('word_count', 0)
            if word_count < 50:
                suggestions.append(create_suggestion(
                    suggestion_type='content_length',
                    message='Consider expanding your content for more comprehensive analysis.',
                    priority='low'
                ))
            
        except Exception as e:
            logger.error(f"Error generating statistics suggestions: {e}")
        
        return suggestions
    
    def _generate_metrics_suggestions(self, technical_metrics: TechnicalMetricsDict) -> List[SuggestionDict]:
        """Generate suggestions based on technical metrics."""
        suggestions = []
        
        if not technical_metrics:
            return suggestions
        
        try:
            # Check readability score
            readability_score = technical_metrics.get('readability_score', 0)
            if readability_score < 60:
                suggestions.append(create_suggestion(
                    suggestion_type='readability',
                    message='Consider improving readability by using simpler words and shorter sentences.',
                    priority='high'
                ))
            
            # Check grade level
            grade_level = technical_metrics.get('grade_level', 0)
            if grade_level > 12:
                suggestions.append(create_suggestion(
                    suggestion_type='grade_level',
                    message='Consider simplifying language to reach a broader audience.',
                    priority='medium'
                ))
            
            # Check error density
            error_density = technical_metrics.get('error_density', 0)
            if error_density > 0.5:
                suggestions.append(create_suggestion(
                    suggestion_type='error_density',
                    message='Focus on addressing the most common issues first.',
                    priority='high'
                ))
            
        except Exception as e:
            logger.error(f"Error generating metrics suggestions: {e}")
        
        return suggestions
    
    def _generate_general_suggestions(
        self, 
        errors: List[ErrorDict], 
        statistics: StatisticsDict, 
        technical_metrics: TechnicalMetricsDict
    ) -> List[SuggestionDict]:
        """Generate general improvement suggestions."""
        suggestions = []
        
        try:
            # Overall performance suggestions
            error_count = len(errors)
            readability_score = technical_metrics.get('readability_score', 60)
            
            if error_count == 0 and readability_score > 70:
                suggestions.append(create_suggestion(
                    suggestion_type='achievement',
                    message='Great work! Your text shows good style and readability.',
                    priority='low'
                ))
            
            elif error_count > 0 and readability_score < 50:
                suggestions.append(create_suggestion(
                    suggestion_type='improvement',
                    message='Focus on both fixing specific issues and improving overall readability.',
                    priority='high'
                ))
            
            elif error_count > 0:
                suggestions.append(create_suggestion(
                    suggestion_type='improvement',
                    message='Address the specific issues highlighted to improve your text.',
                    priority='medium'
                ))
            
            elif readability_score < 60:
                suggestions.append(create_suggestion(
                    suggestion_type='readability',
                    message='Your text is technically correct but could be more readable.',
                    priority='medium'
                ))
            
            # Technical writing specific suggestions
            word_count = statistics.get('word_count', 0)
            if word_count > 500:
                suggestions.append(create_suggestion(
                    suggestion_type='technical_writing',
                    message='For technical writing, consider using headings and bullet points to organize content.',
                    priority='low'
                ))
            
        except Exception as e:
            logger.error(f"Error generating general suggestions: {e}")
        
        return suggestions
    
    def generate_improvement_plan(
        self, 
        errors: List[ErrorDict], 
        statistics: StatisticsDict, 
        technical_metrics: TechnicalMetricsDict
    ) -> Dict[str, Any]:
        """Generate a structured improvement plan."""
        plan = {
            'immediate_actions': [],
            'medium_term_goals': [],
            'long_term_objectives': [],
            'priority_order': []
        }
        
        try:
            error_count = len(errors)
            readability_score = technical_metrics.get('readability_score', 60)
            
            # Immediate actions (high priority)
            if error_count > 3:
                plan['immediate_actions'].append(
                    'Focus on the most frequent error types first'
                )
            
            if readability_score < 50:
                plan['immediate_actions'].append(
                    'Simplify complex sentences and vocabulary'
                )
            
            # Medium-term goals
            if readability_score < 70:
                plan['medium_term_goals'].append(
                    'Improve overall readability to 70+ score'
                )
            
            avg_sentence_length = statistics.get('avg_sentence_length', 0)
            if avg_sentence_length > 20:
                plan['medium_term_goals'].append(
                    'Reduce average sentence length to under 20 words'
                )
            
            # Long-term objectives
            plan['long_term_objectives'].append(
                'Achieve consistent, clear technical writing style'
            )
            
            # Priority order
            plan['priority_order'] = [
                'Fix high-severity errors',
                'Improve readability',
                'Enhance sentence structure',
                'Refine overall style'
            ]
            
        except Exception as e:
            logger.error(f"Error generating improvement plan: {e}")
        
        return plan 
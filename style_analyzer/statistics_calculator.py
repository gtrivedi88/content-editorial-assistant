"""
Statistics Calculator Module
Handles all statistics and metrics calculation safely without analysis conflicts.
Designed for reliability and zero false positives.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from collections import Counter

try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

from .base_types import (
    StatisticsDict, TechnicalMetricsDict, DEFAULT_RULES,
    safe_textstat_call, safe_float_conversion
)

logger = logging.getLogger(__name__)


class StatisticsCalculator:
    """Handles safe calculation of text statistics and technical metrics."""
    
    def __init__(self, rules: Optional[dict] = None):
        """Initialize statistics calculator with rules."""
        self.rules = rules or DEFAULT_RULES.copy()
    
    def calculate_safe_statistics(self, text: str, sentences: List[str], paragraphs: List[str]) -> StatisticsDict:
        """Calculate statistics safely without analysis conflicts."""
        stats = {
            'word_count': 0,
            'sentence_count': 0,
            'paragraph_count': 0,
            'avg_sentence_length': 0.0,
            'avg_paragraph_length': 0.0,
            'character_count': 0,
            'character_count_no_spaces': 0,
            'sentence_types': {'simple': 0, 'compound': 0, 'complex': 0}
        }
        
        if not text.strip():
            return stats
            
        try:
            # Basic counts
            words = text.split()
            stats['word_count'] = len(words)
            stats['sentence_count'] = len([s for s in sentences if s.strip()])
            stats['paragraph_count'] = len([p for p in paragraphs if p.strip()])
            stats['character_count'] = len(text)
            stats['character_count_no_spaces'] = len(text.replace(' ', ''))
            
            # Calculate averages safely
            valid_sentences = [s for s in sentences if s.strip()]
            if valid_sentences:
                sentence_lengths = [len(s.split()) for s in valid_sentences]
                stats['avg_sentence_length'] = sum(sentence_lengths) / len(sentence_lengths)
                
            valid_paragraphs = [p for p in paragraphs if p.strip()]
            if valid_paragraphs:
                paragraph_lengths = [len(p.split()) for p in valid_paragraphs]
                stats['avg_paragraph_length'] = sum(paragraph_lengths) / len(paragraph_lengths)
                
            # Safe sentence type analysis (conservative)
            for sentence in valid_sentences:
                if ';' in sentence and (',' in sentence or ' and ' in sentence):
                    stats['sentence_types']['complex'] += 1
                elif ' and ' in sentence or ' or ' in sentence or ' but ' in sentence:
                    stats['sentence_types']['compound'] += 1
                else:
                    stats['sentence_types']['simple'] += 1
                    
        except Exception as e:
            logger.error(f"Error calculating safe statistics: {e}")
        
        return stats
    
    def calculate_comprehensive_statistics(self, text: str, sentences: List[str], paragraphs: List[str]) -> StatisticsDict:
        """Calculate comprehensive statistics including readability metrics."""
        # Start with safe statistics
        stats = self.calculate_safe_statistics(text, sentences, paragraphs)
        
        if not text.strip() or len(text) < 50:
            return stats
            
        try:
            # Add detailed sentence analysis
            sentence_stats = self._calculate_sentence_statistics(sentences)
            stats.update(sentence_stats)
            
            # Add word analysis
            word_stats = self._calculate_word_statistics(text)
            stats.update(word_stats)
            
            # Add readability metrics if textstat is available
            if TEXTSTAT_AVAILABLE:
                readability_stats = self._calculate_readability_statistics(text)
                stats.update(readability_stats)
                
            # Add language patterns
            pattern_stats = self._calculate_pattern_statistics(text)
            stats.update(pattern_stats)
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive statistics: {e}")
            
        return stats
    
    def calculate_safe_technical_metrics(self, text: str, sentences: List[str], error_count: int) -> TechnicalMetricsDict:
        """Calculate technical writing metrics safely."""
        metrics = {
            'readability_score': 0.0,
            'grade_level': 0.0,
            'error_density': 0.0,
            'improvement_opportunities': 0
        }
        
        if not text.strip():
            return metrics
            
        try:
            # Only calculate for substantial text
            if len(text) > 50 and TEXTSTAT_AVAILABLE:
                metrics['readability_score'] = safe_textstat_call(
                    getattr(textstat, 'flesch_reading_ease', lambda x: 0), text
                )
                
                # Use flesch_kincaid_grade for numeric grade level instead of text_standard
                metrics['grade_level'] = safe_textstat_call(
                    getattr(textstat, 'flesch_kincaid_grade', lambda x: 0), text
                )
                
            # Safe error density calculation
            valid_sentences = [s for s in sentences if s.strip()]
            if valid_sentences:
                metrics['error_density'] = error_count / len(valid_sentences)
                
            # Conservative improvement opportunities
            metrics['improvement_opportunities'] = min(error_count, 10)  # Cap at 10
            
        except Exception as e:
            logger.error(f"Error calculating safe technical metrics: {e}")
        
        return metrics
    
    def calculate_comprehensive_technical_metrics(self, text: str, sentences: List[str], errors: List[Dict[str, Any]]) -> TechnicalMetricsDict:
        """Calculate comprehensive technical writing metrics."""
        # Start with safe metrics
        metrics = self.calculate_safe_technical_metrics(text, sentences, len(errors))
        
        if not text.strip() or len(text) < 50:
            return metrics
            
        try:
            # Add detailed readability metrics
            if TEXTSTAT_AVAILABLE:
                readability_metrics = self._calculate_detailed_readability_metrics(text)
                metrics.update(readability_metrics)
                
            # Add grade level analysis
            grade_analysis = self._calculate_grade_level_analysis(text)
            metrics.update(grade_analysis)
            
            # Add complexity analysis
            complexity_metrics = self._calculate_complexity_metrics(text, sentences)
            metrics.update(complexity_metrics)
            
            # Add error analysis
            error_metrics = self._calculate_error_metrics(errors, sentences)
            metrics.update(error_metrics)
            
        except Exception as e:
            logger.error(f"Error calculating comprehensive technical metrics: {e}")
            
        return metrics
    
    def _calculate_sentence_statistics(self, sentences: List[str]) -> Dict[str, Any]:
        """Calculate detailed sentence statistics."""
        stats = {
            'median_sentence_length': 0.0,
            'sentence_length_variety': 0.0,
            'longest_sentence': 0,
            'shortest_sentence': 0
        }
        
        valid_sentences = [s for s in sentences if s.strip()]
        if not valid_sentences:
            return stats
            
        try:
            sentence_lengths = [len(s.split()) for s in valid_sentences]
            
            stats['median_sentence_length'] = sorted(sentence_lengths)[len(sentence_lengths) // 2]
            stats['longest_sentence'] = max(sentence_lengths)
            stats['shortest_sentence'] = min(sentence_lengths)
            
            # Calculate sentence length variety (coefficient of variation)
            if sentence_lengths:
                avg_length = sum(sentence_lengths) / len(sentence_lengths)
                if avg_length > 0:
                    variance = sum((x - avg_length) ** 2 for x in sentence_lengths) / len(sentence_lengths)
                    std_dev = variance ** 0.5
                    stats['sentence_length_variety'] = std_dev / avg_length
                    
        except Exception as e:
            logger.error(f"Error calculating sentence statistics: {e}")
            
        return stats
    
    def _calculate_word_statistics(self, text: str) -> Dict[str, Any]:
        """Calculate word-level statistics."""
        stats = {
            'avg_word_length': 0.0,
            'avg_syllables_per_word': 0.0,
            'complex_words_count': 0,
            'complex_words_percentage': 0.0,
            'most_common_words': [],
            'word_frequency_distribution': {}
        }
        
        try:
            # Clean and split words
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            if not words:
                return stats
                
            # Calculate word lengths
            word_lengths = [len(word) for word in words]
            stats['avg_word_length'] = sum(word_lengths) / len(word_lengths)
            
            # Calculate syllables and complex words
            total_syllables = 0
            complex_count = 0
            
            for word in words:
                syllables = self._estimate_syllables(word)
                total_syllables += syllables
                if syllables >= 3:
                    complex_count += 1
            
            stats['avg_syllables_per_word'] = total_syllables / len(words)
            stats['complex_words_count'] = complex_count
            stats['complex_words_percentage'] = (complex_count / len(words)) * 100
            
            # Word frequency analysis
            word_counter = Counter(words)
            stats['most_common_words'] = word_counter.most_common(10)
            stats['word_frequency_distribution'] = dict(word_counter.most_common(20))
            
        except Exception as e:
            logger.error(f"Error calculating word statistics: {e}")
            
        return stats
    
    def _calculate_readability_statistics(self, text: str) -> Dict[str, Any]:
        """Calculate readability statistics using textstat."""
        stats = {
            'flesch_reading_ease': 0.0,
            'flesch_kincaid_grade': 0.0,
            'gunning_fog_index': 0.0,
            'smog_index': 0.0,
            'coleman_liau_index': 0.0,
            'automated_readability_index': 0.0,
            'dale_chall_readability': 0.0
        }
        
        if not TEXTSTAT_AVAILABLE or not text.strip():
            return stats
            
        try:
            stats['flesch_reading_ease'] = safe_textstat_call(getattr(textstat, 'flesch_reading_ease', lambda x: 0), text)
            stats['flesch_kincaid_grade'] = safe_textstat_call(getattr(textstat, 'flesch_kincaid_grade', lambda x: 0), text)
            stats['gunning_fog_index'] = safe_textstat_call(getattr(textstat, 'gunning_fog', lambda x: 0), text)
            stats['smog_index'] = safe_textstat_call(getattr(textstat, 'smog_index', lambda x: 0), text)
            stats['coleman_liau_index'] = safe_textstat_call(getattr(textstat, 'coleman_liau_index', lambda x: 0), text)
            stats['automated_readability_index'] = safe_textstat_call(getattr(textstat, 'automated_readability_index', lambda x: 0), text)
            stats['dale_chall_readability'] = safe_textstat_call(getattr(textstat, 'dale_chall_readability_score', lambda x: 0), text)
            
        except Exception as e:
            logger.error(f"Error calculating readability statistics: {e}")
            
        return stats
    
    def _calculate_pattern_statistics(self, text: str) -> Dict[str, Any]:
        """Calculate language pattern statistics."""
        stats = {
            'passive_voice_percentage': 0.0,
            'technical_complexity_score': 0.0
        }
        
        try:
            # Basic passive voice detection (conservative)
            sentences = re.split(r'[.!?]+', text)
            valid_sentences = [s for s in sentences if s.strip()]
            
            if valid_sentences:
                passive_count = 0
                for sentence in valid_sentences:
                    # Very conservative passive detection
                    if re.search(r'\b(was|were|is|are|being|been)\s+\w*(ed|en)\b', sentence, re.IGNORECASE):
                        passive_count += 1
                
                stats['passive_voice_percentage'] = (passive_count / len(valid_sentences)) * 100
                
        except Exception as e:
            logger.error(f"Error calculating pattern statistics: {e}")
            
        return stats
    
    def _calculate_detailed_readability_metrics(self, text: str) -> Dict[str, Any]:
        """Calculate detailed readability metrics."""
        metrics = {
            'readability_category': 'unknown',
            'meets_target_grade': False,
            'readability_recommendations': []
        }
        
        try:
            flesch_score = safe_textstat_call(getattr(textstat, 'flesch_reading_ease', lambda x: 0), text)
            
            # Categorize readability
            if flesch_score >= 90:
                metrics['readability_category'] = 'Very Easy'
            elif flesch_score >= 80:
                metrics['readability_category'] = 'Easy'
            elif flesch_score >= 70:
                metrics['readability_category'] = 'Fairly Easy'
            elif flesch_score >= 60:
                metrics['readability_category'] = 'Standard'
            elif flesch_score >= 50:
                metrics['readability_category'] = 'Fairly Difficult'
            elif flesch_score >= 30:
                metrics['readability_category'] = 'Difficult'
            else:
                metrics['readability_category'] = 'Very Difficult'
                
        except Exception as e:
            logger.error(f"Error calculating detailed readability metrics: {e}")
            
        return metrics
    
    def _calculate_grade_level_analysis(self, text: str) -> Dict[str, Any]:
        """Calculate grade level analysis."""
        analysis = {
            'estimated_grade_level': 0.0,
            'grade_level_category': 'unknown',
            'meets_target_grade': False
        }
        
        try:
            # Use flesch_kincaid_grade for numeric grade level instead of text_standard
            grade_level = safe_textstat_call(
                getattr(textstat, 'flesch_kincaid_grade', lambda x: 0), text
            )
            
            analysis['estimated_grade_level'] = grade_level
            
            # Categorize grade level
            if grade_level <= 8:
                analysis['grade_level_category'] = 'Elementary/Middle School'
            elif grade_level <= 12:
                analysis['grade_level_category'] = 'High School'
            elif grade_level <= 16:
                analysis['grade_level_category'] = 'College Level'
            else:
                analysis['grade_level_category'] = 'Graduate Level'
                
            # Check target
            target_min, target_max = self.rules['target_grade_level']
            analysis['meets_target_grade'] = target_min <= grade_level <= target_max
            
        except Exception as e:
            logger.error(f"Error calculating grade level analysis: {e}")
            
        return analysis
    
    def _calculate_complexity_metrics(self, text: str, sentences: List[str]) -> Dict[str, Any]:
        """Calculate complexity metrics."""
        metrics = {
            'sentence_complexity_score': 0.0,
            'vocabulary_complexity_score': 0.0,
            'overall_complexity_rating': 'unknown'
        }
        
        try:
            # Calculate sentence complexity based on length and punctuation
            valid_sentences = [s for s in sentences if s.strip()]
            if valid_sentences:
                complexity_scores = []
                for sentence in valid_sentences:
                    # Simple complexity based on length and punctuation
                    length_factor = len(sentence.split()) / 20.0  # Normalize to ~20 words
                    punctuation_factor = sentence.count(',') * 0.1 + sentence.count(';') * 0.2
                    complexity_scores.append(length_factor + punctuation_factor)
                
                metrics['sentence_complexity_score'] = sum(complexity_scores) / len(complexity_scores)
            
            # Calculate vocabulary complexity
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            if words:
                total_syllables = sum(self._estimate_syllables(word) for word in words)
                metrics['vocabulary_complexity_score'] = total_syllables / len(words)
                
        except Exception as e:
            logger.error(f"Error calculating complexity metrics: {e}")
            
        return metrics
    
    def _calculate_error_metrics(self, errors: List[Dict[str, Any]], sentences: List[str]) -> Dict[str, Any]:
        """Calculate error-related metrics."""
        metrics = {
            'error_types': {},
            'severity_distribution': {},
            'confidence_average': 0.0
        }
        
        try:
            if errors:
                # Count error types
                error_types = [error.get('type', 'unknown') for error in errors]
                metrics['error_types'] = dict(Counter(error_types))
                
                # Count severity distribution
                severities = [error.get('severity', 'unknown') for error in errors]
                metrics['severity_distribution'] = dict(Counter(severities))
                
                # Calculate average confidence
                confidences = [error.get('confidence', 0.5) for error in errors if 'confidence' in error]
                if confidences:
                    metrics['confidence_average'] = sum(confidences) / len(confidences)
                    
        except Exception as e:
            logger.error(f"Error calculating error metrics: {e}")
            
        return metrics
    
    def _estimate_syllables(self, word: str) -> int:
        """Estimate syllables in a word using simple rules."""
        if not word or not word.strip():
            return 1
            
        word = word.lower().strip()
        count = 0
        vowels = "aeiouy"
        
        # Count vowel groups
        if word[0] in vowels:
            count += 1
            
        for index in range(1, len(word)):
            if word[index] in vowels and word[index - 1] not in vowels:
                count += 1
                
        # Adjust for silent 'e'
        if word.endswith("e") and count > 1:
            count -= 1
            
        # Ensure at least one syllable
        return max(count, 1)
    
    def split_paragraphs_safe(self, text: str) -> List[str]:
        """Split text into paragraphs safely."""
        if not text.strip():
            return []
            
        try:
            paragraphs = re.split(r'\n\s*\n', text)
            return [p.strip() for p in paragraphs if p.strip()]
        except Exception as e:
            logger.error(f"Error splitting paragraphs: {e}")
            return [text]  # Return whole text as single paragraph 
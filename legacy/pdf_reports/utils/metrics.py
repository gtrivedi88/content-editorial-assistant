"""
Metrics Calculator Module

AUTHORITATIVE SOURCE for all scoring calculations.
This module provides the SINGLE source of truth for:
- Grade level extraction
- Readability metrics
- Overall score calculation
- Engagement metrics
- LLM readiness score

All other modules should delegate to this class to ensure consistency.
"""

from typing import Dict, Any, Optional, Tuple, List
import logging
import re

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    AUTHORITATIVE calculator for all writing metrics and scores.
    
    This class is the SINGLE SOURCE OF TRUTH for scoring.
    Other modules (StyleAnalyzer, StructuralAnalyzer, frontend) should
    use this class to ensure consistent scores across the application.
    """
    
    # Industry benchmarks for technical writing
    BENCHMARKS = {
        'grade_level': {'target': 10.0, 'min': 8.0, 'max': 12.0},
        'flesch_reading_ease': {'target': 60.0, 'min': 50.0, 'max': 70.0},
        'sentence_length': {'target': 17.0, 'min': 15.0, 'max': 20.0},
        'passive_voice': {'target': 10.0, 'max': 15.0},
        'complex_words': {'target': 15.0, 'max': 20.0},
        'vocabulary_diversity': {'target': 0.7, 'min': 0.5},
    }
    
    @staticmethod
    def _priority_get(primary: Dict[str, Any], secondary: Dict[str, Any], key: str, default: Any = 0) -> Any:
        """
        Get value from primary dict, falling back to secondary if primary value is None.
        
        Unlike the `or` operator, this correctly handles falsy values like 0,
        which are valid metric values (e.g., flesch_reading_ease=0 indicates
        extremely difficult text).
        """
        value = primary.get(key)
        return value if value is not None else secondary.get(key, default)
    
    @classmethod
    def get_unified_metrics(cls, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and unify all metrics from analysis data.
        
        This resolves the issue of metrics being stored in both
        'statistics' and 'technical_writing_metrics' by providing
        a single, consistent view of all metrics.
        
        Returns:
            Dict with all metrics unified into a single namespace
        """
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        
        # Unified metrics - technical_writing_metrics takes priority
        # Use _priority_get to correctly handle 0 values (which are valid metrics)
        unified = {
            # Readability scores (prefer technical_writing_metrics)
            'flesch_reading_ease': cls._priority_get(technical_metrics, statistics, 'flesch_reading_ease', 0),
            'flesch_kincaid_grade': cls._priority_get(technical_metrics, statistics, 'flesch_kincaid_grade', 0),
            'gunning_fog_index': cls._priority_get(technical_metrics, statistics, 'gunning_fog_index', 0),
            'smog_index': cls._priority_get(technical_metrics, statistics, 'smog_index', 0),
            'coleman_liau_index': cls._priority_get(technical_metrics, statistics, 'coleman_liau_index', 0),
            'automated_readability_index': cls._priority_get(technical_metrics, statistics, 'automated_readability_index', 0),
            'dale_chall_readability': cls._priority_get(technical_metrics, statistics, 'dale_chall_readability', 0),
            
            # Grade level (unified extraction)
            'estimated_grade_level': cls.extract_grade_level(analysis_data),
            'grade_level_category': technical_metrics.get('grade_level_category') if technical_metrics.get('grade_level_category') is not None else cls._get_grade_level_category(cls.extract_grade_level(analysis_data)),
            'meets_target_grade': technical_metrics.get('meets_target_grade', cls._check_target_grade(cls.extract_grade_level(analysis_data))),
            
            # Document statistics (from statistics)
            'word_count': statistics.get('word_count', 0),
            'sentence_count': statistics.get('sentence_count', 0),
            'paragraph_count': statistics.get('paragraph_count', 0),
            'character_count': statistics.get('character_count', 0),
            'avg_sentence_length': statistics.get('avg_sentence_length', 0),
            'avg_paragraph_length': statistics.get('avg_paragraph_length', 0),
            
            # Quality metrics
            'passive_voice_percentage': statistics.get('passive_voice_percentage', 0),
            'complex_words_percentage': statistics.get('complex_words_percentage', 0),
            'vocabulary_diversity': statistics.get('vocabulary_diversity', 0),
            
            # Readability category (unified)
            'readability_category': technical_metrics.get('readability_category') if technical_metrics.get('readability_category') is not None else cls._get_readability_category(
                cls._priority_get(technical_metrics, statistics, 'flesch_reading_ease', 0)
            ),
        }
        
        return unified
    
    @classmethod
    def _get_grade_level_category(cls, grade_level: float) -> str:
        """Get grade level category description."""
        if grade_level <= 8:
            return 'Elementary/Middle School'
        elif grade_level <= 12:
            return 'High School'
        elif grade_level <= 16:
            return 'College Level'
        else:
            return 'Graduate Level'
    
    @classmethod
    def _check_target_grade(cls, grade_level: float) -> bool:
        """Check if grade level meets target range (9-11 for technical writing)."""
        return 9 <= grade_level <= 11
    
    @classmethod
    def _get_readability_category(cls, flesch_score: float) -> str:
        """Get readability category based on Flesch Reading Ease score."""
        if flesch_score >= 90:
            return 'Very Easy'
        elif flesch_score >= 80:
            return 'Easy'
        elif flesch_score >= 70:
            return 'Fairly Easy'
        elif flesch_score >= 60:
            return 'Standard'
        elif flesch_score >= 50:
            return 'Fairly Difficult'
        elif flesch_score >= 30:
            return 'Difficult'
        else:
            return 'Very Difficult'
    
    @classmethod
    def extract_grade_level(cls, analysis_data: Dict[str, Any]) -> float:
        """
        Extract grade level from analysis data using a consistent priority order.
        
        Priority:
        1. technical_writing_metrics.estimated_grade_level (most reliable if computed)
        2. technical_writing_metrics.flesch_kincaid_grade
        3. statistics.flesch_kincaid_grade
        4. Derived from Flesch Reading Ease score
        5. Default: 10.0
        """
        try:
            technical_metrics = analysis_data.get('technical_writing_metrics', {})
            statistics = analysis_data.get('statistics', {})
            
            # Priority order for grade level sources
            sources = [
                technical_metrics.get('estimated_grade_level'),
                technical_metrics.get('flesch_kincaid_grade'),
                statistics.get('flesch_kincaid_grade'),
                statistics.get('estimated_grade_level'),
            ]
            
            for source in sources:
                if source is not None and isinstance(source, (int, float)) and source > 0:
                    return float(source)
            
            # Derive from Flesch Reading Ease if available
            flesch = cls._priority_get(technical_metrics, statistics, 'flesch_reading_ease', 0)
            if flesch > 0:
                return cls._flesch_to_grade(flesch)
            
            return 10.0  # Default for technical writing
            
        except Exception as e:
            logger.error(f"Error extracting grade level: {e}")
            return 10.0
    
    @classmethod
    def _flesch_to_grade(cls, flesch_score: float) -> float:
        """Convert Flesch Reading Ease to approximate grade level."""
        if flesch_score >= 90:
            return 5.0
        elif flesch_score >= 80:
            return 6.0
        elif flesch_score >= 70:
            return 7.0
        elif flesch_score >= 60:
            return 8.5
        elif flesch_score >= 50:
            return 10.0
        elif flesch_score >= 30:
            return 13.0
        else:
            return 16.0
    
    @classmethod
    def calculate_overall_score(cls, analysis_data: Dict[str, Any]) -> float:
        """
        Calculate overall writing quality score (0-100).
        
        THIS IS THE AUTHORITATIVE SCORING METHOD.
        All other modules should call this method instead of implementing their own.
        
        Scoring components:
        - Grade level (25%): Optimal at grade 10 for technical writing
        - Readability (20%): Flesch Reading Ease score
        - Sentence length (15%): Optimal at 17 words
        - Passive voice (15%): Lower is better
        - Error density (15%): Fewer errors = higher score
        - Vocabulary diversity (10%): Higher diversity = better
        """
        scores = []
        weights = []
        
        # Get unified metrics
        unified = cls.get_unified_metrics(analysis_data)
        errors = analysis_data.get('errors', [])
        
        # Grade level score (weight: 25%)
        grade_level = unified['estimated_grade_level']
        grade_score = cls._score_in_range(grade_level, 8, 12, optimal=10)
        scores.append(grade_score)
        weights.append(0.25)
        
        # Readability score (weight: 20%)
        flesch = unified['flesch_reading_ease']
        readability_score = cls._score_in_range(flesch, 40, 80, optimal=60)
        scores.append(readability_score)
        weights.append(0.20)
        
        # Sentence length score (weight: 15%)
        avg_sentence = unified['avg_sentence_length'] or 17
        sentence_score = cls._score_in_range(avg_sentence, 10, 25, optimal=17)
        scores.append(sentence_score)
        weights.append(0.15)
        
        # Passive voice score (weight: 15%)
        passive_pct = unified['passive_voice_percentage']
        passive_score = max(0, 100 - (passive_pct * 4))  # Penalize passive voice
        scores.append(passive_score)
        weights.append(0.15)
        
        # Error density score (weight: 15%)
        word_count = unified['word_count'] or 1
        error_rate = (len(errors) / max(word_count, 1)) * 100
        error_score = max(0, 100 - (error_rate * 50))
        scores.append(error_score)
        weights.append(0.15)
        
        # Vocabulary diversity score (weight: 10%)
        vocab_diversity = unified['vocabulary_diversity'] or 0.5
        vocab_score = min(100, vocab_diversity * 125)
        scores.append(vocab_score)
        weights.append(0.10)
        
        # Calculate weighted average
        total_score = sum(s * w for s, w in zip(scores, weights))
        return min(100, max(0, total_score))
    
    @classmethod
    def calculate_engagement_metrics(cls, text: str, statistics: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate engagement and tone metrics.
        
        THIS IS THE AUTHORITATIVE ENGAGEMENT CALCULATION.
        Previously this was only done on the frontend - now it's computed
        on the backend to ensure consistency across UI, PDF reports, and database.
        
        Returns:
            Dict with engagement_score, direct_address_percentage, adverb_density, etc.
        """
        if not text or not text.strip():
            return {
                'engagement_score': 0,
                'direct_address_percentage': 0.0,
                'adverb_density': 0.0,
                'engagement_category': 'Unknown',
                'voice_analysis': {
                    'second_person': 0,
                    'first_person': 0,
                    'third_person': 0,
                    'total_pronouns': 0
                },
                'recommendations': []
            }
        
        word_count = statistics.get('word_count') or len(text.split())
        recommendations = []
        
        # Voice Analysis - Direct Address Assessment
        voice_metrics = cls._analyze_voice_pattern(text, word_count)
        
        # Adverb Density Analysis
        adverb_metrics = cls._analyze_adverb_density(text, word_count)
        
        # Calculate overall engagement score
        engagement_score = cls._calculate_engagement_score(voice_metrics, adverb_metrics, recommendations)
        
        # Determine engagement category
        category = cls._get_engagement_category(engagement_score)
        
        return {
            'engagement_score': round(engagement_score),
            'direct_address_percentage': round(voice_metrics['direct_address_percentage'], 1),
            'adverb_density': round(adverb_metrics['density'], 1),
            'engagement_category': category,
            'voice_analysis': voice_metrics,
            'adverb_analysis': adverb_metrics,
            'recommendations': recommendations
        }
    
    @classmethod
    def _analyze_voice_pattern(cls, text: str, word_count: int) -> Dict[str, Any]:
        """Analyze voice patterns and direct address usage."""
        # Performance safeguard: truncate very large documents
        max_chars = 100000  # ~20K words
        if len(text) > max_chars:
            text = text[:max_chars]
        
        # Second person pronouns (direct address)
        second_person_matches = re.findall(r'\b(you|your|yours|yourself|yourselves)\b', text, re.IGNORECASE)
        second_person_count = len(second_person_matches)
        
        # First person pronouns (authorial voice)
        first_person_matches = re.findall(r'\b(I|we|our|us|my|mine|myself|ourselves|me)\b', text, re.IGNORECASE)
        first_person_count = len(first_person_matches)
        
        # Third person pronouns
        third_person_matches = re.findall(r'\b(he|she|it|they|him|her|them|his|hers|its|their|theirs)\b', text, re.IGNORECASE)
        third_person_count = len(third_person_matches)
        
        total_pronouns = second_person_count + first_person_count + third_person_count
        direct_address_percentage = (second_person_count / total_pronouns * 100) if total_pronouns > 0 else 0.0
        
        return {
            'second_person': second_person_count,
            'first_person': first_person_count,
            'third_person': third_person_count,
            'total_pronouns': total_pronouns,
            'direct_address_percentage': direct_address_percentage,
            'words_per_pronoun': word_count / total_pronouns if total_pronouns > 0 else 0
        }
    
    @classmethod
    def _analyze_adverb_density(cls, text: str, word_count: int) -> Dict[str, Any]:
        """Analyze adverb density and writing strength."""
        # Performance safeguard: truncate very large documents
        max_chars = 100000  # ~20K words
        if len(text) > max_chars:
            text = text[:max_chars]
        
        # -ly adverbs
        ly_adverbs = re.findall(r'\b\w+ly\b', text, re.IGNORECASE)
        ly_count = len(ly_adverbs)
        
        # Qualifying words that weaken writing
        qualifiers_pattern = r'\b(very|really|quite|rather|somewhat|pretty|fairly|extremely|incredibly|absolutely|completely|totally|entirely|perfectly|exactly|precisely|literally|actually|basically|essentially|generally|typically|usually|normally|obviously|clearly|definitely|certainly|probably|possibly|maybe|perhaps|likely|unlikely)\b'
        qualifiers = re.findall(qualifiers_pattern, text, re.IGNORECASE)
        qualifier_count = len(qualifiers)
        
        total_adverbs = ly_count + qualifier_count
        density = (total_adverbs / word_count * 100) if word_count > 0 else 0.0
        
        return {
            'total_adverbs': total_adverbs,
            'density': density,
            'ly_adverbs': ly_count,
            'qualifiers': qualifier_count,
            'strength_score': max(0, 100 - (density * 10))  # Higher density = lower strength
        }
    
    @classmethod
    def _calculate_engagement_score(cls, voice_metrics: Dict[str, Any], 
                                     adverb_metrics: Dict[str, Any], 
                                     recommendations: List[str]) -> float:
        """Calculate overall engagement score."""
        score = 85.0  # Base score
        
        # Voice Analysis Impact (40% of score)
        direct_address_ratio = voice_metrics['direct_address_percentage'] / 100
        
        if direct_address_ratio >= 0.6:
            score += 15  # Excellent direct address for technical writing
        elif direct_address_ratio >= 0.4:
            score += 5   # Good direct address
        elif direct_address_ratio >= 0.2:
            score -= 5
            recommendations.append('Consider using more direct address ("you") to engage readers')
        else:
            score -= 15
            recommendations.append('Add more direct address ("you", "your") to connect with readers')
        
        # Excessive first person penalty
        if voice_metrics['first_person'] > voice_metrics['second_person'] * 0.5:
            score -= 10
            recommendations.append('Reduce first-person references to maintain professional tone')
        
        # Adverb Density Impact (60% of score)
        if adverb_metrics['density'] <= 3:
            score += 10  # Excellent - strong, direct writing
        elif adverb_metrics['density'] <= 5:
            pass  # Good adverb usage
        elif adverb_metrics['density'] <= 8:
            score -= 10
            recommendations.append('Consider reducing adverbs for stronger, more direct writing')
        else:
            score -= 20
            recommendations.append('Remove unnecessary adverbs and qualifiers to strengthen your writing')
        
        # Qualifier-heavy writing penalty
        if adverb_metrics['qualifiers'] > adverb_metrics['ly_adverbs'] * 1.5:
            score -= 5
            recommendations.append('Reduce hedge words like "really", "very", "quite" for more confident tone')
        
        return max(0, min(100, score))
    
    @classmethod
    def _get_engagement_category(cls, score: float) -> str:
        """Get engagement category based on score."""
        if score >= 85:
            return 'Highly Engaging'
        elif score >= 70:
            return 'Engaging'
        elif score >= 55:
            return 'Moderately Engaging'
        elif score >= 40:
            return 'Needs Improvement'
        else:
            return 'Poor Engagement'
    
    @classmethod
    def _score_in_range(cls, value: float, min_val: float, max_val: float, 
                       optimal: Optional[float] = None) -> float:
        """Score a value based on how well it fits in a range."""
        if optimal is None:
            optimal = (min_val + max_val) / 2
        
        if value < min_val:
            return max(0, 100 - ((min_val - value) / min_val) * 100)
        elif value > max_val:
            return max(0, 100 - ((value - max_val) / max_val) * 50)
        else:
            # Score based on distance from optimal
            distance = abs(value - optimal)
            range_half = max(optimal - min_val, max_val - optimal)
            return 100 - (distance / range_half) * 30
    
    @classmethod
    def calculate_llm_readiness_score(cls, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate LLM/AI readiness score with detailed breakdown."""
        score = 100
        issues = []
        strengths = []
        
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        
        # Word count factor
        word_count = statistics.get('word_count', 0)
        if word_count < 50:
            score -= 30
            issues.append("Content too short for effective LLM processing")
        elif word_count < 100:
            score -= 15
            issues.append("Consider adding more content for better LLM understanding")
        else:
            strengths.append("Sufficient content length for AI processing")
        
        # Sentence structure factor
        avg_sentence_length = statistics.get('avg_sentence_length', 0)
        if avg_sentence_length > 30:
            score -= 20
            issues.append("Very long sentences may confuse LLM processing")
        elif avg_sentence_length < 8:
            score -= 10
            issues.append("Very short sentences may lack context for LLMs")
        else:
            strengths.append("Good sentence length for AI comprehension")
        
        # Readability factor
        flesch_score = technical_metrics.get('flesch_reading_ease', 0)
        if flesch_score < 30:
            score -= 15
            issues.append("Very difficult text may challenge LLM comprehension")
        elif flesch_score >= 50:
            strengths.append("Good readability enhances AI processing accuracy")
        
        # Complex words factor
        complex_words_pct = statistics.get('complex_words_percentage', 0)
        if complex_words_pct > 40:
            score -= 10
            issues.append("High complex word density may reduce LLM accuracy")
        
        final_score = max(0, min(100, score))
        
        return {
            'score': final_score,
            'category': cls._get_llm_category(final_score),
            'issues': issues,
            'strengths': strengths,
        }
    
    @classmethod
    def _get_llm_category(cls, score: float) -> str:
        """Get LLM readiness category."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Needs Improvement"
    
    @classmethod
    def calculate_time_savings(cls, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate estimated time savings from using the analysis."""
        statistics = analysis_data.get('statistics', {})
        errors = analysis_data.get('errors', [])
        
        word_count = statistics.get('word_count', 0)
        error_count = len(errors)
        
        # Base reading time (250 words per minute)
        reading_minutes = word_count / 250
        
        # Manual editing time estimate (30 seconds per error)
        manual_edit_time = error_count * 0.5  # minutes
        
        # AI-assisted editing time (10 seconds per error)
        ai_edit_time = error_count * 0.17  # minutes
        
        # Time saved
        time_saved = manual_edit_time - ai_edit_time
        
        return {
            'reading_time_minutes': round(reading_minutes, 1),
            'manual_edit_minutes': round(manual_edit_time, 1),
            'ai_assisted_minutes': round(ai_edit_time, 1),
            'time_saved_minutes': round(max(0, time_saved), 1),
            'productivity_gain_percent': round((time_saved / max(manual_edit_time, 1)) * 100, 0) if manual_edit_time > 0 else 0
        }
    
    @classmethod
    def get_benchmark_comparison(cls, analysis_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Compare analysis metrics against industry benchmarks."""
        statistics = analysis_data.get('statistics', {})
        technical_metrics = analysis_data.get('technical_writing_metrics', {})
        
        comparisons = {}
        
        # Grade Level
        grade_level = cls.extract_grade_level(analysis_data)
        comparisons['grade_level'] = {
            'value': grade_level,
            'benchmark': cls.BENCHMARKS['grade_level'],
            'status': 'good' if cls.BENCHMARKS['grade_level']['min'] <= grade_level <= cls.BENCHMARKS['grade_level']['max'] else 'needs_improvement',
            'variance': grade_level - cls.BENCHMARKS['grade_level']['target']
        }
        
        # Flesch Reading Ease
        flesch = technical_metrics.get('flesch_reading_ease', 0)
        comparisons['flesch_reading_ease'] = {
            'value': flesch,
            'benchmark': cls.BENCHMARKS['flesch_reading_ease'],
            'status': 'good' if flesch >= cls.BENCHMARKS['flesch_reading_ease']['min'] else 'needs_improvement',
            'variance': flesch - cls.BENCHMARKS['flesch_reading_ease']['target']
        }
        
        # Sentence Length
        avg_sentence = statistics.get('avg_sentence_length', 0)
        comparisons['sentence_length'] = {
            'value': avg_sentence,
            'benchmark': cls.BENCHMARKS['sentence_length'],
            'status': 'good' if cls.BENCHMARKS['sentence_length']['min'] <= avg_sentence <= cls.BENCHMARKS['sentence_length']['max'] else 'needs_improvement',
            'variance': avg_sentence - cls.BENCHMARKS['sentence_length']['target']
        }
        
        # Passive Voice
        passive_pct = statistics.get('passive_voice_percentage', 0)
        comparisons['passive_voice'] = {
            'value': passive_pct,
            'benchmark': cls.BENCHMARKS['passive_voice'],
            'status': 'good' if passive_pct <= cls.BENCHMARKS['passive_voice']['max'] else 'needs_improvement',
            'variance': passive_pct - cls.BENCHMARKS['passive_voice']['target']
        }
        
        return comparisons
    
    @classmethod
    def estimate_reading_time(cls, word_count: int) -> str:
        """Estimate reading time based on word count."""
        minutes = max(1, word_count // 250)
        if minutes == 1:
            return "1 minute"
        elif minutes < 60:
            return f"{minutes} minutes"
        else:
            hours = minutes // 60
            remaining = minutes % 60
            if remaining == 0:
                return f"{hours} hour{'s' if hours > 1 else ''}"
            return f"{hours}h {remaining}m"


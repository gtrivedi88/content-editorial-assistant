"""
Readability Analyzer Module
Handles all readability analysis with different modes based on available capabilities.
Designed for zero false positives with conservative thresholds.
"""

import logging
from typing import List, Optional, Any

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

from .base_types import (
    ErrorDict, AnalysisMethod, ErrorSeverity, CONSERVATIVE_THRESHOLDS,
    DEFAULT_RULES, create_error, safe_textstat_call
)

# Fallback confidence scores when enhanced system not available
FALLBACK_CONFIDENCE_SCORES = {
    AnalysisMethod.SPACY_ENHANCED: 0.8,
    AnalysisMethod.SPACY_LEGACY: 0.8,
    AnalysisMethod.CONSERVATIVE_FALLBACK: 0.6,
    AnalysisMethod.MINIMAL_SAFE: 0.7,
}

logger = logging.getLogger(__name__)


class ReadabilityAnalyzer:
    """Handles readability analysis with fallback mechanisms."""
    
    def __init__(self, rules: Optional[dict] = None):
        """Initialize readability analyzer with rules."""
        self.rules = rules or DEFAULT_RULES.copy()
    
    def analyze_readability_spacy_enhanced(self, text: str, nlp) -> List[ErrorDict]:
        """Enhanced readability check using SpaCy for better accuracy."""
        errors = []
        
        if not nlp or not text.strip():
            return errors
            
        try:
            import textstat  # Lazy import after main.py configures NLTK
            # Use SpaCy to better understand sentence boundaries
            doc = nlp(text)
            sentence_count = len(list(doc.sents))
            
            # Only flag readability if we have sufficient text and clear issues
            if len(text) > 100 and sentence_count > 2:
                flesch_score = safe_textstat_call(getattr(textstat, 'flesch_reading_ease', lambda x: 0), text)
                
                if flesch_score < self.rules['min_readability_score']:
                    error = create_error(
                        error_type='readability',
                        message=f'Text is difficult to read (Flesch score: {flesch_score:.1f}). Aim for 60+ for good readability.',
                        suggestions=[
                            'Use shorter sentences',
                            'Use simpler words',
                            'Break up complex ideas'
                        ],
                        severity=ErrorSeverity.MEDIUM,
                        confidence=FALLBACK_CONFIDENCE_SCORES[AnalysisMethod.SPACY_ENHANCED],
                        analysis_method=AnalysisMethod.SPACY_ENHANCED,
                        score=flesch_score
                    )
                    errors.append(error)
                    
        except Exception as e:
            logger.error(f"SpaCy readability check failed: {e}")
            
        return errors
    
    def analyze_readability_conservative(self, text: str) -> List[ErrorDict]:
        """Conservative readability check with higher thresholds to avoid false positives."""
        errors = []
        
        if not text.strip():
            return errors
            
        try:
            import textstat  # Lazy import after main.py configures NLTK
            # More conservative thresholds
            conservative_min_score = (
                self.rules['min_readability_score'] - 
                CONSERVATIVE_THRESHOLDS['readability_score_buffer']
            )
            
            # Only flag very clear readability issues
            min_length = CONSERVATIVE_THRESHOLDS['readability_min_text_length']
            if len(text) > min_length:
                flesch_score = safe_textstat_call(getattr(textstat, 'flesch_reading_ease', lambda x: 0), text)
                
                if flesch_score < conservative_min_score:
                    error = create_error(
                        error_type='readability',
                        message=f'Text appears difficult to read (Flesch score: {flesch_score:.1f}). Consider simplifying.',
                        suggestions=[
                            'Consider using shorter sentences',
                            'Consider using simpler words'
                        ],
                        severity=ErrorSeverity.LOW,  # Lower severity for conservative mode
                        confidence=FALLBACK_CONFIDENCE_SCORES[AnalysisMethod.CONSERVATIVE_FALLBACK],
                        analysis_method=AnalysisMethod.CONSERVATIVE_FALLBACK,
                        score=flesch_score
                    )
                    errors.append(error)
                    
        except Exception as e:
            logger.error(f"Conservative readability check failed: {e}")
            
        return errors
    
    def analyze_readability_minimal_safe(self, text: str) -> List[ErrorDict]:
        """Minimal safe readability check for when no advanced tools are available."""
        errors = []
        
        if not text.strip():
            return errors
            
        # Only flag readability if text is substantial and score is very low
        min_length = CONSERVATIVE_THRESHOLDS['minimal_safe_text_length']
        if len(text) > min_length:
            try:
                import textstat  # Lazy import after main.py configures NLTK
                flesch_score = safe_textstat_call(getattr(textstat, 'flesch_reading_ease', lambda x: 0), text)
                threshold = CONSERVATIVE_THRESHOLDS['minimal_safe_readability_threshold']
                
                if flesch_score < threshold:
                    error = create_error(
                        error_type='readability',
                        message=f'Text appears quite difficult to read (Flesch score: {flesch_score:.1f}).',
                        suggestions=['Consider reviewing for simpler language'],
                        severity=ErrorSeverity.LOW,
                        confidence=FALLBACK_CONFIDENCE_SCORES[AnalysisMethod.MINIMAL_SAFE],
                        analysis_method=AnalysisMethod.MINIMAL_SAFE,
                        score=flesch_score
                    )
                    errors.append(error)
                    
            except Exception as e:
                logger.error(f"Minimal readability check failed: {e}")
                
        return errors
    
    def calculate_readability_metrics(self, text: str) -> dict:
        """Calculate comprehensive readability metrics safely."""
        metrics = {
            'flesch_reading_ease': 0.0,
            'flesch_kincaid_grade': 0.0,
            'gunning_fog_index': 0.0,
            'smog_index': 0.0,
            'coleman_liau_index': 0.0,
            'automated_readability_index': 0.0,
            'dale_chall_readability': 0.0,
            'text_standard': 0.0
        }
        
        if not text.strip() or len(text) < 50:
            return metrics
            
        try:
            import textstat  # Lazy import after main.py configures NLTK
            # Use safe textstat calls for all metrics
            metrics['flesch_reading_ease'] = safe_textstat_call(
                getattr(textstat, 'flesch_reading_ease', lambda x: 0), text
            )
            metrics['flesch_kincaid_grade'] = safe_textstat_call(
                getattr(textstat, 'flesch_kincaid_grade', lambda x: 0), text
            )
            metrics['gunning_fog_index'] = safe_textstat_call(
                getattr(textstat, 'gunning_fog', lambda x: 0), text
            )
            metrics['smog_index'] = safe_textstat_call(
                getattr(textstat, 'smog_index', lambda x: 0), text
            )
            metrics['coleman_liau_index'] = safe_textstat_call(
                getattr(textstat, 'coleman_liau_index', lambda x: 0), text
            )
            metrics['automated_readability_index'] = safe_textstat_call(
                getattr(textstat, 'automated_readability_index', lambda x: 0), text
            )
            metrics['dale_chall_readability'] = safe_textstat_call(
                getattr(textstat, 'dale_chall_readability_score', lambda x: 0), text
            )
            
            # Handle text_standard separately as it may return non-numeric
            try:
                text_standard_result = getattr(textstat, 'text_standard', lambda x, float_output=True: 0)(text, float_output=True)
                if isinstance(text_standard_result, (int, float)):
                    metrics['text_standard'] = float(text_standard_result)
                else:
                    metrics['text_standard'] = 0.0
            except Exception:
                metrics['text_standard'] = 0.0
                
        except Exception as e:
            logger.error(f"Error calculating readability metrics: {e}")
            
        return metrics
    
    def get_readability_category(self, flesch_score: float) -> str:
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
    
    def get_grade_level_category(self, grade_level: float) -> str:
        """Get grade level category description."""
        if grade_level <= 8:
            return 'Elementary/Middle School'
        elif grade_level <= 12:
            return 'High School'
        elif grade_level <= 16:
            return 'College Level'
        else:
            return 'Graduate Level'
    
    def check_grade_level_target(self, grade_level: float) -> bool:
        """Check if grade level meets target range."""
        target_min, target_max = self.rules['target_grade_level']
        return target_min <= grade_level <= target_max
    
    def estimate_syllables(self, word: str) -> int:
        """Fallback syllable estimation when syllables library is not available."""
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
        if count == 0:
            count = 1
            
        return count
    
    def calculate_word_complexity_stats(self, text: str) -> dict:
        """Calculate word complexity statistics safely."""
        stats = {
            'total_words': 0,
            'complex_words': 0,
            'complex_words_percentage': 0.0,
            'avg_syllables_per_word': 0.0,
            'avg_word_length': 0.0
        }
        
        if not text.strip():
            return stats
            
        try:
            import re
            
            # Clean and split words
            words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
            if not words:
                return stats
                
            stats['total_words'] = len(words)
            
            total_syllables = 0
            total_length = 0
            complex_count = 0
            
            for word in words:
                # Calculate syllables
                syllables = self.estimate_syllables(word)
                total_syllables += syllables
                total_length += len(word)
                
                # Count complex words (3+ syllables)
                if syllables >= 3:
                    complex_count += 1
            
            stats['complex_words'] = complex_count
            stats['complex_words_percentage'] = (complex_count / len(words)) * 100
            stats['avg_syllables_per_word'] = total_syllables / len(words)
            stats['avg_word_length'] = total_length / len(words)
            
        except Exception as e:
            logger.error(f"Error calculating word complexity stats: {e}")
            
        return stats 
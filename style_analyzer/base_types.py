"""
Base Types and Constants for Style Analyzer
Defines common types, enums, and constants used across all analyzer modules.
"""

from typing import Dict, List, Any, Optional, Union
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class AnalysisMode(Enum):
    """Analysis modes for style analysis."""
    SPACY_WITH_MODULAR_RULES = "spacy_with_modular_rules"
    MODULAR_RULES_WITH_FALLBACKS = "modular_rules_with_fallbacks"
    MINIMAL_SAFE_MODE = "minimal_safe_mode"
    ERROR = "error"
    NONE = "none"

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class AnalysisMethod(Enum):
    """Analysis method types for tracking."""
    SPACY_ENHANCED = "spacy_enhanced"
    CONSERVATIVE_FALLBACK = "conservative_fallback"
    SPACY_LEGACY = "spacy_legacy"
    MINIMAL_SAFE = "minimal_safe"

# Type aliases for better code readability
ErrorDict = Dict[str, Any]
SuggestionDict = Dict[str, Any]
StatisticsDict = Dict[str, Any]
TechnicalMetricsDict = Dict[str, Any]
AnalysisResult = Dict[str, Any]

# Analysis configuration constants
DEFAULT_RULES = {
    'max_sentence_length': 25,
    'target_grade_level': (9, 11),  # 9th to 11th grade target
    'min_readability_score': 60.0,
    'max_fog_index': 12.0,  # Gunning Fog Index for technical writing
    'passive_voice_threshold': 0.15,  # Max 15% passive voice
    'word_repetition_threshold': 3,
    'max_syllables_per_word': 2.5,  # Average syllables per word
    'min_sentence_variety': 0.7,  # Sentence length variety
}

# Conservative thresholds for fallback modes
CONSERVATIVE_THRESHOLDS = {
    'sentence_length_threshold': 40,  # Much higher than normal 25
    'readability_min_text_length': 200,  # Require longer text
    'readability_score_buffer': 10,  # Lower threshold by 10 points
    'minimal_safe_text_length': 500,  # Substantial text required
    'minimal_safe_readability_threshold': 30,  # Very low threshold
}

# NOTE: Hardcoded confidence scores removed - now using enhanced ConfidenceCalculator
# Confidence scores are now calculated dynamically using the normalized confidence system
# from validation.confidence.confidence_calculator import ConfidenceCalculator

def create_error(
    error_type: str,
    message: str,
    suggestions: List[str],
    severity: Union[str, ErrorSeverity] = ErrorSeverity.LOW,
    sentence: Optional[str] = None,
    sentence_index: Optional[int] = None,
    confidence: Optional[float] = None,
    analysis_method: Optional[Union[str, AnalysisMethod]] = None,
    **extra_fields
) -> ErrorDict:
    """Create a standardized error dictionary."""
    
    # Convert enums to strings if needed
    if isinstance(severity, ErrorSeverity):
        severity = severity.value
    if isinstance(analysis_method, AnalysisMethod):
        analysis_method = analysis_method.value
    
    error = {
        'type': error_type,
        'message': message,
        'suggestions': suggestions,
        'severity': severity,
    }
    
    # Add optional fields only if provided
    if sentence is not None:
        error['sentence'] = sentence
    if sentence_index is not None:
        error['sentence_index'] = sentence_index
    if confidence is not None:
        error['confidence'] = confidence
    if analysis_method is not None:
        error['analysis_method'] = analysis_method
    
    # Add any extra fields
    error.update(extra_fields)
    
    return error

def create_suggestion(
    suggestion_type: str,
    message: str,
    priority: str = 'low'
) -> SuggestionDict:
    """Create a standardized suggestion dictionary."""
    return {
        'type': suggestion_type,
        'message': message,
        'priority': priority
    }

def create_analysis_result(
    errors: List[ErrorDict],
    suggestions: List[SuggestionDict],
    statistics: StatisticsDict,
    technical_metrics: TechnicalMetricsDict,
    overall_score: float,
    analysis_mode: Union[str, AnalysisMode],
    spacy_available: bool,
    modular_rules_available: bool
) -> AnalysisResult:
    """Create a standardized analysis result dictionary."""
    
    if isinstance(analysis_mode, AnalysisMode):
        analysis_mode = analysis_mode.value
    
    return {
        'errors': errors,
        'suggestions': suggestions,
        'statistics': statistics,
        'technical_writing_metrics': technical_metrics,
        'overall_score': overall_score,
        'analysis_mode': analysis_mode,
        'spacy_available': spacy_available,
        'modular_rules_available': modular_rules_available
    }

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, returning default if conversion fails."""
    try:
        if isinstance(value, (int, float)):
            return float(value)
        return default
    except (ValueError, TypeError):
        return default

def safe_textstat_call(func, text: str, default: float = 0.0) -> float:
    """Safely call a textstat function with error handling."""
    try:
        result = func(text)
        return safe_float_conversion(result, default)
    except Exception as e:
        logger.error(f"Textstat function call failed: {e}")
        return default 
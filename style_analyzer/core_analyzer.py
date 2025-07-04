"""
Core Analyzer Module
Main StyleAnalyzer class that coordinates all analysis with zero false positives.
Implements mutually exclusive analysis paths to prevent conflicts.
"""

import logging
from typing import Dict, List, Any, Optional

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

try:
    import rules
    RULES_AVAILABLE = True
    from rules import get_registry
except ImportError:
    RULES_AVAILABLE = False
    get_registry = None

from .base_types import (
    AnalysisResult, AnalysisMode, AnalysisMethod, ErrorDict,
    create_analysis_result, create_error
)
from .readability_analyzer import ReadabilityAnalyzer
from .sentence_analyzer import SentenceAnalyzer
from .statistics_calculator import StatisticsCalculator
from .suggestion_generator import SuggestionGenerator

logger = logging.getLogger(__name__)


class StyleAnalyzer:
    """Main style analyzer with zero false positives design."""
    
    def __init__(self, rules: Optional[dict] = None):
        """Initialize the style analyzer with components."""
        self.rules = rules or {}
        
        # Initialize components
        self.readability_analyzer = ReadabilityAnalyzer(rules)
        self.sentence_analyzer = SentenceAnalyzer(rules)
        self.statistics_calculator = StatisticsCalculator(rules)
        self.suggestion_generator = SuggestionGenerator(rules)
        
        # Initialize rules registry
        self.rules_registry = None
        if RULES_AVAILABLE and get_registry:
            try:
                self.rules_registry = get_registry()
                logger.info("Rules registry loaded successfully")
            except Exception as e:
                logger.warning(f"Failed to load rules registry: {e}")
                self.rules_registry = None
        
        # Initialize NLP model if available
        self.nlp = None
        if SPACY_AVAILABLE:
            self._initialize_spacy()
    
    def _initialize_spacy(self):
        """Initialize SpaCy model safely."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded successfully")
        except OSError:
            logger.warning("SpaCy model not found, using fallback methods")
            self.nlp = None
    
    def analyze(self, text: str) -> AnalysisResult:
        """Perform comprehensive style analysis with zero false positives."""
        if not text or not text.strip():
            return create_analysis_result(
                errors=[],
                suggestions=[],
                statistics={},
                technical_metrics={},
                overall_score=0,
                analysis_mode=AnalysisMode.NONE,
                spacy_available=SPACY_AVAILABLE,
                modular_rules_available=RULES_AVAILABLE
            )
        
        try:
            # Determine analysis mode based on available capabilities
            analysis_mode = self._determine_analysis_mode()
            
            # Prepare text for analysis
            sentences = self._split_sentences(text)
            paragraphs = self.statistics_calculator.split_paragraphs_safe(text)
            
            # COMPLETELY MUTUALLY EXCLUSIVE ANALYSIS PATHS
            errors = []
            
            if analysis_mode == AnalysisMode.SPACY_WITH_MODULAR_RULES:
                errors = self._analyze_spacy_with_modular_rules(text, sentences)
            
            elif analysis_mode == AnalysisMode.MODULAR_RULES_WITH_FALLBACKS:
                errors = self._analyze_modular_rules_with_fallbacks(text, sentences)
            
            elif analysis_mode == AnalysisMode.SPACY_LEGACY_ONLY:
                errors = self._analyze_spacy_legacy_only(text, sentences)
            
            elif analysis_mode == AnalysisMode.MINIMAL_SAFE_MODE:
                errors = self._analyze_minimal_safe_mode(text, sentences)
            
            else:
                # Error mode
                errors = [create_error(
                    error_type='system',
                    message='Analysis system could not determine safe analysis mode.',
                    suggestions=['Check system configuration and dependencies']
                )]
                analysis_mode = AnalysisMode.ERROR
            
            # Calculate statistics and metrics
            statistics = self.statistics_calculator.calculate_safe_statistics(
                text, sentences, paragraphs
            )
            
            technical_metrics = self.statistics_calculator.calculate_safe_technical_metrics(
                text, sentences, len(errors)
            )
            
            # Generate suggestions
            suggestions = self.suggestion_generator.generate_suggestions(
                errors, statistics, technical_metrics
            )
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(
                errors, technical_metrics, statistics
            )
            
            return create_analysis_result(
                errors=errors,
                suggestions=suggestions,
                statistics=statistics,
                technical_metrics=technical_metrics,
                overall_score=overall_score,
                analysis_mode=analysis_mode,
                spacy_available=SPACY_AVAILABLE,
                modular_rules_available=RULES_AVAILABLE
            )
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return create_analysis_result(
                errors=[create_error(
                    error_type='system',
                    message=f'Analysis failed: {str(e)}',
                    suggestions=['Check text input and system configuration']
                )],
                suggestions=[],
                statistics={},
                technical_metrics={},
                overall_score=0,
                analysis_mode=AnalysisMode.ERROR,
                spacy_available=SPACY_AVAILABLE,
                modular_rules_available=RULES_AVAILABLE
            )
    
    def _determine_analysis_mode(self) -> AnalysisMode:
        """Determine the safest analysis mode based on available capabilities."""
        if SPACY_AVAILABLE and RULES_AVAILABLE and self.nlp:
            return AnalysisMode.SPACY_WITH_MODULAR_RULES
        elif RULES_AVAILABLE:
            return AnalysisMode.MODULAR_RULES_WITH_FALLBACKS
        elif SPACY_AVAILABLE and self.nlp:
            return AnalysisMode.SPACY_LEGACY_ONLY
        else:
            return AnalysisMode.MINIMAL_SAFE_MODE
    
    def _analyze_spacy_with_modular_rules(self, text: str, sentences: List[str]) -> List[ErrorDict]:
        """Analyze using SpaCy enhanced with modular rules (highest accuracy)."""
        errors = []
        
        try:
            # SpaCy-enhanced readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_spacy_enhanced(
                text, self.nlp
            )
            errors.extend(readability_errors)
            
            # SpaCy-enhanced sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_spacy(
                sentences, self.nlp
            )
            errors.extend(sentence_errors)
            
            # Integrate modular rules analysis
            if self.rules_registry:
                try:
                    rules_errors = self.rules_registry.analyze_with_all_rules(text, sentences, self.nlp)
                    # Convert rules errors to our error format
                    for error in rules_errors:
                        converted_error = self._convert_rules_error(error)
                        errors.append(converted_error)
                    logger.info(f"Modular rules analysis found {len(rules_errors)} issues")
                except Exception as e:
                    logger.error(f"Modular rules analysis failed: {e}")
            
        except Exception as e:
            logger.error(f"SpaCy with modular rules analysis failed: {e}")
            # Fall back to next best mode
            return self._analyze_modular_rules_with_fallbacks(text, sentences)
        
        return errors
    
    def _analyze_modular_rules_with_fallbacks(self, text: str, sentences: List[str]) -> List[ErrorDict]:
        """Analyze using modular rules with conservative fallbacks."""
        errors = []
        
        try:
            # Conservative readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_conservative(text)
            errors.extend(readability_errors)
            
            # Conservative sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_conservative(sentences)
            errors.extend(sentence_errors)
            
            # Integrate modular rules analysis
            if self.rules_registry:
                try:
                    rules_errors = self.rules_registry.analyze_with_all_rules(text, sentences, self.nlp)
                    # Convert rules errors to our error format
                    for error in rules_errors:
                        converted_error = self._convert_rules_error(error)
                        errors.append(converted_error)
                    logger.info(f"Modular rules analysis found {len(rules_errors)} issues")
                except Exception as e:
                    logger.error(f"Modular rules analysis failed: {e}")
            
        except Exception as e:
            logger.error(f"Modular rules with fallbacks analysis failed: {e}")
            # Fall back to next best mode
            return self._analyze_spacy_legacy_only(text, sentences)
        
        return errors
    
    def _analyze_spacy_legacy_only(self, text: str, sentences: List[str]) -> List[ErrorDict]:
        """Analyze using only SpaCy (legacy mode)."""
        errors = []
        
        try:
            # SpaCy-only readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_spacy_enhanced(
                text, self.nlp
            )
            errors.extend(readability_errors)
            
            # SpaCy-only sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_spacy(
                sentences, self.nlp
            )
            errors.extend(sentence_errors)
            
        except Exception as e:
            logger.error(f"SpaCy legacy analysis failed: {e}")
            # Fall back to minimal safe mode
            return self._analyze_minimal_safe_mode(text, sentences)
        
        return errors
    
    def _analyze_minimal_safe_mode(self, text: str, sentences: List[str]) -> List[ErrorDict]:
        """Analyze using minimal safe methods (most conservative)."""
        errors = []
        
        try:
            # Minimal safe readability analysis
            readability_errors = self.readability_analyzer.analyze_readability_minimal_safe(text)
            errors.extend(readability_errors)
            
            # Minimal safe sentence analysis
            sentence_errors = self.sentence_analyzer.analyze_sentence_length_minimal_safe(sentences)
            errors.extend(sentence_errors)
            
        except Exception as e:
            logger.error(f"Minimal safe analysis failed: {e}")
            # This is the safest mode, so we just return empty errors
            return []
        
        return errors
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences safely."""
        try:
            if self.nlp:
                return self.sentence_analyzer.split_sentences_safe(text, self.nlp)
            else:
                return self.sentence_analyzer.split_sentences_safe(text)
        except Exception as e:
            logger.error(f"Error splitting sentences: {e}")
            # Ultimate fallback
            import re
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if s.strip()]
    
    def _calculate_overall_score(self, errors: List[ErrorDict], technical_metrics: Dict[str, Any], statistics: Dict[str, Any]) -> float:
        """Calculate overall style score safely."""
        try:
            # Base score
            base_score = 85.0
            
            # Deduct points for errors
            error_penalty = min(len(errors) * 5, 30)  # Max 30 points penalty
            
            # Adjust for readability
            readability_score = technical_metrics.get('readability_score', 60.0)
            if readability_score < 60:
                readability_penalty = (60 - readability_score) * 0.3
            else:
                readability_penalty = 0
            
            # Final score
            final_score = base_score - error_penalty - readability_penalty
            
            # Ensure score is between 0 and 100
            return max(0, min(100, final_score))
            
        except Exception as e:
            logger.error(f"Error calculating overall score: {e}")
            return 50.0  # Safe default
    
    def _convert_rules_error(self, rules_error: Dict[str, Any]) -> ErrorDict:
        """Convert rules system error to our standardized error format."""
        try:
            # Extract information from rules error
            error_type = rules_error.get('type', 'unknown')
            message = rules_error.get('message', 'Unknown error')
            suggestions = rules_error.get('suggestions', [])
            severity = rules_error.get('severity', 'low')
            sentence = rules_error.get('sentence', '')
            sentence_index = rules_error.get('sentence_index', -1)
            
            # Create standardized error
            return create_error(
                error_type=error_type,
                message=message,
                suggestions=suggestions,
                severity=severity,
                sentence=sentence,
                sentence_index=sentence_index,
                confidence=0.85,  # High confidence for rules-based detection
                analysis_method=AnalysisMethod.SPACY_ENHANCED
            )
        except Exception as e:
            logger.error(f"Error converting rules error: {e}")
            return create_error(
                error_type='system',
                message=f'Error processing rule: {str(e)}',
                suggestions=['Check rule implementation']
            ) 
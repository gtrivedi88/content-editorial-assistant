"""
Base Style Analyzer Module
Main StyleAnalyzer class that coordinates all analysis components.
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
    AnalysisResult, AnalysisMode, ErrorDict,
    create_analysis_result, create_error
)
from .readability_analyzer import ReadabilityAnalyzer
from .sentence_analyzer import SentenceAnalyzer
from .statistics_calculator import StatisticsCalculator
from .suggestion_generator import SuggestionGenerator
from .structural_analyzer import StructuralAnalyzer
from .analysis_modes import AnalysisModeExecutor

logger = logging.getLogger(__name__)


class StyleAnalyzer:
    """Main style analyzer with zero false positives design and structural parsing support."""
    
    def __init__(self, rules: Optional[dict] = None):
        """Initialize the style analyzer with components."""
        self.rules = rules or {}
        
        # Initialize core components
        self.readability_analyzer = ReadabilityAnalyzer(rules)
        self.sentence_analyzer = SentenceAnalyzer(rules)
        self.statistics_calculator = StatisticsCalculator(rules)
        self.suggestion_generator = SuggestionGenerator(rules)
        
        # Initialize rules registry with consolidation enabled
        self.rules_registry = None
        if RULES_AVAILABLE and get_registry:
            try:
                self.rules_registry = get_registry(enable_consolidation=True)
                logger.info("Rules registry loaded successfully with error consolidation enabled")
            except Exception as e:
                logger.warning(f"Failed to load rules registry: {e}")
                self.rules_registry = None
        
        # Initialize NLP model if available
        self.nlp = None
        if SPACY_AVAILABLE:
            self._initialize_spacy()
        
        # Initialize structural analyzer with production-appropriate confidence threshold
        self.structural_analyzer = StructuralAnalyzer(
            self.readability_analyzer,
            self.sentence_analyzer,
            self.statistics_calculator,
            self.suggestion_generator,
            self.rules_registry,
            self.nlp,
            enable_enhanced_validation=True,
            confidence_threshold=0.43  # Production threshold to catch real errors
        )
        
        # Initialize analysis mode executor
        self.mode_executor = AnalysisModeExecutor(
            self.readability_analyzer,
            self.sentence_analyzer,
            self.rules_registry,
            self.nlp
        )
    
    def _initialize_spacy(self):
        """Initialize SpaCy model safely."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("SpaCy model loaded successfully")
        except OSError:
            logger.warning("SpaCy model not found, using fallback methods")
            self.nlp = None
    
    def analyze(self, text: str, format_hint: str = 'auto') -> AnalysisResult:
        """Perform comprehensive style analysis with structural awareness."""
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
            
            # Use structural analyzer for comprehensive analysis
            result = self.structural_analyzer.analyze_with_blocks(
                text, format_hint, analysis_mode
            )
            
            # Extract errors from the analysis result
            errors = result.get('analysis', {}).get('errors', [])
            
            # Calculate statistics and metrics
            sentences = self._split_sentences(text)
            paragraphs = self.statistics_calculator.split_paragraphs_safe(text)
            
            statistics = self.statistics_calculator.calculate_comprehensive_statistics(
                text, sentences, paragraphs
            )
            
            technical_metrics = self.statistics_calculator.calculate_comprehensive_technical_metrics(
                text, sentences, errors
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
    
    def analyze_with_blocks(self, text: str, format_hint: str = 'auto', content_type: str = 'concept') -> Dict[str, Any]:
        """Perform block-aware analysis returning structured results with errors per block."""
        try:
            # Determine analysis mode
            analysis_mode = self._determine_analysis_mode()
            
            # Use structural analyzer for block-aware analysis
            analysis_result = self.structural_analyzer.analyze_with_blocks(
                text, format_hint, analysis_mode
            )
            
            # Add modular compliance analysis to the analysis section
            modular_compliance_result = self._analyze_modular_compliance(text, content_type)
            if modular_compliance_result:
                # Add to the analysis dictionary, not the top level
                if 'analysis' in analysis_result:
                    analysis_result['analysis']['modular_compliance'] = modular_compliance_result
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Block-aware analysis failed: {e}")
            return {
                'analysis': create_analysis_result(
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
                ),
                'structural_blocks': [],
                'has_structure': False
            }
    
    def _determine_analysis_mode(self) -> AnalysisMode:
        """Determine the analysis mode - simplified to eliminate complexity."""
        # Use the most capable mode available, with a simple fallback
        if SPACY_AVAILABLE and RULES_AVAILABLE and self.nlp:
            return AnalysisMode.SPACY_WITH_MODULAR_RULES
        elif RULES_AVAILABLE:
            return AnalysisMode.MODULAR_RULES_WITH_FALLBACKS
        else:
            return AnalysisMode.MINIMAL_SAFE_MODE
    
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
    
    def _calculate_overall_score(self, errors: List[ErrorDict], technical_metrics: Dict[str, Any], 
                               statistics: Dict[str, Any]) -> float:
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
    
    def _analyze_modular_compliance(self, text: str, content_type: str) -> Dict[str, Any]:
        """Analyze modular compliance with Phase 5 advanced features."""
        try:
            # Import Phase 5 advanced modular analyzer
            from rules.modular_compliance.advanced_modular_analyzer import AdvancedModularAnalyzer
            
            if content_type not in ['concept', 'procedure', 'reference']:
                logger.warning(f"Unknown content type for modular compliance: {content_type}")
                return None
            
            # Initialize advanced analyzer
            analyzer = AdvancedModularAnalyzer()
            
            # Create enhanced context
            context = {
                'content_type': content_type,
                'block_type': 'document',
                'nlp': self.nlp if hasattr(self, 'nlp') else None
            }
            
            # Use backward-compatible analysis that includes Phase 5 enhancements
            compliance_errors = analyzer.analyze_basic_with_advanced_hints(text, context)
            
            # Format results with Phase 5 enhancements
            result = {
                'content_type': content_type,
                'total_issues': len(compliance_errors),
                'issues_by_severity': self._categorize_compliance_issues(compliance_errors),
                'issues': compliance_errors,
                'compliance_status': self._determine_compliance_status(compliance_errors),
                # Phase 5 enhancements
                'advanced_features_enabled': True,
                'phase5_capabilities': {
                    'cross_reference_validation': True,
                    'template_compliance': True,
                    'inter_module_analysis': True
                }
            }
            
            logger.info(f"Advanced modular compliance analysis completed for {content_type}: {len(compliance_errors)} issues found")
            return result
            
        except ImportError as e:
            logger.warning(f"Advanced modular compliance analyzer not available, falling back to basic: {e}")
            # Fallback to basic analysis
            try:
                from rules.modular_compliance import ConceptModuleRule, ProcedureModuleRule, ReferenceModuleRule
                
                rule_map = {
                    'concept': ConceptModuleRule,
                    'procedure': ProcedureModuleRule, 
                    'reference': ReferenceModuleRule
                }
                
                rule_class = rule_map[content_type]
                rule = rule_class()
                
                context = {
                    'content_type': content_type,
                    'block_type': 'document'
                }
                
                compliance_errors = rule.analyze(text, context)
                
                return {
                    'content_type': content_type,
                    'total_issues': len(compliance_errors),
                    'issues_by_severity': self._categorize_compliance_issues(compliance_errors),
                    'issues': compliance_errors,
                    'compliance_status': self._determine_compliance_status(compliance_errors),
                    'advanced_features_enabled': False
                }
            except ImportError:
                return None
        except Exception as e:
            logger.error(f"Advanced modular compliance analysis failed: {e}")
            return None
    
    def _categorize_compliance_issues(self, errors: List[Dict[str, Any]]) -> Dict[str, int]:
        """Categorize compliance issues by severity."""
        categories = {'high': 0, 'medium': 0, 'low': 0}
        
        for error in errors:
            severity = error.get('severity', 'medium')
            if severity in categories:
                categories[severity] += 1
        
        return categories
    
    def _determine_compliance_status(self, errors: List[Dict[str, Any]]) -> str:
        """Determine overall compliance status."""
        if not errors:
            return 'compliant'
        
        high_severity_count = sum(1 for error in errors if error.get('severity') == 'high')
        
        if high_severity_count > 0:
            return 'non_compliant'
        elif len(errors) > 3:
            return 'needs_improvement'
        else:
            return 'mostly_compliant' 
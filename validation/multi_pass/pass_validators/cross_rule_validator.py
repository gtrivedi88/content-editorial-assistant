"""
CrossRuleValidator Class
Concrete implementation of BasePassValidator for cross-rule analysis and error coherence validation.
Specializes in rule conflict detection, error coherence validation, consolidation assessment,
and overall improvement analysis across multiple rules and errors.
"""

import time
import re
from typing import Dict, List, Tuple, Optional, Any, Set, Union
from dataclasses import dataclass
from collections import defaultdict, Counter
from enum import Enum

from ..base_validator import (
    BasePassValidator, ValidationDecision, ValidationConfidence,
    ValidationEvidence, ValidationResult, ValidationContext
)


class ConflictSeverity(Enum):
    """Severity levels for rule conflicts."""
    MINOR = "minor"            # Minor conflicts that can be resolved automatically
    MODERATE = "moderate"      # Moderate conflicts requiring attention
    SEVERE = "severe"          # Severe conflicts requiring manual resolution
    CRITICAL = "critical"      # Critical conflicts that prevent processing


class CoherenceLevel(Enum):
    """Coherence levels for error validation."""
    EXCELLENT = "excellent"    # Errors are highly coherent and consistent
    GOOD = "good"             # Errors are generally coherent with minor issues
    MODERATE = "moderate"     # Errors have moderate coherence issues
    POOR = "poor"             # Errors have significant coherence issues
    INCOHERENT = "incoherent"  # Errors are incoherent and contradictory


class ImprovementType(Enum):
    """Types of improvement assessment."""
    SIGNIFICANT = "significant"     # Significant overall improvement
    MODERATE = "moderate"          # Moderate improvement with some issues
    MINIMAL = "minimal"            # Minimal improvement achieved
    NO_IMPROVEMENT = "no_improvement"  # No meaningful improvement
    DEGRADATION = "degradation"    # Overall degradation in quality


@dataclass
class RuleConflictDetection:
    """Rule conflict detection results."""
    
    conflicting_rules: List[Tuple[str, str]]     # Pairs of conflicting rule names
    conflict_types: Dict[str, List[str]]         # Types of conflicts by category
    conflict_severity: ConflictSeverity         # Overall conflict severity
    affected_positions: List[int]               # Text positions affected by conflicts
    resolution_strategy: str                    # Recommended resolution strategy
    priority_conflicts: List[Dict[str, Any]]    # High-priority conflicts requiring attention
    rule_interactions: Dict[str, List[str]]     # Rule interaction mappings
    conflict_metadata: Dict[str, Any]           # Additional conflict metadata


@dataclass
class ErrorCoherenceValidation:
    """Error coherence validation results."""
    
    coherence_level: CoherenceLevel             # Overall coherence level
    coherence_score: float                      # Numerical coherence score (0-1)
    logical_consistency: float                  # Logical consistency across errors (0-1)
    temporal_consistency: float                 # Temporal consistency of errors (0-1)
    semantic_consistency: float                 # Semantic consistency of errors (0-1)
    contradiction_count: int                    # Number of contradictions detected
    inconsistency_areas: List[str]              # Areas with consistency issues
    coherence_factors: List[str]                # Factors affecting coherence
    improvement_suggestions: List[str]          # Suggestions for improving coherence


@dataclass
class ConsolidationValidation:
    """Consolidation result validation."""
    
    consolidation_quality: float                # Quality of consolidation (0-1)
    merge_appropriateness: float                # Appropriateness of error merges (0-1)
    priority_accuracy: float                    # Accuracy of priority assignments (0-1)
    completeness_score: float                   # Completeness of consolidation (0-1)
    redundancy_elimination: float               # Effectiveness of redundancy removal (0-1)
    consolidation_errors: List[str]             # Errors in consolidation process
    missed_opportunities: List[str]             # Missed consolidation opportunities
    over_consolidation: List[str]               # Cases of excessive consolidation
    consolidation_metadata: Dict[str, Any]      # Additional consolidation metadata


@dataclass
class ImprovementAssessment:
    """Overall improvement assessment results."""
    
    improvement_type: ImprovementType           # Type of improvement achieved
    improvement_score: float                    # Numerical improvement score (0-1)
    quality_metrics: Dict[str, float]           # Various quality metrics
    readability_improvement: float              # Readability improvement (0-1)
    clarity_improvement: float                  # Clarity improvement (0-1)
    consistency_improvement: float              # Consistency improvement (0-1)
    error_reduction_rate: float                 # Rate of error reduction (0-1)
    remaining_issues: List[str]                 # Issues still present after processing
    improvement_areas: List[str]                # Areas that showed improvement
    regression_areas: List[str]                 # Areas that showed regression
    improvement_confidence: float               # Confidence in improvement assessment (0-1)


class CrossRuleValidator(BasePassValidator):
    """
    Cross-rule validator for multi-pass validation.
    
    This validator focuses on:
    - Rule conflict detection and resolution
    - Error coherence validation across multiple rules
    - Consolidation result validation
    - Overall improvement assessment
    
    It analyzes interactions between different rules and validates
    the coherence and effectiveness of the overall validation process.
    """
    
    def __init__(self,
                 enable_conflict_detection: bool = True,
                 enable_coherence_validation: bool = True,
                 enable_consolidation_validation: bool = True,
                 enable_improvement_assessment: bool = True,
                 cache_analysis_results: bool = True,
                 min_confidence_threshold: float = 0.65,
                 max_conflicts_to_analyze: int = 50):
        """
        Initialize the cross-rule validator.
        
        Args:
            enable_conflict_detection: Whether to detect rule conflicts
            enable_coherence_validation: Whether to validate error coherence
            enable_consolidation_validation: Whether to validate consolidation results
            enable_improvement_assessment: Whether to assess overall improvement
            cache_analysis_results: Whether to cache analysis results
            min_confidence_threshold: Minimum confidence for decisive decisions
            max_conflicts_to_analyze: Maximum number of conflicts to analyze
        """
        super().__init__(
            validator_name="cross_rule_validator",
            min_confidence_threshold=min_confidence_threshold
        )
        
        # Configuration
        self.enable_conflict_detection = enable_conflict_detection
        self.enable_coherence_validation = enable_coherence_validation
        self.enable_consolidation_validation = enable_consolidation_validation
        self.enable_improvement_assessment = enable_improvement_assessment
        self.cache_analysis_results = cache_analysis_results
        self.max_conflicts_to_analyze = max_conflicts_to_analyze
        
        # Analysis cache
        self._analysis_cache: Dict[str, Any] = {}
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Initialize rule conflict patterns and relationships
        self._initialize_rule_relationships()
        self._initialize_conflict_patterns()
        self._initialize_coherence_patterns()
        self._initialize_quality_metrics()
        
        # Performance tracking
        self._analysis_times = {
            'conflict_detection': [],
            'coherence_validation': [],
            'consolidation_validation': [],
            'improvement_assessment': []
        }
    
    def _initialize_rule_relationships(self):
        """Initialize rule relationship mappings and conflict patterns."""
        
        # Rule categories and their typical conflicts
        self.rule_categories = {
            'grammar': ['subject_verb_agreement', 'tense_consistency', 'pronoun_agreement', 'modifier_placement'],
            'style': ['sentence_length', 'tone_consistency', 'formality_level', 'voice_preference'],
            'punctuation': ['comma_usage', 'apostrophe_usage', 'quotation_marks', 'semicolon_usage'],
            'terminology': ['word_choice', 'technical_precision', 'domain_appropriateness', 'consistency'],
            'structure': ['paragraph_organization', 'heading_structure', 'list_formatting', 'document_flow'],
            'clarity': ['ambiguity_removal', 'conciseness', 'redundancy_elimination', 'logical_flow']
        }
        
        # Known rule conflicts (rules that often conflict with each other)
        self.known_conflicts = {
            'conciseness_vs_clarity': {
                'rules': ['sentence_shortening', 'detail_addition'],
                'severity': ConflictSeverity.MODERATE,
                'resolution': 'prioritize_clarity'
            },
            'formality_vs_accessibility': {
                'rules': ['formal_language', 'simple_language'],
                'severity': ConflictSeverity.MODERATE,
                'resolution': 'context_dependent'
            },
            'consistency_vs_variety': {
                'rules': ['terminology_consistency', 'vocabulary_variety'],
                'severity': ConflictSeverity.MINOR,
                'resolution': 'balance_both'
            },
            'brevity_vs_completeness': {
                'rules': ['content_reduction', 'information_completeness'],
                'severity': ConflictSeverity.SEVERE,
                'resolution': 'prioritize_completeness'
            },
            'passive_vs_active_voice': {
                'rules': ['active_voice_preference', 'passive_voice_appropriateness'],
                'severity': ConflictSeverity.MODERATE,
                'resolution': 'context_and_domain_dependent'
            }
        }
        
        # Rule priority mappings (higher priority rules win conflicts)
        self.rule_priorities = {
            'grammar': 100,        # Grammar rules have highest priority
            'legal_compliance': 95, # Legal rules very high priority
            'accuracy': 90,        # Accuracy rules high priority
            'clarity': 80,         # Clarity rules high priority
            'consistency': 70,     # Consistency rules moderate priority
            'style': 60,           # Style rules moderate priority
            'tone': 50,            # Tone rules moderate priority
            'formatting': 40,      # Formatting rules lower priority
            'preference': 30       # Preference rules lowest priority
        }
    
    def _initialize_conflict_patterns(self):
        """Initialize patterns for detecting rule conflicts."""
        
        # Conflict detection patterns
        self.conflict_patterns = {
            'contradictory_suggestions': {
                'pattern': r'(?:remove|delete|eliminate).*(?:add|insert|include)',
                'weight': 0.9,
                'description': 'Contradictory add/remove suggestions'
            },
            'opposing_modifications': {
                'pattern': r'(?:shorten|reduce|minimize).*(?:expand|elaborate|detail)',
                'weight': 0.8,
                'description': 'Opposing length modifications'
            },
            'formality_conflicts': {
                'pattern': r'(?:formal|professional).*(?:casual|informal|conversational)',
                'weight': 0.7,
                'description': 'Formality level conflicts'
            },
            'voice_conflicts': {
                'pattern': r'(?:active voice).*(?:passive voice)',
                'weight': 0.6,
                'description': 'Voice preference conflicts'
            },
            'complexity_conflicts': {
                'pattern': r'(?:simplify|clarify).*(?:technical|complex|sophisticated)',
                'weight': 0.5,
                'description': 'Complexity level conflicts'
            }
        }
        
        # Conflict resolution strategies
        self.resolution_strategies = {
            ConflictSeverity.MINOR: [
                'apply_both_when_possible',
                'prefer_higher_priority_rule',
                'context_sensitive_resolution'
            ],
            ConflictSeverity.MODERATE: [
                'analyze_context_and_domain',
                'prefer_grammar_over_style',
                'consider_user_preferences',
                'escalate_to_human_review'
            ],
            ConflictSeverity.SEVERE: [
                'escalate_to_human_review',
                'apply_safety_first_principle',
                'prefer_accuracy_over_style',
                'document_conflict_for_review'
            ],
            ConflictSeverity.CRITICAL: [
                'halt_processing',
                'require_manual_intervention',
                'preserve_original_text',
                'log_critical_conflict'
            ]
        }
    
    def _initialize_coherence_patterns(self):
        """Initialize patterns for validating error coherence."""
        
        # Coherence validation criteria
        self.coherence_criteria = {
            'logical_consistency': {
                'weight': 0.3,
                'checks': [
                    'no_contradictory_rules',
                    'consistent_error_types',
                    'logical_error_progression'
                ]
            },
            'temporal_consistency': {
                'weight': 0.2,
                'checks': [
                    'chronological_error_order',
                    'consistent_tense_corrections',
                    'time_reference_consistency'
                ]
            },
            'semantic_consistency': {
                'weight': 0.3,
                'checks': [
                    'consistent_terminology',
                    'coherent_meaning_changes',
                    'semantic_field_consistency'
                ]
            },
            'structural_consistency': {
                'weight': 0.2,
                'checks': [
                    'consistent_formatting',
                    'parallel_structure_maintenance',
                    'document_organization_coherence'
                ]
            }
        }
        
        # Incoherence indicators
        self.incoherence_indicators = {
            'contradiction': {
                'patterns': [
                    r'(?:add|include).*(?:remove|delete)',
                    r'(?:formal).*(?:informal)',
                    r'(?:technical).*(?:simple)'
                ],
                'severity': 0.8
            },
            'logical_inconsistency': {
                'patterns': [
                    r'(?:first|initially).*(?:finally|lastly).*(?:first|initially)',
                    r'(?:before).*(?:after).*(?:before)'
                ],
                'severity': 0.7
            },
            'semantic_drift': {
                'patterns': [
                    r'(?:meaning|sense).*(?:different|opposite|contrary)',
                    r'(?:context).*(?:inappropriate|wrong|incorrect)'
                ],
                'severity': 0.6
            }
        }
    
    def _initialize_quality_metrics(self):
        """Initialize quality metrics for improvement assessment."""
        
        # Quality assessment metrics
        self.quality_metrics = {
            'readability': {
                'factors': ['sentence_length', 'word_complexity', 'structure_clarity'],
                'weight': 0.25,
                'optimal_range': (0.6, 0.9)
            },
            'clarity': {
                'factors': ['ambiguity_reduction', 'precision_improvement', 'coherence'],
                'weight': 0.3,
                'optimal_range': (0.7, 1.0)
            },
            'consistency': {
                'factors': ['terminology_consistency', 'style_consistency', 'format_consistency'],
                'weight': 0.2,
                'optimal_range': (0.8, 1.0)
            },
            'correctness': {
                'factors': ['grammar_accuracy', 'spelling_accuracy', 'punctuation_accuracy'],
                'weight': 0.25,
                'optimal_range': (0.9, 1.0)
            }
        }
        
        # Improvement thresholds
        self.improvement_thresholds = {
            ImprovementType.SIGNIFICANT: 0.8,
            ImprovementType.MODERATE: 0.6,
            ImprovementType.MINIMAL: 0.4,
            ImprovementType.NO_IMPROVEMENT: 0.2,
            ImprovementType.DEGRADATION: 0.0
        }
        
        # Error severity mappings
        self.error_severity_weights = {
            'critical': 1.0,
            'major': 0.8,
            'moderate': 0.6,
            'minor': 0.4,
            'suggestion': 0.2
        }
    
    def _validate_error(self, context: ValidationContext) -> ValidationResult:
        """
        Validate an error using cross-rule analysis.
        
        Args:
            context: Validation context containing error and metadata
            
        Returns:
            ValidationResult with cross-rule analysis and decision
        """
        start_time = time.time()
        
        try:
            # Extract multiple rules and errors from context metadata if available
            all_rules = self._extract_all_rules(context)
            all_errors = self._extract_all_errors(context)
            
            if not all_rules and not all_errors:
                return self._create_uncertain_result(
                    context,
                    "No multiple rules or errors found for cross-rule analysis",
                    time.time() - start_time
                )
            
            # Perform cross-rule analyses
            evidence = []
            
            # 1. Rule conflict detection
            if self.enable_conflict_detection and len(all_rules) > 1:
                conflict_detection = self._detect_rule_conflicts(all_rules, context)
                if conflict_detection:
                    evidence.append(self._create_conflict_evidence(conflict_detection, context))
            
            # 2. Error coherence validation
            if self.enable_coherence_validation and len(all_errors) > 1:
                coherence_validation = self._validate_error_coherence(all_errors, context)
                if coherence_validation:
                    evidence.append(self._create_coherence_evidence(coherence_validation, context))
            
            # 3. Consolidation validation (only if multiple errors)
            if self.enable_consolidation_validation and len(all_errors) > 1:
                consolidation_validation = self._validate_consolidation(all_errors, context)
                if consolidation_validation:
                    evidence.append(self._create_consolidation_evidence(consolidation_validation, context))
            
            # 4. Overall improvement assessment (only if multiple rules or errors)
            if self.enable_improvement_assessment and (len(all_rules) > 1 or len(all_errors) > 1):
                improvement_assessment = self._assess_overall_improvement(all_rules, all_errors, context)
                if improvement_assessment:
                    evidence.append(self._create_improvement_evidence(improvement_assessment, context))
            
            # Make validation decision based on cross-rule evidence
            decision, confidence_score, reasoning = self._make_cross_rule_decision(evidence, context)
            
            return ValidationResult(
                validator_name=self.validator_name,
                decision=decision,
                confidence=self._convert_confidence_to_level(confidence_score),
                confidence_score=confidence_score,
                evidence=evidence,
                reasoning=reasoning,
                error_text=context.error_text,
                error_position=context.error_position,
                rule_type=context.rule_type,
                rule_name=context.rule_name,
                validation_time=time.time() - start_time,
                metadata={
                    'total_rules_analyzed': len(all_rules),
                    'total_errors_analyzed': len(all_errors),
                    'cross_rule_evidence_count': len(evidence),
                    'conflict_detection_enabled': self.enable_conflict_detection,
                    'coherence_validation_enabled': self.enable_coherence_validation,
                    'consolidation_validation_enabled': self.enable_consolidation_validation,
                    'improvement_assessment_enabled': self.enable_improvement_assessment
                }
            )
            
        except Exception as e:
            return self._create_error_result(context, str(e), time.time() - start_time)
    
    def _extract_all_rules(self, context: ValidationContext) -> List[str]:
        """Extract all rules from context for cross-rule analysis."""
        rules = []
        
        # Add the current rule
        if context.rule_name:
            rules.append(context.rule_name)
        
        # Extract additional rules from additional_context if available
        if hasattr(context, 'additional_context') and context.additional_context:
            additional_rules = context.additional_context.get('all_rules', [])
            if isinstance(additional_rules, list):
                rules.extend(additional_rules)
            
            # Also check for rules in different formats
            rule_list = context.additional_context.get('applied_rules', [])
            if isinstance(rule_list, list):
                rules.extend(rule_list)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_rules = []
        for rule in rules:
            if rule not in seen:
                seen.add(rule)
                unique_rules.append(rule)
        
        return unique_rules
    
    def _extract_all_errors(self, context: ValidationContext) -> List[Dict[str, Any]]:
        """Extract all errors from context for coherence analysis."""
        errors = []
        
        # Create current error from context
        current_error = {
            'text': context.error_text,
            'position': context.error_position,
            'rule_type': context.rule_type,
            'rule_name': context.rule_name,
            'severity': getattr(context, 'severity', 'moderate')
        }
        errors.append(current_error)
        
        # Extract additional errors from additional_context if available
        if hasattr(context, 'additional_context') and context.additional_context:
            additional_errors = context.additional_context.get('all_errors', [])
            if isinstance(additional_errors, list):
                errors.extend(additional_errors)
            
            # Also check for errors in validation history
            error_history = context.additional_context.get('error_history', [])
            if isinstance(error_history, list):
                errors.extend(error_history)
        
        return errors
    
    def _detect_rule_conflicts(self, rules: List[str], context: ValidationContext) -> Optional[RuleConflictDetection]:
        """Detect conflicts between multiple rules."""
        start_time = time.time()
        
        try:
            # Analyze rule pairs for conflicts
            conflicting_pairs = []
            conflict_types = defaultdict(list)
            affected_positions = []
            priority_conflicts = []
            rule_interactions = defaultdict(list)
            
            # Check all pairs of rules for conflicts
            for i, rule1 in enumerate(rules):
                for rule2 in rules[i+1:]:
                    conflict_analysis = self._analyze_rule_pair_conflict(rule1, rule2, context)
                    
                    if conflict_analysis['has_conflict']:
                        conflicting_pairs.append((rule1, rule2))
                        conflict_type = conflict_analysis['conflict_type']
                        conflict_types[conflict_type].append((rule1, rule2))
                        
                        # Track affected positions
                        if conflict_analysis.get('affected_positions'):
                            affected_positions.extend(conflict_analysis['affected_positions'])
                        
                        # Check if it's a priority conflict
                        if conflict_analysis['severity'] in [ConflictSeverity.SEVERE, ConflictSeverity.CRITICAL]:
                            priority_conflicts.append({
                                'rules': (rule1, rule2),
                                'severity': conflict_analysis['severity'],
                                'description': conflict_analysis['description'],
                                'resolution': conflict_analysis['resolution']
                            })
                        
                        # Track rule interactions
                        rule_interactions[rule1].append(rule2)
                        rule_interactions[rule2].append(rule1)
            
            # Determine overall conflict severity
            if not conflicting_pairs:
                overall_severity = ConflictSeverity.MINOR
            elif any(pc['severity'] == ConflictSeverity.CRITICAL for pc in priority_conflicts):
                overall_severity = ConflictSeverity.CRITICAL
            elif any(pc['severity'] == ConflictSeverity.SEVERE for pc in priority_conflicts):
                overall_severity = ConflictSeverity.SEVERE
            elif len(conflicting_pairs) > 3:
                overall_severity = ConflictSeverity.MODERATE
            else:
                overall_severity = ConflictSeverity.MINOR
            
            # Determine resolution strategy
            resolution_strategy = self._determine_resolution_strategy(overall_severity, conflicting_pairs)
            
            detection = RuleConflictDetection(
                conflicting_rules=conflicting_pairs,
                conflict_types=dict(conflict_types),
                conflict_severity=overall_severity,
                affected_positions=list(set(affected_positions)),
                resolution_strategy=resolution_strategy,
                priority_conflicts=priority_conflicts,
                rule_interactions=dict(rule_interactions),
                conflict_metadata={
                    'total_rules': len(rules),
                    'total_conflicts': len(conflicting_pairs),
                    'analysis_time': time.time() - start_time
                }
            )
            
            self._analysis_times['conflict_detection'].append(time.time() - start_time)
            return detection
            
        except Exception:
            return None
    
    def _analyze_rule_pair_conflict(self, rule1: str, rule2: str, context: ValidationContext) -> Dict[str, Any]:
        """Analyze a pair of rules for potential conflicts."""
        
        # Check known conflicts first
        for conflict_name, conflict_info in self.known_conflicts.items():
            if rule1 in conflict_info['rules'] and rule2 in conflict_info['rules']:
                return {
                    'has_conflict': True,
                    'conflict_type': conflict_name,
                    'severity': conflict_info['severity'],
                    'description': f"Known conflict: {conflict_name}",
                    'resolution': conflict_info['resolution'],
                    'affected_positions': [context.error_position]
                }
        
        # Check for pattern-based conflicts
        rule1_lower = rule1.lower()
        rule2_lower = rule2.lower()
        
        # Check for contradictory patterns
        for pattern_name, pattern_info in self.conflict_patterns.items():
            combined_rules = f"{rule1_lower} {rule2_lower}"
            if re.search(pattern_info['pattern'], combined_rules):
                severity = ConflictSeverity.MODERATE if pattern_info['weight'] > 0.7 else ConflictSeverity.MINOR
                return {
                    'has_conflict': True,
                    'conflict_type': pattern_name,
                    'severity': severity,
                    'description': pattern_info['description'],
                    'resolution': 'analyze_context',
                    'affected_positions': [context.error_position]
                }
        
        # Check for category conflicts (same category rules often conflict)
        rule1_category = self._get_rule_category(rule1)
        rule2_category = self._get_rule_category(rule2)
        
        if rule1_category == rule2_category and rule1_category in ['style', 'tone']:
            return {
                'has_conflict': True,
                'conflict_type': 'category_conflict',
                'severity': ConflictSeverity.MINOR,
                'description': f"Same category conflict: {rule1_category}",
                'resolution': 'prefer_more_specific',
                'affected_positions': [context.error_position]
            }
        
        # No conflict detected
        return {
            'has_conflict': False,
            'conflict_type': 'none',
            'severity': ConflictSeverity.MINOR,
            'description': 'No conflict detected',
            'resolution': 'apply_both'
        }
    
    def _get_rule_category(self, rule: str) -> str:
        """Get the category of a rule."""
        rule_lower = rule.lower()
        
        for category, rules in self.rule_categories.items():
            if any(category_rule in rule_lower for category_rule in rules):
                return category
            
            # Also check if rule name contains category
            if category in rule_lower:
                return category
        
        return 'general'
    
    def _determine_resolution_strategy(self, severity: ConflictSeverity, conflicts: List[Tuple[str, str]]) -> str:
        """Determine the best resolution strategy for conflicts."""
        strategies = self.resolution_strategies.get(severity, ['manual_review'])
        
        # Select primary strategy based on conflict characteristics
        if len(conflicts) > 5:
            return 'escalate_to_human_review'
        elif severity == ConflictSeverity.CRITICAL:
            return 'halt_processing'
        elif any('grammar' in str(conflict).lower() for conflict in conflicts):
            return 'prefer_grammar_over_style'
        else:
            return strategies[0] if strategies else 'manual_review'
    
    def _validate_error_coherence(self, errors: List[Dict[str, Any]], context: ValidationContext) -> Optional[ErrorCoherenceValidation]:
        """Validate coherence across multiple errors."""
        start_time = time.time()
        
        try:
            # Calculate coherence metrics
            logical_consistency = self._assess_logical_consistency(errors)
            temporal_consistency = self._assess_temporal_consistency(errors)
            semantic_consistency = self._assess_semantic_consistency(errors)
            
            # Calculate overall coherence score
            weights = self.coherence_criteria
            coherence_score = (
                logical_consistency * weights['logical_consistency']['weight'] +
                temporal_consistency * weights['temporal_consistency']['weight'] +
                semantic_consistency * weights['semantic_consistency']['weight'] +
                0.8 * weights['structural_consistency']['weight']  # Default structural score
            )
            
            # Determine coherence level
            if coherence_score >= 0.9:
                coherence_level = CoherenceLevel.EXCELLENT
            elif coherence_score >= 0.75:
                coherence_level = CoherenceLevel.GOOD
            elif coherence_score >= 0.6:
                coherence_level = CoherenceLevel.MODERATE
            elif coherence_score >= 0.4:
                coherence_level = CoherenceLevel.POOR
            else:
                coherence_level = CoherenceLevel.INCOHERENT
            
            # Detect contradictions and inconsistencies
            contradictions = self._detect_contradictions(errors)
            inconsistency_areas = self._identify_inconsistency_areas(errors)
            coherence_factors = self._analyze_coherence_factors(errors)
            improvement_suggestions = self._generate_coherence_improvements(errors)
            
            validation = ErrorCoherenceValidation(
                coherence_level=coherence_level,
                coherence_score=coherence_score,
                logical_consistency=logical_consistency,
                temporal_consistency=temporal_consistency,
                semantic_consistency=semantic_consistency,
                contradiction_count=len(contradictions),
                inconsistency_areas=inconsistency_areas,
                coherence_factors=coherence_factors,
                improvement_suggestions=improvement_suggestions
            )
            
            self._analysis_times['coherence_validation'].append(time.time() - start_time)
            return validation
            
        except Exception:
            return None
    
    def _assess_logical_consistency(self, errors: List[Dict[str, Any]]) -> float:
        """Assess logical consistency across errors."""
        if len(errors) < 2:
            return 1.0
        
        consistency_score = 1.0
        
        # Check for logical contradictions
        rule_types = [error.get('rule_type', '') for error in errors]
        rule_names = [error.get('rule_name', '') for error in errors]
        
        # Penalize contradictory rule types
        if 'add_content' in rule_names and 'remove_content' in rule_names:
            consistency_score -= 0.3
        
        if 'formal_style' in rule_names and 'informal_style' in rule_names:
            consistency_score -= 0.2
        
        # Check for logical progression
        positions = [error.get('position', 0) for error in errors if error.get('position')]
        if positions:
            # Errors should generally progress through the text
            sorted_positions = sorted(positions)
            if sorted_positions != positions:
                consistency_score -= 0.1
        
        return max(0.0, consistency_score)
    
    def _assess_temporal_consistency(self, errors: List[Dict[str, Any]]) -> float:
        """Assess temporal consistency of errors."""
        if len(errors) < 2:
            return 1.0
        
        consistency_score = 1.0
        
        # Check for temporal consistency in tense corrections
        tense_corrections = []
        for error in errors:
            rule_name = error.get('rule_name', '').lower()
            if 'tense' in rule_name:
                tense_corrections.append(rule_name)
        
        # If multiple tense corrections, they should be consistent
        if len(tense_corrections) > 1:
            unique_tenses = set(tense_corrections)
            if len(unique_tenses) > 2:  # Too many different tense corrections
                consistency_score -= 0.2
        
        return max(0.0, consistency_score)
    
    def _assess_semantic_consistency(self, errors: List[Dict[str, Any]]) -> float:
        """Assess semantic consistency across errors."""
        if len(errors) < 2:
            return 1.0
        
        consistency_score = 1.0
        
        # Check for consistent terminology changes
        terminology_changes = []
        for error in errors:
            rule_type = error.get('rule_type', '').lower()
            if 'terminology' in rule_type or 'word_choice' in rule_type:
                terminology_changes.append(error)
        
        # Semantic coherence checks would be more sophisticated in real implementation
        # For now, we use simple heuristics
        
        return max(0.0, consistency_score)
    
    def _detect_contradictions(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Detect contradictions between errors."""
        contradictions = []
        
        for i, error1 in enumerate(errors):
            for error2 in errors[i+1:]:
                rule1 = error1.get('rule_name', '').lower()
                rule2 = error2.get('rule_name', '').lower()
                
                # Check for contradictory patterns
                for indicator_name, indicator_info in self.incoherence_indicators.items():
                    combined_rules = f"{rule1} {rule2}"
                    for pattern in indicator_info['patterns']:
                        if re.search(pattern, combined_rules):
                            contradictions.append(f"Contradiction: {rule1} vs {rule2}")
        
        return contradictions
    
    def _identify_inconsistency_areas(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Identify areas with consistency issues."""
        areas = []
        
        # Group errors by type
        error_types = defaultdict(list)
        for error in errors:
            rule_type = error.get('rule_type', 'unknown')
            error_types[rule_type].append(error)
        
        # Check for inconsistencies within types
        for error_type, type_errors in error_types.items():
            if len(type_errors) > 2:
                rule_names = [e.get('rule_name', '') for e in type_errors]
                if len(set(rule_names)) > len(rule_names) * 0.7:  # Too many different rules
                    areas.append(f"Inconsistent {error_type} handling")
        
        return areas
    
    def _analyze_coherence_factors(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Analyze factors affecting coherence."""
        factors = []
        
        if len(errors) > 10:
            factors.append("High error count may affect coherence")
        
        # Check error distribution
        positions = [e.get('position', 0) for e in errors if e.get('position')]
        if positions:
            position_range = max(positions) - min(positions)
            if position_range < 100:  # Errors clustered in small area
                factors.append("Errors clustered in small text area")
        
        # Check rule type diversity
        rule_types = [e.get('rule_type', '') for e in errors]
        if len(set(rule_types)) > len(rule_types) * 0.8:
            factors.append("High diversity of rule types")
        
        return factors
    
    def _generate_coherence_improvements(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Generate suggestions for improving coherence."""
        suggestions = []
        
        if len(errors) > 15:
            suggestions.append("Consider reducing the number of simultaneous corrections")
        
        # Check for rule conflicts
        rule_names = [e.get('rule_name', '') for e in errors]
        if 'formal' in str(rule_names) and 'informal' in str(rule_names):
            suggestions.append("Resolve formality conflicts before applying corrections")
        
        if len(set(rule_names)) < len(rule_names) * 0.5:
            suggestions.append("Group similar corrections for better coherence")
        
        return suggestions
    
    def _validate_consolidation(self, errors: List[Dict[str, Any]], context: ValidationContext) -> Optional[ConsolidationValidation]:
        """Validate the results of error consolidation."""
        start_time = time.time()
        
        try:
            # Assess different aspects of consolidation
            consolidation_quality = self._assess_consolidation_quality(errors)
            merge_appropriateness = self._assess_merge_appropriateness(errors)
            priority_accuracy = self._assess_priority_accuracy(errors)
            completeness_score = self._assess_completeness(errors)
            redundancy_elimination = self._assess_redundancy_elimination(errors)
            
            # Identify consolidation issues
            consolidation_errors = self._identify_consolidation_errors(errors)
            missed_opportunities = self._identify_missed_opportunities(errors)
            over_consolidation = self._identify_over_consolidation(errors)
            
            validation = ConsolidationValidation(
                consolidation_quality=consolidation_quality,
                merge_appropriateness=merge_appropriateness,
                priority_accuracy=priority_accuracy,
                completeness_score=completeness_score,
                redundancy_elimination=redundancy_elimination,
                consolidation_errors=consolidation_errors,
                missed_opportunities=missed_opportunities,
                over_consolidation=over_consolidation,
                consolidation_metadata={
                    'total_errors': len(errors),
                    'analysis_time': time.time() - start_time
                }
            )
            
            self._analysis_times['consolidation_validation'].append(time.time() - start_time)
            return validation
            
        except Exception:
            return None
    
    def _assess_consolidation_quality(self, errors: List[Dict[str, Any]]) -> float:
        """Assess overall quality of consolidation."""
        if not errors:
            return 0.0
        
        quality_score = 0.8  # Base score
        
        # Check for appropriate grouping
        rule_groups = defaultdict(list)
        for error in errors:
            rule_type = error.get('rule_type', 'unknown')
            rule_groups[rule_type].append(error)
        
        # Good consolidation should have reasonable group sizes
        for rule_type, group_errors in rule_groups.items():
            if len(group_errors) == 1:
                continue  # Single errors are fine
            elif 2 <= len(group_errors) <= 5:
                quality_score += 0.1  # Good grouping
            elif len(group_errors) > 10:
                quality_score -= 0.2  # Possibly over-consolidated
        
        return max(0.0, min(1.0, quality_score))
    
    def _assess_merge_appropriateness(self, errors: List[Dict[str, Any]]) -> float:
        """Assess appropriateness of error merging."""
        if len(errors) < 2:
            return 1.0
        
        appropriateness = 0.7  # Base score
        
        # Check for appropriate merges (similar errors should be merged)
        positions = [e.get('position', 0) for e in errors if e.get('position')]
        if positions:
            # Errors close together should potentially be merged
            sorted_positions = sorted(positions)
            close_pairs = 0
            total_pairs = 0
            
            for i in range(len(sorted_positions) - 1):
                total_pairs += 1
                if sorted_positions[i+1] - sorted_positions[i] < 20:  # Within 20 characters
                    close_pairs += 1
            
            if total_pairs > 0:
                close_ratio = close_pairs / total_pairs
                appropriateness += close_ratio * 0.2
        
        return max(0.0, min(1.0, appropriateness))
    
    def _assess_priority_accuracy(self, errors: List[Dict[str, Any]]) -> float:
        """Assess accuracy of priority assignments."""
        if not errors:
            return 1.0
        
        accuracy = 0.8  # Base score
        
        # Check if higher severity errors have appropriate priority
        severity_order = ['critical', 'major', 'moderate', 'minor', 'suggestion']
        error_severities = [e.get('severity', 'moderate') for e in errors]
        
        # Count priority inversions (low severity before high severity)
        inversions = 0
        for i in range(len(error_severities) - 1):
            current_priority = severity_order.index(error_severities[i]) if error_severities[i] in severity_order else 2
            next_priority = severity_order.index(error_severities[i+1]) if error_severities[i+1] in severity_order else 2
            
            if current_priority > next_priority:  # Lower priority before higher priority
                inversions += 1
        
        if len(errors) > 1:
            inversion_rate = inversions / (len(errors) - 1)
            accuracy -= inversion_rate * 0.3
        
        return max(0.0, accuracy)
    
    def _assess_completeness(self, errors: List[Dict[str, Any]]) -> float:
        """Assess completeness of consolidation."""
        if not errors:
            return 0.0
        
        # Simple completeness assessment based on error coverage
        rule_types = set(e.get('rule_type', '') for e in errors)
        
        # More rule types covered suggests more complete analysis
        expected_types = ['grammar', 'style', 'punctuation', 'terminology']
        covered_types = len(rule_types.intersection(expected_types))
        
        completeness = covered_types / len(expected_types)
        return completeness
    
    def _assess_redundancy_elimination(self, errors: List[Dict[str, Any]]) -> float:
        """Assess effectiveness of redundancy elimination."""
        if len(errors) < 2:
            return 1.0
        
        # Check for potential redundant errors
        rule_names = [e.get('rule_name', '') for e in errors]
        unique_rules = set(rule_names)
        
        if len(rule_names) == 0:
            return 1.0
        
        redundancy_elimination = len(unique_rules) / len(rule_names)
        return redundancy_elimination
    
    def _identify_consolidation_errors(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Identify errors in the consolidation process."""
        consolidation_errors = []
        
        # Check for missing required information
        for error in errors:
            if not error.get('rule_type'):
                consolidation_errors.append("Error missing rule type")
            if not error.get('rule_name'):
                consolidation_errors.append("Error missing rule name")
        
        return consolidation_errors
    
    def _identify_missed_opportunities(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Identify missed consolidation opportunities."""
        opportunities = []
        
        # Check for errors that could be merged
        positions = [e.get('position', 0) for e in errors if e.get('position')]
        rule_types = [e.get('rule_type', '') for e in errors]
        
        # Look for similar errors close together
        for i, error1 in enumerate(errors):
            for j, error2 in enumerate(errors[i+1:], i+1):
                if (error1.get('rule_type') == error2.get('rule_type') and
                    abs(error1.get('position', 0) - error2.get('position', 0)) < 50):
                    opportunities.append(f"Could merge similar {error1.get('rule_type')} errors")
        
        return list(set(opportunities))  # Remove duplicates
    
    def _identify_over_consolidation(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Identify cases of over-consolidation."""
        over_consolidation = []
        
        # Check for groups that might be too large
        rule_groups = defaultdict(list)
        for error in errors:
            rule_type = error.get('rule_type', 'unknown')
            rule_groups[rule_type].append(error)
        
        for rule_type, group_errors in rule_groups.items():
            if len(group_errors) > 8:  # Arbitrary threshold
                over_consolidation.append(f"Possible over-consolidation of {rule_type} errors")
        
        return over_consolidation
    
    def _assess_overall_improvement(self, rules: List[str], errors: List[Dict[str, Any]], context: ValidationContext) -> Optional[ImprovementAssessment]:
        """Assess overall improvement achieved by the validation process."""
        start_time = time.time()
        
        try:
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(errors, context)
            
            # Assess different improvement dimensions
            readability_improvement = self._assess_readability_improvement(errors, context)
            clarity_improvement = self._assess_clarity_improvement(errors, context)
            consistency_improvement = self._assess_consistency_improvement(errors, context)
            error_reduction_rate = self._calculate_error_reduction_rate(errors)
            
            # Calculate overall improvement score
            improvement_score = (
                readability_improvement * 0.25 +
                clarity_improvement * 0.3 +
                consistency_improvement * 0.2 +
                error_reduction_rate * 0.25
            )
            
            # Determine improvement type
            improvement_type = self._classify_improvement_type(improvement_score)
            
            # Identify remaining issues and improvements
            remaining_issues = self._identify_remaining_issues(errors)
            improvement_areas = self._identify_improvement_areas(errors)
            regression_areas = self._identify_regression_areas(errors)
            
            # Calculate improvement confidence
            improvement_confidence = self._calculate_improvement_confidence(errors, improvement_score)
            
            assessment = ImprovementAssessment(
                improvement_type=improvement_type,
                improvement_score=improvement_score,
                quality_metrics=quality_metrics,
                readability_improvement=readability_improvement,
                clarity_improvement=clarity_improvement,
                consistency_improvement=consistency_improvement,
                error_reduction_rate=error_reduction_rate,
                remaining_issues=remaining_issues,
                improvement_areas=improvement_areas,
                regression_areas=regression_areas,
                improvement_confidence=improvement_confidence
            )
            
            self._analysis_times['improvement_assessment'].append(time.time() - start_time)
            return assessment
            
        except Exception:
            return None
    
    def _calculate_quality_metrics(self, errors: List[Dict[str, Any]], context: ValidationContext) -> Dict[str, float]:
        """Calculate various quality metrics."""
        metrics = {}
        
        # Readability metric (based on sentence length and complexity)
        text_length = len(context.text) if context.text else 1000  # Default length
        avg_error_density = len(errors) / (text_length / 100)  # Errors per 100 chars
        metrics['readability'] = max(0.0, 1.0 - min(avg_error_density / 10, 1.0))
        
        # Clarity metric (based on clarity-related errors)
        clarity_errors = [e for e in errors if 'clarity' in e.get('rule_type', '').lower() or 'ambiguity' in e.get('rule_name', '').lower()]
        clarity_error_rate = len(clarity_errors) / max(1, len(errors))
        metrics['clarity'] = max(0.0, 1.0 - clarity_error_rate)
        
        # Consistency metric (based on consistency-related errors)
        consistency_errors = [e for e in errors if 'consistency' in e.get('rule_type', '').lower() or 'consistent' in e.get('rule_name', '').lower()]
        consistency_error_rate = len(consistency_errors) / max(1, len(errors))
        metrics['consistency'] = max(0.0, 1.0 - consistency_error_rate)
        
        # Correctness metric (based on grammar and spelling errors)
        correctness_errors = [e for e in errors if e.get('rule_type', '').lower() in ['grammar', 'spelling', 'punctuation']]
        correctness_error_rate = len(correctness_errors) / max(1, len(errors))
        metrics['correctness'] = max(0.0, 1.0 - correctness_error_rate)
        
        return metrics
    
    def _assess_readability_improvement(self, errors: List[Dict[str, Any]], context: ValidationContext) -> float:
        """Assess readability improvement."""
        # Simple heuristic based on types of errors addressed
        readability_rules = ['sentence_length', 'word_complexity', 'structure_clarity']
        readability_errors = [e for e in errors if any(rule in e.get('rule_name', '').lower() for rule in readability_rules)]
        
        if not errors:
            return 0.5  # Neutral when no errors
        
        readability_improvement = len(readability_errors) / len(errors)
        return min(1.0, readability_improvement * 2)  # Scale up the effect
    
    def _assess_clarity_improvement(self, errors: List[Dict[str, Any]], context: ValidationContext) -> float:
        """Assess clarity improvement."""
        clarity_rules = ['ambiguity', 'precision', 'coherence', 'clarity']
        clarity_errors = [e for e in errors if any(rule in e.get('rule_name', '').lower() for rule in clarity_rules)]
        
        if not errors:
            return 0.5  # Neutral when no errors
        
        clarity_improvement = len(clarity_errors) / len(errors)
        return min(1.0, clarity_improvement * 2.5)  # Higher weight for clarity
    
    def _assess_consistency_improvement(self, errors: List[Dict[str, Any]], context: ValidationContext) -> float:
        """Assess consistency improvement."""
        consistency_rules = ['consistency', 'uniformity', 'standardization']
        consistency_errors = [e for e in errors if any(rule in e.get('rule_name', '').lower() for rule in consistency_rules)]
        
        if not errors:
            return 0.5  # Neutral when no errors
        
        consistency_improvement = len(consistency_errors) / len(errors)
        return min(1.0, consistency_improvement * 2)
    
    def _calculate_error_reduction_rate(self, errors: List[Dict[str, Any]]) -> float:
        """Calculate the rate of error reduction."""
        # This would typically compare before/after error counts
        # For now, we estimate based on error severity distribution
        
        if not errors:
            return 1.0  # Perfect reduction if no errors remain
        
        # Weight errors by severity
        total_weight = 0
        for error in errors:
            severity = error.get('severity', 'moderate')
            weight = self.error_severity_weights.get(severity, 0.6)
            total_weight += weight
        
        # Normalize by number of errors (lower is better)
        avg_weight = total_weight / len(errors)
        reduction_rate = 1.0 - avg_weight  # Invert so higher is better
        
        return max(0.0, reduction_rate)
    
    def _classify_improvement_type(self, improvement_score: float) -> ImprovementType:
        """Classify the type of improvement based on score."""
        for improvement_type, threshold in sorted(self.improvement_thresholds.items(), 
                                                 key=lambda x: x[1], reverse=True):
            if improvement_score >= threshold:
                return improvement_type
        return ImprovementType.DEGRADATION
    
    def _identify_remaining_issues(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Identify issues that remain after processing."""
        issues = []
        
        # Group errors by severity
        severe_errors = [e for e in errors if e.get('severity') in ['critical', 'major']]
        if severe_errors:
            issues.append(f"{len(severe_errors)} severe errors remain")
        
        # Check for persistent error types
        error_types = Counter(e.get('rule_type', 'unknown') for e in errors)
        for error_type, count in error_types.most_common(3):
            if count > 2:
                issues.append(f"Multiple {error_type} errors persist")
        
        return issues
    
    def _identify_improvement_areas(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Identify areas that showed improvement."""
        areas = []
        
        # This would typically compare before/after states
        # For now, we infer from the types of errors being addressed
        
        rule_types = set(e.get('rule_type', '') for e in errors)
        for rule_type in rule_types:
            if rule_type in ['grammar', 'spelling']:
                areas.append(f"Grammar and spelling improvements")
            elif rule_type in ['style', 'tone']:
                areas.append(f"Style and tone refinements")
            elif rule_type in ['clarity', 'readability']:
                areas.append(f"Clarity and readability enhancements")
        
        return list(set(areas))  # Remove duplicates
    
    def _identify_regression_areas(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Identify areas that showed regression."""
        # This would require before/after comparison
        # For now, we return an empty list as we don't have comparison data
        return []
    
    def _calculate_improvement_confidence(self, errors: List[Dict[str, Any]], improvement_score: float) -> float:
        """Calculate confidence in the improvement assessment."""
        base_confidence = 0.7
        
        # Higher confidence with more errors analyzed
        if len(errors) > 10:
            base_confidence += 0.1
        elif len(errors) > 5:
            base_confidence += 0.05
        
        # Higher confidence with clearer improvement signal
        if improvement_score > 0.8 or improvement_score < 0.2:
            base_confidence += 0.1  # Clear signal
        
        return min(1.0, base_confidence)
    
    # Evidence creation methods
    def _create_conflict_evidence(self, detection: RuleConflictDetection, 
                                context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from rule conflict detection."""
        
        # Calculate confidence based on conflict severity and number of conflicts
        if detection.conflict_severity == ConflictSeverity.CRITICAL:
            confidence = 0.95
        elif detection.conflict_severity == ConflictSeverity.SEVERE:
            confidence = 0.85
        elif detection.conflict_severity == ConflictSeverity.MODERATE:
            confidence = 0.7
        else:
            confidence = 0.5
        
        # Adjust confidence based on number of conflicts
        num_conflicts = len(detection.conflicting_rules)
        if num_conflicts > 5:
            confidence = min(0.95, confidence + 0.1)
        
        description = f"Rule conflict analysis: {num_conflicts} conflicts detected "
        description += f"(severity: {detection.conflict_severity.value})"
        
        if detection.priority_conflicts:
            description += f" [{len(detection.priority_conflicts)} priority conflicts]"
        
        return ValidationEvidence(
            evidence_type="rule_conflict_detection",
            confidence=confidence,
            description=description,
            source_data={
                'conflicting_rules': detection.conflicting_rules,
                'conflict_types': detection.conflict_types,
                'conflict_severity': detection.conflict_severity.value,
                'affected_positions': detection.affected_positions,
                'resolution_strategy': detection.resolution_strategy,
                'priority_conflicts': detection.priority_conflicts,
                'rule_interactions': detection.rule_interactions,
                'conflict_metadata': detection.conflict_metadata
            }
        )
    
    def _create_coherence_evidence(self, validation: ErrorCoherenceValidation, 
                                 context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from error coherence validation."""
        
        confidence = validation.coherence_score
        
        description = f"Error coherence validation: {validation.coherence_level.value} "
        description += f"(score: {validation.coherence_score:.2f})"
        
        if validation.contradiction_count > 0:
            description += f" [{validation.contradiction_count} contradictions]"
        
        return ValidationEvidence(
            evidence_type="error_coherence_validation",
            confidence=confidence,
            description=description,
            source_data={
                'coherence_level': validation.coherence_level.value,
                'coherence_score': validation.coherence_score,
                'logical_consistency': validation.logical_consistency,
                'temporal_consistency': validation.temporal_consistency,
                'semantic_consistency': validation.semantic_consistency,
                'contradiction_count': validation.contradiction_count,
                'inconsistency_areas': validation.inconsistency_areas,
                'coherence_factors': validation.coherence_factors,
                'improvement_suggestions': validation.improvement_suggestions
            }
        )
    
    def _create_consolidation_evidence(self, validation: ConsolidationValidation,
                                     context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from consolidation validation."""
        
        confidence = validation.consolidation_quality
        
        description = f"Consolidation validation: {validation.consolidation_quality:.2f} quality"
        
        if validation.consolidation_errors:
            description += f" [{len(validation.consolidation_errors)} errors]"
        
        if validation.missed_opportunities:
            description += f" [{len(validation.missed_opportunities)} missed opportunities]"
        
        return ValidationEvidence(
            evidence_type="consolidation_validation",
            confidence=confidence,
            description=description,
            source_data={
                'consolidation_quality': validation.consolidation_quality,
                'merge_appropriateness': validation.merge_appropriateness,
                'priority_accuracy': validation.priority_accuracy,
                'completeness_score': validation.completeness_score,
                'redundancy_elimination': validation.redundancy_elimination,
                'consolidation_errors': validation.consolidation_errors,
                'missed_opportunities': validation.missed_opportunities,
                'over_consolidation': validation.over_consolidation,
                'consolidation_metadata': validation.consolidation_metadata
            }
        )
    
    def _create_improvement_evidence(self, assessment: ImprovementAssessment,
                                   context: ValidationContext) -> ValidationEvidence:
        """Create validation evidence from improvement assessment."""
        
        confidence = assessment.improvement_confidence
        
        description = f"Improvement assessment: {assessment.improvement_type.value} "
        description += f"(score: {assessment.improvement_score:.2f})"
        
        if assessment.remaining_issues:
            description += f" [{len(assessment.remaining_issues)} remaining issues]"
        
        return ValidationEvidence(
            evidence_type="improvement_assessment",
            confidence=confidence,
            description=description,
            source_data={
                'improvement_type': assessment.improvement_type.value,
                'improvement_score': assessment.improvement_score,
                'quality_metrics': assessment.quality_metrics,
                'readability_improvement': assessment.readability_improvement,
                'clarity_improvement': assessment.clarity_improvement,
                'consistency_improvement': assessment.consistency_improvement,
                'error_reduction_rate': assessment.error_reduction_rate,
                'remaining_issues': assessment.remaining_issues,
                'improvement_areas': assessment.improvement_areas,
                'regression_areas': assessment.regression_areas,
                'improvement_confidence': assessment.improvement_confidence
            }
        )
    
    def _make_cross_rule_decision(self, evidence: List[ValidationEvidence], 
                                context: ValidationContext) -> Tuple[ValidationDecision, float, str]:
        """Make validation decision based on cross-rule evidence."""
        
        if not evidence:
            return ValidationDecision.UNCERTAIN, 0.3, "No cross-rule evidence available for validation"
        
        # Calculate weighted average confidence
        total_weight = sum(e.confidence * e.weight for e in evidence)
        total_weights = sum(e.weight for e in evidence)
        avg_confidence = total_weight / total_weights if total_weights > 0 else 0.3
        
        # Analyze evidence types
        evidence_types = [e.evidence_type for e in evidence]
        
        # Decision logic based on cross-rule analysis
        if "rule_conflict_detection" in evidence_types:
            conflict_evidence = next(e for e in evidence if e.evidence_type == "rule_conflict_detection")
            conflict_severity = conflict_evidence.source_data.get('conflict_severity', 'minor')
            
            if conflict_severity == 'critical':
                decision = ValidationDecision.REJECT
                reasoning = f"Critical rule conflicts detected ({avg_confidence:.2f}) - manual intervention required"
            elif conflict_severity == 'severe':
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Severe rule conflicts detected ({avg_confidence:.2f}) - requires careful review"
            elif avg_confidence >= 0.8:
                decision = ValidationDecision.ACCEPT
                reasoning = f"Manageable rule conflicts detected ({avg_confidence:.2f}) - can be resolved automatically"
            else:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Moderate rule conflicts detected ({avg_confidence:.2f}) - requires attention"
        
        elif "error_coherence_validation" in evidence_types:
            coherence_evidence = next(e for e in evidence if e.evidence_type == "error_coherence_validation")
            coherence_level = coherence_evidence.source_data.get('coherence_level', 'moderate')
            
            if coherence_level in ['excellent', 'good']:
                decision = ValidationDecision.ACCEPT
                reasoning = f"Excellent error coherence ({avg_confidence:.2f}) - validation successful"
            elif coherence_level == 'moderate':
                decision = ValidationDecision.UNCERTAIN if avg_confidence < 0.7 else ValidationDecision.ACCEPT
                reasoning = f"Moderate error coherence ({avg_confidence:.2f}) - acceptable with minor issues"
            else:
                decision = ValidationDecision.REJECT if avg_confidence < 0.4 else ValidationDecision.UNCERTAIN
                reasoning = f"Poor error coherence ({avg_confidence:.2f}) - significant issues detected"
        
        elif "improvement_assessment" in evidence_types:
            improvement_evidence = next(e for e in evidence if e.evidence_type == "improvement_assessment")
            improvement_type = improvement_evidence.source_data.get('improvement_type', 'minimal')
            
            if improvement_type in ['significant', 'moderate']:
                decision = ValidationDecision.ACCEPT
                reasoning = f"Good improvement achieved ({avg_confidence:.2f}) - validation successful"
            elif improvement_type == 'minimal':
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Minimal improvement achieved ({avg_confidence:.2f}) - may need additional work"
            else:
                decision = ValidationDecision.REJECT
                reasoning = f"Poor or no improvement ({avg_confidence:.2f}) - validation unsuccessful"
        
        else:
            # General decision based on average confidence
            if avg_confidence >= 0.8:
                decision = ValidationDecision.ACCEPT
                reasoning = f"Strong cross-rule evidence ({avg_confidence:.2f}) supports validation"
            elif avg_confidence >= 0.6:
                decision = ValidationDecision.UNCERTAIN
                reasoning = f"Moderate cross-rule evidence ({avg_confidence:.2f}) - mixed signals"
            else:
                decision = ValidationDecision.REJECT
                reasoning = f"Weak cross-rule evidence ({avg_confidence:.2f}) - validation concerns"
        
        return decision, avg_confidence, reasoning
    
    def _create_uncertain_result(self, context: ValidationContext, reason: str, validation_time: float) -> ValidationResult:
        """Create an uncertain validation result."""
        return ValidationResult(
            validator_name=self.validator_name,
            decision=ValidationDecision.UNCERTAIN,
            confidence=ValidationConfidence.LOW,
            confidence_score=0.3,
            evidence=[ValidationEvidence(
                evidence_type="error",
                confidence=0.0,
                description=reason,
                source_data={"error_type": "analysis_failure"}
            )],
            reasoning=f"Cross-rule validation uncertain: {reason}",
            error_text=context.error_text,
            error_position=context.error_position,
            rule_type=context.rule_type,
            rule_name=context.rule_name,
            validation_time=validation_time,
            metadata={"validation_failure": True}
        )
    
    def _create_error_result(self, context: ValidationContext, error_msg: str, validation_time: float) -> ValidationResult:
        """Create an error validation result."""
        return ValidationResult(
            validator_name=self.validator_name,
            decision=ValidationDecision.UNCERTAIN,
            confidence=ValidationConfidence.LOW,
            confidence_score=0.0,
            evidence=[ValidationEvidence(
                evidence_type="error",
                confidence=0.0,
                description=f"Validation error: {error_msg}",
                source_data={"error_message": error_msg}
            )],
            reasoning=f"Cross-rule validation failed due to error: {error_msg}",
            error_text=context.error_text,
            error_position=context.error_position,
            rule_type=context.rule_type,
            rule_name=context.rule_name,
            validation_time=validation_time,
            metadata={"validation_error": True}
        )
    
    def get_validator_info(self) -> Dict[str, Any]:
        """Get comprehensive information about this validator."""
        return {
            "name": self.validator_name,
            "type": "cross_rule_validator",
            "version": "1.0.0",
            "description": "Validates errors using cross-rule analysis and meta-validation",
            "capabilities": [
                "rule_conflict_detection",
                "error_coherence_validation", 
                "consolidation_validation",
                "improvement_assessment",
                "meta_analysis"
            ],
            "specialties": [
                "cross_rule_analysis",
                "conflict_resolution",
                "error_coherence",
                "consolidation_assessment",
                "improvement_tracking",
                "meta_validation"
            ],
            "configuration": {
                "conflict_detection_enabled": self.enable_conflict_detection,
                "coherence_validation_enabled": self.enable_coherence_validation,
                "consolidation_validation_enabled": self.enable_consolidation_validation,
                "improvement_assessment_enabled": self.enable_improvement_assessment,
                "analysis_caching_enabled": self.cache_analysis_results,
                "min_confidence_threshold": self.min_confidence_threshold,
                "max_conflicts_to_analyze": self.max_conflicts_to_analyze
            },
            "performance_characteristics": {
                "best_for_rule_types": ["meta", "consolidation", "conflict_resolution"],
                "moderate_for_rule_types": ["style", "consistency"],
                "limited_for_rule_types": ["grammar", "spelling"],
                "avg_processing_time_ms": self._get_average_processing_time(),
                "cache_hit_rate": self._get_cache_hit_rate()
            },
            "analysis_knowledge": {
                "known_conflicts": len(self.known_conflicts),
                "conflict_patterns": len(self.conflict_patterns),
                "coherence_criteria": len(self.coherence_criteria),
                "quality_metrics": len(self.quality_metrics),
                "rule_categories": len(self.rule_categories),
                "resolution_strategies": sum(len(strategies) for strategies in self.resolution_strategies.values())
            }
        }
    
    def _get_average_processing_time(self) -> float:
        """Get average processing time across all analysis types."""
        all_times = []
        for analysis_type, times in self._analysis_times.items():
            all_times.extend(times)
        
        return (sum(all_times) / len(all_times) * 1000) if all_times else 0.0
    
    def _get_cache_hit_rate(self) -> float:
        """Get analysis cache hit rate."""
        total = self._cache_hits + self._cache_misses
        return self._cache_hits / total if total > 0 else 0.0
    
    def clear_caches(self) -> None:
        """Clear all caches."""
        self._analysis_cache.clear()
        self._cache_hits = 0
        self._cache_misses = 0
        
        # Clear performance tracking
        for analysis_type in self._analysis_times:
            self._analysis_times[analysis_type].clear()
    
    def get_analysis_statistics(self) -> Dict[str, Any]:
        """Get detailed analysis statistics."""
        return {
            "analysis_cache": {
                "cached_analyses": len(self._analysis_cache),
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "hit_rate": self._get_cache_hit_rate()
            },
            "analysis_performance": {
                analysis_type: {
                    "total_analyses": len(times),
                    "average_time_ms": (sum(times) / len(times) * 1000) if times else 0.0,
                    "min_time_ms": (min(times) * 1000) if times else 0.0,
                    "max_time_ms": (max(times) * 1000) if times else 0.0
                }
                for analysis_type, times in self._analysis_times.items()
            },
            "configuration_status": {
                "conflict_detection": self.enable_conflict_detection,
                "coherence_validation": self.enable_coherence_validation,
                "consolidation_validation": self.enable_consolidation_validation,
                "improvement_assessment": self.enable_improvement_assessment,
                "analysis_caching": self.cache_analysis_results
            },
            "knowledge_base_stats": {
                "known_conflicts": len(self.known_conflicts),
                "conflict_patterns": len(self.conflict_patterns),
                "coherence_criteria": len(self.coherence_criteria),
                "incoherence_indicators": len(self.incoherence_indicators),
                "quality_metrics": len(self.quality_metrics),
                "rule_categories": len(self.rule_categories)
            }
        }
"""
ValidationPipeline Class
Orchestrates multiple pass validators into a unified validation system with consensus-based decision making.
Provides early termination, decision aggregation, audit trail generation, and performance monitoring.
"""

import time
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, Counter

from .base_validator import (
    BasePassValidator, ValidationDecision, ValidationConfidence,
    ValidationEvidence, ValidationResult, ValidationContext
)
from .pass_validators import (
    MorphologicalValidator, ContextValidator, DomainValidator, CrossRuleValidator
)

# Import monitoring capabilities
try:
    from ..monitoring.metrics import record_pipeline_execution, record_validation_duration, get_metrics
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False


class PipelineStage(Enum):
    """Pipeline execution stages."""
    INITIALIZATION = "initialization"
    MORPHOLOGICAL_VALIDATION = "morphological_validation"
    CONTEXTUAL_VALIDATION = "contextual_validation"
    DOMAIN_VALIDATION = "domain_validation"
    CROSS_RULE_VALIDATION = "cross_rule_validation"
    CONSENSUS_BUILDING = "consensus_building"
    AUDIT_TRAIL_GENERATION = "audit_trail_generation"
    FINALIZATION = "finalization"


class ConsensusStrategy(Enum):
    """Strategies for building consensus from validator results."""
    MAJORITY_VOTE = "majority_vote"              # Simple majority wins
    WEIGHTED_AVERAGE = "weighted_average"        # Weight by confidence scores
    CONFIDENCE_THRESHOLD = "confidence_threshold" # Require minimum confidence
    UNANIMOUS_AGREEMENT = "unanimous_agreement"   # All validators must agree
    BEST_CONFIDENCE = "best_confidence"          # Choose highest confidence result
    STAGED_FALLBACK = "staged_fallback"          # Try strategies in order


class TerminationCondition(Enum):
    """Conditions for early pipeline termination."""
    HIGH_CONFIDENCE_CONSENSUS = "high_confidence_consensus"
    UNANIMOUS_DECISION = "unanimous_decision"
    CRITICAL_FAILURE = "critical_failure"
    TIMEOUT = "timeout"
    VALIDATOR_QUORUM = "validator_quorum"


@dataclass
class ValidatorWeight:
    """Weight configuration for individual validators."""
    
    morphological: float = 0.25
    contextual: float = 0.25
    domain: float = 0.25
    cross_rule: float = 0.25
    
    def __post_init__(self):
        """Validate that weights sum to 1.0."""
        total = self.morphological + self.contextual + self.domain + self.cross_rule
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Validator weights must sum to 1.0, got {total}")


@dataclass
class PipelineConfiguration:
    """Configuration for the validation pipeline."""
    
    # Validator settings
    validator_weights: ValidatorWeight = field(default_factory=ValidatorWeight)
    enable_morphological: bool = True
    enable_contextual: bool = True
    enable_domain: bool = True
    enable_cross_rule: bool = True
    
    # Consensus settings
    consensus_strategy: ConsensusStrategy = ConsensusStrategy.WEIGHTED_AVERAGE
    fallback_strategies: List[ConsensusStrategy] = field(default_factory=lambda: [
        ConsensusStrategy.CONFIDENCE_THRESHOLD,
        ConsensusStrategy.MAJORITY_VOTE,
        ConsensusStrategy.BEST_CONFIDENCE
    ])
    minimum_consensus_confidence: float = 0.6
    
    # Early termination settings
    enable_early_termination: bool = True
    termination_conditions: List[TerminationCondition] = field(default_factory=lambda: [
        TerminationCondition.HIGH_CONFIDENCE_CONSENSUS,
        TerminationCondition.UNANIMOUS_DECISION
    ])
    high_confidence_threshold: float = 0.9
    consensus_threshold: float = 0.8
    timeout_seconds: float = 30.0
    
    # Performance settings
    enable_performance_monitoring: bool = True
    enable_audit_trail: bool = True
    enable_parallel_validation: bool = False  # Future enhancement
    
    # Error handling
    continue_on_validator_error: bool = True
    minimum_validator_count: int = 2


@dataclass
class ValidatorExecution:
    """Results of individual validator execution."""
    
    validator_name: str
    result: Optional[ValidationResult]
    execution_time: float
    error: Optional[Exception]
    stage: PipelineStage
    terminated_early: bool = False


@dataclass
class ConsensusAnalysis:
    """Analysis of consensus building process."""
    
    strategy_used: ConsensusStrategy
    strategies_attempted: List[ConsensusStrategy]
    final_decision: ValidationDecision
    final_confidence: float
    agreement_score: float
    validator_agreements: Dict[str, bool]
    confidence_spread: float
    outlier_validators: List[str]
    consensus_metadata: Dict[str, Any]


@dataclass
class PipelineAuditTrail:
    """Comprehensive audit trail of pipeline execution."""
    
    pipeline_id: str
    execution_start_time: float
    execution_end_time: float
    total_execution_time: float
    
    # Configuration
    configuration: PipelineConfiguration
    
    # Context and input
    validation_context: ValidationContext
    
    # Execution stages
    stages_executed: List[PipelineStage]
    validator_executions: List[ValidatorExecution]
    
    # Consensus building
    consensus_analysis: ConsensusAnalysis
    
    # Final results
    final_result: ValidationResult
    
    # Performance metrics
    performance_metrics: Dict[str, Any]
    
    # Error information
    errors_encountered: List[str]
    warnings_generated: List[str]
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineResult:
    """Complete result of pipeline execution."""
    
    # Final validation result
    validation_result: ValidationResult
    
    # Pipeline-specific information
    pipeline_confidence: float
    consensus_achieved: bool
    early_termination: bool
    termination_reason: Optional[TerminationCondition]
    
    # Individual validator results
    validator_results: Dict[str, ValidationResult]
    
    # Consensus information
    consensus_analysis: ConsensusAnalysis
    
    # Audit trail
    audit_trail: PipelineAuditTrail
    
    # Performance metrics
    total_execution_time: float
    individual_execution_times: Dict[str, float]
    
    # Evidence aggregation
    aggregated_evidence: List[ValidationEvidence]
    evidence_by_validator: Dict[str, List[ValidationEvidence]]


class ValidationPipeline:
    """
    Multi-pass validation pipeline that orchestrates multiple validators.
    
    This pipeline coordinates the execution of multiple pass validators,
    implements consensus-based decision making, provides early termination
    logic, and generates comprehensive audit trails.
    """
    
    def __init__(self, configuration: Optional[PipelineConfiguration] = None):
        """
        Initialize the validation pipeline.
        
        Args:
            configuration: Pipeline configuration settings
        """
        self.configuration = configuration or PipelineConfiguration()
        
        # Initialize validators based on configuration
        self.validators: Dict[str, BasePassValidator] = {}
        self._initialize_validators()
        
        # Pipeline state
        self.pipeline_id = self._generate_pipeline_id()
        self.execution_history: List[PipelineAuditTrail] = []
        
        # Performance tracking
        self.performance_metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'early_terminations': 0,
            'consensus_achieved': 0,
            'average_execution_time': 0.0,
            'validator_performance': defaultdict(list)
        }
    
    def _initialize_validators(self):
        """Initialize validators based on configuration."""
        if self.configuration.enable_morphological:
            self.validators['morphological'] = MorphologicalValidator()
        
        if self.configuration.enable_contextual:
            self.validators['contextual'] = ContextValidator()
        
        if self.configuration.enable_domain:
            self.validators['domain'] = DomainValidator()
        
        if self.configuration.enable_cross_rule:
            self.validators['cross_rule'] = CrossRuleValidator()
        
        # Validate minimum validator count
        if len(self.validators) < self.configuration.minimum_validator_count:
            raise ValueError(
                f"Pipeline requires at least {self.configuration.minimum_validator_count} validators, "
                f"but only {len(self.validators)} are enabled"
            )
    
    def _generate_pipeline_id(self) -> str:
        """Generate unique pipeline ID."""
        import uuid
        return f"pipeline_{uuid.uuid4().hex[:8]}"
    
    def validate_error(self, context: ValidationContext) -> PipelineResult:
        """
        Execute the validation pipeline for a given error context.
        
        Args:
            context: Validation context containing error information
            
        Returns:
            PipelineResult with comprehensive validation analysis
        """
        start_time = time.time()
        pipeline_id = self._generate_pipeline_id()
        
        # Initialize audit trail
        audit_trail = PipelineAuditTrail(
            pipeline_id=pipeline_id,
            execution_start_time=start_time,
            execution_end_time=0.0,
            total_execution_time=0.0,
            configuration=self.configuration,
            validation_context=context,
            stages_executed=[],
            validator_executions=[],
            consensus_analysis=None,
            final_result=None,
            performance_metrics={},
            errors_encountered=[],
            warnings_generated=[]
        )
        
        try:
            # Stage 1: Initialization
            audit_trail.stages_executed.append(PipelineStage.INITIALIZATION)
            
            # Record pipeline execution start
            if MONITORING_AVAILABLE:
                record_pipeline_execution('initialization', 'started')
            
            # Stage 2-5: Execute validators
            validator_executions = self._execute_validators(context, audit_trail)
            
            # Check for early termination
            early_termination, termination_reason = self._check_early_termination(validator_executions)
            
            # Stage 6: Build consensus
            audit_trail.stages_executed.append(PipelineStage.CONSENSUS_BUILDING)
            consensus_start_time = time.time()
            consensus_analysis = self._build_consensus(validator_executions, context)
            audit_trail.consensus_analysis = consensus_analysis
            
            # Record consensus building duration
            if MONITORING_AVAILABLE:
                consensus_duration = time.time() - consensus_start_time
                rule_type = context.additional_context.get('rule_type', 'unknown')
                record_validation_duration('consensus_building', rule_type, consensus_duration)
                record_pipeline_execution('consensus_building', 'completed')
            
            # Create final result
            final_result = self._create_final_result(consensus_analysis, validator_executions, context)
            audit_trail.final_result = final_result
            
            # Stage 7: Generate audit trail
            if self.configuration.enable_audit_trail:
                audit_trail.stages_executed.append(PipelineStage.AUDIT_TRAIL_GENERATION)
                audit_trail = self._enhance_audit_trail(audit_trail, validator_executions)
            
            # Stage 8: Finalization
            audit_trail.stages_executed.append(PipelineStage.FINALIZATION)
            end_time = time.time()
            audit_trail.execution_end_time = end_time
            audit_trail.total_execution_time = end_time - start_time
            
            # Create pipeline result
            pipeline_result = self._create_pipeline_result(
                final_result, validator_executions, consensus_analysis,
                audit_trail, early_termination, termination_reason
            )
            
            # Update performance metrics
            self._update_performance_metrics(pipeline_result)
            
            # Store execution history
            self.execution_history.append(audit_trail)
            
            return pipeline_result
            
        except Exception as e:
            # Handle pipeline errors
            return self._handle_pipeline_error(e, context, audit_trail, start_time)
    
    def _execute_validators(self, context: ValidationContext, 
                          audit_trail: PipelineAuditTrail) -> List[ValidatorExecution]:
        """Execute all enabled validators."""
        validator_executions = []
        
        # Define validator execution order and stages
        validator_stages = [
            ('morphological', PipelineStage.MORPHOLOGICAL_VALIDATION),
            ('contextual', PipelineStage.CONTEXTUAL_VALIDATION),
            ('domain', PipelineStage.DOMAIN_VALIDATION),
            ('cross_rule', PipelineStage.CROSS_RULE_VALIDATION)
        ]
        
        for validator_name, stage in validator_stages:
            if validator_name not in self.validators:
                continue
            
            audit_trail.stages_executed.append(stage)
            validator = self.validators[validator_name]
            
            execution_start = time.time()
            result = None
            error = None
            
            try:
                # Execute validator
                result = validator.validate_error(context)
                
            except Exception as e:
                error = e
                audit_trail.errors_encountered.append(f"{validator_name}: {str(e)}")
                
                if not self.configuration.continue_on_validator_error:
                    raise
            
            execution_time = time.time() - execution_start
            
            # Create validator execution record
            execution = ValidatorExecution(
                validator_name=validator_name,
                result=result,
                execution_time=execution_time,
                error=error,
                stage=stage
            )
            
            validator_executions.append(execution)
            audit_trail.validator_executions.append(execution)
            
            # Check for early termination after each validator
            if self.configuration.enable_early_termination:
                early_term, reason = self._check_early_termination(validator_executions)
                if early_term:
                    execution.terminated_early = True
                    break
        
        return validator_executions
    
    def _check_early_termination(self, executions: List[ValidatorExecution]) -> Tuple[bool, Optional[TerminationCondition]]:
        """Check if early termination conditions are met."""
        if not self.configuration.enable_early_termination:
            return False, None
        
        successful_executions = [e for e in executions if e.result is not None]
        
        if len(successful_executions) < 2:
            return False, None
        
        for condition in self.configuration.termination_conditions:
            if condition == TerminationCondition.HIGH_CONFIDENCE_CONSENSUS:
                if self._has_high_confidence_consensus(successful_executions):
                    return True, condition
            
            elif condition == TerminationCondition.UNANIMOUS_DECISION:
                if self._has_unanimous_decision(successful_executions):
                    return True, condition
            
            elif condition == TerminationCondition.VALIDATOR_QUORUM:
                if len(successful_executions) >= 3:  # Quorum of 3 validators
                    return True, condition
        
        return False, None
    
    def _has_high_confidence_consensus(self, executions: List[ValidatorExecution]) -> bool:
        """Check if there's high confidence consensus."""
        if len(executions) < 2:
            return False
        
        decisions = [e.result.decision for e in executions]
        confidences = [e.result.confidence_score for e in executions]
        
        # Check if most validators agree and have high confidence
        decision_counts = Counter(decisions)
        most_common_decision, count = decision_counts.most_common(1)[0]
        
        if count / len(executions) >= self.configuration.consensus_threshold:
            # Check if agreeing validators have high confidence
            agreeing_confidences = [
                conf for exec, conf in zip(executions, confidences)
                if exec.result.decision == most_common_decision
            ]
            avg_confidence = sum(agreeing_confidences) / len(agreeing_confidences)
            
            return avg_confidence >= self.configuration.high_confidence_threshold
        
        return False
    
    def _has_unanimous_decision(self, executions: List[ValidatorExecution]) -> bool:
        """Check if all validators agree on the decision."""
        if len(executions) < 2:
            return False
        
        decisions = [e.result.decision for e in executions]
        return len(set(decisions)) == 1
    
    def _build_consensus(self, executions: List[ValidatorExecution], 
                        context: ValidationContext) -> ConsensusAnalysis:
        """Build consensus from validator results."""
        successful_executions = [e for e in executions if e.result is not None]
        
        if not successful_executions:
            # No successful validators - create default consensus
            return self._create_default_consensus()
        
        # Try consensus strategies in order
        strategies_to_try = [self.configuration.consensus_strategy] + self.configuration.fallback_strategies
        
        for strategy in strategies_to_try:
            try:
                consensus = self._apply_consensus_strategy(strategy, successful_executions, context)
                if consensus:
                    consensus.strategies_attempted = strategies_to_try[:strategies_to_try.index(strategy) + 1]
                    return consensus
            except Exception:
                continue
        
        # If all strategies fail, use best confidence fallback
        return self._apply_best_confidence_strategy(successful_executions)
    
    def _apply_consensus_strategy(self, strategy: ConsensusStrategy,
                                executions: List[ValidatorExecution],
                                context: ValidationContext) -> Optional[ConsensusAnalysis]:
        """Apply a specific consensus strategy."""
        
        if strategy == ConsensusStrategy.MAJORITY_VOTE:
            return self._majority_vote_consensus(executions)
        
        elif strategy == ConsensusStrategy.WEIGHTED_AVERAGE:
            return self._weighted_average_consensus(executions)
        
        elif strategy == ConsensusStrategy.CONFIDENCE_THRESHOLD:
            return self._confidence_threshold_consensus(executions)
        
        elif strategy == ConsensusStrategy.UNANIMOUS_AGREEMENT:
            return self._unanimous_agreement_consensus(executions)
        
        elif strategy == ConsensusStrategy.BEST_CONFIDENCE:
            return self._best_confidence_consensus(executions)
        
        elif strategy == ConsensusStrategy.STAGED_FALLBACK:
            return self._staged_fallback_consensus(executions, context)
        
        return None
    
    def _majority_vote_consensus(self, executions: List[ValidatorExecution]) -> ConsensusAnalysis:
        """Build consensus using majority vote."""
        decisions = [e.result.decision for e in executions]
        decision_counts = Counter(decisions)
        
        majority_decision, count = decision_counts.most_common(1)[0]
        agreement_score = count / len(executions)
        
        # Calculate average confidence for majority decision
        majority_confidences = [
            e.result.confidence_score for e in executions
            if e.result.decision == majority_decision
        ]
        final_confidence = sum(majority_confidences) / len(majority_confidences)
        
        # Determine validator agreements
        validator_agreements = {
            e.validator_name: e.result.decision == majority_decision
            for e in executions
        }
        
        # Calculate confidence spread
        all_confidences = [e.result.confidence_score for e in executions]
        confidence_spread = max(all_confidences) - min(all_confidences)
        
        # Identify outliers
        outlier_validators = [
            e.validator_name for e in executions
            if e.result.decision != majority_decision
        ]
        
        return ConsensusAnalysis(
            strategy_used=ConsensusStrategy.MAJORITY_VOTE,
            strategies_attempted=[ConsensusStrategy.MAJORITY_VOTE],
            final_decision=majority_decision,
            final_confidence=final_confidence,
            agreement_score=agreement_score,
            validator_agreements=validator_agreements,
            confidence_spread=confidence_spread,
            outlier_validators=outlier_validators,
            consensus_metadata={
                'decision_counts': dict(decision_counts),
                'majority_count': count,
                'total_validators': len(executions)
            }
        )
    
    def _weighted_average_consensus(self, executions: List[ValidatorExecution]) -> ConsensusAnalysis:
        """Build consensus using weighted average of confidence scores."""
        weights = self.configuration.validator_weights
        
        # Map validator names to weights
        weight_map = {
            'morphological': weights.morphological,
            'contextual': weights.contextual,
            'domain': weights.domain,
            'cross_rule': weights.cross_rule
        }
        
        # Calculate weighted scores for each decision
        decision_scores = defaultdict(float)
        total_weight = 0.0
        
        for execution in executions:
            validator_name = execution.validator_name
            weight = weight_map.get(validator_name, 0.25)  # Default weight
            decision = execution.result.decision
            confidence = execution.result.confidence_score
            
            decision_scores[decision] += weight * confidence
            total_weight += weight
        
        # Normalize scores
        if total_weight > 0:
            for decision in decision_scores:
                decision_scores[decision] /= total_weight
        
        # Choose decision with highest weighted score
        final_decision = max(decision_scores.items(), key=lambda x: x[1])[0]
        final_confidence = decision_scores[final_decision]
        
        # Calculate agreement metrics
        agreements = [e.result.decision == final_decision for e in executions]
        agreement_score = sum(agreements) / len(agreements)
        
        validator_agreements = {
            e.validator_name: e.result.decision == final_decision
            for e in executions
        }
        
        # Calculate confidence spread
        all_confidences = [e.result.confidence_score for e in executions]
        confidence_spread = max(all_confidences) - min(all_confidences)
        
        outlier_validators = [
            e.validator_name for e in executions
            if e.result.decision != final_decision
        ]
        
        return ConsensusAnalysis(
            strategy_used=ConsensusStrategy.WEIGHTED_AVERAGE,
            strategies_attempted=[ConsensusStrategy.WEIGHTED_AVERAGE],
            final_decision=final_decision,
            final_confidence=final_confidence,
            agreement_score=agreement_score,
            validator_agreements=validator_agreements,
            confidence_spread=confidence_spread,
            outlier_validators=outlier_validators,
            consensus_metadata={
                'decision_scores': dict(decision_scores),
                'total_weight': total_weight,
                'weights_used': weight_map
            }
        )
    
    def _confidence_threshold_consensus(self, executions: List[ValidatorExecution]) -> Optional[ConsensusAnalysis]:
        """Build consensus requiring minimum confidence threshold."""
        high_confidence_executions = [
            e for e in executions
            if e.result.confidence_score >= self.configuration.minimum_consensus_confidence
        ]
        
        if not high_confidence_executions:
            return None  # No validators meet confidence threshold
        
        # Use majority vote among high-confidence validators
        return self._majority_vote_consensus(high_confidence_executions)
    
    def _unanimous_agreement_consensus(self, executions: List[ValidatorExecution]) -> Optional[ConsensusAnalysis]:
        """Build consensus requiring unanimous agreement."""
        decisions = [e.result.decision for e in executions]
        
        if len(set(decisions)) == 1:
            # All validators agree
            return self._majority_vote_consensus(executions)
        
        return None  # No unanimous agreement
    
    def _best_confidence_consensus(self, executions: List[ValidatorExecution]) -> ConsensusAnalysis:
        """Build consensus by choosing the result with highest confidence."""
        best_execution = max(executions, key=lambda e: e.result.confidence_score)
        
        final_decision = best_execution.result.decision
        final_confidence = best_execution.result.confidence_score
        
        # Calculate agreement with best result
        agreements = [e.result.decision == final_decision for e in executions]
        agreement_score = sum(agreements) / len(agreements)
        
        validator_agreements = {
            e.validator_name: e.result.decision == final_decision
            for e in executions
        }
        
        all_confidences = [e.result.confidence_score for e in executions]
        confidence_spread = max(all_confidences) - min(all_confidences)
        
        outlier_validators = [
            e.validator_name for e in executions
            if e.result.decision != final_decision
        ]
        
        return ConsensusAnalysis(
            strategy_used=ConsensusStrategy.BEST_CONFIDENCE,
            strategies_attempted=[ConsensusStrategy.BEST_CONFIDENCE],
            final_decision=final_decision,
            final_confidence=final_confidence,
            agreement_score=agreement_score,
            validator_agreements=validator_agreements,
            confidence_spread=confidence_spread,
            outlier_validators=outlier_validators,
            consensus_metadata={
                'best_validator': best_execution.validator_name,
                'best_confidence': final_confidence,
                'confidence_ranking': [
                    (e.validator_name, e.result.confidence_score)
                    for e in sorted(executions, key=lambda x: x.result.confidence_score, reverse=True)
                ]
            }
        )
    
    def _staged_fallback_consensus(self, executions: List[ValidatorExecution],
                                 context: ValidationContext) -> ConsensusAnalysis:
        """Build consensus using staged fallback strategy."""
        # Try strategies in order: unanimous -> weighted -> majority -> best confidence
        fallback_strategies = [
            ConsensusStrategy.UNANIMOUS_AGREEMENT,
            ConsensusStrategy.WEIGHTED_AVERAGE,
            ConsensusStrategy.MAJORITY_VOTE,
            ConsensusStrategy.BEST_CONFIDENCE
        ]
        
        for strategy in fallback_strategies:
            consensus = self._apply_consensus_strategy(strategy, executions, context)
            if consensus:
                consensus.strategy_used = ConsensusStrategy.STAGED_FALLBACK
                consensus.consensus_metadata['fallback_strategy_used'] = strategy
                return consensus
        
        # Final fallback - should never reach here
        return self._best_confidence_consensus(executions)
    
    def _apply_best_confidence_strategy(self, executions: List[ValidatorExecution]) -> ConsensusAnalysis:
        """Apply best confidence strategy as final fallback."""
        return self._best_confidence_consensus(executions)
    
    def _create_default_consensus(self) -> ConsensusAnalysis:
        """Create default consensus when no validators succeed."""
        return ConsensusAnalysis(
            strategy_used=ConsensusStrategy.BEST_CONFIDENCE,
            strategies_attempted=[],
            final_decision=ValidationDecision.UNCERTAIN,
            final_confidence=0.0,
            agreement_score=0.0,
            validator_agreements={},
            confidence_spread=0.0,
            outlier_validators=[],
            consensus_metadata={'error': 'no_successful_validators'}
        )
    
    def _create_final_result(self, consensus: ConsensusAnalysis,
                           executions: List[ValidatorExecution],
                           context: ValidationContext) -> ValidationResult:
        """Create the final validation result."""
        
        # Aggregate evidence from all successful validators
        aggregated_evidence = []
        for execution in executions:
            if execution.result:
                aggregated_evidence.extend(execution.result.evidence)
        
        # Calculate total execution time
        total_time = sum(e.execution_time for e in executions)
        
        # Create final result
        return ValidationResult(
            validator_name="validation_pipeline",
            decision=consensus.final_decision,
            confidence=self._convert_confidence_to_level(consensus.final_confidence),
            confidence_score=consensus.final_confidence,
            evidence=aggregated_evidence,
            reasoning=self._generate_consensus_reasoning(consensus, executions),
            error_text=context.error_text,
            error_position=context.error_position,
            rule_type=context.rule_type,
            rule_name=context.rule_name,
            validation_time=total_time,
            metadata={
                'consensus_strategy': consensus.strategy_used.value,
                'agreement_score': consensus.agreement_score,
                'validator_count': len([e for e in executions if e.result]),
                'confidence_spread': consensus.confidence_spread,
                'outlier_validators': consensus.outlier_validators,
                'individual_decisions': {
                    e.validator_name: e.result.decision.value if e.result else 'error'
                    for e in executions
                },
                'individual_confidences': {
                    e.validator_name: e.result.confidence_score if e.result else 0.0
                    for e in executions
                }
            }
        )
    
    def _convert_confidence_to_level(self, confidence_score: float) -> ValidationConfidence:
        """Convert confidence score to confidence level."""
        if confidence_score >= 0.8:
            return ValidationConfidence.HIGH
        elif confidence_score >= 0.6:
            return ValidationConfidence.MEDIUM
        else:
            return ValidationConfidence.LOW
    
    def _generate_consensus_reasoning(self, consensus: ConsensusAnalysis,
                                    executions: List[ValidatorExecution]) -> str:
        """Generate reasoning for the consensus decision."""
        successful_count = len([e for e in executions if e.result])
        strategy = consensus.strategy_used.value.replace('_', ' ').title()
        
        reasoning = f"Pipeline consensus via {strategy}: "
        
        if consensus.agreement_score >= 0.8:
            reasoning += f"Strong agreement among {successful_count} validators "
        elif consensus.agreement_score >= 0.6:
            reasoning += f"Moderate agreement among {successful_count} validators "
        else:
            reasoning += f"Limited agreement among {successful_count} validators "
        
        reasoning += f"(confidence: {consensus.final_confidence:.3f}, "
        reasoning += f"agreement: {consensus.agreement_score:.1%})"
        
        if consensus.outlier_validators:
            reasoning += f" [Outliers: {', '.join(consensus.outlier_validators)}]"
        
        return reasoning
    
    def _enhance_audit_trail(self, audit_trail: PipelineAuditTrail,
                           executions: List[ValidatorExecution]) -> PipelineAuditTrail:
        """Enhance audit trail with additional performance metrics."""
        
        # Performance metrics
        execution_times = [e.execution_time for e in executions if e.result]
        
        audit_trail.performance_metrics = {
            'validator_count': len(executions),
            'successful_validators': len([e for e in executions if e.result]),
            'failed_validators': len([e for e in executions if e.error]),
            'total_validator_time': sum(e.execution_time for e in executions),
            'average_validator_time': sum(execution_times) / len(execution_times) if execution_times else 0.0,
            'fastest_validator': min(execution_times) if execution_times else 0.0,
            'slowest_validator': max(execution_times) if execution_times else 0.0,
            'evidence_pieces': sum(len(e.result.evidence) if e.result else 0 for e in executions),
            'total_evidence_types': len(set(
                ev.evidence_type
                for e in executions if e.result
                for ev in e.result.evidence
            ))
        }
        
        return audit_trail
    
    def _create_pipeline_result(self, final_result: ValidationResult,
                              executions: List[ValidatorExecution],
                              consensus: ConsensusAnalysis,
                              audit_trail: PipelineAuditTrail,
                              early_termination: bool,
                              termination_reason: Optional[TerminationCondition]) -> PipelineResult:
        """Create comprehensive pipeline result."""
        
        # Individual validator results
        validator_results = {
            e.validator_name: e.result
            for e in executions if e.result
        }
        
        # Execution times
        individual_times = {
            e.validator_name: e.execution_time
            for e in executions
        }
        
        # Aggregate evidence
        aggregated_evidence = []
        evidence_by_validator = {}
        
        for execution in executions:
            if execution.result:
                evidence_by_validator[execution.validator_name] = execution.result.evidence
                aggregated_evidence.extend(execution.result.evidence)
        
        return PipelineResult(
            validation_result=final_result,
            pipeline_confidence=consensus.final_confidence,
            consensus_achieved=consensus.agreement_score >= 0.6,
            early_termination=early_termination,
            termination_reason=termination_reason,
            validator_results=validator_results,
            consensus_analysis=consensus,
            audit_trail=audit_trail,
            total_execution_time=audit_trail.total_execution_time,
            individual_execution_times=individual_times,
            aggregated_evidence=aggregated_evidence,
            evidence_by_validator=evidence_by_validator
        )
    
    def _handle_pipeline_error(self, error: Exception, context: ValidationContext,
                             audit_trail: PipelineAuditTrail, start_time: float) -> PipelineResult:
        """Handle pipeline execution errors."""
        
        end_time = time.time()
        audit_trail.execution_end_time = end_time
        audit_trail.total_execution_time = end_time - start_time
        audit_trail.errors_encountered.append(f"Pipeline error: {str(error)}")
        
        # Create error result
        error_result = ValidationResult(
            validator_name="validation_pipeline",
            decision=ValidationDecision.UNCERTAIN,
            confidence=ValidationConfidence.LOW,
            confidence_score=0.0,
            evidence=[],
            reasoning=f"Pipeline execution failed: {str(error)}",
            error_text=context.error_text,
            error_position=context.error_position,
            rule_type=context.rule_type,
            rule_name=context.rule_name,
            validation_time=audit_trail.total_execution_time,
            metadata={'pipeline_error': str(error)}
        )
        
        # Create default consensus
        consensus = self._create_default_consensus()
        consensus.consensus_metadata['pipeline_error'] = str(error)
        
        audit_trail.final_result = error_result
        audit_trail.consensus_analysis = consensus
        
        return PipelineResult(
            validation_result=error_result,
            pipeline_confidence=0.0,
            consensus_achieved=False,
            early_termination=False,
            termination_reason=TerminationCondition.CRITICAL_FAILURE,
            validator_results={},
            consensus_analysis=consensus,
            audit_trail=audit_trail,
            total_execution_time=audit_trail.total_execution_time,
            individual_execution_times={},
            aggregated_evidence=[],
            evidence_by_validator={}
        )
    
    def _update_performance_metrics(self, result: PipelineResult):
        """Update pipeline performance metrics."""
        self.performance_metrics['total_executions'] += 1
        
        if result.consensus_achieved:
            self.performance_metrics['successful_executions'] += 1
            self.performance_metrics['consensus_achieved'] += 1
        
        if result.early_termination:
            self.performance_metrics['early_terminations'] += 1
        
        # Update average execution time
        total_time = self.performance_metrics['average_execution_time']
        count = self.performance_metrics['total_executions']
        
        new_average = ((total_time * (count - 1)) + result.total_execution_time) / count
        self.performance_metrics['average_execution_time'] = new_average
        
        # Update validator performance
        for validator_name, exec_time in result.individual_execution_times.items():
            self.performance_metrics['validator_performance'][validator_name].append(exec_time)
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """Get comprehensive pipeline information."""
        return {
            "pipeline_id": self.pipeline_id,
            "configuration": {
                "consensus_strategy": self.configuration.consensus_strategy.value,
                "early_termination_enabled": self.configuration.enable_early_termination,
                "validator_weights": {
                    "morphological": self.configuration.validator_weights.morphological,
                    "contextual": self.configuration.validator_weights.contextual,
                    "domain": self.configuration.validator_weights.domain,
                    "cross_rule": self.configuration.validator_weights.cross_rule
                },
                "enabled_validators": list(self.validators.keys()),
                "minimum_validator_count": self.configuration.minimum_validator_count
            },
            "performance_metrics": dict(self.performance_metrics),
            "validator_info": {
                name: validator.get_validator_info()
                for name, validator in self.validators.items()
            },
            "execution_history_count": len(self.execution_history)
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the pipeline."""
        metrics = self.performance_metrics
        
        success_rate = (
            metrics['successful_executions'] / metrics['total_executions']
            if metrics['total_executions'] > 0 else 0.0
        )
        
        early_termination_rate = (
            metrics['early_terminations'] / metrics['total_executions']
            if metrics['total_executions'] > 0 else 0.0
        )
        
        validator_avg_times = {}
        for validator_name, times in metrics['validator_performance'].items():
            if times:
                validator_avg_times[validator_name] = sum(times) / len(times)
        
        return {
            "total_executions": metrics['total_executions'],
            "success_rate": success_rate,
            "consensus_rate": success_rate,  # Same as success rate for now
            "early_termination_rate": early_termination_rate,
            "average_execution_time_ms": metrics['average_execution_time'] * 1000,
            "validator_average_times_ms": {
                name: time_sec * 1000
                for name, time_sec in validator_avg_times.items()
            }
        }
    
    def clear_history(self):
        """Clear execution history and reset performance metrics."""
        self.execution_history.clear()
        self.performance_metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'early_terminations': 0,
            'consensus_achieved': 0,
            'average_execution_time': 0.0,
            'validator_performance': defaultdict(list)
        }
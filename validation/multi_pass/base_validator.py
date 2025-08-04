"""
BasePassValidator Class
Abstract base class for all multi-pass validation components.
Defines the interface and common functionality for validation passes.
"""

import time
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum

from ..confidence.confidence_calculator import ConfidenceCalculator, ConfidenceBreakdown


class ValidationDecision(Enum):
    """Possible validation decisions."""
    ACCEPT = "accept"       # Error is valid and should be reported
    REJECT = "reject"       # Error is invalid and should be filtered out
    UNCERTAIN = "uncertain" # Validator cannot make a clear decision


class ValidationConfidence(Enum):
    """Confidence levels for validation decisions."""
    HIGH = "high"       # Very confident in the decision (>0.8)
    MEDIUM = "medium"   # Moderately confident (0.5-0.8)
    LOW = "low"         # Low confidence (<0.5)


@dataclass
class ValidationEvidence:
    """Evidence supporting a validation decision."""
    
    evidence_type: str          # Type of evidence (e.g., 'morphological', 'contextual')
    confidence: float           # Confidence in this evidence (0-1)
    description: str            # Human-readable description
    source_data: Dict[str, Any] # Raw data supporting this evidence
    weight: float = 1.0         # Weight of this evidence in decision making


@dataclass
class ValidationResult:
    """Result of a single validation pass."""
    
    validator_name: str                    # Name of the validator that produced this result
    decision: ValidationDecision           # The validation decision made
    confidence: ValidationConfidence       # Confidence level in the decision
    confidence_score: float                # Numerical confidence score (0-1)
    
    # Evidence and reasoning
    evidence: List[ValidationEvidence]     # Evidence supporting the decision
    reasoning: str                         # Human-readable explanation of reasoning
    
    # Error context
    error_text: str                        # The text containing the error
    error_position: int                    # Character position of the error
    rule_type: Optional[str] = None        # Type of rule being validated
    rule_name: Optional[str] = None        # Specific rule being validated
    
    # Performance metrics
    validation_time: float = 0.0           # Time taken for validation (seconds)
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_decisive(self, min_confidence: float = 0.7) -> bool:
        """Check if this result is decisive enough to act upon."""
        return (self.decision != ValidationDecision.UNCERTAIN and 
                self.confidence_score >= min_confidence)
    
    def get_decision_strength(self) -> float:
        """Get the strength of the decision (0-1, higher = stronger)."""
        if self.decision == ValidationDecision.UNCERTAIN:
            return 0.0
        return self.confidence_score


@dataclass
class ValidationContext:
    """Context information for validation."""
    
    # Text and error information
    text: str                              # Full text being analyzed
    error_position: int                    # Position of the potential error
    error_text: str                        # The specific error text
    
    # Rule information
    rule_type: Optional[str] = None        # Type of rule (e.g., 'grammar', 'style')
    rule_name: Optional[str] = None        # Specific rule name
    rule_severity: Optional[str] = None    # Rule severity level
    
    # Content metadata
    content_type: Optional[str] = None     # Type of content (e.g., 'technical', 'narrative')
    domain: Optional[str] = None           # Content domain (e.g., 'programming', 'medical')
    
    # Additional context
    confidence_breakdown: Optional[ConfidenceBreakdown] = None  # Pre-calculated confidence
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationPerformanceMetrics:
    """Performance metrics for validation operations."""
    
    total_validations: int = 0             # Total number of validations performed
    validation_times: List[float] = field(default_factory=list)  # Individual validation times
    
    # Decision statistics
    decisions_made: Dict[ValidationDecision, int] = field(default_factory=lambda: {
        ValidationDecision.ACCEPT: 0,
        ValidationDecision.REJECT: 0,
        ValidationDecision.UNCERTAIN: 0
    })
    
    # Confidence statistics
    confidence_scores: List[float] = field(default_factory=list)
    
    # Error tracking
    validation_errors: int = 0             # Number of validation errors encountered
    
    def add_validation_result(self, result: ValidationResult) -> None:
        """Add a validation result to performance tracking."""
        self.total_validations += 1
        self.validation_times.append(result.validation_time)
        self.decisions_made[result.decision] += 1
        self.confidence_scores.append(result.confidence_score)
    
    def get_average_validation_time(self) -> float:
        """Get average validation time in seconds."""
        if not self.validation_times:
            return 0.0
        return sum(self.validation_times) / len(self.validation_times)
    
    def get_average_confidence(self) -> float:
        """Get average confidence score."""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)
    
    def get_decision_rate(self, decision: ValidationDecision) -> float:
        """Get the rate of a specific decision type."""
        if self.total_validations == 0:
            return 0.0
        return self.decisions_made[decision] / self.total_validations
    
    def get_decisiveness_rate(self, min_confidence: float = 0.7) -> float:
        """Get the rate of decisive decisions (not uncertain and high confidence)."""
        if self.total_validations == 0:
            return 0.0
        
        decisive_count = 0
        for i, decision in enumerate([ValidationDecision.ACCEPT, ValidationDecision.REJECT, ValidationDecision.UNCERTAIN]):
            if decision != ValidationDecision.UNCERTAIN:
                # Count decisions with sufficient confidence
                start_idx = sum(self.decisions_made[d] for d in list(ValidationDecision)[:list(ValidationDecision).index(decision)])
                end_idx = start_idx + self.decisions_made[decision]
                decision_confidences = self.confidence_scores[start_idx:end_idx]
                decisive_count += sum(1 for conf in decision_confidences if conf >= min_confidence)
        
        return decisive_count / self.total_validations


class BasePassValidator(ABC):
    """
    Abstract base class for all multi-pass validation components.
    
    This class defines the interface and provides common functionality
    for all validation passes in the multi-pass validation system.
    Each concrete validator implements specific validation logic while
    inheriting common features like confidence integration, performance
    monitoring, and decision tracking.
    """
    
    def __init__(self, 
                 validator_name: str,
                 confidence_calculator: Optional[ConfidenceCalculator] = None,
                 enable_performance_tracking: bool = True,
                 min_confidence_threshold: float = 0.5):
        """
        Initialize the base validator.
        
        Args:
            validator_name: Unique name for this validator
            confidence_calculator: Optional confidence calculator for scoring
            enable_performance_tracking: Whether to track performance metrics
            min_confidence_threshold: Minimum confidence for decisive decisions
        """
        self.validator_name = validator_name
        self.confidence_calculator = confidence_calculator or ConfidenceCalculator()
        self.enable_performance_tracking = enable_performance_tracking
        self.min_confidence_threshold = min_confidence_threshold
        
        # Performance tracking
        self.performance_metrics = ValidationPerformanceMetrics()
        
        # Configuration
        self.config: Dict[str, Any] = {}
        
        # Validation history for debugging
        self.validation_history: List[ValidationResult] = []
        self.max_history_size = 1000  # Prevent memory bloat
    
    @abstractmethod
    def _validate_error(self, context: ValidationContext) -> ValidationResult:
        """
        Abstract method for validating a specific error.
        
        Each concrete validator must implement this method to provide
        their specific validation logic.
        
        Args:
            context: Validation context containing error and metadata
            
        Returns:
            ValidationResult with decision and supporting evidence
        """
        pass
    
    def validate_error(self, context: ValidationContext) -> ValidationResult:
        """
        Public interface for error validation with performance tracking.
        
        Args:
            context: Validation context containing error and metadata
            
        Returns:
            ValidationResult with decision and supporting evidence
        """
        start_time = time.time()
        
        try:
            # Delegate to concrete implementation
            result = self._validate_error(context)
            
            # Ensure validation time is recorded
            if result.validation_time == 0.0:
                result.validation_time = time.time() - start_time
            
            # Track performance if enabled
            if self.enable_performance_tracking:
                self.performance_metrics.add_validation_result(result)
            
            # Add to history (with size limit)
            self._add_to_history(result)
            
            return result
            
        except Exception as e:
            # Handle validation errors gracefully
            self.performance_metrics.validation_errors += 1
            
            error_result = ValidationResult(
                validator_name=self.validator_name,
                decision=ValidationDecision.UNCERTAIN,
                confidence=ValidationConfidence.LOW,
                confidence_score=0.0,
                evidence=[ValidationEvidence(
                    evidence_type="error",
                    confidence=0.0,
                    description=f"Validation failed: {str(e)}",
                    source_data={"error_type": type(e).__name__, "error_message": str(e)}
                )],
                reasoning=f"Validation failed due to error: {str(e)}",
                error_text=context.error_text,
                error_position=context.error_position,
                rule_type=context.rule_type,
                rule_name=context.rule_name,
                validation_time=time.time() - start_time,
                metadata={"validation_error": True}
            )
            
            self._add_to_history(error_result)
            return error_result
    
    def calculate_confidence_score(self, context: ValidationContext) -> ConfidenceBreakdown:
        """
        Calculate confidence score using the integrated confidence calculator.
        
        Args:
            context: Validation context
            
        Returns:
            Detailed confidence breakdown
        """
        if context.confidence_breakdown is not None:
            return context.confidence_breakdown
        
        return self.confidence_calculator.calculate_confidence(
            text=context.text,
            error_position=context.error_position,
            rule_type=context.rule_type,
            content_type=context.content_type
        )
    
    def _convert_confidence_to_level(self, confidence_score: float) -> ValidationConfidence:
        """Convert numerical confidence to confidence level enum."""
        if confidence_score >= 0.8:
            return ValidationConfidence.HIGH
        elif confidence_score >= 0.5:
            return ValidationConfidence.MEDIUM
        else:
            return ValidationConfidence.LOW
    
    def _add_to_history(self, result: ValidationResult) -> None:
        """Add validation result to history with size management."""
        self.validation_history.append(result)
        
        # Maintain history size limit
        if len(self.validation_history) > self.max_history_size:
            self.validation_history = self.validation_history[-self.max_history_size:]
    
    def get_performance_metrics(self) -> ValidationPerformanceMetrics:
        """Get performance metrics for this validator."""
        return self.performance_metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of performance metrics."""
        metrics = self.performance_metrics
        
        return {
            "validator_name": self.validator_name,
            "total_validations": metrics.total_validations,
            "average_validation_time": metrics.get_average_validation_time(),
            "average_confidence": metrics.get_average_confidence(),
            "decision_rates": {
                "accept_rate": metrics.get_decision_rate(ValidationDecision.ACCEPT),
                "reject_rate": metrics.get_decision_rate(ValidationDecision.REJECT),
                "uncertain_rate": metrics.get_decision_rate(ValidationDecision.UNCERTAIN)
            },
            "decisiveness_rate": metrics.get_decisiveness_rate(self.min_confidence_threshold),
            "validation_errors": metrics.validation_errors,
            "config": self.config
        }
    
    def clear_performance_metrics(self) -> None:
        """Clear performance metrics and history."""
        self.performance_metrics = ValidationPerformanceMetrics()
        self.validation_history = []
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """Set configuration for this validator."""
        self.config.update(config)
        self._apply_config(config)
    
    def _apply_config(self, config: Dict[str, Any]) -> None:
        """Apply configuration changes. Override in subclasses as needed."""
        # Update basic settings from config
        if "min_confidence_threshold" in config:
            self.min_confidence_threshold = config["min_confidence_threshold"]
        
        if "max_history_size" in config:
            self.max_history_size = config["max_history_size"]
            # Trim history if needed
            if len(self.validation_history) > self.max_history_size:
                self.validation_history = self.validation_history[-self.max_history_size:]
    
    def get_recent_validations(self, limit: int = 10) -> List[ValidationResult]:
        """Get recent validation results for debugging."""
        return self.validation_history[-limit:] if self.validation_history else []
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get detailed validation statistics."""
        if not self.validation_history:
            return {"message": "No validation history available"}
        
        # Analyze recent validation patterns
        recent_results = self.get_recent_validations(100)  # Last 100 validations
        
        decision_patterns = {}
        confidence_patterns = {}
        evidence_patterns = {}
        
        for result in recent_results:
            # Decision patterns
            decision = result.decision.value
            if decision not in decision_patterns:
                decision_patterns[decision] = []
            decision_patterns[decision].append(result.confidence_score)
            
            # Confidence patterns
            conf_level = result.confidence.value
            if conf_level not in confidence_patterns:
                confidence_patterns[conf_level] = 0
            confidence_patterns[conf_level] += 1
            
            # Evidence patterns
            for evidence in result.evidence:
                evidence_type = evidence.evidence_type
                if evidence_type not in evidence_patterns:
                    evidence_patterns[evidence_type] = []
                evidence_patterns[evidence_type].append(evidence.confidence)
        
        return {
            "validator_name": self.validator_name,
            "total_validations": len(self.validation_history),
            "recent_validations_analyzed": len(recent_results),
            "decision_patterns": {
                decision: {
                    "count": len(scores),
                    "avg_confidence": sum(scores) / len(scores) if scores else 0.0,
                    "min_confidence": min(scores) if scores else 0.0,
                    "max_confidence": max(scores) if scores else 0.0
                }
                for decision, scores in decision_patterns.items()
            },
            "confidence_level_distribution": confidence_patterns,
            "evidence_type_patterns": {
                evidence_type: {
                    "count": len(confidences),
                    "avg_confidence": sum(confidences) / len(confidences) if confidences else 0.0
                }
                for evidence_type, confidences in evidence_patterns.items()
            }
        }
    
    @abstractmethod
    def get_validator_info(self) -> Dict[str, Any]:
        """
        Get information about this validator.
        
        Returns:
            Dictionary containing validator metadata, capabilities, etc.
        """
        pass
    
    def __str__(self) -> str:
        """String representation of the validator."""
        return f"{self.__class__.__name__}(name='{self.validator_name}')"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"{self.__class__.__name__}("
                f"name='{self.validator_name}', "
                f"validations={self.performance_metrics.total_validations}, "
                f"avg_confidence={self.performance_metrics.get_average_confidence():.3f})")


class ValidationError(Exception):
    """Exception raised when validation fails."""
    
    def __init__(self, message: str, validator_name: str = None, context: ValidationContext = None):
        self.message = message
        self.validator_name = validator_name
        self.context = context
        super().__init__(message)


class ValidationConfigError(Exception):
    """Exception raised when validator configuration is invalid."""
    
    def __init__(self, message: str, config_key: str = None):
        self.message = message
        self.config_key = config_key
        super().__init__(message)
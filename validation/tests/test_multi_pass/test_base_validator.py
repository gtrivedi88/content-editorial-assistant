"""
Comprehensive test suite for BasePassValidator class.
Tests abstract interface, decision tracking, performance monitoring, and common functionality.
"""

import unittest
import time
from unittest.mock import Mock, patch

from validation.multi_pass.base_validator import (
    BasePassValidator, ValidationDecision, ValidationConfidence,
    ValidationEvidence, ValidationResult, ValidationContext,
    ValidationPerformanceMetrics, ValidationError, ValidationConfigError
)
from validation.confidence.confidence_calculator import ConfidenceCalculator, ConfidenceBreakdown


class ConcreteTestValidator(BasePassValidator):
    """Concrete implementation of BasePassValidator for testing."""
    
    def __init__(self, validator_name: str = "test_validator", **kwargs):
        super().__init__(validator_name, **kwargs)
        self.validation_behavior = "accept"  # Control validation behavior for testing
        self.validation_delay = 0.0  # Simulate processing time
        
    def _validate_error(self, context: ValidationContext) -> ValidationResult:
        """Test implementation that can be controlled for testing."""
        if self.validation_delay > 0:
            time.sleep(self.validation_delay)
        
        # Simulate different validation behaviors based on test needs
        if self.validation_behavior == "accept":
            decision = ValidationDecision.ACCEPT
            confidence_score = 0.8
            evidence = [ValidationEvidence(
                evidence_type="test_evidence",
                confidence=0.8,
                description="Test evidence supporting acceptance",
                source_data={"test": True}
            )]
            reasoning = "Test validator accepts this error"
            
        elif self.validation_behavior == "reject":
            decision = ValidationDecision.REJECT
            confidence_score = 0.9
            evidence = [ValidationEvidence(
                evidence_type="test_evidence",
                confidence=0.9,
                description="Test evidence supporting rejection",
                source_data={"test": True}
            )]
            reasoning = "Test validator rejects this error"
            
        elif self.validation_behavior == "uncertain":
            decision = ValidationDecision.UNCERTAIN
            confidence_score = 0.3
            evidence = [ValidationEvidence(
                evidence_type="test_evidence",
                confidence=0.3,
                description="Test evidence is inconclusive",
                source_data={"test": True}
            )]
            reasoning = "Test validator is uncertain about this error"
            
        elif self.validation_behavior == "error":
            raise ValidationError("Test validation error", self.validator_name, context)
            
        else:
            raise ValueError(f"Unknown validation behavior: {self.validation_behavior}")
        
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
            metadata={"test_behavior": self.validation_behavior}
        )
    
    def get_validator_info(self) -> dict:
        """Test implementation of validator info."""
        return {
            "name": self.validator_name,
            "type": "test_validator",
            "version": "1.0.0",
            "capabilities": ["testing"],
            "description": "Test validator for unit testing BasePassValidator functionality"
        }


class TestValidationDataStructures(unittest.TestCase):
    """Test validation data structures and enums."""
    
    def test_validation_decision_enum(self):
        """Test ValidationDecision enum values."""
        self.assertEqual(ValidationDecision.ACCEPT.value, "accept")
        self.assertEqual(ValidationDecision.REJECT.value, "reject")
        self.assertEqual(ValidationDecision.UNCERTAIN.value, "uncertain")
    
    def test_validation_confidence_enum(self):
        """Test ValidationConfidence enum values."""
        self.assertEqual(ValidationConfidence.HIGH.value, "high")
        self.assertEqual(ValidationConfidence.MEDIUM.value, "medium")
        self.assertEqual(ValidationConfidence.LOW.value, "low")
    
    def test_validation_evidence_creation(self):
        """Test ValidationEvidence dataclass creation."""
        evidence = ValidationEvidence(
            evidence_type="morphological",
            confidence=0.8,
            description="POS tagging supports this decision",
            source_data={"pos_tag": "NOUN", "confidence": 0.8},
            weight=1.5
        )
        
        self.assertEqual(evidence.evidence_type, "morphological")
        self.assertEqual(evidence.confidence, 0.8)
        self.assertEqual(evidence.description, "POS tagging supports this decision")
        self.assertEqual(evidence.source_data["pos_tag"], "NOUN")
        self.assertEqual(evidence.weight, 1.5)
    
    def test_validation_evidence_default_weight(self):
        """Test ValidationEvidence default weight."""
        evidence = ValidationEvidence(
            evidence_type="test",
            confidence=0.5,
            description="Test evidence",
            source_data={}
        )
        
        self.assertEqual(evidence.weight, 1.0)
    
    def test_validation_result_creation(self):
        """Test ValidationResult dataclass creation."""
        evidence = [ValidationEvidence(
            evidence_type="test",
            confidence=0.8,
            description="Test evidence",
            source_data={}
        )]
        
        result = ValidationResult(
            validator_name="test_validator",
            decision=ValidationDecision.ACCEPT,
            confidence=ValidationConfidence.HIGH,
            confidence_score=0.85,
            evidence=evidence,
            reasoning="Test reasoning",
            error_text="test error",
            error_position=10,
            rule_type="grammar",
            rule_name="test_rule",
            validation_time=0.1,
            metadata={"test": True}
        )
        
        self.assertEqual(result.validator_name, "test_validator")
        self.assertEqual(result.decision, ValidationDecision.ACCEPT)
        self.assertEqual(result.confidence, ValidationConfidence.HIGH)
        self.assertEqual(result.confidence_score, 0.85)
        self.assertEqual(len(result.evidence), 1)
        self.assertEqual(result.reasoning, "Test reasoning")
        self.assertEqual(result.error_text, "test error")
        self.assertEqual(result.error_position, 10)
        self.assertEqual(result.rule_type, "grammar")
        self.assertEqual(result.rule_name, "test_rule")
        self.assertEqual(result.validation_time, 0.1)
        self.assertTrue(result.metadata["test"])
    
    def test_validation_result_is_decisive(self):
        """Test ValidationResult is_decisive method."""
        # Decisive result
        decisive_result = ValidationResult(
            validator_name="test",
            decision=ValidationDecision.ACCEPT,
            confidence=ValidationConfidence.HIGH,
            confidence_score=0.8,
            evidence=[],
            reasoning="test",
            error_text="test",
            error_position=0
        )
        
        self.assertTrue(decisive_result.is_decisive())
        self.assertTrue(decisive_result.is_decisive(min_confidence=0.7))
        self.assertFalse(decisive_result.is_decisive(min_confidence=0.9))
        
        # Non-decisive result (uncertain)
        uncertain_result = ValidationResult(
            validator_name="test",
            decision=ValidationDecision.UNCERTAIN,
            confidence=ValidationConfidence.HIGH,
            confidence_score=0.9,
            evidence=[],
            reasoning="test",
            error_text="test",
            error_position=0
        )
        
        self.assertFalse(uncertain_result.is_decisive())
        
        # Non-decisive result (low confidence)
        low_conf_result = ValidationResult(
            validator_name="test",
            decision=ValidationDecision.ACCEPT,
            confidence=ValidationConfidence.LOW,
            confidence_score=0.3,
            evidence=[],
            reasoning="test",
            error_text="test",
            error_position=0
        )
        
        self.assertFalse(low_conf_result.is_decisive())
    
    def test_validation_result_decision_strength(self):
        """Test ValidationResult get_decision_strength method."""
        # Strong decision
        strong_result = ValidationResult(
            validator_name="test",
            decision=ValidationDecision.ACCEPT,
            confidence=ValidationConfidence.HIGH,
            confidence_score=0.9,
            evidence=[],
            reasoning="test",
            error_text="test",
            error_position=0
        )
        
        self.assertEqual(strong_result.get_decision_strength(), 0.9)
        
        # Uncertain decision
        uncertain_result = ValidationResult(
            validator_name="test",
            decision=ValidationDecision.UNCERTAIN,
            confidence=ValidationConfidence.LOW,
            confidence_score=0.3,
            evidence=[],
            reasoning="test",
            error_text="test",
            error_position=0
        )
        
        self.assertEqual(uncertain_result.get_decision_strength(), 0.0)
    
    def test_validation_context_creation(self):
        """Test ValidationContext dataclass creation."""
        context = ValidationContext(
            text="This is a test sentence with an error.",
            error_position=25,
            error_text="error",
            rule_type="grammar",
            rule_name="test_rule",
            rule_severity="major",
            content_type="technical",
            domain="programming",
            additional_context={"test": True}
        )
        
        self.assertEqual(context.text, "This is a test sentence with an error.")
        self.assertEqual(context.error_position, 25)
        self.assertEqual(context.error_text, "error")
        self.assertEqual(context.rule_type, "grammar")
        self.assertEqual(context.rule_name, "test_rule")
        self.assertEqual(context.rule_severity, "major")
        self.assertEqual(context.content_type, "technical")
        self.assertEqual(context.domain, "programming")
        self.assertTrue(context.additional_context["test"])


class TestValidationPerformanceMetrics(unittest.TestCase):
    """Test ValidationPerformanceMetrics functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.metrics = ValidationPerformanceMetrics()
    
    def test_initial_metrics_state(self):
        """Test initial state of performance metrics."""
        self.assertEqual(self.metrics.total_validations, 0)
        self.assertEqual(len(self.metrics.validation_times), 0)
        self.assertEqual(self.metrics.decisions_made[ValidationDecision.ACCEPT], 0)
        self.assertEqual(self.metrics.decisions_made[ValidationDecision.REJECT], 0)
        self.assertEqual(self.metrics.decisions_made[ValidationDecision.UNCERTAIN], 0)
        self.assertEqual(len(self.metrics.confidence_scores), 0)
        self.assertEqual(self.metrics.validation_errors, 0)
    
    def test_add_validation_result(self):
        """Test adding validation results to metrics."""
        result = ValidationResult(
            validator_name="test",
            decision=ValidationDecision.ACCEPT,
            confidence=ValidationConfidence.HIGH,
            confidence_score=0.8,
            evidence=[],
            reasoning="test",
            error_text="test",
            error_position=0,
            validation_time=0.1
        )
        
        self.metrics.add_validation_result(result)
        
        self.assertEqual(self.metrics.total_validations, 1)
        self.assertEqual(len(self.metrics.validation_times), 1)
        self.assertEqual(self.metrics.validation_times[0], 0.1)
        self.assertEqual(self.metrics.decisions_made[ValidationDecision.ACCEPT], 1)
        self.assertEqual(len(self.metrics.confidence_scores), 1)
        self.assertEqual(self.metrics.confidence_scores[0], 0.8)
    
    def test_average_validation_time(self):
        """Test average validation time calculation."""
        # Empty metrics
        self.assertEqual(self.metrics.get_average_validation_time(), 0.0)
        
        # Add some results
        times = [0.1, 0.2, 0.3]
        for i, time_val in enumerate(times):
            result = ValidationResult(
                validator_name="test",
                decision=ValidationDecision.ACCEPT,
                confidence=ValidationConfidence.HIGH,
                confidence_score=0.8,
                evidence=[],
                reasoning="test",
                error_text="test",
                error_position=0,
                validation_time=time_val
            )
            self.metrics.add_validation_result(result)
        
        expected_avg = sum(times) / len(times)
        self.assertAlmostEqual(self.metrics.get_average_validation_time(), expected_avg, places=5)
    
    def test_average_confidence(self):
        """Test average confidence calculation."""
        # Empty metrics
        self.assertEqual(self.metrics.get_average_confidence(), 0.0)
        
        # Add some results
        confidences = [0.7, 0.8, 0.9]
        for i, conf in enumerate(confidences):
            result = ValidationResult(
                validator_name="test",
                decision=ValidationDecision.ACCEPT,
                confidence=ValidationConfidence.HIGH,
                confidence_score=conf,
                evidence=[],
                reasoning="test",
                error_text="test",
                error_position=0
            )
            self.metrics.add_validation_result(result)
        
        expected_avg = sum(confidences) / len(confidences)
        self.assertAlmostEqual(self.metrics.get_average_confidence(), expected_avg, places=5)
    
    def test_decision_rates(self):
        """Test decision rate calculations."""
        # Empty metrics
        self.assertEqual(self.metrics.get_decision_rate(ValidationDecision.ACCEPT), 0.0)
        
        # Add mixed results
        decisions = [
            ValidationDecision.ACCEPT,
            ValidationDecision.ACCEPT, 
            ValidationDecision.REJECT,
            ValidationDecision.UNCERTAIN
        ]
        
        for decision in decisions:
            result = ValidationResult(
                validator_name="test",
                decision=decision,
                confidence=ValidationConfidence.MEDIUM,
                confidence_score=0.6,
                evidence=[],
                reasoning="test",
                error_text="test",
                error_position=0
            )
            self.metrics.add_validation_result(result)
        
        self.assertAlmostEqual(self.metrics.get_decision_rate(ValidationDecision.ACCEPT), 0.5, places=5)
        self.assertAlmostEqual(self.metrics.get_decision_rate(ValidationDecision.REJECT), 0.25, places=5)
        self.assertAlmostEqual(self.metrics.get_decision_rate(ValidationDecision.UNCERTAIN), 0.25, places=5)
    
    def test_decisiveness_rate(self):
        """Test decisiveness rate calculation."""
        # Empty metrics
        self.assertEqual(self.metrics.get_decisiveness_rate(), 0.0)
        
        # Add results with varying confidence
        test_cases = [
            (ValidationDecision.ACCEPT, 0.8),     # Decisive
            (ValidationDecision.REJECT, 0.9),    # Decisive
            (ValidationDecision.ACCEPT, 0.5),    # Not decisive (low confidence)
            (ValidationDecision.UNCERTAIN, 0.8), # Not decisive (uncertain)
        ]
        
        for decision, confidence in test_cases:
            result = ValidationResult(
                validator_name="test",
                decision=decision,
                confidence=ValidationConfidence.MEDIUM,
                confidence_score=confidence,
                evidence=[],
                reasoning="test",
                error_text="test",
                error_position=0
            )
            self.metrics.add_validation_result(result)
        
        # Only first 2 should be decisive with threshold 0.7
        expected_rate = 2 / 4  # 2 decisive out of 4 total
        self.assertAlmostEqual(self.metrics.get_decisiveness_rate(0.7), expected_rate, places=5)


class TestBaseValidatorInitialization(unittest.TestCase):
    """Test BasePassValidator initialization and configuration."""
    
    def test_default_initialization(self):
        """Test initialization with default settings."""
        validator = ConcreteTestValidator("test_validator")
        
        self.assertEqual(validator.validator_name, "test_validator")
        self.assertIsInstance(validator.confidence_calculator, ConfidenceCalculator)
        self.assertTrue(validator.enable_performance_tracking)
        self.assertEqual(validator.min_confidence_threshold, 0.5)
        self.assertIsInstance(validator.performance_metrics, ValidationPerformanceMetrics)
        self.assertEqual(len(validator.config), 0)
        self.assertEqual(len(validator.validation_history), 0)
        self.assertEqual(validator.max_history_size, 1000)
    
    def test_custom_initialization(self):
        """Test initialization with custom settings."""
        custom_calculator = ConfidenceCalculator()
        
        validator = ConcreteTestValidator(
            "custom_validator",
            confidence_calculator=custom_calculator,
            enable_performance_tracking=False,
            min_confidence_threshold=0.8
        )
        
        self.assertEqual(validator.validator_name, "custom_validator")
        self.assertEqual(validator.confidence_calculator, custom_calculator)
        self.assertFalse(validator.enable_performance_tracking)
        self.assertEqual(validator.min_confidence_threshold, 0.8)
    
    def test_validator_info(self):
        """Test get_validator_info method."""
        validator = ConcreteTestValidator("info_test")
        info = validator.get_validator_info()
        
        self.assertIsInstance(info, dict)
        self.assertEqual(info["name"], "info_test")
        self.assertEqual(info["type"], "test_validator")
        self.assertIn("capabilities", info)
        self.assertIn("description", info)
    
    def test_string_representations(self):
        """Test string representations of validator."""
        validator = ConcreteTestValidator("string_test")
        
        str_repr = str(validator)
        self.assertIn("ConcreteTestValidator", str_repr)
        self.assertIn("string_test", str_repr)
        
        repr_str = repr(validator)
        self.assertIn("ConcreteTestValidator", repr_str)
        self.assertIn("string_test", repr_str)
        self.assertIn("validations=0", repr_str)


class TestValidationFunctionality(unittest.TestCase):
    """Test core validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ConcreteTestValidator("test_validator")
        self.context = ValidationContext(
            text="This is a test sentence with an error.",
            error_position=30,
            error_text="error",
            rule_type="grammar",
            rule_name="test_rule"
        )
    
    def test_successful_validation_accept(self):
        """Test successful validation with accept decision."""
        self.validator.validation_behavior = "accept"
        
        result = self.validator.validate_error(self.context)
        
        self.assertEqual(result.validator_name, "test_validator")
        self.assertEqual(result.decision, ValidationDecision.ACCEPT)
        self.assertEqual(result.confidence, ValidationConfidence.HIGH)
        self.assertEqual(result.confidence_score, 0.8)
        self.assertEqual(len(result.evidence), 1)
        self.assertEqual(result.evidence[0].evidence_type, "test_evidence")
        self.assertEqual(result.reasoning, "Test validator accepts this error")
        self.assertEqual(result.error_text, "error")
        self.assertEqual(result.error_position, 30)
        self.assertEqual(result.rule_type, "grammar")
        self.assertEqual(result.rule_name, "test_rule")
        self.assertGreater(result.validation_time, 0)
        self.assertEqual(result.metadata["test_behavior"], "accept")
    
    def test_successful_validation_reject(self):
        """Test successful validation with reject decision."""
        self.validator.validation_behavior = "reject"
        
        result = self.validator.validate_error(self.context)
        
        self.assertEqual(result.decision, ValidationDecision.REJECT)
        self.assertEqual(result.confidence, ValidationConfidence.HIGH)
        self.assertEqual(result.confidence_score, 0.9)
        self.assertEqual(result.reasoning, "Test validator rejects this error")
    
    def test_successful_validation_uncertain(self):
        """Test successful validation with uncertain decision."""
        self.validator.validation_behavior = "uncertain"
        
        result = self.validator.validate_error(self.context)
        
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertEqual(result.confidence, ValidationConfidence.LOW)
        self.assertEqual(result.confidence_score, 0.3)
        self.assertEqual(result.reasoning, "Test validator is uncertain about this error")
    
    def test_validation_error_handling(self):
        """Test validation error handling."""
        self.validator.validation_behavior = "error"
        
        result = self.validator.validate_error(self.context)
        
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertEqual(result.confidence, ValidationConfidence.LOW)
        self.assertEqual(result.confidence_score, 0.0)
        self.assertEqual(len(result.evidence), 1)
        self.assertEqual(result.evidence[0].evidence_type, "error")
        self.assertIn("Validation failed", result.reasoning)
        self.assertTrue(result.metadata["validation_error"])
        
        # Check that error was tracked
        self.assertEqual(self.validator.performance_metrics.validation_errors, 1)
    
    def test_validation_time_tracking(self):
        """Test validation time tracking."""
        self.validator.validation_delay = 0.01  # 10ms delay
        self.validator.validation_behavior = "accept"
        
        result = self.validator.validate_error(self.context)
        
        # Should have recorded some validation time
        self.assertGreater(result.validation_time, 0.005)  # At least 5ms
    
    def test_confidence_score_calculation(self):
        """Test confidence score calculation integration."""
        breakdown = self.validator.calculate_confidence_score(self.context)
        
        self.assertIsInstance(breakdown, ConfidenceBreakdown)
        self.assertEqual(breakdown.text, self.context.text)
        self.assertEqual(breakdown.error_position, self.context.error_position)
        self.assertEqual(breakdown.rule_type, self.context.rule_type)
    
    def test_confidence_level_conversion(self):
        """Test confidence score to level conversion."""
        high_level = self.validator._convert_confidence_to_level(0.9)
        medium_level = self.validator._convert_confidence_to_level(0.6)
        low_level = self.validator._convert_confidence_to_level(0.3)
        
        self.assertEqual(high_level, ValidationConfidence.HIGH)
        self.assertEqual(medium_level, ValidationConfidence.MEDIUM)
        self.assertEqual(low_level, ValidationConfidence.LOW)


class TestPerformanceTracking(unittest.TestCase):
    """Test performance tracking functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ConcreteTestValidator("perf_test")
        self.context = ValidationContext(
            text="Test sentence.",
            error_position=5,
            error_text="test",
            rule_type="grammar"
        )
    
    def test_performance_metrics_tracking(self):
        """Test that performance metrics are tracked correctly."""
        self.validator.validation_behavior = "accept"
        
        # Perform several validations
        for i in range(5):
            self.validator.validate_error(self.context)
        
        metrics = self.validator.get_performance_metrics()
        
        self.assertEqual(metrics.total_validations, 5)
        self.assertEqual(len(metrics.validation_times), 5)
        self.assertEqual(metrics.decisions_made[ValidationDecision.ACCEPT], 5)
        self.assertEqual(len(metrics.confidence_scores), 5)
        
        # All confidence scores should be 0.8 (from test behavior)
        for score in metrics.confidence_scores:
            self.assertEqual(score, 0.8)
    
    def test_performance_tracking_disabled(self):
        """Test performance tracking when disabled."""
        validator = ConcreteTestValidator(
            "no_perf_test",
            enable_performance_tracking=False
        )
        validator.validation_behavior = "accept"
        
        validator.validate_error(self.context)
        
        metrics = validator.get_performance_metrics()
        
        # Should not track metrics when disabled
        self.assertEqual(metrics.total_validations, 0)
        self.assertEqual(len(metrics.validation_times), 0)
        self.assertEqual(len(metrics.confidence_scores), 0)
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        self.validator.validation_behavior = "accept"
        
        # Perform validations
        for i in range(3):
            self.validator.validate_error(self.context)
        
        summary = self.validator.get_performance_summary()
        
        self.assertEqual(summary["validator_name"], "perf_test")
        self.assertEqual(summary["total_validations"], 3)
        self.assertGreater(summary["average_validation_time"], 0)
        self.assertAlmostEqual(summary["average_confidence"], 0.8, places=5)
        self.assertEqual(summary["decision_rates"]["accept_rate"], 1.0)
        self.assertEqual(summary["decision_rates"]["reject_rate"], 0.0)
        self.assertEqual(summary["decision_rates"]["uncertain_rate"], 0.0)
        self.assertGreater(summary["decisiveness_rate"], 0.5)  # Should be decisive
        self.assertEqual(summary["validation_errors"], 0)
    
    def test_clear_performance_metrics(self):
        """Test clearing performance metrics."""
        self.validator.validation_behavior = "accept"
        
        # Perform validation
        self.validator.validate_error(self.context)
        
        # Verify metrics exist
        self.assertEqual(self.validator.performance_metrics.total_validations, 1)
        self.assertEqual(len(self.validator.validation_history), 1)
        
        # Clear metrics
        self.validator.clear_performance_metrics()
        
        # Verify metrics are cleared
        self.assertEqual(self.validator.performance_metrics.total_validations, 0)
        self.assertEqual(len(self.validator.validation_history), 0)


class TestConfigurationManagement(unittest.TestCase):
    """Test configuration management functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ConcreteTestValidator("config_test")
    
    def test_set_config(self):
        """Test setting configuration."""
        config = {
            "min_confidence_threshold": 0.8,
            "max_history_size": 500,
            "custom_setting": "test_value"
        }
        
        self.validator.set_config(config)
        
        self.assertEqual(self.validator.min_confidence_threshold, 0.8)
        self.assertEqual(self.validator.max_history_size, 500)
        self.assertEqual(self.validator.config["custom_setting"], "test_value")
    
    def test_config_history_trimming(self):
        """Test that history is trimmed when max_history_size is reduced."""
        # Fill history beyond new limit
        for i in range(10):
            result = ValidationResult(
                validator_name="test",
                decision=ValidationDecision.ACCEPT,
                confidence=ValidationConfidence.HIGH,
                confidence_score=0.8,
                evidence=[],
                reasoning="test",
                error_text="test",
                error_position=0
            )
            self.validator._add_to_history(result)
        
        self.assertEqual(len(self.validator.validation_history), 10)
        
        # Set smaller history size
        self.validator.set_config({"max_history_size": 5})
        
        # History should be trimmed
        self.assertEqual(len(self.validator.validation_history), 5)
        self.assertEqual(self.validator.max_history_size, 5)


class TestValidationHistory(unittest.TestCase):
    """Test validation history management."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ConcreteTestValidator("history_test")
        self.validator.max_history_size = 5  # Small for testing
        self.context = ValidationContext(
            text="Test sentence.",
            error_position=5,
            error_text="test"
        )
    
    def test_history_tracking(self):
        """Test that validation history is tracked correctly."""
        self.validator.validation_behavior = "accept"
        
        # Perform validations
        for i in range(3):
            self.validator.validate_error(self.context)
        
        history = self.validator.validation_history
        self.assertEqual(len(history), 3)
        
        for result in history:
            self.assertEqual(result.decision, ValidationDecision.ACCEPT)
            self.assertEqual(result.validator_name, "history_test")
    
    def test_history_size_limit(self):
        """Test that history respects size limit."""
        self.validator.validation_behavior = "accept"
        
        # Perform more validations than history limit
        for i in range(10):
            self.validator.validate_error(self.context)
        
        # History should be limited to max_history_size
        self.assertEqual(len(self.validator.validation_history), 5)
    
    def test_get_recent_validations(self):
        """Test getting recent validation results."""
        self.validator.validation_behavior = "accept"
        
        # Perform validations
        for i in range(8):
            self.validator.validate_error(self.context)
        
        # Get recent validations (should return last 3 due to history limit)
        recent = self.validator.get_recent_validations(3)
        self.assertEqual(len(recent), 3)
        
        # All should be from the same validator
        for result in recent:
            self.assertEqual(result.validator_name, "history_test")
    
    def test_validation_statistics(self):
        """Test validation statistics generation."""
        # Perform mix of validations
        behaviors = ["accept", "reject", "uncertain"]
        for behavior in behaviors:
            self.validator.validation_behavior = behavior
            self.validator.validate_error(self.context)
        
        stats = self.validator.get_validation_statistics()
        
        self.assertEqual(stats["validator_name"], "history_test")
        self.assertEqual(stats["total_validations"], 3)
        self.assertEqual(stats["recent_validations_analyzed"], 3)
        
        # Should have decision patterns for each behavior
        decision_patterns = stats["decision_patterns"]
        self.assertIn("accept", decision_patterns)
        self.assertIn("reject", decision_patterns)
        self.assertIn("uncertain", decision_patterns)
        
        # Should have confidence level distribution
        self.assertIn("confidence_level_distribution", stats)
        
        # Should have evidence type patterns
        self.assertIn("evidence_type_patterns", stats)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ConcreteTestValidator("error_test")
    
    def test_validation_error_exception(self):
        """Test ValidationError exception."""
        context = ValidationContext(
            text="Test",
            error_position=0,
            error_text="test"
        )
        
        error = ValidationError("Test validation failed", "test_validator", context)
        
        self.assertEqual(error.message, "Test validation failed")
        self.assertEqual(error.validator_name, "test_validator")
        self.assertEqual(error.context, context)
        self.assertEqual(str(error), "Test validation failed")
    
    def test_validation_config_error_exception(self):
        """Test ValidationConfigError exception."""
        error = ValidationConfigError("Invalid config value", "test_key")
        
        self.assertEqual(error.message, "Invalid config value")
        self.assertEqual(error.config_key, "test_key")
        self.assertEqual(str(error), "Invalid config value")
    
    def test_empty_validation_statistics(self):
        """Test validation statistics with no history."""
        stats = self.validator.get_validation_statistics()
        
        self.assertEqual(stats["message"], "No validation history available")


if __name__ == '__main__':
    unittest.main(verbosity=2)
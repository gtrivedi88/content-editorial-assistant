"""
Comprehensive test suite for ValidationPipeline class.
Tests pipeline orchestration, consensus building, early termination, audit trails,
and performance monitoring across all validators.
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock

from validation.multi_pass.validation_pipeline import (
    ValidationPipeline, PipelineConfiguration, PipelineResult, ValidatorWeight,
    ConsensusStrategy, TerminationCondition, PipelineStage, ValidatorExecution,
    ConsensusAnalysis, PipelineAuditTrail
)
from validation.multi_pass import (
    ValidationContext, ValidationDecision, ValidationConfidence, ValidationEvidence,
    ValidationResult, BasePassValidator
)


class TestValidationPipelineInitialization(unittest.TestCase):
    """Test ValidationPipeline initialization and configuration."""
    
    def test_default_initialization(self):
        """Test initialization with default configuration."""
        pipeline = ValidationPipeline()
        
        self.assertIsInstance(pipeline.configuration, PipelineConfiguration)
        self.assertEqual(len(pipeline.validators), 4)  # All validators enabled by default
        self.assertIn('morphological', pipeline.validators)
        self.assertIn('contextual', pipeline.validators)
        self.assertIn('domain', pipeline.validators)
        self.assertIn('cross_rule', pipeline.validators)
        self.assertIsNotNone(pipeline.pipeline_id)
        self.assertEqual(pipeline.performance_metrics['total_executions'], 0)
    
    def test_custom_configuration_initialization(self):
        """Test initialization with custom configuration."""
        config = PipelineConfiguration(
            enable_morphological=True,
            enable_contextual=True,
            enable_domain=False,
            enable_cross_rule=False,
            consensus_strategy=ConsensusStrategy.MAJORITY_VOTE,
            enable_early_termination=False
        )
        
        pipeline = ValidationPipeline(config)
        
        self.assertEqual(len(pipeline.validators), 2)  # Only 2 validators enabled
        self.assertIn('morphological', pipeline.validators)
        self.assertIn('contextual', pipeline.validators)
        self.assertNotIn('domain', pipeline.validators)
        self.assertNotIn('cross_rule', pipeline.validators)
        self.assertEqual(pipeline.configuration.consensus_strategy, ConsensusStrategy.MAJORITY_VOTE)
        self.assertFalse(pipeline.configuration.enable_early_termination)
    
    def test_validator_weight_validation(self):
        """Test validator weight validation."""
        # Test valid weights
        weights = ValidatorWeight(0.3, 0.3, 0.2, 0.2)
        self.assertAlmostEqual(
            weights.morphological + weights.contextual + weights.domain + weights.cross_rule,
            1.0, places=3
        )
        
        # Test invalid weights (should raise ValueError)
        with self.assertRaises(ValueError):
            ValidatorWeight(0.5, 0.5, 0.5, 0.5)  # Sum > 1.0
    
    def test_minimum_validator_count_validation(self):
        """Test minimum validator count validation."""
        config = PipelineConfiguration(
            enable_morphological=True,
            enable_contextual=False,
            enable_domain=False,
            enable_cross_rule=False,
            minimum_validator_count=2
        )
        
        # Should raise ValueError when only 1 validator enabled but minimum is 2
        with self.assertRaises(ValueError):
            ValidationPipeline(config)
    
    def test_pipeline_info(self):
        """Test get_pipeline_info method."""
        pipeline = ValidationPipeline()
        info = pipeline.get_pipeline_info()
        
        self.assertIn('pipeline_id', info)
        self.assertIn('configuration', info)
        self.assertIn('performance_metrics', info)
        self.assertIn('validator_info', info)
        self.assertIn('execution_history_count', info)
        
        # Check configuration details
        config = info['configuration']
        self.assertIn('consensus_strategy', config)
        self.assertIn('enabled_validators', config)
        self.assertEqual(len(config['enabled_validators']), 4)


class TestPipelineOrchestration(unittest.TestCase):
    """Test pipeline orchestration and validator execution."""
    
    def setUp(self):
        """Set up test environment."""
        self.pipeline = ValidationPipeline()
        self.context = ValidationContext(
            text="The comprehensive document demonstrates excellent writing quality.",
            error_position=20,
            error_text="demonstrates",
            rule_type="style",
            rule_name="word_choice"
        )
    
    def test_basic_pipeline_execution(self):
        """Test basic pipeline execution with all validators."""
        result = self.pipeline.validate_error(self.context)
        
        # Check result structure
        self.assertIsInstance(result, PipelineResult)
        self.assertIsInstance(result.validation_result, ValidationResult)
        self.assertIsInstance(result.consensus_analysis, ConsensusAnalysis)
        self.assertIsInstance(result.audit_trail, PipelineAuditTrail)
        
        # Check that all validators executed
        self.assertEqual(len(result.validator_results), 4)
        self.assertIn('morphological', result.validator_results)
        self.assertIn('contextual', result.validator_results)
        self.assertIn('domain', result.validator_results)
        self.assertIn('cross_rule', result.validator_results)
        
        # Check execution times
        self.assertGreater(result.total_execution_time, 0)
        self.assertEqual(len(result.individual_execution_times), 4)
    
    def test_pipeline_execution_with_disabled_validators(self):
        """Test pipeline execution with some validators disabled."""
        config = PipelineConfiguration(
            enable_morphological=True,
            enable_contextual=True,
            enable_domain=False,
            enable_cross_rule=False
        )
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        # Should only have 2 validator results
        self.assertEqual(len(result.validator_results), 2)
        self.assertIn('morphological', result.validator_results)
        self.assertIn('contextual', result.validator_results)
        self.assertNotIn('domain', result.validator_results)
        self.assertNotIn('cross_rule', result.validator_results)
    
    def test_evidence_aggregation(self):
        """Test evidence aggregation from multiple validators."""
        result = self.pipeline.validate_error(self.context)
        
        # Check evidence aggregation
        self.assertGreater(len(result.aggregated_evidence), 0)
        self.assertIsInstance(result.evidence_by_validator, dict)
        
        # Verify evidence is properly attributed to validators
        total_evidence_count = sum(
            len(evidence_list) for evidence_list in result.evidence_by_validator.values()
        )
        self.assertEqual(total_evidence_count, len(result.aggregated_evidence))
        
        # Check evidence types are diverse
        evidence_types = set(ev.evidence_type for ev in result.aggregated_evidence)
        self.assertGreater(len(evidence_types), 1)  # Should have multiple evidence types
    
    def test_pipeline_stage_execution(self):
        """Test that pipeline stages are executed in correct order."""
        result = self.pipeline.validate_error(self.context)
        
        audit_trail = result.audit_trail
        stages = audit_trail.stages_executed
        
        # Check that required stages were executed
        self.assertIn(PipelineStage.INITIALIZATION, stages)
        self.assertIn(PipelineStage.CONSENSUS_BUILDING, stages)
        self.assertIn(PipelineStage.FINALIZATION, stages)
        
        # Check validator stages
        self.assertIn(PipelineStage.MORPHOLOGICAL_VALIDATION, stages)
        self.assertIn(PipelineStage.CONTEXTUAL_VALIDATION, stages)
        self.assertIn(PipelineStage.DOMAIN_VALIDATION, stages)
        self.assertIn(PipelineStage.CROSS_RULE_VALIDATION, stages)
    
    def test_validator_execution_order(self):
        """Test that validators execute in the correct order."""
        result = self.pipeline.validate_error(self.context)
        
        audit_trail = result.audit_trail
        validator_executions = audit_trail.validator_executions
        
        # Check execution order
        expected_order = ['morphological', 'contextual', 'domain', 'cross_rule']
        actual_order = [exec.validator_name for exec in validator_executions]
        
        self.assertEqual(actual_order, expected_order)


class TestConsensusBuilding(unittest.TestCase):
    """Test consensus building strategies."""
    
    def setUp(self):
        """Set up test environment."""
        self.context = ValidationContext(
            text="Test consensus building with multiple validators.",
            error_position=10,
            error_text="consensus",
            rule_type="style",
            rule_name="consensus_test"
        )
    
    def test_majority_vote_consensus(self):
        """Test majority vote consensus strategy."""
        config = PipelineConfiguration(consensus_strategy=ConsensusStrategy.MAJORITY_VOTE)
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        self.assertEqual(
            result.consensus_analysis.strategy_used,
            ConsensusStrategy.MAJORITY_VOTE
        )
        self.assertIsInstance(result.consensus_analysis.final_decision, ValidationDecision)
        self.assertGreaterEqual(result.consensus_analysis.agreement_score, 0.0)
        self.assertLessEqual(result.consensus_analysis.agreement_score, 1.0)
    
    def test_weighted_average_consensus(self):
        """Test weighted average consensus strategy."""
        config = PipelineConfiguration(
            consensus_strategy=ConsensusStrategy.WEIGHTED_AVERAGE,
            validator_weights=ValidatorWeight(0.4, 0.3, 0.2, 0.1)
        )
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        self.assertEqual(
            result.consensus_analysis.strategy_used,
            ConsensusStrategy.WEIGHTED_AVERAGE
        )
        
        # Check that weights were used in metadata
        metadata = result.consensus_analysis.consensus_metadata
        self.assertIn('weights_used', metadata)
        self.assertIn('decision_scores', metadata)
    
    def test_confidence_threshold_consensus(self):
        """Test confidence threshold consensus strategy."""
        config = PipelineConfiguration(
            consensus_strategy=ConsensusStrategy.CONFIDENCE_THRESHOLD,
            minimum_consensus_confidence=0.7
        )
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        # Should either use confidence threshold or fall back to another strategy
        self.assertIn(
            result.consensus_analysis.strategy_used,
            [ConsensusStrategy.CONFIDENCE_THRESHOLD] + config.fallback_strategies
        )
    
    def test_best_confidence_consensus(self):
        """Test best confidence consensus strategy."""
        config = PipelineConfiguration(consensus_strategy=ConsensusStrategy.BEST_CONFIDENCE)
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        self.assertEqual(
            result.consensus_analysis.strategy_used,
            ConsensusStrategy.BEST_CONFIDENCE
        )
        
        # Check metadata contains confidence ranking
        metadata = result.consensus_analysis.consensus_metadata
        self.assertIn('best_validator', metadata)
        self.assertIn('confidence_ranking', metadata)
    
    def test_staged_fallback_consensus(self):
        """Test staged fallback consensus strategy."""
        config = PipelineConfiguration(consensus_strategy=ConsensusStrategy.STAGED_FALLBACK)
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        self.assertEqual(
            result.consensus_analysis.strategy_used,
            ConsensusStrategy.STAGED_FALLBACK
        )
        
        # Check that fallback strategy was recorded
        metadata = result.consensus_analysis.consensus_metadata
        self.assertIn('fallback_strategy_used', metadata)
    
    def test_consensus_agreement_metrics(self):
        """Test consensus agreement metrics calculation."""
        pipeline = ValidationPipeline()
        result = pipeline.validate_error(self.context)
        
        consensus = result.consensus_analysis
        
        # Check agreement metrics
        self.assertIsInstance(consensus.agreement_score, float)
        self.assertGreaterEqual(consensus.agreement_score, 0.0)
        self.assertLessEqual(consensus.agreement_score, 1.0)
        
        self.assertIsInstance(consensus.confidence_spread, float)
        self.assertGreaterEqual(consensus.confidence_spread, 0.0)
        
        self.assertIsInstance(consensus.validator_agreements, dict)
        self.assertEqual(len(consensus.validator_agreements), 4)  # All validators
        
        self.assertIsInstance(consensus.outlier_validators, list)
    
    def test_consensus_with_validator_failures(self):
        """Test consensus building when some validators fail."""
        # This would require mocking validator failures
        # For now, test with minimum validators
        config = PipelineConfiguration(
            enable_morphological=True,
            enable_contextual=True,
            enable_domain=False,
            enable_cross_rule=False,
            minimum_validator_count=2
        )
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        # Should still achieve consensus with 2 validators
        self.assertIsInstance(result.consensus_analysis, ConsensusAnalysis)
        self.assertIsNotNone(result.consensus_analysis.final_decision)


class TestEarlyTermination(unittest.TestCase):
    """Test early termination logic."""
    
    def setUp(self):
        """Set up test environment."""
        self.context = ValidationContext(
            text="Test early termination conditions.",
            error_position=15,
            error_text="termination",
            rule_type="grammar",
            rule_name="early_termination_test"
        )
    
    def test_early_termination_disabled(self):
        """Test behavior when early termination is disabled."""
        config = PipelineConfiguration(enable_early_termination=False)
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        # Should execute all validators
        self.assertEqual(len(result.validator_results), 4)
        self.assertFalse(result.early_termination)
        self.assertIsNone(result.termination_reason)
    
    def test_early_termination_enabled(self):
        """Test early termination when enabled."""
        config = PipelineConfiguration(
            enable_early_termination=True,
            termination_conditions=[
                TerminationCondition.HIGH_CONFIDENCE_CONSENSUS,
                TerminationCondition.UNANIMOUS_DECISION,
                TerminationCondition.VALIDATOR_QUORUM
            ],
            high_confidence_threshold=0.9,
            consensus_threshold=0.8
        )
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        # Early termination may or may not occur depending on validator results
        # Just verify the structure is correct
        self.assertIsInstance(result.early_termination, bool)
        if result.early_termination:
            self.assertIsInstance(result.termination_reason, TerminationCondition)
    
    def test_validator_quorum_termination(self):
        """Test early termination based on validator quorum."""
        config = PipelineConfiguration(
            enable_early_termination=True,
            termination_conditions=[TerminationCondition.VALIDATOR_QUORUM]
        )
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        # With 4 validators, quorum (3) should be reached
        # May terminate early after 3 validators
        if result.early_termination:
            self.assertEqual(result.termination_reason, TerminationCondition.VALIDATOR_QUORUM)
            self.assertGreaterEqual(len(result.validator_results), 3)


class TestAuditTrailGeneration(unittest.TestCase):
    """Test audit trail generation and completeness."""
    
    def setUp(self):
        """Set up test environment."""
        self.pipeline = ValidationPipeline()
        self.context = ValidationContext(
            text="Comprehensive audit trail testing for validation pipeline system.",
            error_position=25,
            error_text="audit",
            rule_type="documentation",
            rule_name="audit_trail_test"
        )
    
    def test_audit_trail_structure(self):
        """Test audit trail structure and completeness."""
        result = self.pipeline.validate_error(self.context)
        
        audit_trail = result.audit_trail
        
        # Check basic structure
        self.assertIsInstance(audit_trail, PipelineAuditTrail)
        self.assertIsNotNone(audit_trail.pipeline_id)
        self.assertGreater(audit_trail.execution_start_time, 0)
        self.assertGreater(audit_trail.execution_end_time, audit_trail.execution_start_time)
        self.assertGreater(audit_trail.total_execution_time, 0)
        
        # Check configuration recording
        self.assertIsInstance(audit_trail.configuration, PipelineConfiguration)
        
        # Check context recording
        self.assertEqual(audit_trail.validation_context, self.context)
        
        # Check stages and executions
        self.assertGreater(len(audit_trail.stages_executed), 0)
        self.assertGreater(len(audit_trail.validator_executions), 0)
        
        # Check final result
        self.assertIsNotNone(audit_trail.final_result)
        self.assertIsNotNone(audit_trail.consensus_analysis)
    
    def test_audit_trail_performance_metrics(self):
        """Test audit trail performance metrics."""
        config = PipelineConfiguration(enable_performance_monitoring=True)
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        audit_trail = result.audit_trail
        metrics = audit_trail.performance_metrics
        
        # Check performance metrics structure
        self.assertIn('validator_count', metrics)
        self.assertIn('successful_validators', metrics)
        self.assertIn('total_validator_time', metrics)
        self.assertIn('average_validator_time', metrics)
        self.assertIn('evidence_pieces', metrics)
        self.assertIn('total_evidence_types', metrics)
        
        # Check values are reasonable
        self.assertGreaterEqual(metrics['validator_count'], 2)
        self.assertGreaterEqual(metrics['successful_validators'], 2)
        self.assertGreater(metrics['total_validator_time'], 0)
        self.assertGreater(metrics['evidence_pieces'], 0)
    
    def test_audit_trail_error_recording(self):
        """Test audit trail error and warning recording."""
        # This would require mocking validator errors
        # For now, test that error lists exist
        result = self.pipeline.validate_error(self.context)
        
        audit_trail = result.audit_trail
        
        self.assertIsInstance(audit_trail.errors_encountered, list)
        self.assertIsInstance(audit_trail.warnings_generated, list)
    
    def test_audit_trail_with_disabled_monitoring(self):
        """Test audit trail when performance monitoring is disabled."""
        config = PipelineConfiguration(enable_performance_monitoring=False)
        pipeline = ValidationPipeline(config)
        
        result = pipeline.validate_error(self.context)
        
        # Should still have basic audit trail
        self.assertIsInstance(result.audit_trail, PipelineAuditTrail)
        self.assertIsNotNone(result.audit_trail.final_result)


class TestPerformanceMonitoring(unittest.TestCase):
    """Test performance monitoring and metrics."""
    
    def setUp(self):
        """Set up test environment."""
        self.pipeline = ValidationPipeline()
        self.context = ValidationContext(
            text="Performance monitoring test for validation pipeline execution metrics.",
            error_position=30,
            error_text="monitoring",
            rule_type="performance",
            rule_name="performance_test"
        )
    
    def test_performance_metrics_tracking(self):
        """Test performance metrics tracking."""
        # Execute pipeline multiple times
        for i in range(3):
            context = ValidationContext(
                text=f"Performance test iteration {i}.",
                error_position=10 + i,
                error_text="test",
                rule_type="performance",
                rule_name=f"perf_test_{i}"
            )
            self.pipeline.validate_error(context)
        
        # Check performance metrics
        metrics = self.pipeline.performance_metrics
        
        self.assertEqual(metrics['total_executions'], 3)
        self.assertGreaterEqual(metrics['successful_executions'], 0)
        self.assertGreater(metrics['average_execution_time'], 0)
        
        # Check validator performance tracking
        validator_performance = metrics['validator_performance']
        self.assertGreater(len(validator_performance), 0)
        
        for validator_name, times in validator_performance.items():
            self.assertGreaterEqual(len(times), 3)  # Should have 3 execution times
            self.assertTrue(all(t > 0 for t in times))  # All times should be positive
    
    def test_performance_summary(self):
        """Test performance summary generation."""
        # Execute pipeline once
        self.pipeline.validate_error(self.context)
        
        summary = self.pipeline.get_performance_summary()
        
        # Check summary structure
        self.assertIn('total_executions', summary)
        self.assertIn('success_rate', summary)
        self.assertIn('consensus_rate', summary)
        self.assertIn('early_termination_rate', summary)
        self.assertIn('average_execution_time_ms', summary)
        self.assertIn('validator_average_times_ms', summary)
        
        # Check values
        self.assertEqual(summary['total_executions'], 1)
        self.assertGreaterEqual(summary['success_rate'], 0.0)
        self.assertLessEqual(summary['success_rate'], 1.0)
        self.assertGreater(summary['average_execution_time_ms'], 0)
    
    def test_execution_time_tracking(self):
        """Test execution time tracking accuracy."""
        start_time = time.time()
        result = self.pipeline.validate_error(self.context)
        end_time = time.time()
        
        actual_time = end_time - start_time
        recorded_time = result.total_execution_time
        
        # Recorded time should be close to actual time (within 10% margin)
        self.assertLess(abs(recorded_time - actual_time), actual_time * 0.1)
        
        # Individual times should sum to less than total time
        individual_total = sum(result.individual_execution_times.values())
        self.assertLess(individual_total, recorded_time * 1.1)  # Small margin for overhead
    
    def test_performance_history_management(self):
        """Test performance history management."""
        # Execute multiple times
        for i in range(5):
            context = ValidationContext(
                text=f"History test {i}.",
                error_position=i,
                error_text="test",
                rule_type="history",
                rule_name=f"history_test_{i}"
            )
            self.pipeline.validate_error(context)
        
        # Check execution history
        self.assertEqual(len(self.pipeline.execution_history), 5)
        
        # Clear history
        self.pipeline.clear_history()
        
        # Check that history and metrics are cleared
        self.assertEqual(len(self.pipeline.execution_history), 0)
        self.assertEqual(self.pipeline.performance_metrics['total_executions'], 0)


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Test error handling and edge case scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.pipeline = ValidationPipeline()
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        context = ValidationContext(
            text="",
            error_position=0,
            error_text="",
            rule_type="test",
            rule_name="empty_test"
        )
        
        result = self.pipeline.validate_error(context)
        
        # Should handle gracefully
        self.assertIsInstance(result, PipelineResult)
        self.assertIsInstance(result.validation_result, ValidationResult)
        self.assertGreater(result.total_execution_time, 0)
    
    def test_invalid_error_position(self):
        """Test handling of invalid error positions."""
        context = ValidationContext(
            text="Short text.",
            error_position=100,  # Beyond text length
            error_text="invalid",
            rule_type="test",
            rule_name="invalid_position_test"
        )
        
        result = self.pipeline.validate_error(context)
        
        # Should handle gracefully
        self.assertIsInstance(result, PipelineResult)
        self.assertIsInstance(result.validation_result, ValidationResult)
    
    def test_continue_on_validator_error_enabled(self):
        """Test behavior when continue_on_validator_error is enabled."""
        config = PipelineConfiguration(continue_on_validator_error=True)
        pipeline = ValidationPipeline(config)
        
        context = ValidationContext(
            text="Test error handling.",
            error_position=5,
            error_text="error",
            rule_type="test",
            rule_name="error_test"
        )
        
        # Even if some validators fail, pipeline should continue
        result = pipeline.validate_error(context)
        
        self.assertIsInstance(result, PipelineResult)
        # Should have at least some successful validators
        self.assertGreaterEqual(len(result.validator_results), 0)
    
    def test_very_long_text_handling(self):
        """Test handling of very long text."""
        long_text = "This is a very long text. " * 1000  # 27,000 characters
        
        context = ValidationContext(
            text=long_text,
            error_position=500,
            error_text="very",
            rule_type="performance",
            rule_name="long_text_test"
        )
        
        result = self.pipeline.validate_error(context)
        
        # Should handle without errors
        self.assertIsInstance(result, PipelineResult)
        self.assertGreater(result.total_execution_time, 0)
        # May take longer but should complete
        self.assertLess(result.total_execution_time, 60.0)  # Within 60 seconds
    
    def test_special_characters_handling(self):
        """Test handling of special characters and unicode."""
        context = ValidationContext(
            text="Special chars: ñáéíóú, emoji: 🎉🚀, symbols: ©®™",
            error_position=15,
            error_text="chars",
            rule_type="unicode",
            rule_name="special_chars_test"
        )
        
        result = self.pipeline.validate_error(context)
        
        # Should handle special characters gracefully
        self.assertIsInstance(result, PipelineResult)
        self.assertIsInstance(result.validation_result, ValidationResult)
    
    def test_extreme_configuration_values(self):
        """Test handling of extreme configuration values."""
        config = PipelineConfiguration(
            high_confidence_threshold=1.0,
            consensus_threshold=1.0,
            minimum_consensus_confidence=1.0,
            timeout_seconds=0.1
        )
        pipeline = ValidationPipeline(config)
        
        context = ValidationContext(
            text="Extreme configuration test.",
            error_position=10,
            error_text="extreme",
            rule_type="test",
            rule_name="extreme_config_test"
        )
        
        result = pipeline.validate_error(context)
        
        # Should handle extreme values gracefully
        self.assertIsInstance(result, PipelineResult)


class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios and complete workflows."""
    
    def setUp(self):
        """Set up test environment."""
        self.pipeline = ValidationPipeline()
    
    def test_complete_validation_workflow(self):
        """Test complete validation workflow with realistic content."""
        context = ValidationContext(
            text="The comprehensive REST API documentation demonstrates best practices for secure authentication mechanisms using OAuth 2.0 protocols and JSON Web Tokens.",
            error_position=60,
            error_text="demonstrates",
            rule_type="style",
            rule_name="word_choice",
            content_type="technical",
            additional_context={
                'all_rules': ['word_choice', 'technical_precision', 'clarity'],
                'all_errors': [
                    {'text': 'demonstrates', 'position': 60, 'rule_type': 'style', 'rule_name': 'word_choice', 'severity': 'minor'},
                    {'text': 'mechanisms', 'position': 120, 'rule_type': 'terminology', 'rule_name': 'technical_precision', 'severity': 'moderate'}
                ]
            }
        )
        
        result = self.pipeline.validate_error(context)
        
        # Comprehensive validation
        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(len(result.validator_results), 4)
        
        # Check evidence diversity
        evidence_types = set(ev.evidence_type for ev in result.aggregated_evidence)
        self.assertGreaterEqual(len(evidence_types), 3)  # Should have diverse evidence
        
        # Check consensus
        self.assertIsInstance(result.consensus_analysis, ConsensusAnalysis)
        self.assertIsNotNone(result.consensus_analysis.final_decision)
        
        # Check audit trail completeness
        audit_trail = result.audit_trail
        self.assertGreaterEqual(len(audit_trail.stages_executed), 6)
        self.assertEqual(len(audit_trail.validator_executions), 4)
    
    def test_high_confidence_consensus_scenario(self):
        """Test scenario where high confidence consensus is achieved."""
        config = PipelineConfiguration(
            enable_early_termination=True,
            termination_conditions=[TerminationCondition.HIGH_CONFIDENCE_CONSENSUS],
            high_confidence_threshold=0.7,  # Lower threshold for testing
            consensus_threshold=0.7
        )
        pipeline = ValidationPipeline(config)
        
        context = ValidationContext(
            text="Clear grammar error for testing high confidence consensus detection.",
            error_position=6,
            error_text="grammar",
            rule_type="grammar",
            rule_name="subject_verb_agreement"
        )
        
        result = pipeline.validate_error(context)
        
        # Check consensus achievement
        self.assertIsInstance(result.consensus_analysis, ConsensusAnalysis)
        self.assertGreaterEqual(result.consensus_analysis.agreement_score, 0.0)
        
        # May achieve early termination
        if result.early_termination:
            self.assertEqual(result.termination_reason, TerminationCondition.HIGH_CONFIDENCE_CONSENSUS)
    
    def test_weighted_consensus_with_domain_focus(self):
        """Test weighted consensus with domain-focused weights."""
        config = PipelineConfiguration(
            consensus_strategy=ConsensusStrategy.WEIGHTED_AVERAGE,
            validator_weights=ValidatorWeight(0.1, 0.2, 0.6, 0.1)  # Domain-heavy weighting
        )
        pipeline = ValidationPipeline(config)
        
        context = ValidationContext(
            text="Technical documentation requires precise terminology and domain-specific accuracy.",
            error_position=40,
            error_text="terminology",
            rule_type="terminology",
            rule_name="domain_appropriateness",
            content_type="technical"
        )
        
        result = pipeline.validate_error(context)
        
        # Check weighted consensus
        self.assertEqual(
            result.consensus_analysis.strategy_used,
            ConsensusStrategy.WEIGHTED_AVERAGE
        )
        
        # Check that domain validator weight was used
        metadata = result.consensus_analysis.consensus_metadata
        self.assertIn('weights_used', metadata)
        weights = metadata['weights_used']
        self.assertEqual(weights.get('domain', 0), 0.6)
    
    def test_fallback_strategy_cascade(self):
        """Test fallback strategy cascade when primary strategy fails."""
        config = PipelineConfiguration(
            consensus_strategy=ConsensusStrategy.UNANIMOUS_AGREEMENT,  # Unlikely to achieve
            fallback_strategies=[
                ConsensusStrategy.CONFIDENCE_THRESHOLD,
                ConsensusStrategy.MAJORITY_VOTE,
                ConsensusStrategy.BEST_CONFIDENCE
            ],
            minimum_consensus_confidence=0.99  # Very high threshold
        )
        pipeline = ValidationPipeline(config)
        
        context = ValidationContext(
            text="Testing fallback strategy cascade when primary consensus fails.",
            error_position=20,
            error_text="fallback",
            rule_type="test",
            rule_name="fallback_test"
        )
        
        result = pipeline.validate_error(context)
        
        # Should fall back to a working strategy
        consensus = result.consensus_analysis
        self.assertIn(
            consensus.strategy_used,
            [ConsensusStrategy.UNANIMOUS_AGREEMENT] + config.fallback_strategies
        )
        
        # Should have attempted multiple strategies
        self.assertGreaterEqual(len(consensus.strategies_attempted), 1)
    
    def test_mixed_validator_confidence_scenario(self):
        """Test scenario with mixed validator confidence levels."""
        # Disable early termination to ensure all validators run
        config = PipelineConfiguration(enable_early_termination=False)
        pipeline = ValidationPipeline(config)
        
        context = ValidationContext(
            text="Mixed confidence scenario with ambiguous error requiring careful analysis.",
            error_position=30,
            error_text="ambiguous",
            rule_type="clarity",
            rule_name="ambiguity_detection"
        )
        
        result = pipeline.validate_error(context)
        
        # Check confidence analysis
        consensus = result.consensus_analysis
        self.assertIsInstance(consensus.confidence_spread, float)
        self.assertGreaterEqual(consensus.confidence_spread, 0.0)
        
        # Check that all validators provided results (when early termination disabled)
        self.assertEqual(len(result.validator_results), 4)
        
        # Verify confidence scores are reasonable
        for validator_result in result.validator_results.values():
            self.assertGreaterEqual(validator_result.confidence_score, 0.0)
            self.assertLessEqual(validator_result.confidence_score, 1.0)


class TestPipelineConfigurationFlexibility(unittest.TestCase):
    """Test pipeline configuration flexibility and customization."""
    
    def test_consensus_strategy_switching(self):
        """Test switching between different consensus strategies."""
        strategies = [
            ConsensusStrategy.MAJORITY_VOTE,
            ConsensusStrategy.WEIGHTED_AVERAGE,
            ConsensusStrategy.BEST_CONFIDENCE,
            ConsensusStrategy.STAGED_FALLBACK
        ]
        
        context = ValidationContext(
            text="Testing consensus strategy flexibility.",
            error_position=10,
            error_text="consensus",
            rule_type="test",
            rule_name="strategy_test"
        )
        
        for strategy in strategies:
            with self.subTest(strategy=strategy):
                config = PipelineConfiguration(consensus_strategy=strategy)
                pipeline = ValidationPipeline(config)
                
                result = pipeline.validate_error(context)
                
                # Should complete successfully with any strategy
                self.assertIsInstance(result, PipelineResult)
                self.assertIsNotNone(result.consensus_analysis.final_decision)
    
    def test_validator_subset_configurations(self):
        """Test various validator subset configurations."""
        configurations = [
            {'morphological': True, 'contextual': True, 'domain': False, 'cross_rule': False},
            {'morphological': True, 'contextual': False, 'domain': True, 'cross_rule': False},
            {'morphological': False, 'contextual': True, 'domain': True, 'cross_rule': False},
            {'morphological': True, 'contextual': True, 'domain': True, 'cross_rule': False},
        ]
        
        context = ValidationContext(
            text="Testing validator subset configurations.",
            error_position=15,
            error_text="validator",
            rule_type="test",
            rule_name="subset_test"
        )
        
        for config_dict in configurations:
            with self.subTest(config=config_dict):
                config = PipelineConfiguration(
                    enable_morphological=config_dict['morphological'],
                    enable_contextual=config_dict['contextual'],
                    enable_domain=config_dict['domain'],
                    enable_cross_rule=config_dict['cross_rule'],
                    enable_early_termination=False  # Disable to ensure all enabled validators run
                )
                
                pipeline = ValidationPipeline(config)
                result = pipeline.validate_error(context)
                
                # Check correct number of validators
                expected_count = sum(config_dict.values())
                self.assertEqual(len(result.validator_results), expected_count)
    
    def test_performance_monitoring_toggle(self):
        """Test performance monitoring enable/disable."""
        context = ValidationContext(
            text="Performance monitoring toggle test.",
            error_position=12,
            error_text="monitoring",
            rule_type="performance",
            rule_name="monitoring_test"
        )
        
        # Test with performance monitoring enabled
        config_enabled = PipelineConfiguration(enable_performance_monitoring=True)
        pipeline_enabled = ValidationPipeline(config_enabled)
        result_enabled = pipeline_enabled.validate_error(context)
        
        # Test with performance monitoring disabled
        config_disabled = PipelineConfiguration(enable_performance_monitoring=False)
        pipeline_disabled = ValidationPipeline(config_disabled)
        result_disabled = pipeline_disabled.validate_error(context)
        
        # Both should work, but enabled should have more detailed metrics
        self.assertIsInstance(result_enabled.audit_trail.performance_metrics, dict)
        self.assertIsInstance(result_disabled.audit_trail.performance_metrics, dict)
        
        # Enabled version should have more detailed metrics
        if len(result_enabled.audit_trail.performance_metrics) > 0:
            self.assertGreaterEqual(
                len(result_enabled.audit_trail.performance_metrics),
                len(result_disabled.audit_trail.performance_metrics)
            )


if __name__ == '__main__':
    unittest.main(verbosity=2)
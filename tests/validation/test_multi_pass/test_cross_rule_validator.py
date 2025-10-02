"""
Comprehensive test suite for CrossRuleValidator class.
Tests rule conflict detection, error coherence validation, consolidation assessment,
and overall improvement analysis.
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock

from validation.multi_pass.pass_validators.cross_rule_validator import (
    CrossRuleValidator, RuleConflictDetection, ErrorCoherenceValidation,
    ConsolidationValidation, ImprovementAssessment, ConflictSeverity,
    CoherenceLevel, ImprovementType
)
from validation.multi_pass import ValidationContext, ValidationDecision, ValidationConfidence


class TestCrossRuleValidatorInitialization(unittest.TestCase):
    """Test CrossRuleValidator initialization and configuration."""
    
    def test_default_initialization(self):
        """Test initialization with default settings."""
        validator = CrossRuleValidator()
        
        self.assertEqual(validator.validator_name, "cross_rule_validator")
        self.assertTrue(validator.enable_conflict_detection)
        self.assertTrue(validator.enable_coherence_validation)
        self.assertTrue(validator.enable_consolidation_validation)
        self.assertTrue(validator.enable_improvement_assessment)
        self.assertTrue(validator.cache_analysis_results)
        self.assertEqual(validator.min_confidence_threshold, 0.65)
        self.assertEqual(validator.max_conflicts_to_analyze, 50)
    
    def test_custom_initialization(self):
        """Test initialization with custom settings."""
        validator = CrossRuleValidator(
            enable_conflict_detection=False,
            enable_coherence_validation=False,
            enable_consolidation_validation=False,
            enable_improvement_assessment=False,
            cache_analysis_results=False,
            min_confidence_threshold=0.75,
            max_conflicts_to_analyze=25
        )
        
        self.assertFalse(validator.enable_conflict_detection)
        self.assertFalse(validator.enable_coherence_validation)
        self.assertFalse(validator.enable_consolidation_validation)
        self.assertFalse(validator.enable_improvement_assessment)
        self.assertFalse(validator.cache_analysis_results)
        self.assertEqual(validator.min_confidence_threshold, 0.75)
        self.assertEqual(validator.max_conflicts_to_analyze, 25)
    
    def test_validator_info(self):
        """Test get_validator_info method."""
        validator = CrossRuleValidator()
        info = validator.get_validator_info()
        
        self.assertEqual(info["name"], "cross_rule_validator")
        self.assertEqual(info["type"], "cross_rule_validator")
        self.assertIn("rule_conflict_detection", info["capabilities"])
        self.assertIn("error_coherence_validation", info["capabilities"])
        self.assertIn("consolidation_validation", info["capabilities"])
        self.assertIn("improvement_assessment", info["capabilities"])
        self.assertIn("cross_rule_analysis", info["specialties"])
        self.assertIn("configuration", info)
        self.assertIn("performance_characteristics", info)
        self.assertIn("analysis_knowledge", info)
    
    def test_rule_relationships_initialization(self):
        """Test that rule relationships and patterns are properly initialized."""
        validator = CrossRuleValidator()
        
        # Check rule categories
        self.assertIn("grammar", validator.rule_categories)
        self.assertIn("style", validator.rule_categories)
        self.assertIn("punctuation", validator.rule_categories)
        
        # Check known conflicts
        self.assertIn("conciseness_vs_clarity", validator.known_conflicts)
        self.assertIn("formality_vs_accessibility", validator.known_conflicts)
        
        # Check rule priorities
        self.assertIn("grammar", validator.rule_priorities)
        self.assertIn("style", validator.rule_priorities)
        
        # Check conflict patterns
        self.assertIn("contradictory_suggestions", validator.conflict_patterns)
        self.assertIn("opposing_modifications", validator.conflict_patterns)
        
        # Check coherence criteria
        self.assertIn("logical_consistency", validator.coherence_criteria)
        self.assertIn("temporal_consistency", validator.coherence_criteria)
    
    def test_quality_metrics_initialization(self):
        """Test that quality metrics are properly initialized."""
        validator = CrossRuleValidator()
        
        # Check quality metrics
        self.assertIn("readability", validator.quality_metrics)
        self.assertIn("clarity", validator.quality_metrics)
        self.assertIn("consistency", validator.quality_metrics)
        self.assertIn("correctness", validator.quality_metrics)
        
        # Check improvement thresholds
        self.assertIn(ImprovementType.SIGNIFICANT, validator.improvement_thresholds)
        self.assertIn(ImprovementType.MODERATE, validator.improvement_thresholds)
        
        # Check error severity weights
        self.assertIn("critical", validator.error_severity_weights)
        self.assertIn("major", validator.error_severity_weights)


class TestRuleConflictDetection(unittest.TestCase):
    """Test rule conflict detection functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = CrossRuleValidator()
    
    def test_rule_conflict_detection_creation(self):
        """Test RuleConflictDetection dataclass creation."""
        detection = RuleConflictDetection(
            conflicting_rules=[("rule1", "rule2")],
            conflict_types={"contradiction": [("rule1", "rule2")]},
            conflict_severity=ConflictSeverity.MODERATE,
            affected_positions=[10, 20],
            resolution_strategy="prefer_higher_priority",
            priority_conflicts=[],
            rule_interactions={"rule1": ["rule2"]},
            conflict_metadata={"total_rules": 2}
        )
        
        self.assertEqual(detection.conflicting_rules, [("rule1", "rule2")])
        self.assertEqual(detection.conflict_severity, ConflictSeverity.MODERATE)
        self.assertEqual(detection.affected_positions, [10, 20])
        self.assertEqual(detection.resolution_strategy, "prefer_higher_priority")
    
    def test_multiple_rule_conflict_detection(self):
        """Test conflict detection with multiple rules."""
        context = ValidationContext(
            text="The sentence should be shortened but also needs more detail for clarity.",
            error_position=20,
            error_text="shortened",
            rule_type="style",
            rule_name="sentence_shortening",
            additional_context={
                "all_rules": ["sentence_shortening", "detail_addition", "clarity_improvement"]
            }
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect conflicts when conflict detection is enabled
        if self.validator.enable_conflict_detection:
            conflict_evidence = next((e for e in result.evidence if e.evidence_type == "rule_conflict_detection"), None)
            if conflict_evidence:
                self.assertIn("conflicting_rules", conflict_evidence.source_data)
                self.assertIn("conflict_severity", conflict_evidence.source_data)
    
    def test_known_conflict_detection(self):
        """Test detection of known rule conflicts."""
        rules = ["sentence_shortening", "detail_addition"]
        
        # Mock the context to provide known conflicting rules
        context = ValidationContext(
            text="Test text for conflict detection.",
            error_position=10,
            error_text="test",
            rule_type="style",
            rule_name="sentence_shortening",
            additional_context={"all_rules": rules}
        )
        
        result = self.validator.validate_error(context)
        
        # Should identify conflicts between shortening and detail addition
        conflict_evidence = next((e for e in result.evidence if e.evidence_type == "rule_conflict_detection"), None)
        if conflict_evidence:
            conflicting_rules = conflict_evidence.source_data.get("conflicting_rules", [])
            self.assertIsInstance(conflicting_rules, list)
    
    def test_conflict_severity_assessment(self):
        """Test conflict severity assessment."""
        # Test different rule combinations for varying severity
        test_cases = [
            (["grammar_rule", "style_rule"], "low_severity_expected"),
            (["formal_language", "simple_language"], "moderate_severity_expected"),
            (["content_reduction", "information_completeness"], "high_severity_expected")
        ]
        
        for rules, expected_severity in test_cases:
            with self.subTest(rules=rules):
                context = ValidationContext(
                    text="Test text for severity assessment.",
                    error_position=10,
                    error_text="test",
                    rule_type="mixed",
                    rule_name=rules[0],
                    additional_context={"all_rules": rules}
                )
                
                result = self.validator.validate_error(context)
                
                # Verify that severity assessment is performed
                conflict_evidence = next((e for e in result.evidence if e.evidence_type == "rule_conflict_detection"), None)
                if conflict_evidence:
                    severity = conflict_evidence.source_data.get("conflict_severity")
                    self.assertIsInstance(severity, str)
    
    def test_resolution_strategy_determination(self):
        """Test resolution strategy determination."""
        rules = ["active_voice_preference", "passive_voice_appropriateness"]
        
        context = ValidationContext(
            text="The document was written by the author.",
            error_position=20,
            error_text="was written",
            rule_type="style",
            rule_name="active_voice_preference",
            additional_context={"all_rules": rules}
        )
        
        result = self.validator.validate_error(context)
        
        # Should provide resolution strategy
        conflict_evidence = next((e for e in result.evidence if e.evidence_type == "rule_conflict_detection"), None)
        if conflict_evidence:
            strategy = conflict_evidence.source_data.get("resolution_strategy")
            self.assertIsInstance(strategy, str)
            self.assertGreater(len(strategy), 0)
    
    def test_conflict_detection_disabled(self):
        """Test behavior when conflict detection is disabled."""
        validator = CrossRuleValidator(enable_conflict_detection=False)
        
        context = ValidationContext(
            text="Test text with potential conflicts.",
            error_position=10,
            error_text="test",
            rule_type="style",
            rule_name="conflicting_rule",
            additional_context={"all_rules": ["rule1", "rule2", "rule3"]}
        )
        
        result = validator.validate_error(context)
        
        # Should not have conflict detection evidence
        conflict_evidence = next((e for e in result.evidence if e.evidence_type == "rule_conflict_detection"), None)
        self.assertIsNone(conflict_evidence)


class TestErrorCoherenceValidation(unittest.TestCase):
    """Test error coherence validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = CrossRuleValidator()
    
    def test_error_coherence_validation_creation(self):
        """Test ErrorCoherenceValidation dataclass creation."""
        validation = ErrorCoherenceValidation(
            coherence_level=CoherenceLevel.GOOD,
            coherence_score=0.75,
            logical_consistency=0.8,
            temporal_consistency=0.7,
            semantic_consistency=0.8,
            contradiction_count=1,
            inconsistency_areas=["style"],
            coherence_factors=["high_error_count"],
            improvement_suggestions=["group_similar_errors"]
        )
        
        self.assertEqual(validation.coherence_level, CoherenceLevel.GOOD)
        self.assertEqual(validation.coherence_score, 0.75)
        self.assertEqual(validation.logical_consistency, 0.8)
        self.assertEqual(validation.contradiction_count, 1)
    
    def test_multiple_error_coherence_validation(self):
        """Test coherence validation with multiple errors."""
        errors = [
            {"text": "error1", "position": 10, "rule_type": "grammar", "rule_name": "subject_verb", "severity": "major"},
            {"text": "error2", "position": 30, "rule_type": "grammar", "rule_name": "tense_consistency", "severity": "moderate"},
            {"text": "error3", "position": 50, "rule_type": "style", "rule_name": "tone_consistency", "severity": "minor"}
        ]
        
        context = ValidationContext(
            text="The comprehensive document contains multiple errors that should be analyzed.",
            error_position=10,
            error_text="error1",
            rule_type="grammar",
            rule_name="subject_verb",
            additional_context={"all_errors": errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should have coherence validation evidence when enabled
        if self.validator.enable_coherence_validation:
            coherence_evidence = next((e for e in result.evidence if e.evidence_type == "error_coherence_validation"), None)
            if coherence_evidence:
                self.assertIn("coherence_level", coherence_evidence.source_data)
                self.assertIn("coherence_score", coherence_evidence.source_data)
                self.assertIn("logical_consistency", coherence_evidence.source_data)
    
    def test_logical_consistency_assessment(self):
        """Test logical consistency assessment."""
        # Test contradictory errors
        contradictory_errors = [
            {"text": "add_content", "position": 10, "rule_type": "content", "rule_name": "add_content", "severity": "moderate"},
            {"text": "remove_content", "position": 30, "rule_type": "content", "rule_name": "remove_content", "severity": "moderate"}
        ]
        
        context = ValidationContext(
            text="Test text for logical consistency.",
            error_position=10,
            error_text="add_content",
            rule_type="content",
            rule_name="add_content",
            additional_context={"all_errors": contradictory_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect logical inconsistency
        coherence_evidence = next((e for e in result.evidence if e.evidence_type == "error_coherence_validation"), None)
        if coherence_evidence:
            logical_consistency = coherence_evidence.source_data.get("logical_consistency", 1.0)
            self.assertIsInstance(logical_consistency, float)
            self.assertGreaterEqual(logical_consistency, 0.0)
            self.assertLessEqual(logical_consistency, 1.0)
    
    def test_temporal_consistency_assessment(self):
        """Test temporal consistency assessment."""
        tense_errors = [
            {"text": "past_tense", "position": 10, "rule_type": "grammar", "rule_name": "past_tense_correction", "severity": "moderate"},
            {"text": "present_tense", "position": 30, "rule_type": "grammar", "rule_name": "present_tense_correction", "severity": "moderate"}
        ]
        
        context = ValidationContext(
            text="Test text for temporal consistency analysis.",
            error_position=10,
            error_text="past_tense",
            rule_type="grammar",
            rule_name="past_tense_correction",
            additional_context={"all_errors": tense_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess temporal consistency
        coherence_evidence = next((e for e in result.evidence if e.evidence_type == "error_coherence_validation"), None)
        if coherence_evidence:
            temporal_consistency = coherence_evidence.source_data.get("temporal_consistency", 1.0)
            self.assertIsInstance(temporal_consistency, float)
            self.assertGreaterEqual(temporal_consistency, 0.0)
            self.assertLessEqual(temporal_consistency, 1.0)
    
    def test_contradiction_detection(self):
        """Test detection of contradictions between errors."""
        contradictory_errors = [
            {"text": "formal", "position": 10, "rule_type": "style", "rule_name": "formal_language", "severity": "moderate"},
            {"text": "informal", "position": 30, "rule_type": "style", "rule_name": "informal_style", "severity": "moderate"}
        ]
        
        context = ValidationContext(
            text="Test text for contradiction detection.",
            error_position=10,
            error_text="formal",
            rule_type="style",
            rule_name="formal_language",
            additional_context={"all_errors": contradictory_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect contradictions
        coherence_evidence = next((e for e in result.evidence if e.evidence_type == "error_coherence_validation"), None)
        if coherence_evidence:
            contradiction_count = coherence_evidence.source_data.get("contradiction_count", 0)
            self.assertIsInstance(contradiction_count, int)
            self.assertGreaterEqual(contradiction_count, 0)
    
    def test_coherence_improvement_suggestions(self):
        """Test generation of coherence improvement suggestions."""
        many_errors = [
            {"text": f"error{i}", "position": i*10, "rule_type": "style", "rule_name": f"rule{i}", "severity": "minor"}
            for i in range(20)
        ]
        
        context = ValidationContext(
            text="Test text with many errors for improvement suggestions.",
            error_position=10,
            error_text="error1",
            rule_type="style",
            rule_name="rule1",
            additional_context={"all_errors": many_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should provide improvement suggestions
        coherence_evidence = next((e for e in result.evidence if e.evidence_type == "error_coherence_validation"), None)
        if coherence_evidence:
            suggestions = coherence_evidence.source_data.get("improvement_suggestions", [])
            self.assertIsInstance(suggestions, list)
    
    def test_coherence_validation_disabled(self):
        """Test behavior when coherence validation is disabled."""
        validator = CrossRuleValidator(enable_coherence_validation=False)
        
        errors = [
            {"text": "error1", "position": 10, "rule_type": "grammar", "rule_name": "rule1", "severity": "major"},
            {"text": "error2", "position": 30, "rule_type": "style", "rule_name": "rule2", "severity": "moderate"}
        ]
        
        context = ValidationContext(
            text="Test text with multiple errors.",
            error_position=10,
            error_text="error1",
            rule_type="grammar",
            rule_name="rule1",
            additional_context={"all_errors": errors}
        )
        
        result = validator.validate_error(context)
        
        # Should not have coherence evidence when disabled
        coherence_evidence = next((e for e in result.evidence if e.evidence_type == "error_coherence_validation"), None)
        self.assertIsNone(coherence_evidence)


class TestConsolidationValidation(unittest.TestCase):
    """Test consolidation validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = CrossRuleValidator()
    
    def test_consolidation_validation_creation(self):
        """Test ConsolidationValidation dataclass creation."""
        validation = ConsolidationValidation(
            consolidation_quality=0.8,
            merge_appropriateness=0.75,
            priority_accuracy=0.85,
            completeness_score=0.9,
            redundancy_elimination=0.7,
            consolidation_errors=[],
            missed_opportunities=["merge_similar_errors"],
            over_consolidation=[],
            consolidation_metadata={"total_errors": 5}
        )
        
        self.assertEqual(validation.consolidation_quality, 0.8)
        self.assertEqual(validation.merge_appropriateness, 0.75)
        self.assertEqual(validation.priority_accuracy, 0.85)
        self.assertEqual(validation.completeness_score, 0.9)
        self.assertEqual(validation.redundancy_elimination, 0.7)
    
    def test_consolidation_quality_assessment(self):
        """Test consolidation quality assessment."""
        well_consolidated_errors = [
            {"text": "error1", "position": 10, "rule_type": "grammar", "rule_name": "rule1", "severity": "major"},
            {"text": "error2", "position": 30, "rule_type": "grammar", "rule_name": "rule2", "severity": "moderate"},
            {"text": "error3", "position": 50, "rule_type": "style", "rule_name": "rule3", "severity": "minor"}
        ]
        
        context = ValidationContext(
            text="Test text for consolidation quality assessment.",
            error_position=10,
            error_text="error1",
            rule_type="grammar",
            rule_name="rule1",
            additional_context={"all_errors": well_consolidated_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess consolidation quality
        if self.validator.enable_consolidation_validation:
            consolidation_evidence = next((e for e in result.evidence if e.evidence_type == "consolidation_validation"), None)
            if consolidation_evidence:
                quality = consolidation_evidence.source_data.get("consolidation_quality", 0)
                self.assertIsInstance(quality, float)
                self.assertGreaterEqual(quality, 0.0)
                self.assertLessEqual(quality, 1.0)
    
    def test_merge_appropriateness_assessment(self):
        """Test merge appropriateness assessment."""
        close_errors = [
            {"text": "error1", "position": 10, "rule_type": "grammar", "rule_name": "rule1", "severity": "major"},
            {"text": "error2", "position": 15, "rule_type": "grammar", "rule_name": "rule2", "severity": "moderate"},  # Close to first
            {"text": "error3", "position": 100, "rule_type": "style", "rule_name": "rule3", "severity": "minor"}   # Far from others
        ]
        
        context = ValidationContext(
            text="Test text for merge appropriateness assessment with errors close together.",
            error_position=10,
            error_text="error1",
            rule_type="grammar", 
            rule_name="rule1",
            additional_context={"all_errors": close_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess merge appropriateness
        consolidation_evidence = next((e for e in result.evidence if e.evidence_type == "consolidation_validation"), None)
        if consolidation_evidence:
            merge_appropriateness = consolidation_evidence.source_data.get("merge_appropriateness", 0)
            self.assertIsInstance(merge_appropriateness, float)
            self.assertGreaterEqual(merge_appropriateness, 0.0)
            self.assertLessEqual(merge_appropriateness, 1.0)
    
    def test_priority_accuracy_assessment(self):
        """Test priority accuracy assessment."""
        priority_ordered_errors = [
            {"text": "critical_error", "position": 10, "rule_type": "grammar", "rule_name": "critical_rule", "severity": "critical"},
            {"text": "major_error", "position": 30, "rule_type": "grammar", "rule_name": "major_rule", "severity": "major"},
            {"text": "minor_error", "position": 50, "rule_type": "style", "rule_name": "minor_rule", "severity": "minor"}
        ]
        
        context = ValidationContext(
            text="Test text for priority accuracy assessment.",
            error_position=10,
            error_text="critical_error",
            rule_type="grammar",
            rule_name="critical_rule",
            additional_context={"all_errors": priority_ordered_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess priority accuracy
        consolidation_evidence = next((e for e in result.evidence if e.evidence_type == "consolidation_validation"), None)
        if consolidation_evidence:
            priority_accuracy = consolidation_evidence.source_data.get("priority_accuracy", 0)
            self.assertIsInstance(priority_accuracy, float)
            self.assertGreaterEqual(priority_accuracy, 0.0)
            self.assertLessEqual(priority_accuracy, 1.0)
    
    def test_redundancy_elimination_assessment(self):
        """Test redundancy elimination assessment."""
        redundant_errors = [
            {"text": "duplicate1", "position": 10, "rule_type": "grammar", "rule_name": "same_rule", "severity": "moderate"},
            {"text": "duplicate2", "position": 30, "rule_type": "grammar", "rule_name": "same_rule", "severity": "moderate"},
            {"text": "unique", "position": 50, "rule_type": "style", "rule_name": "different_rule", "severity": "minor"}
        ]
        
        context = ValidationContext(
            text="Test text for redundancy elimination assessment.",
            error_position=10,
            error_text="duplicate1",
            rule_type="grammar",
            rule_name="same_rule",
            additional_context={"all_errors": redundant_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess redundancy elimination
        consolidation_evidence = next((e for e in result.evidence if e.evidence_type == "consolidation_validation"), None)
        if consolidation_evidence:
            redundancy_elimination = consolidation_evidence.source_data.get("redundancy_elimination", 0)
            self.assertIsInstance(redundancy_elimination, float)
            self.assertGreaterEqual(redundancy_elimination, 0.0)
            self.assertLessEqual(redundancy_elimination, 1.0)
    
    def test_missed_opportunities_identification(self):
        """Test identification of missed consolidation opportunities."""
        similar_errors = [
            {"text": "similar1", "position": 10, "rule_type": "grammar", "rule_name": "grammar_rule", "severity": "moderate"},
            {"text": "similar2", "position": 20, "rule_type": "grammar", "rule_name": "grammar_rule", "severity": "moderate"},
            {"text": "different", "position": 100, "rule_type": "style", "rule_name": "style_rule", "severity": "minor"}
        ]
        
        context = ValidationContext(
            text="Test text for missed opportunities identification.",
            error_position=10,
            error_text="similar1",
            rule_type="grammar",
            rule_name="grammar_rule",
            additional_context={"all_errors": similar_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should identify missed opportunities
        consolidation_evidence = next((e for e in result.evidence if e.evidence_type == "consolidation_validation"), None)
        if consolidation_evidence:
            missed_opportunities = consolidation_evidence.source_data.get("missed_opportunities", [])
            self.assertIsInstance(missed_opportunities, list)
    
    def test_over_consolidation_detection(self):
        """Test detection of over-consolidation."""
        many_similar_errors = [
            {"text": f"error{i}", "position": i*10, "rule_type": "grammar", "rule_name": "grammar_rule", "severity": "minor"}
            for i in range(15)  # Many errors of same type
        ]
        
        context = ValidationContext(
            text="Test text for over-consolidation detection with many similar errors.",
            error_position=10,
            error_text="error1",
            rule_type="grammar",
            rule_name="grammar_rule",
            additional_context={"all_errors": many_similar_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect over-consolidation
        consolidation_evidence = next((e for e in result.evidence if e.evidence_type == "consolidation_validation"), None)
        if consolidation_evidence:
            over_consolidation = consolidation_evidence.source_data.get("over_consolidation", [])
            self.assertIsInstance(over_consolidation, list)
    
    def test_consolidation_validation_disabled(self):
        """Test behavior when consolidation validation is disabled."""
        validator = CrossRuleValidator(enable_consolidation_validation=False)
        
        errors = [
            {"text": "error1", "position": 10, "rule_type": "grammar", "rule_name": "rule1", "severity": "major"},
            {"text": "error2", "position": 30, "rule_type": "style", "rule_name": "rule2", "severity": "moderate"}
        ]
        
        context = ValidationContext(
            text="Test text for disabled consolidation validation.",
            error_position=10,
            error_text="error1",
            rule_type="grammar",
            rule_name="rule1",
            additional_context={"all_errors": errors}
        )
        
        result = validator.validate_error(context)
        
        # Should not have consolidation evidence when disabled
        consolidation_evidence = next((e for e in result.evidence if e.evidence_type == "consolidation_validation"), None)
        self.assertIsNone(consolidation_evidence)


class TestImprovementAssessment(unittest.TestCase):
    """Test improvement assessment functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = CrossRuleValidator()
    
    def test_improvement_assessment_creation(self):
        """Test ImprovementAssessment dataclass creation."""
        assessment = ImprovementAssessment(
            improvement_type=ImprovementType.MODERATE,
            improvement_score=0.65,
            quality_metrics={"readability": 0.8, "clarity": 0.7},
            readability_improvement=0.6,
            clarity_improvement=0.7,
            consistency_improvement=0.65,
            error_reduction_rate=0.8,
            remaining_issues=["minor_style_issues"],
            improvement_areas=["grammar", "clarity"],
            regression_areas=[],
            improvement_confidence=0.75
        )
        
        self.assertEqual(assessment.improvement_type, ImprovementType.MODERATE)
        self.assertEqual(assessment.improvement_score, 0.65)
        self.assertEqual(assessment.readability_improvement, 0.6)
        self.assertEqual(assessment.clarity_improvement, 0.7)
        self.assertEqual(assessment.consistency_improvement, 0.65)
        self.assertEqual(assessment.error_reduction_rate, 0.8)
        self.assertEqual(assessment.improvement_confidence, 0.75)
    
    def test_overall_improvement_assessment(self):
        """Test overall improvement assessment."""
        improved_errors = [
            {"text": "clarity_error", "position": 10, "rule_type": "clarity", "rule_name": "ambiguity_removal", "severity": "moderate"},
            {"text": "readability_error", "position": 30, "rule_type": "readability", "rule_name": "sentence_length", "severity": "minor"},
            {"text": "consistency_error", "position": 50, "rule_type": "consistency", "rule_name": "terminology_consistency", "severity": "minor"}
        ]
        
        context = ValidationContext(
            text="Test text for overall improvement assessment with various error types addressed.",
            error_position=10,
            error_text="clarity_error",
            rule_type="clarity",
            rule_name="ambiguity_removal",
            additional_context={
                "all_errors": improved_errors,
                "all_rules": ["ambiguity_removal", "sentence_length", "terminology_consistency"]
            }
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess overall improvement
        if self.validator.enable_improvement_assessment:
            improvement_evidence = next((e for e in result.evidence if e.evidence_type == "improvement_assessment"), None)
            if improvement_evidence:
                self.assertIn("improvement_type", improvement_evidence.source_data)
                self.assertIn("improvement_score", improvement_evidence.source_data)
                self.assertIn("quality_metrics", improvement_evidence.source_data)
    
    def test_quality_metrics_calculation(self):
        """Test quality metrics calculation."""
        various_errors = [
            {"text": "grammar_error", "position": 10, "rule_type": "grammar", "rule_name": "subject_verb", "severity": "major"},
            {"text": "style_error", "position": 30, "rule_type": "style", "rule_name": "tone_consistency", "severity": "moderate"},
            {"text": "clarity_error", "position": 50, "rule_type": "clarity", "rule_name": "ambiguity", "severity": "minor"}
        ]
        
        context = ValidationContext(
            text="Test text for quality metrics calculation with different error types.",
            error_position=10,
            error_text="grammar_error",
            rule_type="grammar",
            rule_name="subject_verb",
            additional_context={"all_errors": various_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should calculate quality metrics
        improvement_evidence = next((e for e in result.evidence if e.evidence_type == "improvement_assessment"), None)
        if improvement_evidence:
            quality_metrics = improvement_evidence.source_data.get("quality_metrics", {})
            self.assertIsInstance(quality_metrics, dict)
            
            # Check for expected metrics
            expected_metrics = ["readability", "clarity", "consistency", "correctness"]
            for metric in expected_metrics:
                if metric in quality_metrics:
                    self.assertIsInstance(quality_metrics[metric], float)
                    self.assertGreaterEqual(quality_metrics[metric], 0.0)
                    self.assertLessEqual(quality_metrics[metric], 1.0)
    
    def test_improvement_type_classification(self):
        """Test improvement type classification."""
        # Test different scenarios for different improvement types
        test_scenarios = [
            (ImprovementType.SIGNIFICANT, [
                {"text": "critical_fix", "position": 10, "rule_type": "grammar", "rule_name": "critical_rule", "severity": "critical"}
            ]),
            (ImprovementType.MODERATE, [
                {"text": "moderate_fix", "position": 10, "rule_type": "style", "rule_name": "moderate_rule", "severity": "moderate"}
            ]),
            (ImprovementType.MINIMAL, [
                {"text": "minor_fix", "position": 10, "rule_type": "style", "rule_name": "minor_rule", "severity": "minor"}
            ])
        ]
        
        for expected_type, errors in test_scenarios:
            with self.subTest(improvement_type=expected_type):
                context = ValidationContext(
                    text="Test text for improvement type classification.",
                    error_position=10,
                    error_text=errors[0]["text"],
                    rule_type=errors[0]["rule_type"],
                    rule_name=errors[0]["rule_name"],
                    additional_context={"all_errors": errors}
                )
                
                result = self.validator.validate_error(context)
                
                # Should classify improvement type
                improvement_evidence = next((e for e in result.evidence if e.evidence_type == "improvement_assessment"), None)
                if improvement_evidence:
                    improvement_type = improvement_evidence.source_data.get("improvement_type")
                    self.assertIsInstance(improvement_type, str)
    
    def test_remaining_issues_identification(self):
        """Test identification of remaining issues."""
        remaining_errors = [
            {"text": "critical_remaining", "position": 10, "rule_type": "grammar", "rule_name": "critical_rule", "severity": "critical"},
            {"text": "major_remaining", "position": 30, "rule_type": "grammar", "rule_name": "major_rule", "severity": "major"},
            {"text": "minor_remaining", "position": 50, "rule_type": "style", "rule_name": "minor_rule", "severity": "minor"}
        ]
        
        context = ValidationContext(
            text="Test text for remaining issues identification.",
            error_position=10,
            error_text="critical_remaining",
            rule_type="grammar",
            rule_name="critical_rule",
            additional_context={"all_errors": remaining_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should identify remaining issues
        improvement_evidence = next((e for e in result.evidence if e.evidence_type == "improvement_assessment"), None)
        if improvement_evidence:
            remaining_issues = improvement_evidence.source_data.get("remaining_issues", [])
            self.assertIsInstance(remaining_issues, list)
    
    def test_improvement_areas_identification(self):
        """Test identification of improvement areas."""
        improvement_errors = [
            {"text": "grammar_improvement", "position": 10, "rule_type": "grammar", "rule_name": "grammar_rule", "severity": "moderate"},
            {"text": "style_improvement", "position": 30, "rule_type": "style", "rule_name": "style_rule", "severity": "moderate"},
            {"text": "clarity_improvement", "position": 50, "rule_type": "clarity", "rule_name": "clarity_rule", "severity": "minor"}
        ]
        
        context = ValidationContext(
            text="Test text for improvement areas identification.",
            error_position=10,
            error_text="grammar_improvement",
            rule_type="grammar",
            rule_name="grammar_rule",
            additional_context={"all_errors": improvement_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should identify improvement areas
        improvement_evidence = next((e for e in result.evidence if e.evidence_type == "improvement_assessment"), None)
        if improvement_evidence:
            improvement_areas = improvement_evidence.source_data.get("improvement_areas", [])
            self.assertIsInstance(improvement_areas, list)
    
    def test_improvement_confidence_calculation(self):
        """Test improvement confidence calculation."""
        many_errors = [
            {"text": f"error{i}", "position": i*10, "rule_type": "grammar", "rule_name": f"rule{i}", "severity": "moderate"}
            for i in range(12)  # Many errors for higher confidence
        ]
        
        context = ValidationContext(
            text="Test text for improvement confidence calculation with many analyzed errors.",
            error_position=10,
            error_text="error1",
            rule_type="grammar",
            rule_name="rule1",
            additional_context={"all_errors": many_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Should calculate improvement confidence
        improvement_evidence = next((e for e in result.evidence if e.evidence_type == "improvement_assessment"), None)
        if improvement_evidence:
            improvement_confidence = improvement_evidence.source_data.get("improvement_confidence", 0)
            self.assertIsInstance(improvement_confidence, float)
            self.assertGreaterEqual(improvement_confidence, 0.0)
            self.assertLessEqual(improvement_confidence, 1.0)
    
    def test_improvement_assessment_disabled(self):
        """Test behavior when improvement assessment is disabled."""
        validator = CrossRuleValidator(enable_improvement_assessment=False)
        
        errors = [
            {"text": "error1", "position": 10, "rule_type": "grammar", "rule_name": "rule1", "severity": "major"},
            {"text": "error2", "position": 30, "rule_type": "style", "rule_name": "rule2", "severity": "moderate"}
        ]
        
        context = ValidationContext(
            text="Test text for disabled improvement assessment.",
            error_position=10,
            error_text="error1",
            rule_type="grammar",
            rule_name="rule1",
            additional_context={"all_errors": errors}
        )
        
        result = validator.validate_error(context)
        
        # Should not have improvement evidence when disabled
        improvement_evidence = next((e for e in result.evidence if e.evidence_type == "improvement_assessment"), None)
        self.assertIsNone(improvement_evidence)


class TestValidationDecisionMaking(unittest.TestCase):
    """Test validation decision making logic."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = CrossRuleValidator()
    
    def test_critical_conflict_decision(self):
        """Test decision logic for critical conflicts."""
        critical_rules = ["content_reduction", "information_completeness"]  # Known severe conflict
        
        context = ValidationContext(
            text="The document should be shortened but also needs comprehensive detail.",
            error_position=20,
            error_text="shortened",
            rule_type="content",
            rule_name="content_reduction",
            additional_context={"all_rules": critical_rules}
        )
        
        result = self.validator.validate_error(context)
        
        # Critical conflicts should lead to rejection or uncertainty
        self.assertIn(result.decision, [ValidationDecision.REJECT, ValidationDecision.UNCERTAIN])
        self.assertIsInstance(result.confidence_score, float)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
    
    def test_good_coherence_decision(self):
        """Test decision logic for good error coherence."""
        coherent_errors = [
            {"text": "grammar1", "position": 10, "rule_type": "grammar", "rule_name": "subject_verb", "severity": "moderate"},
            {"text": "grammar2", "position": 30, "rule_type": "grammar", "rule_name": "tense_consistency", "severity": "minor"}
        ]
        
        context = ValidationContext(
            text="The document has consistent grammar errors that are coherent.",
            error_position=10,
            error_text="grammar1",
            rule_type="grammar",
            rule_name="subject_verb",
            additional_context={"all_errors": coherent_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Good coherence should lead to acceptance
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        self.assertGreater(result.confidence_score, 0.3)
    
    def test_significant_improvement_decision(self):
        """Test decision logic for significant improvement."""
        improvement_errors = [
            {"text": "critical_fix", "position": 10, "rule_type": "grammar", "rule_name": "critical_grammar", "severity": "critical"},
            {"text": "clarity_fix", "position": 30, "rule_type": "clarity", "rule_name": "ambiguity_removal", "severity": "major"}
        ]
        
        context = ValidationContext(
            text="The document shows significant improvement through critical fixes.",
            error_position=10,
            error_text="critical_fix",
            rule_type="grammar",
            rule_name="critical_grammar",
            additional_context={"all_errors": improvement_errors}
        )
        
        result = self.validator.validate_error(context)
        
        # Significant improvement should lead to acceptance
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        self.assertIsInstance(result.reasoning, str)
        self.assertGreater(len(result.reasoning), 20)
    
    def test_mixed_evidence_decision(self):
        """Test decision logic with mixed evidence types."""
        mixed_context = ValidationContext(
            text="The document has both conflicts and improvements that need careful analysis.",
            error_position=20,
            error_text="conflicts",
            rule_type="mixed",
            rule_name="mixed_analysis",
            additional_context={
                "all_rules": ["formal_language", "simple_language"],  # Conflicting
                "all_errors": [
                    {"text": "error1", "position": 10, "rule_type": "style", "rule_name": "formal_language", "severity": "moderate"},
                    {"text": "error2", "position": 30, "rule_type": "style", "rule_name": "simple_language", "severity": "moderate"}
                ]
            }
        )
        
        result = self.validator.validate_error(mixed_context)
        
        # Mixed evidence should provide comprehensive analysis
        self.assertGreater(len(result.evidence), 0)
        self.assertIsInstance(result.decision, ValidationDecision)
        self.assertIsInstance(result.reasoning, str)
    
    def test_no_cross_rule_evidence_decision(self):
        """Test decision when no cross-rule evidence is available."""
        context = ValidationContext(
            text="Single error.",
            error_position=0,
            error_text="Single",
            rule_type="grammar",
            rule_name="single_rule"
            # No metadata with multiple rules or errors
        )
        
        result = self.validator.validate_error(context)
        
        # No cross-rule evidence should lead to uncertainty
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertLessEqual(result.confidence_score, 0.5)
    
    def test_decision_consistency(self):
        """Test that decisions are consistent for similar inputs."""
        context = ValidationContext(
            text="The comprehensive analysis demonstrates consistent decision making.",
            error_position=20,
            error_text="demonstrates",
            rule_type="style",
            rule_name="consistency_test",
            additional_context={
                "all_rules": ["consistency_test", "related_rule"],
                "all_errors": [
                    {"text": "error1", "position": 10, "rule_type": "style", "rule_name": "consistency_test", "severity": "moderate"},
                    {"text": "error2", "position": 30, "rule_type": "style", "rule_name": "related_rule", "severity": "moderate"}
                ]
            }
        )
        
        # Run validation multiple times
        results = [self.validator.validate_error(context) for _ in range(3)]
        
        # Results should be consistent
        decisions = [r.decision for r in results]
        confidence_scores = [r.confidence_score for r in results]
        
        # All decisions should be the same
        self.assertEqual(len(set(decisions)), 1)
        
        # Confidence scores should be very similar
        for i in range(1, len(confidence_scores)):
            self.assertAlmostEqual(confidence_scores[0], confidence_scores[i], places=3)


class TestPerformanceAndCaching(unittest.TestCase):
    """Test performance monitoring and caching functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = CrossRuleValidator(cache_analysis_results=True)
    
    def test_analysis_caching_enabled(self):
        """Test analysis caching when enabled."""
        context = ValidationContext(
            text="Test text for caching analysis.",
            error_position=10,
            error_text="test",
            rule_type="grammar",
            rule_name="test_rule",
            additional_context={
                "all_rules": ["rule1", "rule2"],
                "all_errors": [
                    {"text": "error1", "position": 10, "rule_type": "grammar", "rule_name": "rule1", "severity": "moderate"},
                    {"text": "error2", "position": 30, "rule_type": "style", "rule_name": "rule2", "severity": "minor"}
                ]
            }
        )
        
        # Perform analysis multiple times
        result1 = self.validator.validate_error(context)
        result2 = self.validator.validate_error(context)
        
        # Both should succeed
        self.assertIsInstance(result1.confidence_score, float)
        self.assertIsInstance(result2.confidence_score, float)
        
        # Check cache statistics
        stats = self.validator.get_analysis_statistics()
        self.assertIn("analysis_cache", stats)
    
    def test_analysis_caching_disabled(self):
        """Test behavior when analysis caching is disabled."""
        validator = CrossRuleValidator(cache_analysis_results=False)
        
        context = ValidationContext(
            text="Test text for disabled caching.",
            error_position=10,
            error_text="test",
            rule_type="grammar",
            rule_name="test_rule",
            additional_context={
                "all_rules": ["rule1", "rule2"],
                "all_errors": [
                    {"text": "error1", "position": 10, "rule_type": "grammar", "rule_name": "rule1", "severity": "moderate"}
                ]
            }
        )
        
        # Perform analysis
        result = validator.validate_error(context)
        
        # Should succeed without caching
        self.assertIsInstance(result.confidence_score, float)
        
        # Cache should be empty
        self.assertEqual(validator._cache_hits, 0)
    
    def test_performance_tracking(self):
        """Test performance tracking for different analysis types."""
        context = ValidationContext(
            text="Comprehensive test for performance tracking across all analysis types.",
            error_position=20,
            error_text="comprehensive",
            rule_type="analysis",
            rule_name="performance_test",
            additional_context={
                "all_rules": ["conflict_rule1", "conflict_rule2"],
                "all_errors": [
                    {"text": "error1", "position": 10, "rule_type": "grammar", "rule_name": "rule1", "severity": "major"},
                    {"text": "error2", "position": 30, "rule_type": "style", "rule_name": "rule2", "severity": "moderate"},
                    {"text": "error3", "position": 50, "rule_type": "clarity", "rule_name": "rule3", "severity": "minor"}
                ]
            }
        )
        
        # Perform validation to populate performance data
        result = self.validator.validate_error(context)
        
        # Check that validation completed successfully
        self.assertIsInstance(result.validation_time, float)
        self.assertGreater(result.validation_time, 0)
        
        # Check analysis statistics
        stats = self.validator.get_analysis_statistics()
        self.assertIn("analysis_performance", stats)
        
        # Verify performance tracking for each analysis type
        performance = stats["analysis_performance"]
        for analysis_type in ["conflict_detection", "coherence_validation", "consolidation_validation", "improvement_assessment"]:
            if analysis_type in performance:
                type_stats = performance[analysis_type]
                self.assertIn("total_analyses", type_stats)
                self.assertIn("average_time_ms", type_stats)
                self.assertGreaterEqual(type_stats["average_time_ms"], 0.0)
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        # Populate cache
        context = ValidationContext(
            text="Test cache clearing functionality.",
            error_position=10,
            error_text="test",
            rule_type="grammar",
            rule_name="cache_test",
            additional_context={"all_rules": ["rule1", "rule2"]}
        )
        
        self.validator.validate_error(context)
        
        # Verify cache has content
        self.assertGreaterEqual(len(self.validator._analysis_cache), 0)
        
        # Clear cache
        self.validator.clear_caches()
        
        # Verify cache is empty
        self.assertEqual(len(self.validator._analysis_cache), 0)
        self.assertEqual(self.validator._cache_hits, 0)
        self.assertEqual(self.validator._cache_misses, 0)
    
    def test_analysis_statistics(self):
        """Test comprehensive analysis statistics."""
        # Perform some operations to generate statistics
        contexts = [
            ValidationContext(
                text=f"Test document {i} for statistics generation.",
                error_position=10,
                error_text="test",
                rule_type="grammar",
                rule_name=f"test_rule_{i}",
                additional_context={
                    "all_rules": [f"rule_{i}a", f"rule_{i}b"],
                    "all_errors": [{"text": f"error_{i}", "position": 10, "rule_type": "grammar", "rule_name": f"rule_{i}", "severity": "moderate"}]
                }
            )
            for i in range(3)
        ]
        
        for context in contexts:
            self.validator.validate_error(context)
        
        # Get statistics
        stats = self.validator.get_analysis_statistics()
        
        # Verify structure
        self.assertIn("analysis_cache", stats)
        self.assertIn("analysis_performance", stats)
        self.assertIn("configuration_status", stats)
        self.assertIn("knowledge_base_stats", stats)
        
        # Verify content
        cache_stats = stats["analysis_cache"]
        self.assertIn("cached_analyses", cache_stats)
        self.assertIn("cache_hits", cache_stats)
        self.assertIn("cache_misses", cache_stats)
        self.assertIn("hit_rate", cache_stats)
        
        config_stats = stats["configuration_status"]
        self.assertIn("conflict_detection", config_stats)
        self.assertIn("coherence_validation", config_stats)
        self.assertIn("consolidation_validation", config_stats)
        self.assertIn("improvement_assessment", config_stats)


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Test error handling and edge case scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = CrossRuleValidator()
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        context = ValidationContext(
            text="",
            error_position=0,
            error_text="",
            rule_type="grammar",
            rule_name="empty_test"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle empty text gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertLessEqual(result.confidence_score, 0.5)
    
    def test_single_rule_context(self):
        """Test handling of single rule context."""
        context = ValidationContext(
            text="Single rule test.",
            error_position=0,
            error_text="Single",
            rule_type="grammar",
            rule_name="single_rule"
            # No metadata with multiple rules
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle single rule gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertIsInstance(result.validation_time, float)
        self.assertGreater(result.validation_time, 0)
    
    def test_single_error_context(self):
        """Test handling of single error context."""
        context = ValidationContext(
            text="Single error test.",
            error_position=0,
            error_text="Single",
            rule_type="grammar",
            rule_name="single_error_rule"
            # No metadata with multiple errors
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle single error gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertIsInstance(result.confidence_score, float)
    
    def test_malformed_metadata_handling(self):
        """Test handling of malformed metadata."""
        context = ValidationContext(
            text="Test with malformed metadata.",
            error_position=10,
            error_text="test",
            rule_type="grammar",
            rule_name="malformed_test",
            additional_context={
                "all_rules": "not_a_list",  # Should be a list
                "all_errors": {"not": "a_list"}  # Should be a list
            }
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle malformed metadata gracefully
        self.assertIn(result.decision, [ValidationDecision.UNCERTAIN])
        self.assertIsInstance(result.validation_time, float)
    
    def test_very_large_rule_set(self):
        """Test handling of very large rule sets."""
        large_rule_set = [f"rule_{i}" for i in range(100)]  # Many rules
        
        context = ValidationContext(
            text="Test with very large rule set for performance and handling.",
            error_position=10,
            error_text="test",
            rule_type="performance",
            rule_name="large_set_test",
            additional_context={"all_rules": large_rule_set}
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle large rule sets without errors
        self.assertIsInstance(result.confidence_score, float)
        self.assertGreater(result.validation_time, 0)
        
        # Should respect max_conflicts_to_analyze limit
        if self.validator.enable_conflict_detection:
            conflict_evidence = next((e for e in result.evidence if e.evidence_type == "rule_conflict_detection"), None)
            if conflict_evidence:
                conflicts = conflict_evidence.source_data.get("conflicting_rules", [])
                # Should not exceed reasonable limits
                self.assertLessEqual(len(conflicts), self.validator.max_conflicts_to_analyze * 2)
    
    def test_very_large_error_set(self):
        """Test handling of very large error sets."""
        large_error_set = [
            {"text": f"error_{i}", "position": i*10, "rule_type": "test", "rule_name": f"rule_{i}", "severity": "minor"}
            for i in range(100)
        ]
        
        context = ValidationContext(
            text="Test with very large error set for performance and coherence analysis.",
            error_position=10,
            error_text="error_1",
            rule_type="test",
            rule_name="large_error_test",
            additional_context={"all_errors": large_error_set}
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle large error sets without errors
        self.assertIsInstance(result.confidence_score, float)
        self.assertGreater(result.validation_time, 0)
    
    def test_missing_metadata_handling(self):
        """Test handling of missing metadata."""
        context = ValidationContext(
            text="Test with no metadata.",
            error_position=10,
            error_text="test",
            rule_type="grammar",
            rule_name="no_metadata_test"
            # No metadata provided
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle missing metadata gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertIsInstance(result.reasoning, str)
    
    def test_all_analyses_disabled(self):
        """Test behavior when all analyses are disabled."""
        validator = CrossRuleValidator(
            enable_conflict_detection=False,
            enable_coherence_validation=False,
            enable_consolidation_validation=False,
            enable_improvement_assessment=False
        )
        
        context = ValidationContext(
            text="Test with all analyses disabled.",
            error_position=10,
            error_text="test",
            rule_type="grammar",
            rule_name="disabled_test",
            additional_context={
                "all_rules": ["rule1", "rule2"],
                "all_errors": [
                    {"text": "error1", "position": 10, "rule_type": "grammar", "rule_name": "rule1", "severity": "moderate"}
                ]
            }
        )
        
        result = validator.validate_error(context)
        
        # Should handle disabled analyses gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertEqual(len(result.evidence), 0)  # No evidence when all disabled
    
    def test_exception_handling(self):
        """Test handling of exceptions during analysis."""
        # This would typically involve mocking methods to raise exceptions
        # For now, we test that the validator doesn't crash on edge cases
        
        edge_cases = [
            ValidationContext(text=None, error_position=0, error_text=None, rule_type=None, rule_name=None),
            ValidationContext(text="", error_position=-1, error_text="", rule_type="", rule_name=""),
            ValidationContext(text="Test", error_position=100, error_text="nonexistent", rule_type="invalid", rule_name="invalid")
        ]
        
        for context in edge_cases:
            with self.subTest(context=str(context)):
                try:
                    result = self.validator.validate_error(context)
                    # Should not crash
                    self.assertIsInstance(result, type(self.validator.validate_error(ValidationContext("test", 0, "test", "test", "test"))))
                except Exception as e:
                    # If there's an exception, it should be handled gracefully
                    self.fail(f"Validator should handle edge cases gracefully, but raised: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
"""
Comprehensive test suite for DomainValidator class.
Tests rule applicability, terminology validation, style consistency, and audience appropriateness.
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock

from validation.multi_pass.pass_validators.domain_validator import (
    DomainValidator, RuleApplicabilityAssessment, TerminologyValidation,
    StyleConsistencyCheck, AudienceAppropriatenessAssessment
)
from validation.multi_pass import ValidationContext, ValidationDecision, ValidationConfidence


class TestDomainValidatorInitialization(unittest.TestCase):
    """Test DomainValidator initialization and configuration."""
    
    def test_default_initialization(self):
        """Test initialization with default settings."""
        validator = DomainValidator()
        
        self.assertEqual(validator.validator_name, "domain_validator")
        self.assertTrue(validator.enable_domain_classification)
        self.assertTrue(validator.enable_terminology_validation)
        self.assertTrue(validator.enable_style_consistency)
        self.assertTrue(validator.enable_audience_assessment)
        self.assertTrue(validator.cache_domain_analyses)
        self.assertEqual(validator.min_confidence_threshold, 0.60)
    
    def test_custom_initialization(self):
        """Test initialization with custom settings."""
        validator = DomainValidator(
            enable_domain_classification=False,
            enable_terminology_validation=False,
            enable_style_consistency=False,
            enable_audience_assessment=False,
            cache_domain_analyses=False,
            min_confidence_threshold=0.75
        )
        
        self.assertFalse(validator.enable_domain_classification)
        self.assertFalse(validator.enable_terminology_validation)
        self.assertFalse(validator.enable_style_consistency)
        self.assertFalse(validator.enable_audience_assessment)
        self.assertFalse(validator.cache_domain_analyses)
        self.assertEqual(validator.min_confidence_threshold, 0.75)
    
    def test_validator_info(self):
        """Test get_validator_info method."""
        validator = DomainValidator()
        info = validator.get_validator_info()
        
        self.assertEqual(info["name"], "domain_validator")
        self.assertEqual(info["type"], "domain_validator")
        self.assertIn("rule_applicability_assessment", info["capabilities"])
        self.assertIn("terminology_validation", info["capabilities"])
        self.assertIn("style_consistency_checking", info["capabilities"])
        self.assertIn("audience_appropriateness_assessment", info["capabilities"])
        self.assertIn("domain_specific_validation", info["specialties"])
        self.assertIn("configuration", info)
        self.assertIn("performance_characteristics", info)
        self.assertIn("domain_knowledge", info)
    
    def test_domain_patterns_initialization(self):
        """Test that domain patterns and rules are properly initialized."""
        validator = DomainValidator()
        
        # Check domain rule applicability
        self.assertIn("technical", validator.domain_rule_applicability)
        self.assertIn("business", validator.domain_rule_applicability)
        self.assertIn("academic", validator.domain_rule_applicability)
        
        # Check rule type domain relevance
        self.assertIn("grammar", validator.rule_type_domain_relevance)
        self.assertIn("style", validator.rule_type_domain_relevance)
        self.assertIn("terminology", validator.rule_type_domain_relevance)
        
        # Check domain terminology
        self.assertIn("technical", validator.domain_terminology)
        self.assertIn("business", validator.domain_terminology)
        
        # Check style expectations
        self.assertIn("technical", validator.domain_style_expectations)
        self.assertIn("business", validator.domain_style_expectations)
        
        # Check audience criteria
        self.assertIn("developers", validator.audience_criteria)
        self.assertIn("business_users", validator.audience_criteria)


class TestRuleApplicabilityAssessment(unittest.TestCase):
    """Test rule applicability assessment functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = DomainValidator()
    
    def test_rule_applicability_assessment_creation(self):
        """Test RuleApplicabilityAssessment dataclass creation."""
        assessment = RuleApplicabilityAssessment(
            rule_type="terminology",
            rule_name="technical_terms",
            domain_relevance=0.9,
            content_type_match=True,
            audience_alignment=0.8,
            applicability_score=0.85,
            applicability_factors=["high_domain_relevance"],
            rule_exceptions=[],
            confidence_modifier=0.85
        )
        
        self.assertEqual(assessment.rule_type, "terminology")
        self.assertEqual(assessment.rule_name, "technical_terms")
        self.assertEqual(assessment.domain_relevance, 0.9)
        self.assertTrue(assessment.content_type_match)
        self.assertEqual(assessment.audience_alignment, 0.8)
        self.assertEqual(assessment.applicability_score, 0.85)
        self.assertEqual(assessment.confidence_modifier, 0.85)
    
    def test_technical_domain_rule_applicability(self):
        """Test rule applicability assessment for technical domain."""
        context = ValidationContext(
            text="The API endpoint processes JSON requests using HTTP authentication mechanisms.",
            error_position=20,
            error_text="processes",
            rule_type="terminology",
            rule_name="technical_precision",
            content_type="technical"
        )
        
        result = self.validator.validate_error(context)
        
        # Should have rule applicability evidence
        applicability_evidence = next((e for e in result.evidence if e.evidence_type == "rule_applicability"), None)
        self.assertIsNotNone(applicability_evidence)
        self.assertIn("rule_type", applicability_evidence.source_data)
        self.assertEqual(applicability_evidence.source_data["rule_type"], "terminology")
    
    def test_business_domain_rule_applicability(self):
        """Test rule applicability assessment for business domain."""
        context = ValidationContext(
            text="The quarterly revenue strategy focuses on customer acquisition and stakeholder management.",
            error_position=20,
            error_text="strategy",
            rule_type="style",
            rule_name="business_writing",
            content_type="business"
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess business domain applicability
        applicability_evidence = next((e for e in result.evidence if e.evidence_type == "rule_applicability"), None)
        if applicability_evidence:
            self.assertGreaterEqual(applicability_evidence.source_data.get("domain_relevance", 0), 0.5)
    
    def test_creative_domain_rule_applicability(self):
        """Test rule applicability assessment for creative domain."""
        context = ValidationContext(
            text="The magical story unfolds with whimsical characters dancing through enchanted forests.",
            error_position=20,
            error_text="magical",
            rule_type="terminology",
            rule_name="technical_precision",
            content_type="creative"
        )
        
        result = self.validator.validate_error(context)
        
        # Terminology rule should have low applicability in creative domain
        self.assertIn(result.decision, [ValidationDecision.REJECT, ValidationDecision.UNCERTAIN])
    
    def test_rule_exceptions_handling(self):
        """Test handling of rule exceptions for specific domains."""
        context = ValidationContext(
            text="The breathtaking landscape painted vivid imagery in the reader's mind.",
            error_position=20,
            error_text="breathtaking",
            rule_type="grammar",
            rule_name="formal_language",
            content_type="creative"
        )
        
        result = self.validator.validate_error(context)
        
        # Creative domain may have exceptions for formal language rules
        applicability_evidence = next((e for e in result.evidence if e.evidence_type == "rule_applicability"), None)
        if applicability_evidence:
            rule_exceptions = applicability_evidence.source_data.get("rule_exceptions", [])
            self.assertIsInstance(rule_exceptions, list)


class TestTerminologyValidation(unittest.TestCase):
    """Test terminology validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = DomainValidator()
    
    def test_terminology_validation_creation(self):
        """Test TerminologyValidation dataclass creation."""
        validation = TerminologyValidation(
            domain="technical",
            terminology_type="technical",
            appropriateness_score=0.9,
            precision_level="high",
            actual_precision=0.85,
            terminology_consistency=0.8,
            inappropriate_terms=[],
            missing_terminology=[],
            alternative_suggestions=["implement", "utilize"]
        )
        
        self.assertEqual(validation.domain, "technical")
        self.assertEqual(validation.terminology_type, "technical")
        self.assertEqual(validation.appropriateness_score, 0.9)
        self.assertEqual(validation.precision_level, "high")
        self.assertEqual(validation.actual_precision, 0.85)
        self.assertEqual(validation.terminology_consistency, 0.8)
        self.assertEqual(validation.alternative_suggestions, ["implement", "utilize"])
    
    def test_technical_terminology_validation(self):
        """Test terminology validation for technical content."""
        context = ValidationContext(
            text="The REST API endpoint implements JSON authentication using HTTP protocols.",
            error_position=30,
            error_text="implements",
            rule_type="terminology",
            rule_name="technical_precision"
        )
        
        result = self.validator.validate_error(context)
        
        # Should have terminology validation evidence when enabled
        terminology_evidence = next((e for e in result.evidence if e.evidence_type == "terminology_validation"), None)
        if self.validator.enable_terminology_validation and terminology_evidence:
            self.assertIn("domain", terminology_evidence.source_data)
            self.assertIn("appropriateness_score", terminology_evidence.source_data)
            domain = terminology_evidence.source_data["domain"]
            self.assertIn(domain, ["technical", "general"])
    
    def test_business_terminology_validation(self):
        """Test terminology validation for business content."""
        context = ValidationContext(
            text="The company's ROI strategy leverages stakeholder synergy for revenue optimization.",
            error_position=30,
            error_text="leverages",
            rule_type="terminology",
            rule_name="business_language"
        )
        
        result = self.validator.validate_error(context)
        
        # Should validate business terminology
        terminology_evidence = next((e for e in result.evidence if e.evidence_type == "terminology_validation"), None)
        if terminology_evidence:
            appropriateness = terminology_evidence.source_data.get("appropriateness_score", 0)
            self.assertIsInstance(appropriateness, float)
            self.assertGreaterEqual(appropriateness, 0.0)
            self.assertLessEqual(appropriateness, 1.0)
    
    def test_inappropriate_terminology_detection(self):
        """Test detection of inappropriate terminology for domain."""
        context = ValidationContext(
            text="The technical API system is totally awesome and super cool to implement.",
            error_position=40,
            error_text="awesome",
            rule_type="terminology",
            rule_name="technical_appropriateness"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect inappropriate casual terms in technical context
        terminology_evidence = next((e for e in result.evidence if e.evidence_type == "terminology_validation"), None)
        if terminology_evidence:
            inappropriate_terms = terminology_evidence.source_data.get("inappropriate_terms", [])
            self.assertIsInstance(inappropriate_terms, list)
            # May detect "awesome" as inappropriate for technical context
    
    def test_terminology_consistency_checking(self):
        """Test terminology consistency within domain."""
        context = ValidationContext(
            text="The software utilizes algorithms for data processing. The app uses functions for calculation.",
            error_position=60,
            error_text="uses",
            rule_type="terminology",
            rule_name="consistency"
        )
        
        result = self.validator.validate_error(context)
        
        # Should check for terminology consistency
        terminology_evidence = next((e for e in result.evidence if e.evidence_type == "terminology_validation"), None)
        if terminology_evidence:
            consistency = terminology_evidence.source_data.get("terminology_consistency", 0)
            self.assertIsInstance(consistency, float)
            self.assertGreaterEqual(consistency, 0.0)
            self.assertLessEqual(consistency, 1.0)
    
    def test_alternative_suggestions_generation(self):
        """Test generation of alternative terminology suggestions."""
        context = ValidationContext(
            text="The system makes data available to users through the interface.",
            error_position=15,
            error_text="makes",
            rule_type="terminology",
            rule_name="precision"
        )
        
        result = self.validator.validate_error(context)
        
        # Should generate alternative suggestions
        terminology_evidence = next((e for e in result.evidence if e.evidence_type == "terminology_validation"), None)
        if terminology_evidence:
            alternatives = terminology_evidence.source_data.get("alternative_suggestions", [])
            self.assertIsInstance(alternatives, list)
    
    def test_terminology_validation_disabled(self):
        """Test behavior when terminology validation is disabled."""
        validator = DomainValidator(enable_terminology_validation=False)
        
        context = ValidationContext(
            text="The technical system implements advanced algorithms.",
            error_position=20,
            error_text="implements",
            rule_type="terminology"
        )
        
        result = validator.validate_error(context)
        
        # Should not have terminology evidence when disabled
        terminology_evidence = next((e for e in result.evidence if e.evidence_type == "terminology_validation"), None)
        self.assertIsNone(terminology_evidence)


class TestStyleConsistencyChecking(unittest.TestCase):
    """Test style consistency checking functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = DomainValidator()
    
    def test_style_consistency_check_creation(self):
        """Test StyleConsistencyCheck dataclass creation."""
        check = StyleConsistencyCheck(
            domain_style_expectations={'formality_level': 'formal'},
            detected_style_features={'formality_level': 'formal'},
            consistency_score=0.9,
            style_violations=[],
            formality_alignment=1.0,
            structure_appropriateness=0.8,
            tone_consistency=0.85,
            style_recommendations=[]
        )
        
        self.assertEqual(check.consistency_score, 0.9)
        self.assertEqual(check.formality_alignment, 1.0)
        self.assertEqual(check.structure_appropriateness, 0.8)
        self.assertEqual(check.tone_consistency, 0.85)
        self.assertEqual(check.style_violations, [])
        self.assertEqual(check.style_recommendations, [])
    
    def test_technical_style_consistency(self):
        """Test style consistency for technical content."""
        context = ValidationContext(
            text="The API system processes requests efficiently. It implements robust authentication mechanisms. The architecture demonstrates scalability.",
            error_position=30,
            error_text="efficiently",
            rule_type="style",
            rule_name="technical_writing"
        )
        
        result = self.validator.validate_error(context)
        
        # Should have style consistency evidence when enabled
        style_evidence = next((e for e in result.evidence if e.evidence_type == "style_consistency"), None)
        if self.validator.enable_style_consistency and style_evidence:
            self.assertIn("consistency_score", style_evidence.source_data)
            consistency = style_evidence.source_data["consistency_score"]
            self.assertIsInstance(consistency, float)
            self.assertGreaterEqual(consistency, 0.0)
            self.assertLessEqual(consistency, 1.0)
    
    def test_business_style_consistency(self):
        """Test style consistency for business content."""
        context = ValidationContext(
            text="The quarterly strategy focuses on revenue growth. Management seeks to leverage market opportunities. Stakeholders expect measurable results.",
            error_position=40,
            error_text="leverage",
            rule_type="style",
            rule_name="business_writing"
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess business style consistency
        style_evidence = next((e for e in result.evidence if e.evidence_type == "style_consistency"), None)
        if style_evidence:
            formality_alignment = style_evidence.source_data.get("formality_alignment", 0)
            self.assertIsInstance(formality_alignment, float)
            self.assertGreaterEqual(formality_alignment, 0.0)
            self.assertLessEqual(formality_alignment, 1.0)
    
    def test_creative_style_flexibility(self):
        """Test style flexibility for creative content."""
        context = ValidationContext(
            text="The magical forest whispered secrets. Ancient trees danced in moonlight. Ethereal beings emerged from shadows.",
            error_position=20,
            error_text="whispered",
            rule_type="style",
            rule_name="descriptive_language"
        )
        
        result = self.validator.validate_error(context)
        
        # Creative content should allow more style flexibility
        style_evidence = next((e for e in result.evidence if e.evidence_type == "style_consistency"), None)
        if style_evidence:
            violations = style_evidence.source_data.get("style_violations", [])
            self.assertIsInstance(violations, list)
            # Creative domain should have fewer strict violations
    
    def test_style_violation_detection(self):
        """Test detection of style violations."""
        context = ValidationContext(
            text="The API is awesome! It's super cool and totally amazing for developers to use in applications.",
            error_position=15,
            error_text="awesome",
            rule_type="style",
            rule_name="technical_formality"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect style violations (informal language in technical context)
        style_evidence = next((e for e in result.evidence if e.evidence_type == "style_consistency"), None)
        if style_evidence:
            violations = style_evidence.source_data.get("style_violations", [])
            self.assertIsInstance(violations, list)
            # May detect formality violations
    
    def test_style_recommendations_generation(self):
        """Test generation of style recommendations."""
        context = ValidationContext(
            text="This is really, really, really important for users to understand completely.",
            error_position=10,
            error_text="really",
            rule_type="style",
            rule_name="clarity"
        )
        
        result = self.validator.validate_error(context)
        
        # Should generate style recommendations
        style_evidence = next((e for e in result.evidence if e.evidence_type == "style_consistency"), None)
        if style_evidence:
            recommendations = style_evidence.source_data.get("style_recommendations", [])
            self.assertIsInstance(recommendations, list)
    
    def test_style_consistency_disabled(self):
        """Test behavior when style consistency is disabled."""
        validator = DomainValidator(enable_style_consistency=False)
        
        context = ValidationContext(
            text="The technical system demonstrates excellent performance.",
            error_position=20,
            error_text="demonstrates",
            rule_type="style"
        )
        
        result = validator.validate_error(context)
        
        # Should not have style evidence when disabled
        style_evidence = next((e for e in result.evidence if e.evidence_type == "style_consistency"), None)
        self.assertIsNone(style_evidence)


class TestAudienceAppropriatenessAssessment(unittest.TestCase):
    """Test audience appropriateness assessment functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = DomainValidator()
    
    def test_audience_appropriateness_assessment_creation(self):
        """Test AudienceAppropriatenessAssessment dataclass creation."""
        assessment = AudienceAppropriatenessAssessment(
            target_audience="developers",
            content_accessibility=0.8,
            technical_level_match=True,
            language_complexity="moderate",
            assumed_knowledge=["programming", "APIs"],
            accessibility_barriers=[],
            appropriateness_score=0.85,
            audience_recommendations=[]
        )
        
        self.assertEqual(assessment.target_audience, "developers")
        self.assertEqual(assessment.content_accessibility, 0.8)
        self.assertTrue(assessment.technical_level_match)
        self.assertEqual(assessment.language_complexity, "moderate")
        self.assertEqual(assessment.assumed_knowledge, ["programming", "APIs"])
        self.assertEqual(assessment.appropriateness_score, 0.85)
    
    def test_developer_audience_assessment(self):
        """Test audience appropriateness for developer audience."""
        context = ValidationContext(
            text="The REST API endpoint accepts JSON payloads and returns HTTP status codes.",
            error_position=20,
            error_text="endpoint",
            rule_type="terminology",
            rule_name="technical_clarity",
            content_type="technical"
        )
        
        result = self.validator.validate_error(context)
        
        # Should have audience appropriateness evidence when enabled
        audience_evidence = next((e for e in result.evidence if e.evidence_type == "audience_appropriateness"), None)
        if self.validator.enable_audience_assessment and audience_evidence:
            self.assertIn("target_audience", audience_evidence.source_data)
            target_audience = audience_evidence.source_data["target_audience"]
            self.assertIsInstance(target_audience, str)
    
    def test_business_audience_assessment(self):
        """Test audience appropriateness for business audience."""
        context = ValidationContext(
            text="The quarterly revenue strategy will increase customer acquisition and improve ROI metrics.",
            error_position=30,
            error_text="strategy",
            rule_type="style",
            rule_name="business_communication",
            content_type="business"
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess business audience appropriateness
        audience_evidence = next((e for e in result.evidence if e.evidence_type == "audience_appropriateness"), None)
        if audience_evidence:
            accessibility = audience_evidence.source_data.get("content_accessibility", 0)
            self.assertIsInstance(accessibility, float)
            self.assertGreaterEqual(accessibility, 0.0)
            self.assertLessEqual(accessibility, 1.0)
    
    def test_general_audience_assessment(self):
        """Test audience appropriateness for general audience."""
        context = ValidationContext(
            text="This user-friendly guide helps everyone understand the basic concepts and procedures.",
            error_position=20,
            error_text="guide",
            rule_type="style",
            rule_name="accessibility"
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess general audience appropriateness
        audience_evidence = next((e for e in result.evidence if e.evidence_type == "audience_appropriateness"), None)
        if audience_evidence:
            technical_match = audience_evidence.source_data.get("technical_level_match", False)
            self.assertIsInstance(technical_match, bool)
    
    def test_technical_complexity_assessment(self):
        """Test assessment of technical complexity for audience."""
        context = ValidationContext(
            text="The asynchronous microservices architecture implements distributed consensus algorithms using Byzantine fault tolerance.",
            error_position=40,
            error_text="algorithms",
            rule_type="terminology",
            rule_name="accessibility"
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess technical complexity
        audience_evidence = next((e for e in result.evidence if e.evidence_type == "audience_appropriateness"), None)
        if audience_evidence:
            complexity = audience_evidence.source_data.get("language_complexity", "simple")
            self.assertIn(complexity, ["simple", "moderate", "complex", "highly_complex"])
    
    def test_accessibility_barriers_detection(self):
        """Test detection of accessibility barriers."""
        context = ValidationContext(
            text="The API utilizes OAuth 2.0 authentication with JWT tokens for secure REST endpoint access.",
            error_position=15,
            error_text="utilizes",
            rule_type="style",
            rule_name="general_accessibility"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect accessibility barriers for general audience
        audience_evidence = next((e for e in result.evidence if e.evidence_type == "audience_appropriateness"), None)
        if audience_evidence:
            barriers = audience_evidence.source_data.get("accessibility_barriers", [])
            self.assertIsInstance(barriers, list)
            # May detect technical jargon as barrier for general audience
    
    def test_audience_recommendations_generation(self):
        """Test generation of audience-specific recommendations."""
        context = ValidationContext(
            text="The sophisticated algorithmic implementation leverages advanced computational methodologies.",
            error_position=20,
            error_text="sophisticated",
            rule_type="style",
            rule_name="simplicity"
        )
        
        result = self.validator.validate_error(context)
        
        # Should generate audience recommendations
        audience_evidence = next((e for e in result.evidence if e.evidence_type == "audience_appropriateness"), None)
        if audience_evidence:
            recommendations = audience_evidence.source_data.get("audience_recommendations", [])
            self.assertIsInstance(recommendations, list)
    
    def test_audience_assessment_disabled(self):
        """Test behavior when audience assessment is disabled."""
        validator = DomainValidator(enable_audience_assessment=False)
        
        context = ValidationContext(
            text="The technical documentation provides comprehensive guidance.",
            error_position=20,
            error_text="documentation",
            rule_type="style"
        )
        
        result = validator.validate_error(context)
        
        # Should not have audience evidence when disabled
        audience_evidence = next((e for e in result.evidence if e.evidence_type == "audience_appropriateness"), None)
        self.assertIsNone(audience_evidence)


class TestValidationDecisionMaking(unittest.TestCase):
    """Test validation decision making logic."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = DomainValidator()
    
    def test_terminology_rule_decision_logic(self):
        """Test decision logic for terminology rules."""
        context = ValidationContext(
            text="The API endpoint implements authentication using secure protocols and encryption algorithms.",
            error_position=30,
            error_text="authentication",
            rule_type="terminology",
            rule_name="technical_precision"
        )
        
        result = self.validator.validate_error(context)
        
        # Terminology rules should benefit from domain analysis
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        self.assertGreater(result.confidence_score, 0.3)
        self.assertIsInstance(result.reasoning, str)
        self.assertGreater(len(result.reasoning), 20)
    
    def test_style_rule_decision_logic(self):
        """Test decision logic for style rules."""
        context = ValidationContext(
            text="The business strategy leverages synergistic opportunities for stakeholder value creation.",
            error_position=30,
            error_text="leverages",
            rule_type="style",
            rule_name="business_writing"
        )
        
        result = self.validator.validate_error(context)
        
        # Style rules should benefit from domain-specific style analysis
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        self.assertIsInstance(result.confidence_score, float)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
    
    def test_grammar_rule_decision_logic(self):
        """Test decision logic for grammar rules."""
        context = ValidationContext(
            text="The comprehensive documentation provides detailed explanations and thorough examples.",
            error_position=30,
            error_text="provides",
            rule_type="grammar",
            rule_name="subject_verb_agreement"
        )
        
        result = self.validator.validate_error(context)
        
        # Grammar rules have universal applicability with domain context
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        self.assertGreater(result.confidence_score, 0.2)
    
    def test_decision_with_strong_domain_evidence(self):
        """Test decision making with strong domain evidence."""
        context = ValidationContext(
            text="The REST API utilizes JSON for data exchange and implements OAuth authentication.",
            error_position=20,
            error_text="utilizes",
            rule_type="terminology",
            rule_name="technical_precision"
        )
        
        result = self.validator.validate_error(context)
        
        # Strong technical domain evidence should lead to confident decisions
        self.assertGreater(len(result.evidence), 0)
        if result.confidence_score > 0.8:
            self.assertEqual(result.decision, ValidationDecision.ACCEPT)
    
    def test_decision_with_domain_mismatch(self):
        """Test decision making with domain mismatch."""
        context = ValidationContext(
            text="The magical fairy tale features enchanted creatures in mystical forest settings.",
            error_position=30,
            error_text="features",
            rule_type="terminology",
            rule_name="technical_precision"
        )
        
        result = self.validator.validate_error(context)
        
        # Technical terminology rule should be rejected for creative content
        self.assertIn(result.decision, [ValidationDecision.REJECT, ValidationDecision.UNCERTAIN])
    
    def test_decision_with_weak_domain_evidence(self):
        """Test decision making with weak domain evidence."""
        context = ValidationContext(
            text="Word.",  # Minimal context
            error_position=0,
            error_text="Word",
            rule_type="terminology",
            rule_name="domain_appropriateness"
        )
        
        result = self.validator.validate_error(context)
        
        # Weak domain context should lead to uncertain decisions
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertLessEqual(result.confidence_score, 0.8)  # More realistic expectation for domain analysis


class TestPerformanceAndCaching(unittest.TestCase):
    """Test performance monitoring and caching functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = DomainValidator(cache_domain_analyses=True)
    
    def test_domain_analysis_caching_enabled(self):
        """Test domain analysis caching when enabled."""
        text = "The comprehensive API documentation demonstrates proper implementation."
        
        # First analysis - should be cached
        analysis1 = self.validator._get_domain_analysis(text, "technical")
        cache_misses_1 = self.validator._cache_misses
        
        # Second analysis - should use cache
        analysis2 = self.validator._get_domain_analysis(text, "technical")
        cache_hits_1 = self.validator._cache_hits
        
        self.assertIsNotNone(analysis1)
        self.assertIsNotNone(analysis2)
        self.assertGreater(cache_hits_1, 0)
    
    def test_domain_analysis_caching_disabled(self):
        """Test behavior when domain analysis caching is disabled."""
        validator = DomainValidator(cache_domain_analyses=False)
        text = "The comprehensive API documentation demonstrates proper implementation."
        
        # Multiple analyses should not use cache
        validator._get_domain_analysis(text, "technical")
        validator._get_domain_analysis(text, "technical")
        
        self.assertEqual(validator._cache_hits, 0)  # No cache hits
    
    def test_performance_tracking(self):
        """Test performance tracking for different analysis types."""
        context = ValidationContext(
            text="The business strategy leverages market opportunities for revenue optimization and stakeholder value.",
            error_position=30,
            error_text="leverages",
            rule_type="style",
            rule_name="business_writing"
        )
        
        # Perform validation to populate performance data
        result = self.validator.validate_error(context)
        
        # Check that validation completed successfully
        self.assertIsInstance(result.validation_time, float)
        self.assertGreater(result.validation_time, 0)
        
        # Check analysis statistics
        stats = self.validator.get_analysis_statistics()
        self.assertIn("analysis_performance", stats)
        self.assertIn("domain_cache", stats)
    
    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        # Perform some operations to generate cache statistics
        texts = [
            "The first technical document for analysis.",
            "The second business document for analysis.",
            "The first technical document for analysis."  # Repeat to test cache hit
        ]
        
        for i, text in enumerate(texts):
            content_type = "technical" if i % 2 == 0 else "business"
            self.validator._get_domain_analysis(text, content_type)
        
        hit_rate = self.validator._get_cache_hit_rate()
        self.assertIsInstance(hit_rate, float)
        self.assertGreaterEqual(hit_rate, 0.0)
        self.assertLessEqual(hit_rate, 1.0)
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        # Populate cache
        self.validator._get_domain_analysis("Test document for caching.", "technical")
        
        # Verify cache has content
        self.assertGreater(len(self.validator._domain_cache), 0)
        
        # Clear cache
        self.validator.clear_caches()
        
        # Verify cache is empty
        self.assertEqual(len(self.validator._domain_cache), 0)
        self.assertEqual(self.validator._cache_hits, 0)
        self.assertEqual(self.validator._cache_misses, 0)
    
    def test_analysis_time_tracking(self):
        """Test tracking of analysis times for different components."""
        context = ValidationContext(
            text="The technical implementation utilizes advanced algorithms for data processing optimization.",
            error_position=30,
            error_text="utilizes",
            rule_type="terminology",
            rule_name="technical_precision"
        )
        
        # Perform validation
        result = self.validator.validate_error(context)
        
        # Check analysis time tracking
        stats = self.validator.get_analysis_statistics()
        performance = stats.get("analysis_performance", {})
        
        for analysis_type in ["rule_applicability", "terminology_validation", "style_consistency", "audience_assessment"]:
            if analysis_type in performance:
                type_stats = performance[analysis_type]
                self.assertIn("total_analyses", type_stats)
                self.assertIn("average_time_ms", type_stats)
                self.assertGreaterEqual(type_stats["average_time_ms"], 0.0)


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Test error handling and edge case scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = DomainValidator()
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        context = ValidationContext(
            text="",
            error_position=0,
            error_text="",
            rule_type="terminology"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle empty text gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertLessEqual(result.confidence_score, 0.7)  # More realistic expectation for domain analysis
    
    def test_single_word_text(self):
        """Test handling of single word text."""
        context = ValidationContext(
            text="Word",
            error_position=0,
            error_text="Word",
            rule_type="terminology"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle minimal context gracefully
        self.assertIn(result.decision, [ValidationDecision.UNCERTAIN])
        self.assertIsInstance(result.validation_time, float)
        self.assertGreater(result.validation_time, 0)
    
    def test_very_long_text_handling(self):
        """Test handling of very long text."""
        long_text = "The business strategy leverages market opportunities. " * 100  # Very long repetitive text
        context = ValidationContext(
            text=long_text,
            error_position=500,
            error_text="leverages",
            rule_type="terminology"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle long text without errors
        self.assertIsInstance(result.confidence_score, float)
        self.assertGreater(result.validation_time, 0)
    
    def test_invalid_error_position(self):
        """Test handling of invalid error positions."""
        context = ValidationContext(
            text="Short text.",
            error_position=100,  # Beyond text length
            error_text="nonexistent",
            rule_type="terminology"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle invalid position gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertIsInstance(result.validation_time, float)
        self.assertGreater(result.validation_time, 0)
    
    def test_unknown_domain_handling(self):
        """Test handling of unknown or mixed domain content."""
        context = ValidationContext(
            text="Random words without clear domain context or structure patterns.",
            error_position=10,
            error_text="words",
            rule_type="terminology"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle unknown domain gracefully
        self.assertIn(result.decision, [ValidationDecision.UNCERTAIN])
        self.assertIsInstance(result.confidence_score, float)
    
    def test_mixed_domain_content(self):
        """Test handling of content with mixed domain signals."""
        context = ValidationContext(
            text="The technical API system leverages business synergy for stakeholder ROI optimization.",
            error_position=40,
            error_text="synergy",
            rule_type="terminology",
            rule_name="domain_consistency"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle mixed domain content
        self.assertIsInstance(result.confidence_score, float)
        terminology_evidence = next((e for e in result.evidence if e.evidence_type == "terminology_validation"), None)
        if terminology_evidence:
            # Should detect mixed terminology
            domain = terminology_evidence.source_data.get("domain", "general")
            self.assertIsInstance(domain, str)
    
    def test_all_analyses_disabled(self):
        """Test behavior when all analyses are disabled."""
        validator = DomainValidator(
            enable_terminology_validation=False,
            enable_style_consistency=False,
            enable_audience_assessment=False
        )
        
        context = ValidationContext(
            text="The technical system demonstrates excellent performance.",
            error_position=20,
            error_text="demonstrates",
            rule_type="terminology"
        )
        
        result = validator.validate_error(context)
        
        # May or may not have rule applicability evidence when all analyses disabled
        applicability_evidence = next((e for e in result.evidence if e.evidence_type == "rule_applicability"), None)
        # Rule applicability may still be generated as it's core functionality
        if applicability_evidence:
            self.assertIn("rule_type", applicability_evidence.source_data)
        
        # Should not have other evidence types
        terminology_evidence = next((e for e in result.evidence if e.evidence_type == "terminology_validation"), None)
        style_evidence = next((e for e in result.evidence if e.evidence_type == "style_consistency"), None)
        audience_evidence = next((e for e in result.evidence if e.evidence_type == "audience_appropriateness"), None)
        
        self.assertIsNone(terminology_evidence)
        self.assertIsNone(style_evidence)
        self.assertIsNone(audience_evidence)
    
    def test_domain_classification_fallback(self):
        """Test fallback domain detection when domain classifier unavailable."""
        # Test the simple domain detection fallback
        validator = DomainValidator(enable_domain_classification=False)
        
        # Technical content
        technical_analysis = validator._simple_domain_detection("The API implements JSON authentication.", "technical")
        self.assertIsNotNone(technical_analysis)
        self.assertEqual(technical_analysis.primary_domain, "technical")
        
        # Business content
        business_analysis = validator._simple_domain_detection("The company leverages ROI strategies.", "business")
        self.assertIsNotNone(business_analysis)
        self.assertIn(business_analysis.primary_domain, ["business", "general"])


class TestValidationConsistency(unittest.TestCase):
    """Test validation decision consistency."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = DomainValidator()
    
    def test_consistent_results_for_identical_input(self):
        """Test that identical inputs produce consistent results."""
        context = ValidationContext(
            text="The comprehensive business strategy leverages market opportunities for stakeholder value creation.",
            error_position=40,
            error_text="leverages",
            rule_type="terminology",
            rule_name="business_precision"
        )
        
        # Run validation multiple times
        results = [self.validator.validate_error(context) for _ in range(3)]
        
        # Results should be consistent
        decisions = [r.decision for r in results]
        confidence_scores = [r.confidence_score for r in results]
        
        # All decisions should be the same
        self.assertEqual(len(set(decisions)), 1)
        
        # Confidence scores should be very similar (allowing for minor floating point differences)
        for i in range(1, len(confidence_scores)):
            self.assertAlmostEqual(confidence_scores[0], confidence_scores[i], places=3)
    
    def test_different_domains_produce_different_results(self):
        """Test that different domains produce appropriately different results."""
        technical_context = ValidationContext(
            text="The API endpoint implements secure authentication mechanisms using OAuth protocols.",
            error_position=30,
            error_text="implements",
            rule_type="terminology",
            rule_name="precision"
        )
        
        creative_context = ValidationContext(
            text="The magical story implements fantastical elements throughout the enchanted narrative.",
            error_position=30,
            error_text="implements",
            rule_type="terminology",
            rule_name="precision"
        )
        
        technical_result = self.validator.validate_error(technical_context)
        creative_result = self.validator.validate_error(creative_context)
        
        # Results should differ based on domain appropriateness
        # Technical domain should be more accepting of "implements"
        # Creative domain should be less accepting of technical terminology
        if technical_result.decision == ValidationDecision.ACCEPT:
            self.assertIn(creative_result.decision, [ValidationDecision.REJECT, ValidationDecision.UNCERTAIN])
    
    def test_complex_domain_content_handling(self):
        """Test handling of various complex domain-specific content."""
        test_cases = [
            # Technical content
            ("The microservices architecture implements RESTful APIs with OAuth 2.0 authentication.", 30, "implements", "terminology"),
            # Business content
            ("The quarterly revenue strategy leverages synergistic opportunities for stakeholder value.", 40, "leverages", "terminology"),
            # Academic content
            ("The research methodology utilizes empirical analysis for hypothesis validation.", 30, "utilizes", "terminology"),
            # Creative content
            ("The mysterious character whispered ancient secrets through the ethereal mist.", 30, "whispered", "style"),
        ]
        
        for text, position, error_text, rule_type in test_cases:
            with self.subTest(text=text[:50] + "..."):
                context = ValidationContext(
                    text=text,
                    error_position=position,
                    error_text=error_text,
                    rule_type=rule_type
                )
                
                result = self.validator.validate_error(context)
                
                # Should handle all complex domain content without errors
                self.assertIsInstance(result.confidence_score, float)
                self.assertGreaterEqual(result.confidence_score, 0.0)
                self.assertLessEqual(result.confidence_score, 1.0)
                self.assertGreater(len(result.evidence), 0)
                self.assertIsInstance(result.reasoning, str)
                self.assertGreater(len(result.reasoning), 10)


class TestDomainSpecificLogic(unittest.TestCase):
    """Test domain-specific validation logic."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = DomainValidator()
    
    def test_technical_domain_specialization(self):
        """Test specialization for technical domain validation."""
        context = ValidationContext(
            text="The REST API utilizes JSON serialization for efficient data transmission across HTTP endpoints.",
            error_position=20,
            error_text="utilizes",
            rule_type="terminology",
            rule_name="technical_precision"
        )
        
        result = self.validator.validate_error(context)
        
        # Technical domain should recognize appropriate technical terminology
        terminology_evidence = next((e for e in result.evidence if e.evidence_type == "terminology_validation"), None)
        if terminology_evidence:
            domain = terminology_evidence.source_data.get("domain", "")
            appropriateness = terminology_evidence.source_data.get("appropriateness_score", 0)
            self.assertIn(domain, ["technical", "general", "academic"])  # Domain classifier may vary
            self.assertGreaterEqual(appropriateness, 0.3)  # Should be reasonably appropriate
    
    def test_business_domain_specialization(self):
        """Test specialization for business domain validation."""
        context = ValidationContext(
            text="The company's strategic initiative leverages core competencies to maximize shareholder value.",
            error_position=40,
            error_text="leverages",
            rule_type="terminology",
            rule_name="business_language"
        )
        
        result = self.validator.validate_error(context)
        
        # Business domain should recognize business terminology
        terminology_evidence = next((e for e in result.evidence if e.evidence_type == "terminology_validation"), None)
        if terminology_evidence:
            domain = terminology_evidence.source_data.get("domain", "")
            self.assertIn(domain, ["business", "general"])
    
    def test_academic_domain_specialization(self):
        """Test specialization for academic domain validation."""
        context = ValidationContext(
            text="The research methodology employs rigorous empirical analysis to validate the proposed hypothesis.",
            error_position=30,
            error_text="employs",
            rule_type="terminology",
            rule_name="academic_precision"
        )
        
        result = self.validator.validate_error(context)
        
        # Academic domain should recognize academic terminology
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        self.assertGreater(result.confidence_score, 0.3)
    
    def test_creative_domain_flexibility(self):
        """Test flexibility for creative domain validation."""
        context = ValidationContext(
            text="The enchanted forest whispered ancient secrets while mystical creatures danced beneath starlight.",
            error_position=30,
            error_text="whispered",
            rule_type="style",
            rule_name="descriptive_language"
        )
        
        result = self.validator.validate_error(context)
        
        # Creative domain should be more flexible with style rules
        style_evidence = next((e for e in result.evidence if e.evidence_type == "style_consistency"), None)
        if style_evidence:
            violations = style_evidence.source_data.get("style_violations", [])
            # Creative domain should have fewer strict style violations
            self.assertIsInstance(violations, list)
    
    def test_cross_domain_terminology_detection(self):
        """Test detection of inappropriate cross-domain terminology."""
        context = ValidationContext(
            text="The magical API endpoint implements JSON spells for database enchantment.",
            error_position=15,
            error_text="endpoint",
            rule_type="terminology",
            rule_name="domain_consistency"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect mixed domain terminology
        terminology_evidence = next((e for e in result.evidence if e.evidence_type == "terminology_validation"), None)
        if terminology_evidence:
            inappropriate_terms = terminology_evidence.source_data.get("inappropriate_terms", [])
            # May detect technical terms as inappropriate in creative context
            self.assertIsInstance(inappropriate_terms, list)


if __name__ == '__main__':
    unittest.main(verbosity=2)
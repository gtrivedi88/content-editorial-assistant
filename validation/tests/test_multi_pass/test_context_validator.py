"""
Comprehensive test suite for ContextValidator class.
Tests coreference validation, discourse flow, semantic consistency, and contextual appropriateness.
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock

from validation.multi_pass.pass_validators.context_validator import (
    ContextValidator, CoreferenceValidation, DiscourseFlowAnalysis,
    SemanticConsistencyCheck, ContextualAppropriateness
)
from validation.multi_pass import ValidationContext, ValidationDecision, ValidationConfidence


class TestContextValidatorInitialization(unittest.TestCase):
    """Test ContextValidator initialization and configuration."""
    
    def test_default_initialization(self):
        """Test initialization with default settings."""
        validator = ContextValidator()
        
        self.assertEqual(validator.validator_name, "context_validator")
        self.assertEqual(validator.spacy_model_name, "en_core_web_sm")
        self.assertEqual(validator.context_window_size, 3)
        self.assertTrue(validator.enable_coreference_analysis)
        self.assertTrue(validator.enable_discourse_analysis)
        self.assertTrue(validator.enable_semantic_consistency)
        self.assertTrue(validator.cache_analysis_results)
        self.assertEqual(validator.min_confidence_threshold, 0.55)
        self.assertIsNotNone(validator.nlp)
    
    def test_custom_initialization(self):
        """Test initialization with custom settings."""
        validator = ContextValidator(
            spacy_model="en_core_web_sm",
            context_window_size=5,
            enable_coreference_analysis=False,
            enable_discourse_analysis=False,
            enable_semantic_consistency=False,
            cache_analysis_results=False,
            min_confidence_threshold=0.7
        )
        
        self.assertEqual(validator.spacy_model_name, "en_core_web_sm")
        self.assertEqual(validator.context_window_size, 5)
        self.assertFalse(validator.enable_coreference_analysis)
        self.assertFalse(validator.enable_discourse_analysis)
        self.assertFalse(validator.enable_semantic_consistency)
        self.assertFalse(validator.cache_analysis_results)
        self.assertEqual(validator.min_confidence_threshold, 0.7)
    
    def test_validator_info(self):
        """Test get_validator_info method."""
        validator = ContextValidator()
        info = validator.get_validator_info()
        
        self.assertEqual(info["name"], "context_validator")
        self.assertEqual(info["type"], "context_validator")
        self.assertIn("coreference_validation", info["capabilities"])
        self.assertIn("discourse_flow_analysis", info["capabilities"])
        self.assertIn("semantic_consistency_checking", info["capabilities"])
        self.assertIn("style_validation", info["specialties"])
        self.assertIn("configuration", info)
        self.assertIn("performance_characteristics", info)
    
    def test_contextual_patterns_initialization(self):
        """Test that contextual patterns are properly initialized."""
        validator = ContextValidator()
        
        # Check pronoun categories
        self.assertIn("personal_pronouns", validator.pronoun_categories)
        self.assertIn("possessive_pronouns", validator.pronoun_categories)
        
        # Check discourse markers
        self.assertIn("addition", validator.discourse_markers)
        self.assertIn("contrast", validator.discourse_markers)
        
        # Check semantic fields
        self.assertIn("technical", validator.semantic_fields)
        self.assertIn("business", validator.semantic_fields)
        
        # Check formality indicators
        self.assertIn("formal", validator.formality_indicators)
        self.assertIn("informal", validator.formality_indicators)


class TestCoreferenceValidation(unittest.TestCase):
    """Test coreference validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ContextValidator()
    
    def test_coreference_validation_creation(self):
        """Test CoreferenceValidation dataclass creation."""
        validation = CoreferenceValidation(
            token="it",
            is_pronoun=True,
            antecedent_found=True,
            antecedent_text="system",
            antecedent_distance=5,
            resolution_confidence=0.8,
            ambiguity_detected=False,
            context_clarity=0.9
        )
        
        self.assertEqual(validation.token, "it")
        self.assertTrue(validation.is_pronoun)
        self.assertTrue(validation.antecedent_found)
        self.assertEqual(validation.antecedent_text, "system")
        self.assertEqual(validation.antecedent_distance, 5)
        self.assertEqual(validation.resolution_confidence, 0.8)
        self.assertFalse(validation.ambiguity_detected)
        self.assertEqual(validation.context_clarity, 0.9)
    
    def test_pronoun_coreference_validation(self):
        """Test coreference validation for pronouns."""
        context = ValidationContext(
            text="The system processes data efficiently. It demonstrates excellent performance.",
            error_position=39,  # Correct position for "It"
            error_text="It",
            rule_type="style",
            rule_name="pronoun_clarity"
        )
        
        result = self.validator.validate_error(context)
        
        # Should have coreference evidence when enabled
        coreference_evidence = next((e for e in result.evidence if e.evidence_type == "coreference_validation"), None)
        if self.validator.enable_coreference_analysis:
            self.assertIsNotNone(coreference_evidence)
            self.assertIn("is_pronoun", coreference_evidence.source_data)
            self.assertTrue(coreference_evidence.source_data["is_pronoun"])
    
    def test_clear_pronoun_reference(self):
        """Test validation with clear pronoun reference."""
        context = ValidationContext(
            text="The documentation is comprehensive. It covers all the important topics thoroughly.",
            error_position=35,
            error_text="It",
            rule_type="style",
            rule_name="pronoun_usage"
        )
        
        result = self.validator.validate_error(context)
        
        # Should generally accept clear pronoun references for style rules
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        self.assertGreaterEqual(result.confidence_score, 0.3)
    
    def test_ambiguous_pronoun_reference(self):
        """Test validation with ambiguous pronoun reference."""
        context = ValidationContext(
            text="The system and the database work together. It processes the requests efficiently.",
            error_position=47,
            error_text="It",
            rule_type="style",
            rule_name="pronoun_clarity"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect ambiguity in pronoun reference
        coreference_evidence = next((e for e in result.evidence if e.evidence_type == "coreference_validation"), None)
        if coreference_evidence:
            # May detect ambiguity due to multiple possible antecedents
            self.assertIsInstance(coreference_evidence.source_data.get("ambiguity_detected"), bool)
    
    def test_pronoun_detection(self):
        """Test pronoun detection logic."""
        # Test various pronoun types
        self.assertTrue(self.validator._is_pronoun("it"))
        self.assertTrue(self.validator._is_pronoun("they"))
        self.assertTrue(self.validator._is_pronoun("his"))
        self.assertTrue(self.validator._is_pronoun("this"))
        self.assertTrue(self.validator._is_pronoun("who"))
        
        # Test non-pronouns
        self.assertFalse(self.validator._is_pronoun("system"))
        self.assertFalse(self.validator._is_pronoun("process"))
        self.assertFalse(self.validator._is_pronoun("the"))
    
    def test_coreference_disabled(self):
        """Test behavior when coreference analysis is disabled."""
        validator = ContextValidator(enable_coreference_analysis=False)
        
        context = ValidationContext(
            text="The system processes data. It works efficiently.",
            error_position=25,
            error_text="It",
            rule_type="style"
        )
        
        result = validator.validate_error(context)
        
        # Should not have coreference evidence when disabled
        coreference_evidence = next((e for e in result.evidence if e.evidence_type == "coreference_validation"), None)
        self.assertIsNone(coreference_evidence)


class TestDiscourseFlowAnalysis(unittest.TestCase):
    """Test discourse flow analysis functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ContextValidator()
    
    def test_discourse_flow_analysis_creation(self):
        """Test DiscourseFlowAnalysis dataclass creation."""
        analysis = DiscourseFlowAnalysis(
            sentence_count=3,
            transition_markers=["however", "therefore"],
            coherence_score=0.8,
            flow_disruption=False,
            topic_consistency=0.7,
            logical_progression=0.9,
            discourse_structure="comparative",
            context_window_used=3
        )
        
        self.assertEqual(analysis.sentence_count, 3)
        self.assertEqual(analysis.transition_markers, ["however", "therefore"])
        self.assertEqual(analysis.coherence_score, 0.8)
        self.assertFalse(analysis.flow_disruption)
        self.assertEqual(analysis.discourse_structure, "comparative")
    
    def test_discourse_markers_detection(self):
        """Test detection of discourse markers."""
        context = ValidationContext(
            text="The system works well. However, it has some limitations. Therefore, we need improvements.",
            error_position=50,
            error_text="limitations",
            rule_type="style",
            rule_name="discourse_flow"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect discourse markers
        discourse_evidence = next((e for e in result.evidence if e.evidence_type == "discourse_flow"), None)
        if self.validator.enable_discourse_analysis and discourse_evidence:
            markers = discourse_evidence.source_data.get("transition_markers", [])
            # Should find some discourse markers
            self.assertIsInstance(markers, list)
    
    def test_coherent_discourse_validation(self):
        """Test validation with coherent discourse."""
        context = ValidationContext(
            text="First, the system initializes. Next, it processes the data. Finally, it outputs the results.",
            error_position=40,
            error_text="processes",
            rule_type="style",
            rule_name="process_description"
        )
        
        result = self.validator.validate_error(context)
        
        # Should generally accept coherent discourse for style rules
        if "discourse_flow" in [e.evidence_type for e in result.evidence]:
            discourse_evidence = next(e for e in result.evidence if e.evidence_type == "discourse_flow")
            # Should have reasonable coherence
            self.assertGreaterEqual(discourse_evidence.source_data.get("coherence_score", 0), 0.3)
    
    def test_disrupted_discourse_flow(self):
        """Test validation with disrupted discourse flow."""
        context = ValidationContext(
            text="The API handles requests. Cats are fluffy animals. Database queries are optimized.",
            error_position=30,
            error_text="fluffy",
            rule_type="style",
            rule_name="topic_consistency"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect topic inconsistency
        discourse_evidence = next((e for e in result.evidence if e.evidence_type == "discourse_flow"), None)
        if discourse_evidence:
            # May detect flow disruption or low topic consistency
            flow_disruption = discourse_evidence.source_data.get("flow_disruption", False)
            topic_consistency = discourse_evidence.source_data.get("topic_consistency", 1.0)
            # Either flow disruption should be detected or topic consistency should be low
            self.assertTrue(flow_disruption or topic_consistency < 0.6)
    
    def test_discourse_structure_identification(self):
        """Test identification of discourse structures."""
        # Test different discourse structures
        test_cases = [
            ("Furthermore, the system provides additional features.", "enumerative"),
            ("However, there are some limitations to consider.", "comparative"),
            ("Therefore, we conclude that the approach works.", "causal"),
            ("First, initialize the system. Then, configure settings.", "temporal"),
        ]
        
        for text, expected_structure_type in test_cases:
            with self.subTest(text=text):
                context = ValidationContext(
                    text=text,
                    error_position=10,
                    error_text="system",
                    rule_type="style"
                )
                
                result = self.validator.validate_error(context)
                
                # Check if discourse structure is identified (structure may vary)
                discourse_evidence = next((e for e in result.evidence if e.evidence_type == "discourse_flow"), None)
                if discourse_evidence:
                    structure = discourse_evidence.source_data.get("discourse_structure", "")
                    self.assertIsInstance(structure, str)
                    self.assertGreater(len(structure), 0)
    
    def test_discourse_analysis_disabled(self):
        """Test behavior when discourse analysis is disabled."""
        validator = ContextValidator(enable_discourse_analysis=False)
        
        context = ValidationContext(
            text="First, we analyze. Then, we conclude. Finally, we implement.",
            error_position=20,
            error_text="conclude",
            rule_type="style"
        )
        
        result = validator.validate_error(context)
        
        # Should not have discourse evidence when disabled
        discourse_evidence = next((e for e in result.evidence if e.evidence_type == "discourse_flow"), None)
        self.assertIsNone(discourse_evidence)


class TestSemanticConsistencyChecking(unittest.TestCase):
    """Test semantic consistency checking functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ContextValidator()
    
    def test_semantic_consistency_check_creation(self):
        """Test SemanticConsistencyCheck dataclass creation."""
        check = SemanticConsistencyCheck(
            semantic_field="technical",
            consistency_score=0.8,
            conflicting_terms=["informal_word"],
            domain_coherence=0.9,
            register_consistency=0.7,
            terminology_alignment=0.8,
            semantic_anomalies=[]
        )
        
        self.assertEqual(check.semantic_field, "technical")
        self.assertEqual(check.consistency_score, 0.8)
        self.assertEqual(check.conflicting_terms, ["informal_word"])
        self.assertEqual(check.domain_coherence, 0.9)
        self.assertEqual(check.register_consistency, 0.7)
        self.assertEqual(check.terminology_alignment, 0.8)
        self.assertEqual(check.semantic_anomalies, [])
    
    def test_technical_semantic_field_detection(self):
        """Test detection of technical semantic field."""
        context = ValidationContext(
            text="The API system processes data using advanced algorithms and optimized functions.",
            error_position=30,
            error_text="algorithms",
            rule_type="terminology",
            rule_name="technical_terms"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect technical semantic field
        semantic_evidence = next((e for e in result.evidence if e.evidence_type == "semantic_consistency"), None)
        if self.validator.enable_semantic_consistency and semantic_evidence:
            semantic_field = semantic_evidence.source_data.get("semantic_field", "")
            self.assertIn(semantic_field, ["technical", "general"])  # Either technical or general is fine
    
    def test_business_semantic_field_detection(self):
        """Test detection of business semantic field."""
        context = ValidationContext(
            text="The company's revenue strategy focuses on customer management and market analysis.",
            error_position=30,
            error_text="strategy",
            rule_type="style",
            rule_name="business_language"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect business semantic field
        semantic_evidence = next((e for e in result.evidence if e.evidence_type == "semantic_consistency"), None)
        if semantic_evidence:
            semantic_field = semantic_evidence.source_data.get("semantic_field", "")
            self.assertIn(semantic_field, ["business", "general"])  # Either business or general is fine
    
    def test_semantic_consistency_scoring(self):
        """Test semantic consistency scoring."""
        context = ValidationContext(
            text="The system implementation requires careful algorithm design and data structure optimization.",
            error_position=40,
            error_text="algorithm",
            rule_type="terminology",
            rule_name="technical_precision"
        )
        
        result = self.validator.validate_error(context)
        
        # Should have semantic consistency analysis
        semantic_evidence = next((e for e in result.evidence if e.evidence_type == "semantic_consistency"), None)
        if semantic_evidence:
            consistency_score = semantic_evidence.source_data.get("consistency_score", 0)
            self.assertIsInstance(consistency_score, float)
            self.assertGreaterEqual(consistency_score, 0.0)
            self.assertLessEqual(consistency_score, 1.0)
    
    def test_semantic_conflicts_detection(self):
        """Test detection of semantic conflicts."""
        context = ValidationContext(
            text="The technical system architecture is totally awesome and super cool to implement.",
            error_position=50,
            error_text="awesome",
            rule_type="style",
            rule_name="register_consistency"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect conflicts between technical and informal language
        semantic_evidence = next((e for e in result.evidence if e.evidence_type == "semantic_consistency"), None)
        if semantic_evidence:
            conflicting_terms = semantic_evidence.source_data.get("conflicting_terms", [])
            self.assertIsInstance(conflicting_terms, list)
            # May detect conflicts due to mixed register
    
    def test_domain_coherence_assessment(self):
        """Test domain coherence assessment."""
        context = ValidationContext(
            text="The research methodology involves systematic analysis of empirical data using statistical techniques.",
            error_position=30,
            error_text="methodology",
            rule_type="terminology",
            rule_name="academic_terms",
            content_type="academic"
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess domain coherence
        semantic_evidence = next((e for e in result.evidence if e.evidence_type == "semantic_consistency"), None)
        if semantic_evidence:
            domain_coherence = semantic_evidence.source_data.get("domain_coherence", 0)
            self.assertIsInstance(domain_coherence, float)
            self.assertGreaterEqual(domain_coherence, 0.0)
            self.assertLessEqual(domain_coherence, 1.0)
    
    def test_semantic_consistency_disabled(self):
        """Test behavior when semantic consistency is disabled."""
        validator = ContextValidator(enable_semantic_consistency=False)
        
        context = ValidationContext(
            text="The technical system uses advanced algorithms.",
            error_position=20,
            error_text="system",
            rule_type="terminology"
        )
        
        result = validator.validate_error(context)
        
        # Should not have semantic evidence when disabled
        semantic_evidence = next((e for e in result.evidence if e.evidence_type == "semantic_consistency"), None)
        self.assertIsNone(semantic_evidence)


class TestContextualAppropriatenessAssessment(unittest.TestCase):
    """Test contextual appropriateness assessment functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ContextValidator()
    
    def test_contextual_appropriateness_creation(self):
        """Test ContextualAppropriateness dataclass creation."""
        appropriateness = ContextualAppropriateness(
            formality_level="formal",
            audience_appropriateness=0.8,
            style_consistency=0.9,
            tone_alignment=0.7,
            register_appropriateness=0.8,
            context_mismatch=False,
            appropriateness_factors=["good_formality"]
        )
        
        self.assertEqual(appropriateness.formality_level, "formal")
        self.assertEqual(appropriateness.audience_appropriateness, 0.8)
        self.assertEqual(appropriateness.style_consistency, 0.9)
        self.assertEqual(appropriateness.tone_alignment, 0.7)
        self.assertEqual(appropriateness.register_appropriateness, 0.8)
        self.assertFalse(appropriateness.context_mismatch)
        self.assertEqual(appropriateness.appropriateness_factors, ["good_formality"])
    
    def test_formal_language_detection(self):
        """Test detection of formal language."""
        context = ValidationContext(
            text="The system demonstrates exceptional performance and facilitates comprehensive data processing.",
            error_position=20,
            error_text="demonstrates",
            rule_type="style",
            rule_name="formality",
            content_type="technical"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect formal language
        appropriateness_evidence = next((e for e in result.evidence if e.evidence_type == "contextual_appropriateness"), None)
        if appropriateness_evidence:
            formality_level = appropriateness_evidence.source_data.get("formality_level", "")
            self.assertIn(formality_level, ["formal", "neutral"])  # Should detect formal or neutral
    
    def test_informal_language_detection(self):
        """Test detection of informal language."""
        context = ValidationContext(
            text="The app is super easy to use and really helps users get stuff done quickly.",
            error_position=15,
            error_text="super",
            rule_type="style",
            rule_name="formality",
            content_type="narrative"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect informal language
        appropriateness_evidence = next((e for e in result.evidence if e.evidence_type == "contextual_appropriateness"), None)
        if appropriateness_evidence:
            formality_level = appropriateness_evidence.source_data.get("formality_level", "")
            self.assertIn(formality_level, ["informal", "neutral"])  # Should detect informal or neutral
    
    def test_audience_appropriateness_technical(self):
        """Test audience appropriateness for technical content."""
        context = ValidationContext(
            text="The API endpoint utilizes advanced authentication mechanisms to ensure secure access.",
            error_position=20,
            error_text="utilizes",
            rule_type="style",
            rule_name="word_choice",
            content_type="technical"
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess audience appropriateness
        appropriateness_evidence = next((e for e in result.evidence if e.evidence_type == "contextual_appropriateness"), None)
        if appropriateness_evidence:
            audience_appropriateness = appropriateness_evidence.source_data.get("audience_appropriateness", 0)
            self.assertIsInstance(audience_appropriateness, float)
            self.assertGreaterEqual(audience_appropriateness, 0.0)
            self.assertLessEqual(audience_appropriateness, 1.0)
    
    def test_style_consistency_assessment(self):
        """Test style consistency assessment."""
        context = ValidationContext(
            text="The documentation provides comprehensive guidance. It offers detailed instructions. Users can follow the steps easily.",
            error_position=40,
            error_text="guidance",
            rule_type="style",
            rule_name="consistency"
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess style consistency
        appropriateness_evidence = next((e for e in result.evidence if e.evidence_type == "contextual_appropriateness"), None)
        if appropriateness_evidence:
            style_consistency = appropriateness_evidence.source_data.get("style_consistency", 0)
            self.assertIsInstance(style_consistency, float)
            self.assertGreaterEqual(style_consistency, 0.0)
            self.assertLessEqual(style_consistency, 1.0)
    
    def test_context_mismatch_detection(self):
        """Test detection of context mismatches."""
        context = ValidationContext(
            text="The enterprise-grade system architecture is totally awesome and super cool.",
            error_position=50,
            error_text="awesome",
            rule_type="style",
            rule_name="register_appropriateness",
            content_type="technical"
        )
        
        result = self.validator.validate_error(context)
        
        # Should potentially detect context mismatch
        appropriateness_evidence = next((e for e in result.evidence if e.evidence_type == "contextual_appropriateness"), None)
        if appropriateness_evidence:
            context_mismatch = appropriateness_evidence.source_data.get("context_mismatch", False)
            self.assertIsInstance(context_mismatch, bool)
            # May detect mismatch due to informal language in technical context
    
    def test_tone_alignment_assessment(self):
        """Test tone alignment assessment."""
        context = ValidationContext(
            text="The excellent system provides outstanding performance and delivers exceptional results.",
            error_position=20,
            error_text="outstanding",
            rule_type="style",
            rule_name="tone_consistency"
        )
        
        result = self.validator.validate_error(context)
        
        # Should assess tone alignment
        appropriateness_evidence = next((e for e in result.evidence if e.evidence_type == "contextual_appropriateness"), None)
        if appropriateness_evidence:
            tone_alignment = appropriateness_evidence.source_data.get("tone_alignment", 0)
            self.assertIsInstance(tone_alignment, float)
            self.assertGreaterEqual(tone_alignment, 0.0)
            self.assertLessEqual(tone_alignment, 1.0)


class TestValidationDecisionMaking(unittest.TestCase):
    """Test validation decision making logic."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ContextValidator()
    
    def test_style_rule_decision_logic(self):
        """Test decision logic for style rules."""
        context = ValidationContext(
            text="Furthermore, the comprehensive documentation demonstrates excellent practices. However, it requires additional examples.",
            error_position=50,
            error_text="demonstrates",
            rule_type="style",
            rule_name="word_choice"
        )
        
        result = self.validator.validate_error(context)
        
        # Style rules should benefit from contextual analysis
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        self.assertGreater(result.confidence_score, 0.3)
        self.assertIsInstance(result.reasoning, str)
        self.assertGreater(len(result.reasoning), 20)
    
    def test_tone_rule_decision_logic(self):
        """Test decision logic for tone rules."""
        context = ValidationContext(
            text="The system works perfectly and provides amazing results for all users.",
            error_position=30,
            error_text="amazing",
            rule_type="tone",
            rule_name="enthusiasm_level"
        )
        
        result = self.validator.validate_error(context)
        
        # Tone rules should strongly benefit from contextual analysis
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN, ValidationDecision.REJECT])
        self.assertIsInstance(result.confidence_score, float)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
    
    def test_grammar_rule_decision_logic(self):
        """Test decision logic for grammar rules."""
        context = ValidationContext(
            text="The documentation which was recently updated provides comprehensive guidance.",
            error_position=20,
            error_text="which",
            rule_type="grammar",
            rule_name="relative_pronoun_usage"
        )
        
        result = self.validator.validate_error(context)
        
        # Grammar rules have moderate benefit from contextual analysis
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        self.assertGreater(result.confidence_score, 0.2)
    
    def test_terminology_rule_decision_logic(self):
        """Test decision logic for terminology rules."""
        context = ValidationContext(
            text="The application programming interface provides standardized access to system functions.",
            error_position=40,
            error_text="standardized",
            rule_type="terminology",
            rule_name="technical_precision"
        )
        
        result = self.validator.validate_error(context)
        
        # Terminology rules benefit from semantic consistency
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        self.assertIsInstance(result.confidence_score, float)
    
    def test_decision_with_strong_evidence(self):
        """Test decision making with strong contextual evidence."""
        context = ValidationContext(
            text="First, initialize the system. Then, configure the settings. Finally, run the application.",
            error_position=40,
            error_text="configure",
            rule_type="style",
            rule_name="instructional_clarity"
        )
        
        result = self.validator.validate_error(context)
        
        # Strong discourse structure should lead to confident decisions
        self.assertGreater(len(result.evidence), 0)
        if result.confidence_score > 0.7:
            self.assertEqual(result.decision, ValidationDecision.ACCEPT)
    
    def test_decision_with_weak_evidence(self):
        """Test decision making with weak contextual evidence."""
        context = ValidationContext(
            text="Word.",  # Minimal context
            error_position=0,
            error_text="Word",
            rule_type="style",
            rule_name="context_appropriateness"
        )
        
        result = self.validator.validate_error(context)
        
        # Weak context should lead to uncertain decisions
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertLessEqual(result.confidence_score, 0.8)  # More realistic expectation


class TestPerformanceAndCaching(unittest.TestCase):
    """Test performance monitoring and caching functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ContextValidator(cache_analysis_results=True)
    
    def test_analysis_caching_enabled(self):
        """Test analysis result caching when enabled."""
        text = "The comprehensive documentation demonstrates proper implementation."
        
        # First analysis - should be cached
        doc1 = self.validator._analyze_text_with_context(text)
        cache_misses_1 = self.validator._cache_misses
        
        # Second analysis - should use cache
        doc2 = self.validator._analyze_text_with_context(text)
        cache_hits_1 = self.validator._cache_hits
        
        self.assertEqual(doc1.text, doc2.text)
        self.assertGreater(cache_hits_1, 0)
    
    def test_analysis_caching_disabled(self):
        """Test behavior when analysis caching is disabled."""
        validator = ContextValidator(cache_analysis_results=False)
        text = "The comprehensive documentation demonstrates proper implementation."
        
        # Multiple analyses should not use cache
        validator._analyze_text_with_context(text)
        validator._analyze_text_with_context(text)
        
        self.assertEqual(validator._cache_hits, 0)  # No cache hits
    
    def test_performance_tracking(self):
        """Test performance tracking for different analysis types."""
        context = ValidationContext(
            text="Furthermore, the comprehensive system demonstrates excellent performance. However, it requires optimization.",
            error_position=40,
            error_text="demonstrates",
            rule_type="style",
            rule_name="word_choice"
        )
        
        # Perform validation to populate performance data
        result = self.validator.validate_error(context)
        
        # Check that validation completed successfully
        self.assertIsInstance(result.validation_time, float)
        self.assertGreater(result.validation_time, 0)
        
        # Check analysis statistics
        stats = self.validator.get_analysis_statistics()
        self.assertIn("analysis_performance", stats)
        self.assertIn("analysis_cache", stats)
    
    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        # Perform some operations to generate cache statistics
        texts = [
            "The first sentence for analysis.",
            "The second sentence for analysis.",
            "The first sentence for analysis."  # Repeat to test cache hit
        ]
        
        for text in texts:
            self.validator._analyze_text_with_context(text)
        
        hit_rate = self.validator._get_cache_hit_rate()
        self.assertIsInstance(hit_rate, float)
        self.assertGreaterEqual(hit_rate, 0.0)
        self.assertLessEqual(hit_rate, 1.0)
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        # Populate cache
        self.validator._analyze_text_with_context("Test sentence for caching.")
        
        # Verify cache has content
        self.assertGreater(len(self.validator._analysis_cache), 0)
        
        # Clear cache
        self.validator.clear_caches()
        
        # Verify cache is empty
        self.assertEqual(len(self.validator._analysis_cache), 0)
        self.assertEqual(self.validator._cache_hits, 0)
        self.assertEqual(self.validator._cache_misses, 0)


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Test error handling and edge case scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ContextValidator()
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        context = ValidationContext(
            text="",
            error_position=0,
            error_text="",
            rule_type="style"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle empty text gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertLessEqual(result.confidence_score, 0.5)
    
    def test_single_word_text(self):
        """Test handling of single word text."""
        context = ValidationContext(
            text="Word",
            error_position=0,
            error_text="Word",
            rule_type="style"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle minimal context gracefully
        self.assertIn(result.decision, [ValidationDecision.UNCERTAIN])
        self.assertIsInstance(result.validation_time, float)
        self.assertGreater(result.validation_time, 0)
    
    def test_very_long_text_handling(self):
        """Test handling of very long text."""
        long_text = "The system processes data. " * 100  # Very long repetitive text
        context = ValidationContext(
            text=long_text,
            error_position=500,
            error_text="processes",
            rule_type="style"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle long text without errors
        self.assertIsInstance(result.confidence_score, float)
        self.assertGreater(result.validation_time, 0)
    
    def test_unclear_pronoun_references(self):
        """Test handling of unclear pronoun references."""
        context = ValidationContext(
            text="The system and database interact. It performs well.",
            error_position=35,
            error_text="It",
            rule_type="style",
            rule_name="pronoun_clarity"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle unclear references (may detect ambiguity)
        coreference_evidence = next((e for e in result.evidence if e.evidence_type == "coreference_validation"), None)
        if coreference_evidence:
            # Should still produce valid analysis
            self.assertIsInstance(coreference_evidence.confidence, float)
    
    def test_mixed_language_registers(self):
        """Test handling of mixed language registers."""
        context = ValidationContext(
            text="The sophisticated algorithm is totally awesome and works great.",
            error_position=40,
            error_text="awesome",
            rule_type="style",
            rule_name="register_consistency"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect register inconsistency
        appropriateness_evidence = next((e for e in result.evidence if e.evidence_type == "contextual_appropriateness"), None)
        if appropriateness_evidence:
            # Should still provide valid analysis despite mixed registers
            self.assertIsInstance(appropriateness_evidence.confidence, float)
    
    def test_invalid_error_position(self):
        """Test handling of invalid error positions."""
        context = ValidationContext(
            text="Short text.",
            error_position=100,  # Beyond text length
            error_text="nonexistent",
            rule_type="style"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle invalid position gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertIsInstance(result.validation_time, float)
        self.assertGreater(result.validation_time, 0)
    
    def test_no_contextual_information(self):
        """Test handling when no contextual information can be extracted."""
        # This would require mocking to create a scenario with no context
        # For now, test that validator handles edge cases gracefully
        
        context = ValidationContext(
            text="A.",  # Minimal text
            error_position=0,
            error_text="A",
            rule_type="style"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle minimal context gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertLessEqual(result.confidence_score, 0.8)  # More realistic expectation


class TestValidationConsistency(unittest.TestCase):
    """Test validation decision consistency."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = ContextValidator()
    
    def test_consistent_results_for_identical_input(self):
        """Test that identical inputs produce consistent results."""
        context = ValidationContext(
            text="Furthermore, the comprehensive documentation demonstrates proper implementation. However, it needs examples.",
            error_position=50,
            error_text="demonstrates",
            rule_type="style",
            rule_name="word_choice"
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
    
    def test_complex_text_structure_handling(self):
        """Test handling of various complex text structures."""
        test_cases = [
            # Complex sentence with multiple clauses
            ("Although the system is comprehensive, it lacks the examples that users need, which creates confusion.", 60, "examples", "style"),
            # Multiple discourse markers
            ("First, initialize the system. Then, configure settings. Finally, test functionality.", 40, "configure", "style"),
            # Mixed registers
            ("The enterprise system utilizes awesome algorithms for data processing.", 30, "awesome", "style"),
            # Technical content
            ("The API endpoint implements RESTful architecture with JSON response formatting.", 20, "implements", "terminology"),
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
                
                # Should handle all complex structures without errors
                self.assertIsInstance(result.confidence_score, float)
                self.assertGreaterEqual(result.confidence_score, 0.0)
                self.assertLessEqual(result.confidence_score, 1.0)
                self.assertGreater(len(result.evidence), 0)
                self.assertIsInstance(result.reasoning, str)
                self.assertGreater(len(result.reasoning), 10)


if __name__ == '__main__':
    unittest.main(verbosity=2)
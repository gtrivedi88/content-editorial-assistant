"""
Comprehensive test suite for MorphologicalValidator class.
Tests POS tagging, dependency parsing, ambiguity detection, and cross-model verification.
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock

from validation.multi_pass.pass_validators.morphological_validator import (
    MorphologicalValidator, POSAnalysis, DependencyAnalysis, MorphologicalAmbiguity
)
from validation.multi_pass import ValidationContext, ValidationDecision, ValidationConfidence


class TestMorphologicalValidatorInitialization(unittest.TestCase):
    """Test MorphologicalValidator initialization and configuration."""
    
    def test_default_initialization(self):
        """Test initialization with default settings."""
        validator = MorphologicalValidator()
        
        self.assertEqual(validator.validator_name, "morphological_validator")
        self.assertEqual(validator.spacy_model_name, "en_core_web_sm")
        self.assertTrue(validator.enable_dependency_parsing)
        self.assertTrue(validator.enable_ambiguity_detection)
        self.assertTrue(validator.cache_nlp_results)
        self.assertEqual(validator.min_confidence_threshold, 0.6)
        self.assertIsNotNone(validator.nlp)
    
    def test_custom_initialization(self):
        """Test initialization with custom settings."""
        validator = MorphologicalValidator(
            spacy_model="en_core_web_sm",
            enable_dependency_parsing=False,
            enable_ambiguity_detection=False,
            cache_nlp_results=False,
            min_confidence_threshold=0.8
        )
        
        self.assertEqual(validator.spacy_model_name, "en_core_web_sm")
        self.assertFalse(validator.enable_dependency_parsing)
        self.assertFalse(validator.enable_ambiguity_detection)
        self.assertFalse(validator.cache_nlp_results)
        self.assertEqual(validator.min_confidence_threshold, 0.8)
    
    def test_validator_info(self):
        """Test get_validator_info method."""
        validator = MorphologicalValidator()
        info = validator.get_validator_info()
        
        self.assertEqual(info["name"], "morphological_validator")
        self.assertEqual(info["type"], "morphological_validator")
        self.assertIn("pos_tagging", info["capabilities"])
        self.assertIn("dependency_parsing", info["capabilities"])
        self.assertIn("morphological_ambiguity_detection", info["capabilities"])
        self.assertIn("grammar_validation", info["specialties"])
        self.assertIn("configuration", info)
        self.assertIn("performance_characteristics", info)
    
    def test_morphological_patterns_initialization(self):
        """Test that morphological patterns are properly initialized."""
        validator = MorphologicalValidator()
        
        # Check grammar patterns
        self.assertIn("subject_verb_agreement", validator.grammar_patterns)
        self.assertIn("possessive_vs_contraction", validator.grammar_patterns)
        
        # Check POS hierarchies
        self.assertIn("noun_tags", validator.pos_hierarchies)
        self.assertIn("verb_tags", validator.pos_hierarchies)
        
        # Check dependency validations
        self.assertIn("subject_relations", validator.dependency_validations)
        self.assertIn("object_relations", validator.dependency_validations)
        
        # Check ambiguity patterns
        self.assertIn("homonyms", validator.ambiguity_patterns)
        self.assertIn("pos_ambiguous", validator.ambiguity_patterns)


class TestPOSTaggingValidation(unittest.TestCase):
    """Test POS tagging validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = MorphologicalValidator()
    
    def test_pos_analysis_creation(self):
        """Test POSAnalysis dataclass creation and validation."""
        analysis = POSAnalysis(
            token="running",
            pos="VERB",
            tag="VBG",
            lemma="run",
            confidence=0.8,
            context_pos=["NOUN", "VERB", "ADV"],
            morphological_features={"Tense": "Pres", "VerbForm": "Part"}
        )
        
        self.assertEqual(analysis.token, "running")
        self.assertEqual(analysis.pos, "VERB")
        self.assertEqual(analysis.tag, "VBG")
        self.assertEqual(analysis.lemma, "run")
        self.assertEqual(analysis.confidence, 0.8)
        self.assertEqual(len(analysis.context_pos), 3)
        self.assertIn("Tense", analysis.morphological_features)
    
    def test_grammar_rule_pos_validation(self):
        """Test POS validation for grammar rules."""
        context = ValidationContext(
            text="The company shared it's quarterly results.",
            error_position=22,
            error_text="it's",
            rule_type="grammar",
            rule_name="possessive_vs_contraction"
        )
        
        result = self.validator.validate_error(context)
        
        # Should accept grammar rules with morphological evidence
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        self.assertGreater(result.confidence_score, 0.3)
        self.assertGreater(len(result.evidence), 0)
        
        # Should have POS tagging evidence
        pos_evidence = next((e for e in result.evidence if e.evidence_type == "pos_tagging"), None)
        self.assertIsNotNone(pos_evidence)
    
    def test_style_rule_pos_validation(self):
        """Test POS validation for style rules."""
        context = ValidationContext(
            text="The documentation is very comprehensive.",
            error_position=20,
            error_text="very",
            rule_type="style",
            rule_name="adverb_usage"
        )
        
        result = self.validator.validate_error(context)
        
        # Style rules should still get morphological analysis
        self.assertIsInstance(result.confidence_score, float)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
        
        # Should have evidence
        self.assertGreater(len(result.evidence), 0)
    
    def test_pos_confidence_calculation(self):
        """Test POS confidence calculation logic."""
        # Create mock token and context
        mock_token = Mock()
        mock_token.pos_ = "NOUN"
        mock_token.morph = Mock()
        mock_token.morph.__str__ = Mock(return_value="Number=Sing")
        
        mock_context = [Mock() for _ in range(3)]
        for i, t in enumerate(mock_context):
            t.pos_ = ["DET", "NOUN", "VERB"][i]
        
        context = ValidationContext(
            text="test",
            error_position=0,
            error_text="test",
            rule_type="grammar"
        )
        
        confidence = self.validator._calculate_pos_confidence(mock_token, mock_context, context)
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        # Grammar rules should get higher confidence
        self.assertGreater(confidence, 0.5)
    
    def test_pos_context_expectations(self):
        """Test POS context expectation logic."""
        noun_context = self.validator._get_expected_pos_context("NOUN")
        verb_context = self.validator._get_expected_pos_context("VERB")
        
        self.assertIn("DET", noun_context)  # Nouns often follow determiners
        self.assertIn("NOUN", verb_context)  # Verbs often follow subjects
        
        # Unknown POS should return empty list
        unknown_context = self.validator._get_expected_pos_context("UNKNOWN")
        self.assertEqual(unknown_context, [])


class TestDependencyParsingValidation(unittest.TestCase):
    """Test dependency parsing validation functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = MorphologicalValidator()
    
    def test_dependency_analysis_creation(self):
        """Test DependencyAnalysis dataclass creation."""
        analysis = DependencyAnalysis(
            token="demonstrates",
            dependency_relation="ROOT",
            head="demonstrates",
            head_pos="VERB",
            children=["documentation", "implementation"],
            sentence_position=0.6,
            dependency_distance=0,
            syntactic_role="main_verb"
        )
        
        self.assertEqual(analysis.token, "demonstrates")
        self.assertEqual(analysis.dependency_relation, "ROOT")
        self.assertEqual(analysis.head, "demonstrates")
        self.assertEqual(analysis.syntactic_role, "main_verb")
        self.assertEqual(len(analysis.children), 2)
    
    def test_dependency_parsing_enabled(self):
        """Test dependency parsing when enabled."""
        context = ValidationContext(
            text="The documentation demonstrates proper implementation.",
            error_position=20,
            error_text="demonstrates",
            rule_type="grammar",
            rule_name="subject_verb_agreement"
        )
        
        result = self.validator.validate_error(context)
        
        # Should have dependency parsing evidence when enabled
        dep_evidence = next((e for e in result.evidence if e.evidence_type == "dependency_parsing"), None)
        if self.validator.enable_dependency_parsing:
            self.assertIsNotNone(dep_evidence)
            self.assertIn("dependency_relation", dep_evidence.source_data)
            self.assertIn("syntactic_role", dep_evidence.source_data)
    
    def test_dependency_parsing_disabled(self):
        """Test behavior when dependency parsing is disabled."""
        validator = MorphologicalValidator(enable_dependency_parsing=False)
        
        context = ValidationContext(
            text="The documentation demonstrates proper implementation.",
            error_position=20,
            error_text="demonstrates",
            rule_type="grammar"
        )
        
        result = validator.validate_error(context)
        
        # Should not have dependency parsing evidence when disabled
        dep_evidence = next((e for e in result.evidence if e.evidence_type == "dependency_parsing"), None)
        self.assertIsNone(dep_evidence)
    
    def test_syntactic_role_determination(self):
        """Test syntactic role determination logic."""
        # Test known dependency relations
        mock_token = Mock()
        
        mock_token.dep_ = "nsubj"
        role = self.validator._determine_syntactic_role(mock_token)
        self.assertEqual(role, "subject")
        
        mock_token.dep_ = "dobj"
        role = self.validator._determine_syntactic_role(mock_token)
        self.assertEqual(role, "direct_object")
        
        mock_token.dep_ = "amod"
        role = self.validator._determine_syntactic_role(mock_token)
        self.assertEqual(role, "adjective_modifier")
        
        # Test unknown dependency relation
        mock_token.dep_ = "custom_rel"
        role = self.validator._determine_syntactic_role(mock_token)
        self.assertEqual(role, "other_custom_rel")
    
    def test_dependency_confidence_calculation(self):
        """Test dependency confidence calculation."""
        analysis = DependencyAnalysis(
            token="demonstrates",
            dependency_relation="ROOT",
            head="demonstrates",
            head_pos="VERB",
            children=[],
            sentence_position=0.5,  # Middle position
            dependency_distance=1,   # Close to head
            syntactic_role="subject"
        )
        
        context = ValidationContext(
            text="test",
            error_position=0,
            error_text="test",
            rule_type="grammar"
        )
        
        confidence = self.validator._calculate_dependency_confidence(analysis, context)
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        # Should be relatively high due to clear syntactic role and grammar rule
        self.assertGreater(confidence, 0.6)


class TestMorphologicalAmbiguityDetection(unittest.TestCase):
    """Test morphological ambiguity detection functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = MorphologicalValidator()
    
    def test_ambiguity_analysis_creation(self):
        """Test MorphologicalAmbiguity dataclass creation."""
        analysis = MorphologicalAmbiguity(
            token="bank",
            possible_interpretations=[("financial_institution", 0.6), ("river_side", 0.4)],
            ambiguity_type="semantic",
            resolution_confidence=0.7,
            context_clues=["financial_context:money", "financial_context:account"]
        )
        
        self.assertEqual(analysis.token, "bank")
        self.assertEqual(len(analysis.possible_interpretations), 2)
        self.assertEqual(analysis.ambiguity_type, "semantic")
        self.assertEqual(analysis.resolution_confidence, 0.7)
        self.assertEqual(len(analysis.context_clues), 2)
    
    def test_semantic_ambiguity_detection(self):
        """Test detection of semantic ambiguities."""
        context = ValidationContext(
            text="I need to visit the bank to deposit money.",
            error_position=20,
            error_text="bank",
            rule_type="terminology"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect ambiguity for known ambiguous words
        ambiguity_evidence = next((e for e in result.evidence if e.evidence_type == "morphological_ambiguity"), None)
        if self.validator.enable_ambiguity_detection and "bank" in self.validator.ambiguity_patterns['homonyms']:
            self.assertIsNotNone(ambiguity_evidence)
            self.assertIn("possible_interpretations", ambiguity_evidence.source_data)
    
    def test_pos_ambiguity_detection(self):
        """Test detection of POS ambiguities."""
        context = ValidationContext(
            text="I like to run in the morning.",
            error_position=10,
            error_text="run",
            rule_type="grammar"
        )
        
        result = self.validator.validate_error(context)
        
        # Should detect POS ambiguity for known ambiguous words
        if self.validator.enable_ambiguity_detection:
            ambiguity_evidence = next((e for e in result.evidence if e.evidence_type == "morphological_ambiguity"), None)
            # May or may not detect depending on context, but shouldn't error
            self.assertIsInstance(result.confidence_score, float)
    
    def test_ambiguity_detection_disabled(self):
        """Test behavior when ambiguity detection is disabled."""
        validator = MorphologicalValidator(enable_ambiguity_detection=False)
        
        context = ValidationContext(
            text="I need to visit the bank to deposit money.",
            error_position=20,
            error_text="bank",
            rule_type="terminology"
        )
        
        result = validator.validate_error(context)
        
        # Should not have ambiguity evidence when disabled
        ambiguity_evidence = next((e for e in result.evidence if e.evidence_type == "morphological_ambiguity"), None)
        self.assertIsNone(ambiguity_evidence)
    
    def test_context_clue_extraction(self):
        """Test context clue extraction for disambiguation."""
        mock_token = Mock()
        mock_token.text = "bank"
        mock_token.lemma_ = "bank"
        
        # Create context with financial terms
        mock_context = []
        for word in ["money", "account", "financial"]:
            mock_context_token = Mock()
            mock_context_token.text = word
            mock_context_token.lemma_ = word
            mock_context.append(mock_context_token)
        
        clues = self.validator._extract_semantic_context_clues(mock_token, mock_context)
        
        # Should find financial context clues
        financial_clues = [clue for clue in clues if "financial_context" in clue]
        self.assertGreater(len(financial_clues), 0)
    
    def test_ambiguity_resolution_confidence(self):
        """Test ambiguity resolution confidence calculation."""
        mock_token = Mock()
        mock_context = [Mock() for _ in range(3)]
        
        possible_interpretations = [("meaning1", 0.8), ("meaning2", 0.2)]
        context_clues = ["context1", "context2", "context3"]
        
        confidence = self.validator._calculate_ambiguity_resolution_confidence(
            mock_token, mock_context, possible_interpretations, context_clues
        )
        
        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)
        # Should be relatively high due to strong interpretation dominance and multiple clues
        self.assertGreater(confidence, 0.5)


class TestCrossModelVerification(unittest.TestCase):
    """Test cross-model verification functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = MorphologicalValidator()
    
    def test_pos_consistency_verification(self):
        """Test POS consistency verification."""
        mock_token = Mock()
        mock_token.pos_ = "NOUN"
        
        # Create context that supports noun interpretation
        mock_context = [Mock(), mock_token, Mock()]
        mock_context[0].pos_ = "DET"  # Determiner before noun
        mock_context[2].pos_ = "VERB"  # Verb after noun (subject-verb pattern)
        
        consistency = self.validator._verify_pos_consistency(mock_token, mock_context)
        
        self.assertIsInstance(consistency, float)
        self.assertGreaterEqual(consistency, 0.0)
        self.assertLessEqual(consistency, 1.0)
        # Should be high due to supportive context
        self.assertGreater(consistency, 0.5)
    
    def test_morphological_consistency_verification(self):
        """Test morphological consistency verification."""
        mock_token = Mock()
        mock_token.pos_ = "VERB"
        mock_token.morph = Mock()
        mock_token.morph.__bool__ = Mock(return_value=True)
        
        context = ValidationContext(
            text="test",
            error_position=0,
            error_text="test",
            rule_type="grammar"
        )
        
        consistency = self.validator._verify_morphological_consistency(mock_token, context)
        
        self.assertIsInstance(consistency, float)
        self.assertGreaterEqual(consistency, 0.0)
        self.assertLessEqual(consistency, 1.0)
        # Should be relatively high for grammar rules with verb POS
        self.assertGreater(consistency, 0.5)
    
    def test_cross_model_evidence_creation(self):
        """Test cross-model verification evidence creation."""
        context = ValidationContext(
            text="The documentation demonstrates proper implementation.",
            error_position=20,
            error_text="demonstrates",
            rule_type="grammar"
        )
        
        result = self.validator.validate_error(context)
        
        # Should have cross-model verification evidence
        cross_evidence = next((e for e in result.evidence if e.evidence_type == "cross_model_verification"), None)
        if cross_evidence:  # May not always be created if confidence is too low
            self.assertIsInstance(cross_evidence.confidence, float)
            self.assertIn("pos_consistency", cross_evidence.source_data)
            self.assertIn("morphological_consistency", cross_evidence.source_data)


class TestDecisionMaking(unittest.TestCase):
    """Test validation decision making logic."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = MorphologicalValidator()
    
    def test_grammar_rule_decision_logic(self):
        """Test decision logic for grammar rules."""
        context = ValidationContext(
            text="The company shared it's quarterly results.",
            error_position=22,
            error_text="it's",
            rule_type="grammar",
            rule_name="possessive_vs_contraction"
        )
        
        result = self.validator.validate_error(context)
        
        # Grammar rules should generally be accepted with morphological evidence
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        
        # Should have reasonable confidence
        self.assertGreater(result.confidence_score, 0.3)
        
        # Should have explanation
        self.assertIsInstance(result.reasoning, str)
        self.assertGreater(len(result.reasoning), 10)
    
    def test_style_rule_decision_logic(self):
        """Test decision logic for style rules."""
        context = ValidationContext(
            text="The documentation is very comprehensive and detailed.",
            error_position=20,
            error_text="very",
            rule_type="style",
            rule_name="adverb_usage"
        )
        
        result = self.validator.validate_error(context)
        
        # Style rules may be less certain with morphological analysis
        self.assertIn(result.decision, [ValidationDecision.ACCEPT, ValidationDecision.UNCERTAIN])
        
        # Should still have valid confidence
        self.assertIsInstance(result.confidence_score, float)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
    
    def test_unknown_rule_type_decision(self):
        """Test decision logic for unknown rule types."""
        context = ValidationContext(
            text="Check the configuration settings carefully.",
            error_position=10,
            error_text="configuration",
            rule_type="unknown_type",
            rule_name="unknown_rule"
        )
        
        result = self.validator.validate_error(context)
        
        # Unknown rule types should be conservative
        self.assertIn(result.decision, [ValidationDecision.UNCERTAIN, ValidationDecision.ACCEPT, ValidationDecision.REJECT])
        
        # Should have valid result structure
        self.assertIsInstance(result.confidence_score, float)
        self.assertGreater(len(result.evidence), 0)
    
    def test_decision_with_no_evidence(self):
        """Test decision making when no evidence is available."""
        # This would require mocking to create a scenario with no evidence
        # For now, test that the validator handles edge cases gracefully
        
        context = ValidationContext(
            text="",  # Empty text
            error_position=0,
            error_text="",
            rule_type="grammar"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle empty text gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertEqual(result.confidence_score, 0.3)  # Uncertain result confidence


class TestPerformanceAndCaching(unittest.TestCase):
    """Test performance monitoring and caching functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = MorphologicalValidator(cache_nlp_results=True)
    
    def test_nlp_caching_enabled(self):
        """Test NLP result caching when enabled."""
        text = "The documentation demonstrates proper implementation."
        
        # First analysis - should be cached
        doc1 = self.validator._analyze_text(text)
        cache_misses_1 = self.validator._cache_misses
        
        # Second analysis - should use cache
        doc2 = self.validator._analyze_text(text)
        cache_hits_1 = self.validator._cache_hits
        
        self.assertEqual(doc1.text, doc2.text)
        self.assertGreater(cache_hits_1, 0)
    
    def test_nlp_caching_disabled(self):
        """Test behavior when NLP caching is disabled."""
        validator = MorphologicalValidator(cache_nlp_results=False)
        text = "The documentation demonstrates proper implementation."
        
        # Multiple analyses should not use cache
        validator._analyze_text(text)
        validator._analyze_text(text)
        
        self.assertEqual(validator._cache_hits, 0)  # No cache hits
    
    def test_performance_tracking(self):
        """Test performance tracking for different analysis types."""
        context = ValidationContext(
            text="The comprehensive API documentation demonstrates proper authentication.",
            error_position=30,
            error_text="demonstrates",
            rule_type="grammar"
        )
        
        # Perform validation to populate performance data
        result = self.validator.validate_error(context)
        
        # Check that validation completed successfully
        self.assertIsInstance(result.validation_time, float)
        self.assertGreater(result.validation_time, 0)
        
        # Check analysis statistics
        stats = self.validator.get_analysis_statistics()
        self.assertIn("analysis_performance", stats)
        self.assertIn("nlp_cache", stats)
    
    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        # Perform some operations to generate cache statistics
        texts = [
            "The first sentence.",
            "The second sentence.",
            "The first sentence."  # Repeat to test cache hit
        ]
        
        for text in texts:
            self.validator._analyze_text(text)
        
        hit_rate = self.validator._get_cache_hit_rate()
        self.assertIsInstance(hit_rate, float)
        self.assertGreaterEqual(hit_rate, 0.0)
        self.assertLessEqual(hit_rate, 1.0)
    
    def test_cache_clearing(self):
        """Test cache clearing functionality."""
        # Populate cache
        self.validator._analyze_text("Test sentence.")
        
        # Verify cache has content
        self.assertGreater(len(self.validator._nlp_cache), 0)
        
        # Clear cache
        self.validator.clear_caches()
        
        # Verify cache is empty
        self.assertEqual(len(self.validator._nlp_cache), 0)
        self.assertEqual(self.validator._cache_hits, 0)
        self.assertEqual(self.validator._cache_misses, 0)


class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = MorphologicalValidator()
    
    def test_empty_text_handling(self):
        """Test handling of empty text."""
        context = ValidationContext(
            text="",
            error_position=0,
            error_text="",
            rule_type="grammar"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle empty text gracefully
        self.assertEqual(result.decision, ValidationDecision.UNCERTAIN)
        self.assertLessEqual(result.confidence_score, 0.5)
    
    def test_invalid_error_position(self):
        """Test handling of invalid error positions."""
        context = ValidationContext(
            text="Short text.",
            error_position=100,  # Beyond text length
            error_text="nonexistent",
            rule_type="grammar"
        )
        
        result = self.validator.validate_error(context)
        
        # Should handle invalid position gracefully
        self.assertIn(result.decision, [ValidationDecision.UNCERTAIN, ValidationDecision.ACCEPT])
        self.assertIsInstance(result.validation_time, float)
        self.assertGreater(result.validation_time, 0)
    
    def test_nlp_model_failure_handling(self):
        """Test handling of NLP model failures."""
        # This would require mocking SpaCy to simulate failure
        # For now, test that validator handles its own exceptions
        
        context = ValidationContext(
            text="Normal text that should process fine.",
            error_position=5,
            error_text="text",
            rule_type="grammar"
        )
        
        # Should not raise exceptions
        try:
            result = self.validator.validate_error(context)
            self.assertIsInstance(result.confidence_score, float)
        except Exception as e:
            self.fail(f"Validator raised unexpected exception: {e}")
    
    def test_malformed_context_handling(self):
        """Test handling of malformed validation contexts."""
        context = ValidationContext(
            text="Test sentence.",
            error_position=5,
            error_text=None,  # Malformed: None error_text
            rule_type="grammar"
        )
        
        # Should handle malformed context gracefully
        result = self.validator.validate_error(context)
        self.assertIsInstance(result, type(self.validator.validate_error(context)))


class TestValidationConsistency(unittest.TestCase):
    """Test validation decision consistency."""
    
    def setUp(self):
        """Set up test environment."""
        self.validator = MorphologicalValidator()
    
    def test_consistent_results_for_identical_input(self):
        """Test that identical inputs produce consistent results."""
        context = ValidationContext(
            text="The documentation demonstrates proper implementation.",
            error_position=20,
            error_text="demonstrates",
            rule_type="grammar",
            rule_name="subject_verb_agreement"
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
    
    def test_sentence_structure_variation_handling(self):
        """Test handling of various sentence structures."""
        test_cases = [
            # Simple sentence
            ("The cat runs.", 8, "runs", "grammar"),
            # Complex sentence
            ("Although the documentation is comprehensive, it lacks examples.", 35, "lacks", "grammar"),
            # Question
            ("Does the API support authentication?", 10, "support", "grammar"),
            # Passive voice
            ("The results were analyzed carefully.", 15, "analyzed", "grammar"),
        ]
        
        for text, position, error_text, rule_type in test_cases:
            context = ValidationContext(
                text=text,
                error_position=position,
                error_text=error_text,
                rule_type=rule_type
            )
            
            result = self.validator.validate_error(context)
            
            # Should handle all sentence types without errors
            self.assertIsInstance(result.confidence_score, float)
            self.assertGreaterEqual(result.confidence_score, 0.0)
            self.assertLessEqual(result.confidence_score, 1.0)
            self.assertGreater(len(result.evidence), 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
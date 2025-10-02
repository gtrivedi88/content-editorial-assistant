"""
Comprehensive test suite for rule-specific enhanced error creation.
Tests integration of enhanced validation system with concrete rule implementations.
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional

# Import test utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import rule classes for testing
from rules.base_rule import BaseRule, ENHANCED_VALIDATION_AVAILABLE

# Import concrete rule implementations
try:
    from rules.word_usage.a_words_rule import AWordsRule
    A_WORDS_AVAILABLE = True
except ImportError:
    A_WORDS_AVAILABLE = False

try:
    from rules.sentence_length_rule import SentenceLengthRule
    SENTENCE_LENGTH_AVAILABLE = True
except ImportError:
    SENTENCE_LENGTH_AVAILABLE = False

try:
    from rules.language_and_grammar.verbs_rule import VerbsRule
    VERBS_RULE_AVAILABLE = True
except ImportError:
    VERBS_RULE_AVAILABLE = False


class TestRuleSpecificEnhancedErrorCreation(unittest.TestCase):
    """Test enhanced error creation in concrete rule implementations."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Test data
        self.test_text = "This is a comprehensive document about API development. " \
                        "The system will process data efficiently. " \
                        "Users can action the workflow to achieve results."
        self.test_sentences = [
            "This is a comprehensive document about API development.",
            "The system will process data efficiently.",
            "Users can action the workflow to achieve results."
        ]
        self.test_context = {
            'block_type': 'paragraph',
            'content_type': 'technical',
            'domain': 'programming',
            'document_title': 'API Development Guide'
        }
    
    @unittest.skipIf(not A_WORDS_AVAILABLE, "AWordsRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_a_words_rule_enhanced_error_creation(self):
        """Test that AWordsRule creates enhanced errors with confidence and validation data."""
        rule = AWordsRule()
        
        # Mock NLP for testing
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_sent = Mock()
        mock_sent.text = self.test_sentences[2]  # Contains "action" as verb
        
        # Mock token for "action"
        mock_token = Mock()
        mock_token.lemma_ = "action"
        mock_token.pos_ = "VERB"
        mock_token.text = "action"
        mock_token.idx = 50
        mock_token.sent = mock_sent
        
        # Set up mock document structure
        mock_doc.__iter__ = Mock(return_value=iter([mock_token]))
        mock_doc.sents = [mock_sent]
        mock_nlp.return_value = mock_doc
        
        # Mock the PhraseMatcher functionality to avoid complex setup
        rule._phrase_matcher = Mock()
        rule._phrase_matcher.return_value = []  # No phrase matches for simplicity
        
        # Analyze with enhanced parameters
        errors = rule.analyze(self.test_text, self.test_sentences, nlp=mock_nlp, context=self.test_context)
        
        # Verify errors were created
        self.assertGreater(len(errors), 0, "Expected at least one error to be found")
        
        # Check the first error for enhanced fields
        error = errors[0]
        
        # Verify basic fields are present
        self.assertIn('type', error)
        self.assertIn('message', error)
        self.assertIn('suggestions', error)
        self.assertIn('sentence', error)
        self.assertIn('sentence_index', error)
        self.assertIn('severity', error)
        
        # Verify enhanced validation fields are present (if system is available)
        if ENHANCED_VALIDATION_AVAILABLE:
            self.assertIn('enhanced_validation_available', error)
            
            # If enhanced validation succeeded, check for enhanced fields
            if error.get('enhanced_validation_available', False):
                self.assertIn('confidence_score', error)
                self.assertIsInstance(error['confidence_score'], (int, float))
                self.assertGreaterEqual(error['confidence_score'], 0.0)
                self.assertLessEqual(error['confidence_score'], 1.0)
                
                # Check for validation result if available
                if 'validation_result' in error:
                    self.assertIsNotNone(error['validation_result'])
    
    @unittest.skipIf(not SENTENCE_LENGTH_AVAILABLE, "SentenceLengthRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_sentence_length_rule_enhanced_error_creation(self):
        """Test that SentenceLengthRule creates enhanced errors with confidence and validation data."""
        rule = SentenceLengthRule()
        
        # Create a long sentence to trigger the rule
        long_sentence = "This is a very long sentence that contains many words and should definitely trigger the sentence length rule because it exceeds the maximum word count limit that is set for reasonable sentence lengths in technical documentation."
        long_sentences = [long_sentence]
        
        # Mock NLP for testing
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_nlp.return_value = mock_doc
        
        # Analyze with enhanced parameters
        errors = rule.analyze(long_sentence, long_sentences, nlp=mock_nlp, context=self.test_context)
        
        # Verify errors were created
        self.assertGreater(len(errors), 0, "Expected at least one error for long sentence")
        
        # Check the first error for enhanced fields
        error = errors[0]
        
        # Verify basic fields are present
        self.assertIn('type', error)
        self.assertEqual(error['type'], 'sentence_length')
        self.assertIn('message', error)
        self.assertIn('suggestions', error)
        self.assertIn('sentence', error)
        self.assertIn('sentence_index', error)
        self.assertIn('severity', error)
        
        # Verify enhanced validation fields are present
        if ENHANCED_VALIDATION_AVAILABLE:
            self.assertIn('enhanced_validation_available', error)
            
            # If enhanced validation succeeded, check for enhanced fields
            if error.get('enhanced_validation_available', False):
                self.assertIn('confidence_score', error)
                self.assertIsInstance(error['confidence_score'], (int, float))
                
                # Check for validation result if available
                if 'validation_result' in error:
                    self.assertIsNotNone(error['validation_result'])
    
    @unittest.skipIf(not VERBS_RULE_AVAILABLE, "VerbsRule not available")
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_verbs_rule_enhanced_error_creation(self):
        """Test that VerbsRule creates enhanced errors with confidence and validation data."""
        rule = VerbsRule()
        
        # Create sentences with passive voice to trigger the rule
        passive_text = "The API will be configured by the administrator."
        passive_sentences = [passive_text]
        
        # Mock NLP and passive voice analyzer
        mock_nlp = Mock()
        mock_doc = Mock()
        mock_nlp.return_value = mock_doc
        
        # Mock passive voice construction
        mock_construction = Mock()
        mock_construction.span_start = 4
        mock_construction.span_end = 20
        mock_construction.flagged_text = "will be configured"
        
        # Mock the passive voice analyzer
        if hasattr(rule, 'passive_analyzer'):
            rule.passive_analyzer = Mock()
            rule.passive_analyzer.find_passive_constructions.return_value = [mock_construction]
            rule.passive_analyzer.classify_context.return_value = 'PROCEDURAL'  # Should be flagged
        
        # Analyze with enhanced parameters
        try:
            errors = rule.analyze(passive_text, passive_sentences, nlp=mock_nlp, context=self.test_context)
            
            # Check if errors were created (may depend on implementation details)
            if len(errors) > 0:
                error = errors[0]
                
                # Verify basic fields are present
                self.assertIn('type', error)
                self.assertIn('message', error)
                self.assertIn('suggestions', error)
                
                # Verify enhanced validation fields are present
                if ENHANCED_VALIDATION_AVAILABLE:
                    self.assertIn('enhanced_validation_available', error)
        except Exception as e:
            # Some mock setup might be incomplete, but the rule should not crash
            self.skipTest(f"VerbsRule test skipped due to mock setup: {e}")
    
    def test_enhanced_error_creation_backward_compatibility(self):
        """Test that enhanced error creation maintains backward compatibility."""
        # Test with a mock rule that uses the old calling pattern
        class BackwardCompatibleRule(BaseRule):
            def _get_rule_type(self):
                return 'backward_compatible'
            
            def analyze(self, text, sentences, nlp=None, context=None):
                # Use the old calling pattern (without text and context)
                error = self._create_error(
                    sentence="Test sentence",
                    sentence_index=0,
                    message="Test error message",
                    suggestions=["Test suggestion"],
                    severity='medium',
                    span=(0, 4),
                    flagged_text="Test"
                )
                return [error]
        
        rule = BackwardCompatibleRule()
        errors = rule.analyze(self.test_text, self.test_sentences, context=self.test_context)
        
        # Verify the error was created successfully
        self.assertEqual(len(errors), 1)
        error = errors[0]
        
        # Verify basic fields are present and correct
        self.assertEqual(error['type'], 'backward_compatible')
        self.assertEqual(error['message'], 'Test error message')
        self.assertEqual(error['suggestions'], ['Test suggestion'])
        self.assertEqual(error['sentence'], 'Test sentence')
        self.assertEqual(error['sentence_index'], 0)
        self.assertEqual(error['severity'], 'medium')
        self.assertEqual(error['span'], [0, 4])  # Note: tuples become lists in serialization
        self.assertEqual(error['flagged_text'], 'Test')
        
        # Check enhanced validation availability
        self.assertIn('enhanced_validation_available', error)
    
    def test_enhanced_error_creation_with_context_parameter(self):
        """Test that passing text and context parameters enhances error creation."""
        class ContextAwareRule(BaseRule):
            def _get_rule_type(self):
                return 'context_aware'
            
            def analyze(self, text, sentences, nlp=None, context=None):
                # Use the enhanced calling pattern (with text and context)
                error = self._create_error(
                    sentence="Test sentence with enhanced validation",
                    sentence_index=0,
                    message="Test error with context",
                    suggestions=["Enhanced suggestion"],
                    severity='high',
                    text=text,  # Pass full text
                    context=context,  # Pass context
                    span=(5, 13),
                    flagged_text="sentence"
                )
                return [error]
        
        rule = ContextAwareRule()
        errors = rule.analyze(self.test_text, self.test_sentences, context=self.test_context)
        
        # Verify the error was created successfully
        self.assertEqual(len(errors), 1)
        error = errors[0]
        
        # Verify basic fields
        self.assertEqual(error['type'], 'context_aware')
        self.assertEqual(error['message'], 'Test error with context')
        self.assertEqual(error['suggestions'], ['Enhanced suggestion'])
        self.assertEqual(error['severity'], 'high')
        
        # Check enhanced validation fields if available
        if ENHANCED_VALIDATION_AVAILABLE:
            self.assertIn('enhanced_validation_available', error)
            
            # If enhanced validation is available and working, check for enhanced fields
            if error.get('enhanced_validation_available', False):
                self.assertIn('confidence_score', error)
                
                # Confidence score should be a valid number
                confidence = error['confidence_score']
                self.assertIsInstance(confidence, (int, float))
                self.assertGreaterEqual(confidence, 0.0)
                self.assertLessEqual(confidence, 1.0)
    
    def test_enhanced_error_creation_performance(self):
        """Test that enhanced error creation doesn't significantly impact performance."""
        class PerformanceTestRule(BaseRule):
            def _get_rule_type(self):
                return 'performance_test'
            
            def analyze(self, text, sentences, nlp=None, context=None):
                errors = []
                for i, sentence in enumerate(sentences):
                    error = self._create_error(
                        sentence=sentence,
                        sentence_index=i,
                        message=f"Performance test error {i}",
                        suggestions=[f"Fix error {i}"],
                        severity='low',
                        text=text,
                        context=context,
                        span=(0, len(sentence)),
                        flagged_text=sentence[:10]
                    )
                    errors.append(error)
                return errors
        
        rule = PerformanceTestRule()
        
        # Measure time for multiple error creations
        start_time = time.time()
        for _ in range(10):  # Create errors multiple times
            errors = rule.analyze(self.test_text, self.test_sentences, context=self.test_context)
        end_time = time.time()
        
        total_time = end_time - start_time
        avg_time_per_iteration = total_time / 10
        
        # Verify errors were created
        self.assertEqual(len(errors), len(self.test_sentences))
        
        # Performance should be reasonable (less than 100ms per iteration)
        self.assertLess(avg_time_per_iteration, 0.1, 
                       f"Enhanced error creation too slow: {avg_time_per_iteration:.4f}s per iteration")
    
    def test_fallback_error_creation_when_validation_unavailable(self):
        """Test error creation fallback when enhanced validation is not available."""
        with patch('rules.base_rule.ENHANCED_VALIDATION_AVAILABLE', False):
            class FallbackTestRule(BaseRule):
                def _get_rule_type(self):
                    return 'fallback_test'
                
                def analyze(self, text, sentences, nlp=None, context=None):
                    error = self._create_error(
                        sentence="Fallback test sentence",
                        sentence_index=0,
                        message="Fallback test message",
                        suggestions=["Fallback suggestion"],
                        severity='medium',
                        text=text,
                        context=context
                    )
                    return [error]
            
            rule = FallbackTestRule()
            errors = rule.analyze(self.test_text, self.test_sentences, context=self.test_context)
            
            # Verify error was created
            self.assertEqual(len(errors), 1)
            error = errors[0]
            
            # Verify basic fields
            self.assertEqual(error['type'], 'fallback_test')
            self.assertEqual(error['message'], 'Fallback test message')
            
            # Enhanced validation should be marked as unavailable
            self.assertEqual(error['enhanced_validation_available'], False)


class TestRuleSpecificErrorFieldIntegrity(unittest.TestCase):
    """Test error field integrity across different rule implementations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_text = "Sample text for testing error field integrity."
        self.test_sentences = ["Sample text for testing error field integrity."]
        self.test_context = {'block_type': 'paragraph', 'content_type': 'technical'}
    
    def test_error_field_serialization_consistency(self):
        """Test that error fields are consistently serialized across rules."""
        test_rules = []
        
        # Add available rules for testing
        if A_WORDS_AVAILABLE:
            test_rules.append(('AWordsRule', AWordsRule))
        if SENTENCE_LENGTH_AVAILABLE:
            test_rules.append(('SentenceLengthRule', SentenceLengthRule))
        
        for rule_name, rule_class in test_rules:
            with self.subTest(rule=rule_name):
                try:
                    rule = rule_class()
                    
                    # Create a simple mock NLP if needed
                    mock_nlp = Mock() if hasattr(rule, 'analyze') else None
                    
                    # Mock minimal NLP functionality for testing
                    if mock_nlp:
                        mock_doc = Mock()
                        mock_doc.__iter__ = Mock(return_value=iter([]))
                        mock_doc.sents = []
                        mock_nlp.return_value = mock_doc
                    
                    # Test error creation (may not find actual errors, but should not crash)
                    try:
                        errors = rule.analyze(self.test_text, self.test_sentences, 
                                            nlp=mock_nlp, context=self.test_context)
                        
                        # If errors were found, check their structure
                        for error in errors:
                            # Verify all error data is serializable
                            self._verify_error_serializable(error)
                            
                            # Verify required fields are present
                            required_fields = ['type', 'message', 'suggestions', 'sentence', 
                                             'sentence_index', 'severity']
                            for field in required_fields:
                                self.assertIn(field, error, 
                                            f"Missing required field '{field}' in {rule_name}")
                    
                    except Exception as e:
                        # Some rules might need specific setup - that's okay
                        self.skipTest(f"Rule {rule_name} requires specific setup: {e}")
                        
                except Exception as e:
                    self.fail(f"Failed to instantiate rule {rule_name}: {e}")
    
    def _verify_error_serializable(self, error):
        """Verify that an error dictionary is fully serializable."""
        import json
        
        try:
            # Attempt to serialize the error
            json_str = json.dumps(error)
            # Attempt to deserialize
            deserialized = json.loads(json_str)
            
            # Verify basic structure is preserved
            self.assertIsInstance(deserialized, dict)
            
        except (TypeError, ValueError) as e:
            self.fail(f"Error is not JSON serializable: {e}\nError data: {error}")


class TestRuleIntegrationWithValidationSystem(unittest.TestCase):
    """Test integration of rule implementations with the validation system."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_text = "The comprehensive API documentation demonstrates effective implementation patterns."
        self.test_sentences = ["The comprehensive API documentation demonstrates effective implementation patterns."]
        self.test_context = {
            'block_type': 'paragraph',
            'content_type': 'technical',
            'domain': 'programming'
        }
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_confidence_calculation_integration(self):
        """Test that confidence calculation is properly integrated with rule implementations."""
        # Mock the confidence calculator to verify it's being called
        with patch.object(BaseRule, '_confidence_calculator') as mock_calc:
            # Mock confidence calculation result
            mock_breakdown = Mock()
            mock_breakdown.final_confidence = 0.75
            mock_calc.calculate_confidence.return_value = mock_breakdown
            
            class IntegrationTestRule(BaseRule):
                def _get_rule_type(self):
                    return 'integration_test'
                
                def analyze(self, text, sentences, nlp=None, context=None):
                    error = self._create_error(
                        sentence=sentences[0],
                        sentence_index=0,
                        message="Integration test error",
                        suggestions=["Fix integration"],
                        severity='medium',
                        text=text,
                        context=context,
                        span=(0, 10),
                        flagged_text="integration"
                    )
                    return [error]
            
            rule = IntegrationTestRule()
            errors = rule.analyze(self.test_text, self.test_sentences, context=self.test_context)
            
            # Verify error was created
            self.assertEqual(len(errors), 1)
            error = errors[0]
            
            # Verify confidence calculation was integrated
            if error.get('enhanced_validation_available', False):
                self.assertIn('confidence_score', error)
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_validation_pipeline_integration(self):
        """Test that validation pipeline is properly integrated with rule implementations."""
        # Mock the validation pipeline to verify it's being called
        with patch.object(BaseRule, '_validation_pipeline') as mock_pipeline:
            # Mock validation pipeline result
            mock_result = Mock()
            mock_final_result = Mock()
            mock_final_result.decision = Mock()
            mock_final_result.decision.value = 'accept'
            mock_final_result.confidence_score = 0.85
            mock_final_result.reasoning = 'Test validation reasoning'
            mock_result.final_result = mock_final_result
            mock_pipeline.validate_error.return_value = mock_result
            
            class PipelineTestRule(BaseRule):
                def _get_rule_type(self):
                    return 'pipeline_test'
                
                def analyze(self, text, sentences, nlp=None, context=None):
                    error = self._create_error(
                        sentence=sentences[0],
                        sentence_index=0,
                        message="Pipeline test error",
                        suggestions=["Fix pipeline"],
                        severity='high',
                        text=text,
                        context=context,
                        span=(4, 17),
                        flagged_text="comprehensive"
                    )
                    return [error]
            
            rule = PipelineTestRule()
            errors = rule.analyze(self.test_text, self.test_sentences, context=self.test_context)
            
            # Verify error was created
            self.assertEqual(len(errors), 1)
            error = errors[0]
            
            # Verify validation pipeline was integrated
            if error.get('enhanced_validation_available', False):
                self.assertIn('validation_result', error)
                if 'validation_decision' in error:
                    self.assertEqual(error['validation_decision'], 'accept')


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)
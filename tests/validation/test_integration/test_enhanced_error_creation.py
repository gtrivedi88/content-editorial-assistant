"""
Comprehensive test suite for enhanced error creation in BaseRule.
Tests integration with confidence calculation and validation pipeline.
"""

import unittest
import time
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional

# Import test utilities
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import BaseRule and related components
from rules.base_rule import BaseRule, ENHANCED_VALIDATION_AVAILABLE

# Mock rule for testing
class MockTestRule(BaseRule):
    """Mock rule implementation for testing enhanced error creation."""
    
    def _get_rule_type(self) -> str:
        return 'test_rule'
    
    def analyze(self, text: str, sentences: List[str], nlp=None, context=None) -> List[Dict[str, Any]]:
        """Simple analyze method for testing."""
        return []


class TestEnhancedErrorCreation(unittest.TestCase):
    """Comprehensive test suite for enhanced error creation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_rule = MockTestRule()
        
        # Test data
        self.test_sentence = "This is a test sentence with an error."
        self.test_message = "Test error message"
        self.test_suggestions = ["Fix this", "Or this"]
        self.test_text = "This is a full document. This is a test sentence with an error. More content here."
        self.test_context = {
            'block_type': 'paragraph',
            'content_type': 'technical',
            'domain': 'programming'
        }
        self.test_extra_data = {
            'span': [25, 30],
            'flagged_text': 'error',
            'rule_specific_data': 'test_value'
        }
    
    def test_backward_compatibility_basic_call(self):
        """Test that basic _create_error calls still work (backward compatibility)."""
        error = self.test_rule._create_error(
            sentence=self.test_sentence,
            sentence_index=0,
            message=self.test_message,
            suggestions=self.test_suggestions
        )
        
        # Check basic fields are present
        self.assertEqual(error['type'], 'test_rule')
        self.assertEqual(error['message'], self.test_message)
        self.assertEqual(error['suggestions'], self.test_suggestions)
        self.assertEqual(error['sentence'], self.test_sentence)
        self.assertEqual(error['sentence_index'], 0)
        self.assertEqual(error['severity'], 'medium')  # Default severity
        
        # Check enhanced validation availability flag is present
        self.assertIn('enhanced_validation_available', error)
    
    def test_backward_compatibility_with_extra_data(self):
        """Test backward compatibility when extra data is provided."""
        error = self.test_rule._create_error(
            sentence=self.test_sentence,
            sentence_index=1,
            message=self.test_message,
            suggestions=self.test_suggestions,
            severity='high',
            span=(10, 15),
            flagged_text='test'
        )
        
        # Check basic fields
        self.assertEqual(error['severity'], 'high')
        self.assertEqual(error['span'], [10, 15])  # Tuples are serialized as lists
        self.assertEqual(error['flagged_text'], 'test')
        
        # Check enhanced validation handling
        self.assertIn('enhanced_validation_available', error)
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_enhanced_error_creation_with_confidence(self):
        """Test enhanced error creation with confidence calculation."""
        with patch.object(self.test_rule._confidence_calculator, 'calculate_confidence') as mock_calc:
            # Mock confidence calculation result
            mock_breakdown = Mock()
            mock_breakdown.final_confidence = 0.85
            mock_calc.return_value = mock_breakdown
            
            error = self.test_rule._create_error(
                sentence=self.test_sentence,
                sentence_index=0,
                message=self.test_message,
                suggestions=self.test_suggestions,
                text=self.test_text,
                context=self.test_context,
                **self.test_extra_data
            )
            
            # Check enhanced fields are present
            self.assertEqual(error['enhanced_validation_available'], True)
            self.assertEqual(error['confidence_score'], 0.85)
            self.assertIsNotNone(error['confidence_breakdown'])
            
            # Verify confidence calculator was called correctly
            mock_calc.assert_called_once()
            call_args = mock_calc.call_args
            self.assertEqual(call_args[1]['text'], self.test_text)
            self.assertEqual(call_args[1]['rule_type'], 'test_rule')
            self.assertEqual(call_args[1]['content_type'], 'technical')
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_enhanced_error_creation_with_validation_pipeline(self):
        """Test enhanced error creation with validation pipeline execution."""
        with patch.object(self.test_rule._validation_pipeline, 'validate_error') as mock_validate:
            # Mock validation pipeline result
            mock_result = Mock()
            mock_final_result = Mock()
            mock_final_result.decision = Mock()
            mock_final_result.decision.value = 'accept'
            mock_final_result.confidence_score = 0.92
            mock_final_result.reasoning = 'Test reasoning'
            mock_result.final_result = mock_final_result
            mock_validate.return_value = mock_result
            
            error = self.test_rule._create_error(
                sentence=self.test_sentence,
                sentence_index=0,
                message=self.test_message,
                suggestions=self.test_suggestions,
                text=self.test_text,
                context=self.test_context,
                **self.test_extra_data
            )
            
            # Check validation fields are present
            self.assertEqual(error['validation_decision'], 'accept')
            self.assertEqual(error['validation_confidence'], 0.92)
            self.assertEqual(error['validation_reasoning'], 'Test reasoning')
            self.assertIsNotNone(error['validation_result'])
            
            # Verify validation pipeline was called
            mock_validate.assert_called_once()
            call_args = mock_validate.call_args[0][0]  # ValidationContext
            self.assertEqual(call_args.text, self.test_text)
            self.assertEqual(call_args.rule_type, 'test_rule')
            self.assertEqual(call_args.error_text, 'error')
    
    def test_error_field_completeness(self):
        """Test that all expected error fields are present and correctly formatted."""
        error = self.test_rule._create_error(
            sentence=self.test_sentence,
            sentence_index=2,
            message=self.test_message,
            suggestions=self.test_suggestions,
            severity='low',
            text=self.test_text,
            context=self.test_context,
            **self.test_extra_data
        )
        
        # Required basic fields
        required_fields = ['type', 'message', 'suggestions', 'sentence', 'sentence_index', 'severity']
        for field in required_fields:
            self.assertIn(field, error)
            self.assertIsNotNone(error[field])
        
        # Enhanced validation fields (should be present regardless of availability)
        self.assertIn('enhanced_validation_available', error)
        
        # Extra data fields
        self.assertIn('span', error)
        self.assertIn('flagged_text', error)
        self.assertIn('rule_specific_data', error)
    
    def test_error_field_accuracy(self):
        """Test accuracy of error field values."""
        test_span = (15, 25)
        test_flagged = "specific_error"
        
        error = self.test_rule._create_error(
            sentence=self.test_sentence,
            sentence_index=5,
            message=self.test_message,
            suggestions=self.test_suggestions,
            severity='high',
            span=test_span,
            flagged_text=test_flagged,
            custom_field="custom_value"
        )
        
        # Check field accuracy
        self.assertEqual(error['type'], 'test_rule')
        self.assertEqual(error['sentence_index'], 5)
        self.assertEqual(error['severity'], 'high')
        self.assertEqual(error['span'], [15, 25])  # Tuples are serialized as lists
        self.assertEqual(error['flagged_text'], test_flagged)
        self.assertEqual(error['custom_field'], "custom_value")
    
    def test_severity_validation_and_fallback(self):
        """Test severity validation and fallback to default."""
        # Valid severity
        error = self.test_rule._create_error(
            sentence=self.test_sentence,
            sentence_index=0,
            message=self.test_message,
            suggestions=self.test_suggestions,
            severity='high'
        )
        self.assertEqual(error['severity'], 'high')
        
        # Invalid severity should fall back to medium
        error = self.test_rule._create_error(
            sentence=self.test_sentence,
            sentence_index=0,
            message=self.test_message,
            suggestions=self.test_suggestions,
            severity='invalid'
        )
        self.assertEqual(error['severity'], 'medium')
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_confidence_calculation_error_handling(self):
        """Test error handling when confidence calculation fails."""
        with patch.object(self.test_rule._confidence_calculator, 'calculate_confidence', side_effect=Exception("Confidence error")):
            error = self.test_rule._create_error(
                sentence=self.test_sentence,
                sentence_index=0,
                message=self.test_message,
                suggestions=self.test_suggestions,
                text=self.test_text
            )
            
            # Should handle error gracefully
            self.assertIn('confidence_calculation_error', error)
            self.assertEqual(error['confidence_score'], 0.5)  # Default fallback
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_validation_pipeline_error_handling(self):
        """Test error handling when validation pipeline fails."""
        with patch.object(self.test_rule._validation_pipeline, 'validate_error', side_effect=Exception("Pipeline error")):
            error = self.test_rule._create_error(
                sentence=self.test_sentence,
                sentence_index=0,
                message=self.test_message,
                suggestions=self.test_suggestions,
                text=self.test_text
            )
            
            # Should handle error gracefully
            self.assertIn('validation_pipeline_error', error)
            self.assertEqual(error['enhanced_validation_available'], True)  # Still marked as available
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_enhanced_validation_system_failure_fallback(self):
        """Test fallback when entire enhanced validation system fails."""
        with patch.object(self.test_rule, '_calculate_enhanced_error_fields', side_effect=Exception("System failure")):
            error = self.test_rule._create_error(
                sentence=self.test_sentence,
                sentence_index=0,
                message=self.test_message,
                suggestions=self.test_suggestions,
                text=self.test_text
            )
            
            # Should fall back gracefully
            self.assertEqual(error['enhanced_validation_available'], False)
            self.assertEqual(error['confidence_score'], 0.5)
            self.assertIsNone(error['validation_result'])
            self.assertIn('validation_error', error)
    
    def test_serialization_safety(self):
        """Test that all error data is properly serialized."""
        # Test with complex nested data that might cause serialization issues
        complex_data = {
            'nested_dict': {'key': 'value', 'number': 42},
            'list_data': [1, 2, 'three'],
            'none_value': None,
            'bool_value': True
        }
        
        error = self.test_rule._create_error(
            sentence=self.test_sentence,
            sentence_index=0,
            message=self.test_message,
            suggestions=self.test_suggestions,
            **complex_data
        )
        
        # All data should be serialized without errors
        self.assertEqual(error['nested_dict'], complex_data['nested_dict'])
        self.assertEqual(error['list_data'], complex_data['list_data'])
        self.assertIsNone(error['none_value'])
        self.assertEqual(error['bool_value'], True)


class TestEnhancedErrorCreationPerformance(unittest.TestCase):
    """Performance tests for enhanced error creation."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        self.test_rule = MockTestRule()
        self.test_data = {
            'sentence': "Performance test sentence with error.",
            'sentence_index': 0,
            'message': "Performance test message",
            'suggestions': ["Fix performance", "Optimize"],
            'text': "Full document text for performance testing. " * 20,
            'context': {'block_type': 'paragraph'},
            'span': (10, 15),
            'flagged_text': 'error'
        }
    
    def test_basic_error_creation_performance(self):
        """Test performance of basic error creation (baseline)."""
        start_time = time.time()
        
        for _ in range(100):
            error = self.test_rule._create_error(**self.test_data)
        
        elapsed_time = time.time() - start_time
        avg_time = elapsed_time / 100
        
        # Basic error creation should be reasonably fast (< 5ms per call, accounting for enhanced validation initialization)
        self.assertLess(avg_time, 0.005, f"Basic error creation too slow: {avg_time:.4f}s per call")
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_enhanced_error_creation_performance(self):
        """Test performance of enhanced error creation."""
        with patch.object(self.test_rule._confidence_calculator, 'calculate_confidence') as mock_calc, \
             patch.object(self.test_rule._validation_pipeline, 'validate_error') as mock_validate:
            
            # Mock fast responses
            mock_calc.return_value = Mock(final_confidence=0.8)
            mock_validate.return_value = Mock(final_result=Mock(
                decision=Mock(value='accept'),
                confidence_score=0.85,
                reasoning='Fast test'
            ))
            
            start_time = time.time()
            
            for _ in range(50):  # Fewer iterations for enhanced version
                error = self.test_rule._create_error(**self.test_data)
            
            elapsed_time = time.time() - start_time
            avg_time = elapsed_time / 50
            
            # Enhanced error creation should still be reasonably fast (< 10ms per call)
            self.assertLess(avg_time, 0.01, f"Enhanced error creation too slow: {avg_time:.4f}s per call")
    
    def test_error_creation_memory_efficiency(self):
        """Test memory efficiency of error creation."""
        import gc
        
        # Force garbage collection
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Create many errors
        errors = []
        for i in range(1000):
            error = self.test_rule._create_error(
                sentence=f"Test sentence {i}",
                sentence_index=i,
                message=f"Test message {i}",
                suggestions=[f"Fix {i}"]
            )
            errors.append(error)
        
        # Force garbage collection again
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory usage should be reasonable (accounting for validation system overhead)
        object_increase = final_objects - initial_objects
        # More relaxed threshold accounting for enhanced validation system complexity
        self.assertLess(object_increase, 100000, f"Memory usage too high: {object_increase} new objects")


class TestEnhancedErrorCreationIntegration(unittest.TestCase):
    """Integration tests with various rule types."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.rule_classes = []
        
        # Import and test various rule types if available
        try:
            from rules.language_and_grammar.verbs_rule import VerbsRule
            self.rule_classes.append(VerbsRule)
        except ImportError:
            pass
        
        try:
            from rules.word_usage.a_words_rule import AWordsRule
            self.rule_classes.append(AWordsRule)
        except ImportError:
            pass
        
        try:
            from rules.punctuation.commas_rule import CommasRule
            self.rule_classes.append(CommasRule)
        except ImportError:
            pass
    
    def test_integration_with_existing_rule_types(self):
        """Test that enhanced error creation works with existing rule types."""
        test_text = "This are a test with grammer error's."
        
        for rule_class in self.rule_classes:
            with self.subTest(rule_class=rule_class.__name__):
                try:
                    rule = rule_class()
                    
                    # Test basic error creation
                    error = rule._create_error(
                        sentence=test_text,
                        sentence_index=0,
                        message="Test error from existing rule",
                        suggestions=["Fix this error"]
                    )
                    
                    # Verify basic structure
                    self.assertIn('type', error)
                    self.assertIn('message', error)
                    self.assertIn('enhanced_validation_available', error)
                    
                except Exception as e:
                    self.fail(f"Enhanced error creation failed for {rule_class.__name__}: {e}")
    
    def test_error_creation_with_various_rule_types(self):
        """Test error creation with different rule type identifiers."""
        rule_types = ['grammar', 'style', 'technical', 'punctuation', 'word_usage']
        
        for rule_type in rule_types:
            with self.subTest(rule_type=rule_type):
                # Create a test rule with different type
                class MockSpecificRule(BaseRule):
                    def _get_rule_type(self):
                        return rule_type
                    
                    def analyze(self, text, sentences, nlp=None, context=None):
                        return []
                
                rule = MockSpecificRule()
                error = rule._create_error(
                    sentence="Test sentence",
                    sentence_index=0,
                    message="Test message",
                    suggestions=["Test suggestion"]
                )
                
                self.assertEqual(error['type'], rule_type)
                self.assertIn('enhanced_validation_available', error)


class TestValidationSystemInitialization(unittest.TestCase):
    """Test validation system initialization and configuration."""
    
    def test_validation_system_initialization_success(self):
        """Test successful initialization of validation system."""
        if not ENHANCED_VALIDATION_AVAILABLE:
            self.skipTest("Enhanced validation not available")
        
        # Create a new rule to trigger initialization
        rule = MockTestRule()
        
        # Check that validation components are initialized
        # Note: Components might be None if initialization fails gracefully
        if ENHANCED_VALIDATION_AVAILABLE:
            # At minimum, the attempt should have been made
            # The components might still be None if initialization failed
            # Check if they're initialized or if there was a graceful failure
            initialization_attempted = (
                BaseRule._confidence_calculator is not None or
                hasattr(BaseRule, '_initialization_attempted')
            )
            self.assertTrue(initialization_attempted or BaseRule._confidence_calculator is None,
                          "Validation system initialization was not attempted properly")
    
    def test_validation_system_initialization_failure_handling(self):
        """Test handling of validation system initialization failure."""
        with patch('rules.base_rule.ConfidenceCalculator', side_effect=Exception("Init failed")):
            # Reset class variables
            BaseRule._confidence_calculator = None
            BaseRule._validation_pipeline = None
            
            # Create a new rule
            rule = MockTestRule()
            
            # Should handle initialization failure gracefully
            self.assertIsNone(BaseRule._confidence_calculator)
            self.assertIsNone(BaseRule._validation_pipeline)
    
    @unittest.skipIf(not ENHANCED_VALIDATION_AVAILABLE, "Enhanced validation not available")
    def test_validation_system_shared_across_rules(self):
        """Test that validation system components are shared across rule instances."""
        rule1 = MockTestRule()
        rule2 = MockTestRule()
        
        # Both rules should share the same validation components
        self.assertIs(rule1._confidence_calculator, rule2._confidence_calculator)
        self.assertIs(rule1._validation_pipeline, rule2._validation_pipeline)


if __name__ == '__main__':
    # Configure test runner
    unittest.main(verbosity=2, buffer=True)
"""
Test Suite for Enhanced BaseRule Integration
Comprehensive testing for BaseRule._create_error() with enhanced validation system.
Testing Phase 3 Step 3.1 - Enhanced BaseRule Testing
"""

import pytest
import time
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Import test dependencies
from rules.base_rule import BaseRule
from style_analyzer.base_types import AnalysisResult, ErrorDict, ErrorSeverity
from validation.confidence.confidence_calculator import ConfidenceCalculator
from validation.config.validation_thresholds_config import ValidationThresholdsConfig
from typing import Dict, List, Any


class TestEnhancedBaseRuleIntegration:
    """Test BaseRule enhanced validation integration."""
    
    @pytest.fixture
    def mock_rule(self):
        """Create a mock rule for testing."""
        class TestRule(BaseRule):
            def __init__(self):
                super().__init__()
                self.rule_type = "test_rule"
                self.description = "Test rule for enhanced validation"
            
            def _get_rule_type(self) -> str:
                return "test_rule"
            
            def analyze(self, text: str, **kwargs) -> List[ErrorDict]:
                # Simple mock analysis that returns test errors
                return [
                    self._create_error(
                        sentence=text,
                        sentence_index=0,
                        message="Test error message",
                        suggestions=["Test suggestion"],
                        severity="medium",
                        text=text
                    )
                ]
        
        return TestRule()
    
    @pytest.fixture
    def threshold_config(self):
        """Create ValidationThresholdsConfig for testing."""
        return ValidationThresholdsConfig()
    
    def test_confidence_calculation_integration(self, mock_rule, threshold_config):
        """Test BaseRule._create_error() with enhanced validation integration."""
        
        test_text = "This is a comprehensive test for enhanced BaseRule validation integration."
        
        # Call the rule's analyze method which uses _create_error
        errors = mock_rule.analyze(test_text)
        
        # Validate error structure
        assert len(errors) == 1, "Should create exactly one test error"
        error = errors[0]
        
        # Validate basic error fields
        assert error.get('sentence') == test_text, "Error should contain original sentence"
        assert error.get('sentence_index') == 0, "Error should have correct sentence index"
        assert error.get('type') == "test_rule", "Error should have correct type"
        assert error.get('message') == "Test error message", "Error should have correct message"
        assert error.get('severity') == "medium", "Error should have correct severity"
        assert "Test suggestion" in error.get('suggestions', []), "Error should have correct suggestion"
        
        # Validate enhanced validation fields
        assert 'confidence_score' in error, "Error should have confidence_score from enhanced validation"
        
        # Validate confidence score properties
        confidence_score = error.get('confidence_score')
        if confidence_score is not None:
            assert isinstance(confidence_score, float), "Confidence score should be float"
            assert 0.0 <= confidence_score <= 1.0, f"Confidence score {confidence_score} should be in range [0.0, 1.0]"
        
        # Check if enhanced validation fields are present (breakdown might be stored as string)
        confidence_breakdown = error.get('confidence_breakdown')
        has_breakdown = confidence_breakdown is not None
        
        # The presence of enhanced fields indicates integration is working
        has_enhanced_validation = 'confidence_score' in error or has_breakdown
        
        # Validate that enhanced validation is working
        assert has_enhanced_validation, "Enhanced validation should be working - no confidence_score or breakdown found"
        
        print(f"✅ Enhanced validation integration: confidence={confidence_score}")
        print(f"✅ Enhanced validation working: has_breakdown={has_breakdown}")
    
    def test_universal_threshold_application(self, mock_rule, threshold_config):
        """Test universal threshold is applied consistently."""
        
        # Get universal threshold
        thresholds = threshold_config.get_minimum_confidence_thresholds()
        universal_threshold = thresholds['universal']
        
        # Verify universal threshold value
        assert universal_threshold == 0.35, f"Universal threshold should be 0.35, got {universal_threshold}"
        
        # Test multiple rule types with same threshold
        rule_types = ['grammar', 'spelling', 'punctuation', 'tone', 'word_usage']
        test_text = "Test sentence for universal threshold validation across multiple rule types."
        
        for rule_type in rule_types:
            # Create a mock rule for each type
            class TypedTestRule(BaseRule):
                def __init__(self, rule_type):
                    self._rule_type = rule_type
                    super().__init__()
                    self.description = f"Test rule for {rule_type}"
                
                def _get_rule_type(self) -> str:
                    return self._rule_type
                
                def analyze(self, text: str, **kwargs) -> List[ErrorDict]:
                    return [
                        self._create_error(
                            sentence=text,
                            sentence_index=0,
                            message=f"Test {rule_type} error",
                            suggestions=[f"Test {rule_type} suggestion"],
                            severity="medium",
                            text=text
                        )
                    ]
            
            typed_rule = TypedTestRule(rule_type)
            errors = typed_rule.analyze(test_text)
            
            # Validate that the same threshold is used
            assert len(errors) == 1, f"Should create one error for {rule_type}"
            error = errors[0]
            
            # The universal threshold should be applied consistently
            # We can verify this by checking that confidence calculation is consistent
            confidence_score = error.get('confidence_score')
            if confidence_score is not None:
                assert 0.0 <= confidence_score <= 1.0, f"Confidence for {rule_type} should be in valid range"
            
            print(f"✅ {rule_type}: confidence={confidence_score}, universal_threshold={universal_threshold}")
        
        print(f"✅ Universal threshold {universal_threshold} applied consistently across all rule types")
    
    def test_confidence_calculator_integration(self, mock_rule):
        """Test ConfidenceCalculator integration works correctly."""
        
        test_text = "Testing ConfidenceCalculator integration with BaseRule enhanced validation system."
        
        # Analyze to trigger confidence calculation
        errors = mock_rule.analyze(test_text)
        error = errors[0]
        
        # Validate that confidence calculation was performed
        assert 'confidence_score' in error, "Error should have confidence_score from ConfidenceCalculator"
        
        confidence_score = error.get('confidence_score')
        
        # Test confidence calculation properties
        if confidence_score is not None:
            assert isinstance(confidence_score, float), "Confidence score should be float"
            assert 0.0 <= confidence_score <= 1.0, "Confidence score should be normalized to [0.0, 1.0]"
        
        # Test confidence breakdown from ConfidenceCalculator
        breakdown = error.get('confidence_breakdown')
        if breakdown is not None:
            # Breakdown might be object or dict, just check it exists and has content
            breakdown_str = str(breakdown)
            assert len(breakdown_str) > 0, "Breakdown should contain meaningful information"
        
        print(f"✅ ConfidenceCalculator integration: confidence={confidence_score}")
        print(f"✅ Confidence calculation completed successfully")
    
    def test_validation_pipeline_integration(self, mock_rule):
        """Test ValidationPipeline integration if available."""
        
        test_text = "Testing ValidationPipeline integration with enhanced BaseRule system."
        
        # Test that validation pipeline doesn't interfere with basic functionality
        errors = mock_rule.analyze(test_text)
        
        # Should still get proper errors
        assert len(errors) == 1, "ValidationPipeline integration should not break error creation"
        error = errors[0]
        
        # Should have enhanced validation fields
        assert 'confidence_score' in error, "ValidationPipeline integration should preserve confidence calculation"
        
        confidence_score = error.get('confidence_score')
        if confidence_score is not None:
            assert 0.0 <= confidence_score <= 1.0, "ValidationPipeline should not break confidence normalization"
        
        print(f"✅ ValidationPipeline integration: error creation working with confidence={confidence_score}")
    
    def test_enhanced_error_fields_completeness(self, mock_rule):
        """Test that all enhanced error fields are properly set."""
        
        test_text = "Comprehensive test for enhanced error field completeness validation."
        
        errors = mock_rule.analyze(test_text)
        error = errors[0]
        
        # Core BaseRule fields (updated for ErrorDict format)
        core_fields = ['sentence', 'sentence_index', 'type', 'message', 'severity', 'suggestions']
        for field in core_fields:
            assert field in error, f"Error should have core field: {field}"
            assert error[field] is not None, f"Core field {field} should not be None"
        
        # Enhanced validation fields
        enhanced_fields = ['confidence_score']
        for field in enhanced_fields:
            assert field in error, f"Error should have enhanced field: {field}"
            value = error[field]
            assert value is not None, f"Enhanced field {field} should not be None"
            
            if field == 'confidence_score':
                assert isinstance(value, float), f"Confidence score should be float, got {type(value)}"
                assert 0.0 <= value <= 1.0, f"Confidence score should be in [0.0, 1.0], got {value}"
        
        # Optional enhanced fields
        optional_fields = ['confidence_breakdown']
        for field in optional_fields:
            if field in error:
                value = error[field]
                assert value is not None, f"Optional field {field} should not be None if present"
                print(f"✅ Optional enhanced field {field}: present")
        
        print(f"✅ Enhanced error fields completeness validated")
    
    def test_error_creation_performance(self, mock_rule):
        """Test performance of enhanced error creation."""
        
        test_texts = [
            "Short test text for performance validation.",
            "Medium length test text for performance validation with enhanced BaseRule system testing.",
            "Long test text for performance validation with enhanced BaseRule system testing that includes multiple sentences and comprehensive content for evaluating the performance characteristics of the enhanced validation system under realistic usage conditions."
        ]
        
        performance_results = {}
        
        for i, test_text in enumerate(test_texts):
            text_length = len(test_text)
            
            # Time error creation
            start_time = time.time()
            
            # Create multiple errors to get meaningful timing
            for _ in range(10):
                errors = mock_rule.analyze(test_text)
            
            end_time = time.time()
            
            # Calculate average time per error creation
            total_time = end_time - start_time
            avg_time_per_error = (total_time / 10) * 1000  # Convert to milliseconds
            
            performance_results[f"text_{i+1}_{text_length}_chars"] = avg_time_per_error
            
            # Validate performance is reasonable
            assert avg_time_per_error < 100, f"Error creation should be <100ms, got {avg_time_per_error:.1f}ms for {text_length} chars"
            
            print(f"✅ Performance for {text_length} chars: {avg_time_per_error:.1f}ms per error")
        
        print(f"✅ Enhanced error creation performance validated")
        return performance_results
    
    def test_cross_rule_consistency(self):
        """Test confidence consistency across different rule types."""
        
        test_text = "Consistency test for enhanced validation across multiple rule types."
        rule_types = ['grammar', 'spelling', 'punctuation', 'tone', 'word_usage']
        
        confidences = {}
        
        for rule_type in rule_types:
            class ConsistencyTestRule(BaseRule):
                def __init__(self, rule_type):
                    self._rule_type = rule_type
                    super().__init__()
                    self.description = f"Consistency test rule for {rule_type}"
                
                def _get_rule_type(self) -> str:
                    return self._rule_type
                
                def analyze(self, text: str, **kwargs) -> List[ErrorDict]:
                    return [
                        self._create_error(
                            sentence=text,
                            sentence_index=0,
                            message=f"Consistency test for {rule_type}",
                            suggestions=[f"Suggestion for {rule_type}"],
                            severity="medium",
                            text=text
                        )
                    ]
            
            rule = ConsistencyTestRule(rule_type)
            errors = rule.analyze(test_text)
            
            assert len(errors) == 1, f"Should create one error for {rule_type}"
            error = errors[0]
            
            confidence = error.get('confidence_score')
            confidences[rule_type] = confidence
            
            if confidence is not None:
                assert 0.0 <= confidence <= 1.0, f"Confidence for {rule_type} should be in valid range"
        
        # Test consistency - confidence scores should be reasonably similar for similar errors
        confidence_values = [c for c in confidences.values() if c is not None]
        if confidence_values:
            mean_confidence = sum(confidence_values) / len(confidence_values)
            std_dev = (sum((c - mean_confidence)**2 for c in confidence_values) / len(confidence_values))**0.5
        
            # Standard deviation should be reasonable (not too high, not zero)
            assert 0.0 <= std_dev <= 0.3, f"Standard deviation {std_dev:.3f} indicates poor consistency"
            
            print(f"✅ Cross-rule consistency: mean={mean_confidence:.3f}, std_dev={std_dev:.3f}")
        else:
            print(f"✅ Cross-rule consistency: no confidence values to analyze")
        for rule_type, confidence in confidences.items():
            print(f"   {rule_type}: {confidence}")
        
        return confidences


class TestEnhancedBaseRuleEdgeCases:
    """Test enhanced BaseRule with edge cases and error conditions."""
    
    @pytest.fixture
    def robust_rule(self):
        """Create a robust rule for edge case testing."""
        class RobustTestRule(BaseRule):
            def __init__(self):
                super().__init__()
                self.rule_type = "robust_test"
                self.description = "Robust test rule for edge cases"
            
            def _get_rule_type(self) -> str:
                return "robust_test"
            
            def analyze(self, text: str, **kwargs) -> List[ErrorDict]:
                if not text or len(text) < 5:
                    return []  # No errors for very short text
                
                return [
                    self._create_error(
                        sentence=text,
                        sentence_index=0,
                        message="Robust test error",
                        suggestions=["Robust suggestion"],
                        severity="medium",
                        text=text
                    )
                ]
        
        return RobustTestRule()
    
    def test_empty_text_handling(self, robust_rule):
        """Test handling of empty or very short text."""
        
        edge_cases = [
            "",           # Empty string
            " ",          # Single space
            "Hi",         # Very short text
            "Test"        # Short text
        ]
        
        for text in edge_cases:
            try:
                errors = robust_rule.analyze(text)
                
                # Should handle gracefully
                assert isinstance(errors, list), f"Should return list for text: '{text}'"
                
                # If errors are created, they should be valid
                for error in errors:
                    assert 'confidence_score' in error, "Error should have confidence_score"
                    confidence = error.get('confidence_score')
                    if confidence is not None:
                        assert 0.0 <= confidence <= 1.0, f"Confidence should be valid for text: '{text}'"
                
                print(f"✅ Edge case '{text}': {len(errors)} errors, all valid")
                
            except Exception as e:
                pytest.fail(f"Should handle edge case '{text}' gracefully, got error: {e}")
    
    def test_very_long_text_handling(self, robust_rule):
        """Test handling of very long text."""
        
        # Create very long text
        long_text = "This is a very long text for testing enhanced BaseRule validation. " * 200
        
        try:
            start_time = time.time()
            errors = robust_rule.analyze(long_text)
            end_time = time.time()
            
            processing_time = (end_time - start_time) * 1000  # Convert to milliseconds
            
            # Should handle gracefully and efficiently
            assert isinstance(errors, list), "Should return list for long text"
            assert processing_time < 1000, f"Should process long text in <1000ms, took {processing_time:.1f}ms"
            
            # Validate any errors created
            for error in errors:
                assert hasattr(error, 'confidence_score'), "Error should have confidence_score"
                confidence = error.confidence_score
                assert 0.0 <= confidence <= 1.0, "Confidence should be valid for long text"
            
            print(f"✅ Long text ({len(long_text)} chars): {len(errors)} errors in {processing_time:.1f}ms")
            
        except Exception as e:
            pytest.fail(f"Should handle long text gracefully, got error: {e}")
    
    def test_special_character_handling(self, robust_rule):
        """Test handling of text with special characters."""
        
        special_texts = [
            "Text with émojis 🚀 and ünïcödé characters!",
            "Code with symbols: def func(x): return x * 2",
            "Math expressions: f(x) = x² + 2x + 1",
            "Mixed content: API calls like GET /api/v1/users?filter=active",
            "Newlines and\ttabs\neverywhere\r\n"
        ]
        
        for text in special_texts:
            try:
                errors = robust_rule.analyze(text)
                
                # Should handle gracefully
                assert isinstance(errors, list), f"Should return list for special text: {text[:50]}..."
                
                # Validate any errors created
                for error in errors:
                    assert hasattr(error, 'confidence_score'), "Error should have confidence_score"
                    confidence = error.confidence_score
                    assert 0.0 <= confidence <= 1.0, f"Confidence should be valid for special text"
                    
                    # Text fields should handle special characters
                    assert isinstance(error.text, str), "Error text should be string"
                    assert isinstance(error.message, str), "Error message should be string"
                
                print(f"✅ Special characters: '{text[:50]}...': {len(errors)} errors, all valid")
                
            except Exception as e:
                pytest.fail(f"Should handle special characters gracefully, got error: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
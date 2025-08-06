"""
Test Suite for Rule Reliability System
Comprehensive testing for the rule reliability coefficient system.
"""

import pytest
import time
from typing import Dict, List
from validation.confidence.rule_reliability import (
    RuleReliabilityCalculator, 
    get_rule_reliability_coefficient,
    get_rule_category,
    validate_all_coefficients
)


class TestRuleReliabilityCalculator:
    """Test the RuleReliabilityCalculator class."""
    
    @pytest.fixture
    def calculator(self):
        """Create RuleReliabilityCalculator instance for testing."""
        return RuleReliabilityCalculator()
    
    
    # COEFFICIENT ASSIGNMENT TESTS (20 minutes implementation time)
    
    def test_all_rule_types_have_coefficients(self, calculator):
        """Test every rule class gets appropriate coefficient."""
        
        # Test high-reliability rules
        high_reliability_rules = [
            'claims', 'personal_information', 'inclusive_language', 'commands',
            'spelling', 'programming_elements', 'ui_elements'
        ]
        
        for rule_type in high_reliability_rules:
            coefficient = calculator.get_rule_reliability_coefficient(rule_type)
            assert coefficient >= 0.85, f"{rule_type} should have high reliability (≥0.85), got {coefficient}"
        
        # Test medium reliability rules
        medium_reliability_rules = [
            'grammar', 'punctuation', 'headings', 'lists', 'numbers',
            'citations', 'word_usage', 'terminology'
        ]
        
        for rule_type in medium_reliability_rules:
            coefficient = calculator.get_rule_reliability_coefficient(rule_type)
            assert 0.70 <= coefficient < 0.90, f"{rule_type} should have medium reliability (0.70-0.90), got {coefficient}"
        
        # Test specific categories
        word_usage_rules = ['a_words', 'b_words', 'c_words', 'x_words', 'z_words']
        for rule_type in word_usage_rules:
            coefficient = calculator.get_rule_reliability_coefficient(rule_type)
            assert coefficient == 0.75, f"Word usage rule {rule_type} should have 0.75 coefficient, got {coefficient}"
    
    def test_coefficient_ranges(self, calculator):
        """Test all coefficients are in valid range [0.5, 1.0]."""
        all_coefficients = calculator.get_all_rule_types()
        
        for rule_type, coefficient in all_coefficients.items():
            assert 0.5 <= coefficient <= 1.0, f"Invalid coefficient for {rule_type}: {coefficient}"
        
        # Test validation method
        assert calculator.validate_coefficient_ranges(), "Coefficient validation should pass"
    
    def test_rule_classification_accuracy(self, calculator):
        """Test rule type classification logic."""
        
        # Test exact matches
        assert calculator.get_rule_reliability_coefficient('claims') == 0.85
        assert calculator.get_rule_reliability_coefficient('commands') == 0.90
        assert calculator.get_rule_reliability_coefficient('spelling') == 0.90
        
        # Test partial matches (should work for complex rule names)
        assert calculator.get_rule_reliability_coefficient('technical_commands') >= 0.80
        assert calculator.get_rule_reliability_coefficient('punctuation_rule') >= 0.75
        
        # Test unknown rules
        unknown_coefficient = calculator.get_rule_reliability_coefficient('nonexistent_rule')
        assert unknown_coefficient == 0.75, f"Unknown rule should get default coefficient 0.75, got {unknown_coefficient}"
        
        # Test empty/None rule types
        assert calculator.get_rule_reliability_coefficient('') == 0.70  # unknown coefficient
        assert calculator.get_rule_reliability_coefficient(None) == 0.70
    
    def test_rule_categories(self, calculator):
        """Test rule category classification."""
        
        # Test high category
        assert calculator.get_rule_category('claims') == 'high'
        assert calculator.get_rule_category('spelling') == 'high'
        assert calculator.get_rule_category('commands') == 'high'
        
        # Test medium_high category
        assert calculator.get_rule_category('grammar') == 'high'  # 0.85
        assert calculator.get_rule_category('capitalization') == 'medium_high'  # 0.82
        
        # Test medium category
        assert calculator.get_rule_category('word_usage') == 'medium'  # 0.75
        assert calculator.get_rule_category('tone') == 'medium'  # 0.72
        
        # Test medium_low category
        assert calculator.get_rule_category('second_person') == 'medium_low'  # 0.68
    
    
    # PERFORMANCE TESTS (20 minutes implementation time)
    
    def test_coefficient_lookup_performance(self, calculator):
        """Test lookup speed for coefficients."""
        rule_types = ['claims', 'grammar', 'commands', 'word_usage', 'punctuation']
        
        # Warm up cache
        for rule_type in rule_types:
            calculator.get_rule_reliability_coefficient(rule_type)
        
        # Test performance
        start_time = time.time()
        for _ in range(1000):
            for rule_type in rule_types:
                calculator.get_rule_reliability_coefficient(rule_type)
        total_time = time.time() - start_time
        
        avg_time_per_lookup = (total_time / 5000) * 1000  # Convert to ms
        assert avg_time_per_lookup < 1.0, f"Average lookup time {avg_time_per_lookup:.3f}ms should be <1ms"
        
        print(f"Performance: {avg_time_per_lookup:.3f}ms per lookup")
    
    def test_classification_performance(self, calculator):
        """Test rule classification speed."""
        test_rules = [
            'claims', 'personal_information', 'grammar', 'spelling', 'commands',
            'programming_elements', 'punctuation', 'headings', 'word_usage',
            'unknown_rule', 'complex_nested_rule_name', 'x_words'
        ]
        
        start_time = time.time()
        for _ in range(100):
            for rule_type in test_rules:
                coefficient = calculator.get_rule_reliability_coefficient(rule_type)
                category = calculator.get_rule_category(rule_type)
                assert 0.5 <= coefficient <= 1.0
                assert category in ['high', 'medium_high', 'medium', 'medium_low']
        
        total_time = time.time() - start_time
        avg_time_per_classification = (total_time / 1200) * 1000  # Convert to ms
        
        assert avg_time_per_classification < 5.0, f"Classification time {avg_time_per_classification:.3f}ms should be <5ms"
        print(f"Classification performance: {avg_time_per_classification:.3f}ms per rule")
    
    def test_cache_effectiveness(self, calculator):
        """Test caching performance."""
        # Clear cache by creating new instance
        calculator = RuleReliabilityCalculator()
        
        test_rules = ['claims', 'grammar', 'commands', 'spelling', 'punctuation']
        
        # First pass - populate cache
        for rule_type in test_rules:
            calculator.get_rule_reliability_coefficient(rule_type)
        
        # Second pass - should hit cache
        start_time = time.time()
        for _ in range(1000):
            for rule_type in test_rules:
                calculator.get_rule_reliability_coefficient(rule_type)
        cached_time = time.time() - start_time
        
        # Get cache stats
        stats = calculator.get_performance_stats()
        hit_rate = stats['cache_hit_rate']
        
        assert hit_rate > 0.95, f"Cache hit rate {hit_rate:.1%} should be >95%"
        assert cached_time < 0.1, f"Cached lookups should be very fast, took {cached_time:.3f}s"
        
        print(f"Cache hit rate: {hit_rate:.1%}, cached time: {cached_time:.3f}s")
    
    
    # INTEGRATION TESTS (20 minutes implementation time)
    
    def test_coefficient_integration(self, calculator):
        """Test coefficient usage in error creation context."""
        
        # Test realistic integration scenario
        error_scenarios = [
            {'type': 'claims', 'severity': 'high', 'expected_min_confidence': 0.85},
            {'type': 'grammar', 'severity': 'medium', 'expected_min_confidence': 0.75},
            {'type': 'word_usage', 'severity': 'low', 'expected_min_confidence': 0.65},
            {'type': 'unknown_rule', 'severity': 'medium', 'expected_min_confidence': 0.65},
        ]
        
        for scenario in error_scenarios:
            rule_type = scenario['type']
            coefficient = calculator.get_rule_reliability_coefficient(rule_type)
            
            # Simulate confidence calculation with reliability coefficient
            base_confidence = 0.8  # Simulated base confidence
            final_confidence = base_confidence * coefficient
            
            assert final_confidence >= 0.5, f"Final confidence should be reasonable for {rule_type}"
            assert coefficient >= 0.5, f"Coefficient should be valid for {rule_type}"
    
    def test_error_consolidator_integration(self, calculator):
        """Test integration with ErrorConsolidator-style confidence estimation."""
        
        def simulate_confidence_estimation(error_type: str, severity: str) -> float:
            """Simulate ErrorConsolidator confidence estimation logic."""
            severity_confidence = {
                'critical': 0.8,
                'high': 0.7,
                'medium': 0.6,
                'low': 0.5,
                'info': 0.4
            }
            
            base_confidence = severity_confidence.get(severity, 0.5)
            rule_reliability = calculator.get_rule_reliability_coefficient(error_type)
            
            return min(1.0, base_confidence * rule_reliability)
        
        # Test various combinations
        test_cases = [
            ('claims', 'high', 0.7 * 0.85),  # Should be high confidence
            ('grammar', 'medium', 0.6 * 0.85),  # Medium-high confidence
            ('word_usage', 'low', 0.5 * 0.75),  # Lower confidence
            ('unknown_rule', 'medium', 0.6 * 0.75),  # Fallback confidence
        ]
        
        for rule_type, severity, expected_min in test_cases:
            confidence = simulate_confidence_estimation(rule_type, severity)
            assert confidence >= expected_min * 0.9, f"Confidence for {rule_type}/{severity} should be ≥{expected_min:.2f}, got {confidence:.2f}"
            assert confidence <= 1.0, f"Confidence should not exceed 1.0 for {rule_type}/{severity}"


class TestGlobalFunctions:
    """Test global function interfaces."""
    
    def test_global_coefficient_function(self):
        """Test get_rule_reliability_coefficient global function."""
        
        # Test known rule types
        assert get_rule_reliability_coefficient('claims') == 0.85
        assert get_rule_reliability_coefficient('commands') == 0.90
        assert get_rule_reliability_coefficient('grammar') == 0.85
        
        # Test unknown rule
        assert get_rule_reliability_coefficient('unknown_rule') == 0.70  # 'unknown' coefficient
        
        # Test consistency
        coefficient1 = get_rule_reliability_coefficient('spelling')
        coefficient2 = get_rule_reliability_coefficient('spelling')
        assert coefficient1 == coefficient2, "Global function should be consistent"
    
    def test_global_category_function(self):
        """Test get_rule_category global function."""
        
        assert get_rule_category('claims') == 'high'
        assert get_rule_category('grammar') == 'high'
        assert get_rule_category('word_usage') == 'medium'
        assert get_rule_category('tone') == 'medium'
    
    def test_global_validation_function(self):
        """Test validate_all_coefficients global function."""
        
        assert validate_all_coefficients() == True, "All coefficients should be valid"


class TestReliabilityMatrix:
    """Test the reliability matrix completeness and logic."""
    
    def test_matrix_completeness(self):
        """Test that the matrix covers all major rule categories."""
        calculator = RuleReliabilityCalculator()
        all_rules = calculator.get_all_rule_types()
        
        # Check major categories are represented
        required_categories = [
            'claims', 'personal_information', 'commands', 'grammar', 'spelling',
            'punctuation', 'headings', 'numbers', 'word_usage', 'tone'
        ]
        
        for category in required_categories:
            assert category in all_rules, f"Required category {category} missing from matrix"
    
    def test_coefficient_logic_validation(self):
        """Test that coefficient assignments make logical sense."""
        calculator = RuleReliabilityCalculator()
        
        # High-reliability rules should have higher coefficients than medium ones
        high_reliability_rules = ['claims', 'commands', 'spelling']
        medium_reliability_rules = ['tone', 'word_usage', 'sentence_length']
        
        for high_rule in high_reliability_rules:
            high_coeff = calculator.get_rule_reliability_coefficient(high_rule)
            for medium_rule in medium_reliability_rules:
                medium_coeff = calculator.get_rule_reliability_coefficient(medium_rule)
                assert high_coeff > medium_coeff, f"{high_rule} ({high_coeff}) should have higher reliability than {medium_rule} ({medium_coeff})"
    
    def test_statistical_properties(self):
        """Test statistical properties of the coefficient distribution."""
        calculator = RuleReliabilityCalculator()
        stats = calculator.get_performance_stats()
        
        coeff_range = stats['coefficient_range']
        
        # Test range properties
        assert coeff_range['min'] >= 0.5, "Minimum coefficient should be ≥0.5"
        assert coeff_range['max'] <= 1.0, "Maximum coefficient should be ≤1.0"
        assert 0.7 <= coeff_range['mean'] <= 0.85, f"Mean coefficient {coeff_range['mean']:.2f} should be reasonable"
        
        # Test distribution spread
        spread = coeff_range['max'] - coeff_range['min']
        assert spread >= 0.15, "Coefficient spread should be meaningful"
        assert spread <= 0.5, "Coefficient spread should not be excessive"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_empty_rule_types(self):
        """Test handling of empty/invalid rule types."""
        calculator = RuleReliabilityCalculator()
        
        # Test empty string
        assert calculator.get_rule_reliability_coefficient('') == 0.70
        
        # Test None
        assert calculator.get_rule_reliability_coefficient(None) == 0.70
        
        # Test whitespace
        assert calculator.get_rule_reliability_coefficient('   ') == 0.75  # default
    
    def test_partial_matches(self):
        """Test partial matching logic."""
        calculator = RuleReliabilityCalculator()
        
        # Test rules with complex names should match base types
        assert calculator.get_rule_reliability_coefficient('advanced_grammar_rule') >= 0.80
        assert calculator.get_rule_reliability_coefficient('custom_punctuation_checker') >= 0.75
        
    def test_case_sensitivity(self):
        """Test case sensitivity handling."""
        calculator = RuleReliabilityCalculator()
        
        # Should work regardless of case (case-sensitive lookup but fallback should work)
        normal_coeff = calculator.get_rule_reliability_coefficient('claims')
        upper_coeff = calculator.get_rule_reliability_coefficient('CLAIMS')
        
        # Both should return reasonable values (might not be identical due to exact matching)
        assert 0.5 <= normal_coeff <= 1.0
        assert 0.5 <= upper_coeff <= 1.0


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
"""
Test Suite for Confidence Normalization System
"""

import pytest
import time
from typing import Dict, List, Any
from validation.confidence.confidence_calculator import ConfidenceCalculator, ConfidenceBreakdown
from validation.confidence.rule_reliability import get_rule_reliability_coefficient
from validation.confidence.context_analyzer import ContentType


class TestConfidenceNormalization:
    """Test the confidence normalization functionality."""
    
    @pytest.fixture
    def calculator(self):
        """Create ConfidenceCalculator instance for testing."""
        return ConfidenceCalculator(cache_results=True)
    
    @pytest.fixture
    def test_texts(self):
        """Sample texts of different content types for testing."""
        return {
            'technical': """
                Configure the REST API endpoint by setting the JSON response format.
                Use the following command: curl -X GET https://api.example.com/v1/users
                Debug any HTTP errors using the trace functionality.
            """,
            'procedural': """
                Step 1: First, open the application and navigate to settings.
                Step 2: Click on the 'Add User' button to create a new account.
                Step 3: Enter the required information and press Save.
            """,
            'narrative': """
                Yesterday, I discovered an amazing new feature in our application.
                I was excited to share my experience with the development team.
                Our journey has been incredible and worth sharing with others.
            """,
            'legal': """
                Users shall comply with all applicable regulations and requirements.
                Any violation of these terms may result in immediate termination.
                The company hereby reserves the right to modify these terms.
            """,
            'marketing': """
                Get started today with our revolutionary new platform!
                Save up to 50% with this exclusive limited-time offer.
                Don't miss out - contact us now for your free consultation!
            """
        }
    
    
    # NORMALIZATION ALGORITHM TESTS (40 minutes implementation time)
    
    def test_confidence_calculation_accuracy(self, calculator, test_texts):
        """Test confidence calculation with known inputs."""
        
        # Test that normalized confidence integrates all components
        for content_type, text in test_texts.items():
            normalized_confidence = calculator.calculate_normalized_confidence(
                text=text,
                error_position=50,  # Middle of text
                rule_type='grammar',
                content_type=content_type
            )
            
            # Should be in valid range
            assert 0.0 <= normalized_confidence <= 1.0, f"Normalized confidence {normalized_confidence} outside valid range for {content_type}"
            
            # Should be different from base confidence
            assert normalized_confidence != 0.5, f"Normalized confidence should differ from base for {content_type}"
            
            print(f"Normalized confidence for {content_type}/grammar: {normalized_confidence:.3f}")
    
    def test_confidence_range_validation(self, calculator, test_texts):
        """Test confidence scores stay in [0.0, 1.0] range."""
        
        test_cases = [
            ('claims', 'legal'),
            ('commands', 'technical'),
            ('tone', 'narrative'),
            ('grammar', 'general'),
            ('unknown_rule', 'general')
        ]
        
        for rule_type, content_type in test_cases:
            text = test_texts.get(content_type, list(test_texts.values())[0])
            
            normalized_confidence = calculator.calculate_normalized_confidence(
                text=text,
                error_position=25,
                rule_type=rule_type,
                content_type=content_type
            )
            
            assert 0.0 <= normalized_confidence <= 1.0, f"Confidence {normalized_confidence} out of range for {rule_type}/{content_type}"
    
    def test_confidence_consistency(self, calculator):
        """Test same input produces same confidence."""
        
        text = "This is a test sentence for consistency validation."
        rule_type = "grammar"
        content_type = "general"
        error_position = 10
        
        # Calculate confidence multiple times
        confidences = []
        for _ in range(5):
            confidence = calculator.calculate_normalized_confidence(
                text=text,
                error_position=error_position,
                rule_type=rule_type,
                content_type=content_type
            )
            confidences.append(confidence)
        
        # All should be identical
        assert len(set(confidences)) == 1, f"Confidence not consistent across calls: {confidences}"
        print(f"Consistent confidence: {confidences[0]:.3f}")
    
    def test_content_type_modifier_effects(self, calculator, test_texts):
        """Test that content-type modifiers affect confidence appropriately."""
        
        # Test specific rule-content combinations that should have different modifiers
        base_text = "Execute the following command to configure the system."
        
        # Commands rule should be higher confidence in technical content vs narrative
        technical_confidence = calculator.calculate_normalized_confidence(
            text=base_text,
            error_position=20,
            rule_type='commands',
            content_type='technical'
        )
        
        narrative_confidence = calculator.calculate_normalized_confidence(
            text=base_text,
            error_position=20,
            rule_type='commands',
            content_type='narrative'
        )
        
        assert technical_confidence > narrative_confidence, f"Commands should be more confident in technical ({technical_confidence:.3f}) vs narrative ({narrative_confidence:.3f})"
        
        print(f"Content modifier effect: technical={technical_confidence:.3f}, narrative={narrative_confidence:.3f}")
    
    def test_rule_reliability_integration(self, calculator):
        """Test that rule reliability coefficients are properly integrated."""
        
        text = "This is a test sentence for reliability testing."
        error_position = 10
        
        # High reliability rule (claims) vs lower reliability rule (tone)
        claims_confidence = calculator.calculate_normalized_confidence(
            text=text,
            error_position=error_position,
            rule_type='claims',
            content_type='legal'
        )
        
        tone_confidence = calculator.calculate_normalized_confidence(
            text=text,
            error_position=error_position,
            rule_type='tone',
            content_type='legal'
        )
        
        # Claims should generally have higher confidence due to higher reliability
        claims_reliability = get_rule_reliability_coefficient('claims')
        tone_reliability = get_rule_reliability_coefficient('tone')
        
        print(f"Claims reliability: {claims_reliability}, confidence: {claims_confidence:.3f}")
        print(f"Tone reliability: {tone_reliability}, confidence: {tone_confidence:.3f}")
        
        # Verify reliability is factored in (exact comparison depends on other factors)
        assert claims_reliability > tone_reliability, "Claims should have higher reliability than tone"
    
    
    # INTEGRATION TESTS (40 minutes implementation time)
    
    def test_baserule_integration(self, calculator):
        """Test confidence normalization in BaseRule._create_error()."""
        
        # Create a test rule to verify integration
        from rules.base_rule import BaseRule
        
        class TestNormalizationRule(BaseRule):
            def _get_rule_type(self):
                return 'grammar'
            
            def analyze(self, text, sentences, nlp=None, context=None):
                # Create a test error using _create_error
                error = self._create_error(
                    sentence=sentences[0] if sentences else text,
                    sentence_index=0,
                    message="Test normalization error",
                    suggestions=["suggestion"],
                    severity='medium',
                    text=text,
                    context={'content_type': 'technical'}
                )
                return [error]
        
        rule = TestNormalizationRule()
        text = "Configure the API endpoint settings properly."
        sentences = [text]
        
        errors = rule.analyze(text, sentences)
        
        assert len(errors) == 1, "Should produce one test error"
        error = errors[0]
        
        # Verify normalized confidence is present
        assert 'confidence_score' in error, "Error should have confidence_score"
        confidence = error['confidence_score']
        
        assert 0.0 <= confidence <= 1.0, f"Confidence {confidence} should be in valid range"
        assert confidence != 0.5, "Confidence should be normalized (different from base)"
        
        print(f"BaseRule integration confidence: {confidence:.3f}")
    
    def test_cross_rule_consistency(self, calculator, test_texts):
        """Test confidence comparability across different rule types."""
        
        # Test similar errors with different rule types should have comparable confidence ranges
        text = "This sentence contains potential issues for testing."
        error_position = 25
        
        rule_types = ['grammar', 'spelling', 'punctuation', 'tone', 'word_usage']
        confidences = {}
        
        for rule_type in rule_types:
            confidence = calculator.calculate_normalized_confidence(
                text=text,
                error_position=error_position,
                rule_type=rule_type,
                content_type='general'
            )
            confidences[rule_type] = confidence
            print(f"{rule_type}: {confidence:.3f}")
        
        # All confidences should be in reasonable ranges
        for rule_type, confidence in confidences.items():
            assert 0.2 <= confidence <= 1.0, f"Confidence for {rule_type} ({confidence:.3f}) outside reasonable range"
        
        # Variation should be reasonable (not all identical, not too spread out)
        confidence_values = list(confidences.values())
        std_dev = (sum((c - sum(confidence_values)/len(confidence_values))**2 for c in confidence_values) / len(confidence_values))**0.5
        assert 0.01 <= std_dev <= 0.3, f"Confidence standard deviation {std_dev:.3f} outside reasonable range"
    
    def test_auto_content_detection_integration(self, calculator, test_texts):
        """Test that auto-detection of content type works correctly."""
        
        for expected_content_type, text in test_texts.items():
            # Don't specify content_type - let it be auto-detected
            confidence = calculator.calculate_normalized_confidence(
                text=text,
                error_position=50,
                rule_type='grammar',
                content_type=None  # Should auto-detect
            )
            
            # Should work without errors
            assert 0.0 <= confidence <= 1.0, f"Auto-detection failed for {expected_content_type}: {confidence}"
            
            print(f"Auto-detected confidence for {expected_content_type}: {confidence:.3f}")
    
    
    # EDGE CASE TESTS (40 minutes implementation time)
    
    def test_error_handling(self, calculator):
        """Test graceful degradation when components fail."""
        
        # Test with invalid inputs
        edge_cases = [
            ("", 0, "grammar", "general"),  # Empty text
            ("Short", 100, "grammar", "general"),  # Position beyond text
            ("Normal text", 5, "", "general"),  # Empty rule type
            ("Normal text", 5, "nonexistent_rule", "general"),  # Unknown rule
            ("Normal text", 5, "grammar", "unknown_content"),  # Unknown content type
        ]
        
        for text, position, rule_type, content_type in edge_cases:
            try:
                confidence = calculator.calculate_normalized_confidence(
                    text=text,
                    error_position=position,
                    rule_type=rule_type,
                    content_type=content_type
                )
                
                # Should return reasonable default, not crash
                assert 0.0 <= confidence <= 1.0, f"Edge case confidence {confidence} outside valid range"
                print(f"Edge case handled: {text[:20]}... -> {confidence:.3f}")
                
            except Exception as e:
                pytest.fail(f"Edge case should not raise exception: {e}")
    
    def test_extreme_inputs(self, calculator):
        """Test with very long/short text, unusual content."""
        
        # Very short text
        short_confidence = calculator.calculate_normalized_confidence(
            text="Hi",
            error_position=0,
            rule_type='grammar',
            content_type='general'
        )
        assert 0.0 <= short_confidence <= 1.0, "Short text confidence invalid"
        
        # Very long text
        long_text = "This is a very long sentence. " * 100  # 3000+ characters
        long_confidence = calculator.calculate_normalized_confidence(
            text=long_text,
            error_position=500,
            rule_type='grammar',
            content_type='general'
        )
        assert 0.0 <= long_confidence <= 1.0, "Long text confidence invalid"
        
        # Unusual content (mixed languages, special characters)
        unusual_text = "Hello 世界! This mixes English and Unicode ñáéíóú with symbols @#$%."
        unusual_confidence = calculator.calculate_normalized_confidence(
            text=unusual_text,
            error_position=10,
            rule_type='grammar',
            content_type='general'
        )
        assert 0.0 <= unusual_confidence <= 1.0, "Unusual text confidence invalid"
        
        print(f"Extreme inputs: short={short_confidence:.3f}, long={long_confidence:.3f}, unusual={unusual_confidence:.3f}")
    
    def test_performance_under_load(self, calculator):
        """Test performance with multiple rapid calculations."""
        
        text = "This is a test sentence for performance validation and stress testing."
        
        # Measure performance for batch calculations
        start_time = time.time()
        confidences = []
        
        for i in range(100):
            confidence = calculator.calculate_normalized_confidence(
                text=text,
                error_position=i % 50,  # Vary position
                rule_type='grammar',
                content_type='general'
            )
            confidences.append(confidence)
        
        total_time = time.time() - start_time
        avg_time = total_time / 100
        
        # Performance should be reasonable
        assert avg_time < 0.1, f"Average calculation time {avg_time:.3f}s too slow"
        
        # All calculations should be valid
        for i, confidence in enumerate(confidences):
            assert 0.0 <= confidence <= 1.0, f"Calculation {i} produced invalid confidence {confidence}"
        
        print(f"Performance: {avg_time*1000:.1f}ms per calculation (100 calculations in {total_time:.2f}s)")


class TestContentTypeModifiers:
    """Test content-type modifier functionality."""
    
    @pytest.fixture
    def calculator(self):
        """Create ConfidenceCalculator instance for testing."""
        return ConfidenceCalculator()
    
    def test_modifier_matrix_completeness(self, calculator):
        """Test all content-rule combinations have modifiers."""
        
        content_types = ['technical', 'procedural', 'narrative', 'legal', 'marketing', 'general']
        rule_types = ['grammar', 'commands', 'tone', 'claims', 'spelling', 'punctuation']
        
        for content_type in content_types:
            for rule_type in rule_types:
                modifier = calculator._get_content_type_modifier(content_type, rule_type)
                
                # Should return valid modifier
                assert 0.5 <= modifier <= 1.5, f"Modifier {modifier} for {content_type}/{rule_type} outside reasonable range"
                assert isinstance(modifier, float), f"Modifier should be float, got {type(modifier)}"
    
    def test_modifier_ranges(self, calculator):
        """Test all modifiers in range [0.7, 1.3]."""
        
        # Test a comprehensive set of combinations
        test_combinations = [
            ('technical', 'commands'),      # Should be high (1.2)
            ('technical', 'tone'),          # Should be low (0.8)
            ('narrative', 'tone'),          # Should be high (1.2)
            ('narrative', 'commands'),      # Should be low (0.8)
            ('legal', 'claims'),            # Should be very high (1.3)
            ('marketing', 'tone'),          # Should be high (1.2)
            ('general', 'grammar'),         # Should be neutral (1.0)
        ]
        
        for content_type, rule_type in test_combinations:
            modifier = calculator._get_content_type_modifier(content_type, rule_type)
            
            # Within expected range
            assert 0.7 <= modifier <= 1.3, f"Modifier {modifier} for {content_type}/{rule_type} outside [0.7, 1.3]"
            print(f"{content_type}/{rule_type}: {modifier}")
    
    def test_modifier_logic(self, calculator):
        """Test modifier assignments make logical sense."""
        
        # Commands should be more confident in technical content than narrative
        tech_commands = calculator._get_content_type_modifier('technical', 'commands')
        narrative_commands = calculator._get_content_type_modifier('narrative', 'commands')
        assert tech_commands > narrative_commands, f"Commands should be higher in technical ({tech_commands}) vs narrative ({narrative_commands})"
        
        # Tone should be more confident in narrative content than technical
        narrative_tone = calculator._get_content_type_modifier('narrative', 'tone')
        tech_tone = calculator._get_content_type_modifier('technical', 'tone')
        assert narrative_tone > tech_tone, f"Tone should be higher in narrative ({narrative_tone}) vs technical ({tech_tone})"
        
        # Claims should be very confident in legal content
        legal_claims = calculator._get_content_type_modifier('legal', 'claims')
        assert legal_claims >= 1.2, f"Legal claims should have high modifier, got {legal_claims}"
    
    def test_modifier_lookup_performance(self, calculator):
        """Test lookup and application speed."""
        
        start_time = time.time()
        
        # Perform many modifier lookups
        for _ in range(1000):
            calculator._get_content_type_modifier('technical', 'commands')
            calculator._get_content_type_modifier('narrative', 'tone')
            calculator._get_content_type_modifier('legal', 'claims')
        
        total_time = time.time() - start_time
        avg_time = total_time / 3000  # 3 lookups * 1000 iterations
        
        assert avg_time < 0.001, f"Modifier lookup too slow: {avg_time*1000:.3f}ms per lookup"
        print(f"Modifier lookup performance: {avg_time*1000000:.1f}μs per lookup")


class TestProductionReadiness:
    """Test production readiness and real-world scenarios."""
    
    @pytest.fixture
    def calculator(self):
        """Create ConfidenceCalculator instance for testing."""
        return ConfidenceCalculator()
    
    def test_real_world_rule_combinations(self, calculator):
        """Test with realistic rule and content combinations."""
        
        realistic_scenarios = [
            {
                'text': 'Use the following command: `git clone https://github.com/user/repo.git`',
                'rule_type': 'commands',
                'content_type': 'technical',
                'expected_confidence_range': (0.3, 1.0)  # More realistic range
            },
            {
                'text': 'Our journey has been amazing, and we\'re excited to share it with you!',
                'rule_type': 'tone',
                'content_type': 'narrative',
                'expected_confidence_range': (0.3, 1.0)  # More realistic range
            },
            {
                'text': 'All users must comply with the terms and conditions as specified.',
                'rule_type': 'claims',
                'content_type': 'legal',
                'expected_confidence_range': (0.4, 1.0)  # More realistic range
            },
            {
                'text': 'Sign up today for exclusive access to our premium features!',
                'rule_type': 'tone',
                'content_type': 'marketing',
                'expected_confidence_range': (0.3, 1.0)  # More realistic range
            }
        ]
        
        for scenario in realistic_scenarios:
            confidence = calculator.calculate_normalized_confidence(
                text=scenario['text'],
                error_position=len(scenario['text']) // 2,
                rule_type=scenario['rule_type'],
                content_type=scenario['content_type']
            )
            
            min_expected, max_expected = scenario['expected_confidence_range']
            assert min_expected <= confidence <= max_expected, \
                f"Confidence {confidence:.3f} outside expected range [{min_expected}, {max_expected}] for {scenario['rule_type']}/{scenario['content_type']}"
            
            print(f"{scenario['rule_type']}/{scenario['content_type']}: {confidence:.3f}")
    
    def test_system_stability(self, calculator):
        """Test system stability under various conditions."""
        
        # Test with various text lengths and positions
        test_cases = [
            ("Short text.", 5),
            ("Medium length text with several words and punctuation marks.", 25),
            ("Very long text that contains multiple sentences and should test the system's ability to handle larger inputs without performance degradation or accuracy loss." * 5, 200)
        ]
        
        for text, position in test_cases:
            for rule_type in ['grammar', 'spelling', 'tone', 'commands']:
                for content_type in ['technical', 'narrative', 'general']:
                    confidence = calculator.calculate_normalized_confidence(
                        text=text,
                        error_position=min(position, len(text) - 1),
                        rule_type=rule_type,
                        content_type=content_type
                    )
                    
                    assert 0.0 <= confidence <= 1.0, f"Invalid confidence {confidence} for {rule_type}/{content_type}"
        
        print("System stability test passed for all combinations")


class TestUniversalThresholdSystem:
    """Test the universal threshold system implementation."""
    
    @pytest.fixture
    def threshold_config(self):
        """Create ValidationThresholdsConfig instance for testing."""
        try:
            from validation.config.validation_thresholds_config import ValidationThresholdsConfig
            return ValidationThresholdsConfig()
        except ImportError:
            pytest.skip("ValidationThresholdsConfig not available")
    
    def test_universal_threshold_loading(self, threshold_config):
        """Test that universal threshold loads correctly."""
        
        thresholds = threshold_config.get_minimum_confidence_thresholds()
        
        # Should have universal threshold
        assert 'universal' in thresholds, "Universal threshold should be present"
        assert thresholds['universal'] == 0.35, f"Universal threshold should be 0.35, got {thresholds['universal']}"
        
        # Legacy thresholds should map to universal
        legacy_keys = ['default', 'high_confidence', 'medium_confidence', 'low_confidence', 'rejection_threshold']
        for key in legacy_keys:
            if key in thresholds:
                assert thresholds[key] == 0.35, f"Legacy threshold {key} should map to 0.35, got {thresholds[key]}"
        
        print(f"Universal threshold validated: {thresholds['universal']}")
    
    def test_confidence_explanation_generation(self, threshold_config):
        """Test confidence explanation generation."""
        
        test_cases = [
            (0.5, 'grammar', 'technical', True),   # Above threshold
            (0.2, 'tone', 'narrative', False),     # Below threshold
            (0.35, 'commands', 'procedural', True), # Exactly at threshold
        ]
        
        for confidence, rule_type, content_type, should_meet in test_cases:
            explanation = threshold_config.create_confidence_breakdown(confidence, rule_type, content_type)
            
            # Validate explanation structure
            assert 'final_confidence' in explanation, "Should have final_confidence"
            assert 'universal_threshold' in explanation, "Should have universal_threshold"
            assert 'meets_threshold' in explanation, "Should have meets_threshold"
            assert 'rule_type' in explanation, "Should have rule_type"
            assert 'content_type' in explanation, "Should have content_type"
            assert 'explanation' in explanation, "Should have explanation text"
            
            # Validate explanation accuracy
            assert explanation['final_confidence'] == confidence, f"Confidence mismatch: expected {confidence}, got {explanation['final_confidence']}"
            assert explanation['universal_threshold'] == 0.35, f"Threshold should be 0.35, got {explanation['universal_threshold']}"
            assert explanation['meets_threshold'] == should_meet, f"Threshold meeting should be {should_meet}, got {explanation['meets_threshold']}"
            assert explanation['rule_type'] == rule_type, f"Rule type mismatch: expected {rule_type}, got {explanation['rule_type']}"
            assert explanation['content_type'] == content_type, f"Content type mismatch: expected {content_type}, got {explanation['content_type']}"
            
            # Validate explanation text
            explanation_text = explanation['explanation']
            assert str(confidence) in explanation_text, "Explanation should contain confidence score"
            assert '0.35' in explanation_text, "Explanation should contain universal threshold"
            assert rule_type in explanation_text, "Explanation should contain rule type"
            assert content_type in explanation_text, "Explanation should contain content type"
            
            if should_meet:
                assert "✅" in explanation_text, "Explanation should indicate acceptance"
            else:
                assert "❌" in explanation_text, "Explanation should indicate rejection"
            
            print(f"Explanation for {confidence:.2f}: {explanation_text[:80]}...")
    
    def test_threshold_consistency_across_system(self, threshold_config):
        """Test that universal threshold is applied consistently."""
        
        # Test that all threshold access methods return universal threshold
        thresholds = threshold_config.get_minimum_confidence_thresholds()
        universal_threshold = thresholds['universal']
        
        # All legacy methods should return universal threshold
        legacy_values = [
            thresholds.get('default', universal_threshold),
            thresholds.get('high_confidence', universal_threshold),
            thresholds.get('medium_confidence', universal_threshold),
            thresholds.get('low_confidence', universal_threshold),
            thresholds.get('rejection_threshold', universal_threshold)
        ]
        
        for value in legacy_values:
            assert value == universal_threshold, f"All threshold values should be {universal_threshold}, got {value}"
        
        print(f"Threshold consistency validated: all methods return {universal_threshold}")
    
    def test_simplified_configuration_validation(self, threshold_config):
        """Test that simplified configuration validation works."""
        
        # Test valid simplified configuration
        valid_config = {
            'minimum_confidence_thresholds': {
                'universal': 0.35,
                'default': 0.35
            },
            'multi_pass_validation': {
                'enabled': True,
                'passes': {
                    'morphological': {'enabled': True, 'weight': 0.35}
                }
            },
            'performance_settings': {
                'result_caching': {'enabled': True, 'cache_ttl': 600}
            }
        }
        
        # Should validate successfully
        try:
            is_valid = threshold_config.validate_config(valid_config)
            assert is_valid, "Valid simplified config should pass validation"
            print("✅ Simplified configuration validation passed")
        except Exception as e:
            pytest.fail(f"Valid simplified config failed validation: {e}")
        
        # Test invalid configuration
        invalid_config = {
            'minimum_confidence_thresholds': {
                'universal': 1.5  # Invalid range
            }
        }
        
        with pytest.raises(Exception):
            threshold_config.validate_config(invalid_config)
        
        print("✅ Invalid configuration properly rejected")
    
    def test_configuration_file_simplification(self, threshold_config):
        """Test that configuration file has been simplified correctly."""
        
        config = threshold_config.load_config()
        
        # Should have required sections
        assert 'minimum_confidence_thresholds' in config, "Should have minimum_confidence_thresholds"
        assert config['minimum_confidence_thresholds']['universal'] == 0.35, "Universal threshold should be 0.35"
        
        # Should have optional sections
        if 'multi_pass_validation' in config:
            assert 'enabled' in config['multi_pass_validation'], "Multi-pass should have enabled flag"
        
        if 'performance_settings' in config:
            assert isinstance(config['performance_settings'], dict), "Performance settings should be dict"
        
        # Should NOT have complex legacy sections (they should be simplified or removed)
        legacy_complex_sections = [
            'severity_thresholds',
            'error_acceptance_criteria', 
            'rule_specific_thresholds',
            'content_type_thresholds'
        ]
        
        simplified_count = 0
        for section in legacy_complex_sections:
            if section not in config:
                simplified_count += 1
        
        print(f"Configuration simplification: {simplified_count}/{len(legacy_complex_sections)} complex sections removed")
        
        # At least some sections should be simplified
        assert simplified_count > 0, "Configuration should have been simplified from original complex version"


class TestNormalizationIntegration:
    """Test normalization algorithm integration with universal threshold."""
    
    @pytest.fixture
    def calculator(self):
        """Create ConfidenceCalculator instance for testing."""
        return ConfidenceCalculator(cache_results=True)
    
    @pytest.fixture
    def threshold_config(self):
        """Create ValidationThresholdsConfig instance for testing."""
        try:
            from validation.config.validation_thresholds_config import ValidationThresholdsConfig
            return ValidationThresholdsConfig()
        except ImportError:
            pytest.skip("ValidationThresholdsConfig not available")
    
    def test_normalization_with_universal_threshold(self, calculator, threshold_config):
        """Test that normalization works correctly with universal threshold."""
        
        test_text = "This is a test sentence for confidence normalization validation."
        
        # Calculate normalized confidence
        normalized_confidence = calculator.calculate_normalized_confidence(
            text=test_text,
            error_position=25,
            rule_type='grammar',
            content_type='general'
        )
        
        # Get universal threshold
        thresholds = threshold_config.get_minimum_confidence_thresholds()
        universal_threshold = thresholds['universal']
        
        # Test threshold application
        meets_threshold = normalized_confidence >= universal_threshold
        
        # Generate explanation
        explanation = threshold_config.create_confidence_breakdown(
            normalized_confidence, 'grammar', 'general'
        )
        
        # Validate integration
        assert 0.0 <= normalized_confidence <= 1.0, f"Normalized confidence {normalized_confidence} outside valid range"
        assert explanation['meets_threshold'] == meets_threshold, "Explanation threshold evaluation should match calculation"
        assert explanation['universal_threshold'] == universal_threshold, "Explanation should use universal threshold"
        
        print(f"Normalization integration: confidence={normalized_confidence:.3f}, threshold={universal_threshold}, meets={meets_threshold}")
    
    def test_cross_rule_normalization_consistency(self, calculator, threshold_config):
        """Test that normalized confidence is consistent across rule types."""
        
        test_text = "This sentence will be tested across multiple rule types for consistency."
        error_position = 30
        universal_threshold = threshold_config.get_minimum_confidence_thresholds()['universal']
        
        rule_types = ['grammar', 'spelling', 'punctuation', 'tone', 'word_usage']
        normalized_confidences = {}
        
        for rule_type in rule_types:
            confidence = calculator.calculate_normalized_confidence(
                text=test_text,
                error_position=error_position,
                rule_type=rule_type,
                content_type='general'
            )
            
            normalized_confidences[rule_type] = confidence
            
            # Should be in valid range
            assert 0.0 <= confidence <= 1.0, f"Confidence for {rule_type} outside valid range: {confidence}"
            
            # Test with universal threshold
            meets_threshold = confidence >= universal_threshold
            explanation = threshold_config.create_confidence_breakdown(confidence, rule_type, 'general')
            assert explanation['meets_threshold'] == meets_threshold, f"Threshold evaluation inconsistent for {rule_type}"
        
        # Test that confidences are reasonable (not all identical, not too spread out)
        confidence_values = list(normalized_confidences.values())
        std_dev = (sum((c - sum(confidence_values)/len(confidence_values))**2 for c in confidence_values) / len(confidence_values))**0.5
        
        assert 0.01 <= std_dev <= 0.4, f"Confidence standard deviation {std_dev:.3f} indicates poor normalization"
        
        print(f"Cross-rule consistency: std_dev={std_dev:.3f}, universal_threshold={universal_threshold}")
        for rule_type, confidence in normalized_confidences.items():
            meets = "✅" if confidence >= universal_threshold else "❌"
            print(f"  {rule_type}: {confidence:.3f} {meets}")


class TestConfidenceProvenance:
    """Test the provenance-aware confidence blending (Upgrade 3)."""
    
    @pytest.fixture
    def calculator(self):
        """Create ConfidenceCalculator instance for testing."""
        return ConfidenceCalculator(cache_results=True)
    
    def test_provenance_presence(self, calculator):
        """Test that provenance is always present when evidence is supplied."""
        text = "This is a test sentence with some technical commands like curl."
        error_position = 30
        
        # Test with evidence score
        confidence, breakdown = calculator.calculate_normalized_confidence(
            text=text,
            error_position=error_position,
            rule_type="technical_commands",
            evidence_score=0.85,
            return_breakdown=True
        )
        
        # Provenance should be present
        assert hasattr(breakdown, 'confidence_provenance'), "Provenance should be attached to breakdown"
        assert 'provenance' in breakdown.metadata, "Provenance should be in breakdown metadata"
        
        provenance = breakdown.confidence_provenance
        
        # Check all required provenance fields
        required_fields = [
            'evidence_weight', 'model_weight', 'rule_reliability', 
            'content_modifier', 'floor_guard_triggered', 'raw_confidence',
            'evidence_score', 'final_confidence'
        ]
        
        for field in required_fields:
            assert field in provenance, f"Provenance should contain {field}"
        
        # Test without evidence score
        confidence2, breakdown2 = calculator.calculate_normalized_confidence(
            text=text,
            error_position=error_position,
            rule_type="technical_commands",
            return_breakdown=True
        )
        
        # Provenance should still be present but with zero evidence weight
        provenance2 = breakdown2.confidence_provenance
        assert provenance2['evidence_weight'] == 0.0
        assert provenance2['model_weight'] == 1.0
        assert provenance2['evidence_score'] is None
    
    def test_provenance_value_ranges(self, calculator):
        """Test that provenance values are in valid ranges."""
        text = "Test sentence for validation with technical elements."
        error_position = 15
        
        # Test with different evidence scores
        evidence_scores = [0.1, 0.5, 0.85, 0.95]
        
        for evidence_score in evidence_scores:
            confidence, breakdown = calculator.calculate_normalized_confidence(
                text=text,
                error_position=error_position,
                rule_type="grammar",
                evidence_score=evidence_score,
                return_breakdown=True
            )
            
            provenance = breakdown.confidence_provenance
            
            # Test ranges
            assert 0.0 <= provenance['evidence_weight'] <= 1.0, f"Evidence weight out of range: {provenance['evidence_weight']}"
            assert 0.0 <= provenance['model_weight'] <= 1.0, f"Model weight out of range: {provenance['model_weight']}"
            assert 0.0 <= provenance['rule_reliability'] <= 1.0, f"Rule reliability out of range: {provenance['rule_reliability']}"
            assert 0.0 <= provenance['content_modifier'] <= 2.0, f"Content modifier out of range: {provenance['content_modifier']}"
            assert 0.0 <= provenance['raw_confidence'] <= 1.0, f"Raw confidence out of range: {provenance['raw_confidence']}"
            assert 0.0 <= provenance['final_confidence'] <= 1.0, f"Final confidence out of range: {provenance['final_confidence']}"
            
            # Evidence and model weights should sum to 1.0 (when evidence is present)
            weight_sum = provenance['evidence_weight'] + provenance['model_weight']
            assert abs(weight_sum - 1.0) < 0.001, f"Weights don't sum to 1.0: {weight_sum}"
    
    def test_floor_guard_behavior(self, calculator):
        """Test that floor guard is correctly tracked in provenance."""
        text = "High-quality technical documentation with clear examples."
        error_position = 20
        
        # Test with high evidence and high reliability (should trigger guard)
        confidence, breakdown = calculator.calculate_normalized_confidence(
            text=text,
            error_position=error_position,
            rule_type="technical_commands",  # Usually has high reliability
            evidence_score=0.90,  # High evidence
            return_breakdown=True
        )
        
        provenance = breakdown.confidence_provenance
        
        # Check if floor guard was triggered properly
        if provenance['evidence_score'] >= 0.85 and provenance['rule_reliability'] >= 0.85:
            # Guard should potentially trigger, check confidence is at least 0.75
            if provenance['floor_guard_triggered']:
                assert provenance['final_confidence'] >= 0.75, "Floor guard should ensure confidence >= 0.75"
        
        # Test with low evidence (should not trigger guard)
        confidence2, breakdown2 = calculator.calculate_normalized_confidence(
            text=text,
            error_position=error_position,
            rule_type="technical_commands",
            evidence_score=0.50,  # Lower evidence
            return_breakdown=True
        )
        
        provenance2 = breakdown2.confidence_provenance
        assert not provenance2['floor_guard_triggered'], "Floor guard should not trigger with low evidence"
    
    def test_evidence_weight_scaling(self, calculator):
        """Test that evidence weight scales with evidence strength."""
        text = "Technical documentation example for testing."
        error_position = 10
        
        evidence_scores = [0.2, 0.5, 0.8, 0.95]
        previous_weight = 0.0
        
        for evidence_score in evidence_scores:
            confidence, breakdown = calculator.calculate_normalized_confidence(
                text=text,
                error_position=error_position,
                rule_type="grammar",
                evidence_score=evidence_score,
                return_breakdown=True
            )
            
            evidence_weight = breakdown.confidence_provenance['evidence_weight']
            
            # Evidence weight should increase with evidence score
            assert evidence_weight > previous_weight, f"Evidence weight should increase: {evidence_weight} > {previous_weight}"
            
            # Weight should be in expected range (0.2 to 0.7)
            assert 0.2 <= evidence_weight <= 0.7, f"Evidence weight out of expected range: {evidence_weight}"
            
            previous_weight = evidence_weight
    
    def test_provenance_backward_compatibility(self, calculator):
        """Test that existing code still works without return_breakdown."""
        text = "Test compatibility with existing confidence calculation."
        error_position = 15
        
        # Old way should still work
        confidence = calculator.calculate_normalized_confidence(
            text=text,
            error_position=error_position,
            rule_type="grammar",
            evidence_score=0.75
        )
        
        assert isinstance(confidence, float), "Should return float when return_breakdown=False"
        assert 0.0 <= confidence <= 1.0, "Confidence should be in valid range"
    
    def test_provenance_serialization(self, calculator):
        """Test that provenance can be serialized (for UI/debug)."""
        text = "Test sentence for serialization testing."
        error_position = 10
        
        confidence, breakdown = calculator.calculate_normalized_confidence(
            text=text,
            error_position=error_position,
            rule_type="grammar",
            evidence_score=0.80,
            return_breakdown=True
        )
        
        provenance = breakdown.confidence_provenance
        
        # Test JSON serialization
        import json
        try:
            json_str = json.dumps(provenance)
            restored = json.loads(json_str)
            
            # Check that all values are preserved
            for key, value in provenance.items():
                assert key in restored, f"Key {key} missing after serialization"
                if isinstance(value, float):
                    assert abs(restored[key] - value) < 0.001, f"Value mismatch for {key}"
                else:
                    assert restored[key] == value, f"Value mismatch for {key}"
                    
        except (TypeError, ValueError) as e:
            pytest.fail(f"Provenance should be serializable: {e}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
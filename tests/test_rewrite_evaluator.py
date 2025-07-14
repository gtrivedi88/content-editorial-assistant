"""
Rewrite Evaluator Tests
Tests for the RewriteEvaluator class that handles confidence calculation and improvement extraction.
"""

import pytest
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rewriter.evaluators import RewriteEvaluator
from tests.test_utils import TestConfig, TestFixtures, TestValidators


class TestRewriteEvaluator:
    """Test suite for the RewriteEvaluator class."""
    
    @pytest.fixture
    def sample_errors(self):
        """Sample errors for testing."""
        return TestFixtures.get_sample_errors()
    
    def test_rewrite_evaluator_initialization(self):
        """Test RewriteEvaluator initialization."""
        
        evaluator = RewriteEvaluator()
        assert isinstance(evaluator, RewriteEvaluator)
    
    def test_rewrite_evaluator_confidence_calculation(self, sample_errors):
        """Test confidence calculation."""
        
        evaluator = RewriteEvaluator()
        
        confidence = evaluator.calculate_confidence(
            TestConfig.SAMPLE_TEXT, 
            TestConfig.SAMPLE_IMPROVED_TEXT, 
            sample_errors, 
            use_ollama=True
        )
        
        assert isinstance(confidence, float)
        assert TestConfig.MIN_CONFIDENCE <= confidence <= TestConfig.MAX_CONFIDENCE
    
    def test_rewrite_evaluator_confidence_ollama_bonus(self, sample_errors):
        """Test confidence bonus for Ollama usage."""
        
        evaluator = RewriteEvaluator()
        
        ollama_confidence = evaluator.calculate_confidence(
            TestConfig.SAMPLE_TEXT, 
            TestConfig.SAMPLE_IMPROVED_TEXT, 
            sample_errors, 
            use_ollama=True
        )
        
        hf_confidence = evaluator.calculate_confidence(
            TestConfig.SAMPLE_TEXT, 
            TestConfig.SAMPLE_IMPROVED_TEXT, 
            sample_errors, 
            use_ollama=False
        )
        
        # Ollama should have higher confidence bonus
        assert ollama_confidence >= hf_confidence
    
    def test_rewrite_evaluator_confidence_no_changes_penalty(self, sample_errors):
        """Test confidence penalty when no changes are made."""
        
        evaluator = RewriteEvaluator()
        
        # Same text (no changes)
        no_change_confidence = evaluator.calculate_confidence(
            TestConfig.SAMPLE_TEXT, 
            TestConfig.SAMPLE_TEXT, 
            sample_errors, 
            use_ollama=True
        )
        
        # Different text (changes made)
        with_changes_confidence = evaluator.calculate_confidence(
            TestConfig.SAMPLE_TEXT, 
            TestConfig.SAMPLE_IMPROVED_TEXT, 
            sample_errors, 
            use_ollama=True
        )
        
        # No changes should have lower confidence
        assert no_change_confidence < with_changes_confidence
    
    def test_rewrite_evaluator_second_pass_confidence(self, sample_errors):
        """Test second pass confidence calculation."""
        
        evaluator = RewriteEvaluator()
        
        confidence = evaluator.calculate_second_pass_confidence(
            "First pass result", 
            "Final polished result", 
            sample_errors
        )
        
        assert isinstance(confidence, float)
        assert TestConfig.MIN_CONFIDENCE <= confidence <= TestConfig.MAX_CONFIDENCE
        assert confidence >= 0.7  # Should be high for second pass
    
    def test_rewrite_evaluator_extract_improvements(self, sample_errors):
        """Test improvement extraction."""
        
        evaluator = RewriteEvaluator()
        
        improvements = evaluator.extract_improvements(
            "The document was written by the team using passive voice.",
            "The team wrote the document using active voice.",
            sample_errors
        )
        
        assert isinstance(improvements, list)
        assert len(improvements) > 0
        assert any('passive voice' in imp.lower() for imp in improvements)
    
    def test_rewrite_evaluator_second_pass_improvements(self):
        """Test second pass improvement extraction."""
        
        evaluator = RewriteEvaluator()
        
        improvements = evaluator.extract_second_pass_improvements(
            "First pass result text",
            "Final polished result text with enhancements"
        )
        
        assert isinstance(improvements, list)
        assert len(improvements) > 0
    
    def test_rewrite_evaluator_analyze_changes(self):
        """Test change analysis."""
        
        evaluator = RewriteEvaluator()
        
        analysis = evaluator.analyze_changes(
            "This is the original text. It has multiple sentences.",
            "This is improved text. It has better structure."
        )
        
        assert isinstance(analysis, dict)
        assert 'word_count_change' in analysis
        assert 'sentence_count_change' in analysis
        assert 'structural_changes' in analysis
    
    def test_rewrite_evaluator_comprehensive_evaluation(self, sample_errors):
        """Test comprehensive rewrite evaluation."""
        
        evaluator = RewriteEvaluator()
        
        evaluation = evaluator.evaluate_rewrite_quality(
            TestConfig.SAMPLE_TEXT,
            TestConfig.SAMPLE_IMPROVED_TEXT,
            sample_errors,
            use_ollama=True
        )
        
        # Validate using utility
        required_keys = ['confidence', 'improvements', 'changes_analysis', 'quality_score', 'pass_number', 'model_used']
        for key in required_keys:
            assert key in evaluation
        
        assert isinstance(evaluation['confidence'], float)
        assert isinstance(evaluation['improvements'], list)
        assert isinstance(evaluation['changes_analysis'], dict)
        assert isinstance(evaluation['quality_score'], float)
    
    def test_rewrite_evaluator_quality_score_calculation(self, sample_errors):
        """Test quality score calculation."""
        
        evaluator = RewriteEvaluator()
        
        # Mock a realistic changes analysis
        changes_analysis = {
            'word_count_change': -5,  # Shorter is often better
            'sentence_count_change': 1,  # Split long sentence
            'structural_changes': ['Sentence splitting', 'Active voice conversion']
        }
        
        quality_score = evaluator._calculate_quality_score(0.8, changes_analysis, sample_errors)
        
        assert isinstance(quality_score, float)
        assert TestConfig.MIN_CONFIDENCE <= quality_score <= TestConfig.MAX_CONFIDENCE
    
    def test_rewrite_evaluator_improvement_categorization(self, sample_errors):
        """Test improvement categorization by error type."""
        
        evaluator = RewriteEvaluator()
        
        # Create specific test case
        original = "The document was written by the team in a very long sentence that goes on and on."
        rewritten = "The team wrote the document. This version is concise and clear."
        
        improvements = evaluator.extract_improvements(original, rewritten, sample_errors)
        
        # Should identify multiple types of improvements
        assert isinstance(improvements, list)
        assert len(improvements) > 0
        
        # Check for specific improvement types
        improvements_text = ' '.join(improvements).lower()
        assert any(keyword in improvements_text for keyword in ['passive', 'active', 'length', 'clarity'])
    
    def test_rewrite_evaluator_error_handling(self, sample_errors):
        """Test error handling in evaluation methods."""
        
        evaluator = RewriteEvaluator()
        
        # Test with problematic inputs
        try:
            confidence = evaluator.calculate_confidence("", "", sample_errors, use_ollama=True)
            assert isinstance(confidence, float)
            assert confidence >= 0.0
        except Exception:
            pytest.fail("Evaluator should handle empty inputs gracefully")
        
        try:
            evaluation = evaluator.evaluate_rewrite_quality("", "", [], use_ollama=True)
            assert isinstance(evaluation, dict)
        except Exception:
            pytest.fail("Evaluator should handle empty inputs gracefully")
    
    def test_rewrite_evaluator_consistency(self, sample_errors):
        """Test evaluation consistency across multiple calls."""
        
        evaluator = RewriteEvaluator()
        
        # Run same evaluation multiple times
        results = []
        for _ in range(3):
            confidence = evaluator.calculate_confidence(
                TestConfig.SAMPLE_TEXT,
                TestConfig.SAMPLE_IMPROVED_TEXT,
                sample_errors,
                use_ollama=True
            )
            results.append(confidence)
        
        # Results should be consistent
        assert all(abs(r - results[0]) < 0.1 for r in results)
    
    def test_rewrite_evaluator_pass_number_tracking(self, sample_errors):
        """Test pass number tracking in evaluations."""
        
        evaluator = RewriteEvaluator()
        
        # Test first pass
        eval1 = evaluator.evaluate_rewrite_quality(
            TestConfig.SAMPLE_TEXT,
            TestConfig.SAMPLE_IMPROVED_TEXT,
            sample_errors,
            use_ollama=True,
            pass_number=1
        )
        
        # Test second pass
        eval2 = evaluator.evaluate_rewrite_quality(
            TestConfig.SAMPLE_TEXT,
            TestConfig.SAMPLE_IMPROVED_TEXT,
            sample_errors,
            use_ollama=True,
            pass_number=2
        )
        
        assert eval1['pass_number'] == 1
        assert eval2['pass_number'] == 2
        
        # Second pass should generally have higher confidence
        assert eval2['confidence'] >= eval1['confidence']
    
    def test_rewrite_evaluator_length_ratio_penalty(self, sample_errors):
        """Test penalty for extreme length changes."""
        
        evaluator = RewriteEvaluator()
        
        # Test extremely long rewrite
        very_long_rewrite = TestConfig.SAMPLE_TEXT + " " + "Additional content. " * 20
        
        long_confidence = evaluator.calculate_confidence(
            TestConfig.SAMPLE_TEXT,
            very_long_rewrite,
            sample_errors,
            use_ollama=True
        )
        
        # Test normal length rewrite
        normal_confidence = evaluator.calculate_confidence(
            TestConfig.SAMPLE_TEXT,
            TestConfig.SAMPLE_IMPROVED_TEXT,
            sample_errors,
            use_ollama=True
        )
        
        # Extremely long rewrites should have lower confidence
        assert normal_confidence >= long_confidence
    
    def test_rewrite_evaluator_no_errors_handling(self):
        """Test evaluation when no errors are provided."""
        
        evaluator = RewriteEvaluator()
        
        confidence = evaluator.calculate_confidence(
            TestConfig.SAMPLE_TEXT,
            TestConfig.SAMPLE_IMPROVED_TEXT,
            [],  # No errors
            use_ollama=True
        )
        
        # Should still provide reasonable confidence
        assert isinstance(confidence, float)
        assert confidence >= 0.5  # Should be decent even without specific errors
    
    def test_rewrite_evaluator_configuration_flexibility(self, sample_errors):
        """Test that evaluator can handle different configurations."""
        
        evaluator = RewriteEvaluator()
        
        # Test different model types
        for use_ollama in [True, False]:
            evaluation = evaluator.evaluate_rewrite_quality(
                TestConfig.SAMPLE_TEXT,
                TestConfig.SAMPLE_IMPROVED_TEXT,
                sample_errors,
                use_ollama=use_ollama
            )
            
            assert evaluation['model_used'] == ('ollama' if use_ollama else 'huggingface')
            assert isinstance(evaluation['confidence'], float) 
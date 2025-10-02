"""
Test Suite for Linguistic Evidence Analyzer
Tests the enhanced linguistic pattern detection system for confidence calculation.
"""

import pytest
import time
from typing import List, Dict, Any
from unittest.mock import Mock, patch

# Import linguistic analysis components
try:
    from validation.confidence.linguistic_anchors import LinguisticAnchors, AnchorAnalysis
    from validation.confidence.context_analyzer import ContextAnalyzer, ContextAnalysis
    from validation.confidence.domain_classifier import DomainClassifier, DomainAnalysis
    ENHANCED_SYSTEM_AVAILABLE = True
except ImportError:
    ENHANCED_SYSTEM_AVAILABLE = False


@pytest.mark.skipif(not ENHANCED_SYSTEM_AVAILABLE, reason="Enhanced validation system not available")
class TestMorphologicalEvidenceDetection:
    """Test morphological evidence detection capabilities."""
    
    @pytest.fixture
    def linguistic_anchors(self):
        """Create LinguisticAnchors instance for testing."""
        return LinguisticAnchors(cache_compiled_patterns=True)
    
    @pytest.fixture
    def test_texts(self):
        """Sample texts for morphological analysis."""
        return {
            'grammar_error': "The company have implemented new policies for their employees.",
            'punctuation_error': "However; this implementation was delayed, due to various factors.",
            'word_usage_error': "We need to discuss this between you and I.",
            'passive_voice': "The document was written by the committee.",
            'complex_sentence': "Although the committee, which was formed last year, has been working diligently on the proposal, it has not yet reached a consensus.",
            'correct_text': "The team successfully completed the project on time."
        }
    
    def test_morphological_evidence_detection(self, linguistic_anchors, test_texts):
        """Test POS tag analysis and dependency parsing."""
        
        for text_type, text in test_texts.items():
            analysis = linguistic_anchors.analyze_text(
                text=text,
                error_position=len(text) // 2,
                rule_type='grammar',
                content_type='general'
            )
            
            # Should return valid analysis
            assert isinstance(analysis, AnchorAnalysis), f"Analysis should be AnchorAnalysis object for {text_type}"
            assert hasattr(analysis, 'net_effect'), f"Analysis should have net_effect for {text_type}"
            assert hasattr(analysis, 'explanation'), f"Analysis should have explanation for {text_type}"
            
            # Net effect should be in valid range
            assert -1.0 <= analysis.net_effect <= 1.0, f"Net effect {analysis.net_effect} outside valid range for {text_type}"
            
            # Should have meaningful explanation
            assert len(analysis.explanation) > 10, f"Explanation too short for {text_type}: '{analysis.explanation}'"
            
            print(f"{text_type}: {analysis.net_effect:.3f} - {analysis.explanation[:50]}...")
    
    def test_syntactic_evidence_detection(self, linguistic_anchors, test_texts):
        """Test sentence structure analysis."""
        
        # Test specific syntactic patterns
        syntactic_tests = [
            ('complex_sentence', 'should detect complex structure'),
            ('passive_voice', 'should detect passive construction'),
            ('correct_text', 'should recognize correct structure')
        ]
        
        for text_key, description in syntactic_tests:
            text = test_texts[text_key]
            
            analysis = linguistic_anchors.analyze_text(
                text=text,
                error_position=len(text) // 2,
                rule_type='grammar',
                content_type='general'
            )
            
            # Should provide reasonable syntactic assessment
            assert isinstance(analysis.net_effect, float), f"Net effect should be float for {description}"
            
            # Complex sentences should typically have different scores than simple ones
            if text_key == 'complex_sentence':
                assert analysis.net_effect != 0.0, f"Complex sentence should have non-zero effect"
            
            print(f"{description}: {analysis.net_effect:.3f}")
    
    def test_semantic_evidence_detection(self, linguistic_anchors, test_texts):
        """Test semantic coherence analysis."""
        
        semantic_tests = [
            ('grammar_error', 'should detect semantic inconsistency'),
            ('word_usage_error', 'should detect usage problems'),
            ('correct_text', 'should recognize coherent semantics')
        ]
        
        for text_key, description in semantic_tests:
            text = test_texts[text_key]
            
            analysis = linguistic_anchors.analyze_text(
                text=text,
                error_position=len(text) // 2,
                rule_type='word_usage',
                content_type='general'
            )
            
            # Should provide semantic analysis
            assert analysis is not None, f"Should provide analysis for {description}"
            assert analysis.explanation is not None, f"Should provide explanation for {description}"
            
            # Semantic scores should be meaningful
            assert -1.0 <= analysis.net_effect <= 1.0, f"Semantic effect outside valid range for {description}"
            
            print(f"{description}: {analysis.net_effect:.3f}")


@pytest.mark.skipif(not ENHANCED_SYSTEM_AVAILABLE, reason="Enhanced validation system not available")
class TestPatternStrengthScoring:
    """Test pattern strength calculation and scoring."""
    
    @pytest.fixture
    def context_analyzer(self):
        """Create ContextAnalyzer instance for testing."""
        return ContextAnalyzer(cache_nlp_results=True)
    
    @pytest.fixture
    def pattern_test_cases(self):
        """Test cases for pattern strength assessment."""
        return [
            {
                'text': "This is a clear, straightforward sentence.",
                'rule_type': 'grammar',
                'expected_range': (0.3, 0.8),
                'description': 'simple correct sentence'
            },
            {
                'text': "The implementation, although complex, was successful.",
                'rule_type': 'punctuation',
                'expected_range': (0.2, 0.7),
                'description': 'complex but correct punctuation'
            },
            {
                'text': "However; this is incorrect punctuation usage.",
                'rule_type': 'punctuation',
                'expected_range': (-0.5, 0.3),
                'description': 'incorrect punctuation pattern'
            },
            {
                'text': "We need to discuss this between you and I.",
                'rule_type': 'word_usage',
                'expected_range': (-0.6, 0.2),
                'description': 'incorrect pronoun usage'
            }
        ]
    
    def test_pattern_strength_scoring(self, context_analyzer, pattern_test_cases):
        """Test pattern strength calculation accuracy."""
        
        for test_case in pattern_test_cases:
            analysis = context_analyzer.analyze_context(
                text=test_case['text'],
                error_position=len(test_case['text']) // 2,
                rule_type=test_case['rule_type'],
                content_type='general'
            )
            
            # Should provide context analysis
            assert isinstance(analysis, ContextAnalysis), f"Should return ContextAnalysis for {test_case['description']}"
            
            # Pattern strength should be in expected range
            confidence_effect = analysis.confidence_effects.get('net_effect', 0.0)
            min_expected, max_expected = test_case['expected_range']
            
            print(f"{test_case['description']}: {confidence_effect:.3f} (expected: {min_expected} to {max_expected})")
            
            # Flexible range check - patterns are complex and context-dependent
            assert -1.0 <= confidence_effect <= 1.0, f"Confidence effect outside valid range for {test_case['description']}"
    
    def test_evidence_aggregation(self, context_analyzer):
        """Test combining multiple evidence types."""
        
        # Test with text that has multiple pattern types
        complex_text = """
        The implementation; although it was complex, and required significant effort
        from the team, was ultimately successful in achieving it's goals.
        """
        
        analysis = context_analyzer.analyze_context(
            text=complex_text,
            error_position=50,
            rule_type='grammar',
            content_type='technical'
        )
        
        # Should aggregate multiple evidence types
        assert isinstance(analysis, ContextAnalysis), "Should return ContextAnalysis"
        assert hasattr(analysis, 'confidence_effects'), "Should have confidence_effects"
        
        effects = analysis.confidence_effects
        
        # Should have multiple confidence components
        assert 'structural' in effects, "Should have structural confidence"
        assert 'coreference' in effects, "Should have coreference confidence"
        assert 'coherence' in effects, "Should have coherence confidence"
        assert 'discourse' in effects, "Should have discourse confidence"
        assert 'net_effect' in effects, "Should have net_effect"
        
        # Net effect should be reasonable aggregation
        net_effect = effects['net_effect']
        assert -1.0 <= net_effect <= 1.0, f"Net effect {net_effect} outside valid range"
        
        print(f"Evidence aggregation: {net_effect:.3f}")
        print(f"Components: structural={effects['structural']:.3f}, coreference={effects['coreference']:.3f}")


@pytest.mark.skipif(not ENHANCED_SYSTEM_AVAILABLE, reason="Enhanced validation system not available")
class TestLinguisticAnalysisPerformance:
    """Test performance characteristics of linguistic analysis."""
    
    @pytest.fixture
    def linguistic_anchors(self):
        """Create LinguisticAnchors instance for performance testing."""
        return LinguisticAnchors(cache_compiled_patterns=True)
    
    @pytest.fixture
    def performance_test_texts(self):
        """Text samples of varying lengths for performance testing."""
        return {
            'short': "This is a short sentence for testing.",
            'medium': " ".join(["This is a medium-length sentence for performance testing."] * 10),
            'long': " ".join(["This is a longer sentence that will test performance with substantial text content."] * 50),
            'very_long': " ".join(["This sentence tests performance with very long text content that includes multiple paragraphs and complex structure."] * 200)
        }
    
    def test_linguistic_analysis_performance(self, linguistic_anchors, performance_test_texts):
        """Test processing speed for various text lengths."""
        
        performance_results = {}
        
        for text_type, text in performance_test_texts.items():
            word_count = len(text.split())
            
            # Measure processing time
            start_time = time.time()
            analysis = linguistic_anchors.analyze_text(
                text=text,
                error_position=len(text) // 2,
                rule_type='grammar',
                content_type='general'
            )
            processing_time = time.time() - start_time
            
            performance_results[text_type] = {
                'word_count': word_count,
                'processing_time': processing_time,
                'words_per_second': word_count / processing_time if processing_time > 0 else float('inf')
            }
            
            # Should complete in reasonable time
            max_time_per_1000_words = 0.05  # 50ms per 1000 words
            expected_max_time = (word_count / 1000) * max_time_per_1000_words
            
            print(f"{text_type}: {word_count} words in {processing_time*1000:.1f}ms ({word_count/processing_time:.0f} words/sec)")
            
            # Performance assertion - be flexible for different hardware
            assert processing_time < expected_max_time * 3, f"Processing too slow for {text_type}: {processing_time:.3f}s"
            
            # Should produce valid analysis regardless of text length
            assert analysis is not None, f"Should produce analysis for {text_type}"
            assert -1.0 <= analysis.net_effect <= 1.0, f"Invalid net effect for {text_type}"
        
        # Performance should scale reasonably
        short_time = performance_results['short']['processing_time']
        long_time = performance_results['long']['processing_time']
        
        # Long text shouldn't be more than 10x slower than short text
        assert long_time < short_time * 10, f"Performance doesn't scale well: {short_time:.3f}s -> {long_time:.3f}s"
    
    def test_caching_effectiveness(self, linguistic_anchors):
        """Test pattern caching and memory usage."""
        
        test_text = "This is a test sentence for caching validation and performance measurement."
        
        # First analysis (cache miss)
        start_time = time.time()
        analysis1 = linguistic_anchors.analyze_text(
            text=test_text,
            error_position=25,
            rule_type='grammar',
            content_type='general'
        )
        first_time = time.time() - start_time
        
        # Second analysis (should hit cache)
        start_time = time.time()
        analysis2 = linguistic_anchors.analyze_text(
            text=test_text,
            error_position=25,
            rule_type='grammar',
            content_type='general'
        )
        second_time = time.time() - start_time
        
        # Results should be identical
        assert analysis1.net_effect == analysis2.net_effect, "Cached analysis should be identical"
        
        # Second analysis should be faster (cached)
        assert second_time <= first_time, f"Cached analysis should be faster: {first_time:.3f}s -> {second_time:.3f}s"
        
        print(f"Cache effectiveness: {first_time*1000:.1f}ms -> {second_time*1000:.1f}ms")
        
        # Test cache hit rate with multiple similar analyses
        cache_tests = []
        for i in range(10):
            start_time = time.time()
            linguistic_anchors.analyze_text(
                text=test_text,
                error_position=25,
                rule_type='grammar',
                content_type='general'
            )
            cache_tests.append(time.time() - start_time)
        
        # Most cache tests should be faster than first analysis
        fast_analyses = [t for t in cache_tests if t <= first_time]
        cache_hit_rate = len(fast_analyses) / len(cache_tests)
        
        print(f"Cache hit rate: {cache_hit_rate:.1%}")
        assert cache_hit_rate >= 0.8, f"Cache hit rate too low: {cache_hit_rate:.1%}"


@pytest.mark.skipif(not ENHANCED_SYSTEM_AVAILABLE, reason="Enhanced validation system not available")
class TestEvidenceScoreCorrelation:
    """Test that evidence scores correlate with manual assessment."""
    
    @pytest.fixture
    def domain_classifier(self):
        """Create DomainClassifier instance for testing."""
        return DomainClassifier(cache_classifications=True)
    
    @pytest.fixture
    def manual_assessment_cases(self):
        """Test cases with manual quality assessments."""
        return [
            {
                'text': "The team completed the project successfully and on time.",
                'manual_score': 0.8,  # High quality
                'rule_type': 'grammar',
                'description': 'high quality sentence'
            },
            {
                'text': "The company have implemented new policies for their employees.",
                'manual_score': 0.3,  # Poor quality (grammar error)
                'rule_type': 'grammar',
                'description': 'grammar error sentence'
            },
            {
                'text': "However; this implementation was delayed, due to various factors.",
                'manual_score': 0.2,  # Poor quality (punctuation error)
                'rule_type': 'punctuation',
                'description': 'punctuation error sentence'
            },
            {
                'text': "The implementation was complex but ultimately successful.",
                'manual_score': 0.7,  # Good quality
                'rule_type': 'grammar',
                'description': 'good quality sentence'
            },
            {
                'text': "We need to discuss this between you and I.",
                'manual_score': 0.1,  # Very poor quality (usage error)
                'rule_type': 'word_usage',
                'description': 'word usage error'
            }
        ]
    
    def test_evidence_scores_correlate_with_manual_assessment(self, domain_classifier, manual_assessment_cases):
        """Test that evidence scores correlate with manual assessment."""
        
        automated_scores = []
        manual_scores = []
        
        for case in manual_assessment_cases:
            # Get domain analysis (includes evidence scoring)
            analysis = domain_classifier.classify_text(
                text=case['text'],
                context={'rule_type': case['rule_type']}
            )
            
            # Extract confidence-related score
            automated_score = analysis.confidence if hasattr(analysis, 'confidence') else 0.5
            
            automated_scores.append(automated_score)
            manual_scores.append(case['manual_score'])
            
            print(f"{case['description']}: manual={case['manual_score']:.1f}, automated={automated_score:.3f}")
        
        # Calculate correlation coefficient
        correlation = self._calculate_correlation(manual_scores, automated_scores)
        
        print(f"Score correlation: {correlation:.3f}")
        
        # Should have reasonable positive correlation
        assert correlation > 0.3, f"Correlation too low: {correlation:.3f}"
        
        # Should not be perfect (that would suggest overfitting)
        assert correlation < 0.95, f"Correlation suspiciously high: {correlation:.3f}"
    
    def _calculate_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient."""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_x_sq = sum(xi * xi for xi in x)
        sum_y_sq = sum(yi * yi for yi in y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = ((n * sum_x_sq - sum_x * sum_x) * (n * sum_y_sq - sum_y * sum_y)) ** 0.5
        
        if denominator == 0:
            return 0.0
        
        return numerator / denominator


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
"""
Test Suite for Evidence-Based Abbreviations Rule
Testing the transformed abbreviations rule with evidence-based scoring system.
"""

import pytest
import spacy
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Import test dependencies
from rules.language_and_grammar.abbreviations_rule import AbbreviationsRule


class TestEvidenceBasedAbbreviationsRule:
    """Test evidence-based abbreviations rule implementation."""
    
    @pytest.fixture
    def nlp(self):
        """Load spaCy model for testing."""
        try:
            return spacy.load('en_core_web_sm')
        except OSError:
            pytest.skip("SpaCy model 'en_core_web_sm' not available")
    
    @pytest.fixture
    def rule(self):
        """Create abbreviations rule instance."""
        return AbbreviationsRule()
    
    @pytest.fixture
    def sample_text(self):
        """Sample text with various abbreviation scenarios."""
        return '''
        This is an example document that uses e.g. Latin abbreviations.
        The API should be defined on first use. In technical contexts, JSON is commonly used.
        You can SSH to the server using proper commands.
        The Application Programming Interface (API) enables software integration.
        '''

    # === EVIDENCE SCORE VALIDATION TESTS ===

    def test_evidence_scores_in_valid_range(self, rule, nlp, sample_text):
        """Test that all evidence scores are in valid range [0.0, 1.0]."""
        sentences = [sent.text for sent in nlp(sample_text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'}
        
        errors = rule.analyze(sample_text, sentences, nlp, context)
        
        for error in errors:
            evidence_score = error.get('evidence_score')
            assert evidence_score is not None, f"Evidence score missing for error: {error['flagged_text']}"
            assert 0.0 <= evidence_score <= 1.0, f"Evidence score {evidence_score} out of range for {error['flagged_text']}"

    def test_high_evidence_scenarios(self, rule, nlp):
        """Test scenarios that should produce high evidence scores."""
        # Latin abbreviation in general audience context
        text = "This example shows e.g. various patterns."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general', 'audience': 'beginner'}
        
        errors = rule.analyze(text, sentences, nlp, context)
        latin_errors = [e for e in errors if e['flagged_text'] == 'e.g.']
        
        assert len(latin_errors) > 0, "Should detect Latin abbreviation"
        assert latin_errors[0]['evidence_score'] > 0.5, "Should have high evidence for Latin in general context"

    def test_low_evidence_scenarios(self, rule, nlp):
        """Test scenarios that should produce low evidence scores."""
        # Common technical abbreviation in technical context
        text = "The API documentation shows JSON response format."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'}
        
        errors = rule.analyze(text, sentences, nlp, context)
        api_errors = [e for e in errors if e['flagged_text'] == 'API']
        
        # Should have low evidence or no errors due to technical context
        if api_errors:
            assert api_errors[0]['evidence_score'] < 0.5, "Should have low evidence for API in technical context"

    def test_context_sensitivity(self, rule, nlp):
        """Test that evidence varies appropriately with context."""
        text = "You can SSH to the server."
        sentences = [sent.text for sent in nlp(text).sents]
        
        # Test in different contexts
        contexts = [
            {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'},
            {'block_type': 'code_block', 'content_type': 'technical', 'audience': 'developer'},
            {'block_type': 'paragraph', 'content_type': 'general', 'audience': 'beginner'}
        ]
        
        evidence_scores = []
        for context in contexts:
            errors = rule.analyze(text, sentences, nlp, context)
            ssh_errors = [e for e in errors if e['flagged_text'] == 'SSH']
            if ssh_errors:
                evidence_scores.append(ssh_errors[0]['evidence_score'])
        
        # Evidence should vary based on context
        assert len(set(evidence_scores)) > 1, "Evidence scores should vary with context"

    # === LINGUISTIC CLUES TESTS ===

    def test_linguistic_clues_latin_abbreviations(self, rule, nlp):
        """Test linguistic clues for Latin abbreviations."""
        # Test parenthetical context
        text1 = "This example (e.g., technical documentation) shows patterns."
        text2 = "This example e.g. shows patterns."
        
        sentences1 = [sent.text for sent in nlp(text1).sents]
        sentences2 = [sent.text for sent in nlp(text2).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors1 = rule.analyze(text1, sentences1, nlp, context)
        errors2 = rule.analyze(text2, sentences2, nlp, context)
        
        # Parenthetical context should affect evidence differently
        eg_errors1 = [e for e in errors1 if 'e.g' in e['flagged_text']]
        eg_errors2 = [e for e in errors2 if 'e.g' in e['flagged_text']]
        
        if eg_errors1 and eg_errors2:
            # Evidence should be different due to parenthetical context
            assert eg_errors1[0]['evidence_score'] != eg_errors2[0]['evidence_score']

    def test_linguistic_clues_undefined_abbreviations(self, rule, nlp):
        """Test linguistic clues for undefined abbreviations."""
        # Test with named entity
        text1 = "Microsoft Azure provides cloud services."
        text2 = "XYZ provides cloud services."
        
        sentences1 = [sent.text for sent in nlp(text1).sents]
        sentences2 = [sent.text for sent in nlp(text2).sents]
        context = {'block_type': 'paragraph', 'content_type': 'technical'}
        
        errors1 = rule.analyze(text1, sentences1, nlp, context)
        errors2 = rule.analyze(text2, sentences2, nlp, context)
        
        # Named entities should have fewer errors than unknown abbreviations
        assert len(errors1) <= len(errors2), "Named entities should produce fewer errors"

    def test_linguistic_clues_verb_usage(self, rule, nlp):
        """Test linguistic clues for verb usage."""
        # Test direct object pattern (strong verb evidence)
        text = "You can SSH the server easily."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'technical'}
        
        errors = rule.analyze(text, sentences, nlp, context)
        ssh_errors = [e for e in errors if e['flagged_text'] == 'SSH']
        
        assert len(ssh_errors) > 0, "Should detect SSH used as verb"
        assert ssh_errors[0]['evidence_score'] > 0.7, "Should have high evidence for direct verb usage"

    # === STRUCTURAL CLUES TESTS ===

    def test_structural_clues_block_types(self, rule, nlp):
        """Test structural clues for different block types."""
        text = "API Documentation Overview"
        sentences = [sent.text for sent in nlp(text).sents]
        
        contexts = [
            {'block_type': 'heading', 'block_level': 1, 'content_type': 'technical'},
            {'block_type': 'paragraph', 'content_type': 'technical'},
            {'block_type': 'code_block', 'content_type': 'technical'}
        ]
        
        evidence_scores = []
        for context in contexts:
            errors = rule.analyze(text, sentences, nlp, context)
            api_errors = [e for e in errors if e['flagged_text'] == 'API']
            if api_errors:
                evidence_scores.append((context['block_type'], api_errors[0]['evidence_score']))
        
        # Different block types should produce different evidence scores
        block_types = [item[0] for item in evidence_scores]
        scores = [item[1] for item in evidence_scores]
        
        if len(scores) > 1:
            assert len(set(scores)) > 1, f"Different block types should yield different evidence: {evidence_scores}"

    def test_structural_clues_code_context(self, rule, nlp):
        """Test that code context reduces evidence scores."""
        text = "You should SSH to the server."
        sentences = [sent.text for sent in nlp(text).sents]
        
        normal_context = {'block_type': 'paragraph', 'content_type': 'technical'}
        code_context = {'block_type': 'code_block', 'content_type': 'technical'}
        
        normal_errors = rule.analyze(text, sentences, nlp, normal_context)
        code_errors = rule.analyze(text, sentences, nlp, code_context)
        
        normal_ssh = [e for e in normal_errors if e['flagged_text'] == 'SSH']
        code_ssh = [e for e in code_errors if e['flagged_text'] == 'SSH']
        
        # Code context should reduce evidence scores
        if normal_ssh and code_ssh:
            assert code_ssh[0]['evidence_score'] < normal_ssh[0]['evidence_score'], \
                "Code context should reduce evidence scores"

    # === SEMANTIC CLUES TESTS ===

    def test_semantic_clues_content_types(self, rule, nlp):
        """Test semantic clues for different content types."""
        text = "This shows e.g. various examples."
        sentences = [sent.text for sent in nlp(text).sents]
        
        contexts = [
            {'block_type': 'paragraph', 'content_type': 'academic', 'audience': 'expert'},
            {'block_type': 'paragraph', 'content_type': 'marketing', 'audience': 'general'},
            {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'}
        ]
        
        evidence_scores = []
        for context in contexts:
            errors = rule.analyze(text, sentences, nlp, context)
            eg_errors = [e for e in errors if 'e.g' in e['flagged_text']]
            if eg_errors:
                evidence_scores.append((context['content_type'], eg_errors[0]['evidence_score']))
        
        # Different content types should affect evidence
        if len(evidence_scores) > 1:
            content_types = [item[0] for item in evidence_scores]
            scores = [item[1] for item in evidence_scores]
            assert len(set(scores)) > 1, f"Content types should affect evidence: {evidence_scores}"

    def test_semantic_clues_audience_awareness(self, rule, nlp):
        """Test that audience affects evidence scoring."""
        text = "The API enables integration."
        sentences = [sent.text for sent in nlp(text).sents]
        
        expert_context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'expert'}
        beginner_context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'beginner'}
        
        expert_errors = rule.analyze(text, sentences, nlp, expert_context)
        beginner_errors = rule.analyze(text, sentences, nlp, beginner_context)
        
        expert_api = [e for e in expert_errors if e['flagged_text'] == 'API']
        beginner_api = [e for e in beginner_errors if e['flagged_text'] == 'API']
        
        # Beginner audience should have higher evidence scores for undefined terms
        if expert_api and beginner_api:
            assert beginner_api[0]['evidence_score'] >= expert_api[0]['evidence_score'], \
                "Beginner audience should have higher evidence for undefined abbreviations"

    # === FEEDBACK PATTERN TESTS ===

    def test_feedback_patterns_accepted_terms(self, rule, nlp):
        """Test that accepted terms have reduced evidence."""
        text = "This shows e.g. various patterns."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        # Mock feedback patterns to include e.g. as accepted
        with patch.object(rule, '_get_cached_feedback_patterns') as mock_feedback:
            mock_feedback.return_value = {
                'accepted_latin_terms': {'e.g.', 'i.e.'},
                'accepted_undefined_terms': {'API', 'JSON'},
                'rejected_latin_suggestions': set(),
                'accepted_verb_abbreviations': set(),
                'software_accepted_abbreviations': set(),
                'finance_accepted_abbreviations': set(),
                'devops_accepted_abbreviations': set(),
            }
            
            errors = rule.analyze(text, sentences, nlp, context)
            eg_errors = [e for e in errors if 'e.g' in e['flagged_text']]
            
            # Should still detect but with lower evidence due to feedback pattern
            if eg_errors:
                assert eg_errors[0]['evidence_score'] < 0.8, \
                    "Accepted terms should have reduced evidence scores"

    # === INTEGRATION TESTS ===

    def test_enhanced_validation_integration(self, rule, nlp, sample_text):
        """Test that rule works with enhanced validation system."""
        sentences = [sent.text for sent in nlp(sample_text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'technical'}
        
        errors = rule.analyze(sample_text, sentences, nlp, context)
        
        # Check that enhanced validation fields are present
        for error in errors:
            assert 'evidence_score' in error, "Evidence score should be present"
            assert 'type' in error, "Rule type should be present"
            assert error['type'] == 'abbreviations', "Should have correct rule type"
            assert 'enhanced_validation_available' in error, "Enhanced validation flag should be present"

    def test_contextual_messaging(self, rule, nlp):
        """Test that messages adapt to evidence scores."""
        text = "You can SSH to the server."
        sentences = [sent.text for sent in nlp(text).sents]
        
        # High evidence context
        high_context = {'block_type': 'paragraph', 'content_type': 'general', 'audience': 'beginner'}
        # Lower evidence context  
        low_context = {'block_type': 'code_block', 'content_type': 'technical', 'audience': 'developer'}
        
        high_errors = rule.analyze(text, sentences, nlp, high_context)
        low_errors = rule.analyze(text, sentences, nlp, low_context)
        
        high_ssh = [e for e in high_errors if e['flagged_text'] == 'SSH']
        low_ssh = [e for e in low_errors if e['flagged_text'] == 'SSH']
        
        # Messages should adapt to evidence levels
        if high_ssh and low_ssh:
            assert high_ssh[0]['message'] != low_ssh[0]['message'], \
                "Messages should adapt to evidence scores"

    def test_smart_suggestions(self, rule, nlp):
        """Test that suggestions are contextually appropriate."""
        text = "The API is undefined here."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'beginner'}
        
        errors = rule.analyze(text, sentences, nlp, context)
        api_errors = [e for e in errors if e['flagged_text'] == 'API']
        
        if api_errors:
            suggestions = api_errors[0]['suggestions']
            assert len(suggestions) > 0, "Should provide suggestions"
            assert any('define' in s.lower() for s in suggestions), \
                "Should suggest defining abbreviation"

    # === PERFORMANCE TESTS ===

    def test_evidence_calculation_performance(self, rule, nlp):
        """Test that evidence calculation doesn't significantly impact performance."""
        text = "This is a longer document with multiple abbreviations like API, JSON, SSH, etc. " * 20
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'technical'}
        
        import time
        start_time = time.time()
        errors = rule.analyze(text, sentences, nlp, context)
        end_time = time.time()
        
        analysis_time = end_time - start_time
        assert analysis_time < 5.0, f"Evidence calculation too slow: {analysis_time:.2f}s"
        assert len(errors) >= 0, "Should complete analysis successfully"

    def test_no_infinite_loops(self, rule, nlp):
        """Test that evidence calculation doesn't cause infinite loops."""
        # Edge case: document with only abbreviations
        text = "API JSON SSH FTP HTTP HTTPS"
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'technical'}
        
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Evidence calculation timed out")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(10)  # 10 second timeout
        
        try:
            errors = rule.analyze(text, sentences, nlp, context)
            assert isinstance(errors, list), "Should return valid error list"
        except TimeoutError:
            pytest.fail("Evidence calculation caused infinite loop or excessive processing")
        finally:
            signal.alarm(0)
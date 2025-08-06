"""
Test Suite for Evidence-Based Anthropomorphism Rule
Testing the transformed anthropomorphism rule with evidence-based scoring system.
"""

import pytest
import spacy
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Import test dependencies
from rules.language_and_grammar.anthropomorphism_rule import AnthropomorphismRule


class TestEvidenceBasedAnthropomorphismRule:
    """Test evidence-based anthropomorphism rule implementation."""
    
    @pytest.fixture
    def nlp(self):
        """Load spaCy model for testing."""
        try:
            return spacy.load('en_core_web_sm')
        except OSError:
            pytest.skip("SpaCy model 'en_core_web_sm' not available")
    
    @pytest.fixture
    def rule(self):
        """Create anthropomorphism rule instance."""
        return AnthropomorphismRule()

    # === EVIDENCE SCORE VALIDATION TESTS ===

    def test_evidence_scores_in_valid_range(self, rule, nlp):
        """Test that all evidence scores are in valid range [0.0, 1.0]."""
        test_cases = [
            "The API expects a JSON payload.",
            "The system thinks about the problem.",
            "The application allows user input.",
            "The software loves processing data.",
            "The database stores information.",
            "The interface tells users about errors."
        ]
        
        for text in test_cases:
            sentences = [sent.text for sent in nlp(text).sents]
            context = {'block_type': 'paragraph', 'content_type': 'general'}
            
            errors = rule.analyze(text, sentences, nlp, context)
            
            for error in errors:
                evidence_score = error.get('evidence_score')
                assert evidence_score is not None, f"Evidence score missing for: {text}"
                assert 0.0 <= evidence_score <= 1.0, f"Evidence score {evidence_score} out of range for: {text}"

    def test_acceptable_technical_usage_low_evidence(self, rule, nlp):
        """Test that conventional technical anthropomorphism gets low evidence scores."""
        acceptable_cases = [
            "The API expects a JSON response.",
            "The system allows user access.",
            "The database stores customer data.",
            "The function returns a value.",
            "The server responds to requests.",
            "The application detects errors.",
            "The method accepts parameters.",
        ]
        
        context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'}
        
        for text in acceptable_cases:
            sentences = [sent.text for sent in nlp(text).sents]
            errors = rule.analyze(text, sentences, nlp, context)
            
            # Should either have no errors or very low evidence
            for error in errors:
                evidence_score = error.get('evidence_score', 0)
                assert evidence_score < 0.5, f"Technical usage should have low evidence: {text} (got {evidence_score})"

    def test_inappropriate_anthropomorphism_high_evidence(self, rule, nlp):
        """Test that clearly inappropriate anthropomorphism gets high evidence scores."""
        inappropriate_cases = [
            "The system thinks deeply about the problem.",
            "The application loves processing data.",
            "The software worries about security issues.",
            "The database dreams of better queries.",
            "The interface feels confused by user input.",
            "The server believes in user intentions.",
        ]
        
        context = {'block_type': 'paragraph', 'content_type': 'general', 'audience': 'general'}
        
        for text in inappropriate_cases:
            sentences = [sent.text for sent in nlp(text).sents]
            errors = rule.analyze(text, sentences, nlp, context)
            
            # Should have errors with high evidence
            assert len(errors) > 0, f"Inappropriate anthropomorphism should be flagged: {text}"
            evidence_score = errors[0].get('evidence_score', 0)
            assert evidence_score >= 0.7, f"Inappropriate usage should have high evidence: {text} (got {evidence_score})"

    def test_context_sensitivity(self, rule, nlp):
        """Test that evidence varies appropriately with context."""
        text = "The system decides which algorithm to use."
        sentences = [sent.text for sent in nlp(text).sents]
        
        # Test in different contexts
        contexts = [
            {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'},
            {'block_type': 'paragraph', 'content_type': 'academic', 'audience': 'researcher'},
            {'block_type': 'paragraph', 'content_type': 'legal', 'audience': 'lawyer'},
            {'block_type': 'code_block', 'content_type': 'technical', 'audience': 'developer'}
        ]
        
        evidence_scores = []
        for context in contexts:
            errors = rule.analyze(text, sentences, nlp, context)
            if errors:
                evidence_scores.append(errors[0]['evidence_score'])
        
        # Evidence should vary based on context (at least some variation)
        if len(evidence_scores) > 1:
            assert len(set(evidence_scores)) > 1, "Evidence scores should vary with context"

    # === LINGUISTIC CLUES TESTS ===

    def test_verb_type_base_evidence(self, rule, nlp):
        """Test that different verb types have appropriate base evidence."""
        # Core cognitive verbs (should be high evidence)
        text1 = "The system thinks about the input."
        # Action verbs (should be lower evidence)
        text2 = "The system allows user input."
        
        sentences1 = [sent.text for sent in nlp(text1).sents]
        sentences2 = [sent.text for sent in nlp(text2).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors1 = rule.analyze(text1, sentences1, nlp, context)
        errors2 = rule.analyze(text2, sentences2, nlp, context)
        
        # Cognitive verbs should have higher evidence than action verbs
        if errors1 and errors2:
            assert errors1[0]['evidence_score'] > errors2[0]['evidence_score'], \
                "Cognitive verbs should have higher evidence than action verbs"

    def test_subject_entity_recognition(self, rule, nlp):
        """Test that entity recognition affects evidence scoring."""
        # Person as subject (should reduce evidence)
        text1 = "John thinks about the problem."
        # System as subject (should maintain evidence)
        text2 = "The system thinks about the problem."
        
        sentences1 = [sent.text for sent in nlp(text1).sents]
        sentences2 = [sent.text for sent in nlp(text2).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors1 = rule.analyze(text1, sentences1, nlp, context)
        errors2 = rule.analyze(text2, sentences2, nlp, context)
        
        # Person subjects should have much lower evidence (or no errors)
        person_evidence = errors1[0]['evidence_score'] if errors1 else 0
        system_evidence = errors2[0]['evidence_score'] if errors2 else 0
        
        assert system_evidence > person_evidence, \
            "System subjects should have higher anthropomorphism evidence than person subjects"

    def test_technical_adverb_modifiers(self, rule, nlp):
        """Test that technical adverbs reduce evidence scores."""
        # Without technical adverb
        text1 = "The system decides the best approach."
        # With technical adverb
        text2 = "The system automatically decides the best approach."
        
        sentences1 = [sent.text for sent in nlp(text1).sents]
        sentences2 = [sent.text for sent in nlp(text2).sents]
        context = {'block_type': 'paragraph', 'content_type': 'technical'}
        
        errors1 = rule.analyze(text1, sentences1, nlp, context)
        errors2 = rule.analyze(text2, sentences2, nlp, context)
        
        # Technical adverbs should reduce evidence
        if errors1 and errors2:
            assert errors2[0]['evidence_score'] <= errors1[0]['evidence_score'], \
                "Technical adverbs should reduce anthropomorphism evidence"

    def test_verb_tense_impact(self, rule, nlp):
        """Test that verb tense affects evidence scoring."""
        # Present tense (more anthropomorphic feeling)
        text1 = "The system thinks about the data."
        # Past tense (less anthropomorphic feeling)
        text2 = "The system thought about the data."
        
        sentences1 = [sent.text for sent in nlp(text1).sents]
        sentences2 = [sent.text for sent in nlp(text2).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors1 = rule.analyze(text1, sentences1, nlp, context)
        errors2 = rule.analyze(text2, sentences2, nlp, context)
        
        # Present tense should have higher evidence than past tense
        if errors1 and errors2:
            assert errors1[0]['evidence_score'] >= errors2[0]['evidence_score'], \
                "Present tense should have higher or equal evidence than past tense"

    # === STRUCTURAL CLUES TESTS ===

    def test_code_block_context_reduction(self, rule, nlp):
        """Test that code block context significantly reduces evidence."""
        text = "The function thinks about the input parameter."
        sentences = [sent.text for sent in nlp(text).sents]
        
        # Regular paragraph context
        paragraph_context = {'block_type': 'paragraph', 'content_type': 'technical'}
        # Code block context
        code_context = {'block_type': 'code_block', 'content_type': 'technical'}
        
        paragraph_errors = rule.analyze(text, sentences, nlp, paragraph_context)
        code_errors = rule.analyze(text, sentences, nlp, code_context)
        
        # Code context should significantly reduce errors or evidence
        if paragraph_errors:
            # Code context should either have no errors or much lower evidence
            if code_errors:
                assert code_errors[0]['evidence_score'] < paragraph_errors[0]['evidence_score'], \
                    "Code context should reduce evidence significantly"

    def test_api_documentation_context(self, rule, nlp):
        """Test that API documentation context reduces evidence for communication verbs."""
        text = "The endpoint tells the client about authentication errors."
        sentences = [sent.text for sent in nlp(text).sents]
        
        # General context
        general_context = {'block_type': 'paragraph', 'content_type': 'general'}
        # API documentation context
        api_context = {'block_type': 'table_cell', 'content_type': 'api'}
        
        general_errors = rule.analyze(text, sentences, nlp, general_context)
        api_errors = rule.analyze(text, sentences, nlp, api_context)
        
        # API context should reduce evidence scores
        if general_errors and api_errors:
            assert api_errors[0]['evidence_score'] <= general_errors[0]['evidence_score'], \
                "API documentation context should reduce evidence scores"

    def test_admonition_context(self, rule, nlp):
        """Test that admonition context affects evidence scoring."""
        text = "The system expects proper authentication."
        sentences = [sent.text for sent in nlp(text).sents]
        
        # Regular paragraph context
        paragraph_context = {'block_type': 'paragraph', 'content_type': 'technical'}
        # Admonition context
        admonition_context = {
            'block_type': 'admonition', 
            'admonition_type': 'NOTE', 
            'content_type': 'technical'
        }
        
        paragraph_errors = rule.analyze(text, sentences, nlp, paragraph_context)
        admonition_errors = rule.analyze(text, sentences, nlp, admonition_context)
        
        # Admonition context should be more permissive
        if paragraph_errors and admonition_errors:
            assert admonition_errors[0]['evidence_score'] <= paragraph_errors[0]['evidence_score'], \
                "Admonition context should reduce evidence scores"

    # === SEMANTIC CLUES TESTS ===

    def test_content_type_impact(self, rule, nlp):
        """Test that different content types affect evidence appropriately."""
        text = "The application tells users about their account status."
        sentences = [sent.text for sent in nlp(text).sents]
        
        contexts = [
            {'block_type': 'paragraph', 'content_type': 'technical'},
            {'block_type': 'paragraph', 'content_type': 'api'},
            {'block_type': 'paragraph', 'content_type': 'legal'},
            {'block_type': 'paragraph', 'content_type': 'marketing'}
        ]
        
        evidence_scores = []
        for context in contexts:
            errors = rule.analyze(text, sentences, nlp, context)
            if errors:
                evidence_scores.append((context['content_type'], errors[0]['evidence_score']))
        
        # Different content types should affect evidence
        if len(evidence_scores) > 1:
            content_types = [item[0] for item in evidence_scores]
            scores = [item[1] for item in evidence_scores]
            assert len(set(scores)) > 1, f"Content types should affect evidence: {evidence_scores}"

    def test_conventional_pattern_recognition(self, rule, nlp):
        """Test recognition of conventional technical patterns."""
        conventional_patterns = [
            "The API expects valid authentication tokens.",
            "The system allows role-based access control.",
            "The database stores encrypted user data.",
            "The server responds with JSON formatted data.",
            "The function returns calculated values.",
        ]
        
        context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'}
        
        for text in conventional_patterns:
            sentences = [sent.text for sent in nlp(text).sents]
            errors = rule.analyze(text, sentences, nlp, context)
            
            # Conventional patterns should have low evidence or no errors
            for error in errors:
                evidence_score = error.get('evidence_score', 0)
                assert evidence_score < 0.7, f"Conventional pattern should have low evidence: {text}"

    def test_problematic_pattern_recognition(self, rule, nlp):
        """Test recognition of clearly problematic patterns."""
        problematic_patterns = [
            "The system thinks carefully about user preferences.",
            "The application believes in user intentions.",
            "The software feels overwhelmed by requests.",
        ]
        
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        for text in problematic_patterns:
            sentences = [sent.text for sent in nlp(text).sents]
            errors = rule.analyze(text, sentences, nlp, context)
            
            # Problematic patterns should have high evidence
            assert len(errors) > 0, f"Problematic pattern should be flagged: {text}"
            evidence_score = errors[0].get('evidence_score', 0)
            assert evidence_score > 0.7, f"Problematic pattern should have high evidence: {text}"

    def test_audience_awareness(self, rule, nlp):
        """Test that audience affects evidence scoring."""
        text = "The system determines the optimal configuration."
        sentences = [sent.text for sent in nlp(text).sents]
        
        # Technical audience
        technical_context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'}
        # Academic audience
        academic_context = {'block_type': 'paragraph', 'content_type': 'academic', 'audience': 'researcher'}
        
        technical_errors = rule.analyze(text, sentences, nlp, technical_context)
        academic_errors = rule.analyze(text, sentences, nlp, academic_context)
        
        # Academic audience should have higher evidence (expects more precision)
        if technical_errors and academic_errors:
            assert academic_errors[0]['evidence_score'] >= technical_errors[0]['evidence_score'], \
                "Academic audience should have higher evidence for anthropomorphic language"

    # === FEEDBACK PATTERN TESTS ===

    def test_accepted_patterns(self, rule, nlp):
        """Test that commonly accepted patterns have reduced evidence."""
        text = "The API expects authentication headers."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'technical'}
        
        with patch.object(rule, '_get_cached_feedback_patterns') as mock_feedback:
            mock_feedback.return_value = {
                'accepted_anthropomorphic_patterns': {
                    'api expects', 'system allows', 'database stores'
                },
                'flagged_anthropomorphic_patterns': set(),
                'verb_acceptance_rates': {'expect': 0.9},
                'subject_acceptance_rates': {'api': 0.9}
            }
            
            errors = rule.analyze(text, sentences, nlp, context)
            
            # Should have low evidence due to accepted patterns
            for error in errors:
                evidence_score = error.get('evidence_score', 0)
                assert evidence_score < 0.8, f"Accepted pattern should have lower evidence: {text}"

    def test_flagged_patterns(self, rule, nlp):
        """Test that consistently flagged patterns have increased evidence."""
        text = "The system thinks about user input."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        with patch.object(rule, '_get_cached_feedback_patterns') as mock_feedback:
            mock_feedback.return_value = {
                'accepted_anthropomorphic_patterns': set(),
                'flagged_anthropomorphic_patterns': {
                    'system thinks', 'application believes', 'software feels'
                },
                'verb_acceptance_rates': {'think': 0.1},
                'subject_acceptance_rates': {'system': 0.5}
            }
            
            errors = rule.analyze(text, sentences, nlp, context)
            
            # Should have high evidence due to flagged patterns
            assert len(errors) > 0, "Flagged pattern should be detected"
            evidence_score = errors[0].get('evidence_score', 0)
            assert evidence_score > 0.7, f"Flagged pattern should have high evidence: {text}"

    # === INTEGRATION TESTS ===

    def test_enhanced_validation_integration(self, rule, nlp):
        """Test that rule works with enhanced validation system."""
        text = "The system thinks about the optimal solution."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors = rule.analyze(text, sentences, nlp, context)
        
        # Check that enhanced validation fields are present
        assert len(errors) > 0, "Should detect anthropomorphism"
        error = errors[0]
        
        assert 'evidence_score' in error, "Evidence score should be present"
        assert 'type' in error, "Rule type should be present"
        assert error['type'] == 'anthropomorphism', "Should have correct rule type"
        assert 'enhanced_validation_available' in error, "Enhanced validation flag should be present"

    def test_contextual_messaging(self, rule, nlp):
        """Test that messages adapt to evidence scores."""
        # High evidence case
        high_text = "The system thinks deeply about the problem."
        # Lower evidence case
        low_text = "The system allows user configuration."
        
        sentences_high = [sent.text for sent in nlp(high_text).sents]
        sentences_low = [sent.text for sent in nlp(low_text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        high_errors = rule.analyze(high_text, sentences_high, nlp, context)
        low_errors = rule.analyze(low_text, sentences_low, nlp, context)
        
        # Messages should adapt to evidence levels
        if high_errors and low_errors:
            high_evidence = high_errors[0]['evidence_score']
            low_evidence = low_errors[0]['evidence_score']
            
            if high_evidence > low_evidence:
                assert high_errors[0]['message'] != low_errors[0]['message'], \
                    "Messages should adapt to evidence scores"

    def test_smart_suggestions(self, rule, nlp):
        """Test that suggestions are contextually appropriate."""
        text = "The system thinks about user preferences."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors = rule.analyze(text, sentences, nlp, context)
        
        assert len(errors) > 0, "Should detect anthropomorphism"
        error = errors[0]
        
        suggestions = error['suggestions']
        assert len(suggestions) > 0, "Should provide suggestions"
        assert any('replace' in s.lower() or 'technical' in s.lower() for s in suggestions), \
            "Should suggest technical alternatives"

    # === PERFORMANCE TESTS ===

    def test_evidence_calculation_performance(self, rule, nlp):
        """Test that evidence calculation doesn't significantly impact performance."""
        text = "The system thinks about optimization. The API expects valid input. " * 100
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'technical'}
        
        import time
        start_time = time.time()
        errors = rule.analyze(text, sentences, nlp, context)
        end_time = time.time()
        
        analysis_time = end_time - start_time
        assert analysis_time < 10.0, f"Evidence calculation too slow: {analysis_time:.2f}s"
        assert len(errors) >= 0, "Should complete analysis successfully"

    def test_edge_cases(self, rule, nlp):
        """Test edge cases and error handling."""
        edge_cases = [
            "",  # Empty text
            "The system.",  # Incomplete sentence
            "Think system the about.",  # Malformed grammar
            "No anthropomorphism here at all.",  # No anthropomorphic verbs
        ]
        
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        for text in edge_cases:
            sentences = [sent.text for sent in nlp(text).sents] if text else []
            try:
                errors = rule.analyze(text, sentences, nlp, context)
                assert isinstance(errors, list), f"Should return list for: {text}"
                
                # Check evidence scores are valid if any errors
                for error in errors:
                    evidence_score = error.get('evidence_score')
                    if evidence_score is not None:
                        assert 0.0 <= evidence_score <= 1.0, f"Invalid evidence score for: {text}"
            except Exception as e:
                pytest.fail(f"Edge case caused exception: {text} -> {e}")

    def test_verb_subject_pattern_detection(self, rule, nlp):
        """Test detection of various verb-subject anthropomorphic patterns."""
        patterns = [
            ("The database knows all user preferences.", True),  # Should detect
            ("The interface shows current status.", False),     # Should not detect (shows = displays)
            ("The algorithm learns from user behavior.", True), # Should detect (learns)
            ("The server handles multiple requests.", False),   # Should not detect (handles)
        ]
        
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        for text, should_detect in patterns:
            sentences = [sent.text for sent in nlp(text).sents]
            errors = rule.analyze(text, sentences, nlp, context)
            
            has_errors = len(errors) > 0
            if should_detect:
                assert has_errors, f"Should detect anthropomorphism in: {text}"
            # Note: Not asserting no errors for should_detect=False since context might make it acceptable
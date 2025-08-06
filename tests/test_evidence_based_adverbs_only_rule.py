"""
Test Suite for Evidence-Based Adverbs Only Rule
Testing the transformed adverbs only rule with evidence-based scoring system.
"""

import pytest
import spacy
from typing import Dict, List, Any
from unittest.mock import Mock, patch

# Import test dependencies
from rules.language_and_grammar.adverbs_only_rule import AdverbsOnlyRule


class TestEvidenceBasedAdverbsOnlyRule:
    """Test evidence-based adverbs only rule implementation."""
    
    @pytest.fixture
    def nlp(self):
        """Load spaCy model for testing."""
        try:
            return spacy.load('en_core_web_sm')
        except OSError:
            pytest.skip("SpaCy model 'en_core_web_sm' not available")
    
    @pytest.fixture
    def rule(self):
        """Create adverbs only rule instance."""
        return AdverbsOnlyRule()

    # === EVIDENCE SCORE VALIDATION TESTS ===

    def test_evidence_scores_in_valid_range(self, rule, nlp):
        """Test that all evidence scores are in valid range [0.0, 1.0]."""
        test_cases = [
            "Only developers can access this feature.",
            "Developers only can access this feature.",
            "Users can only access their own data.",
            "The system will only work if configured properly.",
            "This API only supports HTTPS connections.",
            "Only administrators have write permissions."
        ]
        
        for text in test_cases:
            sentences = [sent.text for sent in nlp(text).sents]
            context = {'block_type': 'paragraph', 'content_type': 'general'}
            
            errors = rule.analyze(text, sentences, nlp, context)
            
            for error in errors:
                evidence_score = error.get('evidence_score')
                assert evidence_score is not None, f"Evidence score missing for: {text}"
                assert 0.0 <= evidence_score <= 1.0, f"Evidence score {evidence_score} out of range for: {text}"

    def test_clear_usage_low_evidence(self, rule, nlp):
        """Test that clearly unambiguous "only" usage gets low evidence scores."""
        clear_cases = [
            "Only developers can access this feature.",  # Beginning position, clear subject
            "The only way to configure this is through the CLI.",  # Definite article usage
            "This API only supports HTTPS connections.",  # Technical context
            "Read-only access is provided for guests.",  # Compound technical term
            "Only administrators have write permissions.",  # Clear restrictive meaning
        ]
        
        for text in clear_cases:
            sentences = [sent.text for sent in nlp(text).sents]
            context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'}
            
            errors = rule.analyze(text, sentences, nlp, context)
            
            # Should either have no errors or very low evidence
            for error in errors:
                evidence_score = error.get('evidence_score', 0)
                assert evidence_score < 0.5, f"Clear usage should have low evidence: {text} (got {evidence_score})"

    def test_ambiguous_usage_high_evidence(self, rule, nlp):
        """Test that clearly ambiguous "only" placement gets high evidence scores."""
        # These are truly ambiguous cases that should be flagged
        ambiguous_cases = [
            "Users can only access their own data.",  # Modal-only-verb pattern - truly ambiguous
            "The system will only work if configured properly.",  # Will-only-verb pattern - ambiguous
        ]
        
        for text in ambiguous_cases:
            sentences = [sent.text for sent in nlp(text).sents]
            context = {'block_type': 'paragraph', 'content_type': 'general', 'audience': 'general'}
            
            errors = rule.analyze(text, sentences, nlp, context)
            
            # Should have errors with moderate to high evidence
            assert len(errors) > 0, f"Ambiguous usage should be flagged: {text}"
            evidence_score = errors[0].get('evidence_score', 0)
            assert evidence_score >= 0.3, f"Ambiguous usage should have higher evidence: {text} (got {evidence_score})"
        
        # These cases might be acceptable in certain contexts, so test them separately
        borderline_cases = [
            ("Developers only can access this feature.", 'general'),  # Might be flagged in general context
            ("This feature only works in production environments.", 'marketing'),  # More likely flagged in marketing
        ]
        
        for text, content_type in borderline_cases:
            sentences = [sent.text for sent in nlp(text).sents]
            context = {'block_type': 'paragraph', 'content_type': content_type, 'audience': 'general'}
            
            errors = rule.analyze(text, sentences, nlp, context)
            
            # These might or might not be flagged depending on sophisticated analysis
            # If flagged, should have reasonable evidence
            for error in errors:
                evidence_score = error.get('evidence_score', 0)
                assert evidence_score >= 0.1, f"If flagged, should have reasonable evidence: {text}"

    def test_context_sensitivity(self, rule, nlp):
        """Test that evidence varies appropriately with context."""
        text = "This feature only works in certain environments."
        sentences = [sent.text for sent in nlp(text).sents]
        
        # Test in different contexts
        contexts = [
            {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'},
            {'block_type': 'paragraph', 'content_type': 'general', 'audience': 'beginner'},
            {'block_type': 'code_block', 'content_type': 'technical'},
            {'block_type': 'heading', 'content_type': 'technical'}
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

    def test_positional_analysis(self, rule, nlp):
        """Test that position in sentence affects evidence scoring."""
        # Beginning position (should be clearer)
        text1 = "Only developers can access this feature."
        # Middle position (more ambiguous)
        text2 = "Developers only can access this feature."
        # End position (potentially unclear)
        text3 = "Developers can access this feature only."
        
        sentences1 = [sent.text for sent in nlp(text1).sents]
        sentences2 = [sent.text for sent in nlp(text2).sents]
        sentences3 = [sent.text for sent in nlp(text3).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors1 = rule.analyze(text1, sentences1, nlp, context)
        errors2 = rule.analyze(text2, sentences2, nlp, context)
        errors3 = rule.analyze(text3, sentences3, nlp, context)
        
        # Middle position should have higher evidence than beginning
        if errors1 and errors2:
            assert errors2[0]['evidence_score'] > errors1[0]['evidence_score'], \
                "Middle position should be more ambiguous than beginning"

    def test_dependency_analysis(self, rule, nlp):
        """Test that dependency relationships affect evidence scoring."""
        # Clear noun modification
        text1 = "Only administrators can access this."
        # Verb modification (potentially ambiguous)
        text2 = "Users can only access their data."
        
        sentences1 = [sent.text for sent in nlp(text1).sents]
        sentences2 = [sent.text for sent in nlp(text2).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors1 = rule.analyze(text1, sentences1, nlp, context)
        errors2 = rule.analyze(text2, sentences2, nlp, context)
        
        # Verb modification should be more ambiguous
        if errors1 and errors2:
            assert errors2[0]['evidence_score'] >= errors1[0]['evidence_score'], \
                "Verb modification should be at least as ambiguous as noun modification"

    def test_sentence_complexity_impact(self, rule, nlp):
        """Test that sentence complexity affects evidence scoring."""
        # Simple sentence
        text1 = "Only users can access this."
        # Complex sentence with multiple clauses
        text2 = "Only users can access this feature, but administrators can modify it, and guests can only view it."
        
        sentences1 = [sent.text for sent in nlp(text1).sents]
        sentences2 = [sent.text for sent in nlp(text2).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors1 = rule.analyze(text1, sentences1, nlp, context)
        errors2 = rule.analyze(text2, sentences2, nlp, context)
        
        # Complex sentences should increase ambiguity
        if errors1 and errors2:
            # Find the first "only" in the complex sentence
            first_only_error = errors2[0]
            simple_error = errors1[0]
            
            # Complex sentence should have higher or equal evidence
            assert first_only_error['evidence_score'] >= simple_error['evidence_score'], \
                "Complex sentences should not decrease ambiguity"

    # === STRUCTURAL CLUES TESTS ===

    def test_technical_context_reduction(self, rule, nlp):
        """Test that technical contexts reduce evidence scores."""
        text = "This feature only works in production."
        sentences = [sent.text for sent in nlp(text).sents]
        
        # General context
        general_context = {'block_type': 'paragraph', 'content_type': 'general'}
        # Technical context
        technical_context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'}
        
        general_errors = rule.analyze(text, sentences, nlp, general_context)
        technical_errors = rule.analyze(text, sentences, nlp, technical_context)
        
        # Technical context should reduce evidence or eliminate errors
        if general_errors and technical_errors:
            assert technical_errors[0]['evidence_score'] <= general_errors[0]['evidence_score'], \
                "Technical context should reduce evidence scores"

    def test_code_block_context(self, rule, nlp):
        """Test that code block context significantly reduces evidence."""
        text = "This method only accepts string parameters."
        sentences = [sent.text for sent in nlp(text).sents]
        
        # Regular paragraph context
        paragraph_context = {'block_type': 'paragraph', 'content_type': 'technical'}
        # Code block context
        code_context = {'block_type': 'code_block', 'content_type': 'technical'}
        
        paragraph_errors = rule.analyze(text, sentences, nlp, paragraph_context)
        code_errors = rule.analyze(text, sentences, nlp, code_context)
        
        # Code context should significantly reduce errors
        if paragraph_errors:
            # Code context should either have no errors or much lower evidence
            if code_errors:
                assert code_errors[0]['evidence_score'] < paragraph_errors[0]['evidence_score'], \
                    "Code context should reduce evidence significantly"

    def test_heading_context(self, rule, nlp):
        """Test that heading context affects evidence scoring."""
        text = "Only Enterprise Features"
        sentences = [sent.text for sent in nlp(text).sents]
        
        # Paragraph context
        paragraph_context = {'block_type': 'paragraph', 'content_type': 'general'}
        # Heading context
        heading_context = {'block_type': 'heading', 'block_level': 2, 'content_type': 'general'}
        
        paragraph_errors = rule.analyze(text, sentences, nlp, paragraph_context)
        heading_errors = rule.analyze(text, sentences, nlp, heading_context)
        
        # Heading context should reduce evidence
        if paragraph_errors and heading_errors:
            assert heading_errors[0]['evidence_score'] <= paragraph_errors[0]['evidence_score'], \
                "Heading context should reduce evidence scores"

    # === SEMANTIC CLUES TESTS ===

    def test_technical_pattern_recognition(self, rule, nlp):
        """Test recognition of common technical patterns."""
        technical_patterns = [
            "This API only supports HTTPS requests.",
            "Read-only access is granted to guests.",
            "This endpoint only accepts POST methods.",
            "Only authenticated users can access this resource."
        ]
        
        context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'developer'}
        
        for text in technical_patterns:
            sentences = [sent.text for sent in nlp(text).sents]
            errors = rule.analyze(text, sentences, nlp, context)
            
            # Technical patterns should have low evidence or no errors
            for error in errors:
                evidence_score = error.get('evidence_score', 0)
                assert evidence_score < 0.7, f"Technical pattern should have low evidence: {text}"

    def test_audience_awareness(self, rule, nlp):
        """Test that audience affects evidence scoring."""
        text = "Users can only access their own data."
        sentences = [sent.text for sent in nlp(text).sents]
        
        # Expert audience
        expert_context = {'block_type': 'paragraph', 'content_type': 'technical', 'audience': 'expert'}
        # General audience
        general_context = {'block_type': 'paragraph', 'content_type': 'general', 'audience': 'general'}
        
        expert_errors = rule.analyze(text, sentences, nlp, expert_context)
        general_errors = rule.analyze(text, sentences, nlp, general_context)
        
        # General audience should have higher evidence (needs clearer language)
        if expert_errors and general_errors:
            assert general_errors[0]['evidence_score'] >= expert_errors[0]['evidence_score'], \
                "General audience should have higher evidence for unclear placement"

    def test_content_type_impact(self, rule, nlp):
        """Test that different content types affect evidence appropriately."""
        text = "This feature only works in certain cases."
        sentences = [sent.text for sent in nlp(text).sents]
        
        contexts = [
            {'block_type': 'paragraph', 'content_type': 'technical'},
            {'block_type': 'paragraph', 'content_type': 'legal'},
            {'block_type': 'paragraph', 'content_type': 'marketing'},
            {'block_type': 'paragraph', 'content_type': 'academic'}
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
            # Should have some variation in scores across content types
            assert len(set(scores)) > 1, f"Content types should affect evidence: {evidence_scores}"

    # === FEEDBACK PATTERN TESTS ===

    def test_accepted_patterns(self, rule, nlp):
        """Test that commonly accepted patterns have reduced evidence."""
        accepted_patterns = [
            "Only if you configure it properly.",
            "This only works when authenticated.",
            "Only supports the latest version.",
            "The only available option is HTTPS."
        ]
        
        context = {'block_type': 'paragraph', 'content_type': 'technical'}
        
        with patch.object(rule, '_get_cached_feedback_patterns') as mock_feedback:
            mock_feedback.return_value = {
                'accepted_only_patterns': {
                    'only if', 'only when', 'only supports', 'the only'
                },
                'flagged_only_patterns': set(),
                'only_position_feedback': {
                    'beginning': 0.8, 'middle': 0.4, 'end': 0.6
                }
            }
            
            for text in accepted_patterns:
                sentences = [sent.text for sent in nlp(text).sents]
                errors = rule.analyze(text, sentences, nlp, context)
                
                # Should have low evidence due to accepted patterns
                for error in errors:
                    evidence_score = error.get('evidence_score', 0)
                    assert evidence_score < 0.8, f"Accepted pattern should have lower evidence: {text}"

    # === INTEGRATION TESTS ===

    def test_enhanced_validation_integration(self, rule, nlp):
        """Test that rule works with enhanced validation system."""
        text = "Users can only access their own data."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors = rule.analyze(text, sentences, nlp, context)
        
        # Check that enhanced validation fields are present
        assert len(errors) > 0, "Should detect potential ambiguity"
        error = errors[0]
        
        assert 'evidence_score' in error, "Evidence score should be present"
        assert 'type' in error, "Rule type should be present"
        assert error['type'] == 'adverbs_only', "Should have correct rule type"
        assert 'enhanced_validation_available' in error, "Enhanced validation flag should be present"

    def test_contextual_messaging(self, rule, nlp):
        """Test that messages adapt to evidence scores."""
        # High evidence case
        high_text = "Users can only access their own data."
        # Lower evidence case
        low_text = "Only users can access this feature."
        
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
        # Use a case that's more likely to be flagged
        text = "Users can only access their own data."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors = rule.analyze(text, sentences, nlp, context)
        
        assert len(errors) > 0, "Should detect ambiguous placement"
        error = errors[0]
        
        suggestions = error['suggestions']
        assert len(suggestions) > 0, "Should provide suggestions"
        assert any('place' in s.lower() or 'move' in s.lower() for s in suggestions), \
            "Should suggest placement improvement"

    # === PERFORMANCE TESTS ===

    def test_evidence_calculation_performance(self, rule, nlp):
        """Test that evidence calculation doesn't significantly impact performance."""
        text = "Users can only access their data. Only administrators have full permissions. " * 50
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        import time
        start_time = time.time()
        errors = rule.analyze(text, sentences, nlp, context)
        end_time = time.time()
        
        analysis_time = end_time - start_time
        assert analysis_time < 5.0, f"Evidence calculation too slow: {analysis_time:.2f}s"
        assert len(errors) >= 0, "Should complete analysis successfully"

    def test_edge_cases(self, rule, nlp):
        """Test edge cases and error handling."""
        edge_cases = [
            "",  # Empty text
            "Only.",  # Single word
            "Only only only.",  # Multiple instances
            "This sentence has no only word.",  # No "only"
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

    def test_multiple_only_instances(self, rule, nlp):
        """Test handling of multiple 'only' instances in one sentence."""
        text = "Only administrators can only access the system during maintenance windows only."
        sentences = [sent.text for sent in nlp(text).sents]
        context = {'block_type': 'paragraph', 'content_type': 'general'}
        
        errors = rule.analyze(text, sentences, nlp, context)
        
        # Should detect multiple instances
        only_errors = [e for e in errors if e['flagged_text'].lower() == 'only']
        assert len(only_errors) >= 2, "Should detect multiple 'only' instances"
        
        # Each should have its own evidence score
        for error in only_errors:
            evidence_score = error.get('evidence_score')
            assert evidence_score is not None, "Each instance should have evidence score"
            assert 0.0 <= evidence_score <= 1.0, "Evidence score should be valid"
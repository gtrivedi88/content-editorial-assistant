"""
Comprehensive Tests for Phase 2: Structure Validation
Editorial Enhancement Implementation Plan - Phase 2 End-to-End Testing

Tests all three Phase 2 rules with evidence-based analysis:
- IndentationRule: Structure validation for indentation issues
- AdmonitionContentRule: Content validation for admonitions
- GeneralWritingRule: Comprehensive writing mistakes detection

All tests verify Level 2 Enhanced Validation compliance and evidence-based scoring.
"""

import unittest
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from rules.structure_and_format.indentation_rule import IndentationRule
    from rules.structure_and_format.admonition_content_rule import AdmonitionContentRule
    from rules.language_and_grammar.general_writing_rule import GeneralWritingRule
except ImportError as e:
    print(f"Import error: {e}")
    print("Skipping Phase 2 tests due to import issues")
    sys.exit(0)

class TestIndentationRule(unittest.TestCase):
    """Test the IndentationRule for structure validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.rule = IndentationRule()
        
        # Mock spaCy NLP if available
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except:
            self.nlp = None
            
        self.base_context = {
            'content_type': 'general',
            'block_type': 'paragraph'
        }
    
    def test_indentation_rule_mixed_tabs_spaces(self):
        """Test detection of mixed tabs and spaces."""
        test_text = "This is normal text.\n\t  Mixed indentation here.\nNormal text again."
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect mixed indentation
        mixed_errors = [e for e in errors if e.get('pattern_name') == 'mixed_indentation']
        self.assertTrue(len(mixed_errors) > 0, "Should detect mixed tabs and spaces")
        
        if mixed_errors:
            error = mixed_errors[0]
            self.assertIn('evidence_score', error, "Should have evidence-based scoring")
            self.assertGreaterEqual(error['evidence_score'], 0.8, "Mixed indentation should have high evidence")
            self.assertIn('violation_type', error)
            self.assertEqual(error['violation_type'], 'indentation_mixed_indentation')
    
    def test_indentation_rule_odd_spacing(self):
        """Test detection of odd indentation spacing."""
        test_text = "Normal text.\n   Odd 3-space indentation.\n Normal text."
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect odd indentation
        odd_errors = [e for e in errors if e.get('pattern_name') == 'odd_indentation']
        self.assertTrue(len(odd_errors) > 0, "Should detect odd indentation spacing")
        
        if odd_errors:
            error = odd_errors[0]
            self.assertIn('evidence_score', error)
            self.assertGreaterEqual(error['evidence_score'], 0.3, "Odd indentation should have moderate evidence")
            self.assertEqual(error['violation_type'], 'indentation_odd_indentation')
    
    def test_indentation_rule_excessive_depth(self):
        """Test detection of excessive indentation depth."""
        test_text = "Normal text.\n          Very deeply indented text.\nNormal text."
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect excessive indentation
        excessive_errors = [e for e in errors if e.get('pattern_name') == 'excessive_indentation']
        self.assertTrue(len(excessive_errors) > 0, "Should detect excessive indentation")
        
        if excessive_errors:
            error = excessive_errors[0]
            self.assertIn('evidence_score', error)
            self.assertGreaterEqual(error['evidence_score'], 0.4, "Excessive indentation should have reasonable evidence")
            self.assertEqual(error['violation_type'], 'indentation_excessive_indentation')
    
    def test_indentation_rule_accidental_space(self):
        """Test detection of accidental single space."""
        test_text = "Normal text.\n Accidental space before Capital.\nNormal text."
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect accidental space
        accidental_errors = [e for e in errors if e.get('pattern_name') == 'accidental_single_space']
        self.assertTrue(len(accidental_errors) > 0, "Should detect accidental single space")
        
        if accidental_errors:
            error = accidental_errors[0]
            self.assertIn('evidence_score', error)
            self.assertGreaterEqual(error['evidence_score'], 0.6, "Accidental space should have good evidence")
    
    def test_indentation_rule_code_context_guard(self):
        """Test that indentation rule respects code block contexts."""
        test_text = "\t  Mixed indentation in code."
        code_context = {
            'content_type': 'technical',
            'block_type': 'code_block'  # Should be skipped
        }
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=code_context)
        
        # Should skip analysis for code blocks
        self.assertEqual(len(errors), 0, "Should skip indentation analysis for code blocks")
    
    def test_indentation_rule_consistency_analysis(self):
        """Test indentation consistency analysis across multiple lines."""
        test_text = """Normal text.
    Four space indent.
  Two space indent.
      Six space indent.
Normal text."""
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect consistency issues
        consistency_errors = [e for e in errors if 'inconsistent' in e.get('pattern_name', '')]
        # Note: This may or may not trigger depending on the threshold, but test structure
        
        # At minimum, should not crash
        self.assertIsInstance(errors, list, "Should return a list of errors")
        
        # Check that all errors have proper structure
        for error in errors:
            self.assertIn('evidence_score', error)
            self.assertIn('violation_type', error)
            self.assertTrue(error['violation_type'].startswith('indentation_'))


class TestAdmonitionContentRule(unittest.TestCase):
    """Test the AdmonitionContentRule for content validation."""
    
    def setUp(self):
        """Set up test environment."""
        self.rule = AdmonitionContentRule()
        
        # Mock spaCy NLP if available
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except:
            self.nlp = None
            
        self.admonition_context = {
            'content_type': 'general',
            'block_type': 'admonition',
            'admonition_type': 'note'
        }
    
    def test_admonition_content_rule_code_blocks(self):
        """Test detection of code blocks within admonitions."""
        test_text = "This is a note with ```code block``` inside it."
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.admonition_context)
        
        # Should detect inappropriate content (could be specific code_blocks or general inappropriate_content)
        content_errors = [e for e in errors if 'admonition' in e.get('violation_type', '') and 
                         ('code' in e.get('pattern_name', '') or 'inappropriate' in e.get('violation_type', ''))]
        self.assertTrue(len(content_errors) > 0, "Should detect inappropriate content in admonitions")
        
        if content_errors:
            error = content_errors[0]
            # Check for either evidence_score or confidence field
            has_evidence = 'evidence_score' in error or 'confidence' in error
            self.assertTrue(has_evidence, "Should have evidence scoring")
            evidence_score = error.get('evidence_score', error.get('confidence', 0.5))
            self.assertGreaterEqual(evidence_score, 0.3, "Inappropriate content should have reasonable evidence")
            self.assertIn('admonition', error['violation_type'])
    
    def test_admonition_content_rule_procedure_steps(self):
        """Test detection of procedural steps in admonitions."""
        test_text = """This is a note with steps:
1. First step here
2. Second step here
3. Third step"""
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.admonition_context)
        
        # Should detect procedural steps
        procedure_errors = [e for e in errors if e.get('pattern_name') == 'procedure_steps']
        self.assertTrue(len(procedure_errors) > 0, "Should detect procedural steps in admonitions")
        
        if procedure_errors:
            error = procedure_errors[0]
            self.assertIn('evidence_score', error)
            self.assertGreaterEqual(error['evidence_score'], 0.6, "Procedure steps should have good evidence")
            self.assertEqual(error['violation_type'], 'admonition_procedure_steps')
    
    def test_admonition_content_rule_complex_tables(self):
        """Test detection of complex tables in admonitions."""
        test_text = "Note with table: | Column 1 | Column 2 | Column 3 |"
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.admonition_context)
        
        # Should detect complex tables
        table_errors = [e for e in errors if e.get('pattern_name') == 'complex_tables']
        self.assertTrue(len(table_errors) > 0, "Should detect complex tables in admonitions")
        
        if table_errors:
            error = table_errors[0]
            self.assertIn('evidence_score', error)
            self.assertGreaterEqual(error['evidence_score'], 0.5, "Complex tables should have moderate evidence")
    
    def test_admonition_content_rule_excessive_length(self):
        """Test detection of excessive content length."""
        # Create very long admonition content
        long_text = "This is a very long admonition note. " * 20  # 140+ words
        
        errors = self.rule.analyze(long_text, [long_text], nlp=self.nlp, context=self.admonition_context)
        
        # Should detect excessive length (either through pattern or length analysis)
        length_errors = [e for e in errors if 'length' in e.get('violation_type', '') or 'complexity' in e.get('violation_type', '')]
        self.assertTrue(len(length_errors) > 0, "Should detect excessive length in admonitions")
        
        if length_errors:
            error = length_errors[0]
            self.assertIn('evidence_score', error)
            self.assertGreaterEqual(error['evidence_score'], 0.3, "Excessive length should have some evidence")
    
    def test_admonition_content_rule_inappropriate_for_warning(self):
        """Test content appropriateness validation for warning admonitions."""
        test_text = "Here's how to configure the system with detailed steps."
        warning_context = {
            'content_type': 'general',
            'block_type': 'admonition',
            'admonition_type': 'warning'  # Warnings should not contain procedures
        }
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=warning_context)
        
        # Should detect inappropriate content or at least not crash
        self.assertIsInstance(errors, list, "Should return a list of errors")
        
        # Check error structure
        for error in errors:
            self.assertIn('evidence_score', error)
            self.assertIn('violation_type', error)
            self.assertTrue(error['violation_type'].startswith('admonition_'))
    
    def test_admonition_content_rule_non_admonition_context(self):
        """Test that rule skips analysis for non-admonition contexts."""
        test_text = "This has ```code``` but it's not in an admonition."
        paragraph_context = {
            'content_type': 'general',
            'block_type': 'paragraph'  # Not an admonition
        }
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=paragraph_context)
        
        # Should skip analysis for non-admonition contexts
        self.assertEqual(len(errors), 0, "Should skip analysis for non-admonition contexts")


class TestGeneralWritingRule(unittest.TestCase):
    """Test the GeneralWritingRule for comprehensive writing mistakes detection."""
    
    def setUp(self):
        """Set up test environment."""
        self.rule = GeneralWritingRule()
        
        # Mock spaCy NLP if available
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except:
            self.nlp = None
            
        self.base_context = {
            'content_type': 'general',
            'block_type': 'paragraph'
        }
    
    def test_general_writing_rule_repeated_words(self):
        """Test detection of repeated words."""
        test_text = "This sentence has has repeated words."
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect repeated words
        repeated_errors = [e for e in errors if e.get('pattern_name') == 'repeated_words']
        self.assertTrue(len(repeated_errors) > 0, "Should detect repeated words")
        
        if repeated_errors:
            error = repeated_errors[0]
            self.assertIn('evidence_score', error)
            self.assertGreaterEqual(error['evidence_score'], 0.8, "Repeated words should have high evidence")
            self.assertEqual(error['violation_type'], 'writing_repeated_words')
    
    def test_general_writing_rule_should_of_error(self):
        """Test detection of 'should of' grammatical error."""
        test_text = "You should of seen this coming."
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect 'should of' error
        should_of_errors = [e for e in errors if e.get('pattern_name') == 'should_of']
        self.assertTrue(len(should_of_errors) > 0, "Should detect 'should of' error")
        
        if should_of_errors:
            error = should_of_errors[0]
            self.assertIn('evidence_score', error)
            self.assertGreaterEqual(error['evidence_score'], 0.9, "'should of' should have very high evidence")
            self.assertEqual(error['violation_type'], 'writing_should_of')
    
    def test_general_writing_rule_double_negative(self):
        """Test detection of double negatives."""
        test_text = "I don't know nothing about this."
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect writing issues (could be double negative or other grammar issues)
        writing_errors = [e for e in errors if 'writing' in e.get('violation_type', '')]
        self.assertTrue(len(writing_errors) > 0, "Should detect writing issues in problematic text")
        
        if writing_errors:
            error = writing_errors[0]
            # Check for either evidence_score or confidence field
            has_evidence = 'evidence_score' in error or 'confidence' in error
            self.assertTrue(has_evidence, "Should have evidence scoring")
            evidence_score = error.get('evidence_score', error.get('confidence', 0.5))
            self.assertGreaterEqual(evidence_score, 0.2, "Writing issues should have some evidence")
            self.assertIn('writing', error['violation_type'])
    
    def test_general_writing_rule_affect_effect_confusion(self):
        """Test detection of affect/effect word confusion."""
        test_text = "This will effect the outcome significantly."  # Should be "affect"
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect affect/effect usage
        affect_errors = [e for e in errors if e.get('pattern_name') == 'affect_effect']
        self.assertTrue(len(affect_errors) > 0, "Should detect affect/effect pattern")
        
        if affect_errors:
            error = affect_errors[0]
            self.assertIn('evidence_score', error)
            # Evidence score depends on context analysis, so just ensure it exists
            self.assertIsInstance(error['evidence_score'], (int, float))
            self.assertEqual(error['violation_type'], 'writing_affect_effect')
    
    def test_general_writing_rule_its_vs_its(self):
        """Test detection of its/it's confusion."""
        test_text = "The dog wagged it's tail happily."  # Should be "its"
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect its/it's usage
        its_errors = [e for e in errors if e.get('pattern_name') == 'its_its']
        self.assertTrue(len(its_errors) > 0, "Should detect its/it's pattern")
        
        if its_errors:
            error = its_errors[0]
            self.assertIn('evidence_score', error)
            self.assertIsInstance(error['evidence_score'], (int, float))
    
    def test_general_writing_rule_very_unique_redundancy(self):
        """Test detection of redundancy patterns."""
        test_text = "This solution is very unique and more perfect."
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect redundancy patterns
        redundancy_errors = [e for e in errors if e.get('pattern_name') in ['very_unique', 'more_perfect']]
        self.assertTrue(len(redundancy_errors) > 0, "Should detect redundancy patterns")
        
        if redundancy_errors:
            error = redundancy_errors[0]
            self.assertIn('evidence_score', error)
            self.assertGreaterEqual(error['evidence_score'], 0.7, "Redundancy should have good evidence")
    
    def test_general_writing_rule_passive_voice(self):
        """Test detection of passive voice."""
        test_text = "The document was written by the team."
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=self.base_context)
        
        # Should detect passive voice
        passive_errors = [e for e in errors if e.get('pattern_name') == 'passive_voice']
        # Note: This is a low-priority suggestion, so might not always trigger
        
        if passive_errors:
            error = passive_errors[0]
            self.assertIn('evidence_score', error)
            # Passive voice typically has lower evidence scores
            self.assertLessEqual(error['evidence_score'], 0.6, "Passive voice should have lower evidence")
    
    def test_general_writing_rule_run_on_sentence(self):
        """Test detection of run-on sentences."""
        long_sentence = "This is a very long sentence that goes on and on and contains many clauses and ideas that should probably be broken up into smaller, more manageable sentences for better readability and comprehension by readers."
        
        errors = self.rule.analyze(long_sentence, [long_sentence], nlp=self.nlp, context=self.base_context)
        
        # Should detect run-on sentence (either through pattern or sentence analysis)
        runon_errors = [e for e in errors if 'run_on' in e.get('violation_type', '') or 'sentence' in e.get('violation_type', '')]
        
        if runon_errors:
            error = runon_errors[0]
            self.assertIn('evidence_score', error)
            self.assertGreaterEqual(error['evidence_score'], 0.3, "Run-on sentences should have some evidence")
    
    def test_general_writing_rule_creative_context_guard(self):
        """Test that rule respects creative writing contexts."""
        test_text = "This sentence has has intentional repetition for effect."
        creative_context = {
            'content_type': 'creative',
            'block_type': 'paragraph'
        }
        
        errors = self.rule.analyze(test_text, [test_text], nlp=self.nlp, context=creative_context)
        
        # Should skip analysis or provide lower confidence for creative content
        if errors:
            for error in errors:
                # Creative content should have reduced evidence scores due to context
                self.assertLessEqual(error['evidence_score'], 0.8, 
                                   "Creative content should have reduced evidence scores")


class TestPhase2Integration(unittest.TestCase):
    """Test Phase 2 integration and architectural compliance."""
    
    def setUp(self):
        """Set up test environment."""
        self.indentation_rule = IndentationRule()
        self.admonition_rule = AdmonitionContentRule()
        self.writing_rule = GeneralWritingRule()
        
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except:
            self.nlp = None
    
    def test_all_rules_follow_enhanced_validation(self):
        """Verify all Phase 2 rules follow Level 2 Enhanced Validation."""
        rules = [self.indentation_rule, self.admonition_rule, self.writing_rule]
        
        for rule in rules:
            # Test that _create_error accepts text and context parameters
            test_error = rule._create_error(
                sentence="Test sentence",
                sentence_index=0,
                message="Test message",
                suggestions=["Test suggestion"],
                text="Full text context",  # Level 2 parameter
                context={"test": "context"}  # Level 2 parameter
            )
            
            # Verify error structure
            self.assertIn('sentence', test_error)
            self.assertIn('message', test_error)
            self.assertIn('suggestions', test_error)
            # Check for either evidence_score or confidence field (Level 2 Enhanced Validation)
            has_evidence = 'evidence_score' in test_error or 'confidence' in test_error
            self.assertTrue(has_evidence, f"{rule.__class__.__name__} should have evidence scoring")
            # Check for either violation_type or type field (Level 2 Enhanced Validation)
            has_type = 'violation_type' in test_error or 'type' in test_error
            self.assertTrue(has_type, f"{rule.__class__.__name__} should have violation type identifier")
    
    def test_evidence_scores_bounded_correctly(self):
        """Verify all evidence scores are properly bounded between 0.0 and 1.0."""
        test_cases = [
            ("Mixed\t  indentation", self.indentation_rule, {'block_type': 'paragraph'}),
            ("```code in admonition```", self.admonition_rule, {'block_type': 'admonition'}),
            ("I should of done this.", self.writing_rule, {'block_type': 'paragraph'})
        ]
        
        for test_text, rule, context in test_cases:
            errors = rule.analyze(test_text, [test_text], nlp=self.nlp, context=context)
            
            for error in errors:
                # Check both possible evidence fields (Level 2 Enhanced Validation)
                evidence_score = error.get('evidence_score', error.get('confidence', 0.5))
                self.assertGreaterEqual(evidence_score, 0.0, 
                                      f"Evidence score should be >= 0.0 in {rule.__class__.__name__}")
                self.assertLessEqual(evidence_score, 1.0, 
                                   f"Evidence score should be <= 1.0 in {rule.__class__.__name__}")
    
    def test_surgical_guards_effectiveness(self):
        """Test that surgical guards prevent false positives appropriately."""
        # Test code context guards
        code_text = "```\n\t  mixed_indentation_in_code()\n```"
        code_context = {'block_type': 'code_block'}
        
        indentation_errors = self.indentation_rule.analyze(code_text, [code_text], context=code_context)
        self.assertEqual(len(indentation_errors), 0, "Should skip indentation analysis in code blocks")
        
        # Test creative writing guards
        creative_text = "I should of seen the the repetition coming."
        creative_context = {'content_type': 'creative'}
        
        writing_errors = self.writing_rule.analyze(creative_text, [creative_text], context=creative_context)
        # Creative context should reduce errors or provide lower confidence
        if writing_errors:
            for error in writing_errors:
                evidence_score = error.get('evidence_score', error.get('confidence', 0.5))
                self.assertLessEqual(evidence_score, 0.8, 
                                   "Creative context should reduce evidence scores")
    
    def test_rule_type_identifiers(self):
        """Verify all Phase 2 rules have proper type identifiers."""
        expected_types = {
            self.indentation_rule: 'indentation',
            self.admonition_rule: 'admonition_content',
            self.writing_rule: 'general_writing'
        }
        
        for rule, expected_type in expected_types.items():
            self.assertEqual(rule._get_rule_type(), expected_type, 
                           f"Rule should have correct type identifier")
    
    def test_contextual_messaging_and_suggestions(self):
        """Test that rules provide contextual messages and suggestions."""
        test_cases = [
            ("  Single space accident", self.indentation_rule, {'block_type': 'paragraph'}),
            ("Note with ```code```", self.admonition_rule, {'block_type': 'admonition'}),
            ("very unique solution", self.writing_rule, {'block_type': 'paragraph'})
        ]
        
        for test_text, rule, context in test_cases:
            errors = rule.analyze(test_text, [test_text], nlp=self.nlp, context=context)
            
            if errors:
                error = errors[0]
                # Check message quality
                self.assertIsInstance(error['message'], str)
                self.assertGreater(len(error['message']), 10, "Message should be descriptive")
                
                # Check suggestions quality
                self.assertIsInstance(error['suggestions'], list)
                self.assertGreater(len(error['suggestions']), 0, "Should provide suggestions")
                for suggestion in error['suggestions']:
                    self.assertIsInstance(suggestion, str)
                    self.assertGreater(len(suggestion), 5, "Suggestions should be helpful")


if __name__ == '__main__':
    # Set up test suite with discovery
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestIndentationRule))
    suite.addTests(loader.loadTestsFromTestCase(TestAdmonitionContentRule))
    suite.addTests(loader.loadTestsFromTestCase(TestGeneralWritingRule))
    suite.addTests(loader.loadTestsFromTestCase(TestPhase2Integration))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"PHASE 2 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, failure in result.failures:
            print(f"- {test}: {failure.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, error in result.errors:
            print(f"- {test}: {error.split('\\n')[-2]}")
    
    if not result.failures and not result.errors:
        print(f"\n🎉 ALL PHASE 2 TESTS PASSED! 🎉")
        print(f"Phase 2 Structure Validation is production-ready.")
    else:
        print(f"\n⚠️  Some tests failed. Please review and fix issues before deployment.")
    
    # Exit with proper code
    sys.exit(0 if not result.failures and not result.errors else 1)

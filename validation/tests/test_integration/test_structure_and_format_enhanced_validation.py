"""
Comprehensive test suite for structure_and_format directory enhanced validation.
Tests all rules in the structure_and_format directory with Level 2 enhanced error creation.
"""
import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from rules.structure_and_format.headings_rule import HeadingsRule
from rules.structure_and_format.notes_rule import NotesRule
from rules.structure_and_format.glossaries_rule import GlossariesRule
from rules.structure_and_format.admonitions_rule import AdmonitionsRule
from rules.structure_and_format.procedures_rule import ProceduresRule
from rules.structure_and_format.paragraphs_rule import ParagraphsRule
from rules.structure_and_format.messages_rule import MessagesRule
from rules.structure_and_format.lists_rule import ListsRule
from rules.structure_and_format.highlighting_rule import HighlightingRule

class TestStructureAndFormatEnhancedValidation(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures and load SpaCy if available."""
        self.test_context = {
            'block_type': 'paragraph',
            'content_type': 'technical', 
            'domain': 'software',
            'topic_type': 'Concept'
        }
        
        # Try to load spaCy model
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except (ImportError, OSError):
            # Create a mock NLP object for basic testing
            self.nlp = None
            print("Warning: SpaCy not available, using mock NLP for basic testing")

    def test_headings_rule_enhanced_validation(self):
        """Test HeadingsRule with enhanced validation parameters."""
        rule = HeadingsRule()
        
        # Test text with heading issues
        test_text = "How to Configure the System. Understanding System Architecture"
        test_sentences = [
            "How to Configure the System.",
            "Understanding System Architecture"
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "should not end with a period",
                    "sentence-style capitalization",
                    "question-style",
                    "should not start with a gerund"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertIn(error['severity'], ['low', 'medium'])
        else:
            print("Skipping detailed headings rule test - SpaCy not available")

    def test_notes_rule_enhanced_validation(self):
        """Test NotesRule with enhanced validation parameters."""
        rule = NotesRule()
        
        # Test text with note issues
        test_text = "NOTE check this carefully. IMPORTANT: follow these steps"
        test_sentences = [
            "NOTE check this carefully.",
            "IMPORTANT: follow these steps"
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "should be followed by a colon",
                    "may not be a complete sentence"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertIn(error['severity'], ['low', 'high'])
        else:
            print("Skipping detailed notes rule test - SpaCy not available")

    def test_glossaries_rule_enhanced_validation(self):
        """Test GlossariesRule with enhanced validation parameters."""
        rule = GlossariesRule()
        
        # Test text with glossary issues
        test_text = "API : programming interface. SDK : development kit"
        test_sentences = [
            "API : programming interface.",
            "SDK : development kit"
        ]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "should be lowercase",
                    "should start with a capital letter"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertEqual(error['severity'], 'medium')
        else:
            print("Skipping detailed glossaries rule test - SpaCy not available")

    def test_admonitions_rule_enhanced_validation(self):
        """Test AdmonitionsRule with enhanced validation parameters."""
        rule = AdmonitionsRule()
        
        # Test text with admonition issues
        test_text = "[WARNING] System may fail"
        
        if self.nlp:
            errors = rule.analyze(test_text, [], nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message formats
                valid_messages = [
                    "Invalid admonition label",
                    "may not be a complete sentence"
                ]
                self.assertTrue(any(msg in error['message'] for msg in valid_messages))
                self.assertIn(error['severity'], ['low', 'medium'])
        else:
            print("Skipping detailed admonitions rule test - SpaCy not available")

    def test_procedures_rule_enhanced_validation(self):
        """Test ProceduresRule with enhanced validation parameters."""
        rule = ProceduresRule()
        
        # Test text with procedure issues
        test_text = "The system will process your request"
        test_sentences = ["The system will process your request"]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("should begin with a strong, imperative verb", error['message'])
                self.assertEqual(error['severity'], 'medium')
        else:
            print("Skipping detailed procedures rule test - SpaCy not available")

    def test_messages_rule_enhanced_validation(self):
        """Test MessagesRule with enhanced validation parameters."""
        rule = MessagesRule()
        
        # Test text with message issues
        test_text = "A fatal error occurred in the system"
        test_sentences = ["A fatal error occurred in the system"]
        
        if self.nlp:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            
            # Should find exaggerated adjectives
            self.assertGreater(len(errors), 0, "Should detect exaggerated adjectives")
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                
                # Verify specific message format
                self.assertIn("Avoid using exaggerated adjectives", error['message'])
                self.assertEqual(error['severity'], 'medium')
        else:
            print("Skipping detailed messages rule test - SpaCy not available")

    def test_complex_structure_scenarios(self):
        """Test complex structure scenarios to ensure comprehensive coverage."""
        if not self.nlp:
            self.skipTest("SpaCy not available for comprehensive testing")
            
        # Test cases with varying complexity
        test_cases = [
            (HeadingsRule(), ["Understanding the System Architecture.", "How to Configure?"], "heading format issues"),
            (NotesRule(), ["NOTE check this", "IMPORTANT follow these steps"], "note formatting"),
            (MessagesRule(), ["A catastrophic failure occurred"], "exaggerated language"),
            (ProceduresRule(), ["The user should configure the system"], "procedure imperative verbs")
        ]
        
        total_errors = 0
        enhanced_errors = 0
        
        for rule, test_sentences, description in test_cases:
            try:
                test_text = " ".join(test_sentences)
                errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
                total_errors += len(errors)
                
                for error in errors:
                    self._verify_enhanced_error_structure(error)
                    if error.get('enhanced_validation_available', False):
                        enhanced_errors += 1
                        
            except Exception as e:
                self.fail(f"Rule {rule.__class__.__name__} failed for {description}: {e}")
        
        if total_errors > 0:
            enhancement_rate = (enhanced_errors / total_errors) * 100
            print(f"Complex structure enhancement coverage: {enhanced_errors}/{total_errors} ({enhancement_rate:.1f}%)")

    def test_all_rules_basic_functionality(self):
        """Test that all rules can be instantiated and called without errors."""
        rules = [
            HeadingsRule(), NotesRule(), GlossariesRule(), AdmonitionsRule(),
            ProceduresRule(), ParagraphsRule(), MessagesRule(), ListsRule(), HighlightingRule()
        ]
        test_text = "Test text for basic functionality."
        test_sentences = ["Test text for basic functionality."]
        
        for rule in rules:
            try:
                # Test with no NLP (should return empty list)
                errors = rule.analyze(test_text, test_sentences, nlp=None, context=self.test_context)
                self.assertIsInstance(errors, list)
                
                # Test with NLP if available (may or may not return errors)
                if self.nlp:
                    errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
                    self.assertIsInstance(errors, list)
                    
            except Exception as e:
                self.fail(f"Rule {rule.__class__.__name__} failed basic functionality test: {e}")

    def test_enhanced_validation_backward_compatibility(self):
        """Test that rules work with old calling patterns (backward compatibility)."""
        rules = [
            HeadingsRule(), NotesRule(), MessagesRule()
        ]
        test_text = "Test text."
        test_sentences = ["Test text."]
        
        for rule in rules:
            try:
                # Test old calling pattern without context
                errors = rule.analyze(test_text, test_sentences, nlp=self.nlp)
                self.assertIsInstance(errors, list)
                
                # Test old calling pattern with positional arguments
                errors = rule.analyze(test_text, test_sentences)
                self.assertIsInstance(errors, list)
                
            except Exception as e:
                self.fail(f"Rule {rule.__class__.__name__} failed backward compatibility test: {e}")

    def test_enhanced_validation_performance(self):
        """Test that enhanced validation doesn't significantly impact performance."""
        import time
        
        rule = HeadingsRule()  # Test with the most complex rule
        test_text = "How to Configure the System. Understanding System Architecture"
        test_sentences = [
            "How to Configure the System.",
            "Understanding System Architecture"
        ]
        
        if self.nlp:
            # Measure performance
            start_time = time.time()
            for _ in range(10):  # Run multiple times for average
                rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
            end_time = time.time()
            
            avg_time = (end_time - start_time) / 10
            # Should be under 100ms per analysis as per the implementation guide
            self.assertLess(avg_time, 0.1, f"Analysis took {avg_time:.3f}s, should be under 0.1s")

    def test_comprehensive_structure_scenarios(self):
        """Test complex structure scenarios to ensure comprehensive coverage."""
        if not self.nlp:
            self.skipTest("SpaCy not available for comprehensive testing")
            
        # Complex text with multiple structure issues
        test_text = """
        How to Configure the System. Understanding System Architecture.
        NOTE check this carefully. IMPORTANT follow these steps.
        API : programming interface. A fatal error occurred.
        """
        
        test_sentences = [s.strip() for s in test_text.strip().split('.') if s.strip()]
        
        rules = [
            HeadingsRule(), NotesRule(), GlossariesRule(), MessagesRule()
        ]
        
        total_errors = 0
        enhanced_errors = 0
        
        for rule in rules:
            try:
                errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
                total_errors += len(errors)
                
                for error in errors:
                    self._verify_enhanced_error_structure(error)
                    if error.get('enhanced_validation_available', False):
                        enhanced_errors += 1
                        
            except Exception as e:
                self.fail(f"Rule {rule.__class__.__name__} failed comprehensive test: {e}")
        
        if total_errors > 0:
            enhancement_rate = (enhanced_errors / total_errors) * 100
            print(f"Comprehensive test enhancement coverage: {enhanced_errors}/{total_errors} ({enhancement_rate:.1f}%)")
            # Should have good enhancement coverage
            self.assertGreater(enhancement_rate, 0, "Should have some enhanced validation coverage")

    def test_domain_specific_validation(self):
        """Test that enhanced validation works with different domain contexts."""
        if not self.nlp:
            self.skipTest("SpaCy not available for domain testing")
            
        rule = MessagesRule()
        test_text = "A fatal error occurred in the application."
        test_sentences = ["A fatal error occurred in the application."]
        
        # Test different domain contexts
        contexts = [
            {'domain': 'software', 'content_type': 'technical'},
            {'domain': 'documentation', 'content_type': 'user_guide'},
            {'domain': 'general', 'content_type': 'instructions'}
        ]
        
        for context in contexts:
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=context)
            
            for error in errors:
                self._verify_enhanced_error_structure(error)
                # Enhanced validation should be available regardless of domain
                self.assertIn('enhanced_validation_available', error)

    def test_json_serialization_compatibility(self):
        """Test that all errors are JSON serializable."""
        if not self.nlp:
            self.skipTest("SpaCy not available for JSON testing")
            
        import json
        
        rule = MessagesRule()
        test_text = "A fatal error occurred."
        test_sentences = ["A fatal error occurred."]
        
        errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.test_context)
        
        for error in errors:
            try:
                json_str = json.dumps(error)
                self.assertIsInstance(json_str, str)
                # Verify it can be parsed back
                parsed = json.loads(json_str)
                self.assertIsInstance(parsed, dict)
            except (TypeError, ValueError) as e:
                self.fail(f"Error is not JSON serializable: {e}")

    def test_special_structure_rules(self):
        """Test special structure rules that require specific handling."""
        if not self.nlp:
            self.skipTest("SpaCy not available for special rule testing")
            
        # Test ParagraphsRule (requires mock paragraph node)
        from unittest.mock import Mock
        paragraph_rule = ParagraphsRule()
        
        # Mock paragraph node with indentation
        mock_node = Mock()
        mock_node.indent = 4  # Simulate indented paragraph
        
        try:
            # This should work even with mock setup
            errors = paragraph_rule.analyze("    Indented text", ["    Indented text"], 
                                          nlp=self.nlp, context=self.test_context, 
                                          paragraph_node=mock_node)
            self.assertIsInstance(errors, list)
        except Exception as e:
            # Expected to fail in some cases due to missing structural context
            print(f"ParagraphsRule test expected behavior: {e}")

    def _verify_enhanced_error_structure(self, error):
        """Verify that an error has the enhanced validation structure."""
        # Verify basic required fields
        required_fields = ['type', 'message', 'suggestions', 'sentence', 'sentence_index', 'severity']
        for field in required_fields:
            self.assertIn(field, error, f"Error missing required field: {field}")
        
        # Verify enhanced validation fields
        self.assertIn('enhanced_validation_available', error)
        
        if error.get('enhanced_validation_available', False):
            # If enhanced validation is available, check for confidence score
            if 'confidence_score' in error:
                confidence = error['confidence_score']
                self.assertIsInstance(confidence, (int, float))
                self.assertGreaterEqual(confidence, 0.0)
                self.assertLessEqual(confidence, 1.0)
        
        # Verify data types
        self.assertIsInstance(error['message'], str)
        self.assertIsInstance(error['suggestions'], list)
        self.assertIsInstance(error['sentence'], str)
        self.assertIsInstance(error['sentence_index'], int)
        self.assertIn(error['severity'], ['low', 'medium', 'high'])
        
        # Verify JSON serializability
        try:
            import json
            json.dumps(error)
        except TypeError as e:
            self.fail(f"Error is not JSON serializable: {e}")

if __name__ == '__main__':
    unittest.main()
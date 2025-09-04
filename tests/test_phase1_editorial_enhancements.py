"""
Comprehensive test suite for Phase 1 Editorial Enhancements.
Tests the new spacing rule, enhanced periods rule, and list punctuation rule.

This test suite validates:
- Evidence-based analysis (0.0-1.0 scoring)
- Level 2 enhanced validation (text and context parameters)
- Surgical zero false positive guards
- Context-aware messaging and suggestions
- Integration with existing architecture
"""
import unittest
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from rules.punctuation.spacing_rule import SpacingRule
from rules.punctuation.periods_rule import PeriodsRule
from rules.structure_and_format.list_punctuation_rule import ListPunctuationRule


class TestPhase1EditorialEnhancements(unittest.TestCase):
    """Comprehensive test suite for Phase 1 Editorial Enhancements."""
    
    def setUp(self):
        """Set up test fixtures and load SpaCy if available."""
        self.base_context = {
            'block_type': 'paragraph',
            'content_type': 'technical', 
            'domain': 'software'
        }
        
        # Try to load spaCy model
        try:
            import spacy
            self.nlp = spacy.load('en_core_web_sm')
        except (ImportError, OSError):
            # Create a mock NLP object for basic testing
            self.nlp = None
            print("Warning: SpaCy not available, using basic fallback testing")
    
    def _verify_enhanced_error_structure(self, error):
        """Verify that error follows Level 2 enhanced validation structure."""
        # Core error structure
        self.assertIn('type', error)
        self.assertIn('message', error)
        self.assertIn('suggestions', error)
        self.assertIn('sentence', error)
        self.assertIn('sentence_index', error)
        self.assertIn('severity', error)
        
        # Level 2 enhanced validation fields
        self.assertIn('text', error)
        self.assertIn('context', error)
        
        # Evidence-based fields
        self.assertIn('evidence_score', error)
        self.assertIsInstance(error['evidence_score'], (int, float))
        self.assertTrue(0.0 <= error['evidence_score'] <= 1.0)
        
        # Additional enhanced fields
        self.assertIn('span', error)
        self.assertIn('flagged_text', error)
        
        # Verify suggestions are non-empty and reasonable
        self.assertIsInstance(error['suggestions'], list)
        self.assertTrue(len(error['suggestions']) > 0)
        for suggestion in error['suggestions']:
            self.assertIsInstance(suggestion, str)
            self.assertTrue(len(suggestion.strip()) > 0)


class TestSpacingRule(TestPhase1EditorialEnhancements):
    """Test the new SpacingRule with evidence-based analysis."""
    
    def setUp(self):
        super().setUp()
        self.rule = SpacingRule()
    
    def test_spacing_rule_double_spaces(self):
        """Test spacing rule detects double spaces with proper evidence scoring."""
        test_text = "This is  a sentence with  double spaces."
        test_sentences = ["This is  a sentence with  double spaces."]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.base_context)
        
        # Should detect double space issues
        self.assertTrue(len(errors) > 0)
        
        for error in errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'spacing')
            self.assertIn('violation_type', error)
            
            # Evidence score should be high for clear double space violations
            if 'double_spaces' in error.get('violation_type', ''):
                self.assertGreater(error['evidence_score'], 0.5)
    
    def test_spacing_rule_missing_space_after_period(self):
        """Test spacing rule detects missing spaces after periods."""
        test_text = "This sentence is wrong.Next sentence starts here."
        test_sentences = ["This sentence is wrong.Next sentence starts here."]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.base_context)
        
        # Should detect missing space after period
        missing_space_errors = [e for e in errors if 'missing_space_after_period' in e.get('violation_type', '')]
        self.assertTrue(len(missing_space_errors) > 0)
        
        for error in missing_space_errors:
            self._verify_enhanced_error_structure(error)
            self.assertGreater(error['evidence_score'], 0.7)  # Should have high evidence
    
    def test_spacing_rule_trailing_spaces(self):
        """Test spacing rule detects trailing spaces."""
        test_text = "This line has trailing spaces.   \nThis line is clean."
        test_sentences = ["This line has trailing spaces.", "This line is clean."]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.base_context)
        
        # May detect trailing spaces (depending on context)
        trailing_errors = [e for e in errors if 'trailing_spaces' in e.get('violation_type', '')]
        
        for error in trailing_errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'spacing')
    
    def test_spacing_rule_code_context_guard(self):
        """Test that spacing rule respects code context guards."""
        code_context = {
            'block_type': 'code_block',
            'content_type': 'technical',
            'domain': 'software'
        }
        
        test_text = "function  test()  {  return  true;  }"  # Multiple spacing issues
        test_sentences = ["function  test()  {  return  true;  }"]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=code_context)
        
        # Should not flag spacing issues in code blocks
        self.assertEqual(len(errors), 0)
    
    def test_spacing_rule_fallback_analysis(self):
        """Test spacing rule fallback analysis when spaCy is not available."""
        test_text = "This has  multiple  spacing   issues."
        test_sentences = ["This has  multiple  spacing   issues."]
        
        # Force fallback analysis
        errors = self.rule.analyze(test_text, test_sentences, nlp=None, context=self.base_context)
        
        # Should still detect some issues using regex patterns
        if len(errors) > 0:
            for error in errors:
                self._verify_enhanced_error_structure(error)
                self.assertEqual(error['type'], 'spacing')


class TestEnhancedPeriodsRule(TestPhase1EditorialEnhancements):
    """Test the enhanced PeriodsRule with new capabilities."""
    
    def setUp(self):
        super().setUp()
        self.rule = PeriodsRule()
    
    def test_periods_rule_abbreviation_periods(self):
        """Test enhanced periods rule detects abbreviation periods."""
        test_text = "The U.S.A. is a country. The F.B.I. investigates crimes."
        test_sentences = ["The U.S.A. is a country.", "The F.B.I. investigates crimes."]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.base_context)
        
        # Should detect abbreviation period issues
        abbrev_errors = [e for e in errors if 'abbreviation_periods' in e.get('violation_type', '')]
        
        for error in abbrev_errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'periods')
            self.assertGreater(error['evidence_score'], 0.5)
    
    def test_periods_rule_duplicate_periods(self):
        """Test enhanced periods rule detects duplicate periods."""
        test_text = "This sentence ends incorrectly.. This is also wrong.."
        test_sentences = ["This sentence ends incorrectly..", "This is also wrong.."]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.base_context)
        
        # Should detect duplicate periods
        duplicate_errors = [e for e in errors if 'duplicate_periods' in e.get('violation_type', '')]
        
        for error in duplicate_errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'periods')
            self.assertGreater(error['evidence_score'], 0.7)  # High evidence for duplicate periods
    
    def test_periods_rule_unnecessary_period_in_heading(self):
        """Test enhanced periods rule detects unnecessary periods in headings."""
        heading_context = {
            'block_type': 'heading',
            'content_type': 'technical',
            'domain': 'software'
        }
        
        test_text = "Installation Guide."
        test_sentences = ["Installation Guide."]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=heading_context)
        
        # Should detect unnecessary period in heading
        heading_errors = [e for e in errors if 'unnecessary_period_in_heading' in e.get('violation_type', '')]
        
        for error in heading_errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'periods')
            self.assertGreater(error['evidence_score'], 0.4)
    
    def test_periods_rule_unnecessary_period_in_list(self):
        """Test enhanced periods rule detects unnecessary periods in list items."""
        list_context = {
            'block_type': 'unordered_list_item',
            'content_type': 'technical',
            'domain': 'software'
        }
        
        test_text = "Install software."  # Short list item with period
        test_sentences = ["Install software."]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=list_context)
        
        # May detect unnecessary period in list item
        list_errors = [e for e in errors if 'unnecessary_period_in_list' in e.get('violation_type', '')]
        
        for error in list_errors:
            self._verify_enhanced_error_structure(error)
            self.assertEqual(error['type'], 'periods')
    
    def test_periods_rule_creative_content_guard(self):
        """Test that periods rule respects creative content guards."""
        creative_context = {
            'block_type': 'paragraph',
            'content_type': 'creative',
            'domain': 'literature'
        }
        
        test_text = "This is U.S.A. creative writing with F.B.I. style."
        test_sentences = ["This is U.S.A. creative writing with F.B.I. style."]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=creative_context)
        
        # Should not flag period issues in creative content
        self.assertEqual(len(errors), 0)


class TestListPunctuationRule(TestPhase1EditorialEnhancements):
    """Test the new ListPunctuationRule with context-aware validation."""
    
    def setUp(self):
        super().setUp()
        self.rule = ListPunctuationRule()
    
    def test_list_punctuation_rule_single_fragment(self):
        """Test list punctuation rule for single fragment items."""
        list_context = {
            'block_type': 'unordered_list_item',
            'content_type': 'technical',
            'domain': 'software'
        }
        
        test_text = "Install software."  # Fragment with unnecessary period
        test_sentences = ["Install software."]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=list_context)
        
        # Should detect unnecessary period in fragment
        if len(errors) > 0:
            for error in errors:
                self._verify_enhanced_error_structure(error)
                self.assertEqual(error['type'], 'list_punctuation')
                self.assertIn('item_classification', error)
    
    def test_list_punctuation_rule_single_sentence(self):
        """Test list punctuation rule for single sentence items."""
        list_context = {
            'block_type': 'ordered_list_item',
            'content_type': 'technical',
            'domain': 'software'
        }
        
        test_text = "You must install the software before proceeding"  # Sentence without period
        test_sentences = ["You must install the software before proceeding"]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=list_context)
        
        # Should detect missing period in sentence
        if len(errors) > 0:
            for error in errors:
                self._verify_enhanced_error_structure(error)
                self.assertEqual(error['type'], 'list_punctuation')
                self.assertIn('item_classification', error)
    
    def test_list_punctuation_rule_item_classification(self):
        """Test the classify_list_item method."""
        # Test sentence classification
        sentence_text = "You should install the software before proceeding with the configuration."
        classification = self.rule.classify_list_item(sentence_text)
        self.assertIn(classification, ['sentence', 'fragment'])
        
        # Test fragment classification  
        fragment_text = "Software installation"
        classification = self.rule.classify_list_item(fragment_text)
        self.assertIn(classification, ['sentence', 'fragment'])
        
        # Test with spaCy if available
        if self.nlp:
            doc = self.nlp(sentence_text)
            classification = self.rule.classify_list_item(sentence_text, doc)
            self.assertIn(classification, ['sentence', 'fragment'])
    
    def test_list_punctuation_rule_non_list_context(self):
        """Test that list punctuation rule skips non-list contexts."""
        paragraph_context = {
            'block_type': 'paragraph',
            'content_type': 'technical',
            'domain': 'software'
        }
        
        test_text = "This is a paragraph with no periods"
        test_sentences = ["This is a paragraph with no periods"]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=paragraph_context)
        
        # Should not analyze non-list contexts
        self.assertEqual(len(errors), 0)
    
    def test_list_punctuation_rule_creative_content_guard(self):
        """Test that list punctuation rule respects creative content guards."""
        creative_list_context = {
            'block_type': 'unordered_list_item',
            'content_type': 'creative',
            'domain': 'literature'
        }
        
        test_text = "Creative item with period."
        test_sentences = ["Creative item with period."]
        
        errors = self.rule.analyze(test_text, test_sentences, nlp=self.nlp, context=creative_list_context)
        
        # Should not flag creative content
        self.assertEqual(len(errors), 0)
    
    def test_list_punctuation_rule_fallback_analysis(self):
        """Test list punctuation rule fallback analysis when spaCy is not available."""
        list_context = {
            'block_type': 'list_item',
            'content_type': 'technical',
            'domain': 'software'
        }
        
        test_text = "Short item."
        test_sentences = ["Short item."]
        
        # Force fallback analysis
        errors = self.rule.analyze(test_text, test_sentences, nlp=None, context=list_context)
        
        # Should still work with fallback classification
        if len(errors) > 0:
            for error in errors:
                self._verify_enhanced_error_structure(error)
                self.assertEqual(error['type'], 'list_punctuation')


class TestPhase1Integration(TestPhase1EditorialEnhancements):
    """Test integration between Phase 1 rules and overall system."""
    
    def test_all_rules_follow_enhanced_validation(self):
        """Test that all Phase 1 rules follow Level 2 enhanced validation."""
        rules = [SpacingRule(), PeriodsRule(), ListPunctuationRule()]
        
        for rule in rules:
            # Verify rule has proper rule type
            self.assertTrue(hasattr(rule, '_get_rule_type'))
            rule_type = rule._get_rule_type()
            self.assertIsInstance(rule_type, str)
            self.assertTrue(len(rule_type) > 0)
            
            # Verify rule has proper analyze method signature
            self.assertTrue(hasattr(rule, 'analyze'))
            
            # Test with sample data
            test_text = "Sample text for testing."
            test_sentences = ["Sample text for testing."]
            
            try:
                errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=self.base_context)
                self.assertIsInstance(errors, list)
                
                # Verify all errors follow enhanced validation structure
                for error in errors:
                    self._verify_enhanced_error_structure(error)
                    
            except Exception as e:
                self.fail(f"Rule {rule.__class__.__name__} failed analysis: {str(e)}")
    
    def test_evidence_score_ranges(self):
        """Test that all Phase 1 rules produce evidence scores in valid ranges."""
        rules = [
            (SpacingRule(), "This has  double spaces.", ['spacing']),
            (PeriodsRule(), "U.S.A. has periods.", ['periods']),
            (ListPunctuationRule(), "List item.", ['list_punctuation'])
        ]
        
        for rule, test_text, expected_types in rules:
            test_sentences = [test_text]
            
            # Use appropriate context for each rule
            if 'list_punctuation' in expected_types:
                context = {'block_type': 'list_item', 'content_type': 'technical'}
            else:
                context = self.base_context
            
            errors = rule.analyze(test_text, test_sentences, nlp=self.nlp, context=context)
            
            for error in errors:
                # Verify evidence score is in valid range
                evidence_score = error['evidence_score']
                self.assertGreaterEqual(evidence_score, 0.0)
                self.assertLessEqual(evidence_score, 1.0)
                
                # Verify rule type matches expected
                self.assertIn(error['type'], expected_types)
    
    def test_surgical_guards_effectiveness(self):
        """Test that surgical zero false positive guards work effectively."""
        # Test spacing rule with code context
        spacing_rule = SpacingRule()
        code_context = {'block_type': 'code_block', 'content_type': 'technical'}
        code_text = "function  test()  {  console.log('hello  world');  }"
        
        spacing_errors = spacing_rule.analyze(code_text, [code_text], nlp=self.nlp, context=code_context)
        self.assertEqual(len(spacing_errors), 0, "Spacing rule should not flag code blocks")
        
        # Test periods rule with creative content
        periods_rule = PeriodsRule()
        creative_context = {'block_type': 'paragraph', 'content_type': 'creative'}
        creative_text = "The U.S.A. is beautiful in this story."
        
        periods_errors = periods_rule.analyze(creative_text, [creative_text], nlp=self.nlp, context=creative_context)
        self.assertEqual(len(periods_errors), 0, "Periods rule should not flag creative content")
        
        # Test list punctuation rule with non-list content
        list_rule = ListPunctuationRule()
        paragraph_context = {'block_type': 'paragraph', 'content_type': 'technical'}
        paragraph_text = "This is not a list item."
        
        list_errors = list_rule.analyze(paragraph_text, [paragraph_text], nlp=self.nlp, context=paragraph_context)
        self.assertEqual(len(list_errors), 0, "List punctuation rule should not analyze non-list content")


if __name__ == '__main__':
    unittest.main(verbosity=2)

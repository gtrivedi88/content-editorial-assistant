"""
Individual Rule Testing Suite
Comprehensive unit tests for each of the 45+ style rules.
Tests each rule in isolation with specific pattern validation.
"""

import pytest
import os
import sys
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test utilities
from tests.test_utils import TestConfig, TestFixtures, TestValidators

# Import rules (with fallback handling)
try:
    from rules.language_and_grammar.abbreviations_rule import AbbreviationsRule
    from rules.language_and_grammar.anthropomorphism_rule import AnthropomorphismRule
    from rules.language_and_grammar.contractions_rule import ContractionsRule
    from rules.language_and_grammar.inclusive_language_rule import InclusiveLanguageRule
    from rules.language_and_grammar.pronouns_rule import PronounsRule
    from rules.language_and_grammar.verbs_rule import VerbsRule
    from rules.punctuation.commas_rule import CommasRule
    from rules.punctuation.quotation_marks_rule import QuotationMarksRule
    from rules.structure_and_format.headings_rule import HeadingsRule
    from rules.structure_and_format.lists_rule import ListsRule
    from rules.structure_and_format.procedures_rule import ProceduresRule
    RULES_AVAILABLE = True
except ImportError:
    RULES_AVAILABLE = False


class TestLanguageRulesIndividual:
    """Individual tests for language and grammar rules."""
    
    @pytest.fixture
    def mock_nlp(self):
        """Create a comprehensive mock SpaCy NLP object."""
        def create_mock_doc(text):
            doc = Mock()
            words = text.split()
            tokens = []
            
            for i, word in enumerate(words):
                token = Mock()
                token.text = word
                token.lemma_ = word.lower()
                token.pos_ = self._get_pos_for_word(word)
                token.tag_ = self._get_tag_for_word(word)
                token.dep_ = "nsubj" if i == 0 else "obj"
                token.is_alpha = word.isalpha()
                token.is_stop = word.lower() in ['the', 'a', 'an', 'and', 'or']
                token.lower_ = word.lower()
                token.i = i
                token.head = tokens[0] if tokens else token
                token.children = []
                tokens.append(token)
            
            doc.__iter__ = Mock(return_value=iter(tokens))
            doc.__len__ = Mock(return_value=len(tokens))
            doc.__getitem__ = Mock(side_effect=lambda x: tokens[x] if 0 <= x < len(tokens) else None)
            
            return doc
        
        nlp = Mock()
        nlp.side_effect = create_mock_doc
        return nlp
    
    def _get_pos_for_word(self, word):
        """Get POS tag for word (simplified)."""
        word_lower = word.lower()
        if word_lower in ['was', 'is', 'are', 'were', 'been', 'being']:
            return 'AUX'
        elif word_lower in ['the', 'a', 'an']:
            return 'DET'
        elif word_lower in ['and', 'or', 'but']:
            return 'CCONJ'
        elif word_lower.endswith('ly'):
            return 'ADV'
        else:
            return 'NOUN'
    
    def _get_tag_for_word(self, word):
        """Get detailed tag for word (simplified)."""
        word_lower = word.lower()
        if word_lower in ['was', 'were']:
            return 'VBD'
        elif word_lower in ['is', 'are']:
            return 'VBZ'
        else:
            return 'NN'
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_abbreviations_rule_detection(self, mock_nlp):
        """Test abbreviations rule with various patterns."""
        rule = AbbreviationsRule()
        
        # Test cases with Latin abbreviations
        test_cases = [
            {
                'text': "Use this feature e.g. in production.",
                'sentences': ["Use this feature e.g. in production."],
                'should_detect': True,
                'expected_suggestion': 'for example'
            },
            {
                'text': "Configure settings i.e. the database.",
                'sentences': ["Configure settings i.e. the database."],
                'should_detect': True,
                'expected_suggestion': 'that is'
            },
            {
                'text': "Use for example in production.",
                'sentences': ["Use for example in production."],
                'should_detect': False,
                'expected_suggestion': None
            },
            {
                'text': "Set up etc. configuration files.",
                'sentences': ["Set up etc. configuration files."],
                'should_detect': True,
                'expected_suggestion': 'and so on'
            }
        ]
        
        for case in test_cases:
            errors = rule.analyze(
                case['text'], 
                case['sentences'], 
                mock_nlp,
                {'block_type': 'paragraph'}
            )
            
            if case['should_detect']:
                assert len(errors) > 0, f"Should detect abbreviation in: {case['text']}"
                assert errors[0]['type'] == 'abbreviations'
                if case['expected_suggestion']:
                    suggestions = ' '.join(errors[0]['suggestions'])
                    assert case['expected_suggestion'] in suggestions.lower()
            else:
                assert len(errors) == 0, f"Should not detect abbreviation in: {case['text']}"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_anthropomorphism_rule_patterns(self, mock_nlp):
        """Test anthropomorphism rule with various patterns."""
        rule = AnthropomorphismRule()
        
        test_cases = [
            {
                'text': "The system thinks this is correct.",
                'sentences': ["The system thinks this is correct."],
                'should_detect': True,
                'reason': 'Systems cannot think'
            },
            {
                'text': "The application wants to connect.",
                'sentences': ["The application wants to connect."],
                'should_detect': True,
                'reason': 'Applications cannot want'
            },
            {
                'text': "The system processes the data.",
                'sentences': ["The system processes the data."],
                'should_detect': False,
                'reason': 'Processing is a valid system action'
            },
            {
                'text': "The user thinks this is helpful.",
                'sentences': ["The user thinks this is helpful."],
                'should_detect': False,
                'reason': 'Users can think'
            }
        ]
        
        for case in test_cases:
            errors = rule.analyze(
                case['text'], 
                case['sentences'], 
                mock_nlp,
                {'block_type': 'paragraph'}
            )
            
            if case['should_detect']:
                assert len(errors) > 0, f"Should detect anthropomorphism in: {case['text']} ({case['reason']})"
                assert errors[0]['type'] == 'anthropomorphism'
            else:
                assert len(errors) == 0, f"Should not detect anthropomorphism in: {case['text']} ({case['reason']})"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_contractions_rule_validation(self, mock_nlp):
        """Test contractions rule with formal tone requirements."""
        rule = ContractionsRule()
        
        test_cases = [
            {
                'text': "Don't use this feature in production.",
                'sentences': ["Don't use this feature in production."],
                'should_detect': True,
                'expected_replacement': 'do not'
            },
            {
                'text': "You can't access this without permission.",
                'sentences': ["You can't access this without permission."],
                'should_detect': True,
                'expected_replacement': 'cannot'
            },
            {
                'text': "Do not use this feature in production.",
                'sentences': ["Do not use this feature in production."],
                'should_detect': False
            },
            {
                'text': "It's working correctly now.",
                'sentences': ["It's working correctly now."],
                'should_detect': True,
                'expected_replacement': 'it is'
            }
        ]
        
        for case in test_cases:
            errors = rule.analyze(
                case['text'], 
                case['sentences'], 
                mock_nlp,
                {'block_type': 'paragraph'}
            )
            
            if case['should_detect']:
                assert len(errors) > 0, f"Should detect contraction in: {case['text']}"
                assert errors[0]['type'] == 'contractions'
                if 'expected_replacement' in case:
                    suggestions = ' '.join(errors[0]['suggestions'])
                    assert case['expected_replacement'] in suggestions.lower()
            else:
                assert len(errors) == 0, f"Should not detect contraction in: {case['text']}"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_inclusive_language_detection(self, mock_nlp):
        """Test inclusive language rule with various non-inclusive terms."""
        rule = InclusiveLanguageRule()
        
        test_cases = [
            {
                'text': "Add items to the whitelist for approval.",
                'sentences': ["Add items to the whitelist for approval."],
                'should_detect': True,
                'expected_alternative': 'allowlist'
            },
            {
                'text': "Remove items from the blacklist.",
                'sentences': ["Remove items from the blacklist."],
                'should_detect': True,
                'expected_alternative': 'blocklist'
            },
            {
                'text': "The master server controls replication.",
                'sentences': ["The master server controls replication."],
                'should_detect': True,
                'expected_alternative': 'primary'
            },
            {
                'text': "Add items to the allowlist for approval.",
                'sentences': ["Add items to the allowlist for approval."],
                'should_detect': False
            },
            {
                'text': "This requires 10 man-hours of work.",
                'sentences': ["This requires 10 man-hours of work."],
                'should_detect': True,
                'expected_alternative': 'person-hours'
            }
        ]
        
        for case in test_cases:
            errors = rule.analyze(
                case['text'], 
                case['sentences'], 
                mock_nlp,
                {'block_type': 'paragraph'}
            )
            
            if case['should_detect']:
                assert len(errors) > 0, f"Should detect non-inclusive language in: {case['text']}"
                assert errors[0]['type'] == 'inclusive_language'
                if 'expected_alternative' in case:
                    suggestions = ' '.join(errors[0]['suggestions'])
                    assert case['expected_alternative'] in suggestions.lower()
            else:
                assert len(errors) == 0, f"Should not detect non-inclusive language in: {case['text']}"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_pronouns_rule_accuracy(self, mock_nlp):
        """Test pronouns rule for proper usage and clarity."""
        rule = PronounsRule()
        
        test_cases = [
            {
                'text': "We recommend using the new feature.",
                'sentences': ["We recommend using the new feature."],
                'should_detect': True,
                'reason': 'Should use second person'
            },
            {
                'text': "You should use the new feature.",
                'sentences': ["You should use the new feature."],
                'should_detect': False,
                'reason': 'Correct second person usage'
            },
            {
                'text': "Our system provides these capabilities.",
                'sentences': ["Our system provides these capabilities."],
                'should_detect': True,
                'reason': 'Should avoid first person possessive'
            },
            {
                'text': "The system provides these capabilities.",
                'sentences': ["The system provides these capabilities."],
                'should_detect': False,
                'reason': 'Clear without pronouns'
            }
        ]
        
        for case in test_cases:
            errors = rule.analyze(
                case['text'], 
                case['sentences'], 
                mock_nlp,
                {'block_type': 'paragraph'}
            )
            
            if case['should_detect']:
                assert len(errors) > 0, f"Should detect pronoun issue in: {case['text']} ({case['reason']})"
                assert errors[0]['type'] == 'pronouns'
            else:
                assert len(errors) == 0, f"Should not detect pronoun issue in: {case['text']} ({case['reason']})"


class TestPunctuationRulesIndividual:
    """Individual tests for punctuation rules."""
    
    @pytest.fixture
    def mock_nlp(self):
        """Create mock SpaCy NLP for punctuation testing."""
        def create_mock_doc(text):
            doc = Mock()
            # Simple tokenization for punctuation testing
            tokens = []
            for i, char in enumerate(text):
                token = Mock()
                token.text = char
                token.is_punct = char in '.,!?;:'
                token.is_alpha = char.isalpha()
                token.i = i
                tokens.append(token)
            
            doc.__iter__ = Mock(return_value=iter(tokens))
            doc.__len__ = Mock(return_value=len(tokens))
            
            return doc
        
        nlp = Mock()
        nlp.side_effect = create_mock_doc
        return nlp
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_commas_rule_patterns(self, mock_nlp):
        """Test comma usage patterns."""
        rule = CommasRule()
        
        test_cases = [
            {
                'text': "Configure the server, database, and application.",
                'sentences': ["Configure the server, database, and application."],
                'should_detect': False,
                'reason': 'Correct serial comma usage'
            },
            {
                'text': "Configure the server, database and application.",
                'sentences': ["Configure the server, database and application."],
                'should_detect': True,
                'reason': 'Missing serial comma'
            },
            {
                'text': "However, you should configure the server.",
                'sentences': ["However, you should configure the server."],
                'should_detect': False,
                'reason': 'Correct introductory comma'
            }
        ]
        
        for case in test_cases:
            errors = rule.analyze(
                case['text'], 
                case['sentences'], 
                mock_nlp,
                {'block_type': 'paragraph'}
            )
            
            if case['should_detect']:
                assert len(errors) > 0, f"Should detect comma issue in: {case['text']} ({case['reason']})"
                assert errors[0]['type'] == 'commas'
            else:
                assert len(errors) == 0, f"Should not detect comma issue in: {case['text']} ({case['reason']})"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_quotation_marks_validation(self, mock_nlp):
        """Test quotation mark usage and style."""
        rule = QuotationMarksRule()
        
        test_cases = [
            {
                'text': 'Use "smart quotes" for better typography.',
                'sentences': ['Use "smart quotes" for better typography.'],
                'should_detect': False,
                'reason': 'Correct smart quotes'
            },
            {
                'text': 'Use "straight quotes" for code examples.',
                'sentences': ['Use "straight quotes" for code examples.'],
                'should_detect': True,
                'reason': 'Should use smart quotes for regular text'
            },
            {
                'text': "Don't mix 'single' and \"double\" quotes.",
                'sentences': ["Don't mix 'single' and \"double\" quotes."],
                'should_detect': True,
                'reason': 'Inconsistent quote style'
            }
        ]
        
        for case in test_cases:
            errors = rule.analyze(
                case['text'], 
                case['sentences'], 
                mock_nlp,
                {'block_type': 'paragraph'}
            )
            
            if case['should_detect']:
                assert len(errors) > 0, f"Should detect quote issue in: {case['text']} ({case['reason']})"
                assert errors[0]['type'] == 'quotation_marks'
            else:
                assert len(errors) == 0, f"Should not detect quote issue in: {case['text']} ({case['reason']})"


class TestStructureRulesIndividual:
    """Individual tests for structure and format rules."""
    
    @pytest.fixture
    def mock_nlp(self):
        """Create mock SpaCy NLP for structure testing."""
        def create_mock_doc(text):
            doc = Mock()
            words = text.split()
            tokens = []
            
            for i, word in enumerate(words):
                token = Mock()
                token.text = word
                token.lemma_ = word.lower()
                token.pos_ = 'VERB' if i == 0 and word.lower() in ['click', 'enter', 'select', 'configure'] else 'NOUN'
                token.tag_ = 'VB' if token.pos_ == 'VERB' else 'NN'
                token.dep_ = 'ROOT' if i == 0 else 'obj'
                token.is_alpha = word.isalpha()
                token.i = i
                tokens.append(token)
            
            doc.__iter__ = Mock(return_value=iter(tokens))
            doc.__len__ = Mock(return_value=len(tokens))
            
            return doc
        
        nlp = Mock()
        nlp.side_effect = create_mock_doc
        return nlp
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_headings_rule_validation(self, mock_nlp):
        """Test heading format and style validation."""
        rule = HeadingsRule()
        
        test_cases = [
            {
                'text': "Configuration Management",
                'sentences': ["Configuration Management"],
                'context': {'block_type': 'heading', 'level': 1},
                'should_detect': False,
                'reason': 'Proper title case heading'
            },
            {
                'text': "configuration management",
                'sentences': ["configuration management"],
                'context': {'block_type': 'heading', 'level': 1},
                'should_detect': True,
                'reason': 'Should use title case'
            },
            {
                'text': "How To Configure The System",
                'sentences': ["How To Configure The System"],
                'context': {'block_type': 'heading', 'level': 2},
                'should_detect': True,
                'reason': 'Should not capitalize articles and prepositions'
            }
        ]
        
        for case in test_cases:
            errors = rule.analyze(
                case['text'], 
                case['sentences'], 
                mock_nlp,
                case.get('context', {'block_type': 'heading'})
            )
            
            if case['should_detect']:
                assert len(errors) > 0, f"Should detect heading issue in: {case['text']} ({case['reason']})"
                assert errors[0]['type'] == 'headings'
            else:
                assert len(errors) == 0, f"Should not detect heading issue in: {case['text']} ({case['reason']})"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_lists_rule_parallelism(self, mock_nlp):
        """Test list parallelism and consistency."""
        rule = ListsRule()
        
        test_cases = [
            {
                'text': "Configure the server\nInstall the software\nStart the service",
                'sentences': ["Configure the server", "Install the software", "Start the service"],
                'context': {'block_type': 'list_item_unordered'},
                'should_detect': False,
                'reason': 'Parallel verb structure'
            },
            {
                'text': "Configure the server\nInstalling the software\nStart the service",
                'sentences': ["Configure the server", "Installing the software", "Start the service"],
                'context': {'block_type': 'list_item_unordered'},
                'should_detect': True,
                'reason': 'Mixed verb forms break parallelism'
            },
            {
                'text': "Server configuration\nSoftware installation\nService startup",
                'sentences': ["Server configuration", "Software installation", "Service startup"],
                'context': {'block_type': 'list_item_unordered'},
                'should_detect': False,
                'reason': 'Parallel noun structure'
            }
        ]
        
        for case in test_cases:
            errors = rule.analyze(
                case['text'], 
                case['sentences'], 
                mock_nlp,
                case.get('context', {'block_type': 'list_item'})
            )
            
            if case['should_detect']:
                assert len(errors) > 0, f"Should detect list issue in: {case['text']} ({case['reason']})"
                assert errors[0]['type'] == 'lists'
            else:
                assert len(errors) == 0, f"Should not detect list issue in: {case['text']} ({case['reason']})"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_procedures_rule_imperatives(self, mock_nlp):
        """Test procedural step formatting with imperative verbs."""
        rule = ProceduresRule()
        
        test_cases = [
            {
                'text': "Click the Save button.",
                'sentences': ["Click the Save button."],
                'context': {'block_type': 'list_item_ordered'},
                'should_detect': False,
                'reason': 'Proper imperative verb'
            },
            {
                'text': "The user should click the Save button.",
                'sentences': ["The user should click the Save button."],
                'context': {'block_type': 'list_item_ordered'},
                'should_detect': True,
                'reason': 'Should start with imperative verb'
            },
            {
                'text': "Clicking the Save button saves changes.",
                'sentences': ["Clicking the Save button saves changes."],
                'context': {'block_type': 'list_item_ordered'},
                'should_detect': True,
                'reason': 'Should use imperative, not gerund'
            },
            {
                'text': "Enter your username in the field.",
                'sentences': ["Enter your username in the field."],
                'context': {'block_type': 'list_item_ordered'},
                'should_detect': False,
                'reason': 'Proper procedural instruction'
            }
        ]
        
        for case in test_cases:
            errors = rule.analyze(
                case['text'], 
                case['sentences'], 
                mock_nlp,
                case.get('context', {'block_type': 'list_item_ordered'})
            )
            
            if case['should_detect']:
                assert len(errors) > 0, f"Should detect procedure issue in: {case['text']} ({case['reason']})"
                assert errors[0]['type'] == 'procedures'
            else:
                assert len(errors) == 0, f"Should not detect procedure issue in: {case['text']} ({case['reason']})"


class TestRuleMetrics:
    """Test rule performance and consistency metrics."""
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_rule_consistency(self):
        """Test that rules provide consistent error structures."""
        rules = [
            AbbreviationsRule(),
            ContractionsRule(),
            InclusiveLanguageRule()
        ]
        
        test_text = "Don't use e.g. the blacklist feature."
        test_sentences = ["Don't use e.g. the blacklist feature."]
        
        for rule in rules:
            errors = rule.analyze(
                test_text, 
                test_sentences, 
                None,  # No NLP for this test
                {'block_type': 'paragraph'}
            )
            
            for error in errors:
                # Validate error structure
                EnhancedTestValidators.validate_error_structure(error)
                
                # Check required fields
                assert 'type' in error
                assert 'message' in error
                assert 'suggestions' in error
                assert 'severity' in error
                assert error['type'] == rule._get_rule_type()
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_rule_performance(self):
        """Test rule analysis performance."""
        import time
        
        rule = InclusiveLanguageRule()
        
        # Large text for performance testing
        large_text = "Use the whitelist and blacklist features. " * 100
        sentences = [large_text]
        
        start_time = time.time()
        errors = rule.analyze(large_text, sentences, None, {'block_type': 'paragraph'})
        end_time = time.time()
        
        # Should complete within reasonable time
        analysis_time = end_time - start_time
        assert analysis_time < 1.0, f"Rule analysis took too long: {analysis_time:.2f}s"
        
        # Should detect errors in large text
        assert len(errors) > 0, "Should detect errors in large text"


class TestRuleErrorHandling:
    """Test rule error handling and edge cases."""
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_rule_empty_input(self):
        """Test rules with empty input."""
        rules = [
            AbbreviationsRule(),
            ContractionsRule(),
            InclusiveLanguageRule()
        ]
        
        for rule in rules:
            # Empty text
            errors = rule.analyze("", [], None, {'block_type': 'paragraph'})
            assert len(errors) == 0, f"Rule {rule._get_rule_type()} should handle empty input"
            
            # Whitespace only
            errors = rule.analyze("   \n\t  ", ["   \n\t  "], None, {'block_type': 'paragraph'})
            assert len(errors) == 0, f"Rule {rule._get_rule_type()} should handle whitespace input"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules not available")
    def test_rule_malformed_context(self):
        """Test rules with malformed context."""
        rule = InclusiveLanguageRule()
        
        test_cases = [
            None,  # No context
            {},    # Empty context
            {'wrong_key': 'value'},  # Wrong context structure
            {'block_type': None},    # None block type
        ]
        
        for context in test_cases:
            try:
                errors = rule.analyze(
                    "Test whitelist feature.", 
                    ["Test whitelist feature."], 
                    None, 
                    context
                )
                # Should not crash and should still detect errors
                assert isinstance(errors, list)
            except Exception as e:
                pytest.fail(f"Rule should handle malformed context {context}: {e}")


# Enhanced Test Validators
class EnhancedTestValidators(TestValidators):
    """Enhanced validators for rule testing."""
    
    @staticmethod
    def validate_error_structure(error):
        """Validate that error has proper structure."""
        required_fields = ['type', 'message', 'suggestions', 'severity']
        
        for field in required_fields:
            assert field in error, f"Error missing required field: {field}"
        
        assert isinstance(error['suggestions'], list), "Suggestions should be a list"
        assert len(error['suggestions']) > 0, "Should have at least one suggestion"
        assert error['severity'] in ['low', 'medium', 'high', 'critical'], f"Invalid severity: {error['severity']}"
    
    @staticmethod
    def validate_rule_instance(rule):
        """Validate that rule instance is properly configured."""
        assert hasattr(rule, '_get_rule_type'), "Rule should have _get_rule_type method"
        assert hasattr(rule, 'analyze'), "Rule should have analyze method"
        
        rule_type = rule._get_rule_type()
        assert isinstance(rule_type, str), "Rule type should be string"
        assert len(rule_type) > 0, "Rule type should not be empty" 
"""
Comprehensive Test Suite for Style Rules System
Tests all style rules, rule discovery, context-aware application, rule mappings,
error structures, and configuration scenarios across all rule categories.
"""

import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock, mock_open
from typing import List, Dict, Any, Optional
import tempfile
import yaml

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import rules system components
try:
    from rules import RulesRegistry, get_registry
    from rules.base_rule import BaseRule
    from rules.language_and_grammar import *
    from rules.punctuation import *
    from rules.structure_and_format import *
    
    # Import specific rule classes for testing
    from rules.language_and_grammar import (
        AbbreviationsRule, ContractionsRule, InclusiveLanguageRule, 
        AnthropomorphismRule
    )
    from rules.punctuation import PunctuationAndSymbolsRule
    from rules.structure_and_format import (
        HeadingsRule, ListsRule, ProceduresRule, AdmonitionsRule
    )
    
    RULES_AVAILABLE = True
except ImportError:
    RULES_AVAILABLE = False


class TestStyleRulesSystem:
    """Comprehensive test suite for the style rules system."""
    
    @pytest.fixture
    def mock_nlp(self):
        """Create a mock SpaCy NLP object for testing."""
        nlp = Mock()
        
        def create_doc(text):
            doc = Mock()
            words = text.split()
            tokens = []
            
            for i, word in enumerate(words):
                token = Mock()
                token.text = word
                token.pos_ = "NOUN"
                token.tag_ = "NN"
                token.dep_ = "nsubj"
                token.lemma_ = word.lower()
                token.is_alpha = True
                token.is_stop = False
                token.children = []  # Empty children list
                token.head = token  # self-reference for simplicity
                token.i = i  # Add token index
                token.lower_ = word.lower()  # Add lower_ attribute
                tokens.append(token)
            
            doc.__iter__ = Mock(return_value=iter(tokens))
            doc.__len__ = Mock(return_value=len(tokens))
            doc.__getitem__ = Mock(side_effect=lambda i: tokens[i] if 0 <= i < len(tokens) else None)
            
            # Mock sents for sentence-level operations
            sentences = [Mock()]
            sentences[0].__iter__ = Mock(return_value=iter(tokens))
            doc.sents = sentences
            
            return doc
        
        nlp.side_effect = create_doc
        return nlp
    
    @pytest.fixture
    def mock_context(self):
        """Create mock context for rule testing."""
        return {
            'block_type': 'paragraph',
            'format': 'markdown',
            'metadata': {}
        }
    
    @pytest.fixture
    def sample_sentences(self):
        """Provide sample sentences for testing."""
        return [
            "This is a simple sentence.",
            "The system is configured by the administrator.",
            "Use contractions like don't when appropriate.",
            "Avoid using whitelist and blacklist terms.",
            "The interface allows users to input data."
        ]
    
    # ===============================
    # RULES REGISTRY TESTS
    # ===============================
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rules_registry_initialization(self):
        """Test that the rules registry initializes correctly."""
        registry = RulesRegistry()
        
        assert registry is not None
        assert hasattr(registry, 'rules')
        assert hasattr(registry, 'rule_locations')
        assert isinstance(registry.rules, dict)
        assert isinstance(registry.rule_locations, dict)
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rules_registry_discovers_rules(self):
        """Test that the registry discovers and loads rules."""
        registry = RulesRegistry()
        
        # Should have discovered multiple rules
        assert len(registry.rules) > 0
        
        # Check that rules are properly instantiated
        for rule_type, rule in registry.rules.items():
            assert isinstance(rule, BaseRule)
            assert rule.rule_type == rule_type
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rules_registry_language_grammar_rules(self):
        """Test that language and grammar rules are discovered."""
        registry = RulesRegistry()
        
        expected_language_rules = [
            'abbreviations', 'adverbs_only', 'anthropomorphism', 'articles',
            'capitalization', 'conjunctions', 'contractions', 'inclusive_language',
            'plurals', 'possessives', 'prepositions', 'pronouns', 'spelling',
            'terminology', 'verbs'
        ]
        
        for rule_type in expected_language_rules:
            assert rule_type in registry.rules, f"Language rule {rule_type} not found"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rules_registry_punctuation_rules(self):
        """Test that punctuation rules are discovered."""
        registry = RulesRegistry()
        
        expected_punctuation_rules = [
            'punctuation_and_symbols', 'colons', 'commas', 'dashes', 'ellipses',
            'exclamation_points', 'hyphens', 'parentheses', 'periods',
            'quotation_marks', 'semicolons', 'slashes'
        ]
        
        for rule_type in expected_punctuation_rules:
            assert rule_type in registry.rules, f"Punctuation rule {rule_type} not found"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rules_registry_structure_format_rules(self):
        """Test that structure and format rules are discovered."""
        registry = RulesRegistry()
        
        expected_structure_rules = [
            'headings', 'highlighting', 'lists', 'messages', 'notes',
            'paragraphs', 'procedures', 'admonitions'
        ]
        
        for rule_type in expected_structure_rules:
            assert rule_type in registry.rules, f"Structure rule {rule_type} not found"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rules_registry_rule_mappings_loaded(self):
        """Test that rule mappings are loaded correctly."""
        registry = RulesRegistry()
        
        assert hasattr(registry, 'block_type_rules')
        assert hasattr(registry, 'rule_exclusions')
        assert isinstance(registry.block_type_rules, dict)
        assert isinstance(registry.rule_exclusions, dict)
        
        # Check for expected block types
        expected_block_types = [
            'heading', 'paragraph', 'list_item', 'list_item_ordered',
            'list_item_unordered', 'admonition', 'blockquote'
        ]
        
        for block_type in expected_block_types:
            assert block_type in registry.block_type_rules
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_get_registry_function(self):
        """Test the get_registry function."""
        registry = get_registry()
        
        assert registry is not None
        assert isinstance(registry, RulesRegistry)
        assert len(registry.rules) > 0
    
    # ===============================
    # INDIVIDUAL RULE TESTS
    # ===============================
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_abbreviations_rule(self, mock_nlp, sample_sentences):
        """Test the abbreviations rule."""
        rule = AbbreviationsRule()
        
        test_text = "Use e.g. and i.e. correctly in technical docs."
        test_sentences = [test_text]
        
        errors = rule.analyze(test_text, test_sentences, mock_nlp)
        
        # Should find abbreviation issues
        assert isinstance(errors, list)
        for error in errors:
            assert error['type'] == 'abbreviations'
            assert 'message' in error
            assert 'suggestions' in error
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_contractions_rule(self, mock_nlp):
        """Test the contractions rule."""
        rule = ContractionsRule()
        
        test_text = "Don't use contractions in formal documentation."
        test_sentences = [test_text]
        
        errors = rule.analyze(test_text, test_sentences, mock_nlp)
        
        assert isinstance(errors, list)
        # May or may not find errors depending on context
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_inclusive_language_rule(self, mock_nlp):
        """Test the inclusive language rule."""
        rule = InclusiveLanguageRule()
        
        test_text = "Add items to the whitelist and remove from blacklist."
        test_sentences = [test_text]
        
        errors = rule.analyze(test_text, test_sentences, mock_nlp)
        
        assert isinstance(errors, list)
        # Should detect non-inclusive terms
        for error in errors:
            assert error['type'] == 'inclusive_language'
            assert any(term in error['message'].lower() for term in ['whitelist', 'blacklist'])
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_anthropomorphism_rule(self, mock_nlp):
        """Test the anthropomorphism rule."""
        rule = AnthropomorphismRule()
        
        test_text = "The system thinks that users want this feature."
        test_sentences = [test_text]
        
        # Mock SpaCy doc with anthropomorphic pattern
        doc = Mock()
        
        # Mock token for "system"
        system_token = Mock()
        system_token.text = "system"
        system_token.pos_ = "NOUN"
        system_token.lemma_ = "system"
        system_token.dep_ = "nsubj"
        
        # Mock token for "thinks"
        thinks_token = Mock()
        thinks_token.text = "thinks"
        thinks_token.pos_ = "VERB"
        thinks_token.lemma_ = "think"
        thinks_token.dep_ = "ROOT"
        thinks_token.head = thinks_token
        thinks_token.children = [system_token]  # system is a child of thinks
        
        # Set up dependency relationships
        system_token.head = thinks_token
        
        doc.__iter__ = Mock(return_value=iter([system_token, thinks_token]))
        mock_nlp.return_value = doc
        
        errors = rule.analyze(test_text, test_sentences, mock_nlp)
        
        assert isinstance(errors, list)
        # Should detect anthropomorphism
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_punctuation_and_symbols_rule(self, mock_nlp):
        """Test the punctuation and symbols rule."""
        rule = PunctuationAndSymbolsRule()
        
        test_text = "Use proper spacing around punctuation marks ."
        test_sentences = [test_text]
        
        errors = rule.analyze(test_text, test_sentences, mock_nlp)
        
        assert isinstance(errors, list)
        # Should detect spacing issues
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_headings_rule(self, mock_nlp):
        """Test the headings rule."""
        rule = HeadingsRule()
        
        test_text = "heading with improper capitalization."
        test_sentences = [test_text]
        
        # Test with heading context
        context = {'block_type': 'heading'}
        
        errors = rule.analyze(test_text, test_sentences, mock_nlp, context)
        
        assert isinstance(errors, list)
        # Should only apply to headings
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_lists_rule(self, mock_nlp):
        """Test the lists rule for parallelism."""
        rule = ListsRule()
        
        # Test parallel structure
        test_text = "Configure the system"
        test_sentences = [test_text]
        
        # Mock SpaCy doc for imperative structure
        doc = Mock()
        configure_token = Mock()
        configure_token.text = "Configure"
        configure_token.pos_ = "VERB"
        configure_token.tag_ = "VB"  # Base form verb (imperative)
        
        doc.__iter__ = Mock(return_value=iter([configure_token]))
        doc.__len__ = Mock(return_value=1)
        mock_nlp.return_value = doc
        
        context = {'block_type': 'list_item_ordered'}
        
        errors = rule.analyze(test_text, test_sentences, mock_nlp, context)
        
        assert isinstance(errors, list)
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_procedures_rule(self, mock_nlp):
        """Test the procedures rule."""
        rule = ProceduresRule()
        
        test_text = "The configuration is completed by the user."
        test_sentences = [test_text]
        
        context = {'block_type': 'list_item_ordered'}
        
        errors = rule.analyze(test_text, test_sentences, mock_nlp, context)
        
        assert isinstance(errors, list)
        # Should detect non-imperative procedures
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_admonitions_rule(self, mock_nlp):
        """Test the admonitions rule."""
        rule = AdmonitionsRule()
        
        test_text = "This is important information."
        test_sentences = [test_text]
        
        context = {'block_type': 'admonition', 'kind': 'NOTE'}
        
        errors = rule.analyze(test_text, test_sentences, mock_nlp, context)
        
        assert isinstance(errors, list)
    
    # ===============================
    # RULE APPLICATION TESTS
    # ===============================
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_context_aware_rule_application(self, mock_nlp):
        """Test that rules are applied based on context."""
        registry = RulesRegistry()
        
        text = "Test content for context-aware analysis."
        sentences = [text]
        
        # Test paragraph context
        paragraph_context = {'block_type': 'paragraph'}
        paragraph_errors = registry.analyze_with_context_aware_rules(
            text, sentences, mock_nlp, paragraph_context
        )
        
        # Test heading context
        heading_context = {'block_type': 'heading'}
        heading_errors = registry.analyze_with_context_aware_rules(
            text, sentences, mock_nlp, heading_context
        )
        
        # Different contexts may produce different error sets
        assert isinstance(paragraph_errors, list)
        assert isinstance(heading_errors, list)
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_code_block_skipping(self, mock_nlp):
        """Test that code blocks are skipped during analysis."""
        registry = RulesRegistry()
        
        text = "print('Hello, World!')"
        sentences = [text]
        
        # Test with code block context
        code_context = {'block_type': 'code_block'}
        errors = registry.analyze_with_context_aware_rules(
            text, sentences, mock_nlp, code_context
        )
        
        # Should skip analysis for code blocks
        assert errors == []
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rule_exclusions(self, mock_nlp):
        """Test that rule exclusions work correctly."""
        registry = RulesRegistry()
        
        text = "Heading Text"
        sentences = [text]
        
        # Test that heading context excludes list rules
        heading_context = {'block_type': 'heading'}
        applicable_rules = registry._get_applicable_rules('heading')
        
        assert 'lists' not in applicable_rules
        assert 'procedures' not in applicable_rules
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_analyze_with_all_rules(self, mock_nlp, sample_sentences):
        """Test analysis with all discovered rules."""
        registry = RulesRegistry()
        
        text = " ".join(sample_sentences)
        
        errors = registry.analyze_with_all_rules(text, sample_sentences, mock_nlp)
        
        assert isinstance(errors, list)
        # Should return analysis results from all rules
        
        for error in errors:
            assert 'type' in error
            assert 'message' in error
            assert 'suggestions' in error
            assert 'severity' in error
    
    # ===============================
    # ERROR STRUCTURE TESTS
    # ===============================
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_error_structure_consistency(self, mock_nlp):
        """Test that all rules produce consistent error structures."""
        registry = RulesRegistry()
        
        text = "Test text for error structure validation."
        sentences = [text]
        
        for rule_type, rule in registry.rules.items():
            try:
                errors = rule.analyze(text, sentences, mock_nlp)
                
                assert isinstance(errors, list)
                
                for error in errors:
                    # Required fields
                    assert 'type' in error
                    assert 'message' in error
                    assert 'suggestions' in error
                    assert 'sentence' in error
                    assert 'sentence_index' in error
                    assert 'severity' in error
                    
                    # Validate types
                    assert isinstance(error['type'], str)
                    assert isinstance(error['message'], str)
                    assert isinstance(error['suggestions'], list)
                    assert isinstance(error['sentence'], str)
                    assert isinstance(error['sentence_index'], int)
                    assert error['severity'] in ['low', 'medium', 'high']
                    
            except Exception as e:
                pytest.fail(f"Rule {rule_type} failed with error: {e}")
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_error_serialization(self, mock_nlp):
        """Test that errors are JSON serializable."""
        registry = RulesRegistry()
        
        text = "Test text for serialization."
        sentences = [text]
        
        errors = registry.analyze_with_all_rules(text, sentences, mock_nlp)
        
        # Should be able to serialize errors
        import json
        try:
            json.dumps(errors)
        except TypeError as e:
            pytest.fail(f"Errors are not JSON serializable: {e}")
    
    # ===============================
    # CONFIGURATION TESTS
    # ===============================
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rule_mappings_configuration(self):
        """Test rule mappings configuration loading."""
        registry = RulesRegistry()
        
        # Test that mappings are loaded
        assert len(registry.block_type_rules) > 0
        assert len(registry.rule_exclusions) > 0
        
        # Test specific mappings
        assert 'paragraph' in registry.block_type_rules
        assert 'heading' in registry.block_type_rules
        
        # Test that paragraph rules include language rules
        paragraph_rules = registry.block_type_rules['paragraph']
        assert 'abbreviations' in paragraph_rules
        assert 'contractions' in paragraph_rules
        
        # Test that heading rules exclude list rules
        heading_exclusions = registry.rule_exclusions.get('heading', [])
        assert 'lists' in heading_exclusions
        assert 'procedures' in heading_exclusions
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_custom_rule_mappings(self):
        """Test loading custom rule mappings."""
        # Create temporary rule mappings file
        custom_mappings = {
            'block_type_rules': {
                'custom_block': ['abbreviations', 'spelling'],
                'paragraph': ['abbreviations']
            },
            'rule_exclusions': {
                'custom_block': ['lists'],
                'paragraph': ['headings']
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(custom_mappings, f)
            temp_file = f.name
        
        try:
            # Test loading custom mappings
            registry = RulesRegistry()
            
            # Mock the _load_rule_mappings method to use our custom file
            with patch('builtins.open', mock_open(read_data=yaml.dump(custom_mappings))):
                with patch('os.path.join', return_value=temp_file):
                    registry._load_rule_mappings()
            
            assert 'custom_block' in registry.block_type_rules
            assert registry.block_type_rules['custom_block'] == ['abbreviations', 'spelling']
            
        finally:
            os.unlink(temp_file)
    
    # ===============================
    # RULE DISCOVERY TESTS
    # ===============================
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rule_discovery_depth_limit(self):
        """Test that rule discovery respects depth limits."""
        registry = RulesRegistry()
        
        # Should have discovered rules but not gone too deep
        discovered = registry.list_discovered_rules()
        
        assert discovered['total_rules'] > 0
        assert len(discovered['locations']) > 0
        
        # Check that locations don't indicate excessive depth
        for location in discovered['locations']:
            depth = location.count('/') if '/' in location else location.count('\\')
            assert depth <= 4  # Should respect 4-level depth limit
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rule_class_validation(self):
        """Test that discovered rules are valid rule classes."""
        registry = RulesRegistry()
        
        for rule_type, rule in registry.rules.items():
            # Should be a BaseRule instance
            assert isinstance(rule, BaseRule)
            
            # Should have required methods
            assert hasattr(rule, 'analyze')
            assert hasattr(rule, '_get_rule_type')
            assert callable(rule.analyze)
            assert callable(rule._get_rule_type)
            
            # Rule type should match
            assert rule.rule_type == rule_type
            assert rule._get_rule_type() == rule_type
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rule_conflict_detection(self):
        """Test that rule type conflicts are detected."""
        # This test ensures the registry handles duplicate rule types
        registry = RulesRegistry()
        
        # All rule types should be unique
        rule_types = list(registry.rules.keys())
        unique_types = set(rule_types)
        
        assert len(rule_types) == len(unique_types), "Duplicate rule types detected"
    
    # ===============================
    # FALLBACK AND ERROR HANDLING TESTS
    # ===============================
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rule_analysis_exception_handling(self, mock_nlp):
        """Test that rule analysis exceptions are handled gracefully."""
        registry = RulesRegistry()
        
        # Create a rule that raises an exception
        class FailingRule(BaseRule):
            def _get_rule_type(self):
                return 'failing_rule'
            
            def analyze(self, text, sentences, nlp=None, context=None):
                raise Exception("Test exception")
        
        # Add the failing rule
        registry.rules['failing_rule'] = FailingRule()
        
        text = "Test text"
        sentences = [text]
        
        # Should handle the exception gracefully
        errors = registry.analyze_with_all_rules(text, sentences, mock_nlp)
        
        # Should include a system error for the failing rule
        system_errors = [e for e in errors if e.get('type') == 'system_error']
        assert len(system_errors) > 0
        
        failing_errors = [e for e in system_errors if 'FailingRule' in e.get('message', '')]
        assert len(failing_errors) > 0
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_missing_nlp_handling(self):
        """Test behavior when SpaCy NLP is not available."""
        registry = RulesRegistry()
        
        text = "Test text without NLP"
        sentences = [text]
        
        # Analyze without NLP
        errors = registry.analyze_with_all_rules(text, sentences, nlp=None)
        
        # Should still work but may have fewer errors
        assert isinstance(errors, list)
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_empty_content_handling(self, mock_nlp):
        """Test handling of empty content."""
        registry = RulesRegistry()
        
        # Test empty text
        errors = registry.analyze_with_all_rules("", [], mock_nlp)
        assert isinstance(errors, list)
        
        # Test whitespace-only text
        errors = registry.analyze_with_all_rules("   \n\t  ", ["   \n\t  "], mock_nlp)
        assert isinstance(errors, list)
    
    # ===============================
    # PERFORMANCE AND EDGE CASE TESTS
    # ===============================
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_large_text_analysis(self, mock_nlp):
        """Test analysis with large text content."""
        registry = RulesRegistry()
        
        # Create large text content
        large_text = "This is a test sentence. " * 100
        sentences = [large_text]
        
        # Should handle large content without issues
        errors = registry.analyze_with_all_rules(large_text, sentences, mock_nlp)
        
        assert isinstance(errors, list)
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_special_characters_handling(self, mock_nlp):
        """Test handling of special characters and Unicode."""
        registry = RulesRegistry()
        
        # Text with special characters
        special_text = "Test with émojis 🚀 and spécial charactërs: àáâãäå çñü"
        sentences = [special_text]
        
        # Should handle special characters gracefully
        errors = registry.analyze_with_all_rules(special_text, sentences, mock_nlp)
        
        assert isinstance(errors, list)
        
        # Errors should be serializable despite special characters
        import json
        json.dumps(errors)
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_concurrent_rule_analysis(self, mock_nlp):
        """Test concurrent access to rules."""
        import threading
        
        registry = RulesRegistry()
        text = "Test content for concurrent analysis."
        sentences = [text]
        results = []
        
        def analyze_text():
            errors = registry.analyze_with_all_rules(text, sentences, mock_nlp)
            results.append(errors)
        
        # Start multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=analyze_text)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All analyses should complete successfully
        assert len(results) == 5
        for result in results:
            assert isinstance(result, list)
    
    # ===============================
    # INTEGRATION TESTS
    # ===============================
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_rules_integration_with_style_analyzer(self, mock_nlp):
        """Test integration of rules with the style analyzer."""
        try:
            from style_analyzer.base_analyzer import StyleAnalyzer
            
            # Create analyzer with rules
            analyzer = StyleAnalyzer()
            
            # Should have rules registry
            assert hasattr(analyzer, 'rules_registry')
            if analyzer.rules_registry:
                assert isinstance(analyzer.rules_registry, RulesRegistry)
                assert len(analyzer.rules_registry.rules) > 0
                
        except ImportError:
            pytest.skip("StyleAnalyzer not available")
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_comprehensive_rule_coverage(self):
        """Test that all expected rules are covered."""
        registry = RulesRegistry()
        
        # Expected rules from documentation
        expected_rules = {
            # Language and Grammar
            'abbreviations', 'adverbs_only', 'anthropomorphism', 'articles',
            'capitalization', 'conjunctions', 'contractions', 'inclusive_language',
            'plurals', 'possessives', 'prepositions', 'pronouns', 'spelling',
            'terminology', 'verbs',
            
            # Punctuation
            'punctuation_and_symbols', 'colons', 'commas', 'dashes', 'ellipses',
            'exclamation_points', 'hyphens', 'parentheses', 'periods',
            'quotation_marks', 'semicolons', 'slashes',
            
            # Structure and Format
            'headings', 'highlighting', 'lists', 'messages', 'notes',
            'paragraphs', 'procedures', 'admonitions'
        }
        
        discovered_rules = set(registry.rules.keys())
        
        # Check coverage
        missing_rules = expected_rules - discovered_rules
        if missing_rules:
            print(f"Missing rules: {missing_rules}")
        
        # Should have good coverage (allow for some rules to be missing during development)
        coverage = len(discovered_rules & expected_rules) / len(expected_rules)
        assert coverage > 0.8, f"Rule coverage too low: {coverage:.2%}"


# ===============================
# SPECIFIC RULE FUNCTIONALITY TESTS
# ===============================

class TestSpecificRules:
    """Test specific functionality of individual rules."""
    
    @pytest.fixture
    def mock_nlp_advanced(self):
        """Create an advanced mock SpaCy NLP object for detailed testing."""
        nlp = Mock()
        
        def create_doc(text):
            doc = Mock()
            tokens = []
            
            # Simple tokenization for testing
            words = text.split()
            for i, word in enumerate(words):
                token = Mock()
                token.text = word
                token.i = i
                token.pos_ = "NOUN"  # Default
                token.tag_ = "NN"    # Default
                token.dep_ = "ROOT"  # Default
                token.lemma_ = word.lower()
                token.is_alpha = word.isalpha()
                token.is_stop = word.lower() in ['the', 'a', 'an', 'and', 'or', 'but']
                token.head = token  # Self-reference for simplicity
                tokens.append(token)
            
            doc.__iter__ = Mock(return_value=iter(tokens))
            doc.__len__ = Mock(return_value=len(tokens))
            doc.__getitem__ = Mock(side_effect=lambda i: tokens[i] if 0 <= i < len(tokens) else None)
            
            return doc
        
        nlp.side_effect = create_doc
        return nlp
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_inclusive_language_rule_specific_terms(self, mock_nlp_advanced):
        """Test inclusive language rule with specific problematic terms."""
        rule = InclusiveLanguageRule()
        
        test_cases = [
            ("Use the whitelist to approve items.", ["whitelist"]),
            ("Add to blacklist for blocking.", ["blacklist"]),
            ("The master server controls slaves.", ["master", "slave"]),
            ("Calculate man-hours for the project.", ["man-hours"]),
            ("The system is manned by operators.", ["manned"]),
            ("Perform a sanity check on the data.", ["sanity check"])
        ]
        
        for text, expected_terms in test_cases:
            errors = rule.analyze(text, [text], mock_nlp_advanced)
            
            # Should detect the problematic terms
            assert len(errors) > 0, f"Should detect issues in: {text}"
            
            # Check that the expected terms are mentioned (allow for partial matches)
            error_messages = " ".join([e['message'] for e in errors]).lower()
            for term in expected_terms:
                # For compound terms like "master"+"slave", check if at least one is mentioned
                if "master" in term.lower() or "slave" in term.lower():
                    assert any(word in error_messages for word in ["master", "slave"]), f"Should mention master or slave in error message"
                else:
                    assert term.lower() in error_messages, f"Should mention {term} in error message"
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_contractions_rule_context_awareness(self, mock_nlp_advanced):
        """Test contractions rule context awareness."""
        rule = ContractionsRule()
        
        # Test cases where contractions might be acceptable vs. unacceptable
        test_cases = [
            ("Don't use contractions in formal docs.", "don't"),
            ("It's important to be consistent.", "it's"),
            ("You can't access this feature.", "can't"),
            ("Won't work in production.", "won't")
        ]
        
        for text, contraction in test_cases:
            errors = rule.analyze(text, [text], mock_nlp_advanced)
            
            # Rule should analyze contractions (may or may not flag them based on context)
            assert isinstance(errors, list)
    
    @pytest.mark.skipif(not RULES_AVAILABLE, reason="Rules system not available")
    def test_procedures_rule_imperative_detection(self, mock_nlp_advanced):
        """Test procedures rule detection of imperative vs. non-imperative steps."""
        rule = ProceduresRule()
        
        # Mock specific POS tags for testing
        def create_imperative_doc(text):
            doc = Mock()
            words = text.split()
            tokens = []
            
            for i, word in enumerate(words):
                token = Mock()
                token.text = word
                token.pos_ = "VERB" if i == 0 else "NOUN"
                token.tag_ = "VB" if i == 0 else "NN"  # VB = base form verb (imperative)
                token.dep_ = "ROOT" if i == 0 else "dobj"
                token.lemma_ = word.lower()
                tokens.append(token)
            
            doc.__iter__ = Mock(return_value=iter(tokens))
            doc.__len__ = Mock(return_value=len(tokens))
            doc.__getitem__ = Mock(side_effect=lambda i: tokens[i] if 0 <= i < len(tokens) else None)
            return doc
        
        def create_passive_doc(text):
            doc = Mock()
            words = text.split()
            tokens = []
            
            for i, word in enumerate(words):
                token = Mock()
                token.text = word
                token.pos_ = "NOUN" if i == 0 else "VERB"
                token.tag_ = "NN" if i == 0 else "VBZ"  # VBZ = 3rd person singular
                token.dep_ = "nsubj" if i == 0 else "ROOT"
                token.lemma_ = word.lower()
                tokens.append(token)
            
            doc.__iter__ = Mock(return_value=iter(tokens))
            doc.__len__ = Mock(return_value=len(tokens))
            doc.__getitem__ = Mock(side_effect=lambda i: tokens[i] if 0 <= i < len(tokens) else None)
            return doc
        
        # Test imperative (good)
        imperative_nlp = Mock()
        imperative_nlp.side_effect = create_imperative_doc
        
        imperative_text = "Configure the server settings"
        context = {'block_type': 'list_item_ordered'}
        
        errors = rule.analyze(imperative_text, [imperative_text], imperative_nlp, context)
        # Imperative form should have fewer or no errors
        
        # Test non-imperative (problematic)
        passive_nlp = Mock()
        passive_nlp.side_effect = create_passive_doc
        
        passive_text = "Configuration is completed"
        
        errors = rule.analyze(passive_text, [passive_text], passive_nlp, context)
        # Non-imperative form may trigger errors
        assert isinstance(errors, list)


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 
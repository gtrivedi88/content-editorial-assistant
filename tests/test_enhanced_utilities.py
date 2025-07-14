"""
Enhanced Test Utilities
Advanced utilities for comprehensive testing of all components.
Provides enhanced mocking, data generation, and validation capabilities.
"""

import pytest
import os
import sys
from unittest.mock import Mock, MagicMock, patch
from typing import List, Dict, Any, Optional, Union
import tempfile
import json
import yaml
from datetime import datetime
import random
import string

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_utils import TestConfig, TestFixtures, TestValidators


class EnhancedTestMockFactory:
    """Enhanced mock factory for comprehensive component testing."""
    
    @staticmethod
    def create_mock_rule(rule_type: str, errors: Optional[List[Dict]] = None, 
                        severity: str = 'medium') -> Mock:
        """Create a comprehensive mock rule instance."""
        mock_rule = Mock()
        mock_rule._get_rule_type.return_value = rule_type
        mock_rule.rule_type = rule_type
        mock_rule.severity_levels = ['low', 'medium', 'high', 'critical']
        
        # Default errors if none provided
        if errors is None:
            errors = [{
                'type': rule_type,
                'message': f'Test {rule_type} violation detected',
                'suggestions': [f'Fix {rule_type} issue'],
                'sentence': 'Test sentence',
                'sentence_index': 0,
                'severity': severity
            }]
        
        mock_rule.analyze.return_value = errors
        
        # Add serialization support
        def make_serializable(data):
            if isinstance(data, dict):
                return {k: v for k, v in data.items() if v is not None}
            return data
        
        mock_rule._make_serializable.side_effect = make_serializable
        
        return mock_rule
    
    @staticmethod
    def create_mock_detector(detector_type: str, 
                           detections: Optional[List] = None) -> Mock:
        """Create a comprehensive mock ambiguity detector."""
        mock_detector = Mock()
        mock_detector.enabled = True
        mock_detector.detector_type = detector_type
        
        # Create mock detections if none provided
        if detections is None:
            mock_detection = Mock()
            mock_detection.to_error_dict.return_value = {
                'type': 'ambiguity',
                'subtype': detector_type,
                'message': f'Test {detector_type} detected',
                'suggestions': [f'Resolve {detector_type}'],
                'severity': 'medium',
                'confidence': 0.85
            }
            detections = [mock_detection]
        
        mock_detector.detect.return_value = detections
        mock_detector.configure = Mock()
        mock_detector.enable = Mock()
        mock_detector.disable = Mock()
        mock_detector.is_enabled.return_value = True
        
        return mock_detector
    
    @staticmethod
    def create_mock_parser(format_type: str, blocks: Optional[List] = None) -> Mock:
        """Create a comprehensive mock document parser."""
        mock_parser = Mock()
        mock_parser.format_type = format_type
        
        # Create default blocks if none provided
        if blocks is None:
            blocks = [
                {
                    'type': 'heading',
                    'content': 'Test Heading',
                    'level': 1,
                    'start_line': 1,
                    'end_line': 1
                },
                {
                    'type': 'paragraph',
                    'content': 'Test paragraph content.',
                    'start_line': 3,
                    'end_line': 3
                }
            ]
        
        # Mock parse result
        mock_result = Mock()
        mock_result.success = True
        mock_result.blocks = blocks
        mock_result.format = format_type
        mock_result.metadata = {'title': 'Test Document'}
        mock_result.errors = []
        
        mock_parser.parse.return_value = mock_result
        
        return mock_parser
    
    @staticmethod
    def create_mock_nlp_with_dependencies() -> Mock:
        """Create a sophisticated SpaCy NLP mock with dependency parsing."""
        def create_advanced_doc(text: str):
            doc = Mock()
            words = text.split()
            tokens = []
            
            for i, word in enumerate(words):
                token = Mock()
                token.text = word
                token.lemma_ = word.lower()
                token.lower_ = word.lower()
                token.i = i
                token.idx = sum(len(w) + 1 for w in words[:i])  # Character position
                
                # Advanced POS tagging
                token.pos_ = EnhancedTestMockFactory._get_advanced_pos(word, i, words)
                token.tag_ = EnhancedTestMockFactory._get_advanced_tag(word, token.pos_)
                
                # Dependency parsing
                token.dep_ = EnhancedTestMockFactory._get_dependency(word, i, words)
                token.head = tokens[0] if tokens and i > 0 else token
                
                # Morphological features
                token.morph = EnhancedTestMockFactory._get_morph_features(word, token.pos_)
                
                # Boolean properties
                token.is_alpha = word.isalpha()
                token.is_digit = word.isdigit()
                token.is_punct = word in '.,!?;:'
                token.is_space = word.isspace()
                token.is_stop = word.lower() in ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at']
                token.like_num = word.isdigit() or word.lower() in ['one', 'two', 'three']
                token.like_url = 'http' in word.lower() or 'www' in word.lower()
                token.like_email = '@' in word
                
                # Shape and case
                token.shape_ = ''.join('X' if c.isupper() else 'x' if c.islower() else 'd' if c.isdigit() else c for c in word)
                token.is_upper = word.isupper()
                token.is_lower = word.islower()
                token.is_title = word.istitle()
                
                # Children (simplified)
                token.children = []
                
                tokens.append(token)
            
            # Set up token relationships
            for i, token in enumerate(tokens):
                if i > 0:
                    token.head = tokens[0]  # Simplified: first token is head
                    tokens[0].children.append(token)
            
            # Document properties
            doc.__iter__ = Mock(return_value=iter(tokens))
            doc.__len__ = Mock(return_value=len(tokens))
            doc.__getitem__ = Mock(side_effect=lambda x: tokens[x] if 0 <= x < len(tokens) else None)
            
            # Sentences
            sentence = Mock()
            sentence.__iter__ = Mock(return_value=iter(tokens))
            sentence.start = 0
            sentence.end = len(tokens)
            sentence.text = text
            doc.sents = [sentence]
            
            # Named entities (simplified)
            doc.ents = []
            
            # Text properties
            doc.text = text
            doc.text_with_ws = text
            
            return doc
        
        nlp = Mock()
        nlp.side_effect = create_advanced_doc
        nlp.pipe = Mock(side_effect=lambda texts: [create_advanced_doc(text) for text in texts])
        
        return nlp
    
    @staticmethod
    def _get_advanced_pos(word: str, position: int, words: List[str]) -> str:
        """Get advanced POS tag based on context."""
        word_lower = word.lower()
        
        # Auxiliaries and copulas
        if word_lower in ['is', 'are', 'was', 'were', 'be', 'been', 'being']:
            return 'AUX'
        
        # Verbs
        if word_lower in ['think', 'know', 'believe', 'want', 'see', 'do', 'make', 'get']:
            return 'VERB'
        
        # Modal verbs
        if word_lower in ['can', 'could', 'should', 'would', 'will', 'must', 'may', 'might']:
            return 'AUX'
        
        # Determiners
        if word_lower in ['the', 'a', 'an', 'this', 'that', 'these', 'those']:
            return 'DET'
        
        # Pronouns
        if word_lower in ['i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them']:
            return 'PRON'
        
        # Conjunctions
        if word_lower in ['and', 'or', 'but', 'so', 'yet']:
            return 'CCONJ'
        
        # Prepositions
        if word_lower in ['in', 'on', 'at', 'by', 'for', 'with', 'to', 'from']:
            return 'ADP'
        
        # Adverbs
        if word.endswith('ly'):
            return 'ADV'
        
        # Default to NOUN
        return 'NOUN'
    
    @staticmethod
    def _get_advanced_tag(word: str, pos: str) -> str:
        """Get detailed tag based on POS."""
        word_lower = word.lower()
        
        if pos == 'VERB':
            if word_lower in ['think', 'know', 'believe']:
                return 'VBP'  # Present tense
            elif word.endswith('ed'):
                return 'VBD'  # Past tense
            elif word.endswith('ing'):
                return 'VBG'  # Gerund
            else:
                return 'VB'   # Base form
        
        elif pos == 'AUX':
            if word_lower in ['is', 'am']:
                return 'VBZ'
            elif word_lower in ['are', 'were']:
                return 'VBP'
            elif word_lower == 'was':
                return 'VBD'
            else:
                return 'MD'   # Modal
        
        elif pos == 'NOUN':
            if word.endswith('s') and not word.endswith('ss'):
                return 'NNS'  # Plural
            else:
                return 'NN'   # Singular
        
        else:
            return pos
    
    @staticmethod
    def _get_dependency(word: str, position: int, words: List[str]) -> str:
        """Get dependency relation."""
        if position == 0:
            return 'ROOT'
        elif position == 1:
            return 'nsubj'  # Subject
        else:
            return 'obj'    # Object
    
    @staticmethod
    def _get_morph_features(word: str, pos: str) -> Dict[str, str]:
        """Get morphological features."""
        features = {}
        
        if pos == 'NOUN':
            if word.endswith('s'):
                features['Number'] = 'Plur'
            else:
                features['Number'] = 'Sing'
        
        elif pos == 'VERB':
            if word.endswith('ed'):
                features['Tense'] = 'Past'
            elif word.endswith('ing'):
                features['Aspect'] = 'Prog'
            else:
                features['Tense'] = 'Pres'
        
        return features


class TestDataGenerators:
    """Generate test data for various scenarios."""
    
    @staticmethod
    def generate_sample_documents(format_type: str = 'markdown', 
                                complexity: str = 'medium',
                                include_errors: bool = True) -> Dict[str, Any]:
        """Generate sample documents with configurable complexity and errors."""
        
        documents = {
            'markdown': TestDataGenerators._generate_markdown_document,
            'asciidoc': TestDataGenerators._generate_asciidoc_document,
            'plain': TestDataGenerators._generate_plain_document
        }
        
        generator = documents.get(format_type, documents['markdown'])
        return generator(complexity, include_errors)
    
    @staticmethod
    def _generate_markdown_document(complexity: str, include_errors: bool) -> Dict[str, Any]:
        """Generate a Markdown document."""
        content_parts = []
        expected_errors = []
        
        # Title
        if include_errors and complexity in ['medium', 'high']:
            content_parts.append("# configuration management")  # Should be title case
            expected_errors.append({'type': 'headings', 'line': 1})
        else:
            content_parts.append("# Configuration Management")
        
        content_parts.append("")
        
        # Introduction
        if include_errors:
            content_parts.append("This document describes how we configure the system.")  # First person
            expected_errors.append({'type': 'pronouns', 'line': 3})
        else:
            content_parts.append("This document describes how to configure the system.")
        
        content_parts.append("")
        
        # List with potential parallelism issues
        content_parts.append("## Prerequisites")
        content_parts.append("")
        
        if include_errors and complexity in ['medium', 'high']:
            content_parts.extend([
                "- Install the software",
                "- Configuration of settings",  # Not parallel
                "- Starting the service"        # Not parallel
            ])
            expected_errors.extend([
                {'type': 'lists', 'line': 9},
                {'type': 'lists', 'line': 10}
            ])
        else:
            content_parts.extend([
                "- Install the software",
                "- Configure the settings",
                "- Start the service"
            ])
        
        # Complex paragraph with multiple issues
        if complexity == 'high':
            content_parts.extend([
                "",
                "## Advanced Configuration",
                "",
                "The system can be configured using various methods, however, it's "
                "important to note that you shouldn't use deprecated APIs e.g. the "
                "legacy whitelist feature which won't work in future versions."
            ])
            
            if include_errors:
                expected_errors.extend([
                    {'type': 'contractions', 'line': 16},
                    {'type': 'abbreviations', 'line': 16},
                    {'type': 'inclusive_language', 'line': 16},
                    {'type': 'contractions', 'line': 16}
                ])
        
        return {
            'content': '\n'.join(content_parts),
            'format': 'markdown',
            'expected_errors': expected_errors,
            'complexity': complexity,
            'line_count': len([line for line in content_parts if line.strip()])
        }
    
    @staticmethod
    def _generate_asciidoc_document(complexity: str, include_errors: bool) -> Dict[str, Any]:
        """Generate an AsciiDoc document."""
        content_parts = []
        expected_errors = []
        
        # Document header
        content_parts.append("= System configuration guide")
        if include_errors:
            expected_errors.append({'type': 'headings', 'line': 1})
        
        content_parts.extend([
            ":toc:",
            ":sectnums:",
            "",
            "This guide explains system configuration."
        ])
        
        # Admonition with potential issues
        if complexity in ['medium', 'high']:
            content_parts.extend([
                "",
                "[NOTE]",
                "===="
            ])
            
            if include_errors:
                content_parts.append("Don't forget to backup your data before proceeding.")
                expected_errors.append({'type': 'contractions', 'line': 10})
            else:
                content_parts.append("Do not forget to backup your data before proceeding.")
            
            content_parts.append("====")
        
        # Procedure with potential imperative issues
        content_parts.extend([
            "",
            "== Configuration Steps",
            "",
            ". The user should open the configuration file."  # Should be imperative
        ])
        
        if include_errors:
            expected_errors.append({'type': 'procedures', 'line': len(content_parts)})
        
        return {
            'content': '\n'.join(content_parts),
            'format': 'asciidoc',
            'expected_errors': expected_errors,
            'complexity': complexity,
            'line_count': len([line for line in content_parts if line.strip()])
        }
    
    @staticmethod
    def _generate_plain_document(complexity: str, include_errors: bool) -> Dict[str, Any]:
        """Generate a plain text document."""
        content_parts = []
        expected_errors = []
        
        if include_errors:
            content_parts.extend([
                "Configuration Management",
                "",
                "We recommend configuring the system using the whitelist approach.",
                "Don't use the deprecated APIs i.e. the legacy endpoints.",
                "",
                "The system thinks this configuration is optimal."
            ])
            
            expected_errors.extend([
                {'type': 'pronouns', 'line': 3},
                {'type': 'inclusive_language', 'line': 3},
                {'type': 'contractions', 'line': 4},
                {'type': 'abbreviations', 'line': 4},
                {'type': 'anthropomorphism', 'line': 6}
            ])
        else:
            content_parts.extend([
                "Configuration Management",
                "",
                "Configure the system using the allowlist approach.",
                "Do not use deprecated APIs, that is, the legacy endpoints.",
                "",
                "This configuration provides optimal performance."
            ])
        
        return {
            'content': '\n'.join(content_parts),
            'format': 'plain',
            'expected_errors': expected_errors,
            'complexity': complexity,
            'line_count': len([line for line in content_parts if line.strip()])
        }
    
    @staticmethod
    def generate_error_scenarios(component: str, error_type: str) -> List[Dict[str, Any]]:
        """Generate error scenarios for testing error handling."""
        
        scenarios = {
            'parser': {
                'malformed_input': [
                    {'input': None, 'expected_error': 'ValueError'},
                    {'input': '', 'expected_error': None},
                    {'input': '<<>>', 'expected_error': 'ParseError'}
                ],
                'encoding_issues': [
                    {'input': b'\x80\x81\x82', 'expected_error': 'UnicodeDecodeError'},
                    {'input': 'café', 'expected_error': None}
                ]
            },
            'analyzer': {
                'missing_nlp': [
                    {'nlp': None, 'expected_behavior': 'fallback'},
                    {'nlp': 'invalid', 'expected_error': 'TypeError'}
                ],
                'large_input': [
                    {'input': 'word ' * 10000, 'expected_behavior': 'timeout_or_success'}
                ]
            },
            'ai_rewriter': {
                'connection_failure': [
                    {'url': 'http://invalid:1234', 'expected_error': 'ConnectionError'},
                    {'url': None, 'expected_error': 'ValueError'}
                ],
                'invalid_response': [
                    {'response': '', 'expected_behavior': 'fallback'},
                    {'response': '{"invalid": json}', 'expected_error': 'JSONDecodeError'}
                ]
            }
        }
        
        return scenarios.get(component, {}).get(error_type, [])
    
    @staticmethod
    def generate_performance_test_data(size: str = 'medium') -> Dict[str, Any]:
        """Generate data for performance testing."""
        
        sizes = {
            'small': {'words': 100, 'sentences': 10, 'paragraphs': 2},
            'medium': {'words': 1000, 'sentences': 50, 'paragraphs': 10},
            'large': {'words': 10000, 'sentences': 500, 'paragraphs': 100},
            'xlarge': {'words': 50000, 'sentences': 2500, 'paragraphs': 500}
        }
        
        config = sizes.get(size, sizes['medium'])
        
        # Generate text with known patterns for testing
        words_per_sentence = config['words'] // config['sentences']
        sentences_per_paragraph = config['sentences'] // config['paragraphs']
        
        content = []
        for p in range(config['paragraphs']):
            paragraph_sentences = []
            for s in range(sentences_per_paragraph):
                sentence_words = []
                for w in range(words_per_sentence):
                    # Add some problematic words for testing
                    if w % 10 == 0:
                        sentence_words.append("whitelist")  # Inclusive language issue
                    elif w % 15 == 0:
                        sentence_words.append("don't")     # Contraction issue
                    else:
                        sentence_words.append(f"word{w}")
                
                sentence = ' '.join(sentence_words) + '.'
                paragraph_sentences.append(sentence)
            
            content.append(' '.join(paragraph_sentences))
        
        text = '\n\n'.join(content)
        
        return {
            'content': text,
            'size': size,
            'word_count': config['words'],
            'sentence_count': config['sentences'],
            'paragraph_count': config['paragraphs'],
            'expected_issues': {
                'inclusive_language': config['paragraphs'] * sentences_per_paragraph,
                'contractions': config['paragraphs'] * sentences_per_paragraph // 2
            }
        }


class EnhancedTestValidators(TestValidators):
    """Enhanced validators for comprehensive testing."""
    
    @staticmethod
    def validate_analysis_result_complete(result: Dict[str, Any]) -> None:
        """Validate complete analysis result structure."""
        required_fields = [
            'errors', 'statistics', 'readability', 'suggestions', 
            'metadata', 'performance'
        ]
        
        for field in required_fields:
            assert field in result, f"Analysis result missing field: {field}"
        
        # Validate errors structure
        assert isinstance(result['errors'], list), "Errors should be a list"
        for error in result['errors']:
            EnhancedTestValidators.validate_error_complete(error)
        
        # Validate statistics
        stats = result['statistics']
        assert 'word_count' in stats, "Statistics missing word_count"
        assert 'sentence_count' in stats, "Statistics missing sentence_count"
        assert 'error_count' in stats, "Statistics missing error_count"
        
        # Validate readability
        readability = result['readability']
        assert 'flesch_score' in readability, "Readability missing flesch_score"
        assert 'grade_level' in readability, "Readability missing grade_level"
    
    @staticmethod
    def validate_error_complete(error: Dict[str, Any]) -> None:
        """Validate complete error structure."""
        required_fields = [
            'type', 'message', 'suggestions', 'sentence', 
            'sentence_index', 'severity'
        ]
        
        for field in required_fields:
            assert field in error, f"Error missing field: {field}"
        
        # Validate field types
        assert isinstance(error['type'], str), "Error type should be string"
        assert isinstance(error['message'], str), "Error message should be string"
        assert isinstance(error['suggestions'], list), "Error suggestions should be list"
        assert isinstance(error['sentence'], str), "Error sentence should be string"
        assert isinstance(error['sentence_index'], int), "Error sentence_index should be int"
        assert isinstance(error['severity'], str), "Error severity should be string"
        
        # Validate values
        assert len(error['message']) > 0, "Error message should not be empty"
        assert len(error['suggestions']) > 0, "Error should have suggestions"
        assert error['severity'] in ['low', 'medium', 'high', 'critical'], f"Invalid severity: {error['severity']}"
        assert error['sentence_index'] >= 0, "Sentence index should be non-negative"
    
    @staticmethod
    def validate_performance_metrics(metrics: Dict[str, Any], 
                                   expected_max_time: float = 5.0) -> None:
        """Validate performance metrics."""
        required_metrics = ['analysis_time', 'memory_usage', 'component_times']
        
        for metric in required_metrics:
            assert metric in metrics, f"Performance metrics missing: {metric}"
        
        # Validate timing
        assert metrics['analysis_time'] > 0, "Analysis time should be positive"
        assert metrics['analysis_time'] < expected_max_time, f"Analysis too slow: {metrics['analysis_time']}s"
        
        # Validate memory usage
        assert metrics['memory_usage'] > 0, "Memory usage should be positive"
        
        # Validate component times
        component_times = metrics['component_times']
        assert isinstance(component_times, dict), "Component times should be dict"
        
        total_component_time = sum(component_times.values())
        assert total_component_time <= metrics['analysis_time'] * 1.1, "Component times inconsistent with total"
    
    @staticmethod
    def validate_ai_rewrite_result(result: Dict[str, Any]) -> None:
        """Validate AI rewrite result structure."""
        required_fields = [
            'rewritten_text', 'confidence', 'improvements', 
            'pass_number', 'model_info'
        ]
        
        for field in required_fields:
            assert field in result, f"Rewrite result missing field: {field}"
        
        # Validate field types and values
        assert isinstance(result['rewritten_text'], str), "Rewritten text should be string"
        assert len(result['rewritten_text']) > 0, "Rewritten text should not be empty"
        
        assert isinstance(result['confidence'], (int, float)), "Confidence should be numeric"
        assert 0 <= result['confidence'] <= 1, f"Confidence out of range: {result['confidence']}"
        
        assert isinstance(result['improvements'], list), "Improvements should be list"
        
        assert isinstance(result['pass_number'], int), "Pass number should be int"
        assert result['pass_number'] in [1, 2], f"Invalid pass number: {result['pass_number']}"


class TestExecutionHelpers:
    """Helpers for test execution and organization."""
    
    @staticmethod
    def run_rule_test_suite(rule_class, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a comprehensive test suite for a rule."""
        rule = rule_class()
        results = {
            'rule_type': rule._get_rule_type(),
            'passed': 0,
            'failed': 0,
            'errors': [],
            'performance': {}
        }
        
        import time
        start_time = time.time()
        
        for i, case in enumerate(test_cases):
            try:
                errors = rule.analyze(
                    case['text'],
                    case.get('sentences', [case['text']]),
                    case.get('nlp'),
                    case.get('context', {'block_type': 'paragraph'})
                )
                
                # Validate expectation
                if case['should_detect']:
                    assert len(errors) > 0, f"Case {i}: Should detect error in '{case['text']}'"
                    results['passed'] += 1
                else:
                    assert len(errors) == 0, f"Case {i}: Should not detect error in '{case['text']}'"
                    results['passed'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'case_index': i,
                    'case': case,
                    'error': str(e)
                })
        
        end_time = time.time()
        results['performance']['total_time'] = end_time - start_time
        results['performance']['avg_time_per_case'] = (end_time - start_time) / len(test_cases)
        
        return results
    
    @staticmethod
    def create_test_environment() -> Dict[str, Any]:
        """Create a complete test environment."""
        temp_dir = tempfile.mkdtemp()
        
        # Create test files
        test_files = {}
        for format_type in ['markdown', 'asciidoc', 'plain']:
            doc_data = TestDataGenerators.generate_sample_documents(format_type)
            filename = f"test_document.{format_type.replace('plain', 'txt')}"
            filepath = os.path.join(temp_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(doc_data['content'])
            
            test_files[format_type] = {
                'path': filepath,
                'content': doc_data['content'],
                'expected_errors': doc_data['expected_errors']
            }
        
        return {
            'temp_dir': temp_dir,
            'test_files': test_files,
            'cleanup': lambda: __import__('shutil').rmtree(temp_dir)
        }


# Pytest fixtures for enhanced testing
@pytest.fixture
def enhanced_mock_factory():
    """Provide enhanced mock factory."""
    return EnhancedTestMockFactory()

@pytest.fixture
def test_data_generator():
    """Provide test data generator."""
    return TestDataGenerators()

@pytest.fixture
def enhanced_validators():
    """Provide enhanced validators."""
    return EnhancedTestValidators()

@pytest.fixture
def test_environment():
    """Provide complete test environment."""
    env = TestExecutionHelpers.create_test_environment()
    yield env
    env['cleanup']()

@pytest.fixture
def performance_test_data():
    """Provide performance test data."""
    return TestDataGenerators.generate_performance_test_data('medium') 
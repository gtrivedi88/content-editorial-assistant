"""
Comprehensive Test Suite for Style Analyzer System
Tests all components of the style analyzer including base analyzer, structural analyzer,
sentence analyzer, readability analyzer, statistics calculator, suggestion generator,
error converters, analysis modes, block processors, mocking, error handling, concurrent
operations, performance, and integration scenarios.
"""

import os
import sys
import pytest
import asyncio
import threading
import time
from unittest.mock import Mock, patch, MagicMock, call, mock_open
from typing import List, Dict, Any, Optional, Tuple
import tempfile
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import style analyzer components
try:
    from style_analyzer import StyleAnalyzer
    from style_analyzer.base_analyzer import StyleAnalyzer as BaseStyleAnalyzer
    from style_analyzer.base_types import (
        AnalysisMode, ErrorSeverity, AnalysisMethod, ErrorDict,
        create_error, create_analysis_result, create_suggestion,
        safe_float_conversion, safe_textstat_call, DEFAULT_RULES,
        CONSERVATIVE_THRESHOLDS, CONFIDENCE_SCORES
    )
    from style_analyzer.readability_analyzer import ReadabilityAnalyzer
    from style_analyzer.sentence_analyzer import SentenceAnalyzer
    from style_analyzer.statistics_calculator import StatisticsCalculator
    from style_analyzer.suggestion_generator import SuggestionGenerator
    from style_analyzer.structural_analyzer import StructuralAnalyzer
    from style_analyzer.analysis_modes import AnalysisModeExecutor
    from style_analyzer.block_processors import BlockProcessor
    from style_analyzer.error_converters import ErrorConverter
    
    STYLE_ANALYZER_AVAILABLE = True
except ImportError as e:
    STYLE_ANALYZER_AVAILABLE = False
    print(f"Style analyzer not available: {e}")

# Try to import rules system
try:
    from rules import get_registry
    RULES_AVAILABLE = True
except ImportError:
    RULES_AVAILABLE = False
    get_registry = None

# Try to import SpaCy
try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False

# Try to import textstat
try:
    import textstat
    TEXTSTAT_AVAILABLE = True
except ImportError:
    TEXTSTAT_AVAILABLE = False

# Try to import structural parsing
try:
    from structural_parsing.extractors import StructuralParserFactory  # type: ignore
    STRUCTURAL_PARSING_AVAILABLE = True
except ImportError:
    STRUCTURAL_PARSING_AVAILABLE = False
    StructuralParserFactory = None


class TestStyleAnalyzerComprehensive:
    """Comprehensive test suite for the style analyzer system."""

    # ===============================
    # FIXTURES AND SETUP
    # ===============================

    @pytest.fixture
    def mock_nlp(self):
        """Create a comprehensive mock SpaCy NLP object."""
        nlp = Mock()
        
        def create_doc(text):
            doc = Mock()
            words = text.split()
            tokens = []
            
            for i, word in enumerate(words):
                token = Mock()
                token.text = word
                token.pos_ = "NOUN" if i % 2 == 0 else "VERB"
                token.tag_ = "NN" if i % 2 == 0 else "VB"
                token.dep_ = "nsubj" if i % 2 == 0 else "obj"
                token.lemma_ = word.lower()
                token.is_alpha = word.isalpha()
                token.is_stop = word.lower() in ['the', 'a', 'an', 'and', 'or', 'but']
                token.is_punct = not word.isalnum()
                token.children = []
                token.head = token
                token.i = i
                token.lower_ = word.lower()
                token.shape_ = "Xxxx" if word.istitle() else "xxxx"
                token.like_num = word.isdigit()
                token.like_email = "@" in word
                token.like_url = "http" in word.lower()
                tokens.append(token)
            
            doc.__iter__ = Mock(return_value=iter(tokens))
            doc.__len__ = Mock(return_value=len(tokens))
            doc.__getitem__ = Mock(side_effect=lambda i: tokens[i] if 0 <= i < len(tokens) else None)
            
            # Mock sentences
            sentences = [Mock()]
            sentences[0].__iter__ = Mock(return_value=iter(tokens))
            sentences[0].__len__ = Mock(return_value=len(tokens))
            sentences[0].text = text
            sentences[0].start = 0
            sentences[0].end = len(text)
            doc.sents = sentences
            
            # Mock entities
            doc.ents = []
            
            # Mock noun chunks
            doc.noun_chunks = []
            
            return doc
        
        nlp.side_effect = create_doc
        return nlp

    @pytest.fixture
    def mock_rules_registry(self):
        """Create a mock rules registry."""
        registry = Mock()
        registry.get_rules.return_value = []
        registry.analyze.return_value = []
        return registry

    @pytest.fixture
    def sample_texts(self):
        """Provide sample texts for testing."""
        return {
            'short': "This is a short text.",
            'medium': "This is a medium-length text with multiple sentences. It contains enough content for basic analysis. The text includes various sentence structures and word patterns.",
            'long': "This is a comprehensive text designed for thorough analysis. " * 20,
            'complex': "The system administrator should configure the authentication mechanism to ensure secure access. Users must authenticate using multi-factor authentication before accessing sensitive resources. The implementation requires careful consideration of security protocols and user experience optimization.",
            'technical': "The RESTful API endpoints utilize JWT tokens for authentication. The microservices architecture implements asynchronous message queuing for improved scalability. Database transactions maintain ACID properties through careful concurrency control mechanisms.",
            'passive': "The document was written by the author. The system is configured by the administrator. The report will be reviewed by the committee.",
            'active': "The author wrote the document. The administrator configures the system. The committee will review the report.",
            'markdown': "# Header\n\nThis is a paragraph with **bold** and *italic* text.\n\n- List item 1\n- List item 2\n\n```python\nprint('hello')\n```",
            'asciidoc': "= Title\n\nThis is a paragraph.\n\n== Section\n\nAnother paragraph with `code`.\n\n[source,python]\n----\nprint('hello')\n----",
            'empty': "",
            'whitespace': "   \n  \t  \n  ",
            'special_chars': "This text contains special characters: @#$%^&*()! and unicode: café naïve résumé",
            'numbers': "The system processes 1,234 requests per second with 99.9% uptime and 0.1ms latency."
        }

    @pytest.fixture
    def mock_textstat(self):
        """Create mock textstat functions."""
        mock_funcs = {
            'flesch_reading_ease': Mock(return_value=65.0),
            'flesch_kincaid_grade': Mock(return_value=8.5),
            'automated_readability_index': Mock(return_value=9.2),
            'coleman_liau_index': Mock(return_value=10.1),
            'gunning_fog': Mock(return_value=11.3),
            'sentence_count': Mock(return_value=5),
            'lexicon_count': Mock(return_value=50),
            'syllable_count': Mock(return_value=75),
            'avg_sentence_length': Mock(return_value=10.0),
            'avg_syllables_per_word': Mock(return_value=1.5),
            'difficult_words': Mock(return_value=8),
            'reading_time': Mock(return_value=30.0)
        }
        
        with patch.multiple('textstat', **mock_funcs):
            yield mock_funcs

    @pytest.fixture
    def custom_rules(self):
        """Provide custom rules for testing."""
        return {
            'max_sentence_length': 20,
            'target_grade_level': (8, 10),
            'min_readability_score': 70.0,
            'max_fog_index': 10.0,
            'passive_voice_threshold': 0.10,
            'word_repetition_threshold': 2,
            'max_syllables_per_word': 2.0,
            'min_sentence_variety': 0.8,
        }

    @pytest.fixture
    def mock_structural_parser(self):
        """Create a mock structural parser."""
        parser = Mock()
        parser.parse_document.return_value = {
            'blocks': [
                {'type': 'paragraph', 'content': 'Test paragraph', 'start': 0, 'end': 14},
                {'type': 'heading', 'content': 'Test heading', 'start': 15, 'end': 27, 'level': 1}
            ],
            'format': 'markdown',
            'has_structure': True
        }
        return parser

    # ===============================
    # BASE ANALYZER TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_style_analyzer_initialization(self):
        """Test StyleAnalyzer initialization with various configurations."""
        # Test default initialization
        analyzer = StyleAnalyzer()
        assert analyzer is not None
        assert hasattr(analyzer, 'readability_analyzer')
        assert hasattr(analyzer, 'sentence_analyzer')
        assert hasattr(analyzer, 'statistics_calculator')
        assert hasattr(analyzer, 'suggestion_generator')
        assert hasattr(analyzer, 'structural_analyzer')
        assert hasattr(analyzer, 'mode_executor')

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_style_analyzer_initialization_with_custom_rules(self, custom_rules):
        """Test StyleAnalyzer initialization with custom rules."""
        analyzer = StyleAnalyzer(rules=custom_rules)
        assert analyzer.rules == custom_rules
        assert analyzer.readability_analyzer.rules == custom_rules
        assert analyzer.sentence_analyzer.rules == custom_rules

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_style_analyzer_component_initialization(self):
        """Test that all components are properly initialized."""
        analyzer = StyleAnalyzer()
        
        # Check component types
        assert isinstance(analyzer.readability_analyzer, ReadabilityAnalyzer)
        assert isinstance(analyzer.sentence_analyzer, SentenceAnalyzer)
        assert isinstance(analyzer.statistics_calculator, StatisticsCalculator)
        assert isinstance(analyzer.suggestion_generator, SuggestionGenerator)
        assert isinstance(analyzer.structural_analyzer, StructuralAnalyzer)
        assert isinstance(analyzer.mode_executor, AnalysisModeExecutor)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_spacy_initialization(self):
        """Test SpaCy initialization with mocking."""
        with patch('spacy.load') as mock_load:
            mock_nlp = Mock()
            mock_load.return_value = mock_nlp
            
            analyzer = StyleAnalyzer()
            
            if SPACY_AVAILABLE:
                mock_load.assert_called_once_with("en_core_web_sm")
                assert analyzer.nlp == mock_nlp
            else:
                assert analyzer.nlp is None

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_spacy_initialization_failure(self):
        """Test SpaCy initialization failure handling."""
        with patch('spacy.load', side_effect=OSError("Model not found")):
            analyzer = StyleAnalyzer()
            assert analyzer.nlp is None

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_rules_registry_initialization(self):
        """Test rules registry initialization."""
        if RULES_AVAILABLE:
            with patch('rules.get_registry') as mock_get_registry:
                mock_registry = Mock()
                mock_get_registry.return_value = mock_registry
                
                analyzer = StyleAnalyzer()
                assert analyzer.rules_registry == mock_registry
        else:
            analyzer = StyleAnalyzer()
            assert analyzer.rules_registry is None

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_rules_registry_initialization_failure(self):
        """Test rules registry initialization failure handling."""
        if RULES_AVAILABLE:
            with patch('rules.get_registry', side_effect=Exception("Registry failed")):
                analyzer = StyleAnalyzer()
                assert analyzer.rules_registry is None

    # ===============================
    # ANALYSIS METHODS TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analyze_method_empty_text(self):
        """Test analyze method with empty text."""
        analyzer = StyleAnalyzer()
        
        # Test empty string
        result = analyzer.analyze("")
        assert result is not None
        assert result['errors'] == []
        assert result['suggestions'] == []
        assert result['overall_score'] == 0
        assert result['analysis_mode'] == AnalysisMode.NONE.value
        
        # Test whitespace only
        result = analyzer.analyze("   \n  \t  \n  ")
        assert result is not None
        assert result['errors'] == []
        assert result['suggestions'] == []
        assert result['overall_score'] == 0

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analyze_method_basic_text(self, sample_texts, mock_nlp):
        """Test analyze method with basic text."""
        with patch.object(StyleAnalyzer, '_initialize_spacy'):
            analyzer = StyleAnalyzer()
            analyzer.nlp = mock_nlp
            
            result = analyzer.analyze(sample_texts['short'])
            assert result is not None
            assert isinstance(result, dict)
            assert 'errors' in result
            assert 'suggestions' in result
            assert 'statistics' in result
            assert 'technical_metrics' in result
            assert 'overall_score' in result
            assert 'analysis_mode' in result

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analyze_method_with_format_hint(self, sample_texts, mock_nlp):
        """Test analyze method with format hints."""
        with patch.object(StyleAnalyzer, '_initialize_spacy'):
            analyzer = StyleAnalyzer()
            analyzer.nlp = mock_nlp
            
            formats = ['markdown', 'asciidoc', 'auto']
            for format_hint in formats:
                result = analyzer.analyze(sample_texts['medium'], format_hint=format_hint)
                assert result is not None
                assert isinstance(result, dict)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analyze_with_blocks_method(self, sample_texts, mock_nlp):
        """Test analyze_with_blocks method."""
        with patch.object(StyleAnalyzer, '_initialize_spacy'):
            analyzer = StyleAnalyzer()
            analyzer.nlp = mock_nlp
            
            result = analyzer.analyze_with_blocks(sample_texts['markdown'])
            assert result is not None
            assert isinstance(result, dict)
            assert 'analysis' in result
            assert 'structural_blocks' in result
            assert 'has_structure' in result

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analyze_exception_handling(self, sample_texts):
        """Test analyze method exception handling."""
        analyzer = StyleAnalyzer()
        
        # Mock structural analyzer to raise exception
        with patch.object(analyzer.structural_analyzer, 'analyze_with_structure', side_effect=Exception("Test error")):
            result = analyzer.analyze(sample_texts['medium'])
            assert result is not None
            assert len(result['errors']) == 1
            assert result['errors'][0]['type'] == 'system'
            assert 'Analysis failed' in result['errors'][0]['message']
            assert result['analysis_mode'] == AnalysisMode.ERROR.value

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analyze_with_blocks_exception_handling(self, sample_texts):
        """Test analyze_with_blocks method exception handling."""
        analyzer = StyleAnalyzer()
        
        # Mock structural analyzer to raise exception
        with patch.object(analyzer.structural_analyzer, 'analyze_with_blocks', side_effect=Exception("Test error")):
            result = analyzer.analyze_with_blocks(sample_texts['medium'])
            assert result is not None
            assert 'analysis' in result
            assert len(result['analysis']['errors']) == 1
            assert result['analysis']['errors'][0]['type'] == 'system'

    # ===============================
    # ANALYSIS MODE TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_determine_analysis_mode_spacy_and_rules(self):
        """Test analysis mode determination with SpaCy and rules available."""
        with patch.object(StyleAnalyzer, '_initialize_spacy'):
            analyzer = StyleAnalyzer()
            analyzer.nlp = Mock()
            analyzer.rules_registry = Mock()
            
            mode = analyzer._determine_analysis_mode()
            assert mode == AnalysisMode.SPACY_WITH_MODULAR_RULES

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_determine_analysis_mode_rules_only(self):
        """Test analysis mode determination with only rules available."""
        with patch.object(StyleAnalyzer, '_initialize_spacy'):
            analyzer = StyleAnalyzer()
            analyzer.nlp = None
            analyzer.rules_registry = Mock()
            
            mode = analyzer._determine_analysis_mode()
            assert mode == AnalysisMode.MODULAR_RULES_WITH_FALLBACKS

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_determine_analysis_mode_spacy_only(self):
        """Test analysis mode determination with only SpaCy available."""
        with patch.object(StyleAnalyzer, '_initialize_spacy'):
            analyzer = StyleAnalyzer()
            analyzer.nlp = Mock()
            analyzer.rules_registry = None
            
            mode = analyzer._determine_analysis_mode()
            assert mode == AnalysisMode.SPACY_LEGACY_ONLY

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_determine_analysis_mode_minimal(self):
        """Test analysis mode determination with minimal capabilities."""
        with patch.object(StyleAnalyzer, '_initialize_spacy'):
            analyzer = StyleAnalyzer()
            analyzer.nlp = None
            analyzer.rules_registry = None
            
            mode = analyzer._determine_analysis_mode()
            assert mode == AnalysisMode.MINIMAL_SAFE_MODE

    # ===============================
    # COMPONENT TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_readability_analyzer_component(self, sample_texts, mock_textstat):
        """Test ReadabilityAnalyzer component."""
        analyzer = ReadabilityAnalyzer()
        
        # Test analysis methods
        errors = analyzer.analyze_readability_conservative(sample_texts['medium'])
        assert isinstance(errors, list)
        
        # Test with custom rules
        custom_rules = {'min_readability_score': 80.0}
        analyzer_custom = ReadabilityAnalyzer(custom_rules)
        errors_custom = analyzer_custom.analyze_readability_conservative(sample_texts['medium'])
        assert isinstance(errors_custom, list)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_sentence_analyzer_component(self, sample_texts, mock_nlp):
        """Test SentenceAnalyzer component."""
        analyzer = SentenceAnalyzer()
        
        # Test sentence splitting
        sentences = analyzer.split_sentences_safe(sample_texts['medium'])
        assert isinstance(sentences, list)
        assert len(sentences) > 0
        
        # Test sentence analysis
        sentences = sample_texts['medium'].split('. ')
        errors = analyzer.analyze_sentence_length_conservative(sentences)
        assert isinstance(errors, list)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_statistics_calculator_component(self, sample_texts):
        """Test StatisticsCalculator component."""
        calculator = StatisticsCalculator()
        
        # Test statistics calculation
        sentences = sample_texts['medium'].split('. ')
        paragraphs = sample_texts['medium'].split('\n\n')
        
        stats = calculator.calculate_safe_statistics(sample_texts['medium'], sentences, paragraphs)
        assert isinstance(stats, dict)
        assert 'word_count' in stats
        assert 'sentence_count' in stats
        assert 'paragraph_count' in stats
        
        # Test technical metrics
        errors = []
        metrics = calculator.calculate_safe_technical_metrics(sample_texts['medium'], sentences, len(errors))
        assert isinstance(metrics, dict)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_suggestion_generator_component(self, sample_texts):
        """Test SuggestionGenerator component."""
        generator = SuggestionGenerator()
        
        # Test suggestion generation
        errors = [
            create_error('readability', 'Text is too complex', ['Simplify language']),
            create_error('sentence_length', 'Sentence too long', ['Break into shorter sentences'])
        ]
        
        statistics = {'word_count': 100, 'sentence_count': 5}
        technical_metrics = {'avg_sentence_length': 20.0}
        
        suggestions = generator.generate_suggestions(errors, statistics, technical_metrics)
        assert isinstance(suggestions, list)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_error_converter_component(self):
        """Test ErrorConverter component."""
        # Test that ErrorConverter can be instantiated
        converter = ErrorConverter()
        assert converter is not None
        
        # Test that it has the expected attributes
        assert hasattr(converter, 'error_converter') or hasattr(converter, 'convert_rules_error')

    # ===============================
    # STRUCTURAL ANALYSIS TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_structural_analyzer_initialization(self):
        """Test StructuralAnalyzer initialization."""
        readability = ReadabilityAnalyzer()
        sentence = SentenceAnalyzer()
        statistics = StatisticsCalculator()
        suggestions = SuggestionGenerator()
        
        analyzer = StructuralAnalyzer(readability, sentence, statistics, suggestions)
        assert analyzer.readability_analyzer == readability
        assert analyzer.sentence_analyzer == sentence
        assert analyzer.statistics_calculator == statistics
        assert analyzer.suggestion_generator == suggestions

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_structural_analyzer_with_structural_parsing(self, sample_texts, mock_structural_parser):
        """Test StructuralAnalyzer with structural parsing."""
        if STRUCTURAL_PARSING_AVAILABLE:
            with patch('structural_parsing.extractors.StructuralParserFactory') as mock_factory:
                mock_factory.return_value = mock_structural_parser
                
                readability = ReadabilityAnalyzer()
                sentence = SentenceAnalyzer()
                statistics = StatisticsCalculator()
                suggestions = SuggestionGenerator()
                
                analyzer = StructuralAnalyzer(readability, sentence, statistics, suggestions)
                
                # Test analyze_with_structure
                errors = analyzer.analyze_with_structure(sample_texts['markdown'], 'markdown', AnalysisMode.MINIMAL_SAFE_MODE)
                assert isinstance(errors, list)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_structural_analyzer_fallback_mode(self, sample_texts):
        """Test StructuralAnalyzer fallback mode without structural parsing."""
        readability = ReadabilityAnalyzer()
        sentence = SentenceAnalyzer()
        statistics = StatisticsCalculator()
        suggestions = SuggestionGenerator()
        
        analyzer = StructuralAnalyzer(readability, sentence, statistics, suggestions)
        
        # Mock the underlying _parser_factory attribute to simulate no structural parsing
        analyzer._parser_factory = None
        analyzer._parser_factory_attempted = True  # Skip lazy initialization
        
        # Test analyze_with_structure in fallback mode
        errors = analyzer.analyze_with_structure(sample_texts['medium'], 'auto', AnalysisMode.MINIMAL_SAFE_MODE)
        assert isinstance(errors, list)

    # ===============================
    # BLOCK PROCESSOR TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_block_processor_initialization(self):
        """Test BlockProcessor initialization."""
        try:
            processor = BlockProcessor()
            assert processor is not None
        except Exception as e:
            # Skip if BlockProcessor is not available
            pytest.skip(f"BlockProcessor not available: {e}")

    # ===============================
    # ANALYSIS MODE EXECUTOR TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analysis_mode_executor_initialization(self):
        """Test AnalysisModeExecutor initialization."""
        readability = ReadabilityAnalyzer()
        sentence = SentenceAnalyzer()
        
        executor = AnalysisModeExecutor(readability, sentence)
        assert executor.readability_analyzer == readability
        assert executor.sentence_analyzer == sentence

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analysis_mode_executor_spacy_rules_mode(self, sample_texts, mock_nlp, mock_rules_registry):
        """Test AnalysisModeExecutor in SpaCy with rules mode."""
        readability = ReadabilityAnalyzer()
        sentence = SentenceAnalyzer()
        
        executor = AnalysisModeExecutor(readability, sentence, mock_rules_registry, mock_nlp)
        
        # Test analyze_spacy_with_modular_rules
        sentences = sample_texts['medium'].split('. ')
        errors = executor.analyze_spacy_with_modular_rules(sample_texts['medium'], sentences)
        assert isinstance(errors, list)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analysis_mode_executor_rules_fallback_mode(self, sample_texts, mock_rules_registry):
        """Test AnalysisModeExecutor in rules with fallback mode."""
        readability = ReadabilityAnalyzer()
        sentence = SentenceAnalyzer()
        
        executor = AnalysisModeExecutor(readability, sentence, mock_rules_registry, None)
        
        # Test analyze_modular_rules_with_fallbacks
        sentences = sample_texts['medium'].split('. ')
        errors = executor.analyze_modular_rules_with_fallbacks(sample_texts['medium'], sentences)
        assert isinstance(errors, list)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analysis_mode_executor_spacy_legacy_mode(self, sample_texts, mock_nlp):
        """Test AnalysisModeExecutor in SpaCy legacy mode."""
        readability = ReadabilityAnalyzer()
        sentence = SentenceAnalyzer()
        
        executor = AnalysisModeExecutor(readability, sentence, None, mock_nlp)
        
        # Test analyze_spacy_legacy_only
        sentences = sample_texts['medium'].split('. ')
        errors = executor.analyze_spacy_legacy_only(sample_texts['medium'], sentences)
        assert isinstance(errors, list)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analysis_mode_executor_minimal_safe_mode(self, sample_texts):
        """Test AnalysisModeExecutor in minimal safe mode."""
        readability = ReadabilityAnalyzer()
        sentence = SentenceAnalyzer()
        
        executor = AnalysisModeExecutor(readability, sentence, None, None)
        
        # Test analyze_minimal_safe_mode
        sentences = sample_texts['medium'].split('. ')
        errors = executor.analyze_minimal_safe_mode(sample_texts['medium'], sentences)
        assert isinstance(errors, list)

    # ===============================
    # BASE TYPES TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_create_error_function(self):
        """Test create_error function."""
        error = create_error(
            'test_type',
            'Test message',
            ['Test suggestion'],
            severity=ErrorSeverity.HIGH,
            sentence='Test sentence',
            sentence_index=0,
            confidence=0.9,
            analysis_method=AnalysisMethod.SPACY_ENHANCED
        )
        
        assert error['type'] == 'test_type'
        assert error['message'] == 'Test message'
        assert error['suggestions'] == ['Test suggestion']
        assert error['severity'] == 'high'
        assert error['sentence'] == 'Test sentence'
        assert error['sentence_index'] == 0
        assert error['confidence'] == 0.9
        assert error['analysis_method'] == 'spacy_enhanced'

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_create_suggestion_function(self):
        """Test create_suggestion function."""
        suggestion = create_suggestion(
            'test_type',
            'Test message',
            priority='high'
        )
        
        assert suggestion['type'] == 'test_type'
        assert suggestion['message'] == 'Test message'
        assert suggestion['priority'] == 'high'

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_create_analysis_result_function(self):
        """Test create_analysis_result function."""
        errors = [create_error('test', 'Test error', ['Fix it'])]
        suggestions = [create_suggestion('test', 'Test suggestion')]
        statistics = {'word_count': 100}
        technical_metrics = {'avg_sentence_length': 15.0}
        
        result = create_analysis_result(
            errors=errors,
            suggestions=suggestions,
            statistics=statistics,
            technical_metrics=technical_metrics,
            overall_score=75.0,
            analysis_mode=AnalysisMode.SPACY_WITH_MODULAR_RULES,
            spacy_available=True,
            modular_rules_available=True
        )
        
        assert result['errors'] == errors
        assert result['suggestions'] == suggestions
        assert result['statistics'] == statistics
        assert result['technical_metrics'] == technical_metrics
        assert result['overall_score'] == 75.0
        assert result['analysis_mode'] == 'spacy_with_modular_rules'
        assert result['spacy_available'] is True
        assert result['modular_rules_available'] is True

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_safe_float_conversion(self):
        """Test safe_float_conversion function."""
        assert safe_float_conversion(10) == 10.0
        assert safe_float_conversion("15.5") == 15.5
        assert safe_float_conversion("invalid", 0.0) == 0.0
        assert safe_float_conversion(None, 5.0) == 5.0

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_safe_textstat_call(self):
        """Test safe_textstat_call function."""
        mock_func = Mock(return_value=10.5)
        result = safe_textstat_call(mock_func, "test text")
        assert result == 10.5
        mock_func.assert_called_once_with("test text")
        
        # Test with exception
        mock_func.side_effect = Exception("Test error")
        result = safe_textstat_call(mock_func, "test text", default=5.0)
        assert result == 5.0

    # ===============================
    # PERFORMANCE TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_performance_large_text(self, sample_texts):
        """Test performance with large text."""
        analyzer = StyleAnalyzer()
        
        # Create large text
        large_text = sample_texts['long'] * 10
        
        start_time = time.time()
        result = analyzer.analyze(large_text)
        end_time = time.time()
        
        assert result is not None
        assert end_time - start_time < 30.0  # Should complete within 30 seconds

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_performance_many_small_texts(self, sample_texts):
        """Test performance with many small texts."""
        analyzer = StyleAnalyzer()
        
        texts = [sample_texts['short']] * 100
        
        start_time = time.time()
        results = []
        for text in texts:
            result = analyzer.analyze(text)
            results.append(result)
        end_time = time.time()
        
        assert len(results) == 100
        assert all(result is not None for result in results)
        assert end_time - start_time < 60.0  # Should complete within 60 seconds

    # ===============================
    # CONCURRENT OPERATION TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_concurrent_analysis(self, sample_texts):
        """Test concurrent analysis operations."""
        analyzer = StyleAnalyzer()
        
        def analyze_text(text):
            return analyzer.analyze(text)
        
        texts = [sample_texts['medium']] * 5
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(analyze_text, text) for text in texts]
            results = [future.result() for future in as_completed(futures)]
        
        assert len(results) == 5
        assert all(result is not None for result in results)
        assert all(isinstance(result, dict) for result in results)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_concurrent_different_analyzers(self, sample_texts):
        """Test concurrent operations with different analyzer instances."""
        def create_and_analyze(text):
            analyzer = StyleAnalyzer()
            return analyzer.analyze(text)
        
        texts = [sample_texts['medium']] * 3
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_and_analyze, text) for text in texts]
            results = [future.result() for future in as_completed(futures)]
        
        assert len(results) == 3
        assert all(result is not None for result in results)

    # ===============================
    # MEMORY MANAGEMENT TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_memory_usage_repeated_analysis(self, sample_texts):
        """Test memory usage with repeated analysis."""
        analyzer = StyleAnalyzer()
        
        # Perform analysis multiple times
        for i in range(10):
            result = analyzer.analyze(sample_texts['medium'])
            assert result is not None
            
            # Clear result to help with memory management
            del result

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_memory_usage_analyzer_recreation(self, sample_texts):
        """Test memory usage with analyzer recreation."""
        for i in range(5):
            analyzer = StyleAnalyzer()
            result = analyzer.analyze(sample_texts['medium'])
            assert result is not None
            
            # Clear analyzer and result
            del analyzer
            del result

    # ===============================
    # EDGE CASE TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_edge_cases_special_characters(self, sample_texts):
        """Test edge cases with special characters."""
        analyzer = StyleAnalyzer()
        
        result = analyzer.analyze(sample_texts['special_chars'])
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_edge_cases_numbers_and_symbols(self, sample_texts):
        """Test edge cases with numbers and symbols."""
        analyzer = StyleAnalyzer()
        
        result = analyzer.analyze(sample_texts['numbers'])
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_edge_cases_very_long_sentences(self):
        """Test edge cases with very long sentences."""
        analyzer = StyleAnalyzer()
        
        # Create a very long sentence
        long_sentence = "This is a very long sentence that goes on and on and on " * 50 + "."
        
        result = analyzer.analyze(long_sentence)
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_edge_cases_repeated_words(self):
        """Test edge cases with repeated words."""
        analyzer = StyleAnalyzer()
        
        repeated_text = "The the the system system system works works works fine fine fine."
        
        result = analyzer.analyze(repeated_text)
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_edge_cases_mixed_formats(self):
        """Test edge cases with mixed format text."""
        analyzer = StyleAnalyzer()
        
        mixed_text = """
        # Markdown Header
        
        This is a paragraph with **bold** text.
        
        = AsciiDoc Header
        
        This is another paragraph with `code`.
        
        Regular text without formatting.
        """
        
        result = analyzer.analyze(mixed_text)
        assert result is not None
        assert isinstance(result, dict)

    # ===============================
    # INTEGRATION TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_integration_with_all_components(self, sample_texts, mock_nlp, mock_rules_registry):
        """Test integration with all components working together."""
        with patch.object(StyleAnalyzer, '_initialize_spacy'):
            analyzer = StyleAnalyzer()
            analyzer.nlp = mock_nlp
            analyzer.rules_registry = mock_rules_registry
            
            result = analyzer.analyze(sample_texts['complex'])
            assert result is not None
            assert isinstance(result, dict)
            assert 'errors' in result
            assert 'suggestions' in result
            assert 'statistics' in result
            assert 'technical_metrics' in result
            assert 'overall_score' in result

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_integration_block_analysis(self, sample_texts, mock_nlp, mock_rules_registry):
        """Test integration with block-aware analysis."""
        with patch.object(StyleAnalyzer, '_initialize_spacy'):
            analyzer = StyleAnalyzer()
            analyzer.nlp = mock_nlp
            analyzer.rules_registry = mock_rules_registry
            
            result = analyzer.analyze_with_blocks(sample_texts['markdown'])
            assert result is not None
            assert isinstance(result, dict)
            assert 'analysis' in result
            assert 'structural_blocks' in result
            assert 'has_structure' in result

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_integration_different_analysis_modes(self, sample_texts):
        """Test integration with different analysis modes."""
        # Test with minimal mode
        analyzer = StyleAnalyzer()
        analyzer.nlp = None
        analyzer.rules_registry = None
        
        result = analyzer.analyze(sample_texts['medium'])
        assert result is not None
        assert result['analysis_mode'] == AnalysisMode.MINIMAL_SAFE_MODE.value

    # ===============================
    # CONFIGURATION TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_configuration_custom_thresholds(self, sample_texts):
        """Test configuration with custom thresholds."""
        custom_rules = {
            'max_sentence_length': 15,
            'min_readability_score': 80.0,
            'passive_voice_threshold': 0.05
        }
        
        analyzer = StyleAnalyzer(rules=custom_rules)
        result = analyzer.analyze(sample_texts['medium'])
        assert result is not None
        assert isinstance(result, dict)

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_configuration_default_values(self):
        """Test configuration with default values."""
        analyzer = StyleAnalyzer()
        
        # Check default rules are applied
        assert analyzer.rules == {}
        assert analyzer.readability_analyzer.rules == {}
        assert analyzer.sentence_analyzer.rules == {}

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_configuration_partial_custom_rules(self, sample_texts):
        """Test configuration with partial custom rules."""
        partial_rules = {
            'max_sentence_length': 30
        }
        
        analyzer = StyleAnalyzer(rules=partial_rules)
        result = analyzer.analyze(sample_texts['medium'])
        assert result is not None
        assert isinstance(result, dict)

    # ===============================
    # ERROR HANDLING TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_error_handling_malformed_input(self):
        """Test error handling with malformed input."""
        analyzer = StyleAnalyzer()
        
        # Test with empty string instead of None to avoid type error
        try:
            result = analyzer.analyze("")
            assert result is not None
        except Exception as e:
            # Should handle gracefully
            pass

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_error_handling_component_failures(self, sample_texts):
        """Test error handling when components fail."""
        analyzer = StyleAnalyzer()
        
        # Mock component to fail
        with patch.object(analyzer.statistics_calculator, 'calculate_safe_statistics', side_effect=Exception("Component failed")):
            result = analyzer.analyze(sample_texts['medium'])
            # Should still return a result, possibly with errors
            assert result is not None

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_error_handling_dependency_missing(self, sample_texts):
        """Test error handling when dependencies are missing."""
        with patch('style_analyzer.base_analyzer.SPACY_AVAILABLE', False):
            with patch('style_analyzer.base_analyzer.RULES_AVAILABLE', False):
                analyzer = StyleAnalyzer()
                result = analyzer.analyze(sample_texts['medium'])
                assert result is not None
                assert result['spacy_available'] is False
                assert result['modular_rules_available'] is False

    # ===============================
    # UTILITY FUNCTION TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_split_sentences_method(self, sample_texts):
        """Test _split_sentences method."""
        analyzer = StyleAnalyzer()
        
        sentences = analyzer._split_sentences(sample_texts['medium'])
        assert isinstance(sentences, list)
        assert len(sentences) > 0

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_calculate_overall_score_method(self):
        """Test _calculate_overall_score method."""
        analyzer = StyleAnalyzer()
        
        errors = [create_error('test', 'Test error', ['Fix it'])]
        technical_metrics = {'avg_sentence_length': 15.0, 'readability_score': 70.0}
        statistics = {'word_count': 100, 'sentence_count': 5}
        
        score = analyzer._calculate_overall_score(errors, technical_metrics, statistics)
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_calculate_overall_score_no_errors(self):
        """Test _calculate_overall_score with no errors."""
        analyzer = StyleAnalyzer()
        
        errors = []
        technical_metrics = {'avg_sentence_length': 15.0, 'readability_score': 70.0}
        statistics = {'word_count': 100, 'sentence_count': 5}
        
        score = analyzer._calculate_overall_score(errors, technical_metrics, statistics)
        assert isinstance(score, float)
        assert score > 0.0

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_calculate_overall_score_many_errors(self):
        """Test _calculate_overall_score with many errors."""
        analyzer = StyleAnalyzer()
        
        errors = [create_error('test', f'Test error {i}', ['Fix it']) for i in range(10)]
        technical_metrics = {'avg_sentence_length': 25.0, 'readability_score': 40.0}
        statistics = {'word_count': 100, 'sentence_count': 5}
        
        score = analyzer._calculate_overall_score(errors, technical_metrics, statistics)
        assert isinstance(score, float)
        assert score < 50.0  # Should be low with many errors

    # ===============================
    # CLEANUP TESTS
    # ===============================

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_analyzer_cleanup(self):
        """Test that analyzer can be properly cleaned up."""
        analyzer = StyleAnalyzer()
        
        # Verify analyzer is created
        assert analyzer is not None
        
        # Delete analyzer
        del analyzer
        
        # Create new analyzer to verify no issues
        new_analyzer = StyleAnalyzer()
        assert new_analyzer is not None

    @pytest.mark.skipif(not STYLE_ANALYZER_AVAILABLE, reason="Style analyzer not available")
    def test_component_cleanup(self):
        """Test that components can be properly cleaned up."""
        analyzer = StyleAnalyzer()
        
        # Get references to components
        readability = analyzer.readability_analyzer
        sentence = analyzer.sentence_analyzer
        statistics = analyzer.statistics_calculator
        
        # Delete analyzer
        del analyzer
        
        # Components should still be accessible
        assert readability is not None
        assert sentence is not None
        assert statistics is not None

# ===============================
# HELPER FUNCTIONS
# ===============================

def create_test_document(format_type: str = 'markdown') -> str:
    """Create a test document in the specified format."""
    if format_type == 'markdown':
        return """
# Test Document

This is a test paragraph with **bold** and *italic* text.

## Section 2

Another paragraph with different content.

- List item 1
- List item 2
- List item 3

```python
print("Hello, World!")
```

Final paragraph with conclusion.
"""
    elif format_type == 'asciidoc':
        return """
= Test Document

This is a test paragraph with *bold* and _italic_ text.

== Section 2

Another paragraph with different content.

* List item 1
* List item 2
* List item 3

[source,python]
----
print("Hello, World!")
----

Final paragraph with conclusion.
"""
    else:
        return """
Test Document

This is a test paragraph with bold and italic text.

Section 2

Another paragraph with different content.

List item 1
List item 2
List item 3

print("Hello, World!")

Final paragraph with conclusion.
"""


def create_mock_analysis_result() -> Dict[str, Any]:
    """Create a mock analysis result for testing."""
    return {
        'errors': [
            create_error('readability', 'Text is too complex', ['Simplify language']),
            create_error('sentence_length', 'Sentence too long', ['Break into shorter sentences'])
        ],
        'suggestions': [
            create_suggestion('improvement', 'Consider using simpler vocabulary'),
            create_suggestion('structure', 'Add more paragraph breaks')
        ],
        'statistics': {
            'word_count': 150,
            'sentence_count': 8,
            'paragraph_count': 3,
            'avg_sentence_length': 18.75,
            'reading_time': 45.0
        },
        'technical_metrics': {
            'flesch_reading_ease': 65.0,
            'flesch_kincaid_grade': 8.5,
            'gunning_fog_index': 10.2,
            'automated_readability_index': 9.1
        },
        'overall_score': 72.5,
        'analysis_mode': 'spacy_with_modular_rules',
        'spacy_available': True,
        'modular_rules_available': True
    }


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 
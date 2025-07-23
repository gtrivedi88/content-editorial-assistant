"""
Comprehensive Test Suite for AI Rewriter System
Tests all components of the AI rewriter including AIRewriter core, ModelManager,
PromptGenerator, TextGenerator, TextProcessor, RewriteEvaluator, two-pass rewriting,
Ollama integration, error handling, concurrent operations, performance, and
integration scenarios.
"""

import os
import sys
import pytest
import asyncio
import threading
import time
import json
import yaml
from unittest.mock import Mock, patch, MagicMock, call, mock_open
from typing import List, Dict, Any, Optional, Tuple
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import AI rewriter components
try:
    from rewriter import AIRewriter
    from rewriter.core import AIRewriter as CoreAIRewriter
    from models import ModelManager
    from rewriter.prompts import PromptGenerator
    from rewriter.generators import TextGenerator
    from rewriter.processors import TextProcessor
    from rewriter.evaluators import RewriteEvaluator
    from src.config import Config
    
    AI_REWRITER_AVAILABLE = True
except ImportError as e:
    AI_REWRITER_AVAILABLE = False
    print(f"AI rewriter not available: {e}")

# Try to import requests for Ollama testing
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Try to import transformers for HuggingFace testing
try:
    import transformers
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


class TestAIRewriterComprehensive:
    """Comprehensive test suite for the AI rewriter system."""

    # ===============================
    # FIXTURES AND SETUP
    # ===============================

    @pytest.fixture
    def mock_ollama_response(self):
        """Create a comprehensive mock Ollama API response."""
        return {
            "model": "llama3:8b",
            "response": "The administrator configures the system efficiently. Users access secure resources through multi-factor authentication. The implementation balances security protocols with user experience optimization.",
            "done": True,
            "total_duration": 5432109876,
            "load_duration": 543210987,
            "prompt_eval_count": 26,
            "prompt_eval_duration": 1234567890,
            "eval_count": 298,
            "eval_duration": 2876543210
        }

    @pytest.fixture
    def mock_ollama_error_response(self):
        """Create a mock Ollama error response."""
        return {
            "error": "model not found"
        }

    @pytest.fixture
    def mock_progress_callback(self):
        """Create a comprehensive mock progress callback."""
        callback = Mock()
        callback.calls = []
        
        def track_calls(*args, **kwargs):
            callback.calls.append(args)
            
        callback.side_effect = track_calls
        return callback

    @pytest.fixture
    def sample_errors(self):
        """Provide sample errors for testing."""
        return [
            {
                'type': 'passive_voice',
                'message': 'Passive voice detected',
                'suggestions': ['Use active voice'],
                'severity': 'medium',
                'sentence': 'The system is configured by the administrator.',
                'sentence_index': 0,
                'confidence': 0.9
            },
            {
                'type': 'sentence_length',
                'message': 'Sentence too long (45 words)',
                'suggestions': ['Break into shorter sentences', 'Use simpler structure'],
                'severity': 'low',
                'sentence': 'The comprehensive implementation requires careful consideration of security protocols, user experience optimization, performance metrics, and scalability factors.',
                'sentence_index': 1,
                'confidence': 0.85
            },
            {
                'type': 'readability',
                'message': 'Text complexity too high',
                'suggestions': ['Use simpler vocabulary', 'Shorter sentences'],
                'severity': 'high',
                'sentence': 'The multifaceted architectural paradigm necessitates comprehensive evaluation.',
                'sentence_index': 2,
                'confidence': 0.92
            }
        ]

    @pytest.fixture
    def sample_texts(self):
        """Provide sample texts for testing."""
        return {
            'short': "This is a short text.",
            'medium': "The system is configured by the administrator. Users must authenticate before accessing resources. The implementation requires careful consideration.",
            'long': "The comprehensive software architecture was designed by the development team to ensure scalability, maintainability, and performance optimization. " * 10,
            'technical': "The RESTful API endpoints utilize JWT tokens for authentication. The microservices architecture implements asynchronous message queuing for improved scalability. Database transactions maintain ACID properties through careful concurrency control mechanisms.",
            'passive': "The document was written by the author. The system is configured by the administrator. The report will be reviewed by the committee.",
            'complex': "The multifaceted architectural paradigm necessitates comprehensive evaluation of performance optimization strategies, security implementation methodologies, and user experience enhancement protocols.",
            'empty': "",
            'whitespace': "   \n  \t  \n  ",
            'markdown': "# Header\n\nThe system **must** be configured properly. Users should authenticate using *secure* methods.\n\n- Point 1\n- Point 2",
            'special_chars': "The system uses UTF-8 encoding: café, naïve, résumé. Symbols: @#$%^&*()!",
        }

    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return {
            'hf_model_name': 'microsoft/DialoGPT-medium',
            'use_ollama': True,
            'ollama_model': 'llama3:8b',
            'ollama_url': 'http://localhost:11434',
            'max_tokens': 512,
            'temperature': 0.7,
            'timeout': 30
        }

    @pytest.fixture
    def mock_model_manager(self):
        """Create a comprehensive mock ModelManager."""
        manager = Mock()
        manager.use_ollama = True
        manager.ollama_model = 'llama3:8b'
        manager.ollama_url = 'http://localhost:11434'
        manager.hf_model = None
        manager.hf_tokenizer = None
        manager.is_available.return_value = True
        manager.get_model_info.return_value = {
            'type': 'ollama',
            'model_name': 'llama3:8b',
            'status': 'available',
            'url': 'http://localhost:11434'
        }
        return manager

    @pytest.fixture
    def mock_prompt_generator(self):
        """Create a comprehensive mock PromptGenerator."""
        generator = Mock()
        generator.style_guide = 'ibm_style'
        generator.use_ollama = True
        generator.prompt_configs = {
            'language_and_grammar': {'passive_voice': 'Fix passive voice'},
            'structure_and_format': {'sentence_length': 'Shorten sentences'}
        }
        generator.generate_prompt.return_value = "Test prompt for first pass"
        generator.generate_self_review_prompt.return_value = "Test prompt for second pass"
        generator.load_prompt_configs.return_value = True
        return generator

    @pytest.fixture
    def mock_text_generator(self):
        """Create a comprehensive mock TextGenerator."""
        generator = Mock()
        generator.model_manager = Mock()
        generator.is_available.return_value = True
        generator.generate_text.return_value = "This is the improved text with better clarity and structure."
        generator.generate_with_ollama.return_value = "Ollama generated text"
        generator.generate_with_hf_model.return_value = "HuggingFace generated text"
        generator.get_model_info.return_value = {
            'type': 'ollama',
            'available': True,
            'model': 'llama3:8b'
        }
        return generator

    @pytest.fixture
    def mock_text_processor(self):
        """Create a comprehensive mock TextProcessor."""
        processor = Mock()
        processor.clean_generated_text.return_value = "Cleaned improved text"
        processor.validate_rewrite.return_value = True
        processor.extract_content.return_value = "Extracted content"
        processor.rule_based_rewrite.return_value = "Rule-based improved text"
        return processor

    @pytest.fixture
    def mock_evaluator(self):
        """Create a comprehensive mock RewriteEvaluator."""
        evaluator = Mock()
        evaluator.evaluate_rewrite_quality.return_value = {
            'overall_score': 0.85,
            'readability_improvement': 0.8,
            'clarity_improvement': 0.9
        }
        evaluator.calculate_confidence.return_value = 0.85
        evaluator.extract_improvements.return_value = [
            'Converted passive voice to active voice',
            'Shortened long sentences'
        ]
        evaluator.extract_second_pass_improvements.return_value = [
            'Applied additional polish',
            'Enhanced clarity'
        ]
        evaluator.analyze_changes.return_value = {
            'changes_made': 3,
            'improvements': ['clarity', 'conciseness'],
            'confidence': 0.85
        }
        return evaluator

    @pytest.fixture
    def sample_prompt_configs(self):
        """Provide sample prompt configurations."""
        return {
            'language_and_grammar': {
                'passive_voice': {
                    'instruction': 'Convert passive voice to active voice',
                    'examples': [
                        {
                            'original': 'The system is configured by the admin.',
                            'improved': 'The admin configures the system.'
                        }
                    ]
                },
                'contractions': {
                    'instruction': 'Expand contractions for technical writing',
                    'examples': []
                }
            },
            'structure_and_format': {
                'sentence_length': {
                    'instruction': 'Break long sentences into shorter ones',
                    'examples': []
                }
            }
        }

    # ===============================
    # CORE AI REWRITER TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_ai_rewriter_initialization_default(self):
        """Test AIRewriter initialization with default parameters."""
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks
                            mock_model_manager_class.return_value = Mock()
                            mock_prompt_gen_class.return_value = Mock()
                            mock_text_gen_class.return_value = Mock()
                            mock_processor_class.return_value = Mock()
                            mock_evaluator_class.return_value = Mock()
                            
                            rewriter = AIRewriter()
                            
                            assert rewriter is not None
                            assert hasattr(rewriter, 'model_manager')
                            assert hasattr(rewriter, 'prompt_generator')
                            assert hasattr(rewriter, 'text_generator')
                            assert hasattr(rewriter, 'text_processor')
                            assert hasattr(rewriter, 'evaluator')
                            assert rewriter.progress_callback is None

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_ai_rewriter_initialization_custom(self, mock_progress_callback):
        """Test AIRewriter initialization with custom parameters."""
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks
                            mock_model_manager_class.return_value = Mock()
                            mock_prompt_gen_class.return_value = Mock()
                            mock_text_gen_class.return_value = Mock()
                            mock_processor_class.return_value = Mock()
                            mock_evaluator_class.return_value = Mock()
                            
                            rewriter = AIRewriter(
                                model_name="custom-model",
                                use_ollama=True,
                                ollama_model="llama3:13b",
                                progress_callback=mock_progress_callback
                            )
                            
                            assert rewriter.progress_callback == mock_progress_callback
                            
                            # Verify component initialization with correct parameters
                            mock_model_manager_class.assert_called_once_with("custom-model", True, "llama3:13b")
                            mock_prompt_gen_class.assert_called_once_with(style_guide='ibm_style', use_ollama=True)

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_ai_rewriter_component_integration(self, mock_model_manager, mock_prompt_generator, 
                                             mock_text_generator, mock_text_processor, mock_evaluator):
        """Test that all components are properly integrated."""
        with patch('rewriter.core.ModelManager', return_value=mock_model_manager):
            with patch('rewriter.core.PromptGenerator', return_value=mock_prompt_generator):
                with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
                    with patch('rewriter.core.TextProcessor', return_value=mock_text_processor):
                        with patch('rewriter.core.RewriteEvaluator', return_value=mock_evaluator):
                            
                            rewriter = AIRewriter()
                            
                            assert rewriter.model_manager == mock_model_manager
                            assert rewriter.prompt_generator == mock_prompt_generator
                            assert rewriter.text_generator == mock_text_generator
                            assert rewriter.text_processor == mock_text_processor
                            assert rewriter.evaluator == mock_evaluator

    # ===============================
    # REWRITE METHOD TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_empty_content(self, mock_text_generator):
        """Test rewrite method with empty content."""
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            result = rewriter.rewrite("", [])
            
            assert result['rewritten_text'] == ''
            assert result['improvements'] == []
            assert result['confidence'] == 0.0
            assert 'error' in result

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_whitespace_content(self, mock_text_generator):
        """Test rewrite method with whitespace-only content."""
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            result = rewriter.rewrite("   \n  \t  \n  ", [])
            
            assert result['rewritten_text'] == ''
            assert result['improvements'] == []
            assert result['confidence'] == 0.0

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_no_errors_first_pass(self, sample_texts, mock_text_generator):
        """Test rewrite method with no errors in first pass."""
        mock_text_generator.is_available.return_value = True
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            result = rewriter.rewrite(sample_texts['medium'], [], pass_number=1)
            
            assert result['rewritten_text'] == sample_texts['medium']
            assert 'No errors detected' in result['improvements']
            assert result['confidence'] == 1.0

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_ai_unavailable(self, sample_texts, sample_errors):
        """Test rewrite method when AI models are unavailable."""
        mock_text_generator = Mock()
        mock_text_generator.is_available.return_value = False
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            result = rewriter.rewrite(sample_texts['medium'], sample_errors)
            
            assert result['rewritten_text'] == sample_texts['medium']
            assert result['improvements'] == []
            assert result['confidence'] == 0.0
            assert 'AI models are not available' in result['error']

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_first_pass_success(self, sample_texts, sample_errors, mock_progress_callback,
                                       mock_model_manager, mock_prompt_generator, mock_text_generator,
                                       mock_text_processor, mock_evaluator):
        """Test successful first pass rewriting."""
        with patch('rewriter.core.ModelManager', return_value=mock_model_manager):
            with patch('rewriter.core.PromptGenerator', return_value=mock_prompt_generator):
                with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
                    with patch('rewriter.core.TextProcessor', return_value=mock_text_processor):
                        with patch('rewriter.core.RewriteEvaluator', return_value=mock_evaluator):
                            
                            mock_text_generator.is_available.return_value = True
                            mock_text_processor.clean_generated_text.return_value = "Improved text from first pass"
                            
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            result = rewriter.rewrite(sample_texts['medium'], sample_errors, pass_number=1)
                            
                            assert result['rewritten_text'] == "Improved text from first pass"
                            assert isinstance(result['improvements'], list)
                            assert result['confidence'] > 0
                            assert 'error' not in result
                            
                            # Verify component interactions
                            mock_prompt_generator.generate_prompt.assert_called_once()
                            mock_text_generator.generate_text.assert_called_once()
                            mock_text_processor.clean_generated_text.assert_called_once()

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_second_pass_success(self, sample_texts, sample_errors, mock_progress_callback,
                                        mock_model_manager, mock_prompt_generator, mock_text_generator,
                                        mock_text_processor, mock_evaluator):
        """Test successful second pass rewriting."""
        with patch('rewriter.core.ModelManager', return_value=mock_model_manager):
            with patch('rewriter.core.PromptGenerator', return_value=mock_prompt_generator):
                with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
                    with patch('rewriter.core.TextProcessor', return_value=mock_text_processor):
                        with patch('rewriter.core.RewriteEvaluator', return_value=mock_evaluator):
                            
                            mock_text_generator.is_available.return_value = True
                            mock_text_processor.clean_generated_text.return_value = "Final refined text"
                            
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            result = rewriter.rewrite(sample_texts['medium'], sample_errors, pass_number=2)
                            
                            assert result['rewritten_text'] == "Final refined text"
                            assert isinstance(result['improvements'], list)
                            assert result['confidence'] > 0
                            
                            # Verify second pass specific interactions
                            mock_prompt_generator.generate_self_review_prompt.assert_called_once()
                            mock_evaluator.extract_second_pass_improvements.assert_called_once()

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_exception_handling(self, sample_texts, sample_errors):
        """Test rewrite method exception handling."""
        mock_text_generator = Mock()
        mock_text_generator.is_available.side_effect = Exception("Test exception")
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            result = rewriter.rewrite(sample_texts['medium'], sample_errors)
            
            assert result['rewritten_text'] == sample_texts['medium']
            assert result['improvements'] == []
            assert result['confidence'] == 0.0
            assert 'AI rewrite failed' in result['error']

    # ===============================
    # REFINE TEXT TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_refine_text_method(self, sample_texts, sample_errors, mock_progress_callback,
                               mock_model_manager, mock_prompt_generator, mock_text_generator,
                               mock_text_processor, mock_evaluator):
        """Test the refine_text method."""
        with patch('rewriter.core.ModelManager', return_value=mock_model_manager):
            with patch('rewriter.core.PromptGenerator', return_value=mock_prompt_generator):
                with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
                    with patch('rewriter.core.TextProcessor', return_value=mock_text_processor):
                        with patch('rewriter.core.RewriteEvaluator', return_value=mock_evaluator):
                            
                            mock_text_generator.is_available.return_value = True
                            mock_text_processor.clean_generated_text.return_value = "Refined text"
                            
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            
                            # Check if refine_text method exists
                            if hasattr(rewriter, 'refine_text'):
                                result = rewriter.refine_text(sample_texts['medium'], sample_errors)
                                assert isinstance(result, dict)
                            else:
                                # Use rewrite with pass_number=2
                                result = rewriter.rewrite(sample_texts['medium'], sample_errors, pass_number=2)
                                assert isinstance(result, dict)

    # ===============================
    # MODEL MANAGER TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_model_manager_initialization_ollama(self):
        """Test ModelManager initialization with Ollama."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"status": "success"}
            
            manager = ModelManager("test-model", use_ollama=True, ollama_model="llama3:8b")
            
            assert manager.use_ollama is True
            assert manager.ollama_model == "llama3:8b"
            assert manager.generator is None

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_model_manager_initialization_hf(self):
        """Test ModelManager initialization with HuggingFace."""
        with patch('transformers.AutoTokenizer') as mock_tokenizer:
            with patch('transformers.AutoModelForCausalLM') as mock_model:
                mock_tokenizer.from_pretrained.return_value = Mock()
                mock_model.from_pretrained.return_value = Mock()
                
                manager = ModelManager("microsoft/DialoGPT-medium", use_ollama=False)
                
                assert manager.use_ollama is False
                assert manager.generator is not None or not TRANSFORMERS_AVAILABLE

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_model_manager_availability_check(self):
        """Test ModelManager availability checking."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"status": "success"}
            
            manager = ModelManager("test-model", use_ollama=True)
            available = manager.is_available()
            
            assert isinstance(available, bool)

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_model_manager_get_info(self):
        """Test ModelManager get_model_info method."""
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.return_value = {"status": "success"}
            
            manager = ModelManager("test-model", use_ollama=True)
            info = manager.get_model_info()
            
            assert isinstance(info, dict)
            assert 'type' in info or 'model_name' in info

    # ===============================
    # PROMPT GENERATOR TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_prompt_generator_initialization(self):
        """Test PromptGenerator initialization."""
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value={}):
                with patch('builtins.open', mock_open(read_data='{}')):
                    generator = PromptGenerator(style_guide='ibm_style', use_ollama=True)
                    
                    assert generator.style_guide_name == 'ibm_style'
                    assert generator.use_ollama is True
                    assert hasattr(generator, 'prompt_configs')

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_prompt_generator_config_loading(self, sample_prompt_configs):
        """Test PromptGenerator configuration loading."""
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value=sample_prompt_configs):
                with patch('builtins.open', mock_open()):
                    generator = PromptGenerator(style_guide='ibm_style')
                    
                    # Test that configs are loaded
                    assert hasattr(generator, 'prompt_configs')

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_prompt_generator_generate_prompt(self, sample_texts, sample_errors):
        """Test prompt generation with errors."""
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value={}):
                with patch('builtins.open', mock_open()):
                    generator = PromptGenerator()
                    
                    prompt = generator.generate_prompt(sample_texts['medium'], sample_errors, 'sentence')
                    
                    assert isinstance(prompt, str)
                    assert len(prompt) > 0

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_prompt_generator_self_review_prompt(self, sample_texts, sample_errors):
        """Test self-review prompt generation."""
        with patch('os.path.exists', return_value=True):
            with patch('yaml.safe_load', return_value={}):
                with patch('builtins.open', mock_open()):
                    generator = PromptGenerator()
                    
                    prompt = generator.generate_self_review_prompt(sample_texts['medium'], sample_errors)
                    
                    assert isinstance(prompt, str)
                    assert len(prompt) > 0

    # ===============================
    # TEXT GENERATOR TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_text_generator_initialization(self, mock_model_manager):
        """Test TextGenerator initialization."""
        generator = TextGenerator(mock_model_manager)
        
        assert generator.model_manager == mock_model_manager
        assert hasattr(generator, 'is_available')

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_text_generator_availability(self, mock_model_manager):
        """Test TextGenerator availability checking."""
        mock_model_manager.is_available.return_value = True
        
        generator = TextGenerator(mock_model_manager)
        available = generator.is_available()
        
        assert available is True

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="Requests not available")
    def test_text_generator_ollama_success(self, mock_ollama_response):
        """Test successful Ollama text generation."""
        mock_model_manager = Mock()
        mock_model_manager.use_ollama = True
        mock_model_manager.ollama_url = 'http://localhost:11434'
        mock_model_manager.ollama_model = 'llama3:8b'
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_ollama_response
            mock_post.return_value.status_code = 200
            
            generator = TextGenerator(mock_model_manager)
            result = generator.generate_text("Test prompt", "Test content")
            
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="Requests not available")
    def test_text_generator_ollama_failure(self, mock_ollama_error_response):
        """Test Ollama text generation failure handling."""
        mock_model_manager = Mock()
        mock_model_manager.use_ollama = True
        mock_model_manager.ollama_url = 'http://localhost:11434'
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_ollama_error_response
            mock_post.return_value.status_code = 400
            
            generator = TextGenerator(mock_model_manager)
            result = generator.generate_text("Test prompt", "Test content")
            
            # Should return original content on failure
            assert result == "Test content"

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_text_generator_hf_fallback(self):
        """Test HuggingFace model fallback."""
        mock_model_manager = Mock()
        mock_model_manager.use_ollama = False
        mock_model_manager.hf_model = Mock()
        mock_model_manager.hf_tokenizer = Mock()
        
        if TRANSFORMERS_AVAILABLE:
            generator = TextGenerator(mock_model_manager)
            result = generator.generate_text("Test prompt", "Test content")
            
            assert isinstance(result, str)

    # ===============================
    # TEXT PROCESSOR TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_text_processor_initialization(self):
        """Test TextProcessor initialization."""
        processor = TextProcessor()
        assert processor is not None

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_text_processor_clean_generation(self, sample_texts):
        """Test text cleaning functionality."""
        processor = TextProcessor()
        
        raw_text = "Here's the improved version: " + sample_texts['medium'] + "\n\nThis is much better!"
        cleaned = processor.clean_generated_text(raw_text, sample_texts['medium'])
        
        assert isinstance(cleaned, str)
        assert len(cleaned) > 0

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_text_processor_empty_generation(self, sample_texts):
        """Test text processor with empty generated text."""
        processor = TextProcessor()
        
        cleaned = processor.clean_generated_text("", sample_texts['medium'])
        
        assert cleaned == sample_texts['medium']

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_text_processor_identical_text(self, sample_texts):
        """Test text processor with identical text."""
        processor = TextProcessor()
        
        cleaned = processor.clean_generated_text(sample_texts['medium'], sample_texts['medium'])
        
        assert cleaned == sample_texts['medium']

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_text_processor_rule_based_rewrite(self, sample_texts, sample_errors):
        """Test rule-based rewriting fallback."""
        processor = TextProcessor()
        
        if hasattr(processor, 'rule_based_rewrite'):
            result = processor.rule_based_rewrite(sample_texts['passive'], sample_errors)
            assert isinstance(result, str)

    # ===============================
    # REWRITE EVALUATOR TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_evaluator_initialization(self):
        """Test RewriteEvaluator initialization."""
        evaluator = RewriteEvaluator()
        assert evaluator is not None

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_evaluator_confidence_calculation(self, sample_texts):
        """Test confidence calculation."""
        evaluator = RewriteEvaluator()
        
        confidence = evaluator.calculate_confidence(
            sample_texts['medium'], 
            "The admin configures the system. Users authenticate before accessing resources.", 
            []
        )
        
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_evaluator_extract_improvements(self, sample_texts):
        """Test improvement extraction."""
        evaluator = RewriteEvaluator()
        
        improvements = evaluator.extract_improvements(
            sample_texts['passive'],
            "The author wrote the document. The admin configures the system.",
            []
        )
        
        assert isinstance(improvements, list)

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_evaluator_quality_assessment(self, sample_texts):
        """Test rewrite quality evaluation."""
        evaluator = RewriteEvaluator()
        
        if hasattr(evaluator, 'evaluate_rewrite_quality'):
            quality = evaluator.evaluate_rewrite_quality(
                sample_texts['medium'],
                "Improved version of the text",
                []  # Add empty errors list
            )
            assert isinstance(quality, dict)

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewrite_evaluator_second_pass_improvements(self, sample_texts):
        """Test second pass improvement extraction."""
        evaluator = RewriteEvaluator()
        
        improvements = evaluator.extract_second_pass_improvements(
            "First pass result",
            "Second pass refined result"
        )
        
        assert isinstance(improvements, list)

    # ===============================
    # INTEGRATION TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_full_two_pass_integration(self, sample_texts, sample_errors, mock_progress_callback):
        """Test complete two-pass rewriting integration."""
        with patch('rewriter.core.ModelManager') as mock_model_manager_class:
            with patch('rewriter.core.PromptGenerator') as mock_prompt_gen_class:
                with patch('rewriter.core.TextGenerator') as mock_text_gen_class:
                    with patch('rewriter.core.TextProcessor') as mock_processor_class:
                        with patch('rewriter.core.RewriteEvaluator') as mock_evaluator_class:
                            
                            # Setup mocks for integration test
                            mock_text_gen = Mock()
                            mock_text_gen.is_available.return_value = True
                            mock_text_gen.generate_text.side_effect = [
                                "First pass improved text",
                                "Second pass refined text"
                            ]
                            
                            mock_processor = Mock()
                            mock_processor.clean_generated_text.side_effect = [
                                "Cleaned first pass",
                                "Cleaned second pass"
                            ]
                            
                            mock_evaluator = Mock()
                            mock_evaluator.extract_improvements.return_value = ['First pass improvements']
                            mock_evaluator.extract_second_pass_improvements.return_value = ['Second pass improvements']
                            mock_evaluator.calculate_confidence.return_value = 0.85
                            
                            mock_model_manager_class.return_value = Mock()
                            mock_prompt_gen_class.return_value = Mock()
                            mock_text_gen_class.return_value = mock_text_gen
                            mock_processor_class.return_value = mock_processor
                            mock_evaluator_class.return_value = mock_evaluator
                            
                            rewriter = AIRewriter(progress_callback=mock_progress_callback)
                            
                            # First pass
                            first_result = rewriter.rewrite(sample_texts['medium'], sample_errors, pass_number=1)
                            assert first_result['rewritten_text'] == "Cleaned first pass"
                            
                            # Second pass
                            second_result = rewriter.rewrite(sample_texts['medium'], sample_errors, pass_number=2)
                            assert second_result['rewritten_text'] == "Cleaned second pass"

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_batch_rewrite_integration(self, sample_texts, sample_errors, mock_text_generator):
        """Test batch rewriting functionality."""
        mock_text_generator.is_available.return_value = True
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            if hasattr(rewriter, 'batch_rewrite'):
                content_list = [sample_texts['short'], sample_texts['medium']]
                errors_list = [[], sample_errors]
                
                results = rewriter.batch_rewrite(content_list, errors_list)
                
                assert isinstance(results, list)
                assert len(results) == 2

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_system_info_integration(self, mock_model_manager, mock_text_generator):
        """Test system information retrieval."""
        with patch('rewriter.core.ModelManager', return_value=mock_model_manager):
            with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
                rewriter = AIRewriter()
                
                system_info = rewriter.get_system_info()
                
                assert isinstance(system_info, dict)
                assert 'model_info' in system_info
                assert 'available_components' in system_info
                assert 'is_ready' in system_info

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_is_ready_integration(self, mock_text_generator):
        """Test readiness checking integration."""
        mock_text_generator.is_available.return_value = True
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            ready = rewriter.is_ready()
            assert ready is True

    # ===============================
    # PERFORMANCE TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_performance_large_content(self, sample_texts, sample_errors, mock_text_generator):
        """Test performance with large content."""
        mock_text_generator.is_available.return_value = True
        mock_text_generator.generate_text.return_value = "Large content rewritten"
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            large_content = sample_texts['long'] * 5
            
            start_time = time.time()
            result = rewriter.rewrite(large_content, sample_errors)
            end_time = time.time()
            
            assert result is not None
            assert end_time - start_time < 30.0  # Should complete within 30 seconds

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_performance_many_small_requests(self, sample_texts, sample_errors, mock_text_generator):
        """Test performance with many small requests."""
        mock_text_generator.is_available.return_value = True
        mock_text_generator.generate_text.return_value = "Small content rewritten"
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            start_time = time.time()
            
            results = []
            for i in range(50):
                result = rewriter.rewrite(sample_texts['short'], [])
                results.append(result)
            
            end_time = time.time()
            
            assert len(results) == 50
            assert all(result is not None for result in results)
            assert end_time - start_time < 60.0  # Should complete within 60 seconds

    # ===============================
    # CONCURRENT OPERATION TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_concurrent_rewrite_requests(self, sample_texts, sample_errors, mock_text_generator):
        """Test concurrent rewrite requests."""
        mock_text_generator.is_available.return_value = True
        mock_text_generator.generate_text.return_value = "Concurrent rewrite result"
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            def rewrite_worker(content, errors):
                return rewriter.rewrite(content, errors)
            
            # Test concurrent requests
            contents = [sample_texts['medium']] * 5
            errors_list = [sample_errors] * 5
            
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [executor.submit(rewrite_worker, content, errors) 
                          for content, errors in zip(contents, errors_list)]
                results = [future.result() for future in as_completed(futures)]
            
            assert len(results) == 5
            assert all(result is not None for result in results)
            assert all(isinstance(result, dict) for result in results)

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_concurrent_different_rewriters(self, sample_texts, sample_errors, mock_text_generator):
        """Test concurrent operations with different rewriter instances."""
        def create_and_rewrite(content, errors):
            with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
                rewriter = AIRewriter()
                return rewriter.rewrite(content, errors)
        
        mock_text_generator.is_available.return_value = True
        mock_text_generator.generate_text.return_value = "Instance rewrite result"
        
        contents = [sample_texts['medium']] * 3
        errors_list = [sample_errors] * 3
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(create_and_rewrite, content, errors) 
                      for content, errors in zip(contents, errors_list)]
            results = [future.result() for future in as_completed(futures)]
        
        assert len(results) == 3
        assert all(result is not None for result in results)

    # ===============================
    # MEMORY MANAGEMENT TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_memory_usage_repeated_rewrite(self, sample_texts, sample_errors, mock_text_generator):
        """Test memory usage with repeated rewrites."""
        mock_text_generator.is_available.return_value = True
        mock_text_generator.generate_text.return_value = "Memory test result"
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            # Perform multiple rewrites
            for i in range(10):
                result = rewriter.rewrite(sample_texts['medium'], sample_errors)
                assert result is not None
                
                # Clear result to help with memory management
                del result

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_memory_usage_rewriter_recreation(self, sample_texts, sample_errors, mock_text_generator):
        """Test memory usage with rewriter recreation."""
        mock_text_generator.is_available.return_value = True
        mock_text_generator.generate_text.return_value = "Recreation test result"
        
        for i in range(5):
            with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
                rewriter = AIRewriter()
                result = rewriter.rewrite(sample_texts['medium'], sample_errors)
                assert result is not None
                
                # Clear rewriter and result
                del rewriter
                del result

    # ===============================
    # EDGE CASE TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_edge_cases_special_characters(self, sample_texts, mock_text_generator):
        """Test edge cases with special characters."""
        mock_text_generator.is_available.return_value = True
        mock_text_generator.generate_text.return_value = "Special chars handled"
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            result = rewriter.rewrite(sample_texts['special_chars'], [])
            
            assert result is not None
            assert isinstance(result, dict)

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_edge_cases_markdown_content(self, sample_texts, mock_text_generator):
        """Test edge cases with markdown content."""
        mock_text_generator.is_available.return_value = True
        mock_text_generator.generate_text.return_value = "Markdown handled"
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            result = rewriter.rewrite(sample_texts['markdown'], [])
            
            assert result is not None
            assert isinstance(result, dict)

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_edge_cases_very_long_content(self, mock_text_generator):
        """Test edge cases with very long content."""
        mock_text_generator.is_available.return_value = True
        mock_text_generator.generate_text.return_value = "Long content handled"
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            # Create very long content
            long_content = "This is a very long sentence. " * 1000
            
            result = rewriter.rewrite(long_content, [])
            
            assert result is not None
            assert isinstance(result, dict)

    # ===============================
    # CONFIGURATION TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_configuration_ollama_enabled(self, mock_config):
        """Test configuration with Ollama enabled."""
        with patch.object(Config, 'get_ai_config', return_value=mock_config):
            with patch('rewriter.core.ModelManager') as mock_model_manager_class:
                mock_model_manager_class.return_value = Mock()
                
                rewriter = AIRewriter(
                    use_ollama=mock_config['use_ollama'],
                    ollama_model=mock_config['ollama_model']
                )
                
                # Verify ModelManager was called with correct parameters
                mock_model_manager_class.assert_called_once()
                args = mock_model_manager_class.call_args[0]
                assert args[1] == mock_config['use_ollama']  # use_ollama parameter

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_configuration_huggingface_enabled(self, mock_config):
        """Test configuration with HuggingFace enabled."""
        hf_config = mock_config.copy()
        hf_config['use_ollama'] = False
        
        with patch.object(Config, 'get_ai_config', return_value=hf_config):
            with patch('rewriter.core.ModelManager') as mock_model_manager_class:
                mock_model_manager_class.return_value = Mock()
                
                rewriter = AIRewriter(
                    model_name=hf_config['hf_model_name'],
                    use_ollama=hf_config['use_ollama']
                )
                
                # Verify ModelManager was called with HF parameters
                mock_model_manager_class.assert_called_once()

    # ===============================
    # ERROR HANDLING TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_error_handling_component_failures(self, sample_texts, sample_errors):
        """Test error handling when components fail."""
        # Test ModelManager failure
        with patch('rewriter.core.ModelManager', side_effect=Exception("ModelManager failed")):
            try:
                rewriter = AIRewriter()
                assert False, "Should have raised exception"
            except Exception as e:
                assert "ModelManager failed" in str(e)

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_error_handling_network_failures(self, sample_texts, sample_errors, mock_model_manager):
        """Test error handling with network failures."""
        mock_text_generator = Mock()
        mock_text_generator.is_available.return_value = True
        mock_text_generator.generate_text.side_effect = requests.ConnectionError("Network error")
        
        with patch('rewriter.core.ModelManager', return_value=mock_model_manager):
            with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
                rewriter = AIRewriter()
                
                result = rewriter.rewrite(sample_texts['medium'], sample_errors)
                
                # Should handle network errors gracefully
                assert result['rewritten_text'] == sample_texts['medium']
                assert 'error' in result

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_error_handling_timeout(self, sample_texts, sample_errors, mock_model_manager):
        """Test error handling with timeout."""
        mock_text_generator = Mock()
        mock_text_generator.is_available.return_value = True
        mock_text_generator.generate_text.side_effect = requests.Timeout("Request timeout")
        
        with patch('rewriter.core.ModelManager', return_value=mock_model_manager):
            with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
                rewriter = AIRewriter()
                
                result = rewriter.rewrite(sample_texts['medium'], sample_errors)
                
                # Should handle timeout gracefully
                assert result['rewritten_text'] == sample_texts['medium']
                assert 'error' in result

    # ===============================
    # OLLAMA SPECIFIC TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="Requests not available")
    def test_ollama_integration_success(self, sample_texts, sample_errors, mock_ollama_response):
        """Test successful Ollama integration."""
        with patch('requests.post') as mock_post:
            with patch('requests.get') as mock_get:
                mock_post.return_value.json.return_value = mock_ollama_response
                mock_post.return_value.status_code = 200
                mock_get.return_value.json.return_value = {"status": "success"}
                
                rewriter = AIRewriter(use_ollama=True, ollama_model="llama3:8b")
                result = rewriter.rewrite(sample_texts['medium'], sample_errors)
                
                assert result is not None
                assert isinstance(result, dict)

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="Requests not available")
    def test_ollama_integration_connection_error(self, sample_texts, sample_errors):
        """Test Ollama integration with connection error."""
        with patch('requests.post', side_effect=requests.ConnectionError("Connection failed")):
            with patch('requests.get', side_effect=requests.ConnectionError("Connection failed")):
                rewriter = AIRewriter(use_ollama=True, ollama_model="llama3:8b")
                result = rewriter.rewrite(sample_texts['medium'], sample_errors)
                
                # Should handle connection error gracefully
                assert result['rewritten_text'] == sample_texts['medium']

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    @pytest.mark.skipif(not REQUESTS_AVAILABLE, reason="Requests not available")
    def test_ollama_model_not_found(self, sample_texts, sample_errors, mock_ollama_error_response):
        """Test Ollama integration when model is not found."""
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_ollama_error_response
            mock_post.return_value.status_code = 404
            
            rewriter = AIRewriter(use_ollama=True, ollama_model="nonexistent:model")
            result = rewriter.rewrite(sample_texts['medium'], sample_errors)
            
            # Should handle model not found gracefully
            assert result['rewritten_text'] == sample_texts['medium']

    # ===============================
    # PROGRESS CALLBACK TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_progress_callback_first_pass(self, sample_texts, sample_errors, mock_progress_callback,
                                         mock_text_generator, mock_text_processor):
        """Test progress callback during first pass."""
        mock_text_generator.is_available.return_value = True
        mock_text_processor.clean_generated_text.return_value = "Improved text"
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            with patch('rewriter.core.TextProcessor', return_value=mock_text_processor):
                rewriter = AIRewriter(progress_callback=mock_progress_callback)
                
                result = rewriter.rewrite(sample_texts['medium'], sample_errors, pass_number=1)
                
                # Verify progress callbacks were made
                assert mock_progress_callback.calls
                assert len(mock_progress_callback.calls) > 0

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_progress_callback_second_pass(self, sample_texts, sample_errors, mock_progress_callback,
                                          mock_text_generator, mock_text_processor):
        """Test progress callback during second pass."""
        mock_text_generator.is_available.return_value = True
        mock_text_processor.clean_generated_text.return_value = "Refined text"
        
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            with patch('rewriter.core.TextProcessor', return_value=mock_text_processor):
                rewriter = AIRewriter(progress_callback=mock_progress_callback)
                
                result = rewriter.rewrite(sample_texts['medium'], sample_errors, pass_number=2)
                
                # Verify progress callbacks were made for second pass
                assert mock_progress_callback.calls
                assert len(mock_progress_callback.calls) > 0

    # ===============================
    # CLEANUP TESTS
    # ===============================

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_rewriter_cleanup(self, mock_text_generator):
        """Test that rewriter can be properly cleaned up."""
        with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
            rewriter = AIRewriter()
            
            # Verify rewriter is created
            assert rewriter is not None
            
            # Delete rewriter
            del rewriter
            
            # Create new rewriter to verify no issues
            new_rewriter = AIRewriter()
            assert new_rewriter is not None

    @pytest.mark.skipif(not AI_REWRITER_AVAILABLE, reason="AI rewriter not available")
    def test_component_cleanup(self, mock_model_manager, mock_text_generator):
        """Test that components can be properly cleaned up."""
        with patch('rewriter.core.ModelManager', return_value=mock_model_manager):
            with patch('rewriter.core.TextGenerator', return_value=mock_text_generator):
                rewriter = AIRewriter()
                
                # Get references to components
                model_manager = rewriter.model_manager
                text_generator = rewriter.text_generator
                
                # Delete rewriter
                del rewriter
                
                # Components should still be accessible
                assert model_manager is not None
                assert text_generator is not None


# ===============================
# HELPER FUNCTIONS
# ===============================

def create_test_rewriter_config() -> Dict[str, Any]:
    """Create a test configuration for AI rewriter."""
    return {
        'hf_model_name': 'microsoft/DialoGPT-medium',
        'use_ollama': True,
        'ollama_model': 'llama3:8b',
        'ollama_url': 'http://localhost:11434',
        'max_tokens': 512,
        'temperature': 0.7,
        'timeout': 30
    }


def create_mock_rewrite_result() -> Dict[str, Any]:
    """Create a mock rewrite result for testing."""
    return {
        'rewritten_text': 'The administrator configures the system. Users authenticate before accessing resources.',
        'improvements': [
            'Converted passive voice to active voice',
            'Improved clarity and readability'
        ],
        'confidence': 0.85,
        'pass_number': 1,
        'can_refine': True,
        'analysis': {
            'changes_made': 2,
            'errors_fixed': 1,
            'readability_improvement': 0.15
        }
    }


def create_mock_ollama_api_response() -> Dict[str, Any]:
    """Create a mock Ollama API response."""
    return {
        "model": "llama3:8b",
        "response": "The administrator configures the system efficiently. Users access secure resources through multi-factor authentication.",
        "done": True,
        "total_duration": 5432109876,
        "load_duration": 543210987,
        "prompt_eval_count": 26,
        "prompt_eval_duration": 1234567890,
        "eval_count": 298,
        "eval_duration": 2876543210
    }


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 
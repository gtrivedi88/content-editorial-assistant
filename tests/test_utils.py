"""
Test Utilities Module
Shared utilities, fixtures, and constants for all AI rewriting system tests.
"""

import pytest
from unittest.mock import MagicMock

class TestConfig:
    """Configuration constants for tests to avoid hardcoding."""
    
    # Model configuration
    DEFAULT_MODEL = "test-model"
    OLLAMA_MODEL = "llama3:8b"
    OLLAMA_URL = "http://localhost:11434/api/generate"
    OLLAMA_BASE_URL = "http://localhost:11434"
    
    # Test data
    SAMPLE_TEXT = "Original text to be rewritten"
    SAMPLE_IMPROVED_TEXT = "Cleaned improved text"
    SAMPLE_RAW_RESPONSE = "Raw AI response"
    SAMPLE_REFINED_TEXT = "Final refined text"
    SAMPLE_POLISHED_TEXT = "Final polished text"
    SAMPLE_EMPTY_TEXT = ""
    
    # Confidence thresholds
    MIN_CONFIDENCE = 0.0
    MAX_CONFIDENCE = 1.0
    EXPECTED_CONFIDENCE = 0.85
    HIGH_CONFIDENCE = 0.92
    
    # Context options
    VALID_CONTEXTS = ['sentence', 'paragraph', 'document']
    
    # Prompt limits
    MAX_PROMPT_LENGTH = 1500
    MIN_PROMPT_LENGTH = 5
    
    # Test identifiers
    TEST_SESSION_ID = "test-session"
    TEST_STEP = "test_step"
    TEST_STATUS = "Test status"
    
    # File-related constants
    TEST_FILENAME_TXT = "test.txt"
    TEST_FILENAME_MD = "test.md"
    TEST_FILENAME_ADOC = "test.adoc"
    TEST_FILENAME_PDF = "test.pdf"
    TEST_FILENAME_DOCX = "test.docx"
    
    # Content extraction constants
    EXTRACTED_PDF_TEXT = "Extracted PDF text"
    EXTRACTED_DOCX_TEXT = "Extracted DOCX text"
    
    # Error messages
    ERROR_NO_FILE_SELECTED = "No file selected"
    ERROR_FILE_TYPE_NOT_SUPPORTED = "File type not supported"
    ERROR_FILE_TOO_LARGE = "File too large"
    ERROR_FAILED_TO_EXTRACT = "Failed to extract text from file"
    ERROR_NO_CONTENT_PROVIDED = "No content provided"
    ERROR_NO_FIRST_PASS_RESULT = "No first pass result provided"
    ERROR_RESOURCE_NOT_FOUND = "Resource not found"
    
    # Status values
    STATUS_HEALTHY = "healthy"
    STATUS_UNHEALTHY = "unhealthy"
    STATUS_AVAILABLE = "available"
    STATUS_CONNECTION_FAILED = "connection_failed"
    STATUS_MODEL_NOT_FOUND = "model_not_found"
    
    # Event names
    EVENT_CONNECTED = "connected"
    EVENT_PROGRESS = "progress"
    EVENT_SESSION_JOINED = "session_joined"
    
    # Secret keys and security
    TEST_SECRET_KEY = "test-secret-key"
    PRODUCTION_SECRET_KEY = "production-secret-key"
    DOCKER_SECRET_KEY = "docker-secret-key"
    
    # Database URLs
    TEST_DATABASE_URL = "postgresql://user:pass@localhost/db"
    MEMORY_DATABASE_URL = "sqlite:///:memory:"
    DEFAULT_DATABASE_URL = "sqlite:///style_guide.db"
    
    # API keys
    TEST_API_KEY = "test-api-key"
    CLOUD_API_KEY = "cloud-api-key"
    
    # Kubernetes config
    K8S_DATABASE_URL = "postgresql://k8s-user:k8s-pass@postgres:5432/app"
    K8S_REDIS_URL = "redis://redis-service:6379/0"
    K8S_OLLAMA_URL = "http://ollama-service:11434"
    
    # Cloud environment config
    CLOUD_PROVIDER = "aws"
    AWS_REGION = "us-east-1"
    LOG_LEVEL_WARNING = "WARNING"
    LOG_LEVEL_DEBUG = "DEBUG"
    
    # Multi-tenant config
    TENANT_1_ID = "tenant1"
    TENANT_2_ID = "tenant2"
    TENANT_1_MODEL = "llama3:8b"
    TENANT_2_MODEL = "llama3:70b"
    TENANT_1_SIZE = 8 * 1024 * 1024  # 8MB
    TENANT_2_SIZE = 32 * 1024 * 1024  # 32MB
    
    # Test statistics
    WORD_COUNT_LARGE = 5000
    SENTENCE_COUNT_LARGE = 1000
    
    # Configuration validation
    MIN_SECRET_KEY_LENGTH = 10
    MAX_FILE_SIZE_LIMIT = 100 * 1024 * 1024  # 100MB
    MAX_TIMEOUT = 300  # 5 minutes
    MIN_TEMPERATURE = 0.0
    MAX_TEMPERATURE = 2.0
    
    # Test environment names
    ENV_DEVELOPMENT = "development"
    ENV_PRODUCTION = "production"
    ENV_TESTING = "testing"
    ENV_DEFAULT = "default"
    
    # AI Model types
    MODEL_TYPE_OLLAMA = "ollama"
    MODEL_TYPE_HUGGINGFACE = "huggingface"
    MODEL_TYPE_OPENAI = "openai"
    
    # Format types
    FORMAT_ASCIIDOC = "asciidoc"
    FORMAT_MARKDOWN = "markdown"
    FORMAT_TXT = "txt"
    
    # Test prompts
    TEST_PROMPT = "Test prompt"
    SELF_REVIEW_PROMPT = "Self-review prompt"
    TEST_PROMPT_SUFFICIENT_LENGTH = "This is a test prompt with sufficient length."
    
    # Docker and deployment
    DOCKER_FLASK_ENV = "production"
    DOCKER_OLLAMA_HOST = "0.0.0.0"
    DOCKER_OLLAMA_PORT = "11434"
    
    # Test rule types
    RULE_TYPE_PASSIVE_VOICE = "passive_voice"
    RULE_TYPE_SENTENCE_LENGTH = "sentence_length"
    RULE_TYPE_AMBIGUITY = "ambiguity"
    RULE_TYPE_ABBREVIATIONS = "abbreviations"
    RULE_TYPE_INCLUSIVE_LANGUAGE = "inclusive_language"
    
    # Test severity levels
    SEVERITY_LOW = "low"
    SEVERITY_MEDIUM = "medium"
    SEVERITY_HIGH = "high"
    SEVERITY_CRITICAL = "critical"
    
    # Test improvement types
    IMPROVEMENT_PASSIVE_TO_ACTIVE = "Converted passive voice to active"
    IMPROVEMENT_SHORTENED_SENTENCE = "Break into shorter sentences"
    IMPROVEMENT_CLARITY_ENHANCEMENT = "Enhanced clarity"
    IMPROVEMENT_TEST_GENERIC = "Test improvement"
    
    # Test detector types
    DETECTOR_MISSING_ACTOR = "missing_actor"
    DETECTOR_PRONOUN_AMBIGUITY = "pronoun_ambiguity"
    DETECTOR_UNSUPPORTED_CLAIM = "unsupported_claim"
    DETECTOR_FABRICATION = "fabrication"


class TestFixtures:
    """Shared test fixtures and data."""
    
    @staticmethod
    def get_sample_errors():
        """Get sample errors for testing."""
        return [
            {
                'type': TestConfig.RULE_TYPE_PASSIVE_VOICE,
                'message': 'Passive voice detected',
                'severity': TestConfig.SEVERITY_MEDIUM,
                'sentence': 'The document was written by the team.',
                'suggestions': ['Use active voice instead']
            },
            {
                'type': TestConfig.RULE_TYPE_SENTENCE_LENGTH,
                'message': 'Sentence too long',
                'severity': TestConfig.SEVERITY_HIGH,
                'sentence': 'This is a very long sentence that contains many clauses and should be shortened.',
                'suggestions': [TestConfig.IMPROVEMENT_SHORTENED_SENTENCE]
            },
            {
                'type': TestConfig.RULE_TYPE_AMBIGUITY,
                'subtype': TestConfig.DETECTOR_MISSING_ACTOR,
                'message': 'Missing actor in passive voice',
                'severity': TestConfig.SEVERITY_HIGH,
                'sentence': 'The configuration is updated automatically.',
                'suggestions': ['Specify who or what updates the configuration']
            }
        ]
    
    @staticmethod
    def get_mock_ollama_response():
        """Get mock Ollama API response."""
        return {
            "model": TestConfig.OLLAMA_MODEL,
            "response": TestConfig.SAMPLE_IMPROVED_TEXT,
            "done": True
        }
    
    @staticmethod
    def get_mock_progress_callback():
        """Get mock progress callback function."""
        return MagicMock()
    
    @staticmethod
    def get_mock_evaluation_result():
        """Get mock evaluation result."""
        return {
            'improvements': [TestConfig.IMPROVEMENT_PASSIVE_TO_ACTIVE],
            'confidence': TestConfig.EXPECTED_CONFIDENCE,
            'model_used': TestConfig.DEFAULT_MODEL
        }
    
    @staticmethod
    def get_mock_web_response(status_code=200, json_data=None):
        """Get mock web response."""
        from unittest.mock import MagicMock
        mock_response = MagicMock()
        mock_response.status_code = status_code
        mock_response.json.return_value = json_data or {}
        return mock_response
    
    @staticmethod
    def get_mock_file_data(filename=None, content=None):
        """Get mock file data for testing."""
        return {
            'filename': filename or TestConfig.TEST_FILENAME_TXT,
            'content': content or TestConfig.SAMPLE_TEXT
        }
    
    @staticmethod
    def get_mock_health_check_response():
        """Get mock health check response."""
        return {
            'status': TestConfig.STATUS_HEALTHY,
            'ollama_status': TestConfig.STATUS_AVAILABLE,
            'ollama_model': TestConfig.OLLAMA_MODEL
        }
    
    @staticmethod
    def get_mock_analysis_statistics():
        """Get mock analysis statistics."""
        return {
            'word_count': TestConfig.WORD_COUNT_LARGE,
            'sentence_count': TestConfig.SENTENCE_COUNT_LARGE
        }

    @staticmethod
    def get_mock_prompt_config():
        """Get mock prompt configuration that matches the real config structure."""
        return {
            'rules': {
                'language_priority': {
                    'primary_command': 'FIRST, apply these CRITICAL language and grammar fixes: 1) Rewrite the text to address the user directly. Use the second person ("you") for all instructions or actions the user should take. 2) Convert all passive voice to active voice.'
                },
                'second_person': {
                    'primary_command': 'Your primary goal is to rewrite the text to address the user directly. Use the second person ("you") for all instructions or actions the user should take. You MUST NOT use any first-person pronouns like "we" or "our", and you MUST use the active voice.'
                },
                TestConfig.RULE_TYPE_PASSIVE_VOICE: {
                    'instruction': 'CRITICAL: Use the present tense and active voice. Convert all passive sentences to active ones to be more direct and clear.'
                },
                TestConfig.RULE_TYPE_SENTENCE_LENGTH: {
                    'instruction': 'Break overly long sentences into shorter, clearer ones (15-20 words each).'
                },
                TestConfig.RULE_TYPE_AMBIGUITY: {
                    'instruction': 'Resolve ambiguous content. Clarify unclear references and ensure pronouns have clear antecedents.'
                },
                'abbreviations': {
                    'instruction': 'Fix issues with abbreviations. Do not use Latin abbreviations like "e.g." or "i.e."; use their English equivalents.'
                },
                'contractions': {
                    'instruction': 'For a formal tone, spell out contractions (e.g., use "do not" instead of "don\'t").'
                },
                'pronouns': {
                    'instruction': 'CRITICAL: Ensure pronouns are used correctly. The text must address the user directly with "you" (second person). Avoid first-person ("we", "our") and gender-specific ("he", "she") pronouns.'
                },
                'verbs': {
                    'instruction': 'CRITICAL: Use the present tense and active voice. Convert all passive sentences to active ones to be more direct and clear.'
                }
            }
        }


class TestValidators:
    """Validation utilities for test assertions."""
    
    @staticmethod
    def validate_rewrite_result(result, expected_text=None, expected_confidence=None):
        """Validate a rewrite result structure."""
        required_keys = ['rewritten_text', 'confidence', 'improvements']
        
        for key in required_keys:
            assert key in result, f"Missing required key: {key}"
        
        if expected_text:
            assert result['rewritten_text'] == expected_text
        
        if expected_confidence:
            assert result['confidence'] == expected_confidence
        
        assert isinstance(result['improvements'], list)
        assert TestConfig.MIN_CONFIDENCE <= result['confidence'] <= TestConfig.MAX_CONFIDENCE
    
    @staticmethod
    def validate_prompt_content(prompt, should_contain=None, should_not_contain=None):
        """Validate prompt content and structure."""
        assert isinstance(prompt, str)
        assert len(prompt) > TestConfig.MIN_PROMPT_LENGTH
        
        if should_contain:
            for text in should_contain:
                assert text.lower() in prompt.lower(), f"Prompt missing required text: {text}"
        
        if should_not_contain:
            for text in should_not_contain:
                assert text.lower() not in prompt.lower(), f"Prompt contains forbidden text: {text}"
    
    @staticmethod
    def validate_system_info(system_info):
        """Validate system information structure."""
        required_keys = ['model_info', 'available_components', 'is_ready']
        
        for key in required_keys:
            assert key in system_info, f"Missing required key: {key}"
        
        assert isinstance(system_info['available_components'], list)
        assert isinstance(system_info['is_ready'], bool)
    
    @staticmethod
    def validate_error_response(response, expected_error=None):
        """Validate error response structure."""
        assert 'error' in response
        if expected_error:
            assert response['error'] == expected_error
    
    @staticmethod
    def validate_file_response(response, expected_filename=None):
        """Validate file response structure."""
        if expected_filename:
            assert response.get('filename') == expected_filename
    
    @staticmethod
    def validate_health_response(response):
        """Validate health check response structure."""
        assert 'status' in response
        assert response['status'] in [TestConfig.STATUS_HEALTHY, TestConfig.STATUS_UNHEALTHY]


class TestMockFactory:
    """Factory for creating consistent mock objects."""
    
    @staticmethod
    def create_mock_model_manager(use_ollama=False):
        """Create mock ModelManager with consistent behavior."""
        mock = MagicMock()
        mock.use_ollama = use_ollama
        mock.ollama_model = TestConfig.OLLAMA_MODEL
        mock.ollama_url = TestConfig.OLLAMA_URL
        mock.model_name = TestConfig.DEFAULT_MODEL
        mock.is_available.return_value = True
        mock.get_model_info.return_value = {
            'use_ollama': use_ollama,
            'ollama_model': TestConfig.OLLAMA_MODEL if use_ollama else None,
            'hf_model': TestConfig.DEFAULT_MODEL if not use_ollama else None,
            'is_available': True
        }
        return mock
    
    @staticmethod
    def create_mock_prompt_generator():
        """Create mock PromptGenerator with consistent behavior."""
        mock = MagicMock()
        mock.style_guide_name = 'ibm_style'
        mock.use_ollama = True
        mock.prompt_config = TestFixtures.get_mock_prompt_config()
        mock.generate_prompt.return_value = TestConfig.TEST_PROMPT
        mock.generate_self_review_prompt.return_value = TestConfig.SELF_REVIEW_PROMPT
        return mock
    
    @staticmethod
    def create_mock_text_generator():
        """Create mock TextGenerator with consistent behavior."""
        mock = MagicMock()
        mock.is_available.return_value = True
        mock.generate_text.return_value = TestConfig.SAMPLE_RAW_RESPONSE
        mock.generate_with_ollama.return_value = TestConfig.SAMPLE_IMPROVED_TEXT
        return mock
    
    @staticmethod
    def create_mock_text_processor():
        """Create mock TextProcessor with consistent behavior."""
        mock = MagicMock()
        mock.clean_generated_text.return_value = TestConfig.SAMPLE_IMPROVED_TEXT
        mock.rule_based_rewrite.return_value = TestConfig.SAMPLE_IMPROVED_TEXT
        return mock
    
    @staticmethod
    def create_mock_evaluator():
        """Create mock RewriteEvaluator with consistent behavior."""
        mock = MagicMock()
        mock.calculate_confidence.return_value = TestConfig.EXPECTED_CONFIDENCE
        mock.evaluate_rewrite_quality.return_value = TestFixtures.get_mock_evaluation_result()
        mock.extract_improvements.return_value = [TestConfig.IMPROVEMENT_TEST_GENERIC]
        mock.extract_second_pass_improvements.return_value = [TestConfig.IMPROVEMENT_CLARITY_ENHANCEMENT]
        mock.calculate_second_pass_confidence.return_value = TestConfig.HIGH_CONFIDENCE
        mock.analyze_changes.return_value = {
            'word_count_change': 0,
            'sentence_count_change': 0,
            'structural_changes': []
        }
        return mock
    
    @staticmethod
    def create_mock_web_client():
        """Create mock web client for testing API endpoints."""
        mock = MagicMock()
        mock.post.return_value = TestFixtures.get_mock_web_response()
        mock.get.return_value = TestFixtures.get_mock_web_response()
        return mock


 
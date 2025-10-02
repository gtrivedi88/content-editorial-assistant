"""
Testing Agent Configuration
Centralized configuration for testing infrastructure and AI analysis.
Reuses the existing MODEL_PROVIDER configuration from .env
"""

import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class TestingConfig:
    """Configuration for testing agent and AI analysis."""
    
    # REUSE existing model configuration from your .env
    MODEL_PROVIDER = os.getenv('MODEL_PROVIDER', 'api').lower()
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:11434')
    MODEL_ID = os.getenv('MODEL_ID', 'llama3.2:latest')
    ACCESS_TOKEN = os.getenv('ACCESS_TOKEN')
    CERT_PATH = os.getenv('CERT_PATH')
    TIMEOUT = int(os.getenv('TIMEOUT', '30'))
    
    # Model generation parameters (reuse from main app)
    MODEL_TEMPERATURE = float(os.getenv('MODEL_TEMPERATURE', '0.4'))
    MODEL_MAX_TOKENS = int(os.getenv('MODEL_MAX_TOKENS', '3072'))
    MODEL_TOP_P = float(os.getenv('MODEL_TOP_P', '0.7'))
    MODEL_TOP_K = int(os.getenv('MODEL_TOP_K', '20'))
    
    # Test Runner Configuration
    APP_URL = os.getenv('APP_URL', 'http://localhost:5000')
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    PARALLEL_TESTS = os.getenv('PARALLEL_TESTS', 'true').lower() == 'true'
    TEST_TIMEOUT = int(os.getenv('TEST_TIMEOUT', '300'))
    
    @classmethod
    def get_ai_config(cls) -> Dict[str, Any]:
        """Get configuration for the active AI provider (same as main app)."""
        config = {
            'provider': cls.MODEL_PROVIDER,
            'temperature': cls.MODEL_TEMPERATURE,
            'max_tokens': cls.MODEL_MAX_TOKENS,
            'top_p': cls.MODEL_TOP_P,
            'top_k': cls.MODEL_TOP_K,
        }
        
        if cls.MODEL_PROVIDER == 'ollama':
            config.update({
                'model': cls.MODEL_ID,
                'base_url': cls.BASE_URL,
                'timeout': cls.TIMEOUT,
            })
        elif cls.MODEL_PROVIDER == 'api':
            config.update({
                'model': cls.MODEL_ID,
                'base_url': cls.BASE_URL,
                'api_key': cls.ACCESS_TOKEN,
                'timeout': cls.TIMEOUT,
                'cert_path': cls.CERT_PATH,
            })
        elif cls.MODEL_PROVIDER == 'llamastack':
            config.update({
                'model': os.getenv('CEA_MODEL_ID', 'style_analyzer_model'),
            })
        
        return config
    
    @classmethod
    def validate_ai_config(cls) -> bool:
        """Validate current AI configuration (same logic as ModelConfig)."""
        provider = cls.MODEL_PROVIDER
        
        # Allow explicitly disabling AI
        if provider in ['none', 'disabled', 'skip']:
            return False
        
        if provider == 'ollama':
            return bool(cls.BASE_URL and cls.MODEL_ID)
        elif provider == 'api':
            return bool(cls.BASE_URL and cls.MODEL_ID and cls.ACCESS_TOKEN)
        elif provider == 'llamastack':
            return bool(os.environ.get('LIGHTRAIL_LLAMA_STACK_BASE_URL'))
        
        return False
    
    @classmethod
    def get_model_name(cls) -> str:
        """Get the model name for the active provider."""
        return cls.MODEL_ID
    
    @classmethod
    def get_ai_info(cls) -> Dict[str, Any]:
        """Get information about the current AI setup (same as ModelConfig)."""
        config = cls.get_ai_config()
        is_valid = cls.validate_ai_config()
        
        base_info = {
            'provider': config['provider'],
            'model': config.get('model', 'Unknown'),
            'status': 'Active' if is_valid else 'Configuration Invalid',
            'available': is_valid
        }
        
        if config['provider'] == 'ollama':
            return {
                **base_info,
                'type': 'Local (Ollama)',
                'url': config.get('base_url')
            }
        elif config['provider'] == 'api':
            return {
                **base_info,
                'type': 'API Provider',
                'url': config.get('base_url'),
                'api_configured': bool(config.get('api_key'))
            }
        elif config['provider'] == 'llamastack':
            return {
                **base_info,
                'type': 'Lightrail Llama Stack',
                'platform': 'Lightrail',
                'url': os.environ.get('LIGHTRAIL_LLAMA_STACK_BASE_URL', 'Not configured')
            }
        
        return {'status': 'Unknown provider', 'available': False}
    
    @classmethod
    def get_test_config(cls) -> Dict[str, Any]:
        """Get configuration for test runner."""
        return {
            'app_url': cls.APP_URL,
            'headless': cls.HEADLESS,
            'parallel': cls.PARALLEL_TESTS,
            'timeout': cls.TEST_TIMEOUT,
        }


"""
Model Configuration
Centralized configuration for all AI model providers.

Loads configuration from environment variables
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class ModelConfig:
    """Configuration for AI model providers."""
    
    MODEL_PROVIDER = os.getenv('MODEL_PROVIDER')
    BASE_URL = os.getenv('BASE_URL')
    MODEL_ID = os.getenv('MODEL_ID')
    TIMEOUT = int(os.getenv('TIMEOUT', '60'))
    ACCESS_TOKEN = os.getenv('ACCESS_TOKEN', None)
    CERT_PATH = os.getenv("CERT_PATH", True)
    
    TEMPERATURE = float(os.getenv('MODEL_TEMPERATURE'))
    MAX_TOKENS = int(os.getenv('MODEL_MAX_TOKENS'))
    TOP_P = float(os.getenv('MODEL_TOP_P'))
    TOP_K = int(os.getenv('MODEL_TOP_K'))
    
    @classmethod
    def get_active_config(cls) -> Dict[str, Any]:
        """Get configuration for the active provider."""
        config = {
            'provider_type': cls.MODEL_PROVIDER,
            'temperature': cls.TEMPERATURE,
            'max_tokens': cls.MAX_TOKENS,
            'top_p': cls.TOP_P,
            'top_k': cls.TOP_K,
        }
        
        if cls.MODEL_PROVIDER == 'ollama':
            config.update({
                'base_url': cls.BASE_URL,
                'model': cls.MODEL_ID,
                'timeout': cls.TIMEOUT,
            })
        elif cls.MODEL_PROVIDER == 'api':
            config.update({
                'base_url': cls.BASE_URL,
                'model': cls.MODEL_ID,
                'api_key': cls.ACCESS_TOKEN,
                'timeout': cls.TIMEOUT,
                'cert_path': cls.CERT_PATH,
            })
        
        return config
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate current configuration."""
        config = cls.get_active_config()
        provider = config['provider_type']
        
        if provider == 'ollama':
            return bool(config.get('base_url') and config.get('model'))
        elif provider == 'api':
            return bool(config.get('base_url') and config.get('model') and config.get('api_key'))
        
        return False
    
    @classmethod
    def get_model_info(cls) -> Dict[str, Any]:
        """Get information about the current model setup."""
        config = cls.get_active_config()
        provider = config['provider_type']
        is_valid = cls.validate_config()
        
        base_info = {
            'model': config.get('model', 'Unknown'),
            'status': 'Active' if is_valid else 'Configuration Invalid'
        }
        
        if provider == 'ollama':
            return {
                **base_info,
                'type': 'Local (Ollama)',
                'url': config.get('base_url')
            }
        elif provider == 'api':
            return {
                **base_info,
                'type': 'API Provider',
                'url': config.get('base_url')
            }        
        return {'status': 'Unknown provider'} 
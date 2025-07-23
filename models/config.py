"""
Model Configuration
Central configuration for all AI model providers.

INSTRUCTIONS FOR CHANGING MODELS:
===============================

1. TO USE OLLAMA (Local Models):
   - Set ACTIVE_PROVIDER = 'ollama'
   - Set OLLAMA_MODEL to any model you have pulled locally
   - Ensure Ollama is running: `ollama serve`
   - Pull models: `ollama pull llama3:8b`

2. TO USE API PROVIDERS (Groq, HuggingFace, etc.):
   - Set ACTIVE_PROVIDER = 'api'
   - Set API_PROVIDER to 'groq', 'huggingface', or custom
   - Set API_MODEL to the model name
   - Set API_BASE_URL and API_KEY for your provider
   - Examples:
     * Groq: llama3-70b-8192, mixtral-8x7b-32768
     * HuggingFace: meta-llama/Llama-2-70b-chat-hf

3. TO ADD NEW PROVIDERS:
   - Create new provider class in providers/
   - Add provider configuration below
   - Register in factory.py
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

class ModelConfig:
    """Centralized model configuration."""
    
    # =============================================================================
    # MAIN SWITCH: Change this to switch between providers
    # Options: 'ollama', 'api'
    # =============================================================================
    ACTIVE_PROVIDER = os.getenv('MODEL_PROVIDER', 'ollama')
    
    # =============================================================================
    # OLLAMA CONFIGURATION (Local Models)
    # =============================================================================
    OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3:8b')  # Change to any local model
    OLLAMA_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '60'))
    
    # =============================================================================
    # API PROVIDER CONFIGURATION (Remote Models)
    # =============================================================================
    API_PROVIDER = os.getenv('API_PROVIDER', 'groq')  # groq, huggingface, openai, etc.
    API_MODEL = os.getenv('API_MODEL', 'llama3-70b-8192')  # Change to any API model
    API_KEY = os.getenv('API_KEY', '')  # Set your API key in environment
    
    # Provider-specific base URLs
    API_BASE_URLS = {
        'groq': 'https://api.groq.com/openai/v1',
        'huggingface': 'https://api-inference.huggingface.co/models',
        'openai': 'https://api.openai.com/v1',
        # Add more providers here as needed
    }
    
    API_BASE_URL = os.getenv('API_BASE_URL') or API_BASE_URLS.get(API_PROVIDER, '')
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '30'))
    
    # =============================================================================
    # GENERATION PARAMETERS (Applied to all providers)
    # =============================================================================
    TEMPERATURE = float(os.getenv('MODEL_TEMPERATURE', '0.4'))
    MAX_TOKENS = int(os.getenv('MODEL_MAX_TOKENS', '512'))
    TOP_P = float(os.getenv('MODEL_TOP_P', '0.7'))
    TOP_K = int(os.getenv('MODEL_TOP_K', '20'))
    
    # =============================================================================
    # QUICK CONFIGURATION PRESETS
    # Uncomment one of these blocks to quickly switch configurations
    # =============================================================================
    
    # # PRESET 1: Local Ollama (Default)
    # ACTIVE_PROVIDER = 'ollama'
    # OLLAMA_MODEL = 'llama3:8b'
    
    # # PRESET 2: Groq API
    # ACTIVE_PROVIDER = 'api'
    # API_PROVIDER = 'groq'
    # API_MODEL = 'llama3-70b-8192'
    
    # # PRESET 3: HuggingFace API
    # ACTIVE_PROVIDER = 'api'
    # API_PROVIDER = 'huggingface'
    # API_MODEL = 'meta-llama/Llama-2-70b-chat-hf'
    
    @classmethod
    def get_active_config(cls) -> Dict[str, Any]:
        """Get configuration for the currently active provider."""
        base_config = {
            'provider_type': cls.ACTIVE_PROVIDER,
            'temperature': cls.TEMPERATURE,
            'max_tokens': cls.MAX_TOKENS,
            'top_p': cls.TOP_P,
            'top_k': cls.TOP_K,
        }
        
        if cls.ACTIVE_PROVIDER == 'ollama':
            base_config.update({
                'base_url': cls.OLLAMA_BASE_URL,
                'model': cls.OLLAMA_MODEL,
                'timeout': cls.OLLAMA_TIMEOUT,
            })
        elif cls.ACTIVE_PROVIDER == 'api':
            base_config.update({
                'provider_name': cls.API_PROVIDER,
                'base_url': cls.API_BASE_URL,
                'model': cls.API_MODEL,
                'api_key': cls.API_KEY,
                'timeout': cls.API_TIMEOUT,
            })
        
        return base_config
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate current configuration."""
        config = cls.get_active_config()
        
        if config['provider_type'] == 'ollama':
            return bool(config['base_url'] and config['model'])
        elif config['provider_type'] == 'api':
            return bool(config['base_url'] and config['model'] and config['api_key'])
        
        return False
    
    @classmethod
    def get_model_info(cls) -> Dict[str, Any]:
        """Get human-readable information about current model setup."""
        config = cls.get_active_config()
        
        if config['provider_type'] == 'ollama':
            return {
                'type': 'Local (Ollama)',
                'model': config['model'],
                'url': config['base_url'],
                'status': 'Active' if cls.validate_config() else 'Configuration Invalid'
            }
        elif config['provider_type'] == 'api':
            return {
                'type': f'API ({config["provider_name"].title()})',
                'model': config['model'],
                'provider': config['provider_name'],
                'url': config['base_url'],
                'status': 'Active' if cls.validate_config() else 'Configuration Invalid'
            }
        
        return {'status': 'Unknown provider type'} 
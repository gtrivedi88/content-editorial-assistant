"""
API Provider
Handles external API-based model providers like Groq, HuggingFace, OpenAI, etc.

USAGE:
======
Configure in models/config.py:
- Set ACTIVE_PROVIDER = 'api'
- Set API_PROVIDER = 'groq' (or 'huggingface', 'openai')
- Set API_MODEL = 'llama3-70b-8192' (or any model supported by the provider)
- Set API_KEY environment variable

EXAMPLES:
=========
# Groq
API_PROVIDER = 'groq'
API_MODEL = 'llama3-70b-8192'
API_KEY = 'your-groq-api-key'

# HuggingFace
API_PROVIDER = 'huggingface'
API_MODEL = 'meta-llama/Llama-2-70b-chat-hf'
API_KEY = 'your-hf-api-key'
"""

import requests
import logging
from typing import Dict, Any
from .base_provider import BaseModelProvider

logger = logging.getLogger(__name__)


class APIProvider(BaseModelProvider):
    """
    Provider for external API-based models.
    
    Supports multiple providers:
    - Groq: Fast inference for Llama, Mixtral models
    - HuggingFace: Inference API for various models
    - OpenAI: GPT models
    - Custom: Any OpenAI-compatible API
    """
    
    def _validate_config(self) -> None:
        """Validate API provider configuration."""
        required_fields = ['provider_name', 'base_url', 'model', 'api_key']
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(f"Missing required API config: {field}")
        
        # Ensure base_url format is correct
        if not self.config['base_url'].startswith('http'):
            raise ValueError("API base_url must start with http:// or https://")
        
        # Validate provider-specific requirements
        provider = self.config['provider_name'].lower()
        if provider == 'groq':
            self._validate_groq_config()
        elif provider == 'huggingface':
            self._validate_huggingface_config()
        elif provider == 'openai':
            self._validate_openai_config()
    
    def _validate_groq_config(self) -> None:
        """Validate Groq-specific configuration."""
        # Common Groq models - add more as they become available
        groq_models = [
            'llama3-70b-8192',
            'llama3-8b-8192',
            'mixtral-8x7b-32768',
            'gemma-7b-it'
        ]
        
        model = self.config['model']
        if model not in groq_models:
            logger.warning(
                f"Model '{model}' may not be available on Groq. "
                f"Common models: {groq_models}"
            )
    
    def _validate_huggingface_config(self) -> None:
        """Validate HuggingFace-specific configuration."""
        # HF models typically have format: organization/model-name
        model = self.config['model']
        if '/' not in model:
            logger.warning(
                f"HuggingFace model '{model}' should typically be in format 'org/model-name'"
            )
    
    def _validate_openai_config(self) -> None:
        """Validate OpenAI-specific configuration."""
        # Common OpenAI models
        openai_models = ['gpt-4', 'gpt-4-turbo', 'gpt-3.5-turbo']
        model = self.config['model']
        
        if not any(openai_model in model for openai_model in openai_models):
            logger.warning(f"Model '{model}' may not be a standard OpenAI model")
    
    def connect(self) -> bool:
        """
        Test connection to the API provider.
        
        Returns:
            bool: True if API is accessible
        """
        try:
            # Test connection with a minimal request
            headers = self._get_headers()
            
            # Different providers may have different health check endpoints
            test_endpoint = self._get_health_check_endpoint()
            
            response = requests.get(
                test_endpoint,
                headers=headers,
                timeout=self.config.get('timeout', 10)
            )
            
            if response.status_code in [200, 401]:  # 401 means API is responding
                self.is_connected = True
                logger.info(f"✅ Connected to {self.config['provider_name']} API")
                return True
            else:
                logger.error(f"API connection failed: {response.status_code}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Cannot connect to {self.config['provider_name']} API: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to API: {e}")
            return False
    
    def _get_health_check_endpoint(self) -> str:
        """Get the appropriate health check endpoint for the provider."""
        provider = self.config['provider_name'].lower()
        base_url = self.config['base_url']
        
        if provider == 'groq':
            return f"{base_url}/models"
        elif provider == 'huggingface':
            return f"{base_url}/{self.config['model']}"
        elif provider == 'openai':
            return f"{base_url}/models"
        else:
            # Default to models endpoint for OpenAI-compatible APIs
            return f"{base_url}/models"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get appropriate headers for the API provider."""
        provider = self.config['provider_name'].lower()
        
        headers = {
            'Content-Type': 'application/json',
        }
        
        if provider == 'groq':
            headers['Authorization'] = f"Bearer {self.config['api_key']}"
        elif provider == 'huggingface':
            headers['Authorization'] = f"Bearer {self.config['api_key']}"
        elif provider == 'openai':
            headers['Authorization'] = f"Bearer {self.config['api_key']}"
        else:
            # Default to Bearer token for most APIs
            headers['Authorization'] = f"Bearer {self.config['api_key']}"
        
        return headers
    
    def is_available(self) -> bool:
        """
        Check if the API provider and model are available.
        
        Returns:
            bool: True if ready to generate text
        """
        if not self.is_connected:
            return self.connect()
        
        # For APIs, we assume if connection works, the service is available
        return self.is_connected
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the API provider.
        
        Args:
            prompt: Input text prompt
            **kwargs: Additional generation parameters
            
        Returns:
            str: Generated text
        """
        if not self.is_available():
            logger.error(f"{self.config['provider_name']} API is not available")
            return ""
        
        # Prepare generation parameters
        params = self._prepare_generation_params(**kwargs)
        
        # Build the API request
        endpoint, payload = self._build_request(prompt, params)
        headers = self._get_headers()
        
        try:
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.config.get('timeout', 30)
            )
            
            if response.status_code == 200:
                generated_text = self._extract_response(response.json())
                
                if generated_text:
                    logger.debug(f"✅ Generated {len(generated_text)} characters")
                    return generated_text.strip()
                else:
                    logger.warning(f"{self.config['provider_name']} returned empty response")
                    return ""
            else:
                logger.error(f"❌ {self.config['provider_name']} API error: {response.status_code} - {response.text}")
                return ""
                
        except requests.exceptions.Timeout:
            logger.error(f"❌ {self.config['provider_name']} request timed out")
            return ""
        except Exception as e:
            logger.error(f"❌ {self.config['provider_name']} generation failed: {e}")
            return ""
    
    def _build_request(self, prompt: str, params: Dict[str, Any]) -> tuple:
        """Build the API request endpoint and payload."""
        provider = self.config['provider_name'].lower()
        base_url = self.config['base_url']
        
        if provider in ['groq', 'openai']:
            # OpenAI-compatible chat completions format
            endpoint = f"{base_url}/chat/completions"
            payload = {
                "model": self.config['model'],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": params['temperature'],
                "max_tokens": params['max_tokens'],
                "top_p": params['top_p'],
                "stop": ["\n\nOriginal:", "\n\nRewrite:", "###", "---"]
            }
            
        elif provider == 'huggingface':
            # HuggingFace Inference API format
            endpoint = f"{base_url}/{self.config['model']}"
            payload = {
                "inputs": prompt,
                "parameters": {
                    "temperature": params['temperature'],
                    "max_new_tokens": params['max_tokens'],
                    "top_p": params['top_p'],
                    "top_k": params['top_k'],
                    "stop": ["\n\nOriginal:", "\n\nRewrite:", "###", "---"]
                }
            }
            
        else:
            # Default to OpenAI-compatible format
            endpoint = f"{base_url}/chat/completions"
            payload = {
                "model": self.config['model'],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": params['temperature'],
                "max_tokens": params['max_tokens'],
                "top_p": params['top_p']
            }
        
        return endpoint, payload
    
    def _extract_response(self, response_data: Dict[str, Any]) -> str:
        """Extract generated text from API response."""
        provider = self.config['provider_name'].lower()
        
        if provider in ['groq', 'openai']:
            # OpenAI-compatible response format
            try:
                return response_data['choices'][0]['message']['content']
            except (KeyError, IndexError):
                logger.error(f"Unexpected {provider} response format: {response_data}")
                return ""
                
        elif provider == 'huggingface':
            # HuggingFace response format
            try:
                if isinstance(response_data, list) and len(response_data) > 0:
                    return response_data[0].get('generated_text', '')
                else:
                    return response_data.get('generated_text', '')
            except Exception:
                logger.error(f"Unexpected HuggingFace response format: {response_data}")
                return ""
                
        else:
            # Try to extract from common response formats
            try:
                # Try OpenAI format first
                if 'choices' in response_data:
                    return response_data['choices'][0]['message']['content']
                # Try simple text response
                elif 'text' in response_data:
                    return response_data['text']
                # Try generated_text
                elif 'generated_text' in response_data:
                    return response_data['generated_text']
                else:
                    logger.error(f"Cannot extract text from response: {response_data}")
                    return ""
            except Exception:
                logger.error(f"Unexpected response format: {response_data}")
                return ""
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the API model setup.
        
        Returns:
            dict: Model information
        """
        return {
            'provider': f'API ({self.config["provider_name"].title()})',
            'type': 'Remote API',
            'model': self.config['model'],
            'base_url': self.config['base_url'],
            'provider_name': self.config['provider_name'],
            'connected': self.is_connected,
            'available': self.is_available(),
            'has_api_key': bool(self.config.get('api_key'))
        }
    
    def disconnect(self) -> None:
        """Clean up API provider resources."""
        super().disconnect()
        logger.info(f"Disconnected from {self.config['provider_name']} API") 
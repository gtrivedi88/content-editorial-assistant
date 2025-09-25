"""
API Provider
"""

import requests
import logging
from typing import Dict, Any
from .base_provider import BaseModelProvider

logger = logging.getLogger(__name__)


class APIProvider(BaseModelProvider):
    """Universal API provider for any OpenAI-compatible REST API service."""
    
    def _validate_config(self) -> None:
        """Validate API provider configuration."""
        required_fields = ['base_url', 'model', 'api_key']
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(f"Missing required API config: {field}")
        
        if not self.config['base_url'].startswith('http'):
            raise ValueError("API base_url must start with http:// or https://")
    
    def connect(self) -> bool:
        """Test connection to the API provider."""
        try:
            headers = self._get_headers()
            test_endpoint = self._get_health_check_endpoint()
            
            # Get SSL certificate path if provided
            cert_path = self.config.get('cert_path')
            verify = cert_path if cert_path else True
            
            response = requests.get(
                test_endpoint,
                headers=headers,
                timeout=self.config.get('timeout', 10),
                verify=verify
            )
            
            # Accept various response codes - some APIs return different codes for /models
            if response.status_code in [200, 401, 403, 404]:
                self.is_connected = True
                logger.info(f"✅ Connected to API at {self.config['base_url']} (status: {response.status_code})")
                return True
            else:
                logger.warning(f"API connection test returned {response.status_code}, trying alternative endpoint")
                # Try chat completions endpoint as fallback
                return self._test_chat_endpoint(headers, verify)
                
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to API: {e}")
            return False
    
    def _get_test_max_tokens(self) -> int:
        """Get appropriate max_tokens for API testing."""
        try:
            from ..token_config import get_token_config
            token_config = get_token_config(self.config)
            return token_config.get_max_tokens('test_payload')
        except Exception:
            # Fallback if token config fails
            return 1
    
    def _test_chat_endpoint(self, headers: Dict[str, str], verify) -> bool:
        """Test connection using chat completions endpoint."""
        try:
            base_url = self.config['base_url'].rstrip('/')
            chat_endpoint = f"{base_url}/chat/completions"
            
            # Minimal test payload
            test_payload = {
                "model": self.config['model'],
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": self._get_test_max_tokens()
            }
            
            response = requests.post(
                chat_endpoint,
                json=test_payload,
                headers=headers,
                timeout=self.config.get('timeout', 10),
                verify=verify
            )
            
            # Accept various response codes for connection test
            if response.status_code in [200, 400, 401, 403]:
                self.is_connected = True
                logger.info(f"✅ Connected to API via chat endpoint (status: {response.status_code})")
                return True
            else:
                logger.error(f"❌ Chat endpoint test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Chat endpoint test failed: {e}")
            return False
    
    def _get_health_check_endpoint(self) -> str:
        """Get health check endpoint. Try chat/completions as fallback."""
        base_url = self.config['base_url'].rstrip('/')
        # First try models endpoint, fallback to chat/completions for APIs that don't support /models
        return f"{base_url}/models"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for API requests."""
        return {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.config['api_key']}"
        }
    
    def is_available(self) -> bool:
        """Check if the API provider and model are available."""
        if not self.is_connected:
            return self.connect()
        
        return self.is_connected
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the API provider."""
        if not self.is_available():
            logger.error("API is not available")
            return ""
        
        params = self._prepare_generation_params(**kwargs)
        endpoint, payload = self._build_request(prompt, params)
        headers = self._get_headers()
        
        try:
            # Get SSL certificate path if provided
            cert_path = self.config.get('cert_path')
            verify = cert_path if cert_path else True
            
            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=self.config.get('timeout', 30),
                verify=verify
            )
            
            if response.status_code == 200:
                generated_text = self._extract_response(response.json())
                
                if generated_text:
                    logger.debug(f"✅ Generated {len(generated_text)} characters")
                    return generated_text.strip()
                else:
                    logger.warning("API returned empty response")
                    return ""
            else:
                logger.error(f"❌ API error: {response.status_code} - {response.text}")
                return ""
                
        except requests.exceptions.Timeout:
            logger.error("❌ API request timed out")
            return ""
        except Exception as e:
            logger.error(f"❌ API generation failed: {e}")
            return ""
    
    def _build_request(self, prompt: str, params: Dict[str, Any]) -> tuple:
        """Build the API request endpoint and payload."""
        base_url = self.config['base_url'].rstrip('/')
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
        try:
            # Try OpenAI-compatible format first (most common)
            if 'choices' in response_data and response_data['choices']:
                choice = response_data['choices'][0]
                if 'message' in choice and 'content' in choice['message']:
                    return choice['message']['content']
                elif 'text' in choice:
                    return choice['text']
            
            # Try direct content fields
            if 'content' in response_data:
                return response_data['content']
            
            # Try text field
            if 'text' in response_data:
                return response_data['text']
            
            # Try generated_text field
            if 'generated_text' in response_data:
                return response_data['generated_text']
            
            # Try array response (some APIs return arrays)
            if isinstance(response_data, list) and response_data:
                first_item = response_data[0]
                if isinstance(first_item, dict):
                    if 'generated_text' in first_item:
                        return first_item['generated_text']
                    elif 'text' in first_item:
                        return first_item['text']
                elif isinstance(first_item, str):
                    return first_item
            
            logger.error(f"Cannot extract text from response. Keys available: {list(response_data.keys()) if isinstance(response_data, dict) else 'non-dict response'}")
            return ""
            
        except Exception as e:
            logger.error(f"Error extracting response: {e}")
            return ""
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the API model setup."""
        return {
            'provider': 'Generic API',
            'type': 'Remote API',
            'model': self.config['model'],
            'base_url': self.config['base_url'],
            'connected': self.is_connected,
            'available': self.is_available(),
            'has_api_key': bool(self.config.get('api_key'))
        }
    
    def disconnect(self) -> None:
        """Clean up API provider resources."""
        super().disconnect()
        logger.info("Disconnected from API") 
"""
Llama Stack Provider for Lightrail Platform
Integrates Llama Stack client with the existing model system.
"""

import os
import ssl
import logging
from typing import Dict, Any, Optional
from llama_stack_client import LlamaStackClient, DefaultHttpxClient
from .base_provider import BaseModelProvider

logger = logging.getLogger(__name__)


class LlamaStackProvider(BaseModelProvider):
    """
    Llama Stack provider for Lightrail platform deployment.
    
    Uses Lightrail environment variables to connect to the managed Llama Stack instance.
    Integrates seamlessly with the existing ModelManager system.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the Llama Stack provider."""
        self.client: Optional[LlamaStackClient] = None
        self.model_id = config.get('model', 'style_analyzer_model')  # Default from llamastack config
        super().__init__(config)
    
    def _validate_config(self) -> None:
        """Validate Llama Stack configuration."""
        # For Lightrail, we rely on environment variables, not config
        base_url = os.environ.get('LIGHTRAIL_LLAMA_STACK_BASE_URL')
        if not base_url:
            raise ValueError(
                "LIGHTRAIL_LLAMA_STACK_BASE_URL environment variable not set. "
                "This provider requires Lightrail platform deployment."
            )
    
    def connect(self) -> bool:
        """Connect to the Llama Stack instance."""
        try:
            base_url = os.environ.get('LIGHTRAIL_LLAMA_STACK_BASE_URL')
            ca_cert_path = os.environ.get('LIGHTRAIL_LLAMA_STACK_TLS_SERVICE_CA_CERT_PATH')
            
            # Setup TLS context for secure communication
            ctx = ssl.create_default_context()
            if ca_cert_path and os.path.exists(ca_cert_path):
                ctx.load_verify_locations(ca_cert_path)
                logger.debug(f"Loaded CA certificate from {ca_cert_path}")
            
            # Initialize client with proper TLS
            self.client = LlamaStackClient(
                base_url=base_url,
                http_client=DefaultHttpxClient(verify=ctx)
            )
            
            # Test connection by listing models
            models = self.client.models.list()
            logger.info(f"Connected to Llama Stack. Available models: {len(models.data)}")
            self.is_connected = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Llama Stack: {e}")
            self.is_connected = False
            return False
    
    def is_available(self) -> bool:
        """Check if Llama Stack is available."""
        if not self.is_connected or not self.client:
            return self.connect()
        
        try:
            # Quick health check
            models = self.client.models.list()
            return len(models.data) > 0
        except Exception as e:
            logger.warning(f"Llama Stack availability check failed: {e}")
            self.is_connected = False
            return False
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using Llama Stack."""
        if not self.is_available():
            raise RuntimeError("Llama Stack is not available")
        
        try:
            # Prepare messages in chat completion format
            messages = [{"role": "user", "content": prompt}]
            
            # Extract parameters with defaults
            temperature = kwargs.get('temperature', 0.4)
            # Use centralized token configuration
            from ..token_config import get_token_config
            token_config = get_token_config(self.config)
            default_max_tokens = token_config.get_max_tokens('default')
            max_tokens = kwargs.get('max_tokens', default_max_tokens)
            
            # Make chat completion request
            response = self.client.inference.chat_completion(
                model_id=self.model_id,
                messages=messages,
                sampling_params={
                    "type": "top_p",
                    "temperature": temperature,
                    "top_p": kwargs.get('top_p', 0.9)
                },
                max_tokens=max_tokens
            )
            
            # Extract response content
            if response.completion_message and response.completion_message.content:
                result = response.completion_message.content
                logger.debug(f"Generated {len(result)} characters via Llama Stack")
                return result
            else:
                logger.warning("Llama Stack returned empty response")
                return ""
                
        except Exception as e:
            logger.error(f"Llama Stack generation failed: {e}")
            return ""
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Llama Stack setup."""
        info = {
            'provider_type': 'llamastack',
            'provider_name': 'Lightrail Llama Stack',
            'model_id': self.model_id,
            'connected': self.is_connected,
            'base_url': os.environ.get('LIGHTRAIL_LLAMA_STACK_BASE_URL', 'Not configured')
        }
        
        if self.is_available():
            try:
                models = self.client.models.list()
                info['available_models'] = [model.model_id for model in models.data]
            except Exception as e:
                logger.debug(f"Could not fetch model list: {e}")
                
        return info

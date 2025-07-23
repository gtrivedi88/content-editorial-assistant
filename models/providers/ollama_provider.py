"""
Ollama Provider
Handles local Ollama model connections and text generation.

USAGE:
======
This provider connects to your local Ollama instance.
Make sure Ollama is running: `ollama serve`
And you have the model pulled: `ollama pull llama3:8b`
"""

import requests
import logging
from typing import Dict, Any
from .base_provider import BaseModelProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseModelProvider):
    """
    Provider for local Ollama models.
    
    Handles connection to local Ollama instance and text generation
    using any model you have pulled locally.
    """
    
    def _validate_config(self) -> None:
        """Validate Ollama-specific configuration."""
        required_fields = ['base_url', 'model']
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(f"Missing required Ollama config: {field}")
        
        # Ensure base_url format is correct
        if not self.config['base_url'].startswith('http'):
            raise ValueError("Ollama base_url must start with http:// or https://")
    
    def connect(self) -> bool:
        """
        Connect to Ollama and verify the model is available.
        
        Returns:
            bool: True if Ollama is running and model is available
        """
        try:
            # Check if Ollama is running
            response = requests.get(
                f"{self.config['base_url']}/api/tags",
                timeout=self.config.get('timeout', 10)
            )
            
            if response.status_code != 200:
                logger.error(f"Ollama is not responding properly: {response.status_code}")
                return False
            
            # Check if our model is available
            models_data = response.json()
            available_models = [model['name'] for model in models_data.get('models', [])]
            
            if self.config['model'] not in available_models:
                logger.error(
                    f"Model '{self.config['model']}' not found in Ollama. "
                    f"Available models: {available_models}"
                )
                logger.info(f"To install: ollama pull {self.config['model']}")
                return False
            
            self.is_connected = True
            logger.info(f"✅ Connected to Ollama. Using model: {self.config['model']}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Cannot connect to Ollama: {e}")
            logger.info("Make sure Ollama is running: ollama serve")
            return False
        except Exception as e:
            logger.error(f"❌ Unexpected error connecting to Ollama: {e}")
            return False
    
    def is_available(self) -> bool:
        """
        Check if Ollama and the model are available.
        
        Returns:
            bool: True if ready to generate text
        """
        if not self.is_connected:
            return self.connect()
        
        # Quick health check
        try:
            response = requests.get(
                f"{self.config['base_url']}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except:
            self.is_connected = False
            return False
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using Ollama.
        
        Args:
            prompt: Input text prompt
            **kwargs: Additional generation parameters
            
        Returns:
            str: Generated text
        """
        if not self.is_available():
            logger.error("Ollama is not available")
            return ""
        
        # Prepare generation parameters
        params = self._prepare_generation_params(**kwargs)
        
        payload = {
            "model": self.config['model'],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": params['temperature'],
                "top_p": params['top_p'],
                "top_k": params['top_k'],
                "num_predict": params['max_tokens'],
                # Stop sequences to prevent runaway generation
                "stop": ["\n\nOriginal:", "\n\nRewrite:", "###", "---", "\n\n\n"]
            }
        }
        
        try:
            response = requests.post(
                f"{self.config['base_url']}/api/generate",
                json=payload,
                timeout=self.config.get('timeout', 60)
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result.get('response', '').strip()
                
                if generated_text:
                    logger.debug(f"✅ Generated {len(generated_text)} characters")
                    return generated_text
                else:
                    logger.warning("Ollama returned empty response")
                    return ""
            else:
                logger.error(f"❌ Ollama API error: {response.status_code} - {response.text}")
                return ""
                
        except requests.exceptions.Timeout:
            logger.error("❌ Ollama request timed out")
            return ""
        except Exception as e:
            logger.error(f"❌ Ollama generation failed: {e}")
            return ""
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the Ollama model setup.
        
        Returns:
            dict: Model information
        """
        base_info = {
            'provider': 'Ollama',
            'type': 'Local',
            'model': self.config['model'],
            'base_url': self.config['base_url'],
            'connected': self.is_connected,
            'available': self.is_available()
        }
        
        # Try to get additional model details from Ollama
        if self.is_connected:
            try:
                response = requests.get(
                    f"{self.config['base_url']}/api/tags",
                    timeout=5
                )
                if response.status_code == 200:
                    models_data = response.json()
                    for model in models_data.get('models', []):
                        if model['name'] == self.config['model']:
                            base_info.update({
                                'size': model.get('size', 'Unknown'),
                                'modified_at': model.get('modified_at', 'Unknown'),
                                'digest': model.get('digest', 'Unknown')[:12] + '...' if model.get('digest') else 'Unknown'
                            })
                            break
            except Exception as e:
                logger.debug(f"Could not fetch detailed model info: {e}")
        
        return base_info
    
    def disconnect(self) -> None:
        """Clean up Ollama provider resources."""
        super().disconnect()
        logger.info("Disconnected from Ollama")
    
    def list_available_models(self) -> list:
        """
        List all models available in local Ollama instance.
        
        Returns:
            list: Available model names
        """
        try:
            response = requests.get(
                f"{self.config['base_url']}/api/tags",
                timeout=10
            )
            
            if response.status_code == 200:
                models_data = response.json()
                return [model['name'] for model in models_data.get('models', [])]
            else:
                logger.error(f"Could not fetch model list: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching available models: {e}")
            return [] 
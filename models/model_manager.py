"""
Model Manager
Main interface for AI model operations throughout the application.

USAGE:
======
This is the PRIMARY interface that other modules should use.
It provides a clean, simple API while handling all the complexity internally.

EXAMPLES:
=========
# Simple text generation
from models import ModelManager

manager = ModelManager()
result = manager.generate_text("Rewrite this text to be more concise...")

# Check model status
status = manager.get_status()
print(f"Using: {status['model_info']['model']}")

# Switch providers programmatically
manager.switch_provider('api', {'api_provider': 'groq', 'model': 'llama3-70b-8192'})
"""

import logging
from typing import Dict, Any, Optional
from .config import ModelConfig
from .factory import ModelFactory

logger = logging.getLogger(__name__)


class ModelManager:
    """
    High-level model management interface.
    
    This class provides a clean, simple API for AI model operations
    while hiding the complexity of provider management, configuration,
    and error handling.
    
    Other modules should use THIS class, not the providers directly.
    """
    
    def __init__(self):
        """Initialize the model manager."""
        self._initialized = False
        self._last_error = None
    
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the configured AI model.
        
        This is the MAIN method that other modules should use.
        
        Args:
            prompt: Input text prompt
            **kwargs: Additional generation parameters (temperature, max_tokens, etc.)
            
        Returns:
            str: Generated text, or empty string if generation fails
            
        Examples:
            # Basic usage
            result = manager.generate_text("Rewrite: The quick brown fox jumps.")
            
            # With custom parameters
            result = manager.generate_text(
                "Improve this text...",
                temperature=0.2,
                max_tokens=256
            )
        """
        try:
            provider = ModelFactory.create_provider()
            result = provider.generate_text(prompt, **kwargs)
            
            if result:
                self._last_error = None
                logger.debug(f"Successfully generated {len(result)} characters")
                return result
            else:
                self._last_error = "Provider returned empty result"
                logger.warning("Model returned empty result")
                return ""
                
        except Exception as e:
            self._last_error = str(e)
            logger.error(f"Text generation failed: {e}")
            return ""
    
    def is_available(self) -> bool:
        """
        Check if the AI model is ready to use.
        
        Returns:
            bool: True if model is available for text generation
        """
        try:
            provider = ModelFactory.get_active_provider()
            if provider:
                return provider.is_available()
            else:
                # Try to create a provider to test availability
                provider = ModelFactory.create_provider()
                return provider.is_available()
        except Exception as e:
            logger.debug(f"Model availability check failed: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get comprehensive status information about the model setup.
        
        Returns:
            dict: Status information including model, provider, health, etc.
        """
        try:
            factory_status = ModelFactory.get_provider_status()
            config_info = ModelConfig.get_model_info()
            
            return {
                'available': self.is_available(),
                'factory_status': factory_status,
                'config_info': config_info,
                'last_error': self._last_error,
                'quick_info': {
                    'provider': config_info.get('type', 'Unknown'),
                    'model': config_info.get('model', 'Unknown'),
                    'status': config_info.get('status', 'Unknown')
                }
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e),
                'last_error': self._last_error
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model.
        
        Returns:
            dict: Model information (simplified version of get_status)
        """
        status = self.get_status()
        return status.get('quick_info', {})
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a comprehensive health check.
        
        Returns:
            dict: Health check results
        """
        try:
            # Configuration validation
            config_valid = ModelConfig.validate_config()
            
            # Provider status
            provider_status = ModelFactory.get_provider_status()
            
            # Connectivity test
            is_available = self.is_available()
            
            # Generation test (optional - only if explicitly requested)
            generation_test = None
            
            overall_health = config_valid and is_available
            
            return {
                'overall_health': 'healthy' if overall_health else 'unhealthy',
                'config_valid': config_valid,
                'provider_available': is_available,
                'provider_status': provider_status,
                'generation_test': generation_test,
                'recommendations': self._get_health_recommendations(
                    config_valid, is_available, provider_status
                )
            }
        except Exception as e:
            return {
                'overall_health': 'error',
                'error': str(e),
                'recommendations': [f"Fix error: {e}"]
            }
    
    def _get_health_recommendations(self, config_valid: bool, is_available: bool, 
                                   provider_status: Dict[str, Any]) -> list:
        """Generate health recommendations based on status."""
        recommendations = []
        
        if not config_valid:
            recommendations.append("Check model configuration in models/config.py")
        
        if not is_available:
            active_provider = ModelConfig.ACTIVE_PROVIDER
            if active_provider == 'ollama':
                recommendations.extend([
                    "Ensure Ollama is running: ollama serve",
                    f"Ensure model is pulled: ollama pull {ModelConfig.OLLAMA_MODEL}",
                    "Check Ollama base URL in configuration"
                ])
            elif active_provider == 'api':
                recommendations.extend([
                    "Check API key is set in environment variables",
                    "Verify API base URL is correct",
                    "Check internet connectivity for API access"
                ])
        
        if provider_status.get('status') == 'Error':
            recommendations.append(f"Provider error: {provider_status.get('error', 'Unknown')}")
        
        if not recommendations:
            recommendations.append("All systems operational!")
        
        return recommendations
    
    def switch_provider(self, provider_type: str, provider_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Switch to a different provider programmatically.
        
        WARNING: This temporarily overrides configuration.
        For permanent changes, update models/config.py
        
        Args:
            provider_type: 'ollama' or 'api'
            provider_config: Additional configuration for the provider
            
        Returns:
            bool: True if switch was successful
            
        Examples:
            # Switch to Groq API
            manager.switch_provider('api', {
                'api_provider': 'groq',
                'model': 'llama3-70b-8192',
                'api_key': 'your-key'
            })
            
            # Switch to different Ollama model
            manager.switch_provider('ollama', {
                'model': 'mistral:7b'
            })
        """
        try:
            # Build new configuration
            new_config = ModelConfig.get_active_config().copy()
            new_config['provider_type'] = provider_type
            
            if provider_config:
                new_config.update(provider_config)
            
            # Validate the new configuration
            if not ModelFactory.validate_configuration(new_config):
                logger.error("Invalid configuration for provider switch")
                return False
            
            # Force creation of new provider with new config
            provider = ModelFactory.create_provider(new_config)
            
            if provider.is_available():
                logger.info(f"Successfully switched to {provider_type} provider")
                return True
            else:
                logger.error(f"New provider {provider_type} is not available")
                return False
                
        except Exception as e:
            logger.error(f"Failed to switch provider: {e}")
            self._last_error = str(e)
            return False
    
    def force_reconnect(self) -> bool:
        """
        Force reconnection to the current provider.
        
        Useful for recovering from connection issues.
        
        Returns:
            bool: True if reconnection was successful
        """
        try:
            provider = ModelFactory.force_recreate()
            success = provider.is_available()
            
            if success:
                logger.info("Successfully reconnected to provider")
                self._last_error = None
            else:
                logger.error("Reconnection failed - provider not available")
                
            return success
            
        except Exception as e:
            logger.error(f"Force reconnection failed: {e}")
            self._last_error = str(e)
            return False
    
    def get_last_error(self) -> Optional[str]:
        """
        Get the last error that occurred.
        
        Returns:
            str or None: Last error message, or None if no errors
        """
        return self._last_error
    
    def test_generation(self, test_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Test text generation with a simple prompt.
        
        Args:
            test_prompt: Custom test prompt. If None, uses default.
            
        Returns:
            dict: Test results including success status and generated text
        """
        if test_prompt is None:
            test_prompt = "Please respond with: 'Test successful'"
        
        try:
            start_time = __import__('time').time()
            result = self.generate_text(test_prompt, max_tokens=50, temperature=0.1)
            end_time = __import__('time').time()
            
            return {
                'success': bool(result),
                'prompt': test_prompt,
                'result': result,
                'duration_seconds': round(end_time - start_time, 2),
                'result_length': len(result) if result else 0
            }
        except Exception as e:
            return {
                'success': False,
                'prompt': test_prompt,
                'error': str(e),
                'duration_seconds': 0,
                'result_length': 0
            } 
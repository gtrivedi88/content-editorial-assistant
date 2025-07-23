"""
Base Provider Interface
All model providers must implement this interface to ensure consistency.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseModelProvider(ABC):
    """
    Abstract base class for all model providers.
    
    This ensures all providers (Ollama, Groq, HuggingFace, etc.) 
    implement the same interface for seamless switching.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider with configuration.
        
        Args:
            config: Configuration dictionary from ModelConfig
        """
        self.config = config
        self.is_connected = False
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate provider-specific configuration.
        Should raise ValueError if config is invalid.
        """
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to the model provider.
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider and model are available.
        
        Returns:
            bool: True if ready to generate text
        """
        pass
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """
        Generate text using the model.
        
        Args:
            prompt: Input text prompt
            **kwargs: Additional generation parameters
            
        Returns:
            str: Generated text
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model setup.
        
        Returns:
            dict: Model information including name, provider, status
        """
        pass
    
    def disconnect(self) -> None:
        """
        Clean up provider resources.
        Default implementation - override if needed.
        """
        self.is_connected = False
        logger.info(f"Disconnected from {self.__class__.__name__}")
    
    def _prepare_generation_params(self, **kwargs) -> Dict[str, Any]:
        """
        Prepare generation parameters by merging config defaults with kwargs.
        
        Args:
            **kwargs: Override parameters
            
        Returns:
            dict: Combined parameters
        """
        params = {
            'temperature': self.config.get('temperature', 0.4),
            'max_tokens': self.config.get('max_tokens', 512),
            'top_p': self.config.get('top_p', 0.7),
            'top_k': self.config.get('top_k', 20),
        }
        
        # Override with provided kwargs
        params.update(kwargs)
        return params
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check on the provider.
        
        Returns:
            dict: Health status information
        """
        try:
            is_available = self.is_available()
            model_info = self.get_model_info()
            
            return {
                'provider': self.__class__.__name__,
                'connected': self.is_connected,
                'available': is_available,
                'model_info': model_info,
                'status': 'healthy' if (self.is_connected and is_available) else 'unhealthy'
            }
        except Exception as e:
            logger.error(f"Health check failed for {self.__class__.__name__}: {e}")
            return {
                'provider': self.__class__.__name__,
                'connected': False,
                'available': False,
                'error': str(e),
                'status': 'error'
            } 
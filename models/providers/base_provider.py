"""
Base Provider Interface
All model providers must implement this interface to ensure consistency.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseModelProvider(ABC):
    """Abstract base class for all model providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the provider with configuration."""
        self.config = config
        self.is_connected = False
        self._validate_config()
    
    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration."""
        pass
    
    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the model provider."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider and model are available."""
        pass
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using the model."""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model setup."""
        pass
    
    def disconnect(self) -> None:
        """Clean up provider resources."""
        self.is_connected = False
        logger.info(f"Disconnected from {self.__class__.__name__}")
    
    def _prepare_generation_params(self, **kwargs) -> Dict[str, Any]:
        """Prepare generation parameters by merging config defaults with kwargs."""
        # Import here to avoid circular imports
        from ..token_config import get_token_config
        
        token_config = get_token_config(self.config)
        default_max_tokens = token_config.get_max_tokens('default')
        
        params = {
            'temperature': self.config.get('temperature', 0.4),
            'max_tokens': self.config.get('max_tokens', default_max_tokens),  # Use centralized config
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
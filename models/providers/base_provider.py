"""
Base Provider Interface
All model providers must implement this interface to ensure consistency.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

logger = logging.getLogger(__name__)


class BaseModelProvider(ABC):
    """Abstract base class for all model providers."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the provider with configuration."""
        self.config = config
        self.is_connected = False
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate provider-specific configuration."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the model provider."""

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider and model are available."""

    @abstractmethod
    def generate_text(self, prompt: str, **kwargs: object) -> str:
        """Generate text using the model."""

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model setup."""

    def disconnect(self) -> None:
        """Clean up provider resources."""
        self.is_connected = False
        logger.info("Disconnected from %s", self.__class__.__name__)

    def _prepare_generation_params(self, **kwargs: object) -> Dict[str, Any]:
        """Prepare generation parameters by merging config defaults with kwargs."""
        # Import here to avoid circular imports
        from ..token_config import get_token_config

        token_config = get_token_config(self.config)
        default_max_tokens = token_config.get_max_tokens('default')

        # Pop internal-only keys so they never leak into API payloads
        kwargs.pop('_result_meta', None)
        kwargs.pop('_timeout_override', None)

        params: Dict[str, Any] = {
            'temperature': self.config.get('temperature', 0.4),
            'max_tokens': self.config.get('max_tokens', default_max_tokens),
            'top_p': self.config.get('top_p', 0.7),
            'top_k': self.config.get('top_k', 20),
        }

        # Override with provided kwargs
        params.update(kwargs)

        if params['temperature'] == 0.0:
            params['top_p'] = 1.0

        return params

    def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the provider.

        Returns:
            dict: Health status information.
        """
        try:
            is_available = self.is_available()
            model_info = self.get_model_info()

            return {
                'provider': self.__class__.__name__,
                'connected': self.is_connected,
                'available': is_available,
                'model_info': model_info,
                'status': (
                    'healthy'
                    if (self.is_connected and is_available)
                    else 'unhealthy'
                ),
            }
        except (ConnectionError, TimeoutError, RuntimeError, ValueError,
                OSError) as exc:
            logger.error(
                "Health check failed for %s: %s",
                self.__class__.__name__, exc
            )
            return {
                'provider': self.__class__.__name__,
                'connected': False,
                'available': False,
                'error': str(exc),
                'status': 'error',
            }

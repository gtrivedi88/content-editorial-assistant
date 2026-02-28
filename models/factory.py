"""
Model Factory
Creates and manages model provider instances.
"""

import logging
from typing import Any, Dict, List, Optional

from .config import ModelConfig
from .providers import LlamaStackProvider
from .providers.api_provider import APIProvider
from .providers.base_provider import BaseModelProvider
from .providers.ollama_provider import OllamaProvider

logger = logging.getLogger(__name__)


class ModelFactory:
    """Factory for creating model provider instances."""

    _active_provider: Optional[BaseModelProvider] = None
    _provider_registry: Dict[str, type] = {
        'ollama': OllamaProvider,
        'api': APIProvider,
    }

    # Add LlamaStackProvider if available (optional dependency)
    if LlamaStackProvider is not None:
        _provider_registry['llamastack'] = LlamaStackProvider

    @classmethod
    def create_provider(
        cls, config: Optional[Dict[str, Any]] = None
    ) -> BaseModelProvider:
        """Create or return the active model provider."""
        if config is None:
            config = ModelConfig.get_active_config()

        # Check if we can reuse the existing provider
        if cls._can_reuse_provider(config):
            logger.debug(
                "Reusing existing %s",
                cls._active_provider.__class__.__name__
            )
            return cls._active_provider

        # Clean up existing provider
        if cls._active_provider:
            cls._cleanup_active_provider()

        # Create new provider
        provider_type = config.get('provider_type')
        if not provider_type:
            raise ValueError("No provider_type specified in configuration")

        if provider_type not in cls._provider_registry:
            available_providers = list(cls._provider_registry.keys())
            raise ValueError(
                "Unsupported provider type: '%s'. "
                "Available providers: %s" % (provider_type, available_providers)
            )

        # Instantiate the provider
        provider_class = cls._provider_registry[provider_type]

        try:
            logger.info("Creating new %s instance", provider_class.__name__)
            provider = provider_class(config)

            # Test the connection
            if not provider.connect():
                raise RuntimeError(
                    "Failed to connect to %s" % provider_class.__name__
                )

            cls._active_provider = provider
            logger.info(
                "Successfully created and connected %s",
                provider_class.__name__
            )

            return provider

        except (ConnectionError, TimeoutError, RuntimeError, ValueError,
                OSError) as exc:
            logger.error(
                "Failed to create %s: %s", provider_class.__name__, exc
            )
            raise RuntimeError(
                "Provider initialization failed: %s" % exc
            ) from exc

    @classmethod
    def _can_reuse_provider(cls, config: Dict[str, Any]) -> bool:
        """Check if existing provider can be reused with given config."""
        if not cls._active_provider:
            return False

        # Check if provider type has changed
        current_type = cls._get_provider_type(cls._active_provider)
        new_type = config.get('provider_type')

        if current_type != new_type:
            logger.debug(
                "Provider type changed: %s -> %s", current_type, new_type
            )
            return False

        # Check if critical configuration has changed
        current_config = cls._active_provider.config
        critical_keys = cls._get_critical_config_keys(new_type)

        for key in critical_keys:
            if current_config.get(key) != config.get(key):
                logger.debug("Critical config changed: %s", key)
                return False

        # Check if provider is still healthy
        if not cls._active_provider.is_available():
            logger.debug("Provider is no longer available")
            return False

        return True

    @classmethod
    def _get_provider_type(cls, provider: BaseModelProvider) -> str:
        """Get the provider type from a provider instance."""
        if isinstance(provider, OllamaProvider):
            return 'ollama'
        elif isinstance(provider, APIProvider):
            return 'api'
        elif LlamaStackProvider is not None and isinstance(
            provider, LlamaStackProvider
        ):
            return 'llamastack'
        return 'unknown'

    @classmethod
    def _get_critical_config_keys(cls, provider_type: str) -> List[str]:
        """Get configuration keys that require provider recreation if changed."""
        common_keys = ['model']

        if provider_type == 'ollama':
            return common_keys + ['base_url']
        elif provider_type == 'api':
            return common_keys + ['provider_name', 'base_url', 'api_key']
        elif provider_type == 'llamastack':
            return common_keys
        return common_keys

    @classmethod
    def _cleanup_active_provider(cls) -> None:
        """Clean up the currently active provider."""
        if cls._active_provider:
            try:
                cls._active_provider.disconnect()
                logger.debug(
                    "Cleaned up %s",
                    cls._active_provider.__class__.__name__
                )
            except (ConnectionError, TimeoutError, RuntimeError, OSError) as exc:
                logger.warning("Error during provider cleanup: %s", exc)
            finally:
                cls._active_provider = None

    @classmethod
    def get_active_provider(cls) -> Optional[BaseModelProvider]:
        """Get the currently active provider without creating a new one."""
        return cls._active_provider

    @classmethod
    def force_recreate(cls) -> BaseModelProvider:
        """Force recreation of the provider, even if config hasn't changed."""
        logger.info("Forcing provider recreation")
        cls._cleanup_active_provider()
        return cls.create_provider()

    @classmethod
    def get_provider_status(cls) -> Dict[str, Any]:
        """Get status information about the current provider setup."""
        if not cls._active_provider:
            return {
                'status': 'No active provider',
                'provider': None,
                'config': ModelConfig.get_active_config(),
            }

        try:
            health_info = cls._active_provider.health_check()
            model_info = cls._active_provider.get_model_info()

            return {
                'status': 'Active',
                'provider': cls._active_provider.__class__.__name__,
                'health': health_info,
                'model_info': model_info,
                'config': cls._active_provider.config,
            }
        except (ConnectionError, TimeoutError, RuntimeError, ValueError,
                OSError) as exc:
            return {
                'status': 'Error',
                'provider': cls._active_provider.__class__.__name__,
                'error': str(exc),
                'config': cls._active_provider.config,
            }

    @classmethod
    def register_provider(cls, name: str, provider_class: type) -> None:
        """Register a new provider type."""
        if not issubclass(provider_class, BaseModelProvider):
            raise ValueError(
                "Provider class must inherit from BaseModelProvider"
            )

        cls._provider_registry[name] = provider_class
        logger.info(
            "Registered new provider: %s -> %s",
            name, provider_class.__name__
        )

    @classmethod
    def list_available_providers(cls) -> List[str]:
        """List all available provider types."""
        return list(cls._provider_registry.keys())

    @classmethod
    def validate_configuration(
        cls, config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Validate configuration without creating a provider."""
        if config is None:
            return ModelConfig.validate_config()

        try:
            provider_type = config.get('provider_type')
            if provider_type not in cls._provider_registry:
                return False

            # Try to instantiate but don't connect
            provider_class = cls._provider_registry[provider_type]
            provider_class(config)
            return True

        except (ValueError, KeyError, TypeError) as exc:
            logger.debug("Configuration validation failed: %s", exc)
            return False

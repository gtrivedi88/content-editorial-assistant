"""
Model Factory
Creates and manages model provider instances.
"""

import logging
from typing import Dict, Any, Optional
from .config import ModelConfig
from .providers.base_provider import BaseModelProvider
from .providers.ollama_provider import OllamaProvider
from .providers.api_provider import APIProvider
from .providers import LlamaStackProvider

logger = logging.getLogger(__name__)


class ModelFactory:
    """Factory for creating model provider instances."""
    
    _active_provider: Optional[BaseModelProvider] = None
    _provider_registry = {
        'ollama': OllamaProvider,
        'api': APIProvider,
    }
    
    # Add LlamaStackProvider if available (optional dependency)
    if LlamaStackProvider is not None:
        _provider_registry['llamastack'] = LlamaStackProvider
    
    @classmethod
    def create_provider(cls, config: Optional[Dict[str, Any]] = None) -> BaseModelProvider:
        """Create or return the active model provider."""
        # Use provided config or default config
        if config is None:
            config = ModelConfig.get_active_config()
        
        # Check if we can reuse the existing provider
        if cls._can_reuse_provider(config):
            logger.debug(f"Reusing existing {cls._active_provider.__class__.__name__}")
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
                f"Unsupported provider type: '{provider_type}'. "
                f"Available providers: {available_providers}"
            )
        
        # Instantiate the provider
        provider_class = cls._provider_registry[provider_type]
        
        try:
            logger.info(f"Creating new {provider_class.__name__} instance")
            provider = provider_class(config)
            
            # Test the connection
            if not provider.connect():
                raise RuntimeError(f"Failed to connect to {provider_class.__name__}")
            
            cls._active_provider = provider
            logger.info(f"✅ Successfully created and connected {provider_class.__name__}")
            
            return provider
            
        except Exception as e:
            logger.error(f"❌ Failed to create {provider_class.__name__}: {e}")
            raise RuntimeError(f"Provider initialization failed: {e}")
    
    @classmethod
    def _can_reuse_provider(cls, config: Dict[str, Any]) -> bool:
        """Check if existing provider can be reused with given config."""
        if not cls._active_provider:
            return False
        
        # Check if provider type has changed
        current_type = cls._get_provider_type(cls._active_provider)
        new_type = config.get('provider_type')
        
        if current_type != new_type:
            logger.debug(f"Provider type changed: {current_type} → {new_type}")
            return False
        
        # Check if critical configuration has changed
        current_config = cls._active_provider.config
        critical_keys = cls._get_critical_config_keys(new_type)
        
        for key in critical_keys:
            if current_config.get(key) != config.get(key):
                logger.debug(f"Critical config changed: {key}")
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
        elif isinstance(provider, LlamaStackProvider):
            return 'llamastack'
        else:
            return 'unknown'
    
    @classmethod
    def _get_critical_config_keys(cls, provider_type: str) -> list:
        """Get configuration keys that require provider recreation if changed."""
        common_keys = ['model']
        
        if provider_type == 'ollama':
            return common_keys + ['base_url']
        elif provider_type == 'api':
            return common_keys + ['provider_name', 'base_url', 'api_key']
        elif provider_type == 'llamastack':
            return common_keys
        else:
            return common_keys
    
    @classmethod
    def _cleanup_active_provider(cls) -> None:
        """Clean up the currently active provider."""
        if cls._active_provider:
            try:
                cls._active_provider.disconnect()
                logger.debug(f"Cleaned up {cls._active_provider.__class__.__name__}")
            except Exception as e:
                logger.warning(f"Error during provider cleanup: {e}")
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
                'config': ModelConfig.get_active_config()
            }
        
        try:
            health_info = cls._active_provider.health_check()
            model_info = cls._active_provider.get_model_info()
            
            return {
                'status': 'Active',
                'provider': cls._active_provider.__class__.__name__,
                'health': health_info,
                'model_info': model_info,
                'config': cls._active_provider.config
            }
        except Exception as e:
            return {
                'status': 'Error',
                'provider': cls._active_provider.__class__.__name__,
                'error': str(e),
                'config': cls._active_provider.config
            }
    
    @classmethod
    def register_provider(cls, name: str, provider_class: type) -> None:
        """Register a new provider type."""
        if not issubclass(provider_class, BaseModelProvider):
            raise ValueError(f"Provider class must inherit from BaseModelProvider")
        
        cls._provider_registry[name] = provider_class
        logger.info(f"Registered new provider: {name} → {provider_class.__name__}")
    
    @classmethod
    def list_available_providers(cls) -> list:
        """List all available provider types."""
        return list(cls._provider_registry.keys())
    
    @classmethod
    def validate_configuration(cls, config: Optional[Dict[str, Any]] = None) -> bool:
        """Validate configuration without creating a provider."""
        if config is None:
            return ModelConfig.validate_config()
        
        try:
            provider_type = config.get('provider_type')
            if provider_type not in cls._provider_registry:
                return False
            
            # Try to instantiate but don't connect
            provider_class = cls._provider_registry[provider_type]
            test_provider = provider_class(config)
            return True
            
        except Exception as e:
            logger.debug(f"Configuration validation failed: {e}")
            return False 
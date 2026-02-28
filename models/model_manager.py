"""
Model Manager
Main interface for AI model operations throughout the application.
"""

import logging
import time
from typing import Any, Dict, List, Optional

from .config import ModelConfig
from .factory import ModelFactory

logger = logging.getLogger(__name__)


class ModelManager:
    """High-level model management interface."""

    def __init__(self) -> None:
        """Initialize the model manager."""
        self._initialized = False
        self._last_error: Optional[str] = None

    def generate_text(self, prompt: str, **kwargs: object) -> str:
        """Generate text using the configured AI model."""
        try:
            provider = ModelFactory.create_provider()
            result = provider.generate_text(prompt, **kwargs)

            if result:
                self._last_error = None
                logger.debug(
                    "Successfully generated %s characters", len(result)
                )
                return result

            self._last_error = "Provider returned empty result"
            logger.warning("Model returned empty result")
            return ""

        except (ConnectionError, TimeoutError, RuntimeError, ValueError,
                OSError) as exc:
            self._last_error = str(exc)
            logger.error("Text generation failed: %s", exc)
            return ""

    def is_available(self) -> bool:
        """Check if the AI model is ready to use."""
        try:
            provider = ModelFactory.get_active_provider()
            if provider:
                return provider.is_available()

            # Try to create a provider to test availability
            provider = ModelFactory.create_provider()
            return provider.is_available()
        except (ConnectionError, TimeoutError, RuntimeError, ValueError,
                OSError) as exc:
            logger.debug("Model availability check failed: %s", exc)
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status information about the model setup."""
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
                    'status': config_info.get('status', 'Unknown'),
                },
            }
        except (ConnectionError, TimeoutError, RuntimeError, ValueError,
                OSError) as exc:
            return {
                'available': False,
                'error': str(exc),
                'last_error': self._last_error,
            }

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        status = self.get_status()
        return status.get('quick_info', {})

    def health_check(self) -> Dict[str, Any]:
        """Perform a comprehensive health check."""
        try:
            config_valid = ModelConfig.validate_config()
            provider_status = ModelFactory.get_provider_status()
            is_available = self.is_available()
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
                ),
            }
        except (ConnectionError, TimeoutError, RuntimeError, ValueError,
                OSError) as exc:
            return {
                'overall_health': 'error',
                'error': str(exc),
                'recommendations': ["Fix error: %s" % exc],
            }

    def _get_health_recommendations(
        self,
        config_valid: bool,
        is_available: bool,
        provider_status: Dict[str, Any],
    ) -> List[str]:
        """Generate health recommendations based on status."""
        recommendations: List[str] = []

        if not config_valid:
            recommendations.append(
                "Check model configuration in models/config.py"
            )

        if not is_available:
            active_config = ModelConfig.get_active_config()
            active_provider = active_config.get('provider_type')
            if active_provider == 'ollama':
                recommendations.extend([
                    "Ensure Ollama is running: ollama serve",
                    "Ensure model is pulled: ollama pull %s"
                    % active_config.get('model', 'unknown'),
                    "Check Ollama base URL in configuration",
                ])
            elif active_provider == 'api':
                recommendations.extend([
                    "Check API key is set in environment variables",
                    "Verify API base URL is correct",
                    "Check internet connectivity for API access",
                ])

        if provider_status.get('status') == 'Error':
            recommendations.append(
                "Provider error: %s"
                % provider_status.get('error', 'Unknown')
            )

        if not recommendations:
            recommendations.append("All systems operational!")

        return recommendations

    def switch_provider(
        self,
        provider_type: str,
        provider_config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Switch to a different provider programmatically."""
        try:
            new_config = ModelConfig.get_active_config().copy()
            new_config['provider_type'] = provider_type

            if provider_config:
                new_config.update(provider_config)

            if not ModelFactory.validate_configuration(new_config):
                logger.error("Invalid configuration for provider switch")
                return False

            provider = ModelFactory.create_provider(new_config)

            if provider.is_available():
                logger.info(
                    "Successfully switched to %s provider", provider_type
                )
                return True

            logger.error(
                "New provider %s is not available", provider_type
            )
            return False

        except (ConnectionError, TimeoutError, RuntimeError, ValueError,
                OSError) as exc:
            logger.error("Failed to switch provider: %s", exc)
            self._last_error = str(exc)
            return False

    def force_reconnect(self) -> bool:
        """Force reconnection to the current provider."""
        try:
            provider = ModelFactory.force_recreate()
            success = provider.is_available()

            if success:
                logger.info("Successfully reconnected to provider")
                self._last_error = None
            else:
                logger.error("Reconnection failed - provider not available")

            return success

        except (ConnectionError, TimeoutError, RuntimeError, ValueError,
                OSError) as exc:
            logger.error("Force reconnection failed: %s", exc)
            self._last_error = str(exc)
            return False

    def get_last_error(self) -> Optional[str]:
        """Get the last error that occurred."""
        return self._last_error

    def test_generation(
        self, test_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """Test text generation with a simple prompt."""
        if test_prompt is None:
            test_prompt = "Please respond with: 'Test successful'"

        try:
            start_time = time.time()
            # Use centralized token configuration for health checks
            from .token_config import get_token_config
            token_config = get_token_config()
            health_check_tokens = token_config.get_max_tokens('health_check')
            result = self.generate_text(
                test_prompt, max_tokens=health_check_tokens, temperature=0.1
            )
            end_time = time.time()

            return {
                'success': bool(result),
                'prompt': test_prompt,
                'result': result,
                'duration_seconds': round(end_time - start_time, 2),
                'result_length': len(result) if result else 0,
            }
        except (ConnectionError, TimeoutError, RuntimeError, ValueError,
                OSError) as exc:
            return {
                'success': False,
                'prompt': test_prompt,
                'error': str(exc),
                'duration_seconds': 0,
                'result_length': 0,
            }

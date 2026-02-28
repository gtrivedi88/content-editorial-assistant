"""
Llama Stack Provider for Lightrail Platform
Integrates Llama Stack client with the existing model system.
"""

import logging
import os
import ssl
from typing import Any, Dict, Optional

from llama_stack_client import DefaultHttpxClient, LlamaStackClient

from .base_provider import BaseModelProvider

logger = logging.getLogger(__name__)


class LlamaStackProvider(BaseModelProvider):
    """Llama Stack provider for Lightrail platform deployment.

    Uses Lightrail environment variables to connect to the managed
    Llama Stack instance. Integrates seamlessly with the existing
    ModelManager system.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize the Llama Stack provider."""
        self.client: Optional[LlamaStackClient] = None
        self.model_id: str = config.get('model', 'style_analyzer_model')
        super().__init__(config)

    def _validate_config(self) -> None:
        """Validate Llama Stack configuration."""
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
            ca_cert_path = os.environ.get(
                'LIGHTRAIL_LLAMA_STACK_TLS_SERVICE_CA_CERT_PATH'
            )

            # Setup TLS context for secure communication
            ctx = ssl.create_default_context()
            ctx.minimum_version = ssl.TLSVersion.TLSv1_2
            if ca_cert_path and os.path.exists(ca_cert_path):
                ctx.load_verify_locations(ca_cert_path)
                logger.debug(
                    "Loaded CA certificate from %s", ca_cert_path
                )

            # Initialize client with proper TLS
            self.client = LlamaStackClient(
                base_url=base_url,
                http_client=DefaultHttpxClient(verify=ctx)
            )

            # Test connection by listing models
            model_list = list(self.client.models.list())
            logger.info(
                "Connected to Llama Stack. Available models: %s",
                len(model_list)
            )
            self.is_connected = True
            return True

        except (OSError, ValueError) as exc:
            logger.error("Failed to connect to Llama Stack: %s", exc)
            self.is_connected = False
            return False

    def is_available(self) -> bool:
        """Check if Llama Stack is available."""
        if not self.is_connected or not self.client:
            return self.connect()

        try:
            model_list = list(self.client.models.list())
            return len(model_list) > 0
        except OSError as exc:
            logger.warning(
                "Llama Stack availability check failed: %s", exc
            )
            self.is_connected = False
            return False

    def generate_text(self, prompt: str, **kwargs: object) -> str:
        """Generate text using Llama Stack."""
        if not self.is_available():
            raise RuntimeError("Llama Stack is not available")

        if not self.client:
            raise RuntimeError("Llama Stack client not initialized")

        try:
            system_prompt = kwargs.pop('system_prompt', '')
            messages: list[Dict[str, Any]] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            temperature = kwargs.get('temperature', 0.4)
            # Use centralized token configuration
            from ..token_config import get_token_config
            token_config = get_token_config(self.config)
            default_max_tokens = token_config.get_max_tokens('default')
            max_tokens = kwargs.get('max_tokens', default_max_tokens)

            call_kwargs: Dict[str, Any] = {
                "model_id": self.model_id,
                "messages": messages,
                "sampling_params": {
                    "type": "top_p",
                    "temperature": temperature,
                    "top_p": kwargs.get('top_p', 0.9),
                    "max_tokens": max_tokens,
                },
            }
            response_format = kwargs.get('response_format')
            if response_format:
                call_kwargs["response_format"] = response_format

            response = self.client.inference.chat_completion(**call_kwargs)

            if (response.completion_message
                    and response.completion_message.content):
                result = response.completion_message.content
                logger.debug(
                    "Generated %s characters via Llama Stack", len(result)
                )
                return result

            logger.warning("Llama Stack returned empty response")
            return ""

        except (RuntimeError, OSError, ValueError) as exc:
            logger.error("Llama Stack generation failed: %s", exc)
            return ""

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Llama Stack setup."""
        info: Dict[str, Any] = {
            'provider_type': 'llamastack',
            'provider_name': 'Lightrail Llama Stack',
            'model_id': self.model_id,
            'connected': self.is_connected,
            'base_url': os.environ.get(
                'LIGHTRAIL_LLAMA_STACK_BASE_URL', 'Not configured'
            ),
        }

        if self.is_available() and self.client:
            try:
                model_list = list(self.client.models.list())
                info['available_models'] = [
                    getattr(m, 'model_id', str(m)) for m in model_list
                ]
            except OSError as exc:
                logger.debug("Could not fetch model list: %s", exc)

        return info

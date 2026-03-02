"""
Llama Stack Provider for Lightrail Platform
Integrates Llama Stack client with the existing model system.
"""

import logging
import os
import ssl
from typing import Any, Dict, Optional, Sequence

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

            # Resolve configured model_id against available models.
            # The server may require a provider prefix
            # (e.g. "vllm-inference/models/gemini-2.5-flash")
            # while the config only specifies a short name
            # (e.g. "gemini-2.5-flash" or "models/gemini-2.5-flash").
            self.model_id = self._resolve_model_id(
                self.model_id, model_list
            )

            self.is_connected = True
            return True

        except (OSError, ValueError) as exc:
            logger.error("Failed to connect to Llama Stack: %s", exc)
            self.is_connected = False
            return False

    @staticmethod
    def _resolve_model_id(
        configured_id: str, model_list: Sequence[object]
    ) -> str:
        """Resolve a short model ID against the available model list.

        The LlamaStack server registers models with a provider prefix
        (e.g. ``vllm-inference/models/gemini-2.5-flash``) while the
        deployment config may specify a short name like
        ``gemini-2.5-flash`` or ``models/gemini-2.5-flash``.  This
        method finds the full identifier by suffix matching.

        Returns the full identifier if a match is found, otherwise
        returns *configured_id* unchanged.
        """
        identifiers = [
            getattr(m, 'identifier', str(m)) for m in model_list
        ]

        # Exact match — already fully qualified
        if configured_id in identifiers:
            return configured_id

        # Suffix match — find the first model whose identifier ends
        # with the configured name (preceded by '/')
        suffix = '/' + configured_id.lstrip('/')
        for full_id in identifiers:
            if full_id.endswith(suffix):
                logger.info(
                    "Resolved model '%s' -> '%s'",
                    configured_id, full_id,
                )
                return full_id

        logger.warning(
            "Model '%s' not found in available models: %s",
            configured_id,
            [i for i in identifiers if 'gemini' in i.lower()][:5],
        )
        return configured_id

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
        """Generate text using Llama Stack.

        Uses the OpenAI-compatible ``/v1/chat/completions`` endpoint
        introduced in llama-stack-client 0.3.x.
        """
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
                "model": self.model_id,
                "messages": messages,
                "temperature": temperature,
                "top_p": kwargs.get('top_p', 0.9),
                "max_tokens": max_tokens,
            }
            seed = kwargs.get('seed')
            if seed is not None:
                call_kwargs["seed"] = seed
            response_format = kwargs.get('response_format')
            if response_format:
                call_kwargs["response_format"] = response_format

            response = self.client.chat.completions.create(**call_kwargs)

            if (response.choices
                    and response.choices[0].message
                    and response.choices[0].message.content):
                result = response.choices[0].message.content
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
                    getattr(m, 'identifier', str(m))
                    for m in model_list
                ]
            except OSError as exc:
                logger.debug("Could not fetch model list: %s", exc)

        return info

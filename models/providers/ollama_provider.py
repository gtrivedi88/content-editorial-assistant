"""
Ollama Provider
Local Ollama model provider.
"""

import logging
from typing import Any, Dict, List

import requests

from .base_provider import BaseModelProvider

logger = logging.getLogger(__name__)


class OllamaProvider(BaseModelProvider):
    """Provider for local Ollama models."""

    def _validate_config(self) -> None:
        """Validate Ollama-specific configuration."""
        required_fields = ['base_url', 'model']
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(
                    "Missing required Ollama config: %s" % field
                )

        # Ensure base_url format is correct
        if not self.config['base_url'].startswith('http'):
            raise ValueError(
                "Ollama base_url must start with http:// or https://"
            )

    def connect(self) -> bool:
        """Connect to Ollama and verify model is available."""
        try:
            response = requests.get(
                "%s/api/tags" % self.config['base_url'],
                timeout=self.config.get('timeout', 10)
            )

            if response.status_code != 200:
                logger.error(
                    "Ollama is not responding properly: %s",
                    response.status_code
                )
                return False

            # Check if our model is available
            models_data = response.json()
            available_models = [
                model['name']
                for model in models_data.get('models', [])
            ]

            if self.config['model'] not in available_models:
                logger.error(
                    "Model '%s' not found in Ollama. Available models: %s",
                    self.config['model'], available_models
                )
                logger.info(
                    "To install: ollama pull %s", self.config['model']
                )
                return False

            self.is_connected = True
            logger.info(
                "Connected to Ollama. Using model: %s", self.config['model']
            )
            return True

        except requests.exceptions.RequestException as exc:
            logger.error("Cannot connect to Ollama: %s", exc)
            logger.info("Make sure Ollama is running: ollama serve")
            return False
        except (KeyError, ValueError) as exc:
            logger.error(
                "Unexpected error connecting to Ollama: %s", exc
            )
            return False

    def is_available(self) -> bool:
        """Check if Ollama and the model are available.

        Returns:
            bool: True if ready to generate text.
        """
        if not self.is_connected:
            return self.connect()

        # Quick health check
        try:
            response = requests.get(
                "%s/api/tags" % self.config['base_url'],
                timeout=5
            )
            return response.status_code == 200
        except (requests.exceptions.RequestException, OSError):
            self.is_connected = False
            return False

    def generate_text(self, prompt: str, **kwargs: object) -> str:
        """Generate text using Ollama's chat API.

        Supports ``system_prompt`` for role-separated messages.

        Args:
            prompt: Input text prompt (sent as user message).
            **kwargs: Additional generation parameters.

        Returns:
            str: Generated text.
        """
        if not self.is_available():
            logger.error("Ollama is not available")
            return ""

        params = self._prepare_generation_params(**kwargs)
        system_prompt = params.pop('system_prompt', '')

        messages: List[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.config['model'],
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": params['temperature'],
                "top_p": params['top_p'],
                "top_k": params['top_k'],
                "num_predict": params['max_tokens'],
                "stop": [
                    "\n\nOriginal:", "\n\nRewrite:",
                    "###", "---", "\n\n\n",
                ],
            },
        }

        return self._send_chat_request(payload)

    def _send_chat_request(self, payload: Dict[str, Any]) -> str:
        """Send a chat request to the Ollama API.

        Args:
            payload: The complete request payload.

        Returns:
            Generated text, or empty string on failure.
        """
        try:
            response = requests.post(
                "%s/api/chat" % self.config['base_url'],
                json=payload,
                timeout=self.config.get('timeout', 60)
            )

            if response.status_code == 200:
                result = response.json()
                message = result.get('message', {})
                generated_text = message.get('content', '').strip()

                if generated_text:
                    logger.debug(
                        "Generated %s characters", len(generated_text)
                    )
                    return generated_text

                logger.warning("Ollama returned empty response")
                return ""

            logger.error(
                "Ollama API error: %s - %s",
                response.status_code, response.text
            )
            return ""

        except requests.exceptions.Timeout:
            logger.error("Ollama request timed out")
            return ""
        except (requests.exceptions.RequestException, OSError) as exc:
            logger.error("Ollama generation failed: %s", exc)
            return ""

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Ollama model setup.

        Returns:
            dict: Model information.
        """
        base_info: Dict[str, Any] = {
            'provider': 'Ollama',
            'type': 'Local',
            'model': self.config['model'],
            'base_url': self.config['base_url'],
            'connected': self.is_connected,
            'available': self.is_available(),
        }

        # Try to get additional model details from Ollama
        if self.is_connected:
            try:
                response = requests.get(
                    "%s/api/tags" % self.config['base_url'],
                    timeout=5
                )
                if response.status_code == 200:
                    models_data = response.json()
                    for model in models_data.get('models', []):
                        if model['name'] == self.config['model']:
                            digest = model.get('digest')
                            base_info.update({
                                'size': model.get('size', 'Unknown'),
                                'modified_at': model.get(
                                    'modified_at', 'Unknown'
                                ),
                                'digest': (
                                    digest[:12] + '...'
                                    if digest
                                    else 'Unknown'
                                ),
                            })
                            break
            except (requests.exceptions.RequestException, OSError) as exc:
                logger.debug(
                    "Could not fetch detailed model info: %s", exc
                )

        return base_info

    def disconnect(self) -> None:
        """Clean up Ollama provider resources."""
        super().disconnect()
        logger.info("Disconnected from Ollama")

    def list_available_models(self) -> List[str]:
        """List all models available in local Ollama instance.

        Returns:
            list: Available model names.
        """
        try:
            response = requests.get(
                "%s/api/tags" % self.config['base_url'],
                timeout=10
            )

            if response.status_code == 200:
                models_data = response.json()
                return [
                    model['name']
                    for model in models_data.get('models', [])
                ]

            logger.error(
                "Could not fetch model list: %s", response.status_code
            )
            return []

        except (requests.exceptions.RequestException, OSError) as exc:
            logger.error("Error fetching available models: %s", exc)
            return []

"""
API Provider
Universal API provider for any OpenAI-compatible REST API service.
"""

import logging
from typing import Any, Dict, Union

import requests

from .base_provider import BaseModelProvider

logger = logging.getLogger(__name__)


class APIProvider(BaseModelProvider):
    """Universal API provider for any OpenAI-compatible REST API service."""

    def _validate_config(self) -> None:
        """Validate API provider configuration."""
        required_fields = ['base_url', 'model', 'api_key']
        for field in required_fields:
            if not self.config.get(field):
                raise ValueError(
                    "Missing required API config: %s" % field
                )

        if not self.config['base_url'].startswith('http'):
            raise ValueError(
                "API base_url must start with http:// or https://"
            )

    def connect(self) -> bool:
        """Test connection to the API provider."""
        try:
            headers = self._get_headers()
            test_endpoint = self._get_health_check_endpoint()

            cert_path = self.config.get('cert_path')
            verify: Union[str, bool] = cert_path if cert_path else True

            response = requests.get(
                test_endpoint,
                headers=headers,
                timeout=self.config.get('timeout', 10),
                verify=verify
            )

            # Accept various response codes - some APIs return
            # different codes for /models
            if response.status_code in [200, 401, 403, 404]:
                self.is_connected = True
                logger.info(
                    "Connected to API at %s (status: %s)",
                    self.config['base_url'], response.status_code
                )
                return True

            logger.warning(
                "API connection test returned %s, "
                "trying alternative endpoint",
                response.status_code
            )
            # Try chat completions endpoint as fallback
            return self._test_chat_endpoint(headers, verify)

        except (requests.exceptions.RequestException, OSError) as exc:
            logger.error(
                "Unexpected error connecting to API: %s", exc
            )
            return False

    def _get_test_max_tokens(self) -> int:
        """Get appropriate max_tokens for API testing."""
        try:
            from ..token_config import get_token_config
            token_config = get_token_config(self.config)
            return token_config.get_max_tokens('test_payload')
        except (ImportError, ValueError, KeyError):
            # Fallback if token config fails
            return 1

    def _test_chat_endpoint(
        self,
        headers: Dict[str, str],
        verify: Union[str, bool],
    ) -> bool:
        """Test connection using chat completions endpoint."""
        try:
            base_url = self.config['base_url'].rstrip('/')
            chat_endpoint = "%s/chat/completions" % base_url

            # Minimal test payload
            test_payload = {
                "model": self.config['model'],
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": self._get_test_max_tokens(),
            }

            response = requests.post(
                chat_endpoint,
                json=test_payload,
                headers=headers,
                timeout=self.config.get('timeout', 10),
                verify=verify
            )

            # Accept various response codes for connection test
            if response.status_code in [200, 400, 401, 403]:
                self.is_connected = True
                logger.info(
                    "Connected to API via chat endpoint (status: %s)",
                    response.status_code
                )
                return True

            logger.error(
                "Chat endpoint test failed: %s", response.status_code
            )
            return False

        except (requests.exceptions.RequestException, OSError) as exc:
            logger.error("Chat endpoint test failed: %s", exc)
            return False

    def _get_health_check_endpoint(self) -> str:
        """Get health check endpoint."""
        base_url = self.config['base_url'].rstrip('/')
        return "%s/models" % base_url

    def _get_headers(self) -> Dict[str, str]:
        """Get standard headers for API requests."""
        return {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer %s' % self.config['api_key'],
        }

    def is_available(self) -> bool:
        """Check if the API provider and model are available."""
        if not self.is_connected:
            return self.connect()

        return self.is_connected

    def generate_text(self, prompt: str, **kwargs: object) -> str:
        """Generate text using the API provider with optimized timeouts."""
        if not self.is_available():
            logger.error("API is not available")
            return ""

        params = self._prepare_generation_params(**kwargs)
        endpoint, payload = self._build_request(prompt, params)
        headers = self._get_headers()

        # Optimize timeout based on use case
        use_case = kwargs.get('use_case', 'default')
        timeout = self._get_timeout_for_use_case(use_case)

        try:
            cert_path = self.config.get('cert_path')
            verify: Union[str, bool] = cert_path if cert_path else True

            response = requests.post(
                endpoint,
                json=payload,
                headers=headers,
                timeout=timeout,
                verify=verify
            )

            if response.status_code == 200:
                generated_text = self._extract_response(response.json())

                if generated_text:
                    logger.debug(
                        "Generated %s characters", len(generated_text)
                    )
                    return generated_text.strip()

                logger.warning("API returned empty response")
                return ""
            elif response.status_code == 429:
                logger.error(
                    "API rate limit exceeded (429). Consider reducing "
                    "request frequency or upgrading your API plan."
                )
                return ""
            elif response.status_code in [400, 413]:
                logger.error(
                    "API error: %s - Request may be too large or "
                    "malformed. Response: %s",
                    response.status_code, response.text
                )
                return ""
            else:
                logger.error(
                    "API error: %s - %s",
                    response.status_code, response.text
                )
                return ""

        except requests.exceptions.Timeout:
            logger.error("API request timed out")
            return ""
        except (requests.exceptions.RequestException, OSError) as exc:
            logger.error("API generation failed: %s", exc)
            return ""

    def _build_request(
        self, prompt: str, params: Dict[str, Any]
    ) -> tuple:
        """Build the API request endpoint and payload."""
        base_url = self.config['base_url'].rstrip('/')
        endpoint = "%s/chat/completions" % base_url

        system_prompt = params.pop('system_prompt', '')
        messages: list[Dict[str, Any]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.config['model'],
            "messages": messages,
            "temperature": params['temperature'],
            "max_tokens": params['max_tokens'],
            "top_p": params['top_p'],
        }

        response_format = params.pop('response_format', None)
        if response_format:
            payload["response_format"] = response_format

        return endpoint, payload

    def _get_timeout_for_use_case(self, use_case: object) -> int:
        """Get optimized timeout based on use case."""
        timeout_map = {
            'surgical': 8,
            'surgical_batch': 12,
            'health_check': 5,
            'test_payload': 3,
            'title_extraction': 10,
            'rewriting': 45,
            'assembly_line': 45,
            'default': 45,
        }

        timeout = timeout_map.get(
            use_case, self.config.get('timeout', 30)
        )
        logger.debug(
            "Using %ss timeout for use_case '%s'", timeout, use_case
        )
        return timeout

    def _extract_response(self, response_data: Any) -> str:
        """Extract generated text from API response."""
        try:
            # OpenAI-compatible format
            if isinstance(response_data, dict):
                if 'choices' in response_data and response_data['choices']:
                    choice = response_data['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        return choice['message']['content'].strip()
                    elif 'text' in choice:
                        return choice['text'].strip()

                # Direct content fields
                for field in ['content', 'text', 'generated_text']:
                    if field in response_data and response_data[field]:
                        return response_data[field].strip()

            # Array response
            if isinstance(response_data, list) and response_data:
                first_item = response_data[0]
                if isinstance(first_item, str):
                    return first_item.strip()
                elif isinstance(first_item, dict):
                    for field in ['generated_text', 'text', 'content']:
                        if field in first_item and first_item[field]:
                            return first_item[field].strip()

            # Log the actual API issue for debugging
            logger.warning(
                "API response missing content. Response structure: %s",
                response_data
            )
            return ""

        except (KeyError, IndexError, TypeError, AttributeError) as exc:
            logger.error("Error extracting response: %s", exc)
            return ""

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the API model setup."""
        return {
            'provider': 'Generic API',
            'type': 'Remote API',
            'model': self.config['model'],
            'base_url': self.config['base_url'],
            'connected': self.is_connected,
            'available': self.is_available(),
            'has_api_key': bool(self.config.get('api_key')),
        }

    def disconnect(self) -> None:
        """Clean up API provider resources."""
        super().disconnect()
        logger.info("Disconnected from API")

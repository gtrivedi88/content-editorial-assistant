"""
Centralized Token Configuration
Provides use-case specific token limits while respecting .env configuration.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class TokenConfig:
    """Centralized token configuration with use-case specific defaults."""

    def __init__(self, model_config: Dict[str, Any]) -> None:
        """Initialize with model configuration from .env via ModelConfig."""
        self.base_max_tokens: int = model_config.get('max_tokens', 3072)
        logger.debug(
            "TokenConfig initialized with base_max_tokens: %s",
            self.base_max_tokens
        )

    def get_max_tokens(self, use_case: str = 'default') -> int:
        """Get max_tokens based on use case, bounded by .env configuration.

        Args:
            use_case: The specific use case for token limits.
                'default' - Main text generation (full limit from .env)
                'health_check' - Quick API connectivity test (small)
                'title_extraction' - Short title generation (limited)
                'test_payload' - Minimal API response test (tiny)

        Returns:
            Appropriate max_tokens for the use case, never exceeding .env limit.
        """
        use_case_limits = {
            'default': self.base_max_tokens,
            'health_check': min(50, self.base_max_tokens),
            'title_extraction': min(100, self.base_max_tokens),
            'test_payload': min(1, self.base_max_tokens),
            'rewriting': max(2048, self.base_max_tokens),
            'assembly_line': max(2048, self.base_max_tokens),
            'holistic_rewrite': max(2048, self.base_max_tokens),
            'surgical': min(800, self.base_max_tokens),
            'surgical_batch': min(1200, self.base_max_tokens),
        }

        result = use_case_limits.get(use_case, self.base_max_tokens)

        if use_case not in use_case_limits:
            logger.warning(
                "Unknown use_case '%s', using default: %s", use_case, result
            )

        logger.debug(
            "TokenConfig.get_max_tokens('%s') = %s (base: %s)",
            use_case, result, self.base_max_tokens
        )
        return result

    def get_all_limits(self) -> Dict[str, int]:
        """Get all use case limits for debugging/monitoring."""
        return {
            use_case: self.get_max_tokens(use_case)
            for use_case in [
                'default', 'health_check', 'title_extraction',
                'test_payload', 'rewriting', 'assembly_line',
                'holistic_rewrite', 'surgical', 'surgical_batch',
            ]
        }

    def __repr__(self) -> str:
        """Return string representation of TokenConfig."""
        return "TokenConfig(base_max_tokens=%s)" % self.base_max_tokens


# Singleton instance - created when first imported
_token_config: Optional[TokenConfig] = None


def get_token_config(
    model_config: Optional[Dict[str, Any]] = None
) -> TokenConfig:
    """Get the global TokenConfig instance.

    Args:
        model_config: Model configuration dict (only needed for initialization).

    Returns:
        TokenConfig instance.
    """
    global _token_config  # noqa: PLW0603

    if _token_config is None:
        if model_config is None:
            # Import here to avoid circular imports
            from .config import ModelConfig
            model_config = ModelConfig.get_active_config()

        _token_config = TokenConfig(model_config)
        logger.info("Initialized global TokenConfig: %s", _token_config)

    return _token_config


def refresh_token_config() -> None:
    """Force refresh of token configuration (useful after .env changes)."""
    global _token_config  # noqa: PLW0603
    _token_config = None
    logger.info("TokenConfig refreshed - will reload on next access")

"""
Centralized Token Configuration
Provides use-case specific token limits while respecting .env configuration.
"""

import logging
from typing import Dict

logger = logging.getLogger(__name__)


class TokenConfig:
    """Centralized token configuration with use-case specific defaults."""
    
    def __init__(self, model_config: Dict[str, any]):
        """Initialize with model configuration from .env via ModelConfig."""
        self.base_max_tokens = model_config.get('max_tokens', 3072)
        logger.debug(f"TokenConfig initialized with base_max_tokens: {self.base_max_tokens}")
    
    def get_max_tokens(self, use_case: str = 'default') -> int:
        """
        Get max_tokens based on use case, bounded by .env configuration.
        
        Args:
            use_case: The specific use case for token limits
                     'default' - Main text generation (full limit from .env)
                     'health_check' - Quick API connectivity test (small)
                     'title_extraction' - Short title generation (limited)  
                     'metadata_extraction' - Brief metadata generation (limited)
                     'test_payload' - Minimal API response test (tiny)
                     
        Returns:
            Appropriate max_tokens for the use case, never exceeding .env limit
        """
        use_case_limits = {
            'default': self.base_max_tokens,                    # Full limit - main generation
            'health_check': min(50, self.base_max_tokens),      # Quick test, but respect .env
            'title_extraction': min(100, self.base_max_tokens), # Short titles, bounded by .env
            'metadata_extraction': min(1000, self.base_max_tokens), # Brief metadata, bounded
            'test_payload': min(1, self.base_max_tokens),       # Minimal test, but respect .env
            'rewriting': max(2048, self.base_max_tokens),       # Sufficient tokens for complex prompts + response
            'assembly_line': max(2048, self.base_max_tokens),   # Sufficient tokens for complex prompts + response
            'surgical': min(800, self.base_max_tokens),         # BALANCED: Fast but sufficient for response
            'surgical_batch': min(1200, self.base_max_tokens),  # BALANCED: Fast but sufficient for batch response
        }
        
        result = use_case_limits.get(use_case, self.base_max_tokens)
        
        if use_case not in use_case_limits:
            logger.warning(f"Unknown use_case '{use_case}', using default: {result}")
        
        logger.debug(f"TokenConfig.get_max_tokens('{use_case}') = {result} (base: {self.base_max_tokens})")
        return result
    
    def get_all_limits(self) -> Dict[str, int]:
        """Get all use case limits for debugging/monitoring."""
        return {
            use_case: self.get_max_tokens(use_case) 
            for use_case in [
                'default', 'health_check', 'title_extraction', 
                'metadata_extraction', 'test_payload', 'rewriting', 'assembly_line',
                'surgical', 'surgical_batch'
            ]
        }
    
    def __repr__(self) -> str:
        return f"TokenConfig(base_max_tokens={self.base_max_tokens})"


# Singleton instance - created when first imported
_token_config = None


def get_token_config(model_config: Dict[str, any] = None) -> TokenConfig:
    """
    Get the global TokenConfig instance.
    
    Args:
        model_config: Model configuration dict (only needed for initialization)
        
    Returns:
        TokenConfig instance
    """
    global _token_config
    
    if _token_config is None:
        if model_config is None:
            # Import here to avoid circular imports
            from .config import ModelConfig
            model_config = ModelConfig.get_active_config()
        
        _token_config = TokenConfig(model_config)
        logger.info(f"Initialized global TokenConfig: {_token_config}")
    
    return _token_config


def refresh_token_config():
    """Force refresh of token configuration (useful after .env changes)."""
    global _token_config
    _token_config = None
    logger.info("TokenConfig refreshed - will reload on next access")

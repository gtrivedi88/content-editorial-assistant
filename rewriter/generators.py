"""
Text Generation Module
Handles actual AI text generation using various models.
"""

import logging
import requests
from typing import Optional, Dict, Any
from models import ModelManager

logger = logging.getLogger(__name__)


class TextGenerator:
    """Handles AI text generation using various models."""
    
    def __init__(self, model_manager: ModelManager):
        """Initialize the text generator with a model manager."""
        self.model_manager = model_manager
    
    def generate_text(self, prompt: str, original_text: str, use_case: str = 'rewriting') -> str:
        """
        Generate text using optimized token and timeout configuration based on use case.
        
        Args:
            prompt: The prompt to use for generation
            original_text: Original text as fallback
            use_case: Use case for optimization ('surgical', 'surgical_batch', 'rewriting', etc.)
            
        Returns:
            Generated text or original text if generation fails
        """
        try:
            # Import here to avoid circular imports
            from models.token_config import get_token_config
            
            # Use use-case-specific token configuration
            token_config = get_token_config()
            max_tokens = token_config.get_max_tokens(use_case)
            
            # Log prompt size for debugging
            prompt_length = len(prompt)
            logger.debug(f"Generating text with prompt length: {prompt_length} chars, max_tokens: {max_tokens}, use_case: {use_case}")
            
            if prompt_length > 8000:  # Approximately 2000 tokens
                logger.warning(f"Prompt is very long ({prompt_length} chars). This may consume most of the token budget.")
            
            result = self.model_manager.generate_text(
                prompt, 
                max_tokens=max_tokens,
                temperature=0.4,  # Consistent temperature for rewriting
                use_case=use_case  # Pass through for timeout optimization
            )
            
            if result and result.strip():
                logger.debug(f"Successfully generated {len(result)} characters")
                return result
            else:
                logger.warning("Model returned empty or whitespace-only result, falling back to original text")
                return original_text
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return original_text
    
    def is_available(self) -> bool:
        """Check if text generation is available."""
        return self.model_manager.is_available()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current generation setup."""
        return {
            **self.model_manager.get_model_info(),
            'generation_available': self.is_available()
        }
    
    # Legacy methods for backward compatibility in case they're used elsewhere
    def generate_with_ollama(self, prompt: str, original_text: str) -> str:
        """Legacy method - now delegates to new system."""
        return self.generate_text(prompt, original_text)
    
    def generate_with_hf_model(self, prompt: str, original_text: str) -> str:
        """Legacy method - now delegates to new system."""
        return self.generate_text(prompt, original_text) 
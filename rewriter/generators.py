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
    
    def generate_text(self, prompt: str, original_text: str) -> str:
        """
        Generate text using the new model system.
        
        Args:
            prompt: The prompt to use for generation
            original_text: Original text as fallback
            
        Returns:
            Generated text or original text if generation fails
        """
        try:
            result = self.model_manager.generate_text(prompt)
            return result if result else original_text
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
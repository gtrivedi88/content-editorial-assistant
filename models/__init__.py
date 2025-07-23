"""
Models Module
Centralized AI model management for the Style Guide Application.

QUICK START:
============
from models import ModelManager

# Basic usage
manager = ModelManager()
result = manager.generate_text("Rewrite this text...")

# Check status
if manager.is_available():
    print("Model ready!")
else:
    print("Model not available")

CONFIGURATION:
==============
Edit models/config.py to change providers and models.

Current setup supports:
- Ollama (local): llama3:8b (default)
- Groq API: llama3-70b-8192
- HuggingFace API: various models
- OpenAI API: GPT models

TO SWITCH PROVIDERS:
===================
1. Edit models/config.py
2. Set ACTIVE_PROVIDER = 'ollama' or 'api'
3. Configure provider-specific settings
4. Restart application

OR switch programmatically:
manager.switch_provider('api', {'api_provider': 'groq', 'model': 'llama3-70b-8192'})
"""

# Main interface - this is what other modules should import
from .model_manager import ModelManager

# Configuration access
from .config import ModelConfig

# Factory for advanced usage
from .factory import ModelFactory

# Provider classes for custom implementations
from .providers.base_provider import BaseModelProvider
from .providers.ollama_provider import OllamaProvider
from .providers.api_provider import APIProvider

# Export the main interface
__all__ = [
    'ModelManager',      # PRIMARY INTERFACE
    'ModelConfig',       # Configuration access
    'ModelFactory',      # Advanced provider management
    'BaseModelProvider', # For custom providers
    'OllamaProvider',    # Ollama implementation
    'APIProvider'        # API implementation
]

# Version info
__version__ = "1.0.0"
__author__ = "Style Guide AI Team"

# Module-level convenience functions
def get_model_manager() -> ModelManager:
    """
    Get a ModelManager instance.
    
    This is the recommended way to access AI models.
    
    Returns:
        ModelManager: Ready-to-use model manager
    """
    return ModelManager()

def quick_generate(prompt: str, **kwargs) -> str:
    """
    Quick text generation without creating a manager instance.
    
    Args:
        prompt: Text to generate from
        **kwargs: Generation parameters
        
    Returns:
        str: Generated text
    """
    manager = ModelManager()
    return manager.generate_text(prompt, **kwargs)

def check_model_status() -> dict:
    """
    Quick status check without creating a manager instance.
    
    Returns:
        dict: Model status information
    """
    manager = ModelManager()
    return manager.get_status()

def is_model_available() -> bool:
    """
    Quick availability check.
    
    Returns:
        bool: True if model is ready to use
    """
    manager = ModelManager()
    return manager.is_available()

# Log module initialization
import logging
logger = logging.getLogger(__name__)
logger.info("Models module initialized. Use ModelManager for AI operations.") 
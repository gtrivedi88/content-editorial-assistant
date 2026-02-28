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
    logging.info("Model ready!")
else:
    logging.info("Model not available")

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

import logging

from .model_manager import ModelManager
from .config import ModelConfig
from .factory import ModelFactory
from .providers.base_provider import BaseModelProvider
from .providers.ollama_provider import OllamaProvider
from .providers.api_provider import APIProvider

try:
    from .providers.llamastack_provider import LlamaStackProvider
except ImportError:
    LlamaStackProvider = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)

__all__ = [
    'ModelManager',
    'ModelConfig',
    'ModelFactory',
    'BaseModelProvider',
    'OllamaProvider',
    'APIProvider',
    'LlamaStackProvider',
]

__version__ = "1.0.0"
__author__ = "Content Editorial Assistant Team"


def get_model_manager() -> ModelManager:
    """Get a ModelManager instance.

    This is the recommended way to access AI models.

    Returns:
        ModelManager: Ready-to-use model manager.
    """
    return ModelManager()


def quick_generate(prompt: str, **kwargs: object) -> str:
    """Quick text generation without creating a manager instance.

    Args:
        prompt: Text to generate from.
        **kwargs: Generation parameters.

    Returns:
        str: Generated text.
    """
    manager = ModelManager()
    return manager.generate_text(prompt, **kwargs)


def check_model_status() -> dict:
    """Quick status check without creating a manager instance.

    Returns:
        dict: Model status information.
    """
    manager = ModelManager()
    return manager.get_status()


def is_model_available() -> bool:
    """Quick availability check.

    Returns:
        bool: True if model is ready to use.
    """
    manager = ModelManager()
    return manager.is_available()


logger.info("Models module initialized. Use ModelManager for AI operations.")

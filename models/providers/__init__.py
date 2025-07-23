"""
Model Providers Module
Contains all AI model provider implementations.

Available Providers:
- OllamaProvider: Local Ollama models
- APIProvider: External API providers (Groq, HuggingFace, OpenAI)
- BaseModelProvider: Abstract base class for custom providers

To add a new provider:
1. Create a new provider class inheriting from BaseModelProvider
2. Implement all abstract methods
3. Register it in factory.py
"""

from .base_provider import BaseModelProvider
from .ollama_provider import OllamaProvider
from .api_provider import APIProvider

__all__ = [
    'BaseModelProvider',
    'OllamaProvider', 
    'APIProvider'
] 
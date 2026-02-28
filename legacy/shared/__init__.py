"""
Shared utilities module
Provides singleton instances and shared resources to reduce memory usage.
"""
from .spacy_singleton import get_spacy_model, is_spacy_available, reset_spacy_model

__all__ = ['get_spacy_model', 'is_spacy_available', 'reset_spacy_model']


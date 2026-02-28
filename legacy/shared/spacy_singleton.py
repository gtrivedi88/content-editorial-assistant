"""
Shared SpaCy Model Singleton
"""
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)

# Global instance cache
_spacy_model = None
_spacy_available = None


@lru_cache(maxsize=1)
def get_spacy_model():
    """
    Get the cached SpaCy model instance.
    Loads the model once and returns the same instance on subsequent calls.
    
    Returns:
        spacy.Language: The loaded SpaCy model, or None if unavailable
    """
    global _spacy_model, _spacy_available
    
    if _spacy_model is not None:
        return _spacy_model
    
    if _spacy_available is False:
        return None
    
    try:
        import spacy
        _spacy_model = spacy.load("en_core_web_sm")
        _spacy_available = True
        logger.info("✓ Loaded spaCy model: en_core_web_sm (singleton)")
        return _spacy_model
    except (ImportError, OSError) as e:
        _spacy_available = False
        logger.warning(f"SpaCy model not available: {e}")
        return None


def is_spacy_available() -> bool:
    """
    Check if SpaCy is available without loading the model.
    
    Returns:
        bool: True if SpaCy can be loaded, False otherwise
    """
    global _spacy_available
    
    if _spacy_available is not None:
        return _spacy_available
    
    # Try to load to check availability
    model = get_spacy_model()
    return model is not None


def reset_spacy_model():
    """
    Reset the cached model (useful for testing).
    """
    global _spacy_model, _spacy_available
    _spacy_model = None
    _spacy_available = None
    get_spacy_model.cache_clear()


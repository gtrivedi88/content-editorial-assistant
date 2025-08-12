"""
Language and Grammar Vocabulary Services

This package provides services for managing YAML-based vocabularies
for language and grammar rules.
"""

from .language_vocabulary_service import (
    get_articles_vocabulary,
    get_plurals_vocabulary,
    get_verbs_vocabulary,
    get_anthropomorphism_vocabulary,
    get_inclusive_language_vocabulary,
    DomainContext
)

__all__ = [
    'get_articles_vocabulary',
    'get_plurals_vocabulary', 
    'get_verbs_vocabulary',
    'get_anthropomorphism_vocabulary',
    'get_inclusive_language_vocabulary',
    'DomainContext'
]

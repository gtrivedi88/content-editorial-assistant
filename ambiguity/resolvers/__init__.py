"""
Ambiguity Resolvers Package

This package contains resolvers that provide strategies for fixing
different types of ambiguity in technical writing.
"""

# Resolvers will be imported as they are created
__all__ = []

# Try to import available resolvers
try:
    from .actor_resolver import ActorResolver
    __all__.append('ActorResolver')
except ImportError:
    pass

try:
    from .pronoun_resolver import PronounResolver
    __all__.append('PronounResolver')
except ImportError:
    pass 
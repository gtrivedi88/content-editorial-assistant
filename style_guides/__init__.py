"""Style guides package -- citation mappings and excerpt data for all supported guides.

Exports unified registry functions for convenient access to citations,
excerpts, and confidence adjustments across IBM Style Guide, Red Hat SSG,
Accessibility guidelines, and Modular Documentation standards.
"""

try:
    from style_guides.registry import (
        format_citation,
        get_citation,
        get_confidence_adjustment,
        get_excerpt,
        get_verification_status,
    )
except ImportError:
    pass

__all__ = [
    'get_citation',
    'get_excerpt',
    'format_citation',
    'get_confidence_adjustment',
    'get_verification_status',
]

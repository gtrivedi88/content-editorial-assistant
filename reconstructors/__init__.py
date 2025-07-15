"""
Document Reconstructors Package

Provides format-specific document reconstruction capabilities for the AI rewriter.
Handles rebuilding documents while preserving their original structure and formatting.

Supported Formats:
- AsciiDoc (.adoc)
- Markdown (.md) - planned

Usage:
    from reconstructors import get_reconstructor
    
    reconstructor = get_reconstructor('asciidoc')
    result = reconstructor.reconstruct(document, block_results)
"""

from typing import Dict, Any, List, Optional
import logging

from .base_reconstructor import BaseReconstructor, ReconstructionResult
from .asciidoc.asciidoc_reconstructor import AsciiDocReconstructor

logger = logging.getLogger(__name__)

# Registry of available reconstructors
_RECONSTRUCTOR_REGISTRY: Dict[str, type] = {
    'asciidoc': AsciiDocReconstructor,
    'adoc': AsciiDocReconstructor,  # Alias
    # 'markdown': MarkdownReconstructor,  # TODO: Implement later
    # 'md': MarkdownReconstructor,  # TODO: Implement later
}

def get_reconstructor(format_name: str, **kwargs) -> BaseReconstructor:
    """
    Get a reconstructor instance for the specified format.
    
    Args:
        format_name: Format name ('asciidoc', 'adoc', 'markdown', 'md')
        **kwargs: Additional arguments passed to reconstructor constructor
        
    Returns:
        BaseReconstructor instance for the specified format
        
    Raises:
        ValueError: If format is not supported
    """
    format_key = format_name.lower().strip()
    
    if format_key not in _RECONSTRUCTOR_REGISTRY:
        available = ', '.join(_RECONSTRUCTOR_REGISTRY.keys())
        raise ValueError(f"Unsupported format '{format_name}'. Available: {available}")
    
    reconstructor_class = _RECONSTRUCTOR_REGISTRY[format_key]
    return reconstructor_class(**kwargs)

def get_supported_formats() -> List[str]:
    """Get list of supported reconstruction formats."""
    return list(_RECONSTRUCTOR_REGISTRY.keys())

def is_format_supported(format_name: str) -> bool:
    """Check if a format is supported for reconstruction."""
    return format_name.lower().strip() in _RECONSTRUCTOR_REGISTRY

__all__ = [
    'BaseReconstructor',
    'ReconstructionResult', 
    'AsciiDocReconstructor',
    'get_reconstructor',
    'get_supported_formats',
    'is_format_supported'
] 
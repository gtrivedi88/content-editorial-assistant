"""
AsciiDoc Elements Package

This package provides element-specific parsing and handling for AsciiDoc documents.
Each element type (titles, admonitions, procedures, etc.) is implemented as a 
separate module with its own parsing, UI, and rule components.

Usage:
    from structural_parsing.asciidoc.elements import element_coordinator
    
    # Process document with element-specific parsing
    result = element_coordinator.process_document_blocks(document_data)
"""

from .base.element_parser import ElementParser, ElementParseResult
from .registry import ElementRegistry, element_registry
from .coordinator import ElementCoordinator, element_coordinator

# Import bootstrap to trigger auto-registration
from . import bootstrap

__all__ = [
    'ElementParser',
    'ElementParseResult', 
    'ElementRegistry',
    'ElementCoordinator',
    'element_registry',
    'element_coordinator',
    'bootstrap'
] 
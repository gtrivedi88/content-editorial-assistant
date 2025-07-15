"""
Element Registry for AsciiDoc Elements

Maintains a registry of all element parsers and provides routing
functionality to determine which parser should handle each block.
"""

from typing import Dict, List, Type, Optional, Any
import logging

from .base.element_parser import ElementParser, ElementParseResult

logger = logging.getLogger(__name__)

class ElementRegistry:
    """
    Registry for AsciiDoc element parsers.
    
    This class maintains a registry of all available element parsers
    and provides routing functionality to determine which parser
    should handle each block type.
    """
    
    def __init__(self):
        self._parsers: Dict[str, ElementParser] = {}
        self._context_mapping: Dict[str, List[str]] = {}
        self._registered_elements: List[str] = []
    
    def register_element(self, parser_class: Type[ElementParser]) -> None:
        """
        Register an element parser.
        
        Args:
            parser_class: The element parser class to register
        """
        try:
            parser = parser_class()
            element_type = parser.element_type
            
            if element_type in self._parsers:
                logger.warning(f"Element parser for '{element_type}' already registered. Overwriting.")
            
            self._parsers[element_type] = parser
            self._registered_elements.append(element_type)
            
            # Build context mapping for faster lookup
            for context in parser.supported_contexts:
                if context not in self._context_mapping:
                    self._context_mapping[context] = []
                self._context_mapping[context].append(element_type)
            
            logger.info(f"Registered element parser: {element_type}")
            
        except Exception as e:
            logger.error(f"Failed to register element parser {parser_class.__name__}: {e}")
    
    def get_parser_for_block(self, block_data: Dict[str, Any]) -> Optional[ElementParser]:
        """
        Get the appropriate parser for a block.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            ElementParser instance or None if no parser can handle the block
        """
        context = block_data.get('context', '')
        
        # Get potential parsers based on context
        potential_parsers = self._context_mapping.get(context, [])
        
        # Find the first parser that can handle this block
        for element_type in potential_parsers:
            parser = self._parsers.get(element_type)
            if parser and parser.can_parse(block_data):
                return parser
        
        return None
    
    def get_parser_by_type(self, element_type: str) -> Optional[ElementParser]:
        """
        Get a parser by element type.
        
        Args:
            element_type: The element type (e.g., 'title', 'admonition')
            
        Returns:
            ElementParser instance or None
        """
        return self._parsers.get(element_type)
    
    def get_all_parsers(self) -> Dict[str, ElementParser]:
        """Get all registered parsers."""
        return self._parsers.copy()
    
    def get_registered_elements(self) -> List[str]:
        """Get list of all registered element types."""
        return self._registered_elements.copy()
    
    def is_supported_context(self, context: str) -> bool:
        """Check if a context is supported by any registered parser."""
        return context in self._context_mapping
    
    def get_implementation_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get implementation status of all elements.
        
        Returns:
            Dictionary with implementation status for tracking
        """
        status = {
            'implemented': {},
            'planned': [
                'callouts',
                'cross_references', 
                'footnotes',
                'index_terms',
                'page_breaks',
                'includes',
                'comments',
                'attributes'
            ],
            'total_registered': len(self._registered_elements)
        }
        
        for element_type, parser in self._parsers.items():
            status['implemented'][element_type] = {
                'contexts': parser.supported_contexts,
                'parser_class': parser.__class__.__name__
            }
        
        return status

# Global registry instance
element_registry = ElementRegistry() 
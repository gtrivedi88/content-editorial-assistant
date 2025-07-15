"""
Element Coordinator for AsciiDoc Processing

Coordinates the parsing of AsciiDoc blocks using registered element parsers.
Acts as the main orchestrator between the Ruby parser output and element-specific processing.
"""

from typing import Dict, List, Any, Optional
import logging

from .base.element_parser import ElementParseResult
from .registry import element_registry

logger = logging.getLogger(__name__)

class ElementCoordinator:
    """
    Coordinates element-specific parsing for AsciiDoc blocks.
    
    This class takes the raw output from the Ruby AsciiDoc parser
    and routes each block to the appropriate element parser.
    """
    
    def __init__(self, registry=None):
        """
        Initialize the coordinator.
        
        Args:
            registry: ElementRegistry instance (uses global instance if None)
        """
        self.registry = registry or element_registry
        self._parsing_stats = {
            'total_blocks': 0,
            'parsed_blocks': 0,
            'failed_blocks': 0,
            'unhandled_blocks': 0,
            'by_element_type': {}
        }
    
    def process_document_blocks(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process all blocks in a document using element-specific parsers.
        
        Args:
            document_data: Raw document data from Ruby parser
            
        Returns:
            Enhanced document data with element-specific processing
        """
        self._reset_stats()
        
        # Process document-level data
        processed_data = {
            'title': document_data.get('title'),
            'attributes': document_data.get('attributes', {}),
            'blocks': [],
            'element_metadata': {
                'parsing_stats': {},
                'implementation_status': self.registry.get_implementation_status()
            }
        }
        
        # Process each block
        blocks = document_data.get('blocks', [])
        for block_data in blocks:
            processed_block = self._process_block(block_data)
            if processed_block:
                processed_data['blocks'].append(processed_block)
        
        # Add parsing statistics
        processed_data['element_metadata']['parsing_stats'] = self._parsing_stats.copy()
        
        return processed_data
    
    def _process_block(self, block_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a single block using appropriate element parser.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            Enhanced block data or None if processing failed
        """
        self._parsing_stats['total_blocks'] += 1
        
        # Get appropriate parser for this block
        parser = self.registry.get_parser_for_block(block_data)
        
        if not parser:
            self._parsing_stats['unhandled_blocks'] += 1
            logger.debug(f"No parser found for block context: {block_data.get('context', 'unknown')}")
            return self._create_fallback_block(block_data)
        
        try:
            # Parse using element-specific parser
            parse_result = parser.parse_element(block_data)
            
            if parse_result.success:
                self._parsing_stats['parsed_blocks'] += 1
                element_type = parser.element_type
                
                # Update element type statistics
                if element_type not in self._parsing_stats['by_element_type']:
                    self._parsing_stats['by_element_type'][element_type] = 0
                self._parsing_stats['by_element_type'][element_type] += 1
                
                # Create enhanced block data
                enhanced_block = self._create_enhanced_block(
                    block_data, 
                    parser, 
                    parse_result
                )
                
                # Process children recursively
                children = block_data.get('children', [])
                if children:
                    enhanced_block['children'] = []
                    for child_data in children:
                        processed_child = self._process_block(child_data)
                        if processed_child:
                            enhanced_block['children'].append(processed_child)
                
                return enhanced_block
            else:
                self._parsing_stats['failed_blocks'] += 1
                logger.warning(f"Element parsing failed for {parser.element_type}: {parse_result.errors}")
                return self._create_fallback_block(block_data)
                
        except Exception as e:
            self._parsing_stats['failed_blocks'] += 1
            logger.error(f"Exception during element parsing: {e}")
            return self._create_fallback_block(block_data)
    
    def _create_enhanced_block(self, block_data: Dict[str, Any], 
                              parser, parse_result: ElementParseResult) -> Dict[str, Any]:
        """
        Create enhanced block data with element-specific information.
        
        Args:
            block_data: Original block data
            parser: Element parser that handled the block
            parse_result: Result from element parsing
            
        Returns:
            Enhanced block data
        """
        # Get display information from parser
        display_info = parser.get_display_info(parse_result.element_data or {})
        
        enhanced_block = {
            # Original block data
            'context': block_data.get('context'),
            'content': block_data.get('content', ''),
            'level': block_data.get('level', 0),
            'attributes': block_data.get('attributes', {}),
            'lines': block_data.get('lines', []),
            'source_location': block_data.get('source_location'),
            
            # Element-specific enhancements
            'element_type': parser.element_type,
            'element_data': parse_result.element_data,
            'display_info': display_info,
            'parsing_errors': parse_result.errors,
            
            # UI rendering hints
            'block_type': parser.element_type,  # For compatibility with existing UI
            'should_skip_analysis': display_info.get('skip_analysis', False)
        }
        
        return enhanced_block
    
    def _create_fallback_block(self, block_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create fallback block data for unhandled blocks.
        
        Args:
            block_data: Original block data
            
        Returns:
            Fallback block data
        """
        context = block_data.get('context', 'unknown')
        
        return {
            'context': context,
            'content': block_data.get('content', ''),
            'level': block_data.get('level', 0),
            'attributes': block_data.get('attributes', {}),
            'lines': block_data.get('lines', []),
            'source_location': block_data.get('source_location'),
            
            # Fallback information
            'element_type': 'fallback',
            'element_data': {'original_context': context},
            'display_info': {
                'icon': 'fas fa-file-alt',
                'title': f'Unknown Block ({context})',
                'skip_analysis': True
            },
            'parsing_errors': [f'No parser available for context: {context}'],
            
            # UI rendering hints
            'block_type': context,
            'should_skip_analysis': True
        }
    
    def _reset_stats(self):
        """Reset parsing statistics."""
        self._parsing_stats = {
            'total_blocks': 0,
            'parsed_blocks': 0,
            'failed_blocks': 0,
            'unhandled_blocks': 0,
            'by_element_type': {}
        }
    
    def get_parsing_stats(self) -> Dict[str, Any]:
        """Get current parsing statistics."""
        return self._parsing_stats.copy()

# Global coordinator instance
element_coordinator = ElementCoordinator() 
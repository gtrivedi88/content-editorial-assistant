"""
Bootstrap module for AsciiDoc element parsers.

This module automatically registers all available element parsers
with the global registry when imported.
"""

import logging
from typing import List, Type, Dict, Any

from .base.element_parser import ElementParser
from .registry import element_registry

logger = logging.getLogger(__name__)

def get_available_parsers() -> List[Type[ElementParser]]:
    """
    Get all available element parser classes.
    
    Returns:
        List of element parser classes
    """
    parsers = []
    
    # Import and collect all parser classes
    try:
        from .titles.parser import TitleParser
        parsers.append(TitleParser)
    except ImportError as e:
        logger.warning(f"Could not import TitleParser: {e}")
    
    try:
        from .admonitions.parser import AdmonitionParser
        parsers.append(AdmonitionParser)
    except ImportError as e:
        logger.warning(f"Could not import AdmonitionParser: {e}")
    
    try:
        from .code_blocks.parser import CodeBlockParser
        parsers.append(CodeBlockParser)
    except ImportError as e:
        logger.warning(f"Could not import CodeBlockParser: {e}")
    
    try:
        from .tables.parser import TableParser
        parsers.append(TableParser)
    except ImportError as e:
        logger.warning(f"Could not import TableParser: {e}")
    
    try:
        from .procedures.parser import ProcedureParser
        parsers.append(ProcedureParser)
    except ImportError as e:
        logger.warning(f"Could not import ProcedureParser: {e}")
    
    try:
        from .lists.parser import ListParser
        parsers.append(ListParser)
    except ImportError as e:
        logger.warning(f"Could not import ListParser: {e}")
    
    try:
        from .delimited_blocks.parser import DelimitedBlockParser
        parsers.append(DelimitedBlockParser)
    except ImportError as e:
        logger.warning(f"Could not import DelimitedBlockParser: {e}")
    
    try:
        from .paragraphs.parser import ParagraphParser
        parsers.append(ParagraphParser)
    except ImportError as e:
        logger.warning(f"Could not import ParagraphParser: {e}")
    
    return parsers

def register_all_parsers(registry=None) -> None:
    """
    Register all available element parsers.
    
    Args:
        registry: ElementRegistry instance (uses global if None)
    """
    if registry is None:
        registry = element_registry
    
    parsers = get_available_parsers()
    
    logger.info(f"Registering {len(parsers)} element parsers...")
    
    for parser_class in parsers:
        try:
            registry.register_element(parser_class)
        except Exception as e:
            logger.error(f"Failed to register {parser_class.__name__}: {e}")
    
    # Log registration summary
    registered_elements = registry.get_registered_elements()
    logger.info(f"Successfully registered parsers for: {', '.join(registered_elements)}")

def get_implementation_status() -> Dict[str, Any]:
    """
    Get detailed implementation status of all elements.
    
    Returns:
        Dictionary with implementation details
    """
    registry_status = element_registry.get_implementation_status()
    
    # Create new status dict with mixed types
    status = {
        'implemented': registry_status.get('implemented', {}),
        'planned': registry_status.get('planned', []),
        'total_registered': registry_status.get('total_registered', 0),
        'available_modules': {
            'titles': 'Complete - handles document titles and headings',
            'admonitions': 'Complete - handles NOTE, TIP, WARNING, IMPORTANT, CAUTION',
            'code_blocks': 'Complete - handles listing and literal blocks',
            'tables': 'Complete - handles table structures with rows and cells',
            'procedures': 'Complete - handles numbered procedure steps with validation',
            'lists': 'Complete - handles ordered, unordered, and description lists',
            'delimited_blocks': 'Complete - handles sidebar, example, quote, verse blocks',
            'paragraphs': 'Complete - handles regular text paragraphs with readability analysis'
        },
        'completion_percentage': len(registry_status.get('implemented', {})) / (len(registry_status.get('implemented', {})) + len(registry_status.get('planned', []))) * 100
    }
    
    return status

# Auto-register parsers when module is imported
try:
    register_all_parsers()
    logger.info("Element parsers auto-registration completed")
except Exception as e:
    logger.error(f"Auto-registration failed: {e}")
    # Don't fail completely, just log the error 
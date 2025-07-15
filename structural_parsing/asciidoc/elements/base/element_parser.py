"""
Base classes for element-specific parsing.
Each AsciiDoc element type should inherit from these base classes.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

@dataclass
class ElementParseResult:
    """Result of parsing a specific element type."""
    success: bool
    element_data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []

class ElementParser(ABC):
    """
    Base class for element-specific parsers.
    
    Each AsciiDoc element type (titles, admonitions, procedures, etc.)
    should have its own parser that inherits from this class.
    """
    
    @property
    @abstractmethod
    def element_type(self) -> str:
        """Return the element type this parser handles (e.g., 'title', 'admonition')."""
        pass
    
    @property
    @abstractmethod
    def supported_contexts(self) -> List[str]:
        """Return list of AsciiDoc contexts this parser handles (e.g., ['heading'], ['admonition'])."""
        pass
    
    @abstractmethod
    def can_parse(self, block_data: Dict[str, Any]) -> bool:
        """
        Check if this parser can handle the given block data.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            True if this parser can handle this block
        """
        pass
    
    @abstractmethod
    def parse_element(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """
        Parse the element-specific data from block data.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            ElementParseResult with parsed element data
        """
        pass
    
    @abstractmethod
    def get_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get display information for UI rendering.
        
        Args:
            element_data: Parsed element data
            
        Returns:
            Dictionary with UI display information
        """
        pass
    
    def validate_element(self, element_data: Dict[str, Any]) -> List[str]:
        """
        Validate the parsed element data.
        
        Args:
            element_data: Parsed element data
            
        Returns:
            List of validation errors (empty if valid)
        """
        return []  # Override in subclasses for specific validation 
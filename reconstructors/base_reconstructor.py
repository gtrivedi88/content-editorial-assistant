"""
Base Document Reconstructor

Defines the abstract interface and common functionality for all document reconstructors.
Provides shared utilities and structure for format-specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class ReconstructionResult:
    """Result of document reconstruction."""
    reconstructed_content: str
    success: bool
    format_name: str
    blocks_processed: int
    metadata_preserved: bool
    structure_preserved: bool
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

class BaseReconstructor(ABC):
    """
    Abstract base class for document reconstructors.
    
    Provides the interface and common functionality for rebuilding documents
    from parsed structures and rewritten content while preserving formatting.
    """
    
    def __init__(self, preserve_metadata: bool = True, preserve_structure: bool = True):
        """
        Initialize the reconstructor.
        
        Args:
            preserve_metadata: Whether to preserve document metadata (headers, attributes)
            preserve_structure: Whether to preserve document structure (sections, hierarchy)
        """
        self.preserve_metadata = preserve_metadata
        self.preserve_structure = preserve_structure
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    @property
    @abstractmethod
    def format_name(self) -> str:
        """Return the format name this reconstructor handles."""
        pass
    
    @property
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """Return list of file extensions this reconstructor supports."""
        pass
    
    @abstractmethod
    def reconstruct(self, document: Any, block_results: List[Any]) -> ReconstructionResult:
        """
        Reconstruct document with rewritten content.
        
        Args:
            document: Parsed document structure
            block_results: List of BlockRewriteResult objects with rewritten content
            
        Returns:
            ReconstructionResult with reconstructed document
        """
        pass
    
    def _log_reconstruction_start(self, document: Any, block_count: int) -> None:
        """Log the start of reconstruction process."""
        self.logger.info(f"Starting {self.format_name} reconstruction with {block_count} blocks")
    
    def _log_reconstruction_complete(self, result: ReconstructionResult) -> None:
        """Log the completion of reconstruction process."""
        status = "successfully" if result.success else "with errors"
        self.logger.info(
            f"Completed {self.format_name} reconstruction {status}. "
            f"Processed {result.blocks_processed} blocks"
        )
        
        if result.warnings:
            for warning in result.warnings:
                self.logger.warning(f"Reconstruction warning: {warning}")
        
        if result.errors:
            for error in result.errors:
                self.logger.error(f"Reconstruction error: {error}")
    
    def _validate_inputs(self, document: Any, block_results: List[Any]) -> List[str]:
        """
        Validate reconstruction inputs.
        
        Args:
            document: Document structure to validate
            block_results: Block results to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        if not document:
            errors.append("Document is required for reconstruction")
        
        if not isinstance(block_results, list):
            errors.append("Block results must be a list")
        elif len(block_results) == 0:
            errors.append("At least one block result is required")
        
        return errors
    
    def _create_error_result(self, errors: List[str]) -> ReconstructionResult:
        """Create a failed reconstruction result with errors."""
        return ReconstructionResult(
            reconstructed_content="",
            success=False,
            format_name=self.format_name,
            blocks_processed=0,
            metadata_preserved=False,
            structure_preserved=False,
            errors=errors
        )
    
    def _extract_block_mapping(self, block_results: List[Any]) -> Dict[str, str]:
        """
        Extract mapping from original blocks to rewritten content.
        
        Args:
            block_results: List of block rewrite results
            
        Returns:
            Dictionary mapping block IDs to their rewritten content
        """
        block_mapping = {}
        
        for i, result in enumerate(block_results):
            if hasattr(result, 'original_block') and hasattr(result, 'rewritten_content'):
                # Use block index as key since blocks might not be hashable
                block_key = f"block_{i}"
                block_mapping[block_key] = result.rewritten_content
                
                # Store the block object reference for later use
                if not hasattr(self, '_block_references'):
                    self._block_references = {}
                self._block_references[block_key] = result.original_block
            else:
                self.logger.warning("Block result missing required attributes")
        
        return block_mapping
    
    def can_handle_document(self, document: Any) -> bool:
        """
        Check if this reconstructor can handle the given document.
        
        Args:
            document: Document to check
            
        Returns:
            True if this reconstructor can handle the document
        """
        # Default implementation - subclasses should override for specific checks
        return document is not None

class ReconstructionError(Exception):
    """Exception raised during document reconstruction."""
    
    def __init__(self, message: str, format_name: Optional[str] = None, original_error: Optional[Exception] = None):
        self.message = message
        self.format_name = format_name
        self.original_error = original_error
        super().__init__(self.message)

def validate_reconstruction_inputs(document: Any, block_results: List[Any]) -> None:
    """
    Validate inputs for reconstruction and raise exception if invalid.
    
    Args:
        document: Document to validate
        block_results: Block results to validate
        
    Raises:
        ReconstructionError: If inputs are invalid
    """
    if not document:
        raise ReconstructionError("Document is required for reconstruction")
    
    if not isinstance(block_results, list):
        raise ReconstructionError("Block results must be a list")
    
    if len(block_results) == 0:
        raise ReconstructionError("At least one block result is required")

def get_block_content_mapping(block_results: List[Any]) -> Dict[str, str]:
    """
    Create a mapping of block IDs to their rewritten content.
    
    Args:
        block_results: List of block rewrite results
        
    Returns:
        Dictionary mapping block identifiers to rewritten content
    """
    mapping = {}
    
    for i, result in enumerate(block_results):
        if hasattr(result, 'rewritten_content'):
            # Use block index as fallback identifier
            block_id = getattr(result, 'block_id', f"block_{i}")
            mapping[block_id] = result.rewritten_content
    
    return mapping 
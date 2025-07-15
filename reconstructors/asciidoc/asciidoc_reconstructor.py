"""
AsciiDoc Document Reconstructor

Main reconstructor class that coordinates all components to rebuild 
complete AsciiDoc documents from parsed structures and rewritten content.

This class orchestrates:
- Header building (metadata, attributes)  
- Content formatting (blocks, markup)
- Structure building (hierarchy, organization)
"""

from typing import Dict, Any, List, Optional
import logging

from ..base_reconstructor import BaseReconstructor, ReconstructionResult
from .header_builder import HeaderBuilder
from .content_formatter import ContentFormatter  
from .structure_builder import StructureBuilder

logger = logging.getLogger(__name__)

class AsciiDocReconstructor(BaseReconstructor):
    """
    Main AsciiDoc document reconstructor.
    
    Coordinates header building, content formatting, and structure building
    to create complete, properly formatted AsciiDoc documents.
    """
    
    def __init__(
        self, 
        preserve_metadata: bool = True,
        preserve_structure: bool = True,
        preserve_formatting: bool = True
    ):
        """
        Initialize the AsciiDoc reconstructor.
        
        Args:
            preserve_metadata: Whether to preserve document metadata
            preserve_structure: Whether to preserve document structure
            preserve_formatting: Whether to preserve original formatting
        """
        super().__init__(preserve_metadata, preserve_structure)
        
        # Initialize component builders
        self.header_builder = HeaderBuilder(
            include_metadata=preserve_metadata,
            include_attributes=preserve_metadata
        )
        
        self.content_formatter = ContentFormatter(
            preserve_original_formatting=preserve_formatting
        )
        
        self.structure_builder = StructureBuilder(
            preserve_hierarchy=preserve_structure,
            include_empty_sections=False
        )
    
    @property
    def format_name(self) -> str:
        """Return the format name this reconstructor handles."""
        return "asciidoc"
    
    @property  
    def supported_extensions(self) -> List[str]:
        """Return list of file extensions this reconstructor supports."""
        return ['.adoc', '.asciidoc', '.asc']
    
    def reconstruct(self, document: Any, block_results: List[Any]) -> ReconstructionResult:
        """
        Reconstruct complete AsciiDoc document with rewritten content.
        
        Args:
            document: Parsed AsciiDoc document structure
            block_results: List of BlockRewriteResult objects with rewritten content
            
        Returns:
            ReconstructionResult with reconstructed document
        """
        # Log reconstruction start
        self._log_reconstruction_start(document, len(block_results))
        
        # Validate inputs
        validation_errors = self._validate_inputs(document, block_results)
        if validation_errors:
            result = self._create_error_result(validation_errors)
            self._log_reconstruction_complete(result)
            return result
        
        try:
            # Extract block mapping
            block_mapping = self._extract_block_mapping(block_results)
            
            # Build document header with rewritten content
            header_content = ""
            if self.preserve_metadata:
                # Find rewritten title if available
                rewritten_title = self._find_rewritten_title(block_results)
                header_content = self.header_builder.build_header(document, "", rewritten_title)
            
            # Format individual blocks and build content directly
            body_parts = []
            processed_blocks = 0
            
            if self.preserve_structure:
                # Process blocks hierarchically using document structure
                body_parts = self._build_structured_content(document, block_results)
                processed_blocks = len(block_results)
            else:
                # Simple processing without hierarchy
                for result in block_results:
                    if hasattr(result, 'original_block') and hasattr(result, 'rewritten_content'):
                        formatted_block = self.content_formatter.format_block(
                            result.original_block,
                            result.rewritten_content
                        )
                        
                        if formatted_block:
                            body_parts.append(formatted_block)
                        
                        processed_blocks += 1
            
            # Join body content
            body_content = "\n\n".join(body_parts) if body_parts else ""
            
            # Combine header and body
            document_parts = []
            
            if header_content:
                document_parts.append(header_content)
            
            if body_content:
                document_parts.append(body_content)
            
            # Create final document
            reconstructed_content = "\n".join(document_parts)
            
            # Validate structure
            structure_warnings = self.structure_builder.validate_structure(document)
            
            # Create successful result
            result = ReconstructionResult(
                reconstructed_content=reconstructed_content,
                success=True,
                format_name=self.format_name,
                blocks_processed=processed_blocks,
                metadata_preserved=self.preserve_metadata and bool(header_content),
                structure_preserved=self.preserve_structure,
                warnings=structure_warnings
            )
            
        except Exception as e:
            # Handle reconstruction errors
            self.logger.error(f"Error during AsciiDoc reconstruction: {e}")
            result = ReconstructionResult(
                reconstructed_content="",
                success=False,
                format_name=self.format_name,
                blocks_processed=0,
                metadata_preserved=False,
                structure_preserved=False,
                errors=[f"Reconstruction failed: {str(e)}"]
            )
        
        # Log completion
        self._log_reconstruction_complete(result)
        return result
    
    def can_handle_document(self, document: Any) -> bool:
        """
        Check if this reconstructor can handle the given document.
        
        Args:
            document: Document to check
            
        Returns:
            True if this reconstructor can handle the document
        """
        if not document:
            return False
        
        # Check if it's an AsciiDoc document
        if hasattr(document, '__class__'):
            class_name = document.__class__.__name__
            if 'AsciiDoc' in class_name:
                return True
        
        # Check if it has AsciiDoc-specific attributes
        if hasattr(document, 'attributes') and hasattr(document, 'blocks'):
            # Likely an AsciiDoc document
            return True
        
        return False
    
    def _build_structured_content(self, document: Any, block_results: List[Any]) -> List[str]:
        """
        Build structured content from document and block results.
        
        Args:
            document: Parsed document structure
            block_results: List of block rewrite results
            
        Returns:
            List of formatted content parts
        """
        content_parts = []
        
        # Create mapping from block results for quick lookup
        block_content_map = {}
        rewritten_blocks = set()  # Track which blocks have been rewritten
        
        for i, result in enumerate(block_results):
            if hasattr(result, 'original_block') and hasattr(result, 'rewritten_content'):
                block_id = id(result.original_block)
                block_content_map[block_id] = result.rewritten_content
                rewritten_blocks.add(block_id)
                logger.info(f"Mapping block {i} to rewritten content: '{result.rewritten_content[:50]}...'")
        
        # Process document blocks hierarchically - only include rewritten content
        if hasattr(document, 'blocks'):
            for block in document.blocks:
                block_id = id(block)
                
                # Only process blocks that have been rewritten
                if block_id in rewritten_blocks:
                    # Skip document titles (level 0 headings) since they're already in the header
                    if self._is_document_title(block):
                        logger.info(f"Skipping document title from body (already in header): {self._get_block_type(block)}")
                        continue
                    
                    rewritten_content = block_content_map[block_id]
                    formatted_block = self.content_formatter.format_block(block, rewritten_content)
                    if formatted_block:
                        content_parts.append(formatted_block)
                        logger.info(f"Added rewritten block: '{formatted_block[:50]}...'")
                else:
                    # Skip blocks that weren't rewritten (like attributes, metadata)
                    logger.info(f"Skipping non-rewritten block: {self._get_block_type(block)}")
        
        return content_parts
    
    def _process_structured_block(self, block: Any, content_map: Dict[int, str]) -> str:
        """
        Process a block and its children with structure preservation.
        
        Args:
            block: Block to process
            content_map: Mapping from block IDs to rewritten content
            
        Returns:
            Formatted block content with children
        """
        parts = []
        
        # Get rewritten content for this block
        block_id = id(block)
        rewritten_content = content_map.get(block_id, "")
        
        # Format the block with rewritten content
        if rewritten_content:
            formatted_block = self.content_formatter.format_block(block, rewritten_content)
            if formatted_block:
                parts.append(formatted_block)
        
        # Process children if this is a structural block
        if hasattr(block, 'children') and block.children:
            child_parts = []
            for child in block.children:
                child_content = self._process_structured_block(child, content_map)
                if child_content:
                    child_parts.append(child_content)
            
            # Add children with appropriate spacing
            if child_parts:
                if parts:  # If we have block content, add spacing
                    parts.append("")  # Empty line for spacing
                parts.extend(child_parts)
        
        return "\n".join(parts) if parts else ""
    
    def _find_rewritten_title(self, block_results: List[Any]) -> Optional[str]:
        """Find rewritten title from block results."""
        for result in block_results:
            if hasattr(result, 'original_block') and hasattr(result, 'rewritten_content'):
                block = result.original_block
                if self._is_document_title(block):
                    return result.rewritten_content
        return None
    
    def _is_document_title(self, block: Any) -> bool:
        """Check if a block is a document title (level 0 heading)."""
        if hasattr(block, 'block_type') and hasattr(block.block_type, 'value'):
            if block.block_type.value == 'heading':
                # Check if this is the document title (level 0)
                level = getattr(block, 'level', 1)
                return level == 0
        return False
    
    def _get_block_type(self, block: Any) -> str:
        """Get the block type string."""
        if hasattr(block, 'block_type'):
            if hasattr(block.block_type, 'value'):
                return block.block_type.value
            else:
                return str(block.block_type)
        
        # Fallback: try to infer from other attributes
        if hasattr(block, 'context'):
            return block.context
        
        return 'unknown'
    
    def get_reconstruction_options(self) -> Dict[str, Any]:
        """
        Get available reconstruction options for this format.
        
        Returns:
            Dictionary of available options and their descriptions
        """
        return {
            'preserve_metadata': {
                'description': 'Include document metadata (title, author, version)',
                'type': 'boolean',
                'default': True
            },
            'preserve_structure': {
                'description': 'Preserve document hierarchy and structure',
                'type': 'boolean', 
                'default': True
            },
            'preserve_formatting': {
                'description': 'Preserve original formatting hints',
                'type': 'boolean',
                'default': True
            },
            'include_attributes': {
                'description': 'Include document attributes (toc, numbered, etc.)',
                'type': 'boolean',
                'default': True
            }
        }
    
    def get_document_outline(self, document: Any) -> List[Dict[str, Any]]:
        """
        Get a structural outline of the document.
        
        Args:
            document: Document to outline
            
        Returns:
            List of outline items
        """
        return self.structure_builder.get_document_outline(document)
    
    def get_metadata_summary(self, document: Any) -> Dict[str, Any]:
        """
        Get a summary of document metadata.
        
        Args:
            document: Document to analyze
            
        Returns:
            Dictionary with metadata summary
        """
        if not document:
            return {}
        
        summary = {
            'title': getattr(document, 'title', None),
            'has_attributes': hasattr(document, 'attributes') and bool(document.attributes),
            'total_blocks': len(getattr(document, 'blocks', [])),
            'format': 'AsciiDoc'
        }
        
        # Extract author info if available
        if hasattr(document, 'attributes') and document.attributes:
            attrs = document.attributes
            if 'author' in attrs:
                summary['author'] = attrs['author']
            if 'email' in attrs:
                summary['email'] = attrs['email']
            if 'revnumber' in attrs:
                summary['version'] = attrs['revnumber']
            if 'revdate' in attrs:
                summary['revision_date'] = attrs['revdate']
        
        return summary
    
    def estimate_reconstruction_complexity(self, document: Any, block_results: List[Any]) -> str:
        """
        Estimate the complexity of reconstructing this document.
        
        Args:
            document: Document to analyze
            block_results: Block results to process
            
        Returns:
            Complexity level ('simple', 'moderate', 'complex')
        """
        if not document or not block_results:
            return 'simple'
        
        complexity_factors = 0
        
        # Check number of blocks
        if len(block_results) > 20:
            complexity_factors += 1
        
        # Check for metadata
        if hasattr(document, 'attributes') and len(document.attributes) > 10:
            complexity_factors += 1
        
        # Check for deep hierarchy
        max_level = 0
        if hasattr(document, 'blocks'):
            for block in document.blocks:
                level = getattr(block, 'level', 0)
                max_level = max(max_level, level)
        
        if max_level > 3:
            complexity_factors += 1
        
        # Check for complex block types
        complex_types = {'table', 'listing', 'admonition', 'sidebar'}
        if hasattr(document, 'blocks'):
            for block in document.blocks:
                block_type = getattr(block, 'block_type', None)
                if block_type and hasattr(block_type, 'value') and block_type.value in complex_types:
                    complexity_factors += 1
                    break
        
        # Determine complexity level
        if complexity_factors == 0:
            return 'simple'
        elif complexity_factors <= 2:
            return 'moderate'
        else:
            return 'complex' 
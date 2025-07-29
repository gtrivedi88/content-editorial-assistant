"""
Block Processing Utilities
Handles the analysis and intelligent flattening of the document AST
into a list of blocks suitable for the UI.
"""
import logging
import re
from typing import List, Dict, Any
from .analysis_modes import AnalysisModeExecutor
# We need to import the types to reference them
from structural_parsing.asciidoc.types import AsciiDocBlock, AsciiDocBlockType

logger = logging.getLogger(__name__)

class BlockProcessor:
    """
    Processes a parsed document tree, running analysis on each node
    and flattening the structure into a list for the UI.
    """
    def __init__(self, mode_executor: AnalysisModeExecutor, analysis_mode: Any):
        self.mode_executor = mode_executor
        self.analysis_mode = analysis_mode
        self.flat_blocks = []

    def analyze_and_flatten_tree(self, root_node: Any) -> List[Any]:
        """
        Main entry point to recursively analyze and then flatten the document tree.
        """
        # Step 1: Run analysis on the entire nested tree first. This ensures
        # SpaCy errors are correctly attached to every node, including children.
        self._analyze_recursively(root_node)

        # Step 2: Now, flatten the fully analyzed tree into the list the UI expects.
        self.flat_blocks = []
        self._flatten_recursively(root_node)
        return self.flat_blocks

    def _analyze_recursively(self, block: Any):
        """Recursively traverses the AST to run analysis on every single node."""
        if not block:
            return

        # CRITICAL FIX: Skip analysis if block has already been analyzed
        # (prevents duplicate processing of list items)
        if hasattr(block, '_already_analyzed') and block._already_analyzed:
            # Still need to recurse through children in case they need analysis
            for child in block.children:
                self._analyze_recursively(child)
            return

        # Run SpaCy and other rule-based analysis on the block's content
        if not block.should_skip_analysis():
            content = block.get_text_content()
            # CRITICAL FIX: Ensure content is a string before analysis. This fixes the
            # error "'list' object has no attribute 'strip'" because container blocks
            # like lists might not have direct string content.
            if not isinstance(content, str):
                logger.warning(f"Block content for type {block.block_type} is not a string, skipping analysis.")
            else:
                context = block.get_context_info()
                
                # ENTERPRISE-GRADE FIX: Analyze document titles with heading context
                # since they will be converted to heading blocks for the UI
                if (context and context.get('block_type') == 'document' and
                    hasattr(block, 'title') and block.title and content.strip()):
                    # Override context for document titles to use heading analysis
                    heading_context = context.copy()
                    heading_context['block_type'] = 'heading'
                    heading_context['level'] = 0  # Document title is level 0
                    context = heading_context
                
                errors = self.mode_executor.analyze_block_content(block, content, self.analysis_mode, context)
                block._analysis_errors = errors

        # Continue the analysis down the tree for all children
        for child in block.children:
            self._analyze_recursively(child)

    def _flatten_recursively(self, block: Any):
        """
        Recursively traverses the analyzed tree to build the final flat list for the UI.
        This is the corrected "smart flattening" logic.
        """
        block_type = getattr(block, 'block_type', None)
        if not block_type:
            return
            
        # FINAL FIX: Filter out paragraphs that are Asciidoctor warnings.
        # This is more robust than the previous regex and checks if the paragraph
        # content simply starts with the warning text.
        if block_type == AsciiDocBlockType.PARAGRAPH:
            content = getattr(block, 'content', '').strip()
            if content.startswith('Unresolved directive in'):
                return  # Skip this block entirely.

        # FIX 3: Explicitly skip empty UNKNOWN blocks from being added to the UI list.
        if block_type == AsciiDocBlockType.UNKNOWN and not (hasattr(block, 'content') and block.content and block.content.strip()):
            return

        # FIX 1: Prevent duplicate document title heading by finding the first *heading* block.
        if block_type.value == 'document':
            if hasattr(block, 'title') and block.title:
                # Find the first child that is a heading block.
                first_heading_child = None
                for child in block.children:
                    if hasattr(child, 'block_type') and child.block_type.value == 'heading':
                        first_heading_child = child
                        break

                if (first_heading_child and
                    hasattr(first_heading_child, 'title') and
                    first_heading_child.title == block.title):
                    # The first heading child matches the doc title, so we don't need a synthetic one.
                    pass
                else:
                    # Create a synthetic heading for the document title.
                    title_block = self._create_document_title_from_document(block)
                    self.flat_blocks.append(title_block)

            # Process all children of the document.
            for child in block.children:
                self._flatten_recursively(child)
            return

        # FIX 2: Prevent adding skippable blocks (like toc::, include::) to the UI list.
        # If a block should be skipped, don't process it or its children further for flattening.
        if block.should_skip_analysis():
            return

        # For preamble and table_row container types, process children only
        if block_type.value in ['preamble', 'table_row']:
            for child in block.children:
                self._flatten_recursively(child)
            return

        # For sections, we create a synthetic 'heading' block for the UI, add it,
        # and then process the section's children.
        if block_type.value == 'section':
            heading_block = self._create_heading_from_section(block)
            self.flat_blocks.append(heading_block)
            for child in block.children:
                self._flatten_recursively(child)
            return

        # For heading blocks that have children (like from AsciiDoc document structure),
        # add the heading and process its children
        if block_type.value == 'heading' and block.children:
            self.flat_blocks.append(block)
            for child in block.children:
                self._flatten_recursively(child)
            return

        # For table blocks, add them and also process their children (rows and cells)
        if block_type.value == 'table':
            self.flat_blocks.append(block)
            # Process table rows and cells
            for child in block.children:
                self._flatten_recursively(child)
            return

        # For table cells, add them to the flat list since they contain analyzable content
        if block_type.value == 'table_cell':
            self.flat_blocks.append(block)
            # Also process any children they might have
            for child in block.children:
                self._flatten_recursively(child)
            return

        # For all other displayable block types (paragraphs, lists, etc.),
        # we add them directly to the flat list. The UI will render their children
        # (like list items) from the block's .children property.
        # We explicitly exclude child-only types that are rendered by their parents.
        if block_type.value not in ['list_item', 'table_row', 'table_cell', 'table']:
             self.flat_blocks.append(block)

    def _create_heading_from_section(self, section_block: Any) -> Any:
        """Creates a 'heading' block from a 'section' block for UI compatibility."""
        from structural_parsing.asciidoc.types import AsciiDocBlock, AsciiDocBlockType
        
        heading_block = AsciiDocBlock(
            block_type=AsciiDocBlockType.HEADING,
            content=section_block.title or "",
            raw_content=section_block.raw_content,
            start_line=section_block.start_line,
            end_line=section_block.end_line,
            start_pos=section_block.start_pos,
            end_pos=section_block.end_pos,
            level=section_block.level,
            title=section_block.title,
            source_location=section_block.source_location,
            attributes=section_block.attributes
        )
        # Manually copy over any analysis errors that might have been attached to the section
        heading_block._analysis_errors = getattr(section_block, '_analysis_errors', [])
        return heading_block

    def _create_document_title_from_document(self, document_block: Any) -> Any:
        """Creates a 'heading' block from a 'document' title for UI compatibility."""
        from structural_parsing.asciidoc.types import AsciiDocBlock, AsciiDocBlockType

        title_block = AsciiDocBlock(
            block_type=AsciiDocBlockType.HEADING,
            content=document_block.title or "",
            raw_content=f"= {document_block.title}" if document_block.title else "",
            start_line=getattr(document_block, 'start_line', 0),
            end_line=getattr(document_block, 'end_line', 0),
            start_pos=getattr(document_block, 'start_pos', 0),
            end_pos=len(document_block.title or ""),
            level=0,  # Document title is level 0
            title=document_block.title,
            source_location=getattr(document_block, 'source_location', ''),
            attributes=getattr(document_block, 'attributes', None)
        )
        
        # Copy analysis errors from the document (since we analyzed it with heading context)
        title_block._analysis_errors = getattr(document_block, '_analysis_errors', [])
        
        return title_block

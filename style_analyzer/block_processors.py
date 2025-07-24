"""
Block Processing Utilities
Handles the analysis and intelligent flattening of the document AST
into a list of blocks suitable for the UI.
"""
import logging
from typing import List, Dict, Any
from .analysis_modes import AnalysisModeExecutor

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

        # Run SpaCy and other rule-based analysis on the block's content
        if not block.should_skip_analysis():
            content = block.get_text_content()
            context = block.get_context_info()
            errors = self.mode_executor._analyze_generic_content(content, self.analysis_mode, context)
            block._analysis_errors = errors

        # Continue the analysis down the tree for all children
        for child in block.children:
            self._analyze_recursively(child)

    def _flatten_recursively(self, block: Any):
        """
        Recursively traverses the analyzed tree to build the final flat list for the UI.
        """
        block_type = getattr(block, 'block_type', None)
        if not block_type:
            return

        # For container types, we don't add the container itself to the UI list,
        # but we MUST process their children. This was the bug you found.
        if block_type.value in ['document', 'preamble', 'table_row', 'table_cell']:
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

        # For all other displayable block types (paragraphs, lists, tables, etc.),
        # we add them directly to the flat list. The UI will render their children
        # (like list items) from the block's .children property.
        if block_type.value not in ['list_item']: # list_item is rendered by its parent
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

    @staticmethod
    def convert_children_to_dict(children: List[Any]) -> List[Dict[str, Any]]:
        """
        (Compatibility Method) This is no longer used by the core logic but is kept
        in case other parts of the system call it.
        """
        # This method is now effectively replaced by the to_dict() method on the block itself.
        return [child.to_dict() for child in children]
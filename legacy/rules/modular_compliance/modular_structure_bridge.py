"""
Modular Structure Bridge
Bridges the existing AsciiDoc parser to provide the structure format expected by modular compliance rules.
"""
from typing import Dict, Any, List
from structural_parsing.asciidoc.parser import AsciiDocParser
from structural_parsing.asciidoc.types import AsciiDocBlockType


class ModularStructureBridge:
    """
    Bridge between the existing AsciiDoc parser and modular compliance rules.
    
    This bridge:
    - Uses the existing sophisticated AsciiDoc parser (no duplication!)
    - Converts the AST structure to the format expected by compliance rules
    - Properly handles '. ' ordered list syntax via Asciidoctor
    - Provides the same interface as the old duplicate parser
    """
    
    def __init__(self):
        """Initialize with the existing AsciiDoc parser."""
        self.asciidoc_parser = AsciiDocParser()
    
    def parse(self, content: str) -> Dict[str, Any]:
        """
        Parse content using the existing AsciiDoc parser and convert to compliance format.
        
        Args:
            content: AsciiDoc content to parse
            
        Returns:
            Dictionary containing parsed structure elements in the format expected by compliance rules
        """
        if not content or not content.strip():
            return self._create_empty_structure()
        
        # Use the existing sophisticated parser
        parse_result = self.asciidoc_parser.parse(content)
        
        if not parse_result.success or not parse_result.document:
            # Fallback to empty structure if parsing fails
            return self._create_empty_structure()
        
        # Convert AST to compliance structure format
        structure = self._convert_ast_to_structure(parse_result.document, content)
        return structure
    
    def _convert_ast_to_structure(self, document, content: str) -> Dict[str, Any]:
        """Convert AsciiDoc AST to the structure format expected by compliance rules."""
        
        structure = {
            'title': document.title,
            'introduction_paragraphs': [],
            'sections': [],
            'ordered_lists': [],
            'unordered_lists': [],
            'tables': [],
            'table_cells': [],  # NEW: Track table cell content for analysis
            'code_blocks': [],
            'images': [],
            'line_count': len(content.split('\n')),
            'word_count': len(content.split()),
            'has_content': len(content.strip()) > 0
        }
        
        # Extract elements from the AST recursively
        self._extract_from_blocks(document.blocks, structure)
        
        # Extract introduction paragraphs separately (content before first major element)
        structure['introduction_paragraphs'] = self._extract_introduction_paragraphs(document.blocks)
        
        return structure
    
    def _extract_from_blocks(self, blocks, structure: Dict[str, Any]):
        """Recursively extract elements from AsciiDoc blocks."""
        for block in blocks:
            # Extract sections (headings)
            if block.block_type == AsciiDocBlockType.HEADING:
                structure['sections'].append({
                    'level': block.level,
                    'title': block.title or block.content,
                    'line_number': block.start_line,
                    'span': (block.start_pos, block.end_pos)
                })
            
            # Extract ordered lists (this is the key fix!)
            elif block.block_type == AsciiDocBlockType.ORDERED_LIST:
                ordered_list = {
                    'items': [],
                    'start_line': block.start_line
                }
                
                # Extract list items
                for child in block.children:
                    if child.block_type == AsciiDocBlockType.LIST_ITEM:
                        ordered_list['items'].append({
                            'text': child.content,
                            'line_number': child.start_line,
                            'span': (child.start_pos, child.end_pos)
                        })
                
                if ordered_list['items']:
                    structure['ordered_lists'].append(ordered_list)
            
            # Extract unordered lists
            elif block.block_type == AsciiDocBlockType.UNORDERED_LIST:
                unordered_list = {
                    'items': [],
                    'start_line': block.start_line
                }
                
                for child in block.children:
                    if child.block_type == AsciiDocBlockType.LIST_ITEM:
                        unordered_list['items'].append({
                            'text': child.content,
                            'line_number': child.start_line,
                            'span': (child.start_pos, child.end_pos)
                        })
                
                if unordered_list['items']:
                    structure['unordered_lists'].append(unordered_list)
            
            # Extract tables and their cell content
            elif block.block_type == AsciiDocBlockType.TABLE:
                table_data = {
                    'line_number': block.start_line,
                    'span': (block.start_pos, block.end_pos),
                    'cells': []
                }
                
                # Extract cell content recursively
                self._extract_table_cells(block, table_data['cells'], block.start_line)
                
                structure['tables'].append(table_data)
                
                # Also add cells to flat list for easier analysis
                for cell in table_data['cells']:
                    structure['table_cells'].append({
                        'text': cell['text'],
                        'line_number': cell['line_number'],
                        'span': cell['span']
                    })
            
            # Extract code blocks
            elif block.block_type in [AsciiDocBlockType.LISTING, AsciiDocBlockType.LITERAL]:
                structure['code_blocks'].append({
                    'content': block.content,
                    'line_number': block.start_line,
                    'span': (block.start_pos, block.end_pos)
                })
            
            # Extract images (if supported by the AST)
            elif block.block_type == AsciiDocBlockType.IMAGE:
                structure['images'].append({
                    'path': block.content,  # May need adjustment based on AST structure
                    'alt_text': block.title or '',
                    'line_number': block.start_line,
                    'span': (block.start_pos, block.end_pos)
                })
            
            # Recursively process children
            if hasattr(block, 'children') and block.children:
                self._extract_from_blocks(block.children, structure)
    
    def _extract_introduction_paragraphs(self, blocks) -> List[str]:
        """
        Extract introduction paragraphs (content before first major structural element).
        
        Per Red Hat: Introduction is a single, concise paragraph after the title.
        We collect all paragraphs that appear before the first == heading (level 2+).
        Tables, lists, etc. can appear after intro paragraphs without ending collection.
        """
        introduction_paragraphs = []
        found_title = False
        
        for block in blocks:
            # Skip until we find the title
            if not found_title:
                if block.block_type == AsciiDocBlockType.HEADING and block.level == 1:
                    found_title = True
                continue
            
            # Stop at first level-2+ heading (== or deeper) - this marks body sections
            if block.block_type == AsciiDocBlockType.HEADING and block.level >= 2:
                break
            
            # Collect paragraph content (continue collecting even if tables/lists appear)
            # This handles cases where intro is followed immediately by tables
            if (block.block_type == AsciiDocBlockType.PARAGRAPH and 
                block.content and block.content.strip()):
                introduction_paragraphs.append(block.content.strip())
                
        # If no paragraphs found but we have blocks after title, check for preamble
        if not introduction_paragraphs and found_title:
            # Some AsciiDoc parsers use PREAMBLE for content before first section
            for block in blocks:
                if block.block_type == AsciiDocBlockType.PREAMBLE:
                    # Extract paragraphs from preamble children
                    if hasattr(block, 'children'):
                        for child in block.children:
                            if (child.block_type == AsciiDocBlockType.PARAGRAPH and 
                                child.content and child.content.strip()):
                                introduction_paragraphs.append(child.content.strip())
        
        return introduction_paragraphs
    
    def _extract_table_cells(self, table_block, cells_list: List[Dict[str, Any]], table_start_line: int):
        """
        Recursively extract cell content from table blocks.
        
        Args:
            table_block: The table block to process
            cells_list: List to append cell data to
            table_start_line: Starting line number of the table
        """
        if not hasattr(table_block, 'children'):
            return
        
        for child in table_block.children:
            # Check if this is a table cell
            if hasattr(child, 'block_type') and str(child.block_type).endswith('TABLE_CELL'):
                cell_text = child.get_text_content() if hasattr(child, 'get_text_content') else child.content
                if cell_text and cell_text.strip():
                    cells_list.append({
                        'text': cell_text.strip(),
                        'line_number': child.start_line if hasattr(child, 'start_line') else table_start_line,
                        'span': (child.start_pos, child.end_pos) if hasattr(child, 'start_pos') else (0, 0)
                    })
            
            # Recursively process children (for nested structures)
            if hasattr(child, 'children') and child.children:
                self._extract_table_cells(child, cells_list, table_start_line)
    
    def _create_empty_structure(self) -> Dict[str, Any]:
        """Create empty structure for empty content or parsing failures."""
        return {
            'title': None,
            'introduction_paragraphs': [],
            'sections': [],
            'ordered_lists': [],
            'unordered_lists': [],
            'tables': [],
            'table_cells': [],
            'code_blocks': [],
            'images': [],
            'line_count': 0,
            'word_count': 0,
            'has_content': False
        }

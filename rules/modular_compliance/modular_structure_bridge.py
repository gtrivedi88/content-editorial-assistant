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
            
            # Extract tables
            elif block.block_type == AsciiDocBlockType.TABLE:
                structure['tables'].append({
                    'line_number': block.start_line,
                    'span': (block.start_pos, block.end_pos)
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
        """Extract introduction paragraphs (content before first major structural element)."""
        introduction_paragraphs = []
        found_title = False
        
        for block in blocks:
            # Skip until we find the title
            if not found_title:
                if block.block_type == AsciiDocBlockType.HEADING and block.level == 1:
                    found_title = True
                continue
            
            # Stop at first major structural element after title
            if block.block_type in [
                AsciiDocBlockType.HEADING,        # Another heading
                AsciiDocBlockType.ORDERED_LIST,   # Ordered list
                AsciiDocBlockType.UNORDERED_LIST, # Unordered list  
                AsciiDocBlockType.TABLE,          # Table
                AsciiDocBlockType.LISTING,        # Code block
                AsciiDocBlockType.LITERAL         # Literal block
            ]:
                break
            
            # Collect paragraph content
            if (block.block_type == AsciiDocBlockType.PARAGRAPH and 
                block.content and block.content.strip()):
                introduction_paragraphs.append(block.content.strip())
        
        return introduction_paragraphs
    
    def _create_empty_structure(self) -> Dict[str, Any]:
        """Create empty structure for empty content or parsing failures."""
        return {
            'title': None,
            'introduction_paragraphs': [],
            'sections': [],
            'ordered_lists': [],
            'unordered_lists': [],
            'tables': [],
            'code_blocks': [],
            'images': [],
            'line_count': 0,
            'word_count': 0,
            'has_content': False
        }

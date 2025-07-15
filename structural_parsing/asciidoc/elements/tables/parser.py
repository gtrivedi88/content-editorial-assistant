"""
AsciiDoc Table Parser

Handles parsing of AsciiDoc table structures:
- Table blocks with headers and body rows
- Table cells and their content
- Table formatting and layout
- Column specifications and alignment
"""

from typing import Dict, Any, List
import logging

from ..base.element_parser import ElementParser, ElementParseResult

logger = logging.getLogger(__name__)

class TableParser(ElementParser):
    """Parser for AsciiDoc table structures."""
    
    @property
    def element_type(self) -> str:
        return "table"
    
    @property
    def supported_contexts(self) -> List[str]:
        return ["table", "table_row", "table_cell"]
    
    def can_parse(self, block_data: Dict[str, Any]) -> bool:
        """Check if this block is table-related."""
        context = block_data.get('context', '')
        return context in ['table', 'table_row', 'table_cell']
    
    def parse_element(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """
        Parse table element data.
        
        Args:
            block_data: Raw block data from Ruby parser
            
        Returns:
            ElementParseResult with table-specific data
        """
        try:
            context = block_data.get('context', 'table')
            
            if context == 'table':
                return self._parse_table_block(block_data)
            elif context == 'table_row':
                return self._parse_table_row(block_data)
            elif context == 'table_cell':
                return self._parse_table_cell(block_data)
            else:
                return ElementParseResult(
                    success=False,
                    errors=[f"Unknown table context: {context}"]
                )
                
        except Exception as e:
            logger.error(f"Error parsing table element: {e}")
            return ElementParseResult(
                success=False,
                errors=[f"Table parsing failed: {str(e)}"]
            )
    
    def _parse_table_block(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """Parse main table block."""
        content = block_data.get('content', '')
        children = block_data.get('children', [])
        attributes = block_data.get('attributes', {})
        
        # Analyze table structure
        table_stats = self._analyze_table_structure(children)
        
        # Extract table properties
        table_props = self._extract_table_properties(attributes)
        
        element_data = {
            'content': content,
            'context': 'table',
            'structure': table_stats,
            'properties': table_props,
            'has_title': bool(block_data.get('title')),
            'title': block_data.get('title', ''),
            'raw_markup': self._reconstruct_table_markup(content, block_data.get('title', ''))
        }
        
        validation_errors = self.validate_element(element_data)
        
        return ElementParseResult(
            success=True,
            element_data=element_data,
            errors=validation_errors
        )
    
    def _parse_table_row(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """Parse table row."""
        children = block_data.get('children', [])
        attributes = block_data.get('attributes', {})
        
        # Determine row type
        row_type = attributes.get('role', attributes.get('style', 'body'))
        is_header = row_type == 'header'
        
        element_data = {
            'context': 'table_row',
            'row_type': row_type,
            'is_header': is_header,
            'cell_count': len(children),
            'row_index': attributes.get('row', 0)
        }
        
        return ElementParseResult(
            success=True,
            element_data=element_data,
            errors=[]
        )
    
    def _parse_table_cell(self, block_data: Dict[str, Any]) -> ElementParseResult:
        """Parse table cell."""
        content = block_data.get('content', '').strip()
        attributes = block_data.get('attributes', {})
        
        element_data = {
            'content': content,
            'context': 'table_cell',
            'column_index': attributes.get('column', 0),
            'row_index': attributes.get('row', 0),
            'is_header': attributes.get('role') == 'header',
            'length': len(content),
            'word_count': len(content.split()) if content else 0
        }
        
        validation_errors = self._validate_table_cell(element_data)
        
        return ElementParseResult(
            success=True,
            element_data=element_data,
            errors=validation_errors
        )
    
    def get_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display information for UI rendering."""
        context = element_data.get('context', 'table')
        
        if context == 'table':
            return self._get_table_display_info(element_data)
        elif context == 'table_row':
            return self._get_row_display_info(element_data)
        elif context == 'table_cell':
            return self._get_cell_display_info(element_data)
        else:
            return {'icon': 'fas fa-table', 'title': 'Table Element'}
    
    def _get_table_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display info for table block."""
        structure = element_data.get('structure', {})
        title = element_data.get('title', '')
        
        row_count = structure.get('total_rows', 0)
        col_count = structure.get('column_count', 0)
        
        display_title = f"Table ({row_count}×{col_count})"
        if title:
            display_title = f"Table: {title}"
        
        return {
            'icon': 'fas fa-table',
            'title': display_title,
            'content_preview': f"{row_count} rows, {col_count} columns",
            'skip_analysis': False,  # Tables should be analyzed
            'table_size': f"{row_count}×{col_count}",
            'has_header': structure.get('has_header', False),
            'complexity': self._estimate_table_complexity(structure)
        }
    
    def _get_row_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display info for table row."""
        row_type = element_data.get('row_type', 'body')
        cell_count = element_data.get('cell_count', 0)
        
        return {
            'icon': 'fas fa-grip-lines-vertical',
            'title': f"Table Row ({row_type.title()})",
            'content_preview': f"{cell_count} cells",
            'skip_analysis': True,  # Individual rows don't need analysis
            'row_type': row_type,
            'cell_count': cell_count
        }
    
    def _get_cell_display_info(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get display info for table cell."""
        content = element_data.get('content', '')
        is_header = element_data.get('is_header', False)
        
        cell_type = 'Header Cell' if is_header else 'Data Cell'
        
        return {
            'icon': 'fas fa-square',
            'title': cell_type,
            'content_preview': content[:30] + '...' if len(content) > 30 else content,
            'skip_analysis': True,  # Individual cells analyzed as part of table
            'is_header': is_header,
            'has_content': bool(content.strip())
        }
    
    def validate_element(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate table element data."""
        context = element_data.get('context', 'table')
        
        if context == 'table':
            return self._validate_table_block(element_data)
        elif context == 'table_cell':
            return self._validate_table_cell(element_data)
        else:
            return []  # Rows don't need specific validation
    
    def _validate_table_block(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate main table block."""
        errors = []
        structure = element_data.get('structure', {})
        
        row_count = structure.get('total_rows', 0)
        col_count = structure.get('column_count', 0)
        
        # Check table size
        if row_count == 0:
            errors.append("Table has no rows")
        elif row_count > 100:
            errors.append("Table is very large (>100 rows) - consider splitting")
        
        if col_count == 0:
            errors.append("Table has no columns")
        elif col_count > 20:
            errors.append("Table has many columns (>20) - consider restructuring")
        
        # Check if table is too small to be useful
        if row_count == 1 and not structure.get('has_header', False):
            errors.append("Single-row table without header may not be necessary")
        
        return errors
    
    def _validate_table_cell(self, element_data: Dict[str, Any]) -> List[str]:
        """Validate table cell."""
        errors = []
        content = element_data.get('content', '')
        word_count = element_data.get('word_count', 0)
        
        # Check for very long cell content
        if word_count > 50:
            errors.append("Table cell content is very long - consider restructuring")
        
        # Check for empty cells (warning, not error)
        if not content.strip():
            errors.append("Table cell is empty")
        
        return errors
    
    def _analyze_table_structure(self, children: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze table structure from children."""
        if not children:
            return {
                'total_rows': 0,
                'header_rows': 0,
                'body_rows': 0,
                'column_count': 0,
                'has_header': False
            }
        
        header_rows = 0
        body_rows = 0
        max_columns = 0
        
        for child in children:
            if child.get('context') == 'table_row':
                child_children = child.get('children', [])
                cell_count = len([c for c in child_children if c.get('context') == 'table_cell'])
                max_columns = max(max_columns, cell_count)
                
                # Check if this is a header row
                row_attrs = child.get('attributes', {})
                if row_attrs.get('role') == 'header' or row_attrs.get('style') == 'header':
                    header_rows += 1
                else:
                    body_rows += 1
        
        return {
            'total_rows': header_rows + body_rows,
            'header_rows': header_rows,
            'body_rows': body_rows,
            'column_count': max_columns,
            'has_header': header_rows > 0
        }
    
    def _extract_table_properties(self, attributes: Dict[str, Any]) -> Dict[str, Any]:
        """Extract table formatting properties."""
        return {
            'format': attributes.get('format', 'psv'),  # pipe-separated values
            'frame': attributes.get('frame', 'all'),
            'grid': attributes.get('grid', 'all'),
            'stripes': attributes.get('stripes', 'none'),
            'width': attributes.get('width', '100%')
        }
    
    def _estimate_table_complexity(self, structure: Dict[str, Any]) -> str:
        """Estimate table complexity."""
        row_count = structure.get('total_rows', 0)
        col_count = structure.get('column_count', 0)
        total_cells = row_count * col_count
        
        if total_cells <= 20:
            return 'simple'
        elif total_cells <= 100:
            return 'moderate'
        elif total_cells <= 500:
            return 'complex'
        else:
            return 'very_complex'
    
    def _reconstruct_table_markup(self, content: str, title: str = '') -> str:
        """Reconstruct AsciiDoc table markup."""
        markup_lines = []
        
        if title:
            markup_lines.append(f".{title}")
        
        markup_lines.append("|===")
        if content:
            markup_lines.append(content)
        markup_lines.append("|===")
        
        return '\n'.join(markup_lines) 
"""
Simplified AsciiDoc structural parser using native Asciidoctor AST.
This version is a drop-in replacement, ensuring full compatibility with the existing system.
"""
import logging
from typing import Dict, Any, Optional
from .ruby_client import get_client
from .types import (
    AsciiDocBlock, AsciiDocDocument, ParseResult, AsciiDocBlockType,
    AdmonitionType, AsciiDocAttributes
)

logger = logging.getLogger(__name__)

class AsciiDocParser:
    def __init__(self):
        self.ruby_client = get_client()
        self.asciidoctor_available = self.ruby_client.ping()

    def parse(self, content: str, filename: str = "") -> ParseResult:
        if not self.asciidoctor_available:
            return ParseResult(success=False, errors=["Asciidoctor Ruby gem is not available."])

        # Correctly calls the 'run' method in the updated client
        result = self.ruby_client.run(content, filename)

        if not result.get('success'):
            return ParseResult(success=False, errors=[result.get('error', 'Unknown Ruby error')])

        json_ast = result.get('data', {})
        if not json_ast:
            return ParseResult(success=False, errors=["Parser returned empty document."])

        try:
            document_node = self._build_block_from_ast(json_ast, filename=filename)
            if isinstance(document_node, AsciiDocDocument):
                return ParseResult(document=document_node, success=True)
            return ParseResult(success=False, errors=["AST root was not a document."])
        except Exception as e:
            logger.exception("Failed to build block structure from AsciiDoc AST.")
            return ParseResult(success=False, errors=[f"Failed to process AST: {e}"])

    def _build_block_from_ast(self, node: Dict[str, Any], parent: Optional[AsciiDocBlock] = None, filename: str = "") -> AsciiDocBlock:
        context = node.get('context', 'unknown')
        block_type = self._map_context_to_block_type(context)
        raw_content = node.get('source', '') or ''
        start_line = node.get('lineno', 0)
        content = self._get_content_from_node(node)

        block = AsciiDocBlock(
            block_type=block_type,
            content=content,
            raw_content=raw_content,
            title=node.get('title'),
            level=node.get('level', 0),
            start_line=start_line,
            end_line=start_line + raw_content.count('\n'),
            start_pos=0,
            end_pos=len(raw_content),
            style=node.get('style'),
            list_marker=node.get('marker'),
            source_location=filename,
            attributes=self._create_attributes(node.get('attributes', {})),
            parent=parent
        )

        if block_type == AsciiDocBlockType.ADMONITION:
            style = node.get('style', 'NOTE').upper()
            block.admonition_type = AdmonitionType[style] if style in AdmonitionType.__members__ else AdmonitionType.NOTE

        block.children = [self._build_block_from_ast(child, parent=block, filename=filename) for child in node.get('children', [])]

        if context == 'document':
            return AsciiDocDocument(
                blocks=block.children,
                source_file=filename,
                block_type=AsciiDocBlockType.DOCUMENT,
                content=node.get('title', ''),
                raw_content=node.get('source', ''),
                start_line=0,
                title=node.get('title', ''),  # CRITICAL FIX: Set the document title properly
                attributes=self._create_attributes(node.get('attributes', {}))
            )
        return block

    def _create_attributes(self, attrs: Dict[str, Any]) -> AsciiDocAttributes:
        """Creates the AsciiDocAttributes object for compatibility."""
        attributes = AsciiDocAttributes()
        attributes.id = attrs.get('id')
        for key, value in attrs.items():
            if isinstance(value, (str, int, float, bool)):
                attributes.named_attributes[key] = str(value)
        return attributes

    def _get_content_from_node(self, node: Dict[str, Any]) -> str:
        """Determines the correct content field from the AST node for analysis."""
        context = node.get('context')
        if context == 'list_item': return node.get('text', '')
        if context == 'section': return node.get('title', '')
        if context in ['listing', 'literal']: return node.get('source', '')
        
        # For table cells, use the 'text' field since 'content' is a list
        if context == 'table_cell': return node.get('text', '') or node.get('source', '')
        
        # For lists, extract content from list items
        if context in ['ulist', 'olist'] and node.get('children'):
            list_items = []
            for child in node.get('children', []):
                if child.get('context') == 'list_item':
                    item_text = child.get('text', '') or child.get('content', '')
                    if item_text:
                        list_items.append(item_text.strip())
            return '\n'.join(list_items) if list_items else ''
        
        # For compound blocks like admonitions, the content is the combined source of its children
        if node.get('children') and context not in ['table']:
            return "\n".join(child.get('source', '') for child in node.get('children', []))
        return node.get('content', '') or ''


    def _map_context_to_block_type(self, context: str) -> AsciiDocBlockType:
        """Maps the Asciidoctor context string to our enum."""
        if context == 'section': return AsciiDocBlockType.HEADING
        try:
            return AsciiDocBlockType(context)
        except ValueError:
            return AsciiDocBlockType.UNKNOWN
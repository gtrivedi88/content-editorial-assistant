"""HTML parser using lxml for DOM tree-based extraction.

Walks the parsed DOM to produce Block structures, skipping script/style
elements and mapping common HTML tags to semantic block types.
"""

import logging
from typing import Optional

from lxml import html as lxml_html
from lxml.html import HtmlElement

from app.services.parsing.base import (
    BaseParser, Block, ParseResult, build_xml_char_map,
)

logger = logging.getLogger(__name__)

# Elements whose subtree should be completely ignored
_SKIP_TAGS = frozenset({"script", "style", "noscript", "svg", "math"})

# Tag -> block_type mapping
_TAG_MAP: dict[str, str] = {
    "h1": "heading",
    "h2": "heading",
    "h3": "heading",
    "h4": "heading",
    "h5": "heading",
    "h6": "heading",
    "p": "paragraph",
    "pre": "code_block",
    "code": "code_block",
    "ul": "list",
    "ol": "list",
    "li": "list_item",
    "table": "table",
    "tr": "table_row",
    "td": "table_cell",
    "th": "table_cell",
    "blockquote": "blockquote",
    "img": "image",
    "figure": "image",
    "section": "section",
    "article": "section",
    "aside": "sidebar",
    "div": "paragraph",
}


class HtmlParser(BaseParser):
    """Parser for HTML documents using lxml.

    Skips ``<script>``, ``<style>``, and ``<noscript>`` elements. Maps
    structural HTML tags to semantic block types for downstream analysis.
    """

    def parse(self, content: str, filename: Optional[str] = None) -> ParseResult:
        """Parse an HTML document into blocks.

        Args:
            content: Raw HTML string.
            filename: Optional filename for logging.

        Returns:
            ParseResult with blocks and metadata.
        """
        logger.debug("HtmlParser: parsing %d chars", len(content) if content else 0)

        if not content or not content.strip():
            return ParseResult(blocks=[], plain_text="")

        try:
            doc = lxml_html.fromstring(content)
        except lxml_html.etree.ParserError:
            logger.warning("HtmlParser: lxml failed to parse content")
            return ParseResult(blocks=[], plain_text="")

        blocks: list[Block] = []
        self._walk(doc, blocks, offset=0)

        plain_text = "\n\n".join(
            b.content for b in blocks if not b.should_skip_analysis and b.content
        )

        logger.debug("HtmlParser: produced %d blocks", len(blocks))
        return ParseResult(
            blocks=blocks,
            plain_text=plain_text,
        )

    # ------------------------------------------------------------------
    # Recursive DOM walker
    # ------------------------------------------------------------------

    def _walk(
        self,
        element: HtmlElement,
        blocks: list[Block],
        offset: int,
    ) -> int:
        """Recursively walk *element* and append blocks.

        Args:
            element: Current DOM node.
            blocks: Accumulator for discovered blocks.
            offset: Running character offset for position tracking.

        Returns:
            Updated character offset after processing this element.
        """
        tag = _local_tag(element)

        if tag in _SKIP_TAGS:
            return offset

        block_type = _TAG_MAP.get(tag)

        if block_type is not None:
            block = self._element_to_block(element, tag, block_type, offset)
            if block is not None:
                blocks.append(block)
                offset = block.end_pos
            return offset

        # Container element without a direct mapping -- recurse into children
        for child in element:
            offset = self._walk(child, blocks, offset)

        return offset

    def _element_to_block(
        self,
        element: HtmlElement,
        tag: str,
        block_type: str,
        offset: int,
    ) -> Optional[Block]:
        """Create a Block from a single HTML element.

        Args:
            element: The HTML element node.
            tag: Normalised lower-case tag name.
            block_type: Mapped block type string.
            offset: Current character offset.

        Returns:
            A Block or None if the element has no useful content.
        """
        text_content = _text_of(element).strip()
        raw_content = _outer_html(element)

        if not text_content and block_type != "image":
            return None

        level = _heading_level(tag)
        skip = block_type == "code_block"
        start_pos = offset
        end_pos = offset + len(raw_content)

        metadata: dict = {}
        if block_type == "image":
            src = element.get("src", "")
            alt = element.get("alt", "")
            metadata["src"] = src
            metadata["alt"] = alt
            text_content = alt or src

        children: list[Block] = []
        if block_type in ("list", "table"):
            children = self._extract_children(element, start_pos)

        # SK-4: build char_map for non-code blocks
        char_map: list[int] | None = None
        if not skip and text_content:
            char_map = build_xml_char_map(raw_content, text_content)

        return Block(
            block_type=block_type,
            content=text_content,
            raw_content=raw_content,
            start_pos=start_pos,
            end_pos=end_pos,
            level=level,
            children=children,
            should_skip_analysis=skip,
            metadata=metadata,
            char_map=char_map,
        )

    def _extract_children(
        self, element: HtmlElement, parent_offset: int
    ) -> list[Block]:
        """Extract child blocks from list or table containers."""
        children: list[Block] = []
        offset = parent_offset
        for child in element:
            tag = _local_tag(child)
            child_type = _TAG_MAP.get(tag)
            if child_type is None:
                continue
            block = self._element_to_block(child, tag, child_type, offset)
            if block is not None:
                children.append(block)
                offset = block.end_pos
        return children


# ------------------------------------------------------------------
# Pure helper functions
# ------------------------------------------------------------------


def _local_tag(element: HtmlElement) -> str:
    """Return the lower-case local tag name of *element*."""
    tag = element.tag if isinstance(element.tag, str) else ""
    return tag.split("}")[-1].lower() if "}" in tag else tag.lower()


def _text_of(element: HtmlElement) -> str:
    """Extract concatenated text content from *element* and descendants."""
    return element.text_content() or ""


def _outer_html(element: HtmlElement) -> str:
    """Serialise *element* back to an HTML string."""
    try:
        return lxml_html.tostring(element, encoding="unicode")
    except (TypeError, lxml_html.etree.SerialisationError):
        return ""


def _heading_level(tag: str) -> int:
    """Return 1-6 for heading tags, 0 otherwise."""
    if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
        return int(tag[1])
    return 0



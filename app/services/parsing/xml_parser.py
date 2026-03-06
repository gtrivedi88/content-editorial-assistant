"""Generic XML parser using lxml.etree.

Extracts text content from XML elements while handling namespaces,
processing instructions, comments, and CDATA sections gracefully.
"""

import logging
from typing import Optional

from lxml import etree

from app.services.parsing.base import (
    BaseParser, Block, ParseResult, build_xml_char_map,
)

logger = logging.getLogger(__name__)

# XXE-safe XML parser — disables external entity resolution and network
# access to prevent SSRF and local file read attacks from malicious uploads.
_SAFE_XML_PARSER = etree.XMLParser(resolve_entities=False, no_network=True)


class XmlParser(BaseParser):
    """Parser for generic XML documents.

    Walks the element tree, skips processing instructions and comments,
    handles CDATA sections, and maps elements to paragraph or section
    blocks based on whether they contain text or only children.
    """

    def parse(self, content: str, filename: Optional[str] = None) -> ParseResult:
        """Parse XML content into blocks.

        Args:
            content: Raw XML string.
            filename: Optional filename for logging.

        Returns:
            ParseResult with blocks and metadata.
        """
        logger.debug("XmlParser: parsing %d chars", len(content) if content else 0)

        if not content or not content.strip():
            return ParseResult(blocks=[], plain_text="")

        try:
            root = etree.fromstring(content.encode("utf-8"), parser=_SAFE_XML_PARSER)
        except etree.XMLSyntaxError as exc:
            logger.warning("XmlParser: XML syntax error: %s", exc)
            return ParseResult(
                blocks=[],
                plain_text="",
                metadata={"error": str(exc)},
            )

        blocks: list[Block] = []
        self._walk(root, blocks, offset=0)

        plain_text = "\n\n".join(
            b.content for b in blocks if not b.should_skip_analysis and b.content
        )

        logger.debug("XmlParser: produced %d blocks", len(blocks))
        return ParseResult(
            blocks=blocks,
            plain_text=plain_text,
        )

    # ------------------------------------------------------------------
    # Recursive element walker
    # ------------------------------------------------------------------

    def _walk(
        self,
        element: etree._Element,
        blocks: list[Block],
        offset: int,
        depth: int = 0,
    ) -> int:
        """Recursively walk the element tree and emit blocks.

        Args:
            element: Current XML element.
            blocks: Accumulator for discovered blocks.
            offset: Running character offset.
            depth: Nesting depth for level tracking.

        Returns:
            Updated character offset.
        """
        # Skip processing instructions and comments
        if not isinstance(element.tag, str):
            return offset

        text_content = _element_text(element)
        raw_content = _serialise(element)
        tag = _local_name(element.tag)

        has_children = len(element) > 0
        has_text = bool(text_content.strip())

        if has_text and not has_children:
            # Leaf element with text -> paragraph
            start = offset
            end = offset + len(raw_content)
            clean = text_content.strip()
            char_map = build_xml_char_map(raw_content, clean)
            blocks.append(Block(
                block_type="paragraph",
                content=clean,
                raw_content=raw_content,
                start_pos=start,
                end_pos=end,
                level=depth,
                metadata={"tag": tag},
                char_map=char_map,
            ))
            return end

        if has_children:
            # Container element -> section wrapper, then recurse
            start = offset
            end = offset + len(raw_content)
            children: list[Block] = []
            child_offset = start

            for child in element:
                child_offset = self._walk(child, children, child_offset, depth + 1)

            clean = text_content.strip()
            char_map = build_xml_char_map(raw_content, clean) if clean else None

            # Only emit a section block if children were produced
            if children:
                blocks.append(Block(
                    block_type="section",
                    content=clean,
                    raw_content=raw_content,
                    start_pos=start,
                    end_pos=end,
                    level=depth,
                    children=children,
                    metadata={"tag": tag},
                    char_map=char_map,
                ))
            elif has_text:
                blocks.append(Block(
                    block_type="paragraph",
                    content=clean,
                    raw_content=raw_content,
                    start_pos=start,
                    end_pos=end,
                    level=depth,
                    metadata={"tag": tag},
                    char_map=char_map,
                ))
            return end

        # Element with no text and no children -- skip
        return offset + len(raw_content)


# ------------------------------------------------------------------
# Pure helper functions
# ------------------------------------------------------------------


def _local_name(tag: str) -> str:
    """Strip any namespace URI prefix from *tag*."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _element_text(element: etree._Element) -> str:
    """Recursively extract text content from *element*."""
    parts: list[str] = []
    if element.text:
        parts.append(element.text)
    for child in element:
        if isinstance(child.tag, str):
            parts.append(_element_text(child))
        if child.tail:
            parts.append(child.tail)
    return "".join(parts)


def _serialise(element: etree._Element) -> str:
    """Serialise *element* to a unicode XML string."""
    try:
        return etree.tostring(element, encoding="unicode")
    except etree.SerialisationError:
        return ""



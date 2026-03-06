"""DITA XML parser using lxml.etree.

Handles concept, task, reference, and troubleshooting topic types.
Detects conref/keyref cross-file references and emits placeholder
blocks with warnings when they cannot be resolved locally.
"""

import logging
import re
from typing import Optional

from lxml import etree

from app.services.parsing.base import (
    BaseParser, Block, ParseResult, build_xml_char_map,
)

logger = logging.getLogger(__name__)

# XXE-safe XML parser — disables external entity resolution and network
# access to prevent SSRF and local file read attacks from malicious uploads.
_SAFE_XML_PARSER = etree.XMLParser(resolve_entities=False, no_network=True)

# Root element -> topic type label
_TOPIC_TYPES: dict[str, str] = {
    "concept": "concept",
    "task": "task",
    "reference": "reference",
    "troubleshooting": "troubleshooting",
    "topic": "topic",
}

# DITA element -> block_type mapping
_ELEMENT_MAP: dict[str, str] = {
    "title": "heading",
    "shortdesc": "paragraph",
    "p": "paragraph",
    "section": "section",
    "example": "example",
    "codeblock": "code_block",
    "note": "admonition",
    "ul": "list",
    "ol": "list",
    "li": "list_item",
    "sli": "list_item",
    "sl": "list",
    "dl": "dlist",
    "dlentry": "list_item",
    "dt": "paragraph",
    "dd": "paragraph",
    "simpletable": "table",
    "table": "table",
    "sthead": "table_row",
    "strow": "table_row",
    "stentry": "table_cell",
    "row": "table_row",
    "entry": "table_cell",
    "step": "list_item_ordered",
    "cmd": "paragraph",
    "info": "paragraph",
    "stepresult": "paragraph",
    "substep": "list_item_ordered",
    "substeps": "list",
    "prereq": "section",
    "context": "section",
    "steps": "list",
    "result": "section",
    "postreq": "section",
    "conbody": "section",
    "taskbody": "section",
    "refbody": "section",
    "troublebody": "section",
    "body": "section",
    "image": "image",
    "fig": "image",
}

# Elements whose subtrees are metadata and should be skipped entirely
_SKIP_ELEMENTS = frozenset({
    "prolog", "metadata", "critdates", "permissions", "author",
    "source", "publisher", "audience", "category", "keywords",
    "prodinfo", "related-links", "linkpool", "link", "copyright",
    "titlealts", "navtitle", "searchtitle",
})


class DitaParser(BaseParser):
    """Parser for DITA XML documents.

    Supports concept, task, reference, and troubleshooting topic types.
    Unresolved conref/keyref attributes produce placeholder comment blocks
    with warnings attached to the parse result metadata.
    """

    def parse(self, content: str, filename: Optional[str] = None) -> ParseResult:
        """Parse DITA XML content into blocks.

        Args:
            content: Raw DITA XML string.
            filename: Optional filename for logging / metadata.

        Returns:
            ParseResult with typed blocks, metadata, and any warnings.
        """
        logger.debug("DitaParser: parsing %d chars", len(content) if content else 0)

        if not content or not content.strip():
            return ParseResult(blocks=[], plain_text="")

        try:
            root = etree.fromstring(content.encode("utf-8"), parser=_SAFE_XML_PARSER)
        except etree.XMLSyntaxError as exc:
            logger.warning("DitaParser: XML syntax error: %s", exc)
            return ParseResult(
                blocks=[],
                plain_text="",
                metadata={"error": str(exc)},
            )

        topic_type = _detect_topic_type(root)
        metadata: dict = {"topic_type": topic_type}
        unresolved: list[str] = []

        blocks: list[Block] = []
        self._walk(root, blocks, unresolved, offset=0)

        if unresolved:
            metadata["unresolved_refs"] = unresolved
            metadata["warning"] = (
                f"{len(unresolved)} cross-file reference(s) could not be resolved."
            )
            logger.info(
                "DitaParser: %d unresolved conref/keyref references in %s",
                len(unresolved),
                filename or "<unknown>",
            )

        plain_text = "\n\n".join(
            b.content for b in blocks if not b.should_skip_analysis and b.content
        )

        logger.debug("DitaParser: produced %d blocks", len(blocks))
        return ParseResult(
            blocks=blocks,
            metadata=metadata,
            plain_text=plain_text,
        )

    # ------------------------------------------------------------------
    # Recursive element walker
    # ------------------------------------------------------------------

    def _walk(
        self,
        element: etree._Element,
        blocks: list[Block],
        unresolved: list[str],
        offset: int,
        depth: int = 0,
    ) -> int:
        """Recursively walk the DITA element tree and emit blocks.

        Args:
            element: Current XML element.
            blocks: Accumulator for discovered blocks.
            unresolved: Accumulator for unresolved cross-file references.
            offset: Running character offset for position tracking.
            depth: Nesting depth.

        Returns:
            Updated character offset.
        """
        if not isinstance(element.tag, str):
            return offset

        tag = _local_name(element.tag)

        if tag in _SKIP_ELEMENTS:
            return offset

        # Conref / keyref detection
        conref = element.get("conref")
        keyref = element.get("keyref")
        if conref or keyref:
            return self._handle_cross_ref(
                element, tag, conref, keyref, blocks, unresolved, offset
            )

        block_type = _ELEMENT_MAP.get(tag)

        if block_type is not None:
            return self._emit_block(
                element, tag, block_type, blocks, unresolved, offset, depth
            )

        # Unknown container -- just recurse
        for child in element:
            offset = self._walk(child, blocks, unresolved, offset, depth + 1)
        return offset

    def _emit_block(
        self,
        element: etree._Element,
        tag: str,
        block_type: str,
        blocks: list[Block],
        unresolved: list[str],
        offset: int,
        depth: int,
    ) -> int:
        """Create a Block from a DITA element and recurse into children.

        Returns:
            Updated character offset.
        """
        text_content = _element_text(element).strip()
        raw_content = _serialise(element)
        start = offset
        end = offset + max(len(raw_content), 1)

        skip = block_type == "code_block"
        level = depth if block_type != "heading" else max(depth, 1)

        children: list[Block] = []
        child_offset = start
        for child in element:
            child_offset = self._walk(child, children, unresolved, child_offset, depth + 1)

        metadata: dict = {"tag": tag}
        if element.get("type"):
            metadata["note_type"] = element.get("type")

        # SK-4: build char_map for non-code blocks
        char_map: list[int] | None = None
        if not skip and text_content:
            char_map = build_xml_char_map(raw_content, text_content)

        blocks.append(Block(
            block_type=block_type,
            content=text_content,
            raw_content=raw_content,
            start_pos=start,
            end_pos=end,
            level=level,
            children=children,
            should_skip_analysis=skip,
            metadata=metadata,
            char_map=char_map,
        ))
        return end

    @staticmethod
    def _handle_cross_ref(
        element: etree._Element,
        tag: str,
        conref: Optional[str],
        keyref: Optional[str],
        blocks: list[Block],
        unresolved: list[str],
        offset: int,
    ) -> int:
        """Emit a placeholder comment block for an unresolved reference.

        Returns:
            Updated character offset.
        """
        ref_value = conref or keyref or ""
        ref_type = "conref" if conref else "keyref"
        placeholder = f'[Unresolved reference: {ref_type}="{ref_value}"]'
        unresolved.append(f"{ref_type}={ref_value}")

        raw_content = _serialise(element)
        end = offset + max(len(raw_content), 1)

        blocks.append(Block(
            block_type="comment",
            content=placeholder,
            raw_content=raw_content,
            start_pos=offset,
            end_pos=end,
            should_skip_analysis=True,
            metadata={"ref_type": ref_type, "ref_value": ref_value, "tag": tag},
        ))
        return end


# ------------------------------------------------------------------
# Pure helper functions
# ------------------------------------------------------------------


def _detect_topic_type(root: etree._Element) -> str:
    """Return the DITA topic type based on the root element tag."""
    if not isinstance(root.tag, str):
        return "unknown"
    tag = _local_name(root.tag)
    return _TOPIC_TYPES.get(tag, "unknown")


def _local_name(tag: str) -> str:
    """Strip namespace URI prefix from *tag*."""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


def _element_text(element: etree._Element) -> str:
    """Recursively extract text from *element* and its descendants."""
    parts: list[str] = []
    if element.text:
        parts.append(element.text)
    for child in element:
        if isinstance(child.tag, str):
            parts.append(_element_text(child))
        if child.tail:
            parts.append(child.tail)
    text = "".join(parts)
    return re.sub(r"\s+", " ", text)


def _serialise(element: etree._Element) -> str:
    """Serialise *element* to a unicode XML string."""
    try:
        return etree.tostring(element, encoding="unicode")
    except etree.SerialisationError:
        return ""



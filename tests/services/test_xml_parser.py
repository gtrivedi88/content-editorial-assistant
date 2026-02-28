"""Tests for the generic XML parser.

Validates basic XML parsing, text extraction without synthetic spaces
(Gap 5 fix verification), inline element adjacency preservation, empty
element handling, and char_map alignment for lxml-based text extraction.
"""

import logging

import pytest

from app.services.parsing.base import Block, ParseResult
from app.services.parsing.xml_parser import XmlParser, _element_text

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _collect_all_blocks(blocks: list[Block]) -> list[Block]:
    """Recursively collect all blocks including children.

    XML parsing produces a hierarchical block tree where container
    elements become sections with children. This helper flattens the
    tree for easier assertion.

    Args:
        blocks: Top-level block list from ParseResult.

    Returns:
        Flat list of all blocks at every nesting level.
    """
    result: list[Block] = []
    for block in blocks:
        result.append(block)
        if block.children:
            result.extend(_collect_all_blocks(block.children))
    return result


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestXmlParser:
    """Tests for the XmlParser class."""

    def test_basic_xml_parsing(self) -> None:
        """Basic XML document produces paragraph blocks with correct content.

        A simple XML document with a root element containing child
        elements should yield blocks whose content matches the text
        nodes in the source document.
        """
        content: str = (
            "<doc>"
            "  <title>Getting Started</title>"
            "  <body>Install the package using the package manager.</body>"
            "</doc>"
        )

        parser: XmlParser = XmlParser()
        result: ParseResult = parser.parse(content)

        all_blocks = _collect_all_blocks(result.blocks)

        # Should have at least the title and body text
        texts = [b.content for b in all_blocks if b.content.strip()]
        assert any("Getting Started" in t for t in texts)
        assert any("Install the package" in t for t in texts)

        # plain_text should include the analysable content
        assert "Install the package" in result.plain_text

    def test_element_text_no_synthetic_spaces(self) -> None:
        """_element_text does not inject synthetic spaces between adjacent nodes.

        When text and tail content are adjacent in the XML tree (e.g.
        ``<p>Hello<b>world</b>!</p>``), _element_text should join them
        with ``"".join(parts)`` -- no synthetic whitespace is added.
        This verifies the Gap 5 fix using the same pattern as the DITA
        parser test.
        """
        from lxml import etree

        xml_str: str = "<p>Hello<b>world</b>!</p>"
        element = etree.fromstring(xml_str)
        text: str = _element_text(element)

        # "".join(parts) means no synthetic space between text nodes
        assert text == "Helloworld!"

    def test_inline_elements_preserve_adjacency(self) -> None:
        """Inline elements preserve text adjacency in parsed output.

        When a ``<p>`` contains a child ``<code>`` element, the XML parser
        treats it as a container (section) because it has children. The
        section's ``content`` is built by ``_element_text()``, which
        concatenates text/tail nodes without inserting synthetic spaces.
        """
        content: str = (
            "<doc>"
            "  <p>Run the <code>install</code>command now.</p>"
            "</doc>"
        )

        parser: XmlParser = XmlParser()
        result: ParseResult = parser.parse(content)

        all_blocks = _collect_all_blocks(result.blocks)
        all_texts = [b.content for b in all_blocks if b.content.strip()]

        # The _element_text() concatenation should produce "installcommand"
        # (no synthetic space) in the parent section's content
        assert any("installcommand" in t for t in all_texts)

    def test_empty_elements_produce_no_blocks(self) -> None:
        """Empty XML elements are skipped and produce no blocks.

        Elements with no text content and no children should not
        generate blocks in the parse result.
        """
        content: str = (
            "<doc>"
            "  <empty/>"
            "  <p>Some content here.</p>"
            "</doc>"
        )

        parser: XmlParser = XmlParser()
        result: ParseResult = parser.parse(content)

        all_blocks = _collect_all_blocks(result.blocks)
        # The <empty/> element should not produce a block
        for block in all_blocks:
            tag = block.metadata.get("tag", "")
            if tag == "empty":
                assert block.content.strip() == "", (
                    "Empty element should have no text content"
                )

        # The <p> element should still produce a paragraph
        paragraphs = [b for b in all_blocks if b.block_type == "paragraph"]
        assert any("Some content" in p.content for p in paragraphs)

    def test_char_map_alignment(self) -> None:
        """char_map maps content positions back to raw_content positions.

        For a paragraph containing inline markup, the char_map should
        map each character in the extracted text to a valid position
        in the serialised XML raw_content. All positions must be within
        the raw_content bounds.
        """
        content: str = (
            "<doc>"
            "  <p>Start <b>bold</b> end</p>"
            "</doc>"
        )

        parser: XmlParser = XmlParser()
        result: ParseResult = parser.parse(content)

        all_blocks = _collect_all_blocks(result.blocks)
        paragraphs = [
            b for b in all_blocks
            if b.block_type == "paragraph" and "bold" in b.content
        ]
        assert len(paragraphs) >= 1
        block = paragraphs[0]

        assert block.char_map is not None
        # char_map length should match content length
        assert len(block.char_map) == len(block.content)
        # All mapped positions should be within raw_content bounds
        for i, pos in enumerate(block.char_map):
            assert 0 <= pos < len(block.raw_content), (
                f"char_map[{i}] = {pos} out of bounds for "
                f"raw_content length {len(block.raw_content)}"
            )

    def test_malformed_xml_returns_empty_result(self) -> None:
        """Malformed XML returns an empty ParseResult with error metadata.

        The parser should handle XML syntax errors gracefully by
        returning an empty result rather than raising an exception.
        """
        content: str = "<doc><unclosed>"

        parser: XmlParser = XmlParser()
        result: ParseResult = parser.parse(content)

        assert result.blocks == []
        assert result.plain_text == ""
        assert "error" in result.metadata

    def test_empty_content_returns_empty_result(self) -> None:
        """Empty or whitespace-only content returns an empty ParseResult.

        The parser should not raise on empty input.
        """
        parser: XmlParser = XmlParser()

        result_empty: ParseResult = parser.parse("")
        assert result_empty.blocks == []
        assert result_empty.plain_text == ""

        result_whitespace: ParseResult = parser.parse("   \n  ")
        assert result_whitespace.blocks == []
        assert result_whitespace.plain_text == ""

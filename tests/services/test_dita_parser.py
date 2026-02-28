"""Tests for the DITA XML parser.

Validates concept document parsing, text extraction without synthetic
spaces, codeblock skip behavior, inline element adjacency, empty element
handling, and char_map alignment with lxml-based text extraction.
"""

import logging

import pytest

from app.services.parsing.base import Block, ParseResult
from app.services.parsing.dita_parser import DitaParser, _element_text

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _collect_all_blocks(blocks: list[Block]) -> list[Block]:
    """Recursively collect all blocks including children.

    DITA parsing produces a hierarchical block tree (e.g. conbody becomes
    a section block whose children include paragraph and code_block).
    This helper flattens the tree for easier assertion.

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


class TestDitaParser:
    """Tests for the DitaParser class."""

    def test_basic_concept_parsing(self) -> None:
        """Basic DITA concept document produces heading and paragraph blocks.

        A minimal ``<concept>`` document with a ``<title>`` and ``<p>``
        should yield at least a heading block and a paragraph block with
        the correct text content. The ``<conbody>`` emits a section block
        whose children include the ``<p>`` paragraph.
        """
        content: str = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<concept id="test_concept">\n'
            '  <title>Test Concept Title</title>\n'
            '  <conbody>\n'
            '    <p>This is the concept body paragraph.</p>\n'
            '  </conbody>\n'
            '</concept>\n'
        )

        parser: DitaParser = DitaParser()
        result: ParseResult = parser.parse(content)

        all_blocks = _collect_all_blocks(result.blocks)

        headings = [b for b in all_blocks if b.block_type == "heading"]
        assert len(headings) >= 1
        assert headings[0].content == "Test Concept Title"

        paragraphs = [b for b in all_blocks if b.block_type == "paragraph"]
        para_texts = [p.content for p in paragraphs]
        assert any("concept body paragraph" in t for t in para_texts)

        # Metadata should identify the topic type
        assert result.metadata.get("topic_type") == "concept"

    def test_element_text_no_synthetic_spaces(self) -> None:
        """_element_text does not insert synthetic spaces between adjacent nodes.

        When text and tail content are adjacent in the XML tree (e.g.
        ``<p>Hello<b>world</b>!</p>``), _element_text should join them
        without inserting extra spaces. The 4D fix ensures no synthetic
        whitespace is added between text/tail nodes.
        """
        from lxml import etree

        xml_str: str = "<p>Hello<b>world</b>!</p>"
        element = etree.fromstring(xml_str)
        text: str = _element_text(element)

        # Should be "Helloworld!" -- no synthetic space between text nodes
        assert text == "Helloworld!"

    def test_codeblock_marked_as_code_skip_analysis(self) -> None:
        """<codeblock> elements are marked as code with should_skip_analysis.

        Code blocks in DITA should not be style-checked, so they must
        have block_type='code_block' and should_skip_analysis=True.
        The ``<codeblock>`` element is a child of ``<conbody>`` (section).
        """
        content: str = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<concept id="code_test">\n'
            '  <title>Code Example</title>\n'
            '  <conbody>\n'
            '    <codeblock>echo "hello world"</codeblock>\n'
            '  </conbody>\n'
            '</concept>\n'
        )

        parser: DitaParser = DitaParser()
        result: ParseResult = parser.parse(content)

        all_blocks = _collect_all_blocks(result.blocks)
        code_blocks = [b for b in all_blocks if b.block_type == "code_block"]
        assert len(code_blocks) >= 1
        assert code_blocks[0].should_skip_analysis is True
        assert "echo" in code_blocks[0].content

    def test_inline_elements_preserve_adjacency(self) -> None:
        """Inline elements preserve text adjacency in parsed output.

        ``<p>Hello<b>world</b>!</p>`` should produce a paragraph block
        whose content is ``Helloworld!`` -- the bold element's text is
        concatenated without synthetic whitespace. The ``<b>`` tag is not
        in ``_ELEMENT_MAP``, so its text is collected recursively by
        ``_element_text`` and folded into the parent ``<p>`` block.
        """
        content: str = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<concept id="inline_test">\n'
            '  <title>Inline Test</title>\n'
            '  <conbody>\n'
            '    <p>Hello<b>world</b>!</p>\n'
            '  </conbody>\n'
            '</concept>\n'
        )

        parser: DitaParser = DitaParser()
        result: ParseResult = parser.parse(content)

        all_blocks = _collect_all_blocks(result.blocks)
        paragraphs = [b for b in all_blocks if b.block_type == "paragraph"]
        para_texts = [p.content for p in paragraphs]
        # The concatenated text should not have synthetic spaces
        assert any("Helloworld!" in t for t in para_texts)

    def test_empty_elements_produce_no_text(self) -> None:
        """Empty DITA elements produce blocks with empty content.

        An element like ``<p></p>`` should result in a block whose
        content is empty. The ``<conbody>`` wraps it as a section
        whose child paragraph has no text.
        """
        content: str = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<concept id="empty_test">\n'
            '  <title>Empty Elements</title>\n'
            '  <conbody>\n'
            '    <p></p>\n'
            '  </conbody>\n'
            '</concept>\n'
        )

        parser: DitaParser = DitaParser()
        result: ParseResult = parser.parse(content)

        all_blocks = _collect_all_blocks(result.blocks)
        # Find the empty <p> block among all blocks (including children)
        empty_paragraphs = [
            b for b in all_blocks
            if b.block_type == "paragraph" and b.content.strip() == ""
        ]
        # The empty <p> should produce a block with no meaningful content
        assert len(empty_paragraphs) >= 1

    def test_char_map_alignment_with_inline_elements(self) -> None:
        """char_map aligns content positions to raw_content (serialised XML).

        For a paragraph containing inline markup like ``<b>bold</b>``,
        the char_map should map each character in the extracted text
        back to a valid position in the serialised XML raw_content.
        The paragraph block is a child of the ``<conbody>`` section.
        """
        content: str = (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<concept id="charmap_test">\n'
            '  <title>CharMap Test</title>\n'
            '  <conbody>\n'
            '    <p>Start <b>bold</b> end</p>\n'
            '  </conbody>\n'
            '</concept>\n'
        )

        parser: DitaParser = DitaParser()
        result: ParseResult = parser.parse(content)

        all_blocks = _collect_all_blocks(result.blocks)
        # Find the paragraph with inline bold among all blocks
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

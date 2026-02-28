"""Tests for the AsciiDoc regex-based parser.

Validates heading, list, code block, admonition, block attribute, and
list continuation parsing. Verifies inline marker stripping, char_map
construction, and start_pos/end_pos alignment with the original source.
"""

import logging

import pytest

from app.services.parsing.asciidoc_parser import AsciidocParser
from app.services.parsing.base import Block, ParseResult

logger = logging.getLogger(__name__)


class TestAsciidocParser:
    """Tests for the AsciidocParser regex fallback path."""

    def test_heading_parsing(self) -> None:
        """Level-1 heading ``= Title`` produces a heading block.

        The parser should extract the title text (without the ``=`` marker)
        and assign block_type='heading' with level=1.
        """
        content: str = "= My Document Title\n"

        parser: AsciidocParser = AsciidocParser()
        result: ParseResult = parser.parse(content)

        headings = [b for b in result.blocks if b.block_type == "heading"]
        assert len(headings) == 1
        assert headings[0].content == "My Document Title"
        assert headings[0].level == 1

    def test_unordered_list(self) -> None:
        """Unordered list item ``* Item`` produces list_item_unordered.

        The block content should be the item text without the ``*`` marker.
        """
        content: str = "* First item\n* Second item\n"

        parser: AsciidocParser = AsciidocParser()
        result: ParseResult = parser.parse(content)

        ulist_items = [b for b in result.blocks if b.block_type == "list_item_unordered"]
        assert len(ulist_items) == 2
        assert ulist_items[0].content == "First item"
        assert ulist_items[1].content == "Second item"

    def test_ordered_list(self) -> None:
        """Ordered list item ``. Item`` produces list_item_ordered.

        The block content should be the item text without the ``.`` marker.
        """
        content: str = ". Step one\n. Step two\n"

        parser: AsciidocParser = AsciidocParser()
        result: ParseResult = parser.parse(content)

        olist_items = [b for b in result.blocks if b.block_type == "list_item_ordered"]
        assert len(olist_items) == 2
        assert olist_items[0].content == "Step one"
        assert olist_items[1].content == "Step two"

    def test_code_block_skip_analysis(self) -> None:
        """Code block delimited by ``----`` has should_skip_analysis=True.

        Code blocks must not be style-checked, so should_skip_analysis
        must be set to True.
        """
        content: str = (
            "----\n"
            "echo 'hello world'\n"
            "ls -la\n"
            "----\n"
        )

        parser: AsciidocParser = AsciidocParser()
        result: ParseResult = parser.parse(content)

        code_blocks = [b for b in result.blocks if b.block_type == "code_block"]
        assert len(code_blocks) == 1
        assert code_blocks[0].should_skip_analysis is True
        assert "echo 'hello world'" in code_blocks[0].content

    def test_admonition_note(self) -> None:
        """Admonition ``[NOTE]`` followed by text produces an admonition block.

        The block should have block_type='admonition' and metadata with
        admonition_type set to 'NOTE'. The content should be the body text
        without the ``[NOTE]`` marker line.
        """
        content: str = (
            "[NOTE]\n"
            "This is an important note about the system.\n"
        )

        parser: AsciidocParser = AsciidocParser()
        result: ParseResult = parser.parse(content)

        admonitions = [b for b in result.blocks if b.block_type == "admonition"]
        assert len(admonitions) == 1
        assert "important note" in admonitions[0].content
        assert admonitions[0].metadata.get("admonition_type") == "NOTE"

    def test_char_map_identity_for_plain_text(self) -> None:
        """char_map maps content positions to inline_content positions.

        For plain text without inline markers, the char_map should be an
        identity mapping — each position maps to itself.
        """
        content: str = "This is plain text without formatting.\n"

        parser: AsciidocParser = AsciidocParser()
        result: ParseResult = parser.parse(content)

        assert len(result.blocks) >= 1
        block = result.blocks[0]
        assert block.char_map is not None
        # Identity mapping: char_map[i] == i for all positions
        for i, mapped_pos in enumerate(block.char_map):
            assert mapped_pos == i, (
                f"char_map[{i}] = {mapped_pos}, expected {i}"
            )

    def test_inline_content_preserves_markers(self) -> None:
        """inline_content preserves markers while content has them stripped.

        For ``**bold** text``, inline_content should retain ``**bold**``
        and content should have just ``bold``.
        """
        content: str = "**bold** text\n"

        parser: AsciidocParser = AsciidocParser()
        result: ParseResult = parser.parse(content)

        assert len(result.blocks) >= 1
        block = result.blocks[0]
        # inline_content preserves the AsciiDoc inline markers
        assert "**bold**" in block.inline_content
        # content has inline markers stripped
        assert block.content == "bold text"
        # char_map should exist since stripping occurred
        assert block.char_map is not None
        assert len(block.char_map) == len(block.content)

    def test_start_pos_end_pos_alignment(self) -> None:
        """start_pos and end_pos use original text offsets.

        end_pos should cover the full raw line length from the original
        start position, and start_pos may be advanced past block-level
        markers (e.g. ``= `` for headings).
        """
        content: str = "= Title\n\nSome paragraph text.\n"

        parser: AsciidocParser = AsciidocParser()
        result: ParseResult = parser.parse(content)

        heading = [b for b in result.blocks if b.block_type == "heading"][0]
        paragraph = [b for b in result.blocks if b.block_type == "paragraph"][0]

        # Heading end_pos should encompass the raw line from the original start
        assert heading.end_pos > heading.start_pos
        # Paragraph start_pos should be after the heading + blank line
        assert paragraph.start_pos > heading.start_pos

    def test_list_continuation_no_bleed(self) -> None:
        """Paragraph after list continuation ``+`` does not bleed into previous block.

        The ``+`` marker on its own line is a list continuation indicator.
        A paragraph following it should be a separate block, not merged
        into a preceding paragraph.
        """
        content: str = (
            "* List item\n"
            "+\n"
            "Continuation paragraph.\n"
        )

        parser: AsciidocParser = AsciidocParser()
        result: ParseResult = parser.parse(content)

        # The + marker should be handled as a comment/skip block
        list_items = [b for b in result.blocks if b.block_type == "list_item_unordered"]
        assert len(list_items) == 1
        assert list_items[0].content == "List item"

        # The continuation paragraph should be a separate block
        paragraphs = [b for b in result.blocks if b.block_type == "paragraph"]
        assert len(paragraphs) == 1
        assert paragraphs[0].content == "Continuation paragraph."

    def test_block_attributes_recognized_as_code(self) -> None:
        """Block attribute ``[source,bash]`` before ``----`` produces a code block.

        The generic block attribute pattern should be recognized and
        skipped (not treated as paragraph text), and the following
        ``----`` delimited block should be a code_block.
        """
        content: str = (
            "[source,bash]\n"
            "----\n"
            "dnf install httpd\n"
            "----\n"
        )

        parser: AsciidocParser = AsciidocParser()
        result: ParseResult = parser.parse(content)

        # The [source,bash] line should be skipped (comment block)
        comment_blocks = [
            b for b in result.blocks
            if b.block_type == "comment" and b.should_skip_analysis
        ]
        assert len(comment_blocks) >= 1

        # The ---- block should be a code_block
        code_blocks = [b for b in result.blocks if b.block_type == "code_block"]
        assert len(code_blocks) == 1
        assert code_blocks[0].should_skip_analysis is True
        assert "dnf install httpd" in code_blocks[0].content

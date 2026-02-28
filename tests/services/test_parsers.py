"""Tests for the document parsing services.

Validates the plaintext parser, markdown parser, and format detector
to ensure they correctly extract text content and identify file formats.
"""

import logging
from typing import Optional

import pytest

from app.models.enums import FileType
from app.services.parsing.base import Block, ParseResult
from app.services.parsing.format_detector import detect_format
from app.services.parsing.markdown_parser import MarkdownParser
from app.services.parsing.plaintext_parser import PlaintextParser

logger = logging.getLogger(__name__)


class TestPlaintextParser:
    """Tests for the PlaintextParser class."""

    def test_plaintext_parser(self) -> None:
        """Plaintext parser extracts text correctly from plain paragraphs.

        Multiple paragraphs separated by blank lines should produce
        separate Block instances, each containing the paragraph text.
        """
        content: str = (
            "This is the first paragraph.\n"
            "\n"
            "This is the second paragraph."
        )

        parser: PlaintextParser = PlaintextParser()
        result: ParseResult = parser.parse(content)

        assert len(result.blocks) >= 2
        texts = [block.content for block in result.blocks]
        assert "This is the first paragraph." in texts
        assert "This is the second paragraph." in texts

    def test_plaintext_parser_empty_content(self) -> None:
        """Plaintext parser handles empty input without errors.

        An empty string should produce an empty blocks list and
        an empty plain_text string.
        """
        parser: PlaintextParser = PlaintextParser()
        result: ParseResult = parser.parse("")

        assert len(result.blocks) == 0
        assert result.plain_text == ""

    def test_plaintext_parser_single_paragraph(self) -> None:
        """Plaintext parser handles a single paragraph correctly.

        A text without blank-line separators should produce at
        least one block.
        """
        content: str = "Just a single paragraph of text."

        parser: PlaintextParser = PlaintextParser()
        result: ParseResult = parser.parse(content)

        assert len(result.blocks) >= 1
        assert result.blocks[0].content == "Just a single paragraph of text."

    def test_plaintext_parser_block_types(self) -> None:
        """Plaintext parser assigns valid block types.

        Each block should be typed as either 'heading' or 'paragraph'.
        """
        content: str = (
            "HEADING TEXT\n"
            "\n"
            "This is a regular paragraph with a full sentence."
        )

        parser: PlaintextParser = PlaintextParser()
        result: ParseResult = parser.parse(content)

        for block in result.blocks:
            assert block.block_type in ("heading", "paragraph"), (
                f"Unexpected block type: {block.block_type}"
            )

    def test_plaintext_parser_plain_text_output(self) -> None:
        """Plaintext parser builds plain_text from non-skipped blocks.

        The plain_text field should concatenate all analyzable block
        contents separated by double newlines.
        """
        content: str = (
            "First paragraph.\n"
            "\n"
            "Second paragraph."
        )

        parser: PlaintextParser = PlaintextParser()
        result: ParseResult = parser.parse(content)

        assert "First paragraph." in result.plain_text
        assert "Second paragraph." in result.plain_text


class TestMarkdownParser:
    """Tests for the MarkdownParser class."""

    def test_markdown_parser(self) -> None:
        """Markdown parser extracts text from markdown content.

        A markdown document with a heading and paragraph should produce
        corresponding blocks with the correct content text.
        """
        content: str = (
            "# Main Heading\n"
            "\n"
            "This is a paragraph under the heading.\n"
        )

        parser: MarkdownParser = MarkdownParser()
        result: ParseResult = parser.parse(content)

        assert len(result.blocks) >= 2

        heading_blocks = [b for b in result.blocks if b.block_type == "heading"]
        paragraph_blocks = [b for b in result.blocks if b.block_type == "paragraph"]

        assert len(heading_blocks) >= 1
        assert "Main Heading" in heading_blocks[0].content

        assert len(paragraph_blocks) >= 1
        assert "paragraph under the heading" in paragraph_blocks[0].content

    def test_markdown_parser_code_blocks_skipped(self) -> None:
        """Markdown parser marks code blocks as should_skip_analysis.

        Code fences should produce code_block typed blocks with
        should_skip_analysis set to True.
        """
        content: str = (
            "Some text.\n"
            "\n"
            "```python\n"
            "print('hello')\n"
            "```\n"
        )

        parser: MarkdownParser = MarkdownParser()
        result: ParseResult = parser.parse(content)

        code_blocks = [b for b in result.blocks if b.block_type == "code_block"]
        assert len(code_blocks) >= 1
        assert code_blocks[0].should_skip_analysis is True

    def test_markdown_parser_empty_content(self) -> None:
        """Markdown parser handles empty input without errors.

        An empty string should produce zero blocks and empty plain_text.
        """
        parser: MarkdownParser = MarkdownParser()
        result: ParseResult = parser.parse("")

        assert len(result.blocks) == 0
        assert result.plain_text == ""

    def test_markdown_parser_heading_levels(self) -> None:
        """Markdown parser correctly detects heading levels.

        H1, H2, and H3 markdown headings should have corresponding
        level values on the resulting Block objects.
        """
        content: str = (
            "# Level 1\n"
            "\n"
            "## Level 2\n"
            "\n"
            "### Level 3\n"
        )

        parser: MarkdownParser = MarkdownParser()
        result: ParseResult = parser.parse(content)

        headings = [b for b in result.blocks if b.block_type == "heading"]
        levels = [h.level for h in headings]

        assert 1 in levels
        assert 2 in levels
        assert 3 in levels


class TestFormatDetector:
    """Tests for the format_detector.detect_format function."""

    def test_format_detector_plaintext(self) -> None:
        """Detector identifies .txt files as plaintext.

        When given a .txt filename extension, the detector should
        return FileType.PLAINTEXT.
        """
        result: FileType = detect_format(
            "Just some plain text.",
            filename="document.txt",
        )

        assert result == FileType.PLAINTEXT

    def test_format_detector_markdown(self) -> None:
        """Detector identifies .md files as markdown.

        When given a .md filename extension with markdown content
        patterns, the detector should return FileType.MARKDOWN.
        """
        content: str = "# Heading\n\nSome paragraph text.\n"

        result: FileType = detect_format(content, filename="readme.md")

        assert result == FileType.MARKDOWN

    def test_format_detector_html(self) -> None:
        """Detector identifies HTML content correctly.

        Content containing HTML doctype and html tags should be
        detected as FileType.HTML.
        """
        content: str = (
            "<!DOCTYPE html>\n"
            "<html>\n"
            "<body><p>Hello</p></body>\n"
            "</html>"
        )

        result: FileType = detect_format(content, filename="page.html")

        assert result == FileType.HTML

    def test_format_detector_empty_content(self) -> None:
        """Detector handles empty content gracefully.

        Empty content without a filename should default to PLAINTEXT.
        """
        result: FileType = detect_format("")

        assert result == FileType.PLAINTEXT

    def test_format_detector_asciidoc(self) -> None:
        """Detector identifies AsciiDoc content by patterns.

        Content with AsciiDoc heading markers and attributes should
        be detected as FileType.ASCIIDOC.
        """
        content: str = (
            "= Main Title\n"
            ":author: Test Author\n"
            ":doctype: article\n"
            "\n"
            "== Section One\n"
            "\n"
            "[NOTE]\n"
            "This is a note.\n"
        )

        result: FileType = detect_format(content, filename="doc.adoc")

        assert result == FileType.ASCIIDOC

    def test_format_detector_extension_only(self) -> None:
        """Detector falls back to extension when content is empty.

        When content is blank but a filename is provided, the
        extension should determine the file type.
        """
        result: FileType = detect_format("", filename="notes.md")

        assert result == FileType.MARKDOWN

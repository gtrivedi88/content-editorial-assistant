"""Tests for the HTML parser.

Validates container recursion (div/section/article), typed list items,
inline marker preservation (bold + code), char_map alignment with
bold/code markers, and integration scenarios including the word
concatenation fix.
"""

import logging

import pytest

from app.services.parsing.base import Block, ParseResult
from app.services.parsing.html_parser import (
    HtmlParser,
    _build_inline_char_map,
    _extract_text_with_inline_markers,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _collect_all_blocks(blocks: list[Block]) -> list[Block]:
    """Recursively collect all blocks including children.

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
# Container recursion tests (5 tests)
# ---------------------------------------------------------------------------


class TestContainerRecursion:
    """Tests for div/section/article container recursion."""

    def test_structural_div_produces_multiple_blocks(self) -> None:
        """Structural div with <h2> + <p> + <ol> produces multiple blocks.

        A div wrapping heterogeneous content must recurse into children
        instead of flattening everything via text_content().
        """
        html = (
            "<div>"
            "<h2>Configure the bridge</h2>"
            "<p>Follow these steps to configure the network bridge.</p>"
            "<ol><li>Open the console.</li><li>Run the command.</li></ol>"
            "</div>"
        )
        parser = HtmlParser()
        result = parser.parse(html)
        all_blocks = _collect_all_blocks(result.blocks)

        types = [b.block_type for b in all_blocks]
        assert "heading" in types
        assert "paragraph" in types
        assert "list" in types
        assert len(all_blocks) >= 3

    def test_nested_divs_recurse_correctly(self) -> None:
        """Nested divs recurse into each level without flattening.

        ``<div><div><p>text</p></div></div>`` must produce a paragraph
        block with content "text", not a single flattened block.
        """
        html = "<div><div><p>Inner paragraph text.</p></div></div>"
        parser = HtmlParser()
        result = parser.parse(html)
        all_blocks = _collect_all_blocks(result.blocks)

        paragraphs = [b for b in all_blocks if b.block_type == "paragraph"]
        assert len(paragraphs) >= 1
        assert any("Inner paragraph text" in p.content for p in paragraphs)

    def test_section_and_article_recurse_like_divs(self) -> None:
        """<section> and <article> recurse into children like divs.

        These container tags were removed from _TAG_MAP so they are
        treated as containers that the walker recurses through.
        """
        html = (
            "<section>"
            "<h3>Section heading</h3>"
            "<p>Section content.</p>"
            "</section>"
            "<article>"
            "<h3>Article heading</h3>"
            "<p>Article content.</p>"
            "</article>"
        )
        parser = HtmlParser()
        result = parser.parse(html)
        all_blocks = _collect_all_blocks(result.blocks)

        headings = [b for b in all_blocks if b.block_type == "heading"]
        paragraphs = [b for b in all_blocks if b.block_type == "paragraph"]
        assert len(headings) >= 2
        assert len(paragraphs) >= 2

    def test_admonition_div_treated_as_terminal_block(self) -> None:
        """Admonition div with CSS class 'note' produces an admonition block.

        Admonition divs should NOT recurse — they are treated as terminal
        blocks with should_skip_analysis=True.
        """
        html = (
            '<div class="note">'
            "<p>Remember to save your work before proceeding.</p>"
            "</div>"
        )
        parser = HtmlParser()
        result = parser.parse(html)
        all_blocks = _collect_all_blocks(result.blocks)

        admonitions = [b for b in all_blocks if b.block_type == "admonition"]
        assert len(admonitions) >= 1
        assert admonitions[0].should_skip_analysis is True
        assert "save your work" in admonitions[0].content

    def test_loose_text_inside_div_becomes_paragraph(self) -> None:
        """Loose text inside a div (not wrapped in <p>) becomes a paragraph.

        Text nodes directly inside container elements are captured by
        _emit_loose_text() as paragraph blocks.
        """
        html = "<div>Some loose text here<p>And a paragraph.</p></div>"
        parser = HtmlParser()
        result = parser.parse(html)
        all_blocks = _collect_all_blocks(result.blocks)

        paragraphs = [b for b in all_blocks if b.block_type == "paragraph"]
        contents = [p.content for p in paragraphs]
        assert any("Some loose text here" in c for c in contents)
        assert any("And a paragraph" in c for c in contents)


# ---------------------------------------------------------------------------
# List item typing tests (4 tests)
# ---------------------------------------------------------------------------


class TestListItemTyping:
    """Tests for typed list items (ordered vs unordered)."""

    def test_ordered_list_produces_list_item_ordered_children(self) -> None:
        """<ol><li> produces list_item_ordered children."""
        html = "<ol><li>First step.</li><li>Second step.</li></ol>"
        parser = HtmlParser()
        result = parser.parse(html)
        all_blocks = _collect_all_blocks(result.blocks)

        lists = [b for b in all_blocks if b.block_type == "list"]
        assert len(lists) >= 1
        children = lists[0].children
        assert len(children) == 2
        for child in children:
            assert child.block_type == "list_item_ordered"

    def test_unordered_list_produces_list_item_unordered_children(self) -> None:
        """<ul><li> produces list_item_unordered children."""
        html = "<ul><li>Item A.</li><li>Item B.</li></ul>"
        parser = HtmlParser()
        result = parser.parse(html)
        all_blocks = _collect_all_blocks(result.blocks)

        lists = [b for b in all_blocks if b.block_type == "list"]
        assert len(lists) >= 1
        children = lists[0].children
        assert len(children) == 2
        for child in children:
            assert child.block_type == "list_item_unordered"

    def test_parent_list_block_type_preserved(self) -> None:
        """Parent <ul>/<ol> block type is still 'list'."""
        html = "<ul><li>Item.</li></ul><ol><li>Step.</li></ol>"
        parser = HtmlParser()
        result = parser.parse(html)

        lists = [b for b in result.blocks if b.block_type == "list"]
        assert len(lists) == 2

    def test_inline_code_in_list_items_gets_backtick_markers(self) -> None:
        """Inline <code> in list items gets backtick markers in inline_content."""
        html = "<ul><li>Run the <code>curl</code> command.</li></ul>"
        parser = HtmlParser()
        result = parser.parse(html)
        all_blocks = _collect_all_blocks(result.blocks)

        items = [
            b for b in all_blocks
            if b.block_type in ("list_item", "list_item_unordered")
        ]
        assert len(items) >= 1
        item = items[0]
        assert "`curl`" in item.inline_content
        assert "curl" in item.content
        # content should NOT have backticks
        assert "`" not in item.content


# ---------------------------------------------------------------------------
# Inline marker preservation tests (5 tests)
# ---------------------------------------------------------------------------


class TestInlineMarkerPreservation:
    """Tests for bold and code inline marker preservation."""

    def test_bold_b_tag_produces_double_star_in_inline_content(self) -> None:
        """<b>text</b> produces **text** in inline_content."""
        html = "<p>Click <b>Save</b> to continue.</p>"
        parser = HtmlParser()
        result = parser.parse(html)

        paragraphs = [b for b in result.blocks if b.block_type == "paragraph"]
        assert len(paragraphs) >= 1
        p = paragraphs[0]
        assert "**Save**" in p.inline_content
        assert "Save" in p.content
        assert "**" not in p.content

    def test_strong_tag_produces_double_star_in_inline_content(self) -> None:
        """<strong>text</strong> produces **text** in inline_content."""
        html = "<p>Click <strong>Apply</strong> to confirm.</p>"
        parser = HtmlParser()
        result = parser.parse(html)

        paragraphs = [b for b in result.blocks if b.block_type == "paragraph"]
        assert len(paragraphs) >= 1
        p = paragraphs[0]
        assert "**Apply**" in p.inline_content

    def test_code_tag_produces_backticks_regression(self) -> None:
        """<code>cmd</code> produces `cmd` in inline_content (regression)."""
        html = "<p>Run <code>systemctl</code> to check status.</p>"
        parser = HtmlParser()
        result = parser.parse(html)

        paragraphs = [b for b in result.blocks if b.block_type == "paragraph"]
        assert len(paragraphs) >= 1
        p = paragraphs[0]
        assert "`systemctl`" in p.inline_content
        assert "systemctl" in p.content

    def test_bold_wrapping_code_produces_correct_markers(self) -> None:
        """<b><code>curl</code></b> produces **`curl`** in inline_content.

        Code is processed first (innermost), then bold (outermost).
        """
        html = "<p>Use <b><code>curl</code></b> for HTTP requests.</p>"
        parser = HtmlParser()
        result = parser.parse(html)

        paragraphs = [b for b in result.blocks if b.block_type == "paragraph"]
        assert len(paragraphs) >= 1
        p = paragraphs[0]
        assert "**`curl`**" in p.inline_content

    def test_nested_bold_guard_no_double_wrapping(self) -> None:
        """Nested <b><b>text</b></b> does not produce ****double-wrap****.

        The XPath guard not(ancestor::b or ancestor::strong) prevents
        double-processing of nested bold elements.
        """
        html = "<p>See <b><b>important</b></b> note.</p>"
        parser = HtmlParser()
        result = parser.parse(html)

        paragraphs = [b for b in result.blocks if b.block_type == "paragraph"]
        assert len(paragraphs) >= 1
        p = paragraphs[0]
        # Should have exactly one pair of **, not ****
        assert "****" not in p.inline_content
        assert "**important**" in p.inline_content


# ---------------------------------------------------------------------------
# char_map tests (3 tests)
# ---------------------------------------------------------------------------


class TestCharMap:
    """Tests for char_map with bold and code markers."""

    def test_char_map_with_bold_markers(self) -> None:
        """char_map with ** bold markers maps content to inline_content correctly."""
        content = "Click Save to continue."
        inline_content = "Click **Save** to continue."

        char_map = _build_inline_char_map(content, inline_content)

        assert len(char_map) == len(content)
        # 'S' in content (pos 6) should map past the ** in inline_content
        assert char_map[6] == 8  # 'S' after '**' (pos 0-6: 'Click ', 7-8: '**')

    def test_char_map_with_mixed_backtick_and_bold_markers(self) -> None:
        """char_map with both backtick and ** markers maps correctly."""
        content = "Run curl as root."
        inline_content = "Run `curl` as **root**."

        char_map = _build_inline_char_map(content, inline_content)

        assert len(char_map) == len(content)
        # Each content position should map to a valid inline_content position
        for i, pos in enumerate(char_map):
            assert 0 <= pos < len(inline_content), (
                f"char_map[{i}] = {pos} out of bounds "
                f"for inline_content length {len(inline_content)}"
            )

    def test_char_map_code_only_regression(self) -> None:
        """char_map with backtick-only markers (regression for existing behavior)."""
        content = "Run curl command."
        inline_content = "Run `curl` command."

        char_map = _build_inline_char_map(content, inline_content)

        assert len(char_map) == len(content)
        # 'c' in 'curl' at content pos 4 should map past the backtick
        assert char_map[4] == 5  # 'c' after '`' (pos 0-3: 'Run ', 4: '`')


# ---------------------------------------------------------------------------
# Integration tests (4 tests)
# ---------------------------------------------------------------------------


class TestIntegration:
    """End-to-end integration tests for HtmlParser."""

    def test_full_red_hat_procedure_html_produces_multiple_blocks(self) -> None:
        """Full Red Hat procedure-style HTML produces 10+ blocks.

        A realistic page with headings, paragraphs, ordered and unordered
        lists, code blocks, and bold UI elements must parse into many
        individual blocks with correct types.
        """
        html = (
            "<div>"
            "<h2>Configuring a network bridge</h2>"
            "<p>A network bridge connects two or more network segments.</p>"
            "<div class='note'>"
            "<p>Back up your configuration before proceeding.</p>"
            "</div>"
            "<h3>Prerequisites</h3>"
            "<ul>"
            "<li>A running <code>NetworkManager</code> service.</li>"
            "<li>Root access to the system.</li>"
            "<li>An active network connection.</li>"
            "</ul>"
            "<h3>Procedure</h3>"
            "<ol>"
            "<li>Open the <b>Settings</b> panel.</li>"
            "<li>Click <b>Network</b> in the sidebar.</li>"
            "<li>Run <code>nmcli connection add type bridge</code>.</li>"
            "<li>Verify the bridge with <code>ip link show</code>.</li>"
            "<li>Save your changes.</li>"
            "</ol>"
            "<h3>Verification</h3>"
            "<p>Run <code>bridge link</code> to confirm the configuration.</p>"
            "<pre>$ bridge link\n2: enp1s0: ...</pre>"
            "</div>"
        )
        parser = HtmlParser()
        result = parser.parse(html)
        all_blocks = _collect_all_blocks(result.blocks)

        assert len(all_blocks) >= 10, (
            f"Expected 10+ blocks, got {len(all_blocks)}: "
            f"{[b.block_type for b in all_blocks]}"
        )

        types = {b.block_type for b in all_blocks}
        assert "heading" in types
        assert "paragraph" in types
        assert "list" in types
        assert "admonition" in types

    def test_plain_text_joins_non_skipped_block_content(self) -> None:
        """plain_text joins content from non-skipped blocks."""
        html = (
            "<div>"
            "<p>First paragraph.</p>"
            "<pre>code block here</pre>"
            "<p>Second paragraph.</p>"
            "</div>"
        )
        parser = HtmlParser()
        result = parser.parse(html)

        assert "First paragraph." in result.plain_text
        assert "Second paragraph." in result.plain_text
        # Code block is skipped, should not be in plain_text
        assert "code block here" not in result.plain_text

    def test_empty_and_whitespace_input_returns_empty_result(self) -> None:
        """Empty or whitespace-only input returns empty ParseResult."""
        parser = HtmlParser()

        result_empty = parser.parse("")
        assert result_empty.blocks == []
        assert result_empty.plain_text == ""

        result_ws = parser.parse("   \n  \t  ")
        assert result_ws.blocks == []
        assert result_ws.plain_text == ""

    def test_no_word_concatenation_bug(self) -> None:
        """No word concatenation artifacts like 'linkUse' or 'consoleConfiguring'.

        The old parser used text_content() on wrapper divs which
        concatenated descendant text without spaces. With container
        recursion, each content element produces its own block.
        """
        html = (
            "<div>"
            "<p>Click the link</p>"
            "<p>Use the console</p>"
            "<p>Configuring the network</p>"
            "</div>"
        )
        parser = HtmlParser()
        result = parser.parse(html)
        all_blocks = _collect_all_blocks(result.blocks)

        for block in all_blocks:
            # No word concatenation artifacts
            assert "linkUse" not in block.content
            assert "consoleConfiguring" not in block.content

        # Each paragraph is its own block
        paragraphs = [b for b in all_blocks if b.block_type == "paragraph"]
        assert len(paragraphs) == 3
        assert paragraphs[0].content == "Click the link"
        assert paragraphs[1].content == "Use the console"
        assert paragraphs[2].content == "Configuring the network"


# ---------------------------------------------------------------------------
# Position coordinate tests — Part G (5 tests)
# ---------------------------------------------------------------------------


class TestPositionCoordinates:
    """Tests for plain-text coordinate space in block positions.

    HtmlParser must produce start_pos/end_pos in plain-text coordinates
    (matching the browser's innerText), NOT in HTML-byte coordinates.
    """

    def test_block_positions_use_text_length_not_html_length(self) -> None:
        """end_pos - start_pos equals len(text_content), not len(raw_html).

        For ``<p>Click <b>Save</b></p>``, the block span should be 10
        characters (``Click Save``), not 29 characters (the HTML string).
        """
        html = "<p>Click <b>Save</b></p>"
        parser = HtmlParser()
        result = parser.parse(html)

        paragraphs = [b for b in result.blocks if b.block_type == "paragraph"]
        assert len(paragraphs) >= 1
        p = paragraphs[0]
        text_len = len(p.content)
        block_span = p.end_pos - p.start_pos
        assert block_span == text_len, (
            f"Block span {block_span} != text length {text_len}; "
            f"positions are in HTML-byte space instead of text space"
        )

    def test_block_boundary_newline_accounted(self) -> None:
        """Block boundary newline is accounted for in positions.

        For ``<h2>Title</h2><p>Body text</p>``, the ``<p>`` block's
        start_pos should be ``len('Title') + 1`` — the +1 accounts for
        the newline that innerText injects between block elements.
        """
        html = "<h2>Title</h2><p>Body text</p>"
        parser = HtmlParser()
        result = parser.parse(html)

        headings = [b for b in result.blocks if b.block_type == "heading"]
        paragraphs = [b for b in result.blocks if b.block_type == "paragraph"]
        assert len(headings) >= 1
        assert len(paragraphs) >= 1

        h = headings[0]
        p = paragraphs[0]
        # Heading: start=0, end=len("Title")=5
        assert h.start_pos == 0
        assert h.end_pos == len("Title")
        # Paragraph: start=len("Title") + 1 (block boundary newline)
        expected_start = len("Title") + 1
        assert p.start_pos == expected_start, (
            f"Paragraph start_pos {p.start_pos} != expected {expected_start}; "
            f"block boundary newline not accounted for"
        )

    def test_positions_monotonically_increase(self) -> None:
        """All blocks' start_pos values increase monotonically.

        For a multi-block document, no block should start before the
        previous block ends.
        """
        html = (
            "<h2>Heading</h2>"
            "<p>A paragraph of text.</p>"
            "<ol><li>First item.</li><li>Second item.</li></ol>"
        )
        parser = HtmlParser()
        result = parser.parse(html)

        prev_start = -1
        for block in result.blocks:
            assert block.start_pos > prev_start, (
                f"Block '{block.block_type}' start_pos {block.start_pos} "
                f"<= previous start {prev_start}"
            )
            prev_start = block.start_pos

    def test_child_positions_within_parent_range(self) -> None:
        """Children's positions fall within the parent block range.

        For a ``<ul>`` with 3 ``<li>`` items, each child's start_pos
        must be >= parent start_pos and end_pos <= parent end_pos.
        """
        html = (
            "<ul>"
            "<li>Apple</li>"
            "<li>Banana</li>"
            "<li>Cherry</li>"
            "</ul>"
        )
        parser = HtmlParser()
        result = parser.parse(html)

        lists = [b for b in result.blocks if b.block_type == "list"]
        assert len(lists) >= 1
        parent = lists[0]
        assert len(parent.children) == 3

        for child in parent.children:
            assert child.start_pos >= parent.start_pos, (
                f"Child start {child.start_pos} < parent start {parent.start_pos}"
            )
            assert child.end_pos <= parent.end_pos, (
                f"Child end {child.end_pos} > parent end {parent.end_pos}"
            )

    def test_no_html_byte_inflation(self) -> None:
        """Positions are in text space, not HTML-byte space.

        For HTML with heavy markup, the last block's end_pos must be
        less than the length of the HTML string.
        """
        html = (
            "<h2>Setup</h2>"
            "<p>Install <b>the</b> <code>curl</code> tool and "
            '<a href="https://example.com">read the docs</a>.</p>'
            "<p>Then run <code>curl -v https://api.example.com</code>.</p>"
        )
        parser = HtmlParser()
        result = parser.parse(html)

        assert len(result.blocks) >= 2
        last_block = result.blocks[-1]
        assert last_block.end_pos < len(html), (
            f"Last block end_pos {last_block.end_pos} >= HTML length "
            f"{len(html)}; positions are in HTML-byte space"
        )

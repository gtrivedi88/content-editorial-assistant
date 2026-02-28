"""
Unit tests for SourceMap — character position tracking through text transformations.
"""

import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from structural_parsing.source_map import SourceMap


class TestSourceMapInit:
    """Test SourceMap initialization."""

    def test_identity_map(self):
        sm = SourceMap("hello")
        text, positions = sm.result
        assert text == "hello"
        assert positions == [0, 1, 2, 3, 4]

    def test_empty_input(self):
        sm = SourceMap("")
        text, positions = sm.result
        assert text == ""
        assert positions == []


class TestApplySub:
    """Test apply_sub with group captures and fixed replacements."""

    def test_bold_stripping(self):
        """Strip **bold** → bold, positions map to inside the markers."""
        sm = SourceMap("This is **bold** text")
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        text, positions = sm.result
        assert text == "This is bold text"
        # 'b' was at position 10 in raw, 'o' at 11, 'l' at 12, 'd' at 13
        assert positions[8] == 10  # 'b'
        assert positions[9] == 11  # 'o'
        assert positions[10] == 12  # 'l'
        assert positions[11] == 13  # 'd'

    def test_italic_stripping(self):
        """Strip __italic__ → italic."""
        sm = SourceMap("This is __italic__ text")
        sm.apply_sub(r'__(.+?)__', r'\1')
        text, positions = sm.result
        assert text == "This is italic text"

    def test_monospace_stripping(self):
        """Strip `code` → code."""
        sm = SourceMap("Use `kubectl` command")
        sm.apply_sub(r'`([^`]+)`', r'\1')
        text, positions = sm.result
        assert text == "Use kubectl command"
        # 'k' was at position 5 in raw
        assert positions[4] == 5

    def test_xref_macro_stripping(self):
        """Strip xref:target[text] → text."""
        sm = SourceMap("See xref:guide.adoc[the guide] for details")
        sm.apply_sub(r'xref:[^\[]+\[([^\]]*)\]', r'\1')
        text, positions = sm.result
        assert text == "See the guide for details"

    def test_link_macro_stripping(self):
        """Strip link:URL[text] → text."""
        sm = SourceMap("Visit link:https://example.com[our site] today")
        sm.apply_sub(r'link:https?://[^\s\[\]]+\[([^\]]*)\]', r'\1')
        text, positions = sm.result
        assert text == "Visit our site today"

    def test_attribute_replacement(self):
        """Replace {attribute} → placeholder, all chars map to match start."""
        sm = SourceMap("Install {product-name} now")
        sm.apply_sub(r'\{[^{}]+\}', 'placeholder')
        text, positions = sm.result
        assert text == "Install placeholder now"
        # All chars of 'placeholder' map to position 8 (start of {product-name})
        for i in range(8, 8 + len('placeholder')):
            assert positions[i] == 8

    def test_multiple_matches(self):
        """Handle multiple matches in one call."""
        sm = SourceMap("**bold** and **more bold**")
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        text, positions = sm.result
        assert text == "bold and more bold"

    def test_no_match(self):
        """No matches — text and positions unchanged."""
        sm = SourceMap("plain text")
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        text, positions = sm.result
        assert text == "plain text"
        assert positions == list(range(10))

    def test_empty_text(self):
        """apply_sub on empty text is a no-op."""
        sm = SourceMap("")
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        text, positions = sm.result
        assert text == ""
        assert positions == []

    def test_adjacent_matches(self):
        """Matches right next to each other."""
        sm = SourceMap("**a****b**")
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        text, positions = sm.result
        assert text == "ab"
        assert positions[0] == 2  # 'a' was at position 2
        assert positions[1] == 7  # 'b' was at position 7 (**a****b** → b is at index 7)


class TestApplyDelete:
    """Test apply_delete for removing matches."""

    def test_delete_email(self):
        """Remove email addresses."""
        sm = SourceMap("Contact user@example.com for help")
        sm.apply_delete(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        text, positions = sm.result
        assert text == "Contact  for help"
        # 'f' in 'for' was at position 25 in raw
        assert positions[9] == 25

    def test_delete_url(self):
        """Remove standalone URLs."""
        sm = SourceMap("Visit https://example.com/path for info")
        sm.apply_delete(r'https?://[^\s\[\]]+')
        text, positions = sm.result
        assert text == "Visit  for info"

    def test_delete_no_match(self):
        """No matches — nothing changes."""
        sm = SourceMap("no emails here")
        sm.apply_delete(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        text, positions = sm.result
        assert text == "no emails here"
        assert positions == list(range(14))

    def test_delete_empty_text(self):
        """apply_delete on empty text is a no-op."""
        sm = SourceMap("")
        sm.apply_delete(r'https?://[^\s]+')
        text, positions = sm.result
        assert text == ""
        assert positions == []


class TestCollapseSpaces:
    """Test collapse_spaces for multi-space runs."""

    def test_collapse_double_space(self):
        """Two spaces → one space."""
        sm = SourceMap("hello  world")
        sm.collapse_spaces()
        text, positions = sm.result
        assert text == "hello world"
        assert positions[5] == 5  # first space kept

    def test_collapse_many_spaces(self):
        """Many spaces → one space."""
        sm = SourceMap("hello     world")
        sm.collapse_spaces()
        text, positions = sm.result
        assert text == "hello world"

    def test_collapse_tabs(self):
        """Tab + space → single space."""
        sm = SourceMap("hello\t world")
        sm.collapse_spaces()
        text, positions = sm.result
        assert text == "hello world"

    def test_single_spaces_unchanged(self):
        """Single spaces are not collapsed."""
        sm = SourceMap("hello world test")
        sm.collapse_spaces()
        text, positions = sm.result
        assert text == "hello world test"
        assert positions == list(range(16))

    def test_collapse_empty(self):
        sm = SourceMap("")
        sm.collapse_spaces()
        text, positions = sm.result
        assert text == ""


class TestCleanSpaceBeforePunct:
    """Test clean_space_before_punct for artifact removal."""

    def test_space_before_period(self):
        """Remove space before period."""
        sm = SourceMap("hello .")
        sm.clean_space_before_punct()
        text, positions = sm.result
        assert text == "hello."

    def test_space_before_comma(self):
        """Remove space before comma."""
        sm = SourceMap("hello , world")
        sm.clean_space_before_punct()
        text, positions = sm.result
        assert text == "hello, world"

    def test_multiple_spaces_before_punct(self):
        """Remove multiple spaces before punctuation."""
        sm = SourceMap("hello   .")
        sm.clean_space_before_punct()
        text, positions = sm.result
        assert text == "hello."

    def test_no_artifact(self):
        """Normal text with proper punctuation — no change."""
        sm = SourceMap("hello. world")
        sm.clean_space_before_punct()
        text, positions = sm.result
        assert text == "hello. world"

    def test_clean_empty(self):
        sm = SourceMap("")
        sm.clean_space_before_punct()
        text, positions = sm.result
        assert text == ""


class TestStrip:
    """Test strip for whitespace trimming."""

    def test_strip_leading(self):
        sm = SourceMap("  hello")
        sm.strip()
        text, positions = sm.result
        assert text == "hello"
        assert positions[0] == 2  # 'h' was at position 2

    def test_strip_trailing(self):
        sm = SourceMap("hello  ")
        sm.strip()
        text, positions = sm.result
        assert text == "hello"
        assert len(positions) == 5

    def test_strip_both(self):
        sm = SourceMap("  hello  ")
        sm.strip()
        text, positions = sm.result
        assert text == "hello"
        assert positions[0] == 2

    def test_strip_newlines(self):
        sm = SourceMap("\nhello\n")
        sm.strip()
        text, positions = sm.result
        assert text == "hello"
        assert positions[0] == 1

    def test_strip_all_whitespace(self):
        sm = SourceMap("   ")
        sm.strip()
        text, positions = sm.result
        assert text == ""
        assert positions == []

    def test_strip_empty(self):
        sm = SourceMap("")
        sm.strip()
        text, positions = sm.result
        assert text == ""
        assert positions == []


class TestFullPipeline:
    """Test complete transformation pipelines matching real parser usage."""

    def test_asciidoc_pipeline(self):
        """Full AsciiDoc transformation: bold + xref + attribute + strip."""
        raw = "Install **{product}** using xref:guide.adoc[the installation guide]."
        sm = SourceMap(raw)
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        sm.apply_sub(r'xref:[^\[]+\[([^\]]*)\]', r'\1')
        sm.apply_sub(r'\{[^{}]+\}', 'placeholder')
        sm.collapse_spaces()
        sm.strip()
        text, positions = sm.result
        assert "placeholder" in text
        assert "the installation guide" in text
        assert "**" not in text
        assert "xref:" not in text

    def test_markdown_pipeline(self):
        """Full Markdown transformation: bold + link + strip."""
        raw = "Click **here** to visit [our docs](https://docs.example.com)."
        sm = SourceMap(raw)
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        sm.apply_sub(r'\[([^\]]*)\]\([^\)]*\)', r'\1')
        sm.collapse_spaces()
        sm.strip()
        text, positions = sm.result
        assert text == "Click here to visit our docs."
        assert "**" not in text
        assert "https://" not in text

    def test_position_integrity_through_pipeline(self):
        """Verify positions are correct after multiple transformations."""
        raw = "Use **bold** and `code` here"
        sm = SourceMap(raw)
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        sm.apply_sub(r'`([^`]+)`', r'\1')
        text, positions = sm.result

        assert text == "Use bold and code here"
        # Verify each character maps back correctly
        for i, pos in enumerate(positions):
            assert raw[pos] == text[i], f"Position {i}: expected '{text[i]}' but raw[{pos}]='{raw[pos]}'"

    def test_delete_then_clean_punct(self):
        """Delete URL before period, then clean the space artifact."""
        raw = "Visit https://example.com ."
        sm = SourceMap(raw)
        sm.apply_delete(r'https?://[^\s\[\]]+')
        sm.clean_space_before_punct()
        sm.collapse_spaces()
        sm.strip()
        text, positions = sm.result
        assert text == "Visit."

    def test_source_map_length_matches_text(self):
        """Source map length must always match cleaned text length."""
        raw = "This has **bold**, `code`, and xref:target[a link] with {attr}."
        sm = SourceMap(raw)
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        sm.apply_sub(r'`([^`]+)`', r'\1')
        sm.apply_sub(r'xref:[^\[]+\[([^\]]*)\]', r'\1')
        sm.apply_sub(r'\{[^{}]+\}', 'placeholder')
        sm.collapse_spaces()
        sm.strip()
        text, positions = sm.result
        assert len(text) == len(positions)

    def test_all_positions_in_bounds(self):
        """All position values must be valid indices into the original raw text."""
        raw = "**bold** `mono` link:https://x.com[click] {var}"
        sm = SourceMap(raw)
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        sm.apply_sub(r'`([^`]+)`', r'\1')
        sm.apply_sub(r'link:https?://[^\s\[\]]+\[([^\]]*)\]', r'\1')
        sm.apply_sub(r'\{[^{}]+\}', 'placeholder')
        sm.strip()
        text, positions = sm.result
        for i, pos in enumerate(positions):
            assert 0 <= pos < len(raw), f"Position {i} out of bounds: {pos} >= {len(raw)}"

    def test_span_conversion_round_trip(self):
        """Simulate the full error span conversion: find text in cleaned, map back to raw."""
        raw = "This is **important** and must not be `deleted` today."
        sm = SourceMap(raw)
        sm.apply_sub(r'\*\*(.+?)\*\*', r'\1')
        sm.apply_sub(r'`([^`]+)`', r'\1')
        text, positions = sm.result

        # Suppose a rule flags "important" in the cleaned text
        idx = text.index("important")
        span = [idx, idx + len("important")]

        # Convert to raw coordinates
        raw_start = positions[span[0]]
        raw_end = positions[span[1] - 1] + 1

        # The raw text at those positions should be "important" (inside the ** markers)
        assert raw[raw_start:raw_end] == "important"

    def test_span_conversion_for_attribute(self):
        """Attribute replacement: span on 'placeholder' maps back to {attr} start."""
        raw = "Install {product-name} now"
        sm = SourceMap(raw)
        sm.apply_sub(r'\{[^{}]+\}', 'placeholder')
        text, positions = sm.result

        idx = text.index("placeholder")
        span = [idx, idx + len("placeholder")]

        # All positions map to the start of {product-name}
        raw_start = positions[span[0]]
        assert raw_start == 8  # position of '{'
        # raw_end maps to same position since all chars map to match start
        raw_end = positions[span[1] - 1] + 1
        assert raw_start == 8

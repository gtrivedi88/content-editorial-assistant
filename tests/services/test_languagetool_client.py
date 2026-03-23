"""Tests for the LanguageTool HTTP client module.

Validates batch building, offset mapping, UTF-16 conversion,
cross-boundary match discard, inline code guards, technical content
detection, category/severity mappings, and graceful degradation.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
from app.services.analysis.languagetool_client import (
    _BatchEntry,
    _build_batches,
    _call_languagetool,
    _find_entry_for_offset,
    _HINT_GATED_CATEGORIES,
    _is_technical_content,
    _load_spelling_allowlist,
    _LT_CATEGORY_MAP,
    _LT_SEVERITY_MAP,
    _LT_SKIP_RULES,
    _map_lt_match_to_issue,
    _PROSE_BLOCK_TYPES,
    _should_skip_match,
    _SPELLING_ALLOWLIST,
    _utf16_to_codepoint_offset,
    check_blocks,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_block(
    content: str,
    block_type: str = "paragraph",
    start_pos: int = 0,
    end_pos: int | None = None,
    inline_content: str | None = None,
    char_map: list[int] | None = None,
    should_skip_analysis: bool = False,
) -> MagicMock:
    """Create a mock Block object for testing.

    Args:
        content: The stripped plain text content (Tier 3).
        block_type: Type of block (paragraph, heading, code, etc.).
        start_pos: Character offset where the block starts in original text.
        end_pos: Character offset where the block ends.
        inline_content: Tier 2 content with inline markers preserved.
        char_map: Maps content positions to inline_content positions.
        should_skip_analysis: Whether to skip analysis for this block.

    Returns:
        A MagicMock configured with block attributes.
    """
    block = MagicMock()
    block.content = content
    block.block_type = block_type
    block.start_pos = start_pos
    block.end_pos = end_pos if end_pos is not None else start_pos + len(content)
    block.inline_content = inline_content if inline_content is not None else content
    block.char_map = char_map
    block.should_skip_analysis = should_skip_analysis
    return block


def _make_lt_match(
    offset: int = 0,
    length: int = 5,
    message: str = "Test error",
    rule_id: str = "TEST_RULE",
    category_id: str = "GRAMMAR",
    issue_type: str = "grammar",
    replacements: list[dict] | None = None,
    sentence: str = "This is a test sentence.",
    confidence: float = 0.95,
) -> dict:
    """Create a mock LanguageTool match dict.

    Args:
        offset: Character offset (UTF-16 code units) in the batch text.
        length: Length of the flagged text (UTF-16 code units).
        message: Human-readable error message.
        rule_id: LT rule identifier.
        category_id: LT category identifier.
        issue_type: LT issue type string.
        replacements: List of replacement suggestion dicts.
        sentence: The full sentence containing the match.
        confidence: Rule confidence score.

    Returns:
        A dict matching LT's JSON match schema.
    """
    return {
        "offset": offset,
        "length": length,
        "message": message,
        "sentence": sentence,
        "rule": {
            "id": rule_id,
            "category": {"id": category_id},
            "issueType": issue_type,
            "confidence": confidence,
        },
        "replacements": replacements or [{"value": "fix"}],
    }


# ---------------------------------------------------------------------------
# UTF-16 → codepoint conversion
# ---------------------------------------------------------------------------


class TestUtf16ToCodepointOffset:
    """Tests for _utf16_to_codepoint_offset()."""

    def test_ascii_text_identity(self) -> None:
        """For pure ASCII text, UTF-16 offset equals Python index."""
        text = "Hello, world!"
        assert _utf16_to_codepoint_offset(text, 7) == 7

    def test_emoji_shifts_offset(self) -> None:
        """An emoji (outside BMP) occupies 2 UTF-16 code units but 1 codepoint.

        Text: "Hello 🚀 world" — the rocket emoji at position 6 is 2 code
        units in UTF-16. LT would report the space after it at offset 9
        (6 + 2 + 1), but Python sees it at index 8 (6 + 1 + 1).
        """
        text = "Hello \U0001f680 world"
        # "Hello " = 6 chars, emoji = 1 char (2 UTF-16 units), " " = 1
        # UTF-16 offset 9 → Python index 8
        assert _utf16_to_codepoint_offset(text, 9) == 8

    def test_offset_beyond_string_clamps(self) -> None:
        """Offsets beyond the string length are clamped to the end."""
        text = "short"
        result = _utf16_to_codepoint_offset(text, 100)
        assert result == len(text)

    def test_zero_offset(self) -> None:
        """Zero offset returns zero."""
        assert _utf16_to_codepoint_offset("any text", 0) == 0

    def test_multiple_bmp_characters(self) -> None:
        """Text with only BMP characters (accented letters) maps 1:1."""
        text = "café résumé"
        # All BMP — UTF-16 offset equals Python index
        assert _utf16_to_codepoint_offset(text, 5) == 5


# ---------------------------------------------------------------------------
# Technical content detection
# ---------------------------------------------------------------------------


class TestIsTechnicalContent:
    """Tests for _is_technical_content()."""

    def test_camel_case_detected(self) -> None:
        """camelCase identifiers are detected as technical."""
        assert _is_technical_content("camelCase") is True

    def test_pascal_case_detected(self) -> None:
        """PascalCase identifiers are detected as technical."""
        assert _is_technical_content("PascalCase") is True

    def test_file_path_detected(self) -> None:
        """File paths with slashes and dots are detected."""
        assert _is_technical_content("com.example.package") is True
        assert _is_technical_content("src/main/java") is True

    def test_url_detected(self) -> None:
        """URLs are detected as technical."""
        assert _is_technical_content("https://example.com") is True

    def test_underscore_identifier_detected(self) -> None:
        """Snake_case identifiers are detected."""
        assert _is_technical_content("my_variable") is True

    def test_digit_identifier_detected(self) -> None:
        """Alphanumeric identifiers with digits are detected as technical."""
        assert _is_technical_content("k8s") is True
        assert _is_technical_content("ipv4") is True
        assert _is_technical_content("x86_64") is True

    def test_uppercase_acronym_detected(self) -> None:
        """All-uppercase acronyms (2+ chars) are detected as technical."""
        assert _is_technical_content("RBAC") is True
        assert _is_technical_content("YAML") is True
        assert _is_technical_content("API") is True

    def test_single_uppercase_char_not_technical(self) -> None:
        """A single uppercase letter is not detected as an acronym."""
        assert _is_technical_content("I") is False

    def test_plain_english_not_technical(self) -> None:
        """Normal English words are not technical."""
        assert _is_technical_content("the quick brown fox") is False

    def test_empty_string_not_technical(self) -> None:
        """Empty string is not technical."""
        assert _is_technical_content("") is False

    def test_long_text_not_technical(self) -> None:
        """Text longer than 80 chars is not considered (optimization)."""
        assert _is_technical_content("a" * 81) is False


# ---------------------------------------------------------------------------
# Batch building
# ---------------------------------------------------------------------------


class TestBuildBatches:
    """Tests for _build_batches()."""

    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_single_prose_block(self, mock_ranges: MagicMock) -> None:
        """A single paragraph block produces one batch with correct offsets."""
        block = _make_block("Hello world.", block_type="paragraph")
        batches = _build_batches([block])

        assert len(batches) == 1
        assert batches[0].text == "Hello world.\n\n"
        assert len(batches[0].entries) == 1
        assert batches[0].entries[0].batch_start == 0
        assert batches[0].entries[0].batch_end == 12

    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_code_blocks_excluded(self, mock_ranges: MagicMock) -> None:
        """Code blocks are not included in batches."""
        blocks = [
            _make_block("Prose text.", block_type="paragraph"),
            _make_block("def foo(): pass", block_type="code_block"),
            _make_block("More prose.", block_type="paragraph", start_pos=30),
        ]
        batches = _build_batches(blocks)

        assert len(batches) == 1
        assert len(batches[0].entries) == 2
        # Code block should not be present
        for entry in batches[0].entries:
            assert entry.block.block_type != "code_block"

    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_skip_analysis_blocks_excluded(self, mock_ranges: MagicMock) -> None:
        """Blocks with should_skip_analysis=True are excluded."""
        block = _make_block(
            "Skip me.", block_type="paragraph", should_skip_analysis=True,
        )
        batches = _build_batches([block])
        assert len(batches) == 0

    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_empty_content_excluded(self, mock_ranges: MagicMock) -> None:
        """Blocks with empty or whitespace-only content are excluded."""
        block = _make_block("   ", block_type="paragraph")
        batches = _build_batches([block])
        assert len(batches) == 0

    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_batch_splits_at_max_chars(self, mock_ranges: MagicMock) -> None:
        """A new batch starts when accumulated text exceeds _MAX_BATCH_CHARS."""
        # Create blocks that together exceed 6000 chars
        long_text = "x" * 3500
        block_a = _make_block(long_text, block_type="paragraph")
        block_b = _make_block(long_text, block_type="paragraph", start_pos=3500)
        batches = _build_batches([block_a, block_b])

        assert len(batches) == 2
        assert len(batches[0].entries) == 1
        assert len(batches[1].entries) == 1

    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_multiple_blocks_correct_offsets(self, mock_ranges: MagicMock) -> None:
        """Multiple blocks in one batch have correct batch_start/batch_end."""
        block_a = _make_block("First block.", block_type="paragraph")
        block_b = _make_block(
            "Second block.", block_type="heading", start_pos=20,
        )
        batches = _build_batches([block_a, block_b])

        assert len(batches) == 1
        entries = batches[0].entries
        assert entries[0].batch_start == 0
        assert entries[0].batch_end == 12  # len("First block.")
        # Second block starts after "First block.\n\n" = 14
        assert entries[1].batch_start == 14
        assert entries[1].batch_end == 14 + 13  # len("Second block.")

    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_all_prose_block_types_accepted(self, mock_ranges: MagicMock) -> None:
        """All prose block types are included in batches."""
        blocks = [
            _make_block("Para.", block_type="paragraph"),
            _make_block("Head.", block_type="heading", start_pos=10),
            _make_block("Ordered.", block_type="list_item_ordered", start_pos=20),
            _make_block("Unordered.", block_type="list_item_unordered", start_pos=30),
        ]
        batches = _build_batches(blocks)
        assert len(batches) == 1
        assert len(batches[0].entries) == 4


# ---------------------------------------------------------------------------
# Match resolution — _find_entry_for_offset
# ---------------------------------------------------------------------------


class TestFindEntryForOffset:
    """Tests for _find_entry_for_offset()."""

    def test_match_within_first_entry(self) -> None:
        """A match within the first entry's range is returned."""
        entry_a = _BatchEntry(
            block=MagicMock(), batch_start=0, batch_end=50,
        )
        entry_b = _BatchEntry(
            block=MagicMock(), batch_start=52, batch_end=100,
        )
        result = _find_entry_for_offset([entry_a, entry_b], 10, 5)
        assert result is entry_a

    def test_match_within_second_entry(self) -> None:
        """A match within the second entry's range is returned."""
        entry_a = _BatchEntry(
            block=MagicMock(), batch_start=0, batch_end=50,
        )
        entry_b = _BatchEntry(
            block=MagicMock(), batch_start=52, batch_end=100,
        )
        result = _find_entry_for_offset([entry_a, entry_b], 60, 5)
        assert result is entry_b

    def test_cross_boundary_match_discarded(self) -> None:
        """A match spanning across a block boundary returns None."""
        entry_a = _BatchEntry(
            block=MagicMock(), batch_start=0, batch_end=50,
        )
        entry_b = _BatchEntry(
            block=MagicMock(), batch_start=52, batch_end=100,
        )
        # Match starts at 45, length 10 → extends to 55, past entry_a's end
        result = _find_entry_for_offset([entry_a, entry_b], 45, 10)
        assert result is None

    def test_match_at_exact_end_of_block(self) -> None:
        """A match ending exactly at batch_end is within bounds."""
        entry = _BatchEntry(
            block=MagicMock(), batch_start=0, batch_end=50,
        )
        # Match at offset 45, length 5 → ends at 50 == batch_end
        result = _find_entry_for_offset([entry], 45, 5)
        assert result is entry

    def test_offset_outside_all_entries(self) -> None:
        """An offset not in any entry's range returns None."""
        entry = _BatchEntry(
            block=MagicMock(), batch_start=0, batch_end=50,
        )
        result = _find_entry_for_offset([entry], 200, 5)
        assert result is None


# ---------------------------------------------------------------------------
# Match mapping — _map_lt_match_to_issue
# ---------------------------------------------------------------------------


class TestMapLtMatchToIssue:
    """Tests for _map_lt_match_to_issue()."""

    def test_basic_mapping(self) -> None:
        """A simple match maps to a correctly populated IssueResponse."""
        block = _make_block(
            "This is wrong text here.", start_pos=100,
        )
        entry = _BatchEntry(
            block=block, batch_start=0, batch_end=24,
        )
        match = _make_lt_match(
            offset=8, length=5, message="Use 'right' instead.",
            rule_id="WRONG_WORD", category_id="GRAMMAR",
            replacements=[{"value": "right"}],
        )
        issue = _map_lt_match_to_issue(match, entry, 8, 5, "wrong", "")

        assert issue is not None
        assert issue.source == "languagetool"
        assert issue.rule_name == "lt_wrong_word"
        assert issue.flagged_text == "wrong"
        assert issue.message == "Use 'right' instead."
        assert issue.suggestions == ["right"]
        assert issue.category == IssueCategory.GRAMMAR
        assert issue.severity == IssueSeverity.HIGH

    def test_category_mapping(self) -> None:
        """LT category IDs are mapped to CEA IssueCategory values."""
        block = _make_block("Test text.", start_pos=0)
        entry = _BatchEntry(block=block, batch_start=0, batch_end=10)

        for lt_cat, cea_cat in _LT_CATEGORY_MAP.items():
            match = _make_lt_match(
                offset=0, length=4, category_id=lt_cat,
            )
            issue = _map_lt_match_to_issue(
                match, entry, 0, 4, "Test", "",
            )
            assert issue is not None
            assert issue.category == cea_cat

    def test_severity_mapping(self) -> None:
        """LT issueType values are mapped to CEA IssueSeverity."""
        block = _make_block("Test text.", start_pos=0)
        entry = _BatchEntry(block=block, batch_start=0, batch_end=10)

        for lt_type, cea_sev in _LT_SEVERITY_MAP.items():
            match = _make_lt_match(
                offset=0, length=4, issue_type=lt_type,
            )
            issue = _map_lt_match_to_issue(
                match, entry, 0, 4, "Test", "",
            )
            assert issue is not None
            assert issue.severity == cea_sev

    def test_unknown_category_defaults_to_grammar(self) -> None:
        """Unmapped LT categories default to GRAMMAR."""
        block = _make_block("Test text.", start_pos=0)
        entry = _BatchEntry(block=block, batch_start=0, batch_end=10)
        match = _make_lt_match(category_id="UNKNOWN_CAT")
        issue = _map_lt_match_to_issue(match, entry, 0, 5, "Test ", "")
        assert issue is not None
        assert issue.category == IssueCategory.GRAMMAR

    def test_unknown_severity_defaults_to_medium(self) -> None:
        """Unmapped LT issueTypes default to MEDIUM severity."""
        block = _make_block("Test text.", start_pos=0)
        entry = _BatchEntry(block=block, batch_start=0, batch_end=10)
        match = _make_lt_match(issue_type="unknown_type")
        issue = _map_lt_match_to_issue(match, entry, 0, 5, "Test ", "")
        assert issue is not None
        assert issue.severity == IssueSeverity.MEDIUM

    def test_offset_out_of_bounds_returns_none(self) -> None:
        """Block-local offset beyond content length returns None."""
        block = _make_block("Short.", start_pos=0)
        entry = _BatchEntry(block=block, batch_start=0, batch_end=6)
        match = _make_lt_match(offset=0, length=20)
        issue = _map_lt_match_to_issue(
            match, entry, 0, 20, "Short.xxxxxxxxxxxxxx", "",
        )
        assert issue is None

    def test_char_map_used_for_span_mapping(self) -> None:
        """When char_map is present, spans are mapped through it."""
        block = _make_block(
            "hello", start_pos=100, end_pos=109,
            inline_content="**hello**",
            char_map=[2, 3, 4, 5, 6],
        )
        entry = _BatchEntry(block=block, batch_start=0, batch_end=5)
        match = _make_lt_match(offset=0, length=5)
        issue = _map_lt_match_to_issue(match, entry, 0, 5, "hello", "")

        assert issue is not None
        assert issue.span[0] == 102

    def test_char_map_end_of_block_uses_end_pos(self) -> None:
        """When end offset equals content length, end_pos is used directly."""
        block = _make_block(
            "hello", start_pos=100, end_pos=109,
            char_map=[2, 3, 4, 5, 6],
        )
        entry = _BatchEntry(block=block, batch_start=0, batch_end=5)
        match = _make_lt_match(offset=0, length=5)
        issue = _map_lt_match_to_issue(match, entry, 0, 5, "hello", "")

        assert issue is not None
        assert issue.span[1] == 109

    def test_max_five_suggestions(self) -> None:
        """Only the first 5 replacement values are kept."""
        block = _make_block("Test text.", start_pos=0)
        entry = _BatchEntry(block=block, batch_start=0, batch_end=10)
        replacements = [{"value": f"fix{i}"} for i in range(10)]
        match = _make_lt_match(offset=0, length=4, replacements=replacements)
        issue = _map_lt_match_to_issue(match, entry, 0, 4, "Test", "")
        assert issue is not None
        assert len(issue.suggestions) == 5

    def test_confidence_clamped(self) -> None:
        """Confidence values are clamped between 0.0 and 1.0."""
        block = _make_block("Test text.", start_pos=0)
        entry = _BatchEntry(block=block, batch_start=0, batch_end=10)
        match = _make_lt_match(offset=0, length=4, confidence=1.5)
        issue = _map_lt_match_to_issue(match, entry, 0, 4, "Test", "")
        assert issue is not None
        assert abs(issue.confidence - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# HTTP call — _call_languagetool
# ---------------------------------------------------------------------------


class TestCallLanguageTool:
    """Tests for _call_languagetool() graceful degradation."""

    @patch("app.services.analysis.languagetool_client.requests.post")
    def test_timeout_returns_empty(self, mock_post: MagicMock) -> None:
        """Timeout exceptions return an empty list."""
        mock_post.side_effect = requests.Timeout("timed out")
        result = _call_languagetool("test text")
        assert result == []

    @patch("app.services.analysis.languagetool_client.requests.post")
    def test_connection_error_returns_empty(self, mock_post: MagicMock) -> None:
        """Connection errors return an empty list."""
        mock_post.side_effect = requests.ConnectionError("refused")
        result = _call_languagetool("test text")
        assert result == []

    @patch("app.services.analysis.languagetool_client.requests.post")
    def test_request_exception_returns_empty(self, mock_post: MagicMock) -> None:
        """General request exceptions return an empty list."""
        mock_post.side_effect = requests.RequestException("error")
        result = _call_languagetool("test text")
        assert result == []

    @patch("app.services.analysis.languagetool_client.requests.post")
    def test_invalid_json_returns_empty(self, mock_post: MagicMock) -> None:
        """Invalid JSON responses return an empty list."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.side_effect = ValueError("bad json")
        mock_post.return_value = mock_resp
        result = _call_languagetool("test text")
        assert result == []

    @patch("app.services.analysis.languagetool_client.requests.post")
    def test_successful_call_returns_matches(self, mock_post: MagicMock) -> None:
        """A successful response returns the matches list."""
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "matches": [{"offset": 0, "length": 3, "message": "test"}],
        }
        mock_post.return_value = mock_resp
        result = _call_languagetool("test text")
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Skip rules
# ---------------------------------------------------------------------------


class TestSkipRules:
    """Tests for _LT_SKIP_RULES filtering."""

    def test_skip_rules_contains_expected_ids(self) -> None:
        """All expected FP-prone rule IDs are in the skip set."""
        assert "TYPOGRAPHICAL_APOSTROPHE" in _LT_SKIP_RULES
        assert "DASH_RULE" in _LT_SKIP_RULES
        assert "EN_QUOTES" in _LT_SKIP_RULES
        assert "MULTIPLICATION_SIGN" in _LT_SKIP_RULES
        assert "EN_UNPAIRED_BRACKETS" in _LT_SKIP_RULES

    def test_morfologik_not_in_skip_rules(self) -> None:
        """MORFOLOGIK is NOT blanket-skipped — handled by allowlist instead."""
        assert "MORFOLOGIK_RULE_EN_US" not in _LT_SKIP_RULES


# ---------------------------------------------------------------------------
# Domain-aware spelling allowlist
# ---------------------------------------------------------------------------


class TestSpellingAllowlist:
    """Tests for the _SPELLING_ALLOWLIST domain shield."""

    def test_loaded_from_yaml(self) -> None:
        """Allowlist is loaded from the YAML config file, not empty."""
        assert len(_SPELLING_ALLOWLIST) > 100

    def test_loader_returns_frozenset(self) -> None:
        """The loader function returns a frozenset."""
        result = _load_spelling_allowlist()
        assert isinstance(result, frozenset)
        assert len(result) > 100

    def test_known_terms_in_allowlist(self) -> None:
        """Key Red Hat / Kubernetes terms are in the allowlist."""
        for term in ("ostree", "stateroots", "kubelet", "buildah",
                     "podman", "coreos", "ansible", "etcd"):
            assert term in _SPELLING_ALLOWLIST, f"{term!r} missing"

    def test_english_words_not_in_allowlist(self) -> None:
        """Normal English words are not in the allowlist."""
        for word in ("application", "server", "the", "running"):
            assert word not in _SPELLING_ALLOWLIST

    @patch(
        "app.services.analysis.languagetool_client.open",
        side_effect=FileNotFoundError,
    )
    def test_missing_yaml_returns_empty(self, mock_open: MagicMock) -> None:
        """Missing YAML file returns empty frozenset (graceful degradation)."""
        result = _load_spelling_allowlist()
        assert result == frozenset()


# ---------------------------------------------------------------------------
# _should_skip_match guard logic
# ---------------------------------------------------------------------------


class TestShouldSkipMatch:
    """Tests for _should_skip_match() guard function."""

    def test_skip_rules_blocked(self) -> None:
        """Matches with IDs in _LT_SKIP_RULES are skipped."""
        assert _should_skip_match("EN_QUOTES", "text", 0, []) is True

    def test_inline_code_blocked(self) -> None:
        """Matches inside inline code ranges are skipped."""
        assert _should_skip_match("TEST", "word", 5, [(3, 10)]) is True

    def test_technical_content_blocked(self) -> None:
        """Matches on camelCase / paths are skipped."""
        assert _should_skip_match("TEST", "camelCase", 0, []) is True

    def test_morfologik_allowlisted_term_blocked(self) -> None:
        """MORFOLOGIK match on an allowlisted term is skipped."""
        assert _should_skip_match(
            "MORFOLOGIK_RULE_EN_US", "ostree", 0, [],
        ) is True

    def test_morfologik_allowlist_strips_punctuation(self) -> None:
        """Trailing punctuation is stripped before allowlist lookup."""
        assert _should_skip_match(
            "MORFOLOGIK_RULE_EN_US", "kubelet.", 0, [],
        ) is True

    def test_morfologik_allowlist_case_insensitive(self) -> None:
        """Allowlist lookup is case-insensitive."""
        assert _should_skip_match(
            "MORFOLOGIK_RULE_EN_US", "Podman", 0, [],
        ) is True

    def test_morfologik_genuine_typo_passes(self) -> None:
        """MORFOLOGIK match on a real typo is NOT skipped."""
        assert _should_skip_match(
            "MORFOLOGIK_RULE_EN_US", "aplication", 0, [],
        ) is False

    def test_normal_rule_passes(self) -> None:
        """A non-skipped, non-technical match passes through."""
        assert _should_skip_match(
            "GRAMMAR_RULE", "the the", 0, [],
        ) is False


# ---------------------------------------------------------------------------
# check_blocks() integration
# ---------------------------------------------------------------------------


class TestCheckBlocks:
    """Integration tests for the check_blocks() public API."""

    @patch("app.services.analysis.languagetool_client.Config")
    def test_disabled_returns_empty(self, mock_config: MagicMock) -> None:
        """When LANGUAGETOOL_ENABLED is False, returns empty list."""
        mock_config.LANGUAGETOOL_ENABLED = False
        block = _make_block("Some text.", block_type="paragraph")
        result = check_blocks([block])
        assert result == []

    @patch("app.services.analysis.languagetool_client._call_languagetool")
    @patch("app.services.analysis.languagetool_client.Config")
    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_skipped_rule_ids_filtered(
        self, mock_ranges: MagicMock,
        mock_config: MagicMock,
        mock_call: MagicMock,
    ) -> None:
        """Matches with rule IDs in _LT_SKIP_RULES are filtered out."""
        mock_config.LANGUAGETOOL_ENABLED = True
        mock_config.LANGUAGETOOL_DISABLED_RULES = ""
        mock_config.LANGUAGETOOL_DISABLED_CATEGORIES = ""
        mock_call.return_value = [
            _make_lt_match(
                offset=0, length=4, rule_id="TYPOGRAPHICAL_APOSTROPHE",
            ),
            _make_lt_match(
                offset=5, length=5, rule_id="REAL_GRAMMAR_RULE",
                category_id="GRAMMAR",
            ),
        ]
        block = _make_block("Test hello world.", block_type="paragraph")
        result = check_blocks([block])
        assert len(result) == 1
        assert result[0].rule_name == "lt_real_grammar_rule"

    @patch("app.services.analysis.languagetool_client._call_languagetool")
    @patch("app.services.analysis.languagetool_client.Config")
    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_technical_content_filtered(
        self, mock_ranges: MagicMock,
        mock_config: MagicMock,
        mock_call: MagicMock,
    ) -> None:
        """Matches on technical content (camelCase, paths) are filtered."""
        mock_config.LANGUAGETOOL_ENABLED = True
        mock_config.LANGUAGETOOL_DISABLED_RULES = ""
        mock_config.LANGUAGETOOL_DISABLED_CATEGORIES = ""
        # Match on "camelCase" which is technical content
        mock_call.return_value = [
            _make_lt_match(offset=0, length=9, rule_id="SPELLING"),
        ]
        block = _make_block("camelCase is used here.", block_type="paragraph")
        result = check_blocks([block])
        assert len(result) == 0

    @patch("app.services.analysis.languagetool_client._call_languagetool")
    @patch("app.services.analysis.languagetool_client.Config")
    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
    )
    def test_inline_code_guard_filters_match(
        self, mock_ranges: MagicMock,
        mock_config: MagicMock,
        mock_call: MagicMock,
    ) -> None:
        """Matches inside inline code ranges are filtered out."""
        mock_config.LANGUAGETOOL_ENABLED = True
        mock_config.LANGUAGETOOL_DISABLED_RULES = ""
        mock_config.LANGUAGETOOL_DISABLED_CATEGORIES = ""
        # Code range covers positions 5-12 within block content
        mock_ranges.return_value = [(5, 12)]
        mock_call.return_value = [
            _make_lt_match(offset=6, length=4, rule_id="SPELLING"),
        ]
        block = _make_block(
            "Some systemd service.", block_type="paragraph",
        )
        result = check_blocks([block])
        assert len(result) == 0

    @patch("app.services.analysis.languagetool_client._call_languagetool")
    @patch("app.services.analysis.languagetool_client.Config")
    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_no_prose_blocks_returns_empty(
        self, mock_ranges: MagicMock,
        mock_config: MagicMock,
        mock_call: MagicMock,
    ) -> None:
        """When only code blocks are present, returns empty list."""
        mock_config.LANGUAGETOOL_ENABLED = True
        block = _make_block("def foo(): pass", block_type="code_block")
        result = check_blocks([block])
        assert result == []
        mock_call.assert_not_called()

    @patch("app.services.analysis.languagetool_client._call_languagetool")
    @patch("app.services.analysis.languagetool_client.Config")
    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_cross_boundary_match_discarded(
        self, mock_ranges: MagicMock,
        mock_config: MagicMock,
        mock_call: MagicMock,
    ) -> None:
        """Matches spanning across a block boundary are discarded."""
        mock_config.LANGUAGETOOL_ENABLED = True
        mock_config.LANGUAGETOOL_DISABLED_RULES = ""
        mock_config.LANGUAGETOOL_DISABLED_CATEGORIES = ""
        block_a = _make_block("First block.", block_type="paragraph")
        block_b = _make_block(
            "Second block.", block_type="paragraph", start_pos=20,
        )
        # Match starts near end of first block, extends into separator
        mock_call.return_value = [
            _make_lt_match(offset=8, length=10, rule_id="GRAMMAR_RULE"),
        ]
        result = check_blocks([block_a, block_b])
        assert len(result) == 0

    @patch("app.services.analysis.languagetool_client._call_languagetool")
    @patch("app.services.analysis.languagetool_client.Config")
    @patch(
        "app.services.analysis.languagetool_client._compute_content_code_ranges",
        return_value=[],
    )
    def test_source_set_to_languagetool(
        self, mock_ranges: MagicMock,
        mock_config: MagicMock,
        mock_call: MagicMock,
    ) -> None:
        """Issues produced by check_blocks have source='languagetool'."""
        mock_config.LANGUAGETOOL_ENABLED = True
        mock_config.LANGUAGETOOL_DISABLED_RULES = ""
        mock_config.LANGUAGETOOL_DISABLED_CATEGORIES = ""
        mock_call.return_value = [
            _make_lt_match(
                offset=0, length=4, rule_id="TEST_RULE",
                category_id="GRAMMAR",
            ),
        ]
        block = _make_block("Test text here.", block_type="paragraph")
        result = check_blocks([block])
        assert len(result) == 1
        assert result[0].source == "languagetool"


# ---------------------------------------------------------------------------
# Prose block type filtering
# ---------------------------------------------------------------------------


class TestProseBlockTypes:
    """Tests for prose block type filtering."""

    def test_expected_types_included(self) -> None:
        """All 4 prose block types are in the filter set."""
        assert "paragraph" in _PROSE_BLOCK_TYPES
        assert "heading" in _PROSE_BLOCK_TYPES
        assert "list_item_ordered" in _PROSE_BLOCK_TYPES
        assert "list_item_unordered" in _PROSE_BLOCK_TYPES

    def test_non_prose_types_excluded(self) -> None:
        """Code blocks, tables, and admonitions are not prose types."""
        assert "code_block" not in _PROSE_BLOCK_TYPES
        assert "table" not in _PROSE_BLOCK_TYPES
        assert "admonition" not in _PROSE_BLOCK_TYPES


# ---------------------------------------------------------------------------
# Picky-mode level parameter
# ---------------------------------------------------------------------------


class TestPickyLevelParameter:
    """Tests for the ``level`` parameter in _call_languagetool."""

    @patch("app.services.analysis.languagetool_client.requests.post")
    @patch("app.services.analysis.languagetool_client.Config")
    def test_picky_level_sent_in_payload(
        self, mock_config: MagicMock, mock_post: MagicMock,
    ) -> None:
        """Picky level value is included in the HTTP payload."""
        mock_config.LANGUAGETOOL_URL = "http://localhost:8010"
        mock_config.LANGUAGETOOL_TIMEOUT = 5
        mock_config.LANGUAGETOOL_LEVEL = "picky"
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"matches": []},
        )
        mock_post.return_value.raise_for_status = MagicMock()

        _call_languagetool("Test text.")

        called_data = mock_post.call_args[1].get("data") or mock_post.call_args[0][1] if len(mock_post.call_args[0]) > 1 else mock_post.call_args[1].get("data", {})
        assert called_data["level"] == "picky"

    @patch("app.services.analysis.languagetool_client.requests.post")
    @patch("app.services.analysis.languagetool_client.Config")
    def test_default_level_sent_in_payload(
        self, mock_config: MagicMock, mock_post: MagicMock,
    ) -> None:
        """Default level value is included in the HTTP payload."""
        mock_config.LANGUAGETOOL_URL = "http://localhost:8010"
        mock_config.LANGUAGETOOL_TIMEOUT = 5
        mock_config.LANGUAGETOOL_LEVEL = "default"
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"matches": []},
        )
        mock_post.return_value.raise_for_status = MagicMock()

        _call_languagetool("Test text.")

        called_data = mock_post.call_args[1].get("data") or mock_post.call_args[0][1] if len(mock_post.call_args[0]) > 1 else mock_post.call_args[1].get("data", {})
        assert called_data["level"] == "default"


# ---------------------------------------------------------------------------
# Confidence and Hint-type filtering
# ---------------------------------------------------------------------------


class TestConfidenceFiltering:
    """Tests for confidence and Hint-type FP guard in _should_skip_match."""

    def test_hint_confused_words_skipped(self) -> None:
        """CONFUSED_WORDS + typeName='Hint' is skipped."""
        assert _should_skip_match(
            "CONFUSION_RULE", "then", 0, [],
            lt_category="CONFUSED_WORDS", confidence=0.95,
            match_type="Hint",
        ) is True

    def test_other_confused_words_passes(self) -> None:
        """CONFUSED_WORDS + typeName='Other' passes through."""
        assert _should_skip_match(
            "CONFUSION_RULE", "then", 0, [],
            lt_category="CONFUSED_WORDS", confidence=0.95,
            match_type="Other",
        ) is False

    def test_hint_style_skipped(self) -> None:
        """STYLE + typeName='Hint' is skipped."""
        assert _should_skip_match(
            "STYLE_RULE", "very", 0, [],
            lt_category="STYLE", confidence=0.95,
            match_type="Hint",
        ) is True

    def test_hint_grammar_not_gated(self) -> None:
        """GRAMMAR + typeName='Hint' passes (GRAMMAR not in gated set)."""
        assert _should_skip_match(
            "GRAMMAR_RULE", "the the", 0, [],
            lt_category="GRAMMAR", confidence=0.95,
            match_type="Hint",
        ) is False

    def test_empty_match_type_passes(self) -> None:
        """Missing typeName (empty string) passes through."""
        assert _should_skip_match(
            "CONFUSION_RULE", "then", 0, [],
            lt_category="CONFUSED_WORDS", confidence=0.95,
            match_type="",
        ) is False

    @patch("app.services.analysis.languagetool_client.Config")
    def test_filter_hints_disabled(self, mock_config: MagicMock) -> None:
        """Hint matches pass when LANGUAGETOOL_FILTER_HINTS is False."""
        mock_config.LANGUAGETOOL_FILTER_HINTS = False
        mock_config.LANGUAGETOOL_CONFIDENCE_THRESHOLD = 0.85
        result = _should_skip_match(
            "CONFUSION_RULE", "then", 0, [],
            lt_category="CONFUSED_WORDS", confidence=0.95,
            match_type="Hint",
        )
        assert result is False

    def test_confidence_fallback_low(self) -> None:
        """Low confidence in gated category is skipped."""
        assert _should_skip_match(
            "CONFUSION_RULE", "then", 0, [],
            lt_category="CONFUSED_WORDS", confidence=0.50,
            match_type="Other",
        ) is True

    def test_confidence_fallback_boundary(self) -> None:
        """Confidence exactly at threshold passes (strict <)."""
        assert _should_skip_match(
            "CONFUSION_RULE", "then", 0, [],
            lt_category="CONFUSED_WORDS", confidence=0.85,
            match_type="Other",
        ) is False


# ---------------------------------------------------------------------------
# Picky-mode skip rules
# ---------------------------------------------------------------------------


class TestPickyModeSkipRules:
    """Tests for picky-mode rule IDs in _LT_SKIP_RULES."""

    _PICKY_RULES = [
        "ARTICLE_MISSING",
        "COMMA_COMPOUND_SENTENCE",
        "COMMA_COMPOUND_SENTENCE_2",
        "WHO_WHOM",
        "CONSECUTIVE_SPACES",
        "UNLIKELY_OPENING_PUNCTUATION",
        "SENTENCE_WHITESPACE",
        "EN_COMPOUNDS",
        "WORD_CONTAINS_UNDERSCORE",
    ]

    @pytest.mark.parametrize("rule_id", _PICKY_RULES)
    def test_picky_fp_rules_in_skip_set(self, rule_id: str) -> None:
        """Each picky FP rule is present in _LT_SKIP_RULES."""
        assert rule_id in _LT_SKIP_RULES

    def test_en_compounds_skipped(self) -> None:
        """EN_COMPOUNDS match is skipped by _should_skip_match."""
        assert _should_skip_match("EN_COMPOUNDS", "setup", 0, []) is True

    def test_word_contains_underscore_skipped(self) -> None:
        """WORD_CONTAINS_UNDERSCORE match is skipped."""
        assert _should_skip_match(
            "WORD_CONTAINS_UNDERSCORE", "my_var", 0, [],
        ) is True

    def test_total_skip_rules_count(self) -> None:
        """Total skip rules = 27 (18 existing + 9 picky)."""
        assert len(_LT_SKIP_RULES) == 27

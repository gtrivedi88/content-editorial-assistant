"""Tests for LLM response parsers.

Validates JSON extraction, code-fence stripping, truncated-response
salvaging, field normalization, suggestion parsing, and judge
response parsing from raw LLM output strings.
"""

import json
import logging
from unittest.mock import patch

import pytest

from app.llm.parser import (
    _normalize_issue_fields,
    _strip_code_fences,
    parse_analysis_response,
    parse_judge_response,
    parse_suggestion_response,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# _strip_code_fences
# ---------------------------------------------------------------------------


class TestStripCodeFences:
    """Tests for _strip_code_fences() helper."""

    def test_strips_json_code_fence(self) -> None:
        """Removes ```json and closing ``` from LLM output."""
        raw = '```json\n[{"key": "value"}]\n```'
        result = _strip_code_fences(raw)
        assert result == '[{"key": "value"}]'

    def test_strips_bare_code_fence(self) -> None:
        """Removes bare ``` fences without a language tag."""
        raw = '```\n{"key": "value"}\n```'
        result = _strip_code_fences(raw)
        assert result == '{"key": "value"}'

    def test_no_fences_returns_stripped(self) -> None:
        """Text without code fences is returned with whitespace trimmed."""
        raw = '  [{"key": "value"}]  '
        result = _strip_code_fences(raw)
        assert result == '[{"key": "value"}]'

    def test_only_opening_fence_stripped(self) -> None:
        """Only a leading fence is stripped when no closing fence exists."""
        raw = '```json\n[{"key": "value"}]'
        result = _strip_code_fences(raw)
        assert result == '[{"key": "value"}]'


# ---------------------------------------------------------------------------
# parse_analysis_response
# ---------------------------------------------------------------------------


class TestParseAnalysisResponse:
    """Tests for parse_analysis_response()."""

    def test_valid_json_array(self) -> None:
        """Parses a well-formed JSON array of issues."""
        issues = [
            {
                "flagged_text": "was deleted",
                "message": "Use active voice.",
                "severity": "medium",
                "category": "style",
                "confidence": 0.9,
            }
        ]
        result = parse_analysis_response(json.dumps(issues))
        assert len(result) == 1
        assert result[0]["flagged_text"] == "was deleted"
        assert result[0]["source"] == "llm"

    def test_code_fenced_json(self) -> None:
        """Parses JSON wrapped in ```json code fences."""
        issues = [
            {
                "flagged_text": "inputted",
                "message": "Use 'entered' instead.",
                "severity": "high",
                "category": "grammar",
                "confidence": 0.95,
            }
        ]
        raw = f"```json\n{json.dumps(issues)}\n```"
        result = parse_analysis_response(raw)
        assert len(result) == 1
        assert result[0]["severity"] == "high"
        assert result[0]["source"] == "llm"

    def test_wrapper_object_with_issues_key(self) -> None:
        """Extracts issues from a wrapper dict with an 'issues' key."""
        wrapper = {
            "issues": [
                {
                    "flagged_text": "click on",
                    "message": "Use 'click' without 'on'.",
                    "severity": "low",
                    "category": "style",
                    "confidence": 0.85,
                }
            ]
        }
        result = parse_analysis_response(json.dumps(wrapper))
        assert len(result) == 1
        assert result[0]["flagged_text"] == "click on"

    def test_empty_input_returns_empty_list(self) -> None:
        """Empty string input returns an empty list."""
        result = parse_analysis_response("")
        assert result == []

    def test_invalid_json_returns_empty_list(self) -> None:
        """Completely invalid JSON returns an empty list."""
        result = parse_analysis_response("this is not json at all")
        assert result == []

    def test_missing_required_field_skips_issue(self) -> None:
        """Issues missing required fields are silently dropped."""
        issues = [
            {
                "flagged_text": "valid issue",
                "message": "A message.",
                "severity": "medium",
                "category": "style",
                "confidence": 0.9,
            },
            {
                # Missing 'message' field
                "flagged_text": "incomplete",
                "severity": "low",
                "category": "style",
                "confidence": 0.9,
            },
        ]
        result = parse_analysis_response(json.dumps(issues))
        assert len(result) == 1
        assert result[0]["flagged_text"] == "valid issue"

    @patch("app.llm.parser.Config")
    def test_confidence_below_threshold_filtered(
        self, mock_config: object,
    ) -> None:
        """Issues below the confidence threshold are filtered out."""
        mock_config.LLM_CONFIDENCE_THRESHOLD = 0.8
        issues = [
            {
                "flagged_text": "low confidence",
                "message": "Uncertain issue.",
                "severity": "medium",
                "category": "style",
                "confidence": 0.5,
            },
            {
                "flagged_text": "high confidence",
                "message": "Certain issue.",
                "severity": "medium",
                "category": "style",
                "confidence": 0.9,
            },
        ]
        result = parse_analysis_response(json.dumps(issues))
        assert len(result) == 1
        assert result[0]["flagged_text"] == "high confidence"

    def test_truncated_json_array_salvaged(self) -> None:
        """Complete objects are salvaged from a truncated JSON array."""
        # Build a truncated response: first issue complete, second cut off
        raw = (
            '[{"flagged_text": "word", "message": "Fix it.", '
            '"severity": "medium", "category": "style", "confidence": 0.9}, '
            '{"flagged_text": "trunc'
        )
        result = parse_analysis_response(raw)
        assert len(result) == 1
        assert result[0]["flagged_text"] == "word"

    def test_trailing_comma_handled(self) -> None:
        """Trailing commas in JSON are cleaned before parsing."""
        raw = '[{"flagged_text": "text", "message": "msg", "severity": "medium", "category": "style", "confidence": 0.9,}]'
        result = parse_analysis_response(raw)
        assert len(result) == 1

    def test_source_stamp_always_llm(self) -> None:
        """Every returned issue has source='llm'."""
        issues = [
            {
                "flagged_text": "test",
                "message": "Test message.",
                "severity": "low",
                "category": "grammar",
                "confidence": 0.95,
            }
        ]
        result = parse_analysis_response(json.dumps(issues))
        assert all(i["source"] == "llm" for i in result)

    def test_empty_flagged_text_allowed_for_global_issues(self) -> None:
        """Empty flagged_text is allowed for document-level global issues."""
        issues = [
            {
                "flagged_text": "",
                "message": "Document tone is inconsistent.",
                "severity": "medium",
                "category": "style",
                "confidence": 0.85,
            }
        ]
        result = parse_analysis_response(json.dumps(issues))
        assert len(result) == 1
        assert result[0]["flagged_text"] == ""


# ---------------------------------------------------------------------------
# _normalize_issue_fields
# ---------------------------------------------------------------------------


class TestNormalizeIssueFields:
    """Tests for _normalize_issue_fields() in-place normalizer."""

    def test_invalid_severity_defaults_to_medium(self) -> None:
        """Unknown severity values default to 'medium'."""
        item: dict = {
            "flagged_text": "test",
            "message": "msg",
            "severity": "CRITICAL",
            "category": "style",
        }
        _normalize_issue_fields(item)
        assert item["severity"] == "medium"

    def test_valid_severity_lowercased(self) -> None:
        """Valid severity values are lowercased."""
        item: dict = {
            "flagged_text": "test",
            "message": "msg",
            "severity": "HIGH",
            "category": "style",
        }
        _normalize_issue_fields(item)
        assert item["severity"] == "high"

    def test_invalid_category_defaults_to_style(self) -> None:
        """Unknown category values default to 'style'."""
        item: dict = {
            "flagged_text": "test",
            "message": "msg",
            "severity": "low",
            "category": "UNKNOWN_CAT",
        }
        _normalize_issue_fields(item)
        assert item["category"] == "style"

    def test_suggestions_string_wrapped_in_list(self) -> None:
        """A single string suggestion is wrapped into a list."""
        item: dict = {
            "flagged_text": "test",
            "message": "msg",
            "severity": "low",
            "category": "style",
            "suggestions": "Use this instead.",
        }
        _normalize_issue_fields(item)
        assert item["suggestions"] == ["Use this instead."]

    def test_missing_sentence_defaults_to_flagged_text(self) -> None:
        """Missing sentence field defaults to flagged_text."""
        item: dict = {
            "flagged_text": "the word",
            "message": "msg",
            "severity": "low",
            "category": "style",
        }
        _normalize_issue_fields(item)
        assert item["sentence"] == "the word"

    def test_invalid_sentence_index_defaults_to_zero(self) -> None:
        """Non-numeric sentence_index defaults to 0."""
        item: dict = {
            "flagged_text": "test",
            "message": "msg",
            "severity": "low",
            "category": "style",
            "sentence_index": "not_a_number",
        }
        _normalize_issue_fields(item)
        assert item["sentence_index"] == 0

    def test_invalid_confidence_defaults_to_0_8(self) -> None:
        """Non-numeric confidence defaults to 0.8."""
        item: dict = {
            "flagged_text": "test",
            "message": "msg",
            "severity": "low",
            "category": "style",
            "confidence": "invalid",
        }
        _normalize_issue_fields(item)
        assert item["confidence"] == 0.8


# ---------------------------------------------------------------------------
# parse_suggestion_response
# ---------------------------------------------------------------------------


class TestParseSuggestionResponse:
    """Tests for parse_suggestion_response()."""

    def test_valid_suggestion(self) -> None:
        """Parses a well-formed suggestion response."""
        raw = json.dumps({
            "rewritten_text": "Click the button.",
            "explanation": "Removed 'on' per IBM Style Guide.",
            "confidence": 0.92,
        })
        result = parse_suggestion_response(raw)
        assert result["rewritten_text"] == "Click the button."
        assert result["explanation"] == "Removed 'on' per IBM Style Guide."
        assert result["confidence"] == 0.92

    def test_missing_rewritten_text_returns_error(self) -> None:
        """Returns an error dict when rewritten_text is absent."""
        raw = json.dumps({
            "explanation": "Some explanation.",
            "confidence": 0.9,
        })
        result = parse_suggestion_response(raw)
        assert "error" in result

    def test_invalid_json_returns_error(self) -> None:
        """Returns an error dict for unparseable input."""
        result = parse_suggestion_response("not valid json")
        assert "error" in result

    def test_code_fenced_suggestion(self) -> None:
        """Parses suggestion wrapped in code fences."""
        payload = {
            "rewritten_text": "Enter the data.",
            "explanation": "Use 'enter' not 'input'.",
            "confidence": 0.88,
        }
        raw = f"```json\n{json.dumps(payload)}\n```"
        result = parse_suggestion_response(raw)
        assert result["rewritten_text"] == "Enter the data."

    def test_missing_confidence_defaults_to_0_8(self) -> None:
        """Missing confidence field defaults to 0.8."""
        raw = json.dumps({
            "rewritten_text": "Some text.",
            "explanation": "Explanation.",
        })
        result = parse_suggestion_response(raw)
        assert result["confidence"] == 0.8

    def test_alternate_key_suggestion(self) -> None:
        """Accepts 'suggestion' as alternate key for rewritten_text."""
        raw = json.dumps({
            "suggestion": "Click the button.",
            "explanation": "Removed 'on'.",
            "confidence": 0.9,
        })
        result = parse_suggestion_response(raw)
        assert result["rewritten_text"] == "Click the button."
        assert "error" not in result

    def test_alternate_key_rewrite(self) -> None:
        """Accepts 'rewrite' as alternate key for rewritten_text."""
        raw = json.dumps({
            "rewrite": "Enter the data.",
            "explanation": "Changed verb.",
        })
        result = parse_suggestion_response(raw)
        assert result["rewritten_text"] == "Enter the data."
        assert "error" not in result

    def test_alternate_key_corrected_text(self) -> None:
        """Accepts 'corrected_text' as alternate key for rewritten_text."""
        raw = json.dumps({
            "corrected_text": "The server restarts.",
            "explanation": "Active voice.",
            "confidence": 0.85,
        })
        result = parse_suggestion_response(raw)
        assert result["rewritten_text"] == "The server restarts."
        assert "error" not in result

    def test_primary_key_preferred_over_alternate(self) -> None:
        """When both rewritten_text and an alternate key exist, primary wins."""
        raw = json.dumps({
            "rewritten_text": "Primary text.",
            "suggestion": "Alternate text.",
            "explanation": "Test.",
        })
        result = parse_suggestion_response(raw)
        assert result["rewritten_text"] == "Primary text."


# ---------------------------------------------------------------------------
# parse_judge_response
# ---------------------------------------------------------------------------


class TestParseJudgeResponse:
    """Tests for parse_judge_response()."""

    def test_valid_judge_response(self) -> None:
        """Parses keep and drop index arrays correctly."""
        raw = json.dumps({"keep": [0, 2], "drop": [1]})
        keep, drop = parse_judge_response(raw, total_issues=3)
        assert 0 in keep
        assert 2 in keep
        assert 1 in drop

    def test_invalid_json_fails_open(self) -> None:
        """Invalid JSON causes fail-open: all issues kept."""
        keep, drop = parse_judge_response("not json", total_issues=3)
        assert keep == [0, 1, 2]
        assert drop == []

    def test_unmentioned_indices_kept_by_default(self) -> None:
        """Indices not in keep or drop are added to keep."""
        raw = json.dumps({"keep": [0], "drop": [2]})
        keep, drop = parse_judge_response(raw, total_issues=4)
        # Index 1 and 3 are not mentioned, should be in keep
        assert 1 in keep
        assert 3 in keep
        assert 0 in keep
        assert 2 in drop

    def test_out_of_range_indices_ignored(self) -> None:
        """Indices outside [0, total_issues) are silently ignored."""
        raw = json.dumps({"keep": [0, 99], "drop": [-1, 1]})
        keep, drop = parse_judge_response(raw, total_issues=2)
        assert 0 in keep
        assert 99 not in keep
        assert -1 not in drop
        assert 1 in drop

    def test_empty_input_fails_open(self) -> None:
        """Empty string causes fail-open."""
        keep, drop = parse_judge_response("", total_issues=2)
        assert keep == [0, 1]
        assert drop == []

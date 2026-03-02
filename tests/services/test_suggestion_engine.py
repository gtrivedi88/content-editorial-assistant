"""Tests for the suggestion engine three-tier pipeline.

Validates the cache-hit path, deterministic replacement path, LLM fallback
path, instruction-suggestion detection, and error handling for missing
sessions and issues.
"""

import logging
import uuid
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
from app.models.schemas import (
    AnalyzeResponse,
    IssueResponse,
    ReportResponse,
    ScoreResponse,
)
from app.services.suggestions.engine import (
    _extract_alternative_from_message,
    _is_instruction_suggestion,
    _is_simple_replacement,
    _match_case_engine,
    get_suggestion,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_issue(
    issue_id: str | None = None,
    source: str = "deterministic",
    suggestions: list[str] | None = None,
    rule_name: str = "passive_voice",
    flagged_text: str = "was restarted",
    message: str = "Consider using active voice.",
) -> IssueResponse:
    """Build a minimal IssueResponse for engine tests.

    Args:
        issue_id: Optional issue identifier; generated if not provided.
        source: Issue source ("deterministic" or "llm").
        suggestions: Replacement suggestions list.
        rule_name: Rule identifier string.
        flagged_text: Text span that was flagged.
        message: Human-readable issue message.

    Returns:
        A fully populated IssueResponse.
    """
    return IssueResponse(
        id=issue_id or str(uuid.uuid4()),
        source=source,
        category=IssueCategory.STYLE,
        rule_name=rule_name,
        flagged_text=flagged_text,
        message=message,
        suggestions=suggestions if suggestions is not None else ["restarted"],
        severity=IssueSeverity.MEDIUM,
        sentence="The server was restarted by the administrator.",
        sentence_index=0,
        span=[11, 24],
        style_guide_citation="IBM Style Guide, Section 5.1",
        confidence=1.0,
        status=IssueStatus.OPEN,
    )


def _make_response(issues: list[IssueResponse] | None = None) -> AnalyzeResponse:
    """Build a minimal AnalyzeResponse containing the given issues.

    Args:
        issues: Issues to include; defaults to a single passive_voice issue.

    Returns:
        A fully populated AnalyzeResponse.
    """
    if issues is None:
        issues = [_make_issue()]

    score = ScoreResponse(
        score=85,
        color="#06c",
        label="Good",
        total_issues=len(issues),
        category_counts={"style": len(issues)},
        compliance={},
    )
    report = ReportResponse(
        word_count=50,
        sentence_count=3,
        paragraph_count=1,
        avg_words_per_sentence=16.67,
        avg_syllables_per_word=1.5,
    )
    return AnalyzeResponse(
        session_id="",
        issues=issues,
        score=score,
        report=report,
        partial=False,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGetSuggestion:
    """Tests for the get_suggestion() three-tier pipeline."""

    def test_cache_hit_returns_cached_result(self, app: Flask) -> None:
        """Tier 1: when a cached suggestion exists, return it immediately.

        The session store should be consulted first. If a cached suggestion
        is found, the engine should return it without querying deterministic
        or LLM paths.
        """
        issue = _make_issue(issue_id="issue-cached")
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            cached = {
                "rewritten_text": "cached rewrite",
                "explanation": "from cache",
                "confidence": 1.0,
            }
            store.cache_suggestion(session_id, "issue-cached", cached)

            result = get_suggestion(session_id, "issue-cached")

        assert result["rewritten_text"] == "cached rewrite"
        assert result["explanation"] == "from cache"

    def test_session_not_found_returns_error(self, app: Flask) -> None:
        """When the session ID does not exist, return an error dict.

        The engine should handle missing sessions gracefully by returning
        a dict with an ``error`` key.
        """
        with app.app_context():
            result = get_suggestion("nonexistent-session-id", "any-issue-id")

        assert "error" in result
        assert "not found" in result["error"].lower() or "expired" in result["error"].lower()

    def test_issue_not_found_returns_error(self, app: Flask) -> None:
        """When the issue ID does not exist in the session, return an error.

        A valid session with no matching issue should produce an error
        dict with a descriptive message.
        """
        issue = _make_issue(issue_id="existing-issue")
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            result = get_suggestion(session_id, "nonexistent-issue-id")

        assert "error" in result
        assert "not found" in result["error"].lower()

    def test_simple_deterministic_replacement(self, app: Flask) -> None:
        """Tier 2: a single non-instruction deterministic suggestion is returned directly.

        When the issue has exactly one suggestion from a deterministic
        source and the suggestion is not instruction-style, the engine
        should return a deterministic result with confidence 1.0.
        """
        issue = _make_issue(
            issue_id="issue-simple",
            source="deterministic",
            suggestions=["use"],
            flagged_text="utilize",
            message="Use 'use' instead of 'utilize'.",
        )
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            result = get_suggestion(session_id, "issue-simple")

        assert result["rewritten_text"] == "use"
        assert result["confidence"] == 1.0

    def test_simple_replacement_is_cached(self, app: Flask) -> None:
        """Tier 2 results are cached in the session suggestion cache.

        After a deterministic suggestion is built, subsequent calls for
        the same issue should hit the cache (Tier 1).
        """
        issue = _make_issue(
            issue_id="issue-cache-me",
            source="deterministic",
            suggestions=["use"],
            flagged_text="utilize",
            message="Use 'use' instead of 'utilize'.",
        )
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            first_result = get_suggestion(session_id, "issue-cache-me")
            cached = store.get_cached_suggestion(session_id, "issue-cache-me")

        assert cached is not None
        assert cached["rewritten_text"] == first_result["rewritten_text"]

    @patch("app.services.suggestions.engine.LLMClient")
    def test_instruction_suggestion_routes_to_llm(
        self, mock_llm_cls: MagicMock, app: Flask
    ) -> None:
        """Instruction-style suggestions bypass deterministic and call LLM.

        When the single suggestion starts with an imperative prefix like
        "Rewrite...", the engine should treat it as an instruction and
        attempt the LLM path. With LLM mocked as unavailable, the
        fallback error dict should be returned.
        """
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        mock_llm_cls.return_value = mock_client

        issue = _make_issue(
            issue_id="issue-instruction",
            source="deterministic",
            suggestions=["Rewrite using active voice"],
            flagged_text="was restarted",
            message="Consider using active voice.",
        )
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            result = get_suggestion(session_id, "issue-instruction")

        # LLM not available -> fallback with error and suggestions
        assert "error" in result
        assert "suggestions" in result
        assert result["suggestions"] == ["Rewrite using active voice"]

    @patch("app.services.suggestions.engine.LLMClient")
    def test_llm_source_routes_to_llm(
        self, mock_llm_cls: MagicMock, app: Flask
    ) -> None:
        """Issues from the LLM source always route to the LLM tier.

        Even with a single suggestion, LLM-sourced issues should not
        use the deterministic path since they are not word-swap rules.
        """
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        mock_llm_cls.return_value = mock_client

        issue = _make_issue(
            issue_id="issue-llm-source",
            source="llm",
            suggestions=["improved text"],
            flagged_text="some text",
            message="Style improvement suggestion.",
        )
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            result = get_suggestion(session_id, "issue-llm-source")

        # LLM not available in test -> fallback
        assert "error" in result
        assert "suggestions" in result

    @patch("app.services.suggestions.engine.LLMClient")
    def test_multiple_suggestions_route_to_llm(
        self, mock_llm_cls: MagicMock, app: Flask
    ) -> None:
        """Issues with multiple deterministic suggestions route to LLM.

        The simple replacement path requires exactly one suggestion.
        Multiple suggestions should fall through to the LLM tier.
        """
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        mock_llm_cls.return_value = mock_client

        issue = _make_issue(
            issue_id="issue-multi",
            source="deterministic",
            suggestions=["option A", "option B"],
            flagged_text="ambiguous",
            message="Multiple replacements possible.",
        )
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            result = get_suggestion(session_id, "issue-multi")

        # LLM not available -> fallback with suggestions list
        assert "error" in result
        assert set(result["suggestions"]) == {"option A", "option B"}

    @patch("app.services.suggestions.engine.LLMClient")
    def test_llm_success_returns_rewrite(
        self, mock_llm_cls: MagicMock, app: Flask
    ) -> None:
        """Tier 3: when the LLM succeeds, its result is returned and cached.

        The LLM client should be called with the correct parameters
        when the deterministic path is not applicable. A successful
        LLM response should be returned to the caller.
        """
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.suggest.return_value = {
            "rewritten_text": "The administrator restarted the server.",
            "explanation": "Active voice is preferred.",
            "confidence": 0.9,
        }
        mock_llm_cls.return_value = mock_client

        issue = _make_issue(
            issue_id="issue-llm-ok",
            source="deterministic",
            suggestions=["Rewrite in active voice"],
            flagged_text="was restarted",
            message="Consider using active voice.",
        )
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            result = get_suggestion(session_id, "issue-llm-ok")

        assert result["rewritten_text"] == "The administrator restarted the server."
        assert result["confidence"] == 0.9
        mock_client.suggest.assert_called_once()


class TestIsInstructionSuggestion:
    """Tests for _is_instruction_suggestion() detection."""

    @pytest.mark.parametrize("text", [
        "Rewrite this sentence in active voice.",
        "Consider rephrasing for clarity.",
        "Rephrase to avoid passive construction.",
        "Restructure the paragraph.",
        "Replace 'the previous step' with a specific reference.",
        "Remove bold markup: use `curl` instead of **`curl`**.",
        "Break the sentence into shorter ones.",
        "Combine these two sentences.",
        "Simplify the wording.",
        "Avoid contractions in technical writing.",
        "Insert a space between the punctuation and the next word.",
        "Add a comma before 'and' in a series of three or more items.",
        "Move the punctuation mark inside the quotes.",
        "Split into two or more shorter sentences.",
        "Write 'backup' without the hyphen.",
        "Do not use abbreviations in headings.",
        "Ensure consistent capitalization throughout.",
        "Verify that the link text is descriptive.",
        "Check the spelling of technical terms.",
        "Make the sentence more concise.",
        "Use a gerund instead of a noun clause.",
    ])
    def test_instruction_prefixes_detected(self, text: str) -> None:
        """Known instruction prefixes should be detected as instructions.

        Each string starting with a recognized imperative prefix should
        return True, routing the suggestion to the LLM tier.
        """
        assert _is_instruction_suggestion(text) is True

    @pytest.mark.parametrize("text", [
        "use",
        "should not",
        "Red Hat Enterprise Linux",
        "the server restarted",
        "data are",
    ])
    def test_direct_replacements_not_detected(self, text: str) -> None:
        """Direct replacement strings should not be detected as instructions.

        Simple word or phrase replacements should return False, allowing
        the deterministic path to handle them.
        """
        assert _is_instruction_suggestion(text) is False


class TestIsSimpleReplacement:
    """Tests for _is_simple_replacement() logic."""

    def test_single_deterministic_non_instruction(self) -> None:
        """A deterministic issue with one non-instruction suggestion is simple.

        This is the canonical case for Tier 2 deterministic replacement.
        """
        issue = _make_issue(
            source="deterministic",
            suggestions=["use"],
        )
        assert _is_simple_replacement(issue) is True

    def test_llm_source_not_simple(self) -> None:
        """LLM-sourced issues are never simple replacements.

        Regardless of the suggestion count or content, LLM issues
        should not use the deterministic path.
        """
        issue = _make_issue(
            source="llm",
            suggestions=["use"],
        )
        assert _is_simple_replacement(issue) is False

    def test_instruction_suggestion_not_simple(self) -> None:
        """A deterministic issue with an instruction suggestion is not simple.

        Instruction-style suggestions require the LLM for a proper
        rewrite, so they should not use the deterministic path.
        """
        issue = _make_issue(
            source="deterministic",
            suggestions=["Rewrite in active voice"],
        )
        assert _is_simple_replacement(issue) is False

    def test_multiple_suggestions_not_simple(self) -> None:
        """Deterministic issues with multiple suggestions are not simple.

        The simple replacement path requires exactly one suggestion.
        """
        issue = _make_issue(
            source="deterministic",
            suggestions=["option A", "option B"],
        )
        assert _is_simple_replacement(issue) is False


class TestExtractAlternativeFromMessage:
    """Tests for _extract_alternative_from_message() message parsing (Fix 3)."""

    def test_use_pattern(self) -> None:
        """Extracts alternative from \"Use 'X' instead\" pattern."""
        result = _extract_alternative_from_message("Use 'inactive' instead of 'quiescent'.")
        assert result == "inactive"

    def test_change_to_pattern(self) -> None:
        """Extracts alternative from \"Change to 'X'\" pattern."""
        result = _extract_alternative_from_message("Change to 'is in' for better readability.")
        assert result == "is in"

    def test_replace_with_pattern(self) -> None:
        """Extracts alternative from \"Replace with 'X'\" pattern."""
        result = _extract_alternative_from_message("Replace with 'Kerberos-aware' in this context.")
        assert result == "Kerberos-aware"

    def test_refer_to_as_pattern(self) -> None:
        """Extracts alternative from \"Refer to ... as 'X'\" pattern."""
        result = _extract_alternative_from_message(
            "Refer to such applications as 'Kerberos-enabled'."
        )
        assert result == "Kerberos-enabled"

    def test_no_alternative_returns_none(self) -> None:
        """Messages without quoted alternatives return None."""
        result = _extract_alternative_from_message(
            "Do not use 'please' in technical documentation."
        )
        assert result is None

    def test_empty_message_returns_none(self) -> None:
        """Empty message returns None."""
        result = _extract_alternative_from_message("")
        assert result is None

    def test_backtick_use_pattern(self) -> None:
        """Extracts alternative from backtick-quoted 'Use `X` instead' pattern."""
        result = _extract_alternative_from_message(
            "Remove bold markup: use `curl` instead of **`curl`**."
        )
        assert result == "curl"

    def test_backtick_change_to_pattern(self) -> None:
        """Extracts alternative from backtick-quoted 'Change to `X`' pattern."""
        result = _extract_alternative_from_message("Change to `oc` for the CLI tool.")
        assert result == "oc"

    def test_backtick_replace_with_pattern(self) -> None:
        """Extracts alternative from backtick-quoted 'Replace with `X`' pattern."""
        result = _extract_alternative_from_message("Replace with `kubectl` in this context.")
        assert result == "kubectl"


class TestMatchCaseEngine:
    """Tests for _match_case_engine() case matching (Fix 3)."""

    def test_uppercase_flagged_capitalizes_replacement(self) -> None:
        """Replacement is capitalized when flagged text starts uppercase."""
        result = _match_case_engine("is in", "Resides")
        assert result == "Is in"

    def test_lowercase_flagged_preserves_replacement(self) -> None:
        """Replacement is unchanged when flagged text starts lowercase."""
        result = _match_case_engine("is in", "resides")
        assert result == "is in"

    def test_empty_flagged_preserves_replacement(self) -> None:
        """Empty flagged text does not modify replacement."""
        result = _match_case_engine("is in", "")
        assert result == "is in"

    def test_empty_replacement_returns_empty(self) -> None:
        """Empty replacement returns empty string."""
        result = _match_case_engine("", "Resides")
        assert result == ""


class TestLlmUnavailableFallback:
    """Tests for LLM-unavailable fallback path with message extraction (Fix 3)."""

    @patch("app.services.suggestions.engine.LLMClient")
    def test_fallback_extracts_from_message(
        self, mock_llm_cls: MagicMock, app: Flask,
    ) -> None:
        """When LLM is unavailable and suggestions empty, extract from message.

        Issues whose messages contain quoted alternatives should get a
        rewritten_text response even without LLM access.
        """
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        mock_llm_cls.return_value = mock_client

        issue = _make_issue(
            issue_id="issue-fallback",
            source="deterministic",
            suggestions=[],
            flagged_text="quiescent",
            message="Do not use 'quiescent'. Use 'inactive' instead.",
        )
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            result = get_suggestion(session_id, "issue-fallback")

        assert "rewritten_text" in result
        assert result["rewritten_text"] == "inactive"
        assert result["confidence"] == pytest.approx(0.7)

    @patch("app.services.suggestions.engine.LLMClient")
    def test_fallback_case_matches_uppercase(
        self, mock_llm_cls: MagicMock, app: Flask,
    ) -> None:
        """Fallback applies case matching when flagged text is uppercase.

        Extracted alternative should be capitalized to match the
        original flagged text.
        """
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        mock_llm_cls.return_value = mock_client

        issue = _make_issue(
            issue_id="issue-case-fallback",
            source="deterministic",
            suggestions=[],
            flagged_text="Resides",
            message="Do not use 'resides'. Use 'is in' instead.",
        )
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            result = get_suggestion(session_id, "issue-case-fallback")

        assert "rewritten_text" in result
        assert result["rewritten_text"] == "Is in"

    @patch("app.services.suggestions.engine.LLMClient")
    def test_fallback_no_alternative_returns_error(
        self, mock_llm_cls: MagicMock, app: Flask,
    ) -> None:
        """When no alternative can be extracted, return error with suggestions.

        Messages without quoted alternatives should fall through to the
        standard error response.
        """
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        mock_llm_cls.return_value = mock_client

        issue = _make_issue(
            issue_id="issue-no-alt",
            source="deterministic",
            suggestions=[],
            flagged_text="please",
            message="Do not use 'please' in technical documentation.",
        )
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            result = get_suggestion(session_id, "issue-no-alt")

        assert "error" in result


class TestLlmCallFailFallback:
    """Tests for LLM-call-failed fallback with message extraction."""

    @patch("app.services.suggestions.engine.LLMClient")
    def test_llm_fail_extracts_from_message(
        self, mock_llm_cls: MagicMock, app: Flask,
    ) -> None:
        """When LLM is available but suggest fails, extract from message.

        The engine should try _extract_alternative_from_message() before
        returning the raw error dict.
        """
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.suggest.return_value = {"error": "LLM returned empty response"}
        mock_llm_cls.return_value = mock_client

        issue = _make_issue(
            issue_id="issue-llm-fail",
            source="deterministic",
            suggestions=["Rewrite to avoid using 'quiescent'."],
            flagged_text="quiescent",
            message="Do not use 'quiescent'. Use 'inactive' instead.",
        )
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            result = get_suggestion(session_id, "issue-llm-fail")

        assert "rewritten_text" in result
        assert result["rewritten_text"] == "inactive"
        assert result["confidence"] == pytest.approx(0.7)

    @patch("app.services.suggestions.engine.LLMClient")
    def test_llm_fail_no_alternative_returns_error(
        self, mock_llm_cls: MagicMock, app: Flask,
    ) -> None:
        """When LLM fails and message has no alternative, return error dict.

        Messages without quoted alternatives should fall through to the
        standard error response with suggestions list.
        """
        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.suggest.return_value = {"error": "LLM timeout"}
        mock_llm_cls.return_value = mock_client

        issue = _make_issue(
            issue_id="issue-llm-fail-noalt",
            source="deterministic",
            suggestions=["Rewrite in active voice"],
            flagged_text="was restarted",
            message="Consider using active voice.",
        )
        response = _make_response([issue])

        with app.app_context():
            from app.services.session.store import get_session_store

            store = get_session_store()
            session_id = store.create_session(response)

            result = get_suggestion(session_id, "issue-llm-fail-noalt")

        assert "error" in result
        assert "suggestions" in result

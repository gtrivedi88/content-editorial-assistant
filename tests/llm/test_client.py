"""Tests for LLMClient multi-provider wrapper.

Validates availability checks, analysis/suggestion/judge calls,
retry logic on transient failures, and temperature configuration
via Config settings.
"""

import json
import logging
from unittest.mock import MagicMock, patch

import pytest

from app.llm.client import LLMClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_model_manager(
    available: bool = True,
    generate_return: str = "[]",
) -> MagicMock:
    """Build a mock ModelManager with configurable behavior.

    Args:
        available: Value returned by ``is_available()``.
        generate_return: Value returned by ``generate_text()``.

    Returns:
        A MagicMock configured as a ModelManager instance.
    """
    mm = MagicMock(name="mock_model_manager")
    mm.is_available.return_value = available
    mm.generate_text.return_value = generate_return
    return mm


# ---------------------------------------------------------------------------
# LLMClient.is_available
# ---------------------------------------------------------------------------


class TestIsAvailable:
    """Tests for LLMClient.is_available()."""

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_returns_true_when_enabled_and_provider_ready(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Returns True when LLM_ENABLED=True and provider is available."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_get_mm.return_value = _make_mock_model_manager(available=True)

        client = LLMClient()
        assert client.is_available() is True

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_returns_false_when_disabled(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Returns False when LLM_ENABLED is False."""
        mock_config.LLM_ENABLED = False
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_get_mm.return_value = _make_mock_model_manager(available=True)

        client = LLMClient()
        assert client.is_available() is False

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_returns_false_when_provider_unavailable(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Returns False when the model provider is not available."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_get_mm.return_value = _make_mock_model_manager(available=False)

        client = LLMClient()
        assert client.is_available() is False


# ---------------------------------------------------------------------------
# LLMClient.analyze_block
# ---------------------------------------------------------------------------


class TestAnalyzeBlock:
    """Tests for LLMClient.analyze_block()."""

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_returns_parsed_issues(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Returns parsed issue list from valid LLM response."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.1
        mock_config.MODEL_SEED = None
        mock_config.LLM_CONFIDENCE_THRESHOLD = 0.8

        issues_json = json.dumps([{
            "flagged_text": "was restarted",
            "message": "Use active voice.",
            "severity": "medium",
            "category": "style",
            "confidence": 0.9,
        }])
        mock_get_mm.return_value = _make_mock_model_manager(
            available=True, generate_return=issues_json,
        )

        client = LLMClient()
        result = client.analyze_block(
            "The server was restarted.",
            ["The server was restarted."],
            [],
        )
        assert len(result) == 1
        assert result[0]["flagged_text"] == "was restarted"
        assert result[0]["source"] == "llm"

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_returns_empty_when_unavailable(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Returns empty list when the LLM is not available."""
        mock_config.LLM_ENABLED = False
        mock_config.LLM_MAX_CONCURRENT = 5

        mock_get_mm.return_value = _make_mock_model_manager(available=False)

        client = LLMClient()
        result = client.analyze_block("Some text.", ["Some text."], [])
        assert result == []

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_seed_passed_to_model_manager(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Seed from Config is forwarded to generate_text kwargs."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.1
        mock_config.MODEL_SEED = 42
        mock_config.LLM_CONFIDENCE_THRESHOLD = 0.8

        mock_get_mm.return_value = _make_mock_model_manager(
            available=True, generate_return="[]",
        )

        client = LLMClient()
        client.analyze_block("Test text.", ["Test text."], [])

        call_kwargs = mock_get_mm.return_value.generate_text.call_args
        assert call_kwargs[1].get("seed") == 42


# ---------------------------------------------------------------------------
# LLMClient.analyze_global
# ---------------------------------------------------------------------------


class TestAnalyzeGlobal:
    """Tests for LLMClient.analyze_global()."""

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_returns_parsed_global_issues(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Returns parsed issue list from a global analysis call."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.1
        mock_config.MODEL_SEED = None
        mock_config.LLM_CONFIDENCE_THRESHOLD = 0.8

        issues_json = json.dumps([{
            "flagged_text": "",
            "message": "Inconsistent tone throughout document.",
            "severity": "low",
            "category": "audience",
            "confidence": 0.85,
        }])
        mock_get_mm.return_value = _make_mock_model_manager(
            available=True, generate_return=issues_json,
        )

        client = LLMClient()
        result = client.analyze_global(
            "Full document text here.", "concept", [],
        )
        assert len(result) == 1
        assert result[0]["message"] == "Inconsistent tone throughout document."


# ---------------------------------------------------------------------------
# LLMClient.suggest
# ---------------------------------------------------------------------------


class TestSuggest:
    """Tests for LLMClient.suggest()."""

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_returns_suggestion_dict(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Returns a suggestion dict with rewritten_text."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_SUGGESTION_TEMPERATURE = 0.2
        mock_config.MODEL_SEED = None

        suggestion_json = json.dumps({
            "rewritten_text": "Click the button.",
            "explanation": "Removed 'on' per style guide.",
            "confidence": 0.92,
        })
        mock_get_mm.return_value = _make_mock_model_manager(
            available=True, generate_return=suggestion_json,
        )

        client = LLMClient()
        result = client.suggest(
            "click on",
            ["Click on the button to proceed."],
            {"rule_name": "word_usage", "category": "style",
             "message": "Use click without on.", "severity": "low"},
            {},
        )
        assert result["rewritten_text"] == "Click the button."
        assert "error" not in result


# ---------------------------------------------------------------------------
# LLMClient retry logic
# ---------------------------------------------------------------------------


class TestRetryLogic:
    """Tests for tenacity retry behavior on transient errors."""

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_retries_on_connection_error(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """ConnectionError triggers retry; eventual success is returned."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.1
        mock_config.MODEL_SEED = None
        mock_config.LLM_CONFIDENCE_THRESHOLD = 0.8

        issues_json = json.dumps([{
            "flagged_text": "test",
            "message": "Test.",
            "severity": "low",
            "category": "style",
            "confidence": 0.9,
        }])

        mm = _make_mock_model_manager(available=True)
        # First call raises ConnectionError, second call succeeds
        mm.generate_text.side_effect = [
            ConnectionError("connection refused"),
            issues_json,
        ]
        mock_get_mm.return_value = mm

        client = LLMClient()
        result = client.analyze_block("test text", ["test text"], [])
        assert len(result) == 1
        assert mm.generate_text.call_count == 2


# ---------------------------------------------------------------------------
# LLMClient.judge_issues
# ---------------------------------------------------------------------------


class TestJudgeIssues:
    """Tests for LLMClient.judge_issues()."""

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_returns_keep_and_drop_indices(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Returns parsed keep/drop index lists from judge response."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.1
        mock_config.MODEL_SEED = None

        judge_json = json.dumps({"keep": [0, 2], "drop": [1]})
        mock_get_mm.return_value = _make_mock_model_manager(
            available=True, generate_return=judge_json,
        )

        issues = [
            {"flagged_text": "a", "message": "A"},
            {"flagged_text": "b", "message": "B"},
            {"flagged_text": "c", "message": "C"},
        ]

        client = LLMClient()
        keep, drop = client.judge_issues(issues, "doc excerpt", "concept")
        assert 0 in keep
        assert 2 in keep
        assert 1 in drop

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_empty_issues_returns_empty(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Empty issue list returns empty keep and drop lists."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5

        mock_get_mm.return_value = _make_mock_model_manager(available=True)

        client = LLMClient()
        keep, drop = client.judge_issues([], "doc excerpt", "concept")
        assert keep == []
        assert drop == []

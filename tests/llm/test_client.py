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
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"

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
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"

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
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"

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
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"

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

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_judge_uses_basic_response_format(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Judge call uses basic json_object format, not strict json_schema."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.1
        mock_config.MODEL_SEED = None

        judge_json = json.dumps({"keep": [0], "drop": []})
        mm = _make_mock_model_manager(available=True, generate_return=judge_json)
        mock_get_mm.return_value = mm

        client = LLMClient()
        client.judge_issues(
            [{"flagged_text": "a", "message": "A"}],
            "doc excerpt", "concept",
        )
        call_kwargs = mm.generate_text.call_args[1]
        assert call_kwargs["response_format"] == {"type": "json_object"}


# ---------------------------------------------------------------------------
# _safe_analysis_call format fallback
# ---------------------------------------------------------------------------


class TestSafeAnalysisCallFallback:
    """Tests for json_schema → json_object fallback in _safe_analysis_call."""

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_fallback_on_empty_response(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Falls back to basic format when strict schema returns empty."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.1
        mock_config.MODEL_SEED = None
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"

        issues_json = json.dumps([{
            "flagged_text": "test",
            "message": "Test issue.",
            "severity": "low",
            "category": "style",
            "confidence": 0.9,
        }])

        mm = _make_mock_model_manager(available=True)
        mm.generate_text.side_effect = ["", issues_json]
        mock_get_mm.return_value = mm

        client = LLMClient()
        result = client.analyze_block("test text", ["test text"], [])
        assert len(result) == 1
        assert mm.generate_text.call_count == 2

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_fallback_on_runtime_error(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """Falls back to basic format when strict schema raises RuntimeError."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.1
        mock_config.MODEL_SEED = None
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"

        issues_json = json.dumps([{
            "flagged_text": "test",
            "message": "Test issue.",
            "severity": "low",
            "category": "style",
            "confidence": 0.9,
        }])

        mm = _make_mock_model_manager(available=True)
        mm.generate_text.side_effect = [
            RuntimeError("400: unsupported response_format"),
            issues_json,
        ]
        mock_get_mm.return_value = mm

        client = LLMClient()
        result = client.analyze_block("test text", ["test text"], [])
        assert len(result) == 1
        assert mm.generate_text.call_count == 2

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_remembers_downgraded_format(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """After fallback, subsequent calls use basic format directly."""
        from app.llm.client import _ANALYSIS_RESPONSE_FORMAT_BASIC

        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.1
        mock_config.MODEL_SEED = None
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"

        issues_json = json.dumps([{
            "flagged_text": "test",
            "message": "Test.",
            "severity": "low",
            "category": "style",
            "confidence": 0.9,
        }])

        mm = _make_mock_model_manager(available=True)
        mm.generate_text.side_effect = ["", issues_json, issues_json]
        mock_get_mm.return_value = mm

        client = LLMClient()
        client.analyze_block("text1", ["text1"], [])
        assert client._current_analysis_format == _ANALYSIS_RESPONSE_FORMAT_BASIC

        mm.generate_text.reset_mock()
        mm.generate_text.return_value = issues_json
        client.analyze_block("text2", ["text2"], [])
        assert mm.generate_text.call_count == 1


# ---------------------------------------------------------------------------
# _dynamic_max_tokens
# ---------------------------------------------------------------------------


class TestDynamicMaxTokens:
    """Tests for per-phase token budget prediction."""

    @patch("app.llm.client.Config")
    def test_granular_procedure_higher_than_concept(
        self, mock_config: MagicMock,
    ) -> None:
        """Procedure content type produces a higher budget than concept."""
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"
        proc = LLMClient._dynamic_max_tokens(
            "granular", sentence_count=20, content_type="procedure",
        )
        concept = LLMClient._dynamic_max_tokens(
            "granular", sentence_count=20, content_type="concept",
        )
        assert proc > concept

    @patch("app.llm.client.Config")
    def test_det_issue_count_scales_budget(
        self, mock_config: MagicMock,
    ) -> None:
        """Higher deterministic issue count produces larger budget."""
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"
        low = LLMClient._dynamic_max_tokens(
            "granular", sentence_count=10, det_issue_count=3,
        )
        high = LLMClient._dynamic_max_tokens(
            "granular", sentence_count=10, det_issue_count=30,
        )
        assert high > low

    @patch("app.llm.client.Config")
    def test_floor_at_1024(
        self, mock_config: MagicMock,
    ) -> None:
        """Budget never drops below 1024."""
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "none"
        result = LLMClient._dynamic_max_tokens("suggest")
        assert result >= 1024

    @patch("app.llm.client.Config")
    def test_cap_at_model_max(
        self, mock_config: MagicMock,
    ) -> None:
        """Budget never exceeds MODEL_MAX_TOKENS."""
        mock_config.MODEL_MAX_TOKENS = 2048
        mock_config.GEMINI_REASONING_EFFORT = "medium"
        result = LLMClient._dynamic_max_tokens(
            "granular", sentence_count=500, det_issue_count=200,
        )
        assert result <= 2048

    @patch("app.llm.client.Config")
    def test_high_effort_returns_cap(
        self, mock_config: MagicMock,
    ) -> None:
        """High reasoning effort returns MODEL_MAX_TOKENS directly."""
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "high"
        result = LLMClient._dynamic_max_tokens("granular")
        assert result == 16384

    @patch("app.llm.client.Config")
    def test_judge_scales_with_issues(
        self, mock_config: MagicMock,
    ) -> None:
        """Judge budget scales with number of issues."""
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"
        small = LLMClient._dynamic_max_tokens("judge", num_issues=5)
        large = LLMClient._dynamic_max_tokens("judge", num_issues=50)
        assert large > small

    @patch("app.llm.client.Config")
    def test_suggest_fixed_budget(
        self, mock_config: MagicMock,
    ) -> None:
        """Suggest phase uses a fixed base_think + 500 budget."""
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"
        result = LLMClient._dynamic_max_tokens("suggest")
        assert result == 1500  # 1000 (base_think for low) + 500


# ---------------------------------------------------------------------------
# Truncation retry
# ---------------------------------------------------------------------------


class TestTruncationRetry:
    """Tests for truncation detection and retry in _safe_analysis_call."""

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_parser_truncation_triggers_retry(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """When parser detects truncation, retry with 1.5x budget."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.0
        mock_config.MODEL_SEED = None
        mock_config.MODEL_MAX_TOKENS = 4096

        issue = {
            "flagged_text": "foo",
            "message": "bar",
            "severity": "medium",
            "category": "style",
            "confidence": 0.9,
        }
        # First call: truncated (salvaged 1 issue)
        truncated_json = '[' + json.dumps(issue) + ', {"flagged_text": "partial'
        # Retry call: clean with 2 issues
        clean_json = json.dumps([issue, issue])

        mm = _make_mock_model_manager(available=True)
        mm.generate_text.side_effect = [truncated_json, clean_json]
        mock_get_mm.return_value = mm

        client = LLMClient()
        result = client._safe_analysis_call("test prompt")
        assert len(result) == 2
        assert mm.generate_text.call_count == 2

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_finish_reason_length_triggers_retry(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """When finish_reason='length', triggers retry."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.0
        mock_config.MODEL_SEED = None
        mock_config.MODEL_MAX_TOKENS = 4096

        issue = {
            "flagged_text": "foo",
            "message": "bar",
            "severity": "medium",
            "category": "style",
            "confidence": 0.9,
        }
        clean_json = json.dumps([issue])

        mm = _make_mock_model_manager(available=True)

        def side_effect(prompt, **kwargs):
            meta = kwargs.get("_result_meta")
            if meta is not None and mm.generate_text.call_count <= 1:
                meta["finish_reason"] = "length"
            return clean_json

        mm.generate_text.side_effect = side_effect
        mock_get_mm.return_value = mm

        client = LLMClient()
        result = client._safe_analysis_call("test prompt")
        assert len(result) >= 1
        assert mm.generate_text.call_count == 2


# ---------------------------------------------------------------------------
# GAP 1: _dynamic_max_tokens wired into analyze_block / analyze_global
# ---------------------------------------------------------------------------


class TestDynamicTokenWiring:
    """Verify analyze_block and analyze_global pass computed max_tokens."""

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_analyze_block_passes_max_tokens(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """analyze_block computes and forwards max_tokens."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.0
        mock_config.MODEL_SEED = None
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"

        mm = _make_mock_model_manager(available=True, generate_return="[]")
        mock_get_mm.return_value = mm

        client = LLMClient()
        client.analyze_block(
            "Some text", ["Some text"], [],
            content_type="concept",
            det_issue_count=10,
        )

        call_kwargs = mm.generate_text.call_args
        assert call_kwargs is not None
        assert "max_tokens" in call_kwargs.kwargs or (
            len(call_kwargs.args) > 0
        )
        max_tok = call_kwargs.kwargs.get("max_tokens")
        assert max_tok is not None
        assert max_tok >= 1024

    @patch("app.llm.client._get_model_manager")
    @patch("app.llm.client.Config")
    def test_analyze_global_passes_max_tokens(
        self, mock_config: MagicMock, mock_get_mm: MagicMock,
    ) -> None:
        """analyze_global computes and forwards max_tokens."""
        mock_config.LLM_ENABLED = True
        mock_config.LLM_MAX_CONCURRENT = 5
        mock_config.MODEL_ANALYSIS_TEMPERATURE = 0.0
        mock_config.MODEL_SEED = None
        mock_config.MODEL_MAX_TOKENS = 16384
        mock_config.GEMINI_REASONING_EFFORT = "low"

        mm = _make_mock_model_manager(available=True, generate_return="[]")
        mock_get_mm.return_value = mm

        client = LLMClient()
        client.analyze_global(
            "Full document text " * 50, "concept", [],
            det_issue_count=5,
        )

        call_kwargs = mm.generate_text.call_args
        assert call_kwargs is not None
        max_tok = call_kwargs.kwargs.get("max_tokens")
        assert max_tok is not None
        assert max_tok >= 1024

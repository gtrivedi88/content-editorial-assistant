"""Tests for the analysis pipeline orchestrator.

Validates that the orchestrator correctly coordinates the three-phase
analysis pipeline and returns properly structured AnalyzeResponse objects.
"""

import logging
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
from app.models.schemas import AnalyzeResponse, IssueResponse, ReportResponse, ScoreResponse
from app.services.analysis.orchestrator import (
    _collect_acronyms,
    _run_languagetool_phase,
)

logger = logging.getLogger(__name__)


def _make_issue(
    rule_name: str = "test_rule",
    message: str = "Test issue",
) -> IssueResponse:
    """Create a minimal IssueResponse for orchestrator tests.

    Args:
        rule_name: Name of the triggering rule.
        message: Human-readable issue description.

    Returns:
        A fully populated IssueResponse instance.
    """
    return IssueResponse(
        id="test-001",
        source="deterministic",
        category=IssueCategory.STYLE,
        rule_name=rule_name,
        flagged_text="test",
        message=message,
        suggestions=["fix it"],
        severity=IssueSeverity.MEDIUM,
        sentence="This is a test.",
        sentence_index=0,
        span=[0, 4],
        style_guide_citation="IBM Style Guide",
        confidence=1.0,
        status=IssueStatus.OPEN,
    )


def _make_prep_result() -> Dict[str, Any]:
    """Create a mock preprocessor result dict.

    Returns:
        Dictionary matching the shape returned by preprocessor.preprocess().
    """
    return {
        "text": "This is a test sentence. It has multiple words.",
        "sentences": ["This is a test sentence.", "It has multiple words."],
        "spacy_doc": MagicMock(),
        "word_count": 10,
        "char_count": 48,
        "sentence_count": 2,
        "paragraph_count": 1,
        "avg_words_per_sentence": 5.0,
        "avg_syllables_per_word": 1.4,
    }


class TestOrchestrator:
    """Tests for orchestrator.analyze()."""

    @patch("app.services.analysis.orchestrator.Config")
    @patch("app.services.analysis.orchestrator.run_deterministic")
    @patch("app.services.analysis.orchestrator.preprocess")
    def test_deterministic_only_pipeline(
        self,
        mock_preprocess: MagicMock,
        mock_run_det: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Analyze with LLM disabled returns deterministic results only.

        When Config.LLM_ENABLED is False, the orchestrator should run
        only the deterministic phase and return partial=False.
        """
        mock_config.LLM_ENABLED = False
        mock_config.CONFIDENCE_THRESHOLD = 0.7
        mock_config.LLM_GLOBAL_PASS_MAX_WORDS = 5000

        mock_preprocess.return_value = _make_prep_result()
        det_issues: List[IssueResponse] = [_make_issue()]
        mock_run_det.return_value = det_issues

        from app.services.analysis.orchestrator import analyze

        result: AnalyzeResponse = analyze(
            text="This is a test sentence. It has multiple words.",
            content_type="concept",
        )

        assert isinstance(result, AnalyzeResponse)
        assert result.partial is False
        assert len(result.issues) == 1
        assert result.issues[0].source == "deterministic"

    @patch("app.services.analysis.orchestrator.Config")
    @patch("app.services.analysis.orchestrator.run_deterministic")
    @patch("app.services.analysis.orchestrator.preprocess")
    def test_pipeline_returns_analyze_response(
        self,
        mock_preprocess: MagicMock,
        mock_run_det: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Result has expected shape: session_id, issues, score, report.

        The AnalyzeResponse returned from analyze() must contain a
        valid UUID session_id, a list of issues, a ScoreResponse, and
        a ReportResponse with document statistics.
        """
        mock_config.LLM_ENABLED = False
        mock_config.CONFIDENCE_THRESHOLD = 0.7
        mock_config.LLM_GLOBAL_PASS_MAX_WORDS = 5000

        mock_preprocess.return_value = _make_prep_result()
        mock_run_det.return_value = [_make_issue()]

        from app.services.analysis.orchestrator import analyze

        result: AnalyzeResponse = analyze(
            text="This is a test sentence. It has multiple words.",
            content_type="concept",
        )

        # session_id should be a UUID-like string
        assert result.session_id is not None
        assert len(result.session_id) > 0
        assert "-" in result.session_id

        # issues should be a list of IssueResponse
        assert isinstance(result.issues, list)

        # score should be a ScoreResponse
        assert isinstance(result.score, ScoreResponse)
        assert 30 <= result.score.score <= 100
        assert result.score.label in ("Excellent", "Good", "Needs Work", "Poor")

        # report should be a ReportResponse
        assert isinstance(result.report, ReportResponse)
        assert result.report.word_count == 10
        assert result.report.sentence_count == 2

    @patch("app.services.analysis.orchestrator.Config")
    @patch("app.services.analysis.orchestrator.run_deterministic")
    @patch("app.services.analysis.orchestrator.preprocess")
    def test_empty_text_produces_valid_response(
        self,
        mock_preprocess: MagicMock,
        mock_run_det: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        """Analyzing empty-ish text still produces a valid AnalyzeResponse.

        Even when no issues are found, the orchestrator should return
        a well-formed response with score 100 and empty issues list.
        """
        mock_config.LLM_ENABLED = False
        mock_config.CONFIDENCE_THRESHOLD = 0.7
        mock_config.LLM_GLOBAL_PASS_MAX_WORDS = 5000

        prep = _make_prep_result()
        prep["word_count"] = 5
        prep["sentence_count"] = 1
        prep["sentences"] = ["Hello world."]
        mock_preprocess.return_value = prep
        mock_run_det.return_value = []

        from app.services.analysis.orchestrator import analyze

        result: AnalyzeResponse = analyze(text="Hello world.", content_type="concept")

        assert isinstance(result, AnalyzeResponse)
        assert result.score.score == 100
        assert len(result.issues) == 0


class TestCollectAcronyms:
    """Tests for _collect_acronyms()."""

    def test_standard_pattern(self) -> None:
        """Detects 'Full Name (ACRONYM)' pattern."""
        text = "Container Storage Interface (CSI) provides storage."
        result = _collect_acronyms(text)
        assert "CSI" in result
        assert result["CSI"] == "Container Storage Interface"

    def test_reverse_pattern(self) -> None:
        """Detects '(ACRONYM) Full Name' pattern."""
        text = "The (OCP) OpenShift Container Platform is available."
        result = _collect_acronyms(text)
        assert "OCP" in result
        assert result["OCP"] == "OpenShift Container Platform"

    def test_multiple_acronyms(self) -> None:
        """Collects multiple acronym definitions from one text."""
        text = (
            "Container Storage Interface (CSI) and "
            "OpenShift Container Platform (OCP) are Red Hat products."
        )
        result = _collect_acronyms(text)
        assert "CSI" in result
        assert "OCP" in result

    def test_no_acronyms(self) -> None:
        """Returns empty dict when no acronym definitions found."""
        text = "This text has no acronym definitions at all."
        result = _collect_acronyms(text)
        assert result == {}

    def test_numeric_acronyms(self) -> None:
        """Detects acronyms with digits like S3."""
        text = "Amazon Simple Storage Service (S3) provides object storage."
        result = _collect_acronyms(text)
        assert "S3" in result

    def test_standard_pattern_priority(self) -> None:
        """Standard pattern takes priority over reverse pattern."""
        text = (
            "Container Storage Interface (CSI) is documented. "
            "(CSI) Container Storage Impl is alternative."
        )
        result = _collect_acronyms(text)
        assert result["CSI"] == "Container Storage Interface"

    def test_single_char_not_matched(self) -> None:
        """Single-character abbreviations in parentheses are not matched."""
        text = "Some word (X) is not an acronym."
        result = _collect_acronyms(text)
        assert "X" not in result

    def test_empty_text(self) -> None:
        """Empty text returns empty dict."""
        result = _collect_acronyms("")
        assert result == {}


# ---------------------------------------------------------------------------
# LanguageTool phase integration
# ---------------------------------------------------------------------------


class TestRunLanguageToolPhase:
    """Tests for _run_languagetool_phase() helper."""

    @patch("app.services.analysis.languagetool_client.check_blocks")
    def test_returns_issues_from_check_blocks(
        self, mock_check: MagicMock,
    ) -> None:
        """Calls check_blocks with blocks and original_text from prep."""
        mock_block = MagicMock()
        prep = {
            "blocks": [mock_block],
            "original_text": "Hello world.",
        }
        mock_issue = _make_issue()
        mock_check.return_value = [mock_issue]

        result = _run_languagetool_phase(prep)

        assert len(result) == 1
        mock_check.assert_called_once_with(
            [mock_block], original_text="Hello world.",
        )

    def test_empty_blocks_returns_empty(self) -> None:
        """When blocks list is empty, returns empty without calling LT."""
        prep = {"blocks": [], "original_text": ""}
        result = _run_languagetool_phase(prep)
        assert result == []

    def test_missing_blocks_key_returns_empty(self) -> None:
        """When prep has no 'blocks' key, returns empty."""
        result = _run_languagetool_phase({})
        assert result == []

    @patch(
        "app.services.analysis.languagetool_client.check_blocks",
        side_effect=RuntimeError("LT crashed"),
    )
    def test_exception_returns_empty(self, mock_check: MagicMock) -> None:
        """Exceptions from check_blocks are caught, returns empty."""
        prep = {
            "blocks": [MagicMock()],
            "original_text": "",
        }
        result = _run_languagetool_phase(prep)
        assert result == []

    @patch("app.services.analysis.languagetool_client.check_blocks")
    def test_missing_original_text_defaults_empty(
        self, mock_check: MagicMock,
    ) -> None:
        """When original_text is missing from prep, defaults to empty."""
        mock_check.return_value = []
        prep = {"blocks": [MagicMock()]}
        _run_languagetool_phase(prep)
        mock_check.assert_called_once()
        _, kwargs = mock_check.call_args
        assert kwargs["original_text"] == ""

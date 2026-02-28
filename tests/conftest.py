"""Shared pytest fixtures for the Content Editorial Assistant test suite.

Provides fixtures for the Flask test app, test client, mock SpaCy NLP,
mock Gemini LLM client, sample text with known issues, and pre-populated
sessions for issue lifecycle testing.
"""

import logging
import uuid
from typing import Any, Generator
from unittest.mock import MagicMock, patch

import pytest
from flask import Flask
from flask.testing import FlaskClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: build a minimal mock SpaCy Doc
# ---------------------------------------------------------------------------


def _build_mock_spacy_nlp() -> MagicMock:
    """Build a mock SpaCy Language pipeline returning minimal Doc objects.

    The mock ``nlp(text)`` produces a Doc-like object with:
      - ``sents``: list of sentence-like objects with ``.text`` attributes
      - Iterable tokens with ``.text``, ``.is_punct``, ``.is_space`` attrs
      - ``__len__`` returning the number of tokens

    Returns:
        A MagicMock configured to behave like a SpaCy Language model.
    """
    nlp_mock = MagicMock(name="mock_spacy_nlp")

    def _create_doc(text: str) -> MagicMock:
        """Create a mock SpaCy Doc for the given text."""
        doc = MagicMock(name="mock_doc")

        # Split into sentences on period-space or period-end
        raw_sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
        sent_mocks = []
        for sent_text in raw_sentences:
            sent_mock = MagicMock()
            # Re-add the period if the original had one
            if not sent_text.endswith("."):
                sent_text = sent_text + "."
            sent_mock.text = sent_text
            sent_mocks.append(sent_mock)

        if not sent_mocks:
            fallback = MagicMock()
            fallback.text = text
            sent_mocks = [fallback]

        doc.sents = sent_mocks

        # Build token list from whitespace splitting
        words = text.split()
        tokens = []
        for word in words:
            token = MagicMock()
            token.text = word
            token.is_punct = bool(len(word) == 1 and not word.isalnum())
            token.is_space = word.isspace()
            tokens.append(token)

        doc.__iter__ = lambda self: iter(tokens)
        doc.__len__ = lambda self: len(tokens)

        return doc

    nlp_mock.side_effect = _create_doc
    return nlp_mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_spacy() -> Generator[MagicMock, None, None]:
    """Patch ``app.extensions.get_nlp`` to return a mock SpaCy pipeline.

    Yields:
        The mock NLP callable so tests can inspect calls if needed.
    """
    mock_nlp = _build_mock_spacy_nlp()
    with patch("app.extensions.get_nlp", return_value=mock_nlp):
        # Also patch the preprocessor import of get_nlp
        with patch("app.services.analysis.preprocessor.get_nlp", return_value=mock_nlp):
            yield mock_nlp


@pytest.fixture()
def mock_llm() -> Generator[MagicMock, None, None]:
    """Patch ``app.llm.client.LLMClient`` to return predefined responses.

    The mock client reports ``is_available() == False`` so that analysis
    runs in deterministic-only mode, avoiding any network calls.

    Yields:
        The mock LLMClient class.
    """
    with patch("app.llm.client.LLMClient") as mock_cls:
        instance = MagicMock()
        instance.is_available.return_value = False
        instance.analyze_block.return_value = []
        instance.analyze_global.return_value = []
        instance.suggest.return_value = {"error": "LLM is not available"}
        mock_cls.return_value = instance
        yield mock_cls


@pytest.fixture()
def app(mock_spacy: MagicMock, mock_llm: MagicMock) -> Generator[Flask, None, None]:
    """Create a Flask test application with testing overrides.

    Configures:
      - TESTING = True
      - LLM_ENABLED = False (deterministic only)
      - FEEDBACK_PERSISTENT = False (in-memory SQLite)
      - FEEDBACK_DB_PATH = ':memory:'

    The SpaCy and LLM mocks are active for the app lifetime.

    Args:
        mock_spacy: The patched SpaCy NLP fixture.
        mock_llm: The patched LLM client fixture.

    Yields:
        The configured Flask application instance.
    """
    # Reset singleton stores before each test app creation
    _reset_singleton_stores()

    from app import create_app

    test_app = create_app({
        "TESTING": True,
        "LLM_ENABLED": False,
        "FEEDBACK_PERSISTENT": False,
        "FEEDBACK_DB_PATH": ":memory:",
    })

    yield test_app

    # Cleanup singleton stores after test
    _reset_singleton_stores()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    """Create a Flask test client from the app fixture.

    Args:
        app: The Flask test application.

    Returns:
        A FlaskClient for making test HTTP requests.
    """
    return app.test_client()


@pytest.fixture()
def sample_text() -> str:
    """Return sample technical documentation with known editorial issues.

    The text contains passive voice, contractions, informal language,
    and other patterns that deterministic rules should detect.

    Returns:
        A multi-sentence string suitable for analysis testing.
    """
    return (
        "The server was restarted by the administrator. "
        "It's important to note that you shouldn't use contractions in technical writing. "
        "The data is inputted into the system. "
        "Please click on the button to proceed. "
        "The functionality was implemented and the tests were ran successfully. "
        "This document provides an overview of the system architecture."
    )


@pytest.fixture()
def session_with_issues(app: Flask) -> dict[str, Any]:
    """Create a pre-populated session in the session store with mock issues.

    Stores an AnalyzeResponse with two open issues so that accept,
    dismiss, and feedback operations can be tested.

    Args:
        app: The Flask test application (ensures app context is available).

    Returns:
        Dictionary with ``session_id``, ``issue_id_1``, and ``issue_id_2``.
    """
    from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
    from app.models.schemas import (
        AnalyzeResponse,
        IssueResponse,
        ReportResponse,
        ScoreResponse,
    )
    from app.services.session.store import get_session_store

    issue_id_1 = str(uuid.uuid4())
    issue_id_2 = str(uuid.uuid4())

    issues = [
        IssueResponse(
            id=issue_id_1,
            source="deterministic",
            category=IssueCategory.STYLE,
            rule_name="passive_voice",
            flagged_text="was restarted",
            message="Consider using active voice.",
            suggestions=["restarted"],
            severity=IssueSeverity.MEDIUM,
            sentence="The server was restarted by the administrator.",
            sentence_index=0,
            span=[11, 24],
            style_guide_citation="IBM Style Guide, Section 5.1",
            confidence=1.0,
            status=IssueStatus.OPEN,
        ),
        IssueResponse(
            id=issue_id_2,
            source="deterministic",
            category=IssueCategory.GRAMMAR,
            rule_name="contraction_usage",
            flagged_text="shouldn't",
            message="Avoid contractions in technical writing.",
            suggestions=["should not"],
            severity=IssueSeverity.HIGH,
            sentence="You shouldn't use contractions.",
            sentence_index=1,
            span=[50, 59],
            style_guide_citation="IBM Style Guide, Section 3.2",
            confidence=1.0,
            status=IssueStatus.OPEN,
        ),
    ]

    score = ScoreResponse(
        score=85,
        color="#06c",
        label="Good",
        total_issues=2,
        category_counts={"style": 1, "grammar": 1},
        compliance={},
    )

    report = ReportResponse(
        word_count=50,
        sentence_count=3,
        paragraph_count=1,
        avg_words_per_sentence=16.67,
        avg_syllables_per_word=1.5,
    )

    response = AnalyzeResponse(
        session_id="",
        issues=issues,
        score=score,
        report=report,
        partial=False,
    )

    with app.app_context():
        store = get_session_store()
        session_id = store.create_session(response)

    return {
        "session_id": session_id,
        "issue_id_1": issue_id_1,
        "issue_id_2": issue_id_2,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _reset_singleton_stores() -> None:
    """Reset singleton session and feedback store instances.

    This ensures test isolation by clearing any state from previous
    test runs. Patches the module-level singleton variables directly.
    """
    try:
        import app.services.session.store as session_mod
        session_mod._store_instance = None
    except ImportError:
        pass

    try:
        import app.services.feedback.store as feedback_mod
        feedback_mod._store_instance = None
    except ImportError:
        pass

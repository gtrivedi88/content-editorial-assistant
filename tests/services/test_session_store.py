"""Tests for the thread-safe in-memory session store.

Validates session CRUD operations, TTL expiration, issue status updates
with score recalculation, suggestion caching, active analysis tracking,
concurrent access safety, and multi-session independence.
"""

import logging
import threading
import time
import uuid
from typing import Any
from unittest.mock import patch

import pytest
from flask import Flask

from app.models.enums import IssueCategory, IssueSeverity, IssueStatus
from app.models.schemas import (
    AnalyzeResponse,
    IssueResponse,
    ReportResponse,
    ScoreResponse,
)
from app.services.session.store import SessionStore, get_session_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_response(
    num_issues: int = 2,
    word_count: int = 100,
) -> AnalyzeResponse:
    """Build a minimal AnalyzeResponse with the given number of issues.

    Args:
        num_issues: Number of open issues to include.
        word_count: Word count for the report.

    Returns:
        A fully populated AnalyzeResponse suitable for session store tests.
    """
    issues = []
    for i in range(num_issues):
        issues.append(IssueResponse(
            id=str(uuid.uuid4()),
            source="deterministic",
            category=IssueCategory.STYLE if i % 2 == 0 else IssueCategory.GRAMMAR,
            rule_name=f"test_rule_{i}",
            flagged_text=f"flagged {i}",
            message=f"Test message {i}",
            suggestions=[f"suggestion {i}"],
            severity=IssueSeverity.MEDIUM if i % 2 == 0 else IssueSeverity.HIGH,
            sentence=f"This is test sentence {i}.",
            sentence_index=i,
            span=[i * 10, i * 10 + 5],
            confidence=1.0,
            status=IssueStatus.OPEN,
        ))

    score = ScoreResponse(
        score=85,
        color="#06c",
        label="Good",
        total_issues=num_issues,
        category_counts={"style": num_issues // 2, "grammar": num_issues - num_issues // 2},
    )

    report = ReportResponse(
        word_count=word_count,
        sentence_count=num_issues,
        paragraph_count=1,
        avg_words_per_sentence=float(word_count) / max(num_issues, 1),
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


class TestSessionStore:
    """Tests for the SessionStore class."""

    def test_create_session_returns_id(self, app: Flask) -> None:
        """create_session returns a non-empty UUID session ID.

        The returned ID should be a valid string that can be used
        to retrieve the session later.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response = _make_response()
            session_id: str = store.create_session(response)

            assert session_id is not None
            assert isinstance(session_id, str)
            assert len(session_id) > 0

    def test_get_session_retrieves_stored(self, app: Flask) -> None:
        """get_session retrieves the stored AnalyzeResponse.

        After creating a session, the same response (with its issues)
        should be retrievable by the session ID.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response = _make_response(num_issues=3)
            session_id: str = store.create_session(response)

            retrieved = store.get_session(session_id)
            assert retrieved is not None
            assert len(retrieved.issues) == 3
            assert retrieved.session_id == session_id

    def test_get_session_returns_none_for_unknown_id(self, app: Flask) -> None:
        """get_session returns None for a session ID that was never created.

        Querying a non-existent session should return None rather than
        raising an error.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            result = store.get_session("nonexistent-session-id")
            assert result is None

    def test_ttl_expiration(self, app: Flask) -> None:
        """Expired sessions return None from get_session.

        A session with a very short TTL should become inaccessible
        after the TTL period has elapsed.
        """
        with app.app_context():
            store = SessionStore(ttl_seconds=1)
            response = _make_response()
            session_id: str = store.create_session(response)

            # Session should be accessible immediately
            assert store.get_session(session_id) is not None

            # Wait for TTL to expire
            time.sleep(1.5)

            # Session should now be expired
            assert store.get_session(session_id) is None

    def test_update_issue_status_accept(self, app: Flask) -> None:
        """update_issue_status changes an issue status to ACCEPTED.

        After accepting an issue, its status should be updated and
        the method should return a recalculated ScoreResponse.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response = _make_response(num_issues=2)
            session_id: str = store.create_session(response)
            issue_id: str = response.issues[0].id

            new_score = store.update_issue_status(
                session_id, issue_id, IssueStatus.ACCEPTED
            )

            assert new_score is not None
            assert isinstance(new_score, ScoreResponse)
            # The accepted issue should have updated status
            retrieved = store.get_session(session_id)
            assert retrieved is not None
            matched = [i for i in retrieved.issues if i.id == issue_id]
            assert len(matched) == 1
            assert matched[0].status == IssueStatus.ACCEPTED

    def test_update_issue_status_dismiss(self, app: Flask) -> None:
        """update_issue_status changes an issue status to DISMISSED.

        Dismissing an issue should update its status and return a
        recalculated score.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response = _make_response(num_issues=2)
            session_id: str = store.create_session(response)
            issue_id: str = response.issues[1].id

            new_score = store.update_issue_status(
                session_id, issue_id, IssueStatus.DISMISSED
            )

            assert new_score is not None
            retrieved = store.get_session(session_id)
            assert retrieved is not None
            matched = [i for i in retrieved.issues if i.id == issue_id]
            assert len(matched) == 1
            assert matched[0].status == IssueStatus.DISMISSED

    def test_update_issue_status_recalculates_score(self, app: Flask) -> None:
        """Score is recalculated after accepting an issue.

        Accepting an issue should result in a different (typically higher)
        score compared to when all issues are open.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response = _make_response(num_issues=4)
            session_id: str = store.create_session(response)
            original_score: int = response.score.score

            # Accept first two issues
            store.update_issue_status(
                session_id, response.issues[0].id, IssueStatus.ACCEPTED
            )
            new_score = store.update_issue_status(
                session_id, response.issues[1].id, IssueStatus.ACCEPTED
            )

            assert new_score is not None
            # With fewer open issues, the score should generally improve
            assert new_score.score >= original_score

    def test_suggestion_cache_set_and_get(self, app: Flask) -> None:
        """Suggestion cache stores and retrieves suggestions by issue ID.

        After caching a suggestion, it should be retrievable using the
        same session and issue IDs.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response = _make_response()
            session_id: str = store.create_session(response)
            issue_id: str = response.issues[0].id

            suggestion: dict[str, str] = {
                "replacement": "improved text",
                "source": "llm",
            }
            store.cache_suggestion(session_id, issue_id, suggestion)

            cached = store.get_cached_suggestion(session_id, issue_id)
            assert cached is not None
            assert cached["replacement"] == "improved text"
            assert cached["source"] == "llm"

    def test_set_active_analysis_is_current(self, app: Flask) -> None:
        """set_active_analysis + is_analysis_current — fresh analysis is current.

        After setting an active analysis, is_analysis_current should
        return True for that session ID.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response = _make_response()
            session_id: str = store.create_session(response)

            store.set_active_analysis("socket-1", session_id)
            assert store.is_analysis_current(session_id) is True

    def test_set_active_analysis_supersedes_old(self, app: Flask) -> None:
        """Old analysis is not current after a new one is set for the same socket.

        When set_active_analysis is called with a new session ID for the
        same Socket.IO SID, the previous session should be marked as
        cancelled and is_analysis_current should return False for it.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response_1 = _make_response()
            session_id_1: str = store.create_session(response_1)
            response_2 = _make_response()
            session_id_2: str = store.create_session(response_2)

            store.set_active_analysis("socket-1", session_id_1)
            assert store.is_analysis_current(session_id_1) is True

            # Supersede with a new analysis
            store.set_active_analysis("socket-1", session_id_2)
            assert store.is_analysis_current(session_id_1) is False
            assert store.is_analysis_current(session_id_2) is True

    def test_update_session_response(self, app: Flask) -> None:
        """update_session_response updates the stored response.

        After updating, the session should contain the new response
        data with the updated issue count.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response = _make_response(num_issues=2)
            session_id: str = store.create_session(response)

            # Create an updated response with more issues
            updated_response = _make_response(num_issues=5)
            updated_response.session_id = session_id
            result: bool = store.update_session_response(session_id, updated_response)

            assert result is True
            retrieved = store.get_session(session_id)
            assert retrieved is not None
            assert len(retrieved.issues) == 5

    def test_concurrent_access_thread_safety(self, app: Flask) -> None:
        """Multiple threads can create and read sessions concurrently.

        Concurrent create_session and get_session calls should not
        raise exceptions or corrupt data.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            errors: list[str] = []
            session_ids: list[str] = []
            lock = threading.Lock()

            def create_and_read() -> None:
                """Create a session and immediately read it back."""
                try:
                    resp = _make_response()
                    sid = store.create_session(resp)
                    with lock:
                        session_ids.append(sid)
                    retrieved = store.get_session(sid)
                    if retrieved is None:
                        with lock:
                            errors.append(f"Session {sid} not found after creation")
                except (KeyError, ValueError, RuntimeError) as exc:
                    with lock:
                        errors.append(str(exc))

            threads = [threading.Thread(target=create_and_read) for _ in range(10)]
            for t in threads:
                t.start()
            for t in threads:
                t.join(timeout=5)

            assert len(errors) == 0, f"Thread safety errors: {errors}"
            assert len(session_ids) == 10

    def test_multiple_sessions_independent(self, app: Flask) -> None:
        """Multiple sessions are stored and retrieved independently.

        Changes to one session should not affect another session.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response_a = _make_response(num_issues=1)
            response_b = _make_response(num_issues=3)

            session_a: str = store.create_session(response_a)
            session_b: str = store.create_session(response_b)

            retrieved_a = store.get_session(session_a)
            retrieved_b = store.get_session(session_b)

            assert retrieved_a is not None
            assert retrieved_b is not None
            assert len(retrieved_a.issues) == 1
            assert len(retrieved_b.issues) == 3
            assert session_a != session_b

    def test_session_not_found_for_update(self, app: Flask) -> None:
        """update_session_response returns False for a nonexistent session.

        Attempting to update a session that does not exist should return
        False without raising an exception.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response = _make_response()
            result: bool = store.update_session_response("nonexistent-id", response)
            assert result is False

    def test_issue_not_found_in_session(self, app: Flask) -> None:
        """update_issue_status returns None for a nonexistent issue ID.

        If the issue ID does not match any issue in the session, the
        method should return None.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            response = _make_response(num_issues=1)
            session_id: str = store.create_session(response)

            result = store.update_issue_status(
                session_id, "nonexistent-issue-id", IssueStatus.ACCEPTED
            )
            assert result is None


class TestUpdateSessionResponsePreservesStatuses:
    """Verify that update_session_response preserves user-modified statuses."""

    def test_accepted_status_preserved_after_session_update(self, app: Flask) -> None:
        """Accepted issue statuses should survive an update_session_response call.

        Simulates the race condition where a user accepts an issue during
        the LLM background phase, then the orchestrator replaces the session
        response with merged results.
        """
        with app.app_context():
            store: SessionStore = get_session_store()
            original = _make_response(num_issues=2)
            session_id: str = store.create_session(original)

            # User accepts the first issue during LLM phase
            issue_id = original.issues[0].id
            store.update_issue_status(session_id, issue_id, IssueStatus.ACCEPTED)

            # Verify the status was set
            session = store.get_session(session_id)
            assert session is not None
            assert session.issues[0].status == IssueStatus.ACCEPTED

            # Orchestrator creates a new response with the same issue IDs
            new_response = _make_response(num_issues=2)
            # Copy issue IDs so they match
            new_response.issues[0].id = issue_id
            new_response.issues[1].id = original.issues[1].id

            store.update_session_response(session_id, new_response)

            # Verify status was preserved
            updated = store.get_session(session_id)
            assert updated is not None
            accepted_issues = [i for i in updated.issues if i.status == IssueStatus.ACCEPTED]
            assert len(accepted_issues) == 1, (
                f"Expected 1 accepted issue after session update, got {len(accepted_issues)}"
            )
            assert accepted_issues[0].id == issue_id

    def test_score_recalculated_after_status_transfer(self, app: Flask) -> None:
        """Score should reflect preserved statuses, not original penalties."""
        with app.app_context():
            store: SessionStore = get_session_store()
            original = _make_response(num_issues=1)
            session_id: str = store.create_session(original)

            # Accept the only issue — score should become 100
            issue_id = original.issues[0].id
            score_result = store.update_issue_status(session_id, issue_id, IssueStatus.ACCEPTED)
            assert score_result is not None
            assert score_result.score == 100

            # New response with the same issue ID (OPEN status)
            new_response = _make_response(num_issues=1)
            new_response.issues[0].id = issue_id

            store.update_session_response(session_id, new_response)

            # Score should still be 100 because status was preserved
            updated = store.get_session(session_id)
            assert updated is not None
            assert updated.score.score == 100

"""Thread-safe in-memory session store with TTL-based expiration.

Stores analysis responses keyed by session ID, supports suggestion
caching, issue status updates with score recalculation, and request
cancellation for superseded analyses.

Usage:
    from app.services.session.store import get_session_store

    store = get_session_store()
    session_id = store.create_session(analyze_response)
    response = store.get_session(session_id)
"""

import logging
import threading
import time
import uuid
from typing import Optional

from app.config import Config
from app.models.enums import IssueStatus
from app.models.schemas import AnalyzeResponse, ScoreResponse
from app.services.analysis.scorer import calculate_score

logger = logging.getLogger(__name__)


class SessionStore:
    """Thread-safe in-memory session store with TTL expiration.

    Manages analysis sessions keyed by UUID. Each session holds the
    full AnalyzeResponse, a suggestion cache, creation timestamp, and
    cancellation flag. A daemon background thread periodically purges
    expired sessions.

    Attributes:
        _sessions: Dict mapping session IDs to session data dicts.
        _lock: Threading lock for thread-safe access.
        _ttl_seconds: Time-to-live for sessions in seconds.
        _active_analyses: Maps Socket.IO SIDs to active session IDs.
        _cleanup_thread: Daemon thread that purges expired sessions.
    """

    def __init__(self, ttl_seconds: Optional[int] = None) -> None:
        """Initialize the session store.

        Args:
            ttl_seconds: Session time-to-live in seconds. Defaults to
                the configured SESSION_TTL_SECONDS value.
        """
        self._sessions: dict[str, dict] = {}
        self._lock: threading.Lock = threading.Lock()
        self._ttl_seconds: int = ttl_seconds if ttl_seconds is not None else Config.SESSION_TTL_SECONDS
        self._active_analyses: dict[str, str] = {}
        self._cleanup_thread: threading.Thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name="session-cleanup",
        )
        self._cleanup_thread.start()
        logger.info("SessionStore initialized with TTL=%d seconds", self._ttl_seconds)

    # ------------------------------------------------------------------
    # Public API — Session CRUD
    # ------------------------------------------------------------------

    def create_session(self, response: AnalyzeResponse) -> str:
        """Create a new session and store the analysis response.

        Generates a UUID for the session, stores the response along with
        metadata, and updates the response's session_id field.

        Args:
            response: The analysis response to store.

        Returns:
            The generated session ID string.
        """
        session_id = str(uuid.uuid4())
        response.session_id = session_id
        return self.store_session(session_id, response)

    def store_session(self, session_id: str, response: AnalyzeResponse) -> str:
        """Store an analysis response under a specific session ID.

        Used when the session ID is already determined (e.g., by the
        orchestrator) and must remain consistent across WebSocket events
        and HTTP responses.

        Args:
            session_id: The pre-determined session identifier.
            response: The analysis response to store.

        Returns:
            The session ID string.
        """
        with self._lock:
            self._sessions[session_id] = {
                "response": response,
                "created_at": time.time(),
                "suggestion_cache": {},
                "cancelled": False,
            }

        logger.info("Stored session %s with %d issues", session_id, len(response.issues))
        logger.debug(
            "store: session %s stored, total sessions=%d, all_ids=%s",
            session_id, len(self._sessions), list(self._sessions.keys()),
        )
        return session_id

    def update_session_response(self, session_id: str, response: AnalyzeResponse) -> bool:
        """Update an existing session with a new analysis response.

        Preserves the suggestion cache, creation timestamp, and any
        user-modified issue statuses (accept/dismiss/manually-fixed)
        from the previous response. Used by the orchestrator to update
        results after LLM phases complete.

        Args:
            session_id: The session identifier.
            response: The updated analysis response.

        Returns:
            True if the session was found and updated, False otherwise.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            old_response = session["response"]
            _transfer_issue_statuses(old_response, response)
            session["response"] = response
        logger.info("Updated session %s with %d issues", session_id, len(response.issues))
        return True

    def get_session(self, session_id: str) -> Optional[AnalyzeResponse]:
        """Retrieve the analysis response for a session.

        Returns None if the session does not exist or has expired.

        Args:
            session_id: The session identifier.

        Returns:
            The stored AnalyzeResponse, or None if not found/expired.
        """
        with self._lock:
            logger.debug(
                "store.get_session: looking for %s in %d sessions: %s",
                session_id, len(self._sessions), list(self._sessions.keys()),
            )
            session = self._sessions.get(session_id)
            if session is None:
                logger.debug("store.get_session: %s NOT FOUND", session_id)
                return None
            if self._is_expired(session):
                del self._sessions[session_id]
                logger.debug("Session %s expired on access", session_id)
                return None
            logger.debug(
                "store.get_session: %s FOUND with %d issues",
                session_id, len(session["response"].issues),
            )
            return session["response"]

    def update_issue_status(
        self, session_id: str, issue_id: str, status: IssueStatus
    ) -> Optional[ScoreResponse]:
        """Update an issue's status and recalculate the session score.

        Args:
            session_id: The session identifier.
            issue_id: The issue identifier within the session.
            status: The new status to apply.

        Returns:
            The recalculated ScoreResponse, or None if the session or
            issue was not found.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if self._is_expired(session):
                del self._sessions[session_id]
                return None

            response = session["response"]
            issue = self._find_issue(response, issue_id)
            if issue is None:
                return None

            issue.status = status

        new_score = calculate_score(response.issues, response.report.word_count)
        response.score = new_score

        logger.info(
            "Updated issue %s to %s in session %s; new score=%d",
            issue_id, status.value, session_id, new_score.score,
        )
        return new_score

    # ------------------------------------------------------------------
    # Public API — Suggestion caching
    # ------------------------------------------------------------------

    def get_cached_suggestion(self, session_id: str, issue_id: str) -> Optional[dict]:
        """Retrieve a cached suggestion for an issue.

        Args:
            session_id: The session identifier.
            issue_id: The issue identifier.

        Returns:
            The cached suggestion dict, or None if not cached.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if self._is_expired(session):
                return None
            return session["suggestion_cache"].get(issue_id)

    def cache_suggestion(self, session_id: str, issue_id: str, suggestion: dict) -> None:
        """Cache a suggestion for an issue in the session.

        Args:
            session_id: The session identifier.
            issue_id: The issue identifier.
            suggestion: The suggestion dict to cache.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                logger.debug("Cannot cache suggestion: session %s not found", session_id)
                return
            session["suggestion_cache"][issue_id] = suggestion

        logger.debug("Cached suggestion for issue %s in session %s", issue_id, session_id)

    # ------------------------------------------------------------------
    # Public API — Incremental analysis (block tracking)
    # ------------------------------------------------------------------

    def store_block_results(
        self,
        session_id: str,
        block_hashes: list[str],
        block_issues: dict[str, list[dict]],
    ) -> None:
        """Store block hashes and per-block LLM issues for incremental re-analysis.

        Args:
            session_id: The session identifier.
            block_hashes: Ordered list of block content hashes.
            block_issues: Mapping of block hash to raw LLM issue dicts.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return
            session["block_hashes"] = block_hashes
            session["block_llm_issues"] = block_issues

    def get_block_results(
        self, session_id: str,
    ) -> Optional[tuple[list[str], dict[str, list[dict]]]]:
        """Retrieve stored block hashes and per-block LLM issues.

        Args:
            session_id: The session identifier.

        Returns:
            Tuple of (block_hashes, block_issues) or None if not stored.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            hashes = session.get("block_hashes")
            issues = session.get("block_llm_issues")
            if hashes is None or issues is None:
                return None
            return hashes, issues

    # ------------------------------------------------------------------
    # Public API — Request cancellation (Amendment 4)
    # ------------------------------------------------------------------

    def set_active_analysis(self, socket_sid: str, session_id: str) -> None:
        """Register the active analysis session for a browser tab.

        When a new analysis starts for the same Socket.IO SID, the
        previous session is implicitly superseded.

        Args:
            socket_sid: The Socket.IO session identifier for the tab.
            session_id: The session ID of the new active analysis.
        """
        with self._lock:
            previous = self._active_analyses.get(socket_sid)
            if previous and previous != session_id:
                prev_session = self._sessions.get(previous)
                if prev_session is not None:
                    prev_session["cancelled"] = True
                    logger.info(
                        "Superseded session %s for socket %s with %s",
                        previous, socket_sid, session_id,
                    )
            self._active_analyses[socket_sid] = session_id

    def is_analysis_current(self, session_id: str) -> bool:
        """Check whether an analysis session is still the active one.

        Returns False if the session has been cancelled or superseded
        by a newer analysis for the same browser tab.

        Args:
            session_id: The session identifier to check.

        Returns:
            True if the session is still active and not cancelled.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            return not session["cancelled"]

    def cancel_analysis(self, session_id: str) -> None:
        """Mark an analysis session as cancelled.

        Args:
            session_id: The session identifier to cancel.
        """
        with self._lock:
            session = self._sessions.get(session_id)
            if session is not None:
                session["cancelled"] = True
                logger.info("Cancelled session %s", session_id)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _is_expired(self, session: dict) -> bool:
        """Check whether a session has exceeded its TTL.

        Args:
            session: The session data dict.

        Returns:
            True if the session is older than the configured TTL.
        """
        age = time.time() - session["created_at"]
        return age > self._ttl_seconds

    @staticmethod
    def _find_issue(response: AnalyzeResponse, issue_id: str) -> object:
        """Find an issue by ID within an analysis response.

        Args:
            response: The analysis response to search.
            issue_id: The issue identifier to find.

        Returns:
            The matching IssueResponse, or None if not found.
        """
        for issue in response.issues:
            if issue.id == issue_id:
                return issue
        return None

    def _cleanup_loop(self) -> None:
        """Background loop that periodically removes expired sessions.

        Runs as a daemon thread with a sleep interval of half the TTL
        (minimum 30 seconds). Silently handles any unexpected errors
        to keep the cleanup thread alive.
        """
        interval = max(30, self._ttl_seconds // 2)
        logger.info("Session cleanup thread started, interval=%d seconds", interval)

        while True:
            time.sleep(interval)
            self._purge_expired()

    def _purge_expired(self) -> None:
        """Remove all expired sessions from the store."""
        now = time.time()
        expired_ids: list[str] = []

        with self._lock:
            for session_id, session in self._sessions.items():
                age = now - session["created_at"]
                if age > self._ttl_seconds:
                    expired_ids.append(session_id)

            for session_id in expired_ids:
                del self._sessions[session_id]

            # Clean up active_analyses entries pointing to expired sessions
            stale_sids = [
                sid for sid, s_id in self._active_analyses.items()
                if s_id in expired_ids
            ]
            for sid in stale_sids:
                del self._active_analyses[sid]

        if expired_ids:
            logger.info("Purged %d expired sessions", len(expired_ids))


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _transfer_issue_statuses(
    old_response: AnalyzeResponse,
    new_response: AnalyzeResponse,
) -> None:
    """Transfer user-modified issue statuses from old to new response.

    When the LLM background phase completes and replaces the session
    response, any accept/dismiss/manually-fixed actions the user took
    during the LLM phase must be preserved.

    Args:
        old_response: The previous response with potential user actions.
        new_response: The incoming response to receive preserved statuses.
    """
    old_statuses: dict[str, IssueStatus] = {}
    for issue in old_response.issues:
        if issue.status != IssueStatus.OPEN:
            old_statuses[issue.id] = issue.status

    if not old_statuses:
        return

    for issue in new_response.issues:
        saved = old_statuses.get(issue.id)
        if saved is not None:
            issue.status = saved

    # Recalculate score to reflect preserved statuses
    new_score = calculate_score(
        new_response.issues, new_response.report.word_count
    )
    new_response.score = new_score
    logger.debug(
        "Transferred %d user-modified statuses, recalculated score=%d",
        len(old_statuses), new_score.score,
    )


# ---------------------------------------------------------------------------

_store_instance: Optional[SessionStore] = None
_store_lock: threading.Lock = threading.Lock()


def get_session_store() -> SessionStore:
    """Return the singleton SessionStore instance.

    Creates the store on first call. Thread-safe via a module-level lock.

    Returns:
        The shared SessionStore instance.
    """
    global _store_instance  # noqa: PLW0603
    if _store_instance is None:
        with _store_lock:
            if _store_instance is None:
                _store_instance = SessionStore()
    return _store_instance

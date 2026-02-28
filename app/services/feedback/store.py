"""SQLite-backed feedback persistence store.

Stores user feedback (thumbs up/down) on detected issues for false
positive tracking and rule quality monitoring. Falls back to an
in-memory SQLite database when persistent storage is unavailable.

Usage:
    from app.services.feedback.store import get_feedback_store

    store = get_feedback_store()
    row_id = store.store_feedback("s1", "i1", "passive_voice", True)
    stats = store.get_rule_feedback_stats("passive_voice")
"""

import logging
import os
import sqlite3
import threading
from typing import Optional

from app.config import Config

logger = logging.getLogger(__name__)

_CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    issue_id TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    thumbs_up BOOLEAN NOT NULL,
    comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

_INSERT_SQL = """
INSERT INTO feedback (session_id, issue_id, rule_type, thumbs_up, comment)
VALUES (?, ?, ?, ?, ?)
"""

_STATS_SQL = """
SELECT
    COUNT(*) AS total,
    SUM(CASE WHEN thumbs_up = 1 THEN 1 ELSE 0 END) AS positive,
    SUM(CASE WHEN thumbs_up = 0 THEN 1 ELSE 0 END) AS negative
FROM feedback
WHERE rule_type = ?
"""


class FeedbackStore:
    """SQLite-backed store for user feedback on editorial issues.

    Persists thumbs up/down feedback with optional comments. Provides
    aggregate statistics per rule type for false positive rate tracking.

    The store uses parameterized queries exclusively and creates the
    database directory structure on initialization if needed.

    Attributes:
        _db_path: Path to the SQLite database file, or ":memory:".
        _connection: The SQLite connection instance.
        _lock: Threading lock for thread-safe database access.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """Initialize the feedback store and create the schema.

        If ``db_path`` is not provided, uses the configured
        ``FEEDBACK_DB_PATH`` or falls back to ``:memory:`` when
        ``FEEDBACK_PERSISTENT`` is False.

        Args:
            db_path: Path to the SQLite database file. Use ``:memory:``
                for a non-persistent in-memory database.
        """
        self._db_path: str = self._resolve_db_path(db_path)
        self._lock: threading.Lock = threading.Lock()
        self._connection: sqlite3.Connection = self._create_connection()
        self._initialize_schema()

    def store_feedback(
        self,
        session_id: str,
        issue_id: str,
        rule_type: str,
        thumbs_up: bool,
        comment: Optional[str] = None,
    ) -> int:
        """Store a feedback entry for an issue.

        Args:
            session_id: The analysis session identifier.
            issue_id: The issue identifier.
            rule_type: The rule that detected the issue.
            thumbs_up: True for positive feedback, False for negative.
            comment: Optional user comment.

        Returns:
            The auto-incremented row ID of the inserted record.
        """
        with self._lock:
            cursor = self._connection.execute(
                _INSERT_SQL,
                (session_id, issue_id, rule_type, thumbs_up, comment),
            )
            self._connection.commit()
            row_id = cursor.lastrowid

        logger.info(
            "Stored feedback row %d: rule=%s, thumbs_up=%s",
            row_id, rule_type, thumbs_up,
        )
        return row_id

    def get_rule_feedback_stats(self, rule_type: str) -> dict[str, object]:
        """Get aggregate feedback statistics for a rule type.

        Args:
            rule_type: The rule identifier to query.

        Returns:
            Dict with ``total``, ``positive``, ``negative``, and
            ``false_positive_rate`` keys. The false positive rate is
            the ratio of negative to total feedback (0.0 when no
            feedback exists).
        """
        with self._lock:
            cursor = self._connection.execute(_STATS_SQL, (rule_type,))
            row = cursor.fetchone()

        total = row[0] or 0
        positive = row[1] or 0
        negative = row[2] or 0
        false_positive_rate = negative / total if total > 0 else 0.0

        return {
            "total": total,
            "positive": positive,
            "negative": negative,
            "false_positive_rate": round(false_positive_rate, 4),
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_db_path(db_path: Optional[str]) -> str:
        """Determine the database path from arguments and configuration.

        Args:
            db_path: Explicitly provided path, or None to use config.

        Returns:
            The resolved database path string.
        """
        if db_path is not None:
            return db_path

        if not Config.FEEDBACK_PERSISTENT:
            logger.info("Feedback persistence disabled; using in-memory database")
            return ":memory:"

        return Config.FEEDBACK_DB_PATH

    def _create_connection(self) -> sqlite3.Connection:
        """Create and return a SQLite connection.

        Creates the parent directory if the path is a file path and the
        directory does not exist. Falls back to ``:memory:`` if directory
        creation fails.

        Returns:
            An open SQLite connection.
        """
        if self._db_path != ":memory:":
            self._ensure_directory()

        connection = sqlite3.connect(self._db_path, check_same_thread=False)
        logger.info("Feedback database connected at: %s", self._db_path)
        return connection

    def _ensure_directory(self) -> None:
        """Create the parent directory for the database file if needed.

        Falls back to in-memory storage if directory creation fails due
        to filesystem errors.
        """
        db_dir = os.path.dirname(self._db_path)
        if not db_dir:
            return

        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError as exc:
            logger.warning(
                "Cannot create feedback database directory '%s': %s. "
                "Falling back to in-memory database.",
                db_dir, exc,
            )
            self._db_path = ":memory:"

    def _initialize_schema(self) -> None:
        """Create the feedback table if it does not exist."""
        with self._lock:
            self._connection.execute(_CREATE_TABLE_SQL)
            self._connection.commit()
        logger.info("Feedback database schema initialized")


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_store_instance: Optional[FeedbackStore] = None
_store_lock: threading.Lock = threading.Lock()


def get_feedback_store() -> FeedbackStore:
    """Return the singleton FeedbackStore instance.

    Creates the store on first call. Thread-safe via a module-level lock.

    Returns:
        The shared FeedbackStore instance.
    """
    global _store_instance  # noqa: PLW0603
    if _store_instance is None:
        with _store_lock:
            if _store_instance is None:
                _store_instance = FeedbackStore()
    return _store_instance

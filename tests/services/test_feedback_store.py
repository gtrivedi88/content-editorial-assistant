"""Tests for the SQLite-backed feedback persistence store.

Validates feedback storage and retrieval, aggregate statistics per rule,
in-memory fallback when persistent storage is disabled, and thread-safe
concurrent access.
"""

import logging
import threading
from typing import Any
from unittest.mock import patch

import pytest

from app.services.feedback.store import FeedbackStore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestFeedbackStore:
    """Tests for FeedbackStore with in-memory SQLite backend."""

    def test_store_and_retrieve_feedback(self) -> None:
        """Stored feedback is retrievable via aggregate stats.

        After inserting a positive feedback entry, the stats for the
        corresponding rule should reflect one total and one positive.
        """
        store = FeedbackStore(db_path=":memory:")

        row_id: int = store.store_feedback(
            session_id="s1",
            issue_id="i1",
            rule_type="passive_voice",
            thumbs_up=True,
            comment="Good catch",
        )

        assert row_id >= 1

        stats = store.get_rule_feedback_stats("passive_voice")
        assert stats["total"] == 1
        assert stats["positive"] == 1
        assert stats["negative"] == 0
        assert stats["false_positive_rate"] == 0.0

    def test_negative_feedback_increments_negative_count(self) -> None:
        """Negative (thumbs-down) feedback increments the negative counter.

        The false positive rate should reflect the proportion of negative
        feedback relative to the total.
        """
        store = FeedbackStore(db_path=":memory:")

        store.store_feedback("s1", "i1", "contraction_usage", True)
        store.store_feedback("s1", "i2", "contraction_usage", False)

        stats = store.get_rule_feedback_stats("contraction_usage")
        assert stats["total"] == 2
        assert stats["positive"] == 1
        assert stats["negative"] == 1
        assert stats["false_positive_rate"] == 0.5

    def test_stats_for_unknown_rule_returns_zeros(self) -> None:
        """Querying stats for a rule with no feedback returns all zeros.

        The store should handle unknown rules gracefully rather than
        raising errors.
        """
        store = FeedbackStore(db_path=":memory:")

        stats = store.get_rule_feedback_stats("nonexistent_rule")
        assert stats["total"] == 0
        assert stats["positive"] == 0
        assert stats["negative"] == 0
        assert stats["false_positive_rate"] == 0.0

    def test_memory_fallback_when_persistent_disabled(self) -> None:
        """FeedbackStore falls back to in-memory when persistence is disabled.

        When Config.FEEDBACK_PERSISTENT is False and no db_path is
        provided, the store should use ':memory:' and still function
        correctly.
        """
        with patch("app.services.feedback.store.Config") as mock_config:
            mock_config.FEEDBACK_PERSISTENT = False
            mock_config.FEEDBACK_DB_PATH = "/nonexistent/path/feedback.db"

            store = FeedbackStore()

        assert store._db_path == ":memory:"

        # Verify functional -- store and retrieve
        store.store_feedback("s1", "i1", "test_rule", True)
        stats = store.get_rule_feedback_stats("test_rule")
        assert stats["total"] == 1

    def test_multiple_rules_tracked_independently(self) -> None:
        """Feedback for different rules is tracked independently.

        Inserting feedback for rule_a should not affect stats for rule_b.
        """
        store = FeedbackStore(db_path=":memory:")

        store.store_feedback("s1", "i1", "rule_a", True)
        store.store_feedback("s1", "i2", "rule_a", True)
        store.store_feedback("s1", "i3", "rule_b", False)

        stats_a = store.get_rule_feedback_stats("rule_a")
        stats_b = store.get_rule_feedback_stats("rule_b")

        assert stats_a["total"] == 2
        assert stats_a["positive"] == 2
        assert stats_a["negative"] == 0

        assert stats_b["total"] == 1
        assert stats_b["positive"] == 0
        assert stats_b["negative"] == 1

    def test_store_feedback_with_no_comment(self) -> None:
        """Feedback can be stored without a comment (None default).

        The comment field is optional. Storing without a comment should
        succeed and not affect aggregate stats.
        """
        store = FeedbackStore(db_path=":memory:")

        row_id: int = store.store_feedback(
            session_id="s1",
            issue_id="i1",
            rule_type="tone_rule",
            thumbs_up=False,
        )

        assert row_id >= 1

        stats = store.get_rule_feedback_stats("tone_rule")
        assert stats["total"] == 1
        assert stats["negative"] == 1

    def test_false_positive_rate_calculation(self) -> None:
        """False positive rate is calculated correctly and rounded to 4 decimals.

        With 1 positive and 2 negative entries, the false positive rate
        should be 2/3 = 0.6667 (rounded to 4 decimal places).
        """
        store = FeedbackStore(db_path=":memory:")

        store.store_feedback("s1", "i1", "fp_rule", True)
        store.store_feedback("s1", "i2", "fp_rule", False)
        store.store_feedback("s1", "i3", "fp_rule", False)

        stats = store.get_rule_feedback_stats("fp_rule")
        assert stats["total"] == 3
        assert stats["positive"] == 1
        assert stats["negative"] == 2
        assert stats["false_positive_rate"] == round(2 / 3, 4)

    def test_thread_safe_concurrent_writes(self) -> None:
        """Concurrent feedback writes from multiple threads do not corrupt data.

        The store uses a threading.Lock for all database operations.
        Multiple threads writing simultaneously should produce correct
        aggregate counts.
        """
        store = FeedbackStore(db_path=":memory:")
        num_threads = 10
        barrier = threading.Barrier(num_threads)
        errors: list[str] = []

        def _write_feedback(thread_id: int) -> None:
            """Write feedback from a thread, waiting for all threads first."""
            try:
                barrier.wait(timeout=5)
                store.store_feedback(
                    session_id=f"s-{thread_id}",
                    issue_id=f"i-{thread_id}",
                    rule_type="concurrent_rule",
                    thumbs_up=(thread_id % 2 == 0),
                )
            except Exception as exc:
                errors.append(f"Thread {thread_id}: {exc}")

        threads = [
            threading.Thread(target=_write_feedback, args=(i,))
            for i in range(num_threads)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10)

        assert not errors, f"Thread errors: {errors}"

        stats = store.get_rule_feedback_stats("concurrent_rule")
        assert stats["total"] == num_threads
        # Even-numbered threads give positive, odd give negative
        assert stats["positive"] == num_threads // 2
        assert stats["negative"] == num_threads - num_threads // 2

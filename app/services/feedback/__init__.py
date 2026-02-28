"""Feedback service — user feedback persistence and retrieval.

Provides the ``FeedbackStore`` class and the singleton
``get_feedback_store()`` accessor for storing and querying
user feedback on editorial issues.
"""

from app.services.feedback.store import FeedbackStore, get_feedback_store

__all__ = ["FeedbackStore", "get_feedback_store"]

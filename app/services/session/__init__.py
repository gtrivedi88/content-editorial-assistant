"""Session service — thread-safe session store with TTL expiration.

Provides the singleton ``get_session_store()`` accessor and the
``SessionStore`` class for managing analysis sessions.
"""

from app.services.session.store import SessionStore, get_session_store

__all__ = ["SessionStore", "get_session_store"]

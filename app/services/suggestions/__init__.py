"""Suggestions service — LLM-powered rewrite suggestions for flagged issues.

Provides the ``get_suggestion()`` function as the public entry point
for retrieving rewrite suggestions for detected issues.
"""

from app.services.suggestions.engine import get_suggestion

__all__ = ["get_suggestion"]

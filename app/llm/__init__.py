"""LLM integration package -- multi-provider client, prompt templates, and response parsing.

Exports:
    LLMClient: Multi-provider LLM client using ``models.ModelManager``.
    select_excerpts: Category-triggered style guide excerpt selection.
"""

try:
    from app.llm.client import LLMClient
    from app.llm.excerpt_selector import select_excerpts
except ImportError:
    pass

__all__ = [
    "LLMClient",
    "select_excerpts",
]

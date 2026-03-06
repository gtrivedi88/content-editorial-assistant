"""LLM client using the multi-provider ModelManager.

Delegates text generation to ``models.ModelManager`` which supports
Ollama, generic OpenAI-compatible APIs, and LlamaStack providers.
Retries transient failures with exponential backoff and runs
concurrent block-level analysis via a bounded thread pool.

Usage:
    from app.llm.client import LLMClient

    client = LLMClient()
    if client.is_available():
        issues = client.analyze_block(text, sentences, excerpts)
"""

import logging
from concurrent.futures import ThreadPoolExecutor

from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import Config
from app.llm.parser import (
    parse_analysis_response,
    parse_judge_response,
    parse_suggestion_response,
)
from app.llm.prompts import (
    build_global_prompt,
    build_granular_prompt,
    build_judge_prompt,
    build_suggestion_prompt,
)

logger = logging.getLogger(__name__)

# JSON schema for structured LLM analysis output.  Providers that support
# JSON mode for analysis calls.  Uses ``{"type": "json_object"}`` which
# is supported by Gemini, OpenAI, and Ollama.  The exact schema is
# described in the system prompt; this just constrains the model to
# return valid JSON, eliminating code-fence parsing failures.
_ANALYSIS_RESPONSE_FORMAT: dict = {"type": "json_object"}

# Lazy-initialized singleton to avoid import-time side effects
_model_manager_instance = None


def _get_model_manager():
    """Return a lazily-initialized ModelManager singleton.

    Returns:
        The shared ModelManager instance.
    """
    global _model_manager_instance  # noqa: PLW0603
    if _model_manager_instance is None:
        from models.model_manager import ModelManager
        _model_manager_instance = ModelManager()
    return _model_manager_instance


class LLMClient:
    """Multi-provider LLM client for the Content Editorial Assistant.

    Wraps ``models.ModelManager`` to provide analysis and suggestion
    capabilities.  All methods return empty results immediately when
    the LLM is disabled or the provider is unavailable.

    Attributes:
        _model_manager: Shared ModelManager instance.
        _executor: Thread pool for concurrent block analysis.
    """

    def __init__(self) -> None:
        """Initialize the LLM client with the shared ModelManager."""
        self._model_manager = _get_model_manager()
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(
            max_workers=Config.LLM_MAX_CONCURRENT,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def is_available(self) -> bool:
        """Check whether the LLM integration is enabled and configured.

        Returns:
            True if ``LLM_ENABLED`` is set and the provider is available.
        """
        if not Config.LLM_ENABLED:
            return False
        try:
            return self._model_manager.is_available()
        except (RuntimeError, OSError) as exc:
            logger.debug("Model availability check failed: %s", exc)
            return False

    def analyze_block(
        self,
        text: str,
        sentences: list[str],
        style_guide_excerpts: list[dict],
        content_type: str = "concept",
        acronym_context: dict[str, str] | None = None,
        document_outline: str | None = None,
    ) -> list[dict]:
        """Run granular per-block analysis via the LLM.

        Args:
            text: The text block to analyse.
            sentences: Individual sentences from the block.
            style_guide_excerpts: Relevant style guide excerpt dicts.
            content_type: Modular documentation type (concept, procedure, etc.).
            acronym_context: Known acronym definitions from the document.
            document_outline: Compact heading outline of the full document.

        Returns:
            List of issue dicts with ``source="llm"``, or empty list
            on failure or when the LLM is unavailable.
        """
        if not self.is_available():
            return []

        system_prompt, user_prompt = build_granular_prompt(
            text, sentences, style_guide_excerpts,
            content_type=content_type,
            acronym_context=acronym_context,
            document_outline=document_outline,
        )
        return self._safe_analysis_call(user_prompt, system_prompt=system_prompt)

    def analyze_global(
        self,
        full_text: str,
        content_type: str,
        style_guide_excerpts: list[dict],
        document_outline: str | None = None,
        abstract_context: str | None = None,
    ) -> list[dict]:
        """Run global document-level analysis via the LLM.

        Checks tone consistency, flow, minimalism, wordiness,
        structure, and accessibility across the entire document.

        Args:
            full_text: Full document text.
            content_type: Modular documentation type (concept/procedure/etc.).
            style_guide_excerpts: Relevant style guide excerpt dicts.
            document_outline: Compact heading outline for structural review.
            abstract_context: Module abstract (first paragraph after heading)
                for targeted short-description quality evaluation.

        Returns:
            List of issue dicts with ``source="llm"``, or empty list
            on failure or when the LLM is unavailable.
        """
        if not self.is_available():
            return []

        system_prompt, user_prompt = build_global_prompt(
            full_text, content_type, style_guide_excerpts,
            document_outline=document_outline,
            abstract_context=abstract_context,
        )
        return self._safe_analysis_call(user_prompt, system_prompt=system_prompt)

    def suggest(
        self,
        flagged_text: str,
        context_sentences: list[str],
        rule_info: dict,
        style_guide_excerpt: dict,
    ) -> dict:
        """Request a rewrite suggestion from the LLM.

        Args:
            flagged_text: The exact text span that was flagged.
            context_sentences: Surrounding sentences for context.
            rule_info: Dict with rule_name, category, message, severity.
            style_guide_excerpt: The relevant style guide excerpt dict.

        Returns:
            Dict with ``rewritten_text``, ``explanation``, ``confidence``
            keys, or an error dict when unavailable/failed.
        """
        if not self.is_available():
            return {"error": "LLM is not available"}

        system_prompt, user_prompt = build_suggestion_prompt(
            flagged_text, context_sentences, rule_info, style_guide_excerpt,
        )
        return self._safe_suggestion_call(
            user_prompt, system_prompt=system_prompt,
        )

    def judge_issues(
        self,
        issues: list[dict],
        document_excerpt: str,
        content_type: str,
    ) -> tuple[list[int], list[int]]:
        """Run self-correction judge on a batch of LLM issues.

        Asks the LLM to review issues and decide which are real (keep)
        and which are false positives (drop).

        Args:
            issues: List of issue dicts to review.
            document_excerpt: Representative excerpt for context.
            content_type: Modular documentation type.

        Returns:
            Tuple of (keep_indices, drop_indices).  On failure,
            all issues are kept (fail-open).
        """
        if not self.is_available() or not issues:
            return list(range(len(issues))), []

        system_prompt, user_prompt = build_judge_prompt(
            issues, document_excerpt, content_type,
        )

        try:
            raw_text = self._generate(
                user_prompt,
                system_prompt=system_prompt,
                response_format=_ANALYSIS_RESPONSE_FORMAT,
            )
            if not raw_text:
                return list(range(len(issues))), []
            return parse_judge_response(raw_text, len(issues))
        except (ConnectionError, TimeoutError, RuntimeError) as exc:
            logger.warning("LLM judge call failed: %s", exc)
        except (ValueError, KeyError) as exc:
            logger.warning("LLM judge response parsing failed: %s", exc)
        return list(range(len(issues))), []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _safe_analysis_call(
        self, prompt: str, system_prompt: str = "",
    ) -> list[dict]:
        """Call the LLM and parse an analysis response safely.

        Args:
            prompt: The user prompt string.
            system_prompt: Invariant system instructions.

        Returns:
            Parsed issue list, or empty list on any failure.
        """
        try:
            raw_text = self._generate(
                prompt,
                system_prompt=system_prompt,
                response_format=_ANALYSIS_RESPONSE_FORMAT,
            )
            if not raw_text:
                return []
            return parse_analysis_response(raw_text)
        except (ConnectionError, TimeoutError, RuntimeError) as exc:
            logger.warning("LLM analysis call failed: %s", exc)
        except (ValueError, KeyError) as exc:
            logger.warning("LLM analysis response parsing failed: %s", exc)
        return []

    def _safe_suggestion_call(
        self, prompt: str, system_prompt: str = "",
    ) -> dict:
        """Call the LLM and parse a suggestion response safely.

        Args:
            prompt: The user prompt string.
            system_prompt: Invariant system instructions.

        Returns:
            Parsed suggestion dict, or error dict on failure.
        """
        try:
            raw_text = self._generate(
                prompt,
                temperature=Config.MODEL_SUGGESTION_TEMPERATURE,
                system_prompt=system_prompt,
            )
            if not raw_text:
                return {"error": "LLM returned empty response"}
            return parse_suggestion_response(raw_text)
        except (ConnectionError, TimeoutError, RuntimeError) as exc:
            logger.warning("LLM suggestion call failed: %s", exc)
        except (ValueError, KeyError) as exc:
            logger.warning("LLM suggestion response parsing failed: %s", exc)
        return {"error": "LLM request failed"}

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((ConnectionError, TimeoutError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    def _generate(
        self,
        prompt: str,
        temperature: float | None = None,
        **kwargs: object,
    ) -> str:
        """Generate text via the ModelManager with retry logic.

        Retries automatically on connection and timeout errors.
        Extra keyword arguments (e.g. ``response_format``) are
        forwarded to the provider.

        Args:
            prompt: The prompt text to send.
            temperature: Sampling temperature.  Defaults to
                ``Config.MODEL_ANALYSIS_TEMPERATURE`` when not supplied.
            **kwargs: Additional provider parameters.

        Returns:
            Generated text string, or empty string on failure.

        Raises:
            ConnectionError: On network failures (retried).
            TimeoutError: When the request exceeds the timeout (retried).
        """
        if temperature is None:
            temperature = Config.MODEL_ANALYSIS_TEMPERATURE
        if Config.MODEL_SEED is not None:
            kwargs.setdefault("seed", Config.MODEL_SEED)
        return self._model_manager.generate_text(
            prompt, temperature=temperature, **kwargs,
        )


# ------------------------------------------------------------------
# Module-level singleton and wrapper functions
# ------------------------------------------------------------------

_client_instance: LLMClient | None = None


def _get_client() -> LLMClient:
    """Return a lazily-initialized LLMClient singleton.

    Avoids creating a new ThreadPoolExecutor and ModelManager
    connection on every call from the orchestrator.

    Returns:
        The shared LLMClient instance.
    """
    global _client_instance  # noqa: PLW0603
    if _client_instance is None:
        _client_instance = LLMClient()
    return _client_instance


def analyze_block(
    text: str,
    sentences: list[str],
    content_type: str,
    acronym_context: dict[str, str] | None = None,
    style_guide_excerpts: list[dict] | None = None,
    document_outline: str | None = None,
) -> list[dict]:
    """Module-level wrapper for per-block LLM analysis.

    Called by the orchestrator which imports this function directly.

    Args:
        text: The text block to analyse.
        sentences: Individual sentences from the block.
        content_type: Modular documentation type (concept, procedure, etc.).
        acronym_context: Known acronym definitions from the document.
        style_guide_excerpts: Relevant style guide excerpt dicts.
        document_outline: Compact heading outline of the full document.

    Returns:
        List of issue dicts from the LLM, or empty list.
    """
    return _get_client().analyze_block(
        text, sentences, style_guide_excerpts or [],
        content_type=content_type,
        acronym_context=acronym_context,
        document_outline=document_outline,
    )


def analyze_global(
    text: str,
    content_type: str,
    style_guide_excerpts: list[dict] | None = None,
    document_outline: str | None = None,
    abstract_context: str | None = None,
) -> list[dict]:
    """Module-level wrapper for full-document LLM analysis.

    Called by the orchestrator which imports this function directly.

    Args:
        text: Full document text.
        content_type: Modular documentation type.
        style_guide_excerpts: Relevant style guide excerpt dicts.
        document_outline: Compact heading outline for structural review.
        abstract_context: Module abstract for short-description quality check.

    Returns:
        List of issue dicts from the LLM, or empty list.
    """
    return _get_client().analyze_global(
        text, content_type, style_guide_excerpts or [],
        document_outline=document_outline,
        abstract_context=abstract_context,
    )


def judge_issues(
    issues: list[dict],
    document_excerpt: str,
    content_type: str,
) -> tuple[list[int], list[int]]:
    """Module-level wrapper for LLM judge self-correction.

    Called by the orchestrator to filter false positives.

    Args:
        issues: List of issue dicts to review.
        document_excerpt: Representative excerpt for context.
        content_type: Modular documentation type.

    Returns:
        Tuple of (keep_indices, drop_indices).
    """
    return _get_client().judge_issues(issues, document_excerpt, content_type)

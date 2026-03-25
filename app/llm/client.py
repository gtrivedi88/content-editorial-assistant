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
    parse_analysis_response_ex,
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

# Structured JSON schema for LLM analysis output.  Constrains the
# model's output to the exact field names, types, and enum values
# expected by the parser — reduces run-to-run variance by shrinking
# the output space the model samples from.
_ISSUE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "flagged_text": {"type": "string"},
        "message": {"type": "string"},
        "suggestions": {"type": "array", "items": {"type": "string"}},
        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
        "category": {
            "type": "string",
            "enum": ["style", "grammar", "punctuation", "structure", "audience"],
        },
        "sentence": {"type": "string"},
        "sentence_index": {"type": "integer"},
        "confidence": {"type": "number"},
    },
    "required": [
        "flagged_text", "message", "suggestions", "severity",
        "category", "sentence", "sentence_index", "confidence",
    ],
    "additionalProperties": False,
}

_ANALYSIS_RESPONSE_FORMAT: dict = {
    "type": "json_schema",
    "json_schema": {
        "name": "analysis_response",
        "schema": {
            "type": "object",
            "properties": {
                "reasoning": {"type": "string", "maxLength": 1000},
                "issues": {"type": "array", "items": _ISSUE_SCHEMA},
            },
            "required": ["reasoning", "issues"],
            "additionalProperties": False,
        },
    },
}

# Fallback for providers that don't support json_schema (e.g. older Ollama)
_ANALYSIS_RESPONSE_FORMAT_BASIC: dict = {"type": "json_object"}

# Provider-agnostic set of finish_reason values that indicate output
# was truncated.  Values are upper-cased for matching (OpenAI returns
# "length", Gemini returns "MAX_TOKENS").
_TRUNCATION_FINISH_REASONS: frozenset[str] = frozenset({"LENGTH", "MAX_TOKENS"})

# Per-content-type multipliers for token budget prediction.
_CONTENT_TYPE_MULTIPLIERS: dict[str, float] = {
    "procedure": 1.2,
    "assembly": 1.15,
    "release_notes": 1.1,
    "reference": 0.9,
}

# Reasoning effort → thinking token baseline map.
_EFFORT_BASE_THINK: dict[str, int] = {
    "none": 200,
    "low": 1000,
    "medium": 8000,
}

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
        self._current_analysis_format: dict = _ANALYSIS_RESPONSE_FORMAT

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
        det_issue_count: int = 0,
    ) -> list[dict]:
        """Run granular per-block analysis via the LLM.

        Args:
            text: The text block to analyse.
            sentences: Individual sentences from the block.
            style_guide_excerpts: Relevant style guide excerpt dicts.
            content_type: Modular documentation type (concept, procedure, etc.).
            acronym_context: Known acronym definitions from the document.
            document_outline: Compact heading outline of the full document.
            det_issue_count: Phase 1 deterministic issue count (messiness signal
                for dynamic token budget prediction).

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
        max_tokens = self._dynamic_max_tokens(
            "granular",
            input_text_len=len(text),
            sentence_count=len(sentences),
            det_issue_count=det_issue_count,
            content_type=content_type,
        )
        return self._safe_analysis_call(
            user_prompt, system_prompt=system_prompt, max_tokens=max_tokens,
        )

    def analyze_global(
        self,
        full_text: str,
        content_type: str,
        style_guide_excerpts: list[dict],
        document_outline: str | None = None,
        abstract_context: str | None = None,
        det_issue_count: int = 0,
    ) -> list[dict]:
        """Run global document-level analysis via the LLM.

        Checks tone consistency, audience level, accessibility, and
        short description quality across the entire document.

        Args:
            full_text: Full document text.
            content_type: Modular documentation type (concept/procedure/etc.).
            style_guide_excerpts: Relevant style guide excerpt dicts.
            document_outline: Compact heading outline for structural review.
            abstract_context: Module abstract (first paragraph after heading)
                for targeted short-description quality evaluation.
            det_issue_count: Phase 1 deterministic issue count (messiness signal
                for dynamic token budget prediction).

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
        max_tokens = self._dynamic_max_tokens(
            "global",
            input_text_len=len(full_text),
            content_type=content_type,
            det_issue_count=det_issue_count,
        )
        return self._safe_analysis_call(
            user_prompt, system_prompt=system_prompt, max_tokens=max_tokens,
        )

    def suggest(
        self,
        flagged_text: str,
        context_sentences: list[str],
        rule_info: dict,
        style_guide_excerpt: dict,
        sentence: str = "",
    ) -> dict:
        """Request a rewrite suggestion from the LLM.

        Args:
            flagged_text: The exact text span that was flagged.
            context_sentences: Surrounding sentences for context.
            rule_info: Dict with rule_name, category, message, severity.
            style_guide_excerpt: The relevant style guide excerpt dict.
            sentence: The containing sentence for anchored rewriting.

        Returns:
            Dict with ``rewritten_text``, ``explanation``, ``confidence``
            keys, or an error dict when unavailable/failed.
        """
        if not self.is_available():
            return {"error": "LLM is not available"}

        system_prompt, user_prompt = build_suggestion_prompt(
            flagged_text, context_sentences, rule_info, style_guide_excerpt,
            sentence=sentence,
        )
        return self._safe_suggestion_call(
            user_prompt, system_prompt=system_prompt,
            flagged_text=flagged_text,
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
                response_format=_ANALYSIS_RESPONSE_FORMAT_BASIC,
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

    @staticmethod
    def _dynamic_max_tokens(
        phase: str,
        input_text_len: int = 0,
        num_issues: int = 0,
        content_type: str = "concept",
        sentence_count: int = 0,
        det_issue_count: int = 0,
    ) -> int:
        """Predict the required ``max_tokens`` budget for a given phase.

        Uses structural features of the input to estimate output size
        plus a reasoning-effort-scaled thinking baseline.

        Args:
            phase: One of ``granular``, ``global``, ``judge``, ``suggest``.
            input_text_len: Character length of the input text.
            num_issues: Number of issues (for judge phase).
            content_type: Document content type for multiplier lookup.
            sentence_count: Number of sentences in the block/document.
            det_issue_count: Phase 1 deterministic issue count (messiness signal).

        Returns:
            Token budget clamped to ``[1024, Config.MODEL_MAX_TOKENS]``.
        """
        effort = getattr(Config, 'GEMINI_REASONING_EFFORT', 'low') or 'low'
        effort = effort.strip().lower()

        # High effort → return cap immediately (model decides its own budget)
        if effort == "high":
            return Config.MODEL_MAX_TOKENS

        base_think = _EFFORT_BASE_THINK.get(effort, 1000)

        if phase == "granular":
            predicted_issues = max(3, sentence_count // 2, det_issue_count // 3)
            output_tokens = 200 + predicted_issues * 85
            think_tokens = base_think + sentence_count * 15
            budget = output_tokens + think_tokens
        elif phase == "global":
            output_tokens = 300 + input_text_len // 40
            think_tokens = int(base_think * 1.5)
            budget = output_tokens + think_tokens
        elif phase == "judge":
            output_tokens = 100 + num_issues * 15
            think_tokens = int(base_think * 0.8)
            budget = output_tokens + think_tokens
        elif phase == "suggest":
            budget = base_think + 500
        else:
            budget = base_think + 1000

        # Content-type scaling
        multiplier = _CONTENT_TYPE_MULTIPLIERS.get(content_type, 1.0)
        budget = int(budget * multiplier)

        return max(1024, min(budget, Config.MODEL_MAX_TOKENS))

    def _safe_analysis_call(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int | None = None,
    ) -> list[dict]:
        """Call the LLM and parse an analysis response safely.

        Tries the current preferred response format first.  If the
        provider rejects it (empty response or RuntimeError from HTTP
        400), falls back to the basic ``json_object`` format and
        remembers the working format for subsequent calls.

        On truncation (detected via parser salvage or provider
        ``finish_reason``), retries once with a 1.5x token budget.

        Args:
            prompt: The user prompt string.
            system_prompt: Invariant system instructions.
            max_tokens: Optional explicit token budget override.

        Returns:
            Parsed issue list, or empty list on any failure.
        """
        formats = [self._current_analysis_format]
        if self._current_analysis_format is not _ANALYSIS_RESPONSE_FORMAT_BASIC:
            formats.append(_ANALYSIS_RESPONSE_FORMAT_BASIC)

        for fmt in formats:
            try:
                result_meta: dict = {}
                gen_kwargs: dict = {
                    "system_prompt": system_prompt,
                    "response_format": fmt,
                    "_result_meta": result_meta,
                }
                if max_tokens is not None:
                    gen_kwargs["max_tokens"] = max_tokens

                raw_text = self._generate(prompt, **gen_kwargs)
                if not raw_text:
                    continue

                # Reasoning instrumentation: log reasoning vs issues split
                self._log_reasoning_split(raw_text)

                issues, truncated = parse_analysis_response_ex(raw_text)

                # Check provider-level truncation signal
                fr = str(result_meta.get("finish_reason", "")).upper()
                if fr in _TRUNCATION_FINISH_REASONS:
                    truncated = True

                if fmt is not self._current_analysis_format:
                    logger.info(
                        "Switching analysis response format to basic "
                        "json_object (provider rejected json_schema)",
                    )
                    self._current_analysis_format = fmt

                # On truncation, retry once with a larger budget
                if truncated:
                    retried = self._retry_truncated_analysis(
                        prompt, system_prompt, fmt, max_tokens,
                    )
                    if len(retried) > len(issues):
                        return retried

                return issues
            except (ConnectionError, TimeoutError, RuntimeError) as exc:
                logger.warning("LLM analysis call failed: %s", exc)
                continue
            except (ValueError, KeyError) as exc:
                logger.warning(
                    "LLM analysis response parsing failed: %s", exc,
                )
                break
        return []

    @staticmethod
    def _log_reasoning_split(raw_text: str) -> None:
        """Log the character-count split between reasoning and issues.

        Helps quantify whether reasoning is consuming a disproportionate
        share of the output budget (Issue #16).
        """
        import json as _json
        try:
            stripped = raw_text.strip()
            if stripped.startswith("```"):
                stripped = stripped.lstrip("`json\n").rstrip("`\n").strip()
            data = _json.loads(stripped)
            if isinstance(data, dict):
                r_len = len(data.get("reasoning", ""))
                i_text = _json.dumps(data.get("issues", []))
                logger.info(
                    "LLM output split: reasoning=%d chars, issues=%d chars, total=%d",
                    r_len, len(i_text), len(raw_text),
                )
        except (ValueError, TypeError):
            pass

    def _retry_truncated_analysis(
        self,
        prompt: str,
        system_prompt: str,
        fmt: dict,
        original_max_tokens: int | None,
    ) -> list[dict]:
        """Retry a truncated analysis call with 1.5x token budget.

        Args:
            prompt: The original user prompt.
            system_prompt: The original system prompt.
            fmt: The response format dict to use.
            original_max_tokens: Token budget from the original call.

        Returns:
            Parsed issue list from the retry, or empty list on failure.
        """
        base = original_max_tokens or Config.MODEL_MAX_TOKENS
        retry_budget = min(int(base * 1.5), Config.MODEL_MAX_TOKENS)
        logger.info(
            "Retrying truncated analysis with budget %d (was %d)",
            retry_budget, base,
        )
        try:
            raw_text = self._generate(
                prompt,
                system_prompt=system_prompt,
                response_format=fmt,
                max_tokens=retry_budget,
                _timeout_override=75,
            )
            if not raw_text:
                return []
            return parse_analysis_response(raw_text)
        except (ConnectionError, TimeoutError, RuntimeError) as exc:
            logger.warning("Truncation retry failed: %s", exc)
            return []

    def _safe_suggestion_call(
        self,
        prompt: str,
        system_prompt: str = "",
        flagged_text: str = "",
    ) -> dict:
        """Call the LLM and parse a suggestion response safely.

        Args:
            prompt: The user prompt string.
            system_prompt: Invariant system instructions.
            flagged_text: Original flagged text for scope detection.

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
            return parse_suggestion_response(raw_text, flagged_text=flagged_text)
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
    det_issue_count: int = 0,
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
        det_issue_count: Phase 1 deterministic issue count.

    Returns:
        List of issue dicts from the LLM, or empty list.
    """
    return _get_client().analyze_block(
        text, sentences, style_guide_excerpts or [],
        content_type=content_type,
        acronym_context=acronym_context,
        document_outline=document_outline,
        det_issue_count=det_issue_count,
    )


def analyze_global(
    text: str,
    content_type: str,
    style_guide_excerpts: list[dict] | None = None,
    document_outline: str | None = None,
    abstract_context: str | None = None,
    det_issue_count: int = 0,
) -> list[dict]:
    """Module-level wrapper for full-document LLM analysis.

    Called by the orchestrator which imports this function directly.

    Args:
        text: Full document text.
        content_type: Modular documentation type.
        style_guide_excerpts: Relevant style guide excerpt dicts.
        document_outline: Compact heading outline for structural review.
        abstract_context: Module abstract for short-description quality check.
        det_issue_count: Phase 1 deterministic issue count.

    Returns:
        List of issue dicts from the LLM, or empty list.
    """
    return _get_client().analyze_global(
        text, content_type, style_guide_excerpts or [],
        document_outline=document_outline,
        abstract_context=abstract_context,
        det_issue_count=det_issue_count,
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

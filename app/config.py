"""Application configuration loaded from environment variables.

Uses python-dotenv to load a .env file if present, then reads all
configuration values from os.environ with sensible defaults.
"""

import logging
import os
import secrets
from typing import Optional

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env file if it exists (does not override existing env vars)
load_dotenv()


class Config:
    """Central configuration for the Content Editorial Assistant.

    All values are read from environment variables with defaults suitable
    for local development.  Production deployments should set values via
    the container environment or a mounted .env file.

    Attributes:
        SECRET_KEY: Flask secret key for session signing.
        MAX_CONTENT_LENGTH: Maximum upload file size in bytes.
        MAX_TEXT_LENGTH: Maximum character count for direct text input.
        SPACY_MODEL: SpaCy language model to load.
        LLM_ENABLED: Whether LLM-based analysis is active.
        MODEL_PROVIDER: Model inference provider (llamastack, api, ollama).
        MODEL_TEMPERATURE: Default sampling temperature.
        MODEL_ANALYSIS_TEMPERATURE: Sampling temperature for analysis calls.
        MODEL_SUGGESTION_TEMPERATURE: Sampling temperature for suggestion calls.
        MODEL_SEED: Optional seed for reproducible generation.
        MODEL_MAX_TOKENS: Max output tokens per generation.
        LLM_MAX_CONCURRENT: Max concurrent LLM requests.
        LLM_GLOBAL_PASS_MAX_WORDS: Word-count ceiling for the global LLM pass.
        LLM_EXCERPT_BUDGET_MAX: Token budget for style-guide excerpts.
        CONFIDENCE_THRESHOLD: Minimum score to surface an issue.
        FEEDBACK_DB_PATH: Path to the SQLite feedback database.
        FEEDBACK_PERSISTENT: Use persistent (file) or in-memory SQLite.
        SESSION_TTL_SECONDS: Session time-to-live in seconds.
        CORS_ORIGINS: Allowed CORS origins (comma-separated or '*').
        HTTPS_PROXY: HTTPS proxy URL.
        HTTP_PROXY: HTTP proxy URL.
        NO_PROXY: Comma-separated no-proxy host list.
        ASCIIDOCTOR_MAX_CONCURRENT: Max concurrent Asciidoctor subprocesses.
        PDF_MARGIN_CROP_PERCENT: Percentage of page to crop from margins.
    """

    # --- Flask ---
    SECRET_KEY: str = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    MAX_CONTENT_LENGTH: int = int(os.environ.get("MAX_CONTENT_LENGTH", "10485760"))
    MAX_TEXT_LENGTH: int = int(os.environ.get("MAX_TEXT_LENGTH", "50000"))

    # --- SpaCy ---
    SPACY_MODEL: str = os.environ.get("SPACY_MODEL", "en_core_web_md")

    # --- LLM / Model Provider ---
    LLM_ENABLED: bool = os.environ.get("LLM_ENABLED", "True").lower() in ("true", "1", "yes")
    MODEL_PROVIDER: str = os.environ.get("MODEL_PROVIDER", "llamastack")
    MODEL_TEMPERATURE: float = float(os.environ.get("MODEL_TEMPERATURE", "0.4"))
    MODEL_ANALYSIS_TEMPERATURE: float = float(os.environ.get("MODEL_ANALYSIS_TEMPERATURE", "0.0"))
    MODEL_SUGGESTION_TEMPERATURE: float = float(os.environ.get("MODEL_SUGGESTION_TEMPERATURE", "0.2"))
    MODEL_SEED: int | None = int(os.environ.get("MODEL_SEED", "42"))
    MODEL_MAX_TOKENS: int = int(os.environ.get("MODEL_MAX_TOKENS", "3072"))
    LLM_MAX_CONCURRENT: int = int(os.environ.get("LLM_MAX_CONCURRENT", "5"))
    LLM_GLOBAL_PASS_MAX_WORDS: int = int(os.environ.get("LLM_GLOBAL_PASS_MAX_WORDS", "5000"))
    LLM_EXCERPT_BUDGET_MAX: int = int(os.environ.get("LLM_EXCERPT_BUDGET_MAX", "8000"))
    BLOCK_CACHE_TTL: int = int(os.environ.get("BLOCK_CACHE_TTL", "3600"))

    # --- Analysis ---
    CONFIDENCE_THRESHOLD: float = float(os.environ.get("CONFIDENCE_THRESHOLD", "0.7"))
    LLM_CONFIDENCE_THRESHOLD: float = float(os.environ.get("LLM_CONFIDENCE_THRESHOLD", "0.80"))
    # Defaults to False intentionally — enabling the judge pass is a
    # per-deployment decision that depends on LLM budget and latency
    # tolerance.  Set LLM_JUDGE_ENABLED=true in the environment when
    # the additional LLM round-trip is acceptable.
    LLM_JUDGE_ENABLED: bool = os.environ.get("LLM_JUDGE_ENABLED", "False").lower() in ("true", "1", "yes")

    # --- Feedback ---
    FEEDBACK_DB_PATH: str = os.environ.get("FEEDBACK_DB_PATH", "data/feedback.db")
    FEEDBACK_PERSISTENT: bool = os.environ.get("FEEDBACK_PERSISTENT", "True").lower() in ("true", "1", "yes")

    # --- Sessions ---
    SESSION_TTL_SECONDS: int = int(os.environ.get("SESSION_TTL_SECONDS", "3600"))

    # --- CORS ---
    CORS_ORIGINS: str = os.environ.get("CORS_ORIGINS", "*")

    # --- Proxy ---
    HTTPS_PROXY: Optional[str] = os.environ.get("HTTPS_PROXY")
    HTTP_PROXY: Optional[str] = os.environ.get("HTTP_PROXY")
    NO_PROXY: Optional[str] = os.environ.get("NO_PROXY")

    # --- AsciiDoc ---
    ASCIIDOCTOR_MAX_CONCURRENT: int = int(os.environ.get("ASCIIDOCTOR_MAX_CONCURRENT", "3"))

    # --- Rate Limiting ---
    RATE_LIMIT_ENABLED: bool = os.environ.get("RATE_LIMIT_ENABLED", "False").lower() in ("true", "1", "yes")
    RATE_LIMIT_DEFAULT: str = os.environ.get("RATE_LIMIT_DEFAULT", "120/minute")
    RATE_LIMIT_ANALYZE: str = os.environ.get("RATE_LIMIT_ANALYZE", "30/minute")

    # --- PDF ---
    PDF_MARGIN_CROP_PERCENT: int = int(os.environ.get("PDF_MARGIN_CROP_PERCENT", "8"))

    @classmethod
    def log_summary(cls) -> None:
        """Log a summary of non-secret configuration values."""
        logger.info("Configuration loaded:")
        logger.info("  SPACY_MODEL=%s", cls.SPACY_MODEL)
        logger.info("  LLM_ENABLED=%s", cls.LLM_ENABLED)
        logger.info("  MODEL_PROVIDER=%s", cls.MODEL_PROVIDER)
        logger.info("  MODEL_TEMPERATURE=%.2f", cls.MODEL_TEMPERATURE)
        logger.info("  MODEL_ANALYSIS_TEMPERATURE=%.2f", cls.MODEL_ANALYSIS_TEMPERATURE)
        logger.info("  MODEL_SUGGESTION_TEMPERATURE=%.2f", cls.MODEL_SUGGESTION_TEMPERATURE)
        logger.info("  MODEL_SEED=%s", cls.MODEL_SEED)
        logger.info("  MODEL_MAX_TOKENS=%d", cls.MODEL_MAX_TOKENS)
        logger.info("  LLM_MAX_CONCURRENT=%d", cls.LLM_MAX_CONCURRENT)
        logger.info("  CONFIDENCE_THRESHOLD=%.2f", cls.CONFIDENCE_THRESHOLD)
        logger.info("  LLM_CONFIDENCE_THRESHOLD=%.2f", cls.LLM_CONFIDENCE_THRESHOLD)
        logger.info("  LLM_JUDGE_ENABLED=%s", cls.LLM_JUDGE_ENABLED)
        logger.info("  BLOCK_CACHE_TTL=%d", cls.BLOCK_CACHE_TTL)
        logger.info("  FEEDBACK_PERSISTENT=%s", cls.FEEDBACK_PERSISTENT)
        logger.info("  SESSION_TTL_SECONDS=%d", cls.SESSION_TTL_SECONDS)
        logger.info("  CORS_ORIGINS=%s", cls.CORS_ORIGINS)
        logger.info("  RATE_LIMIT_ENABLED=%s", cls.RATE_LIMIT_ENABLED)

        if cls.CORS_ORIGINS == "*":
            logger.warning(
                "CORS_ORIGINS='*' -- restrict in production via CORS_ORIGINS env var"
            )

        if os.environ.get("SECRET_KEY") is None:
            logger.warning(
                "SECRET_KEY auto-generated -- set SECRET_KEY env var"
                " for session persistence across restarts"
            )

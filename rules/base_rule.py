"""
Base Rule Class -- Abstract interface for all writing rules.

All concrete rules must inherit from BaseRule (or a category-specific
subclass such as BaseLanguageRule, BaseWordUsageRule, etc.) and implement
the ``analyze`` and ``_get_rule_type`` abstract methods.

This module provides:
- Standardized error creation with automatic exception/technical-content filtering
- Protected product-name range detection
- IBM Style Guide citation enrichment via ``style_guides.ibm.ibm_style_mapping``
- SpaCy token serialization helpers
"""

import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Style guide mapping imports (optional dependency)
# ---------------------------------------------------------------------------
try:
    from style_guides.ibm.ibm_style_mapping import (
        IBM_STYLE_GUIDE_DEFAULT_CITATION,
        format_citation,
        get_confidence_adjustment as get_mapping_confidence_adjustment,
        get_rule_mapping,
        get_verification_status,
    )
    _IBM_STYLE_MAPPING_AVAILABLE = True
except ImportError:
    _IBM_STYLE_MAPPING_AVAILABLE = False
    IBM_STYLE_GUIDE_DEFAULT_CITATION = "IBM Style Guide"

    def get_rule_mapping(
        _rule_id: str, _category: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Fallback when style_guides package is unavailable."""
        return None

    def format_citation(
        _rule_id: str,
        _category: Optional[str] = None,
        _include_verification: bool = True,
    ) -> str:
        """Fallback when style_guides package is unavailable."""
        return IBM_STYLE_GUIDE_DEFAULT_CITATION

    def get_mapping_confidence_adjustment(
        _rule_id: str, _category: Optional[str] = None
    ) -> float:
        """Fallback when style_guides package is unavailable."""
        return 0.0

    def get_verification_status(
        _rule_id: str, _category: Optional[str] = None
    ) -> Dict[str, Any]:
        """Fallback when style_guides package is unavailable."""
        return {"status": "unknown", "verified": False}


# ---------------------------------------------------------------------------
# Shared inline-code guard helper
# ---------------------------------------------------------------------------


def in_code_range(content_pos: int, ranges: list) -> bool:
    """Return True if *content_pos* falls inside any inline-code range.

    Args:
        content_pos: Character position in block content coordinates.
        ranges: List of ``(start, end)`` tuples from
            ``context.get("inline_code_ranges", [])``.

    Returns:
        True if the position is inside an inline-code span.
    """
    return any(s <= content_pos < e for s, e in ranges)


# ---------------------------------------------------------------------------
# Pre-compiled technical content patterns
# ---------------------------------------------------------------------------
_URL_RE = re.compile(r"^(?:https?://|www\.)", re.IGNORECASE)
_EMAIL_RE = re.compile(
    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
)
_UNIX_PATH_RE = re.compile(r"^[/~][\w./\-]+$")
_WIN_PATH_RE = re.compile(r"^[A-Z]:\\")
_CAMEL_RE = re.compile(r"^[a-z]+[A-Z]")
_DOTTED_RE = re.compile(r"^[a-z]+(\.[a-z]+){2,}$")


class BaseRule(ABC):
    """Abstract base class for all writing rules.

    Provides exception checking, IBM Style citations, protected product-name
    detection, technical-content filtering, and standardized error creation.
    Subclasses must implement ``_get_rule_type`` and ``analyze``.
    """

    # Class-level cache -- loaded once, shared across all rule instances
    _exceptions: Optional[Dict[str, Any]] = None
    _protected_terms: Optional[List[str]] = None
    _protected_patterns: Optional[List["re.Pattern[str]"]] = None

    def __init__(self) -> None:
        """Initialize the rule, load exceptions and style-guide mapping."""
        self.rule_type: str = self._get_rule_type()
        self.severity_levels: List[str] = ["low", "medium", "high"]

        # Load exceptions once, cache at the class level
        if BaseRule._exceptions is None:
            self._load_exceptions()
            self._load_protected_terms()

        # IBM Style Guide citation fields
        self._ibm_style_mapping: Optional[Dict[str, Any]] = None
        self._ibm_style_citation: Optional[str] = None
        self._ibm_style_confidence_boost: float = 0.0
        if _IBM_STYLE_MAPPING_AVAILABLE:
            self._load_ibm_style_mapping()

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def _get_rule_type(self) -> str:
        """Return the rule type identifier (e.g. 'passive_voice')."""

    @abstractmethod
    def analyze(
        self,
        text: str,
        sentences: List[str],
        nlp: Any = None,
        context: Optional[Dict[str, Any]] = None,
        spacy_doc: Any = None,
    ) -> List[Dict[str, Any]]:
        """Analyze *text* and return a list of error dicts.

        Args:
            text: Full text to analyze.
            sentences: Pre-split list of sentences.
            nlp: SpaCy language model (optional).
            context: Block-level context dict (optional).
            spacy_doc: Pre-created SpaCy Doc object (optional).

        Returns:
            List of error dictionaries produced by ``_create_error``.
        """

    # ------------------------------------------------------------------
    # Exception loading
    # ------------------------------------------------------------------

    @classmethod
    def _load_exceptions(cls) -> None:
        """Load ``rules/config/exceptions.yaml`` and cache at class level."""
        config_dir = os.path.join(os.path.dirname(__file__), "config")
        path = os.path.join(config_dir, "exceptions.yaml")
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
                if not isinstance(data, dict):
                    logger.warning(
                        "exceptions.yaml at %s is not a valid dictionary; "
                        "disabling exceptions",
                        path,
                    )
                    cls._exceptions = {}
                else:
                    cls._exceptions = data
        except FileNotFoundError:
            logger.info(
                "exceptions.yaml not found at %s; no exceptions will be applied",
                path,
            )
            cls._exceptions = {}
        except yaml.YAMLError as exc:
            logger.warning("Failed to parse exceptions.yaml: %s", exc)
            cls._exceptions = {}

    @classmethod
    def _load_protected_terms(cls) -> None:
        """Build pre-compiled regex patterns for protected product names."""
        terms: List[str] = []
        if cls._exceptions and isinstance(cls._exceptions, dict):
            raw = cls._exceptions.get("protected_product_names", [])
            terms = [str(t) for t in raw if t]

        cls._protected_terms = terms
        cls._protected_patterns = []
        for term in cls._protected_terms:
            try:
                pattern = re.compile(
                    r"\b" + re.escape(term) + r"\b", re.IGNORECASE
                )
                cls._protected_patterns.append(pattern)
            except re.error:
                logger.warning(
                    "Invalid regex for protected term '%s'; skipping", term
                )

    # ------------------------------------------------------------------
    # Exception / technical-content filtering
    # ------------------------------------------------------------------

    def _is_excepted(self, text_span: str) -> bool:
        """Return ``True`` if *text_span* matches a global or rule-specific exception."""
        if not self._exceptions or not text_span:
            return False

        normalized = text_span.lower().strip()

        global_exc = self._exceptions.get("global_exceptions", [])
        if isinstance(global_exc, list):
            if normalized in {str(e).lower() for e in global_exc}:
                return True

        rule_specifics = self._exceptions.get("rule_specific_exceptions", {})
        if isinstance(rule_specifics, dict):
            rule_exc = rule_specifics.get(self.rule_type, [])
            if isinstance(rule_exc, list):
                if normalized in {str(e).lower() for e in rule_exc}:
                    return True

        return False

    def _is_technical_content(self, text_span: str) -> bool:
        """Return ``True`` if *text_span* is a URL, email, path, or code identifier."""
        if not text_span:
            return False

        stripped = text_span.strip()

        # URLs
        if _URL_RE.match(stripped):
            return True
        # Emails
        if _EMAIL_RE.match(stripped):
            return True
        # File paths (Unix or Windows)
        if _UNIX_PATH_RE.match(stripped) or _WIN_PATH_RE.match(stripped):
            return True
        # Inline code backticks
        if stripped.startswith("`") and stripped.endswith("`"):
            return True
        # Identifiers: camelCase, snake_case, dotted package names
        if " " not in stripped and (
            _CAMEL_RE.match(stripped)
            or "_" in stripped
            or _DOTTED_RE.match(stripped)
        ):
            return True

        return False

    # ------------------------------------------------------------------
    # Protected product-name ranges
    # ------------------------------------------------------------------

    def _get_protected_ranges(self, text: str) -> List[tuple]:
        """Return character ranges in *text* covered by protected product names."""
        ranges: List[tuple] = []
        if not self._protected_patterns:
            return ranges
        for pattern in self._protected_patterns:
            for match in pattern.finditer(text):
                ranges.append((match.start(), match.end()))
        return ranges

    @staticmethod
    def _is_in_protected_range(
        start: int, end: int, protected_ranges: List[tuple]
    ) -> bool:
        """Return ``True`` if the span [start, end) falls within a protected range."""
        for pstart, pend in protected_ranges:
            if start >= pstart and end <= pend:
                return True
        return False

    # ------------------------------------------------------------------
    # IBM Style Guide mapping
    # ------------------------------------------------------------------

    def _load_ibm_style_mapping(self) -> None:
        """Load IBM Style Guide citation and confidence boost for this rule."""
        try:
            category = self._get_rule_category_for_mapping()
            self._ibm_style_mapping = get_rule_mapping(
                self.rule_type, category
            )

            if self._ibm_style_mapping:
                self._ibm_style_citation = format_citation(
                    self.rule_type, category, include_verification=True
                )
                self._ibm_style_confidence_boost = (
                    get_mapping_confidence_adjustment(
                        self.rule_type, category
                    )
                )
                verification = get_verification_status(
                    self.rule_type, category
                )
                if verification.get("verified"):
                    logger.debug(
                        "IBM Style mapping loaded for '%s': %s",
                        self.rule_type,
                        self._ibm_style_citation,
                    )
            else:
                self._ibm_style_citation = IBM_STYLE_GUIDE_DEFAULT_CITATION
                logger.debug(
                    "No IBM Style mapping found for rule '%s'",
                    self.rule_type,
                )
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning(
                "Error loading IBM Style mapping for '%s': %s",
                self.rule_type,
                exc,
            )
            self._ibm_style_citation = IBM_STYLE_GUIDE_DEFAULT_CITATION
            self._ibm_style_confidence_boost = 0.0

    def _get_rule_category_for_mapping(self) -> str:
        """Infer the style-guide category from class name or module path.

        Override in subclasses if the automatic inference is incorrect.
        """
        category_keywords: Dict[str, List[str]] = {
            "word_usage": [
                "word", "awords", "bwords", "cwords",
            ],
            "language_and_grammar": [
                "language", "grammar", "spelling", "article",
                "pronoun", "verb",
            ],
            "structure_and_format": [
                "structure", "format", "heading", "list",
                "procedure", "referential",
            ],
            "audience_and_medium": [
                "audience", "medium", "tone", "llm", "global",
            ],
            "legal_information": ["legal", "claim", "company"],
            "punctuation": [
                "punctuation", "comma", "semicolon", "colon",
                "dash", "period",
            ],
            "numbers_and_measurement": [
                "number", "currency", "date", "time", "measurement",
            ],
            "technical_elements": [
                "technical", "command", "keyboard", "mouse",
                "file", "directory",
            ],
            "references": [
                "reference", "citation", "geographic", "product",
            ],
        }

        class_name = self.__class__.__name__.lower()
        for category, keywords in category_keywords.items():
            if any(kw in class_name for kw in keywords):
                return category

        module = self.__class__.__module__
        for category in category_keywords:
            if category in module:
                return category

        return "language_and_grammar"

    # ------------------------------------------------------------------
    # Error creation
    # ------------------------------------------------------------------

    def _create_error(
        self,
        sentence: str,
        sentence_index: int,
        message: str,
        suggestions: List[str],
        severity: str = "medium",
        text: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        **extra_data: Any,
    ) -> Optional[Dict[str, Any]]:
        """Create a standardized error dict.

        Returns ``None`` when the flagged text is excepted or is technical
        content, providing universal false-positive protection for all rules.

        Args:
            sentence: The sentence containing the issue.
            sentence_index: Zero-based index of the sentence.
            message: Human-readable description of the issue.
            suggestions: List of suggested corrections.
            severity: One of 'low', 'medium', 'high'.
            text: Full document text (optional).
            context: Block-level context dict (optional).
            **extra_data: Arbitrary additional fields (e.g. ``flagged_text``,
                ``span``, ``confidence_score``).

        Returns:
            Error dict or ``None`` if the flagged text is excepted.
        """
        flagged_text = extra_data.get("flagged_text", "")
        if flagged_text:
            if self._is_excepted(flagged_text):
                return None
            if self._is_technical_content(flagged_text):
                return None

        if severity not in self.severity_levels:
            severity = "medium"

        final_message = str(message)
        if self._ibm_style_citation and not final_message.endswith(
            self._ibm_style_citation
        ):
            if "IBM Style" not in final_message and "Red Hat" not in final_message:
                final_message = f"{final_message} Per {self._ibm_style_citation}."

        error: Dict[str, Any] = {
            "type": self.rule_type,
            "message": final_message,
            "suggestions": [str(s) for s in suggestions],
            "sentence": str(sentence),
            "sentence_index": int(sentence_index),
            "severity": severity,
            "style_guide_citation": (
                self._ibm_style_citation or IBM_STYLE_GUIDE_DEFAULT_CITATION
            ),
        }

        for key, value in extra_data.items():
            error[str(key)] = self._make_serializable(value)

        return error

    # ------------------------------------------------------------------
    # Serialization helpers
    # ------------------------------------------------------------------

    def _make_serializable(self, data: Any) -> Any:
        """Recursively convert *data* to a JSON-serializable structure.

        Handles SpaCy tokens, dicts, lists, tuples, sets, and primitives.
        """
        if data is None:
            return None

        # SpaCy token detection
        if hasattr(data, "text") and hasattr(data, "lemma_"):
            return self._token_to_dict(data)

        # Mapping-like objects that are not plain dicts
        if (
            hasattr(data, "__iter__")
            and hasattr(data, "get")
            and not isinstance(data, (str, dict, list, tuple))
        ):
            return self._serialize_mapping(data)

        if isinstance(data, dict):
            return self._serialize_dict(data)

        if isinstance(data, (list, tuple, set, frozenset)):
            return [self._make_serializable(item) for item in data]

        if isinstance(data, (str, int, float, bool)):
            return data

        return str(data)

    def _serialize_mapping(self, data: Any) -> Any:
        """Attempt to convert a mapping-like object to a dict."""
        try:
            return dict(data)
        except (TypeError, ValueError):
            return str(data)

    def _serialize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize all values in a dict."""
        result: Dict[str, Any] = {}
        for key, value in data.items():
            result[str(key)] = self._make_serializable(value)
        return result

    def _token_to_dict(self, token: Any) -> Optional[Dict[str, Any]]:
        """Convert a SpaCy token to a JSON-serializable dictionary."""
        if token is None:
            return None

        try:
            token_dict: Dict[str, Any] = {
                "text": token.text,
                "lemma": token.lemma_,
                "pos": token.pos_,
                "tag": token.tag_,
                "dep": token.dep_,
                "idx": token.idx,
                "i": token.i,
            }
            token_dict["morphology"] = self._extract_morphology(token)
            return token_dict
        except AttributeError:
            return self._token_fallback(token)

    @staticmethod
    def _extract_morphology(token: Any) -> Any:
        """Safely extract morphology data from a SpaCy token."""
        if hasattr(token, "morph") and token.morph:
            try:
                return dict(token.morph)
            except (TypeError, ValueError):
                return str(token.morph)
        return {}

    @staticmethod
    def _token_fallback(token: Any) -> Dict[str, Any]:
        """Build a best-effort dict when normal attribute access fails."""
        return {
            "text": str(token),
            "lemma": getattr(token, "lemma_", ""),
            "pos": getattr(token, "pos_", ""),
            "tag": getattr(token, "tag_", ""),
            "dep": getattr(token, "dep_", ""),
            "idx": getattr(token, "idx", 0),
            "i": getattr(token, "i", 0),
            "morphology": {},
        }

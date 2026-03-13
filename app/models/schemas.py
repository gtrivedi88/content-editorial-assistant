"""Data schemas for the Content Editorial Assistant.

Defines dataclass-based schemas for API request and response payloads.
Each schema provides to_dict() for JSON serialization, and selected
schemas provide from_dict() for deserialization from API responses.
"""

import logging
from dataclasses import dataclass, field
from typing import Optional

from app.models.enums import (
    ContentType,
    FileType,
    IssueCategory,
    IssueSeverity,
    IssueStatus,
)

logger = logging.getLogger(__name__)


@dataclass
class AnalyzeRequest:
    """Request payload for the content analysis endpoint.

    Attributes:
        text: The raw text content to analyze.
        content_type: Modular documentation type classification.
        file_type: Original file format, if uploaded as a file.
    """

    text: str
    content_type: ContentType = ContentType.CONCEPT
    file_type: Optional[FileType] = None

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-compatible dictionary.

        Returns:
            Dictionary with all fields, enums converted to their string values.
        """
        result: dict[str, object] = {
            "text": self.text,
            "content_type": self.content_type.value,
        }
        if self.file_type is not None:
            result["file_type"] = self.file_type.value
        else:
            result["file_type"] = None
        return result


@dataclass
class IssueResponse:
    """A single editorial issue found during content analysis.

    Represents one flagged problem in the analyzed text, including its
    location, category, severity, suggested fixes, and lifecycle status.

    Attributes:
        id: Unique identifier for this issue instance.
        source: Origin of the detection — "deterministic" or "llm".
        category: Editorial category this issue belongs to.
        rule_name: Identifier of the rule that triggered this issue.
        flagged_text: The exact text span that triggered the issue.
        message: Human-readable explanation of the problem.
        suggestions: List of suggested replacement texts.
        severity: How critical this issue is.
        sentence: The full sentence containing the flagged text.
        sentence_index: Zero-based index of the sentence in the document.
        span: Two-element list [start, end] character offsets in the document.
        style_guide_citation: Reference to the applicable style guide section.
        confidence: Detection confidence score between 0.0 and 1.0.
        status: Current lifecycle status of this issue.
    """

    id: str
    source: str
    category: IssueCategory
    rule_name: str
    flagged_text: str
    message: str
    suggestions: list[str]
    severity: IssueSeverity
    sentence: str
    sentence_index: int
    span: list[int]
    style_guide_citation: str = ""
    confidence: float = 1.0
    status: IssueStatus = IssueStatus.OPEN

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-compatible dictionary.

        Returns:
            Dictionary with all fields, enums converted to their string values.
        """
        return {
            "id": self.id,
            "source": self.source,
            "category": self.category.value if isinstance(self.category, IssueCategory) else str(self.category),
            "rule_name": self.rule_name,
            "flagged_text": self.flagged_text,
            "message": self.message,
            "suggestions": list(self.suggestions),
            "severity": self.severity.value if isinstance(self.severity, IssueSeverity) else str(self.severity),
            "sentence": self.sentence,
            "sentence_index": self.sentence_index,
            "span": list(self.span),
            "style_guide_citation": self.style_guide_citation,
            "confidence": self.confidence,
            "status": self.status.value if isinstance(self.status, IssueStatus) else str(self.status),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "IssueResponse":
        """Reconstruct an IssueResponse from a dictionary.

        Converts string values back to their enum counterparts. Handles
        both raw string values and pre-constructed enum instances.

        Args:
            data: Dictionary containing issue fields, typically from an API response.

        Returns:
            A fully populated IssueResponse instance.
        """
        category = data.get("category", "style")
        if isinstance(category, str):
            category = IssueCategory(category)

        severity = data.get("severity", "medium")
        if isinstance(severity, str):
            severity = IssueSeverity(severity)

        status = data.get("status", "open")
        if isinstance(status, str):
            status = IssueStatus(status)

        return cls(
            id=str(data.get("id", "")),
            source=str(data.get("source", "deterministic")),
            category=category,
            rule_name=str(data.get("rule_name", "")),
            flagged_text=str(data.get("flagged_text", "")),
            message=str(data.get("message", "")),
            suggestions=list(data.get("suggestions", [])),
            severity=severity,
            sentence=str(data.get("sentence", "")),
            sentence_index=int(data.get("sentence_index", 0)),
            span=list(data.get("span", [0, 0])),
            style_guide_citation=str(data.get("style_guide_citation", "")),
            confidence=float(data.get("confidence", 1.0)),
            status=status,
        )


@dataclass
class ScoreResponse:
    """Aggregate quality score for an analyzed document.

    Attributes:
        score: Overall quality score (0-100).
        color: UI color indicator based on score thresholds.
        label: Human-readable quality label (e.g. "Good", "Needs work").
        total_issues: Total number of issues found.
        category_counts: Number of issues per category.
        compliance: Per-guide compliance percentages (0.0-1.0).
    """

    score: int
    color: str
    label: str
    total_issues: int
    category_counts: dict[str, int] = field(default_factory=dict)
    compliance: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-compatible dictionary.

        Returns:
            Dictionary with all fields in JSON-serializable form.
        """
        return {
            "score": self.score,
            "color": self.color,
            "label": self.label,
            "total_issues": self.total_issues,
            "category_counts": dict(self.category_counts),
            "compliance": dict(self.compliance),
        }


@dataclass
class ReadabilityMetric:
    """A single readability measurement for the analyzed content.

    Attributes:
        name: Name of the readability metric (e.g. "Flesch-Kincaid").
        score: Computed readability score value.
        help_text: Explanation of what the score means and target ranges.
    """

    name: str
    score: float
    help_text: str

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-compatible dictionary.

        Returns:
            Dictionary with name, score, and help_text fields.
        """
        return {
            "name": self.name,
            "score": self.score,
            "help_text": self.help_text,
        }


@dataclass
class ReportResponse:
    """Statistical report for an analyzed document.

    Contains word counts, sentence metrics, readability scores,
    issue category breakdowns, per-guide compliance percentages,
    and LLM consumability analysis.

    Attributes:
        word_count: Total number of words in the document.
        sentence_count: Total number of sentences detected.
        paragraph_count: Total number of paragraphs detected.
        avg_words_per_sentence: Mean words per sentence.
        avg_syllables_per_word: Mean syllables per word.
        readability: Readability metrics keyed by metric name,
            each containing score and help_text.
        category_breakdown: Issue counts keyed by category name.
        compliance: Per-guide compliance percentages (0.0-1.0).
        unique_words: Count of distinct words (case-insensitive).
        vocabulary_diversity: Type-token ratio (0.0-1.0).
        estimated_reading_time: Human-readable reading time string.
        llm_consumability: LLM consumability score and breakdown.
    """

    word_count: int
    sentence_count: int
    paragraph_count: int
    avg_words_per_sentence: float
    avg_syllables_per_word: float
    readability: dict[str, dict[str, object]] = field(default_factory=dict)
    category_breakdown: dict[str, int] = field(default_factory=dict)
    compliance: dict[str, float] = field(default_factory=dict)
    unique_words: int = 0
    vocabulary_diversity: float = 0.0
    estimated_reading_time: str = ""
    llm_consumability: dict = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-compatible dictionary.

        Returns:
            Dictionary with all report fields in JSON-serializable form.
        """
        return {
            "word_count": self.word_count,
            "sentence_count": self.sentence_count,
            "paragraph_count": self.paragraph_count,
            "avg_words_per_sentence": self.avg_words_per_sentence,
            "avg_syllables_per_word": self.avg_syllables_per_word,
            "readability": {
                name: dict(metrics) for name, metrics in self.readability.items()
            },
            "category_breakdown": dict(self.category_breakdown),
            "compliance": dict(self.compliance),
            "statistics": {
                "word_count": self.word_count,
                "sentence_count": self.sentence_count,
                "paragraph_count": self.paragraph_count,
                "avg_sentence_length": self.avg_words_per_sentence,
                "unique_words": self.unique_words,
                "vocabulary_diversity": self.vocabulary_diversity,
                "avg_syllables_per_word": self.avg_syllables_per_word,
                "estimated_reading_time": self.estimated_reading_time,
            },
            "llm_consumability": dict(self.llm_consumability),
        }


@dataclass
class AnalyzeResponse:
    """Complete response from the content analysis endpoint.

    Bundles all issues found, the aggregate quality score, and the
    statistical report into a single response payload.

    Attributes:
        session_id: Unique identifier for this analysis session.
        partial: True when only deterministic results are included
            and LLM analysis is still pending via Socket.IO.
        issues: List of all editorial issues found.
        score: Aggregate quality score and breakdown.
        report: Statistical and readability report.
        detected_content_type: Auto-detected modular documentation type.
    """

    session_id: str
    issues: list[IssueResponse]
    score: ScoreResponse
    report: ReportResponse
    partial: bool = False
    detected_content_type: str = "concept"

    def to_dict(self) -> dict[str, object]:
        """Serialize to a JSON-compatible dictionary.

        Recursively serializes nested IssueResponse, ScoreResponse,
        and ReportResponse instances via their own to_dict() methods.

        Returns:
            Dictionary with all fields in JSON-serializable form.
        """
        return {
            "success": True,
            "session_id": self.session_id,
            "partial": self.partial,
            "issues": [issue.to_dict() for issue in self.issues],
            "score": self.score.to_dict(),
            "report": self.report.to_dict(),
            "detected_content_type": self.detected_content_type,
        }

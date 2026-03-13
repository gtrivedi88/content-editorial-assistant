"""LLM Consumability Score for analyzed documents.

Measures how well an LLM can parse and use the document across three
dimensions: Structural Clarity (40%), Content Clarity (30%), and
Format Compliance (30%).  Each dimension scores 0-100 and the final
score is a weighted aggregate.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Safe math helpers — guard against degenerate inputs (Trap 1)
# ---------------------------------------------------------------------------


def _safe_divide(
    numerator: float,
    denominator: float,
    default: float = 0.0,
) -> float:
    """Divide safely, returning *default* when denominator is zero."""
    return numerator / denominator if denominator > 0 else default


def _safe_std_dev(values: list[float]) -> float:
    """Sample standard deviation, safe for 0- or 1-element lists."""
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return variance ** 0.5


# ---------------------------------------------------------------------------
# Dimension 1 — Structural Clarity (40 %)
# ---------------------------------------------------------------------------

_HEADING_TYPES = frozenset({"heading", "heading_1", "heading_2", "heading_3",
                            "heading_4", "heading_5", "heading_6"})
_LIST_TYPES = frozenset({"list_item_ordered", "list_item_unordered",
                         "definition_list"})


def _score_structural_clarity(blocks: list[Any]) -> dict[str, Any]:
    """Evaluate heading hierarchy, section balance, lists, and paragraphs."""
    details: list[str] = []

    # --- Heading hierarchy ---
    heading_levels: list[int] = []
    for b in blocks:
        if b.block_type in _HEADING_TYPES or b.block_type == "heading":
            heading_levels.append(getattr(b, "level", 1))

    hierarchy_score = 100
    if not heading_levels:
        hierarchy_score = 40
        details.append("No headings detected — add structure for LLM parsing")
    else:
        # Check for sequential hierarchy (no skipped levels)
        skips = 0
        for i in range(1, len(heading_levels)):
            diff = heading_levels[i] - heading_levels[i - 1]
            if diff > 1:
                skips += 1
        if skips:
            penalty = min(40, skips * 15)
            hierarchy_score = max(20, 100 - penalty)
            details.append(f"{skips} heading level skip(s) detected")
        else:
            details.append("Clean heading hierarchy")

    # --- Section length balance ---
    section_lengths: list[float] = []
    current_length = 0
    for b in blocks:
        if b.block_type in _HEADING_TYPES or b.block_type == "heading":
            if current_length > 0:
                section_lengths.append(float(current_length))
            current_length = 0
        else:
            current_length += len(b.content)
    if current_length > 0:
        section_lengths.append(float(current_length))

    if len(section_lengths) >= 2:
        std = _safe_std_dev(section_lengths)
        mean = _safe_divide(sum(section_lengths), len(section_lengths))
        cv = _safe_divide(std, mean) if mean > 0 else 0
        if cv < 0.5:
            balance_score = 100
        elif cv < 1.0:
            balance_score = 70
        else:
            balance_score = max(30, 100 - int(cv * 30))
        details.append(f"Section length CV: {cv:.2f}")
    else:
        balance_score = 60
        details.append("Single section — consider splitting for clarity")

    # --- List presence ---
    list_count = sum(1 for b in blocks if b.block_type in _LIST_TYPES)
    total_blocks = max(1, len(blocks))
    list_ratio = _safe_divide(list_count, total_blocks)
    if list_ratio >= 0.1:
        list_score = 100
        details.append("Good use of lists for structured content")
    elif list_ratio > 0:
        list_score = 70
    else:
        list_score = 50
        details.append("No lists — consider adding for scannable content")

    # --- Paragraph length ---
    para_lengths = [
        len(b.content.split())
        for b in blocks
        if b.block_type == "paragraph" and b.content.strip()
    ]
    if para_lengths:
        avg_para = _safe_divide(sum(para_lengths), len(para_lengths))
        if 30 <= avg_para <= 100:
            para_score = 100
        elif 15 <= avg_para < 30 or 100 < avg_para <= 150:
            para_score = 75
        else:
            para_score = 50
    else:
        para_score = 70

    score = int(
        hierarchy_score * 0.35
        + balance_score * 0.25
        + list_score * 0.20
        + para_score * 0.20
    )
    return {"score": min(100, max(0, score)), "details": details}


# ---------------------------------------------------------------------------
# Dimension 2 — Content Clarity (30 %)
# ---------------------------------------------------------------------------

_PRONOUN_RE = re.compile(
    r"\b(he|she|it|they|this|that|these|those|its|their|his|her)\b",
    re.IGNORECASE,
)


def _score_content_clarity(
    prep: dict[str, Any],
    readability: dict[str, dict[str, object]],
) -> dict[str, Any]:
    """Evaluate sentence length, vocabulary, readability, and ambiguity."""
    details: list[str] = []

    # --- Avg sentence length ---
    avg_sent = prep.get("avg_words_per_sentence", 0)
    if 15 <= avg_sent <= 20:
        sent_score = 100
        details.append("Ideal sentence length for LLM comprehension")
    elif 10 <= avg_sent < 15 or 20 < avg_sent <= 25:
        sent_score = 75
    elif avg_sent > 30:
        sent_score = 30
        details.append("Very long sentences reduce LLM parsing accuracy")
    else:
        sent_score = 60

    # --- Vocabulary consistency (type-token ratio) ---
    ttr = prep.get("vocabulary_diversity", 0.0)
    if 0.4 <= ttr <= 0.7:
        vocab_score = 100
        details.append("Good vocabulary consistency for LLM context")
    elif ttr > 0.7:
        vocab_score = 70
        details.append("High vocabulary diversity — may scatter LLM focus")
    else:
        vocab_score = 60

    # --- Flesch Reading Ease ---
    flesch_data = readability.get("Flesch Reading Ease", {})
    flesch = float(flesch_data.get("score", 0))
    if flesch >= 60:
        flesch_score = 100
    elif flesch >= 40:
        flesch_score = 70
    else:
        flesch_score = max(30, int(flesch))

    # --- Pronoun density (ambiguity approximation) ---
    text = prep.get("text", "")
    word_count = prep.get("word_count", 0)
    pronoun_matches = len(_PRONOUN_RE.findall(text))
    pronoun_density = _safe_divide(pronoun_matches, word_count)
    if pronoun_density < 0.05:
        pronoun_score = 100
    elif pronoun_density < 0.10:
        pronoun_score = 75
    else:
        pronoun_score = max(30, 100 - int(pronoun_density * 500))
        details.append("High pronoun density — may cause ambiguity for LLMs")

    score = int(
        sent_score * 0.30
        + vocab_score * 0.25
        + flesch_score * 0.25
        + pronoun_score * 0.20
    )
    return {"score": min(100, max(0, score)), "details": details}


# ---------------------------------------------------------------------------
# Dimension 3 — Format Compliance (30 %)
# ---------------------------------------------------------------------------

_STRUCTURED_FORMATS = frozenset({
    "asciidoc", "markdown", "html", "dita", "xml", "docbook",
})


def _score_format_compliance(
    blocks: list[Any],
    file_type: str | None,
) -> dict[str, Any]:
    """Evaluate code markup, format type, metadata, and cross-references."""
    details: list[str] = []

    # --- Code blocks properly marked up ---
    code_blocks = [b for b in blocks if getattr(b, "should_skip_analysis", False)]
    if code_blocks:
        code_score = 100
        details.append(f"{len(code_blocks)} code block(s) properly delimited")
    else:
        code_score = 70

    # --- Structured format detection ---
    detected_format = (file_type or "").lower()
    if detected_format in _STRUCTURED_FORMATS:
        format_score = 100
        details.append(f"Structured format detected: {detected_format}")
    elif detected_format:
        format_score = 60
    else:
        format_score = 50
        details.append("Plain text — structured formats improve LLM parsing")

    # --- Metadata / attributes ---
    has_metadata = False
    for b in blocks:
        meta = getattr(b, "metadata", None)
        if meta and isinstance(meta, dict) and meta:
            has_metadata = True
            break
    metadata_score = 100 if has_metadata else 60

    # --- Cross-reference patterns ---
    xref_pattern = re.compile(r"(xref:|<<|href=|\[link\]|link:)", re.IGNORECASE)
    has_xrefs = any(
        xref_pattern.search(getattr(b, "raw_content", ""))
        for b in blocks
    )
    xref_score = 100 if has_xrefs else 60

    score = int(
        code_score * 0.30
        + format_score * 0.30
        + metadata_score * 0.20
        + xref_score * 0.20
    )
    return {"score": min(100, max(0, score)), "details": details}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_LABELS = [
    (90, "Excellent", "#1A8F57"),
    (75, "Good", "#2E9E59"),
    (60, "Fair", "#F2BA4D"),
    (0, "Needs Improvement", "#E3735E"),
]


def calculate_llm_consumability(
    blocks: list[Any],
    prep: dict[str, Any],
    file_type: str | None,
    readability: dict[str, dict[str, object]],
) -> dict[str, Any]:
    """Calculate LLM consumability score with dimensional breakdown.

    Args:
        blocks: Parsed document blocks.
        prep: Preprocessed text data dictionary.
        file_type: Detected file format string (e.g. ``"asciidoc"``).
        readability: Readability metrics dict from ``calculate_readability``.

    Returns:
        Dictionary with ``score`` (0-100), ``label``, ``color``,
        ``dimensions`` (3 sub-scores with details), ``strengths``,
        and ``improvements``.
    """
    structural = _score_structural_clarity(blocks)
    content = _score_content_clarity(prep, readability)
    fmt = _score_format_compliance(blocks, file_type)

    total = int(
        structural["score"] * 0.40
        + content["score"] * 0.30
        + fmt["score"] * 0.30
    )
    total = min(100, max(0, total))

    label = "Needs Improvement"
    color = "#E3735E"
    for threshold, lbl, clr in _LABELS:
        if total >= threshold:
            label = lbl
            color = clr
            break

    # Collect strengths and improvements from details
    strengths: list[str] = []
    improvements: list[str] = []
    for dim_result in (structural, content, fmt):
        for detail in dim_result.get("details", []):
            lower = detail.lower()
            if any(w in lower for w in ("good", "clean", "ideal", "properly")):
                strengths.append(detail)
            elif any(w in lower for w in ("no ", "consider", "high", "very",
                                          "reduce", "may", "plain")):
                improvements.append(detail)

    return {
        "score": total,
        "label": label,
        "color": color,
        "dimensions": {
            "structural_clarity": {
                "score": structural["score"],
                "details": structural["details"],
            },
            "content_clarity": {
                "score": content["score"],
                "details": content["details"],
            },
            "format_compliance": {
                "score": fmt["score"],
                "details": fmt["details"],
            },
        },
        "strengths": strengths[:5],
        "improvements": improvements[:5],
    }

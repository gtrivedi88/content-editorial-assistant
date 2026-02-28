"""Readability metric calculations for analyzed content.

Computes six standard readability metrics using the textstat library.
Each metric returns a numeric score and explanatory help text suitable
for display in the statistical report panel.
"""

import logging
from typing import Any

import textstat

logger = logging.getLogger(__name__)

_MIN_WORDS_FOR_READABILITY = 3

_METRIC_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "Flesch Reading Ease",
        "func": textstat.flesch_reading_ease,
        "help_text": (
            "Measures how easy text is to read. 60-70 is ideal for "
            "technical documentation. Higher scores mean easier reading."
        ),
    },
    {
        "name": "Flesch-Kincaid Grade",
        "func": textstat.flesch_kincaid_grade,
        "help_text": (
            "US school grade level needed to understand the text. "
            "8-12 is ideal for technical documentation."
        ),
    },
    {
        "name": "SMOG Index",
        "func": textstat.smog_index,
        "help_text": (
            "Years of education needed to understand the text. "
            "Based on polysyllabic word density."
        ),
    },
    {
        "name": "Gunning Fog",
        "func": textstat.gunning_fog,
        "help_text": (
            "Readability weighted by complex words. "
            "12-14 is ideal for technical documentation."
        ),
    },
    {
        "name": "Coleman-Liau",
        "func": textstat.coleman_liau_index,
        "help_text": (
            "Based on character count per word and sentence length. "
            "10-14 is typical for technical writing."
        ),
    },
    {
        "name": "ARI",
        "func": textstat.automated_readability_index,
        "help_text": (
            "Automated Readability Index. Based on characters per word "
            "and words per sentence."
        ),
    },
]


def _is_text_too_short(text: str) -> bool:
    """Check whether text has fewer words than the readability threshold.

    Args:
        text: The text to evaluate.

    Returns:
        True if the text has fewer than the minimum required words.
    """
    words = text.split()
    return len(words) < _MIN_WORDS_FOR_READABILITY


def _compute_single_metric(definition: dict[str, Any], text: str) -> dict[str, object]:
    """Compute one readability metric safely.

    Catches computation errors from textstat for edge-case inputs and
    falls back to a zero score rather than propagating the failure.

    Args:
        definition: Metric definition dict with 'name', 'func', and 'help_text'.
        text: The document text to score.

    Returns:
        Dictionary with 'score' (float) and 'help_text' (str).
    """
    try:
        raw_score = definition["func"](text)
        score = round(float(raw_score), 2)
    except (ValueError, ZeroDivisionError):
        logger.warning(
            "Readability metric '%s' returned an error; defaulting to 0.0",
            definition["name"],
        )
        score = 0.0

    return {
        "score": score,
        "help_text": definition["help_text"],
    }


def calculate_readability(text: str) -> dict[str, dict[str, object]]:
    """Calculate all six readability metrics for the given text.

    Handles edge cases such as empty text, very short text (fewer than
    three words), and single-sentence documents by returning 0.0 scores
    when the text is too short for meaningful readability analysis.

    Args:
        text: The document text to analyze.

    Returns:
        Dictionary keyed by metric name, where each value is a dict
        containing 'score' (float) and 'help_text' (str).
    """
    stripped = text.strip() if text else ""

    if not stripped or _is_text_too_short(stripped):
        logger.info("Text too short for readability analysis; returning zero scores")
        return _build_zero_scores()

    results: dict[str, dict[str, object]] = {}
    for definition in _METRIC_DEFINITIONS:
        results[definition["name"]] = _compute_single_metric(definition, stripped)

    logger.debug("Calculated %d readability metrics", len(results))
    return results


def _build_zero_scores() -> dict[str, dict[str, object]]:
    """Build a result dict with zero scores for all metrics.

    Returns:
        Dictionary keyed by metric name, each with score 0.0 and
        the standard help text.
    """
    return {
        definition["name"]: {
            "score": 0.0,
            "help_text": definition["help_text"],
        }
        for definition in _METRIC_DEFINITIONS
    }

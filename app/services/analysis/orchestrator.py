"""Analysis pipeline orchestrator for the Content Editorial Assistant.

Coordinates the three-phase analysis pipeline: deterministic rules,
LLM granular (per-block), and LLM global (full-document). Streams
partial results via Socket.IO as each phase completes.

Phase 1 (deterministic) returns immediately with partial=True.
Phases 2 and 3 run in the background and emit WebSocket events
when complete. LLM failures are non-fatal.

The granular LLM pass splits text into paragraph blocks and processes
them concurrently (up to LLM_MAX_CONCURRENT workers) for performance.
"""

import hashlib
import logging
import re
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from difflib import SequenceMatcher
from typing import Any, Optional

from app.config import Config
from app.models.enums import IssueStatus
from app.models.schemas import (
    AnalyzeResponse,
    IssueResponse,
    ReportResponse,
    ScoreResponse,
)
from app.services.analysis.deterministic import analyze as run_deterministic
from app.services.analysis.merger import merge as merge_issues
from app.services.analysis.preprocessor import _block_to_markdown, preprocess
from app.services.analysis.scorer import calculate_score

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session store import — deferred to call time to avoid circular imports
# ---------------------------------------------------------------------------


def _get_session_store():
    """Import and return get_session_store at call time."""
    from app.services.session.store import get_session_store
    return get_session_store()

try:
    from app.llm.client import analyze_block, analyze_global, judge_issues
except ImportError:
    analyze_block = None  # type: ignore[assignment]
    analyze_global = None  # type: ignore[assignment]
    judge_issues = None  # type: ignore[assignment]

# Maximum number of issues per judge batch (SK-13).
_JUDGE_BATCH_SIZE = 20


def _select_style_guide_excerpts(
    det_issues: list[IssueResponse],
    content_type: str,
) -> list[dict]:
    """Select style guide excerpts based on deterministic analysis results.

    Wraps the excerpt selector with error handling so excerpt failures
    never block analysis.

    Args:
        det_issues: Deterministic issues from Phase 1.
        content_type: Modular documentation type.

    Returns:
        List of excerpt dicts, empty on failure.
    """
    try:
        from app.llm.excerpt_selector import select_excerpts
        excerpts = select_excerpts(det_issues, content_type)
        if excerpts:
            logger.info(
                "Selected %d style guide excerpts for LLM prompts", len(excerpts),
            )
        return excerpts
    except (ImportError, ValueError, KeyError) as exc:
        logger.warning("Excerpt selection failed: %s", exc)
        return []


def _resolve_detected_content_type(
    content_type: str,
    detected: Optional[str],
    user_selected: bool,
) -> str:
    """Choose the final content type from auto-detection vs user selection.

    When the user explicitly selected a type (via popup or badge override),
    their choice is preserved.  Otherwise, auto-detected type overrides
    the default.

    Args:
        content_type: The content type from the request (default or user-chosen).
        detected: Auto-detected content type from preprocessing, or None.
        user_selected: Whether the user explicitly chose the content type.

    Returns:
        The resolved content type string.
    """
    if detected and not user_selected:
        logger.info(
            "Auto-detected content_type=%s (overriding default=%s)",
            detected, content_type,
        )
        return detected
    if user_selected:
        logger.info(
            "Using user-selected content_type=%s (auto-detected=%s)",
            content_type, detected,
        )
    return content_type


def analyze(
    text: str,
    content_type: str,
    file_type: Optional[str] = None,
    socket_sid: Optional[str] = None,
    session_id: Optional[str] = None,
    blocks: Optional[list] = None,
    user_selected: bool = False,
) -> AnalyzeResponse:
    """Run the full three-phase analysis pipeline.

    Phase 1 (deterministic) executes synchronously and returns
    immediately. Phases 2 and 3 (LLM) run in the background and
    emit Socket.IO events on completion.

    Args:
        text: Raw text content to analyze.
        content_type: Modular documentation type (concept, procedure, etc.).
        file_type: Original file format, if uploaded.
        socket_sid: Socket.IO session ID for progress emission.
        session_id: Optional client-provided session ID for session continuity.
            When provided, reuses the same session ID so the frontend's
            suggestion requests match the stored session. When None, a new
            UUID is generated.
        blocks: Optional list of Block objects from a parser. Enables
            lite_markers Markdown representation for LLM analysis and
            semantic block-boundary splitting.
        user_selected: Whether the user explicitly selected the content type
            via the popup or badge override.  When True, the auto-detected
            type does not override the user's choice.

    Returns:
        AnalyzeResponse with deterministic results and partial=True
        when LLM analysis will follow asynchronously.
    """
    if not session_id:
        session_id = str(uuid.uuid4())
    logger.info(
        "Starting analysis session=%s, content_type=%s, file_type=%s",
        session_id, content_type, file_type,
    )

    # Phase 0: Preprocessing
    _emit_progress(socket_sid, session_id, "preprocessing", "Preprocessing text", 5)
    prep = preprocess(text, blocks=blocks, file_type=file_type)

    # Resolve final content_type: auto-detected overrides default,
    # but user's explicit selection takes priority.
    detected = prep.get("detected_content_type")
    content_type = _resolve_detected_content_type(
        content_type, detected, user_selected,
    )

    # Phase 0.5: Collect acronym definitions for LLM context
    acronym_context = _collect_acronyms(prep["text"])
    if acronym_context:
        logger.info("Collected %d acronym definitions", len(acronym_context))

    # Phase 1: Deterministic analysis
    _emit_progress(socket_sid, session_id, "deterministic", "Running style checks", 20)
    logger.debug(
        "LLM_ENABLED=%s analyze_block_imported=%s file_type=%s",
        Config.LLM_ENABLED, analyze_block is not None, file_type,
    )
    logger.debug(
        "cleaned_text_len=%d blocks=%d lite_markers_len=%d",
        len(prep["text"]), len(prep.get("blocks", [])),
        len(prep.get("lite_markers", "")),
    )
    logger.debug("cleaned_text[:300]=%.300r", prep["text"][:300])
    block_det, full_det = _run_deterministic_with_blocks(
        prep, content_type, acronym_context,
    )

    # Block issues are already in original-text coordinates.
    # Full-text issues need remap from cleaned-text to original-text.
    for i, iss in enumerate(full_det):
        logger.debug(
            "full_det[%d] BEFORE remap: rule=%s span=%s "
            "flagged_text=%r",
            i, iss.rule_name, iss.span, iss.flagged_text[:80] if iss.flagged_text else "",
        )

    _remap_issues_to_original(
        full_det, prep.get("offset_map", []), prep.get("original_text", ""),
    )

    # Drop full-text issues whose remap failed
    pre_count = len(full_det)
    full_det = [iss for iss in full_det if iss.span != [-1, -1]]
    if len(full_det) < pre_count:
        logger.info(
            "Dropped %d full-text issues with failed remap",
            pre_count - len(full_det),
        )

    # Merge block issues (already remapped) with full-text issues (just remapped)
    det_issues = _merge_block_and_full_issues(block_det, full_det)
    logger.debug(
        "block_det=%d full_det=%d merged=%d",
        len(block_det), len(full_det), len(det_issues),
    )

    # Phase 1b: Structural analysis (inter-block rules)
    parsed_blocks = prep.get("blocks", blocks or [])
    structural_issues = _run_structural_analysis(
        parsed_blocks, content_type, prep.get("original_text", text),
    )
    det_issues.extend(structural_issues)  # Already in original coords

    for i, iss in enumerate(det_issues):
        logger.debug(
            "det issue[%d] FINAL: rule=%s span=%s "
            "flagged_text=%r",
            i, iss.rule_name, iss.span, iss.flagged_text[:80] if iss.flagged_text else "",
        )

    # Calculate preliminary score and report
    score = calculate_score(det_issues, prep["word_count"])
    report = _build_report(prep, score)

    _emit_progress(socket_sid, session_id, "deterministic_complete", "Style checks complete", 50)
    _emit_event(socket_sid, "deterministic_complete", {
        "session_id": session_id,
        "issues": [i.to_dict() for i in det_issues],
        "score": score.to_dict(),
        "report": report.to_dict(),
        "detected_content_type": content_type,
    })
    _emit_event(socket_sid, "stage_progress", {
        "session_id": session_id,
        "phase": "deterministic",
        "status": "done",
    })

    # Determine whether LLM phases should run
    llm_enabled = Config.LLM_ENABLED and analyze_block is not None
    partial = llm_enabled

    response = AnalyzeResponse(
        session_id=session_id,
        issues=det_issues,
        score=score,
        report=report,
        partial=partial,
        detected_content_type=content_type,
    )

    # Store session so suggestion requests can find it
    logger.debug("Storing session_id=%s with %d issues", session_id, len(response.issues))
    _store_session(session_id, response)

    logger.debug(
        "llm_enabled=%s partial=%s det_issues=%d",
        llm_enabled, partial, len(det_issues),
    )
    if llm_enabled:
        logger.debug("Scheduling LLM phases in background")
        _schedule_llm_phases(
            session_id, socket_sid, prep, det_issues, content_type, acronym_context,
        )
    else:
        logger.debug("LLM DISABLED, skipping phases 2+3")
        _emit_progress(socket_sid, session_id, "analysis_complete", "Analysis complete", 100)
        _emit_event(socket_sid, "analysis_complete", {
            "session_id": session_id,
            "issues": [i.to_dict() for i in det_issues],
            "score": score.to_dict(),
            "report": report.to_dict(),
            "detected_content_type": content_type,
        })

    return response


# ---------------------------------------------------------------------------
# LLM phase scheduling
# ---------------------------------------------------------------------------


def _schedule_llm_phases(
    session_id: str,
    socket_sid: Optional[str],
    prep: dict[str, Any],
    det_issues: list[IssueResponse],
    content_type: str,
    acronym_context: dict[str, str] | None = None,
) -> None:
    """Schedule LLM granular and global passes in the background.

    Uses the Socket.IO server's start_background_task to avoid
    blocking the HTTP response. Falls back to synchronous execution
    if Socket.IO background tasks are unavailable.

    Args:
        session_id: Unique analysis session identifier.
        socket_sid: Socket.IO session ID for progress emission.
        prep: Preprocessed text data from preprocess().
        det_issues: Deterministic issues from Phase 1.
        content_type: Modular documentation type.
        acronym_context: Known acronym definitions from the document.
    """
    try:
        from app.extensions import socketio as sio
        logger.debug("Starting background LLM task via socketio")
        sio.start_background_task(
            _run_llm_phases,
            session_id, socket_sid, prep, det_issues, content_type,
            acronym_context,
        )
    except (ImportError, AttributeError, RuntimeError) as exc:
        logger.warning("Cannot start background LLM task: %s", exc)
        _emit_event(socket_sid, "llm_skipped", {
            "session_id": session_id,
            "reason": str(exc),
        })


def _run_llm_phases(
    session_id: str,
    socket_sid: Optional[str],
    prep: dict[str, Any],
    det_issues: list[IssueResponse],
    content_type: str,
    acronym_context: dict[str, str] | None = None,
) -> None:
    """Execute LLM granular and global passes sequentially.

    Checks for session cancellation between phases. Emits progress
    and completion events via Socket.IO.

    Args:
        session_id: Unique analysis session identifier.
        socket_sid: Socket.IO session ID for progress emission.
        prep: Preprocessed text data.
        det_issues: Deterministic issues from Phase 1.
        content_type: Modular documentation type.
        acronym_context: Known acronym definitions from the document.
    """
    logger.debug("_run_llm_phases STARTED session=%s", session_id)
    llm_issues: list[IssueResponse] = []

    # Select style guide excerpts based on deterministic findings
    excerpts = _select_style_guide_excerpts(det_issues, content_type)
    logger.debug("Selected %d excerpts", len(excerpts))

    # Build document outline for LLM section-level awareness
    doc_outline = _build_document_outline(prep.get("blocks", []))

    # Fire LanguageTool in parallel with LLM granular
    lt_future = None
    if Config.LANGUAGETOOL_ENABLED and not _is_cancelled(session_id):
        logger.debug("Starting LanguageTool phase (parallel)")
        _emit_event(socket_sid, "stage_progress", {
            "session_id": session_id,
            "phase": "languagetool",
            "status": "started",
        })
        lt_executor = ThreadPoolExecutor(max_workers=1)
        lt_future = lt_executor.submit(
            _run_languagetool_phase, prep,
        )

    # Phase 2: LLM granular (per-block)
    blocks_total = len(prep.get("blocks", []))
    if not _is_cancelled(session_id):
        logger.debug("Starting granular phase")
        _emit_event(socket_sid, "stage_progress", {
            "session_id": session_id,
            "phase": "llm_granular",
            "status": "started",
            "blocks_total": blocks_total,
        })
        llm_issues = _run_llm_granular(
            session_id, socket_sid, prep, content_type, acronym_context,
            style_guide_excerpts=excerpts,
            document_outline=doc_outline,
        )
        logger.debug("Granular produced %d issues", len(llm_issues))
        _emit_event(socket_sid, "stage_progress", {
            "session_id": session_id,
            "phase": "llm_granular",
            "status": "done",
        })

    # Collect LanguageTool results (runs parallel, collect after granular)
    lt_issues: list[IssueResponse] = []
    if lt_future is not None and not _is_cancelled(session_id):
        try:
            lt_issues = lt_future.result(
                timeout=Config.LANGUAGETOOL_TIMEOUT + 2,
            )
            logger.info("LanguageTool produced %d issues", len(lt_issues))
        except TimeoutError:
            logger.warning("LanguageTool phase timed out")
        except Exception as exc:
            logger.warning("LanguageTool phase failed: %s", exc)
        _emit_event(socket_sid, "stage_progress", {
            "session_id": session_id,
            "phase": "languagetool",
            "status": "done",
        })

    # Phase 3: LLM global (full-document)
    if not _is_cancelled(session_id):
        logger.debug("Starting global phase")
        _emit_event(socket_sid, "stage_progress", {
            "session_id": session_id,
            "phase": "llm_global",
            "status": "started",
        })
        abstract_text = _extract_abstract(prep.get("blocks", []))
        global_issues = _run_llm_global(
            session_id, socket_sid, prep, content_type,
            style_guide_excerpts=excerpts,
            document_outline=doc_outline,
            abstract_context=abstract_text,
        )
        logger.debug("Global produced %d issues", len(global_issues))
        llm_issues.extend(global_issues)
        _emit_event(socket_sid, "stage_progress", {
            "session_id": session_id,
            "phase": "llm_global",
            "status": "done",
        })

    # Phase 2C: LLM judge self-correction (optional)
    if not _is_cancelled(session_id) and llm_issues and Config.LLM_JUDGE_ENABLED:
        document_excerpt = prep.get("lite_markers") or prep.get("text", "")
        llm_issues = _run_judge_pass(llm_issues, document_excerpt, content_type)

    # Merge and emit final results
    logger.debug(
        "Total LLM issues=%d, LT issues=%d, merging with det=%d",
        len(llm_issues), len(lt_issues), len(det_issues),
    )
    if not _is_cancelled(session_id):
        merged = merge_issues(
            det_issues, llm_issues, Config.CONFIDENCE_THRESHOLD,
            blocks=prep.get("blocks"),
            lt_issues=lt_issues,
        )
        score = calculate_score(merged, prep["word_count"])
        report = _build_report(prep, score)
        logger.debug("FINAL merged=%d issues, emitting analysis_complete", len(merged))

        # Log final merged results
        for i, iss in enumerate(merged):
            logger.debug(
                "FINAL merged[%d]: source=%s rule=%s span=%s "
                "flagged=%r",
                i, iss.source, iss.rule_name, iss.span,
                iss.flagged_text[:80] if iss.flagged_text else "",
            )

        # Update session store with final merged results
        updated_response = AnalyzeResponse(
            session_id=session_id,
            issues=merged,
            score=score,
            report=report,
            partial=False,
            detected_content_type=content_type,
        )
        logger.debug(
            "Updating stored session %s with %d merged issues",
            session_id, len(merged),
        )
        _update_stored_session(session_id, updated_response)

        _emit_progress(socket_sid, session_id, "analysis_complete", "Analysis complete", 100)
        _emit_event(socket_sid, "analysis_complete", {
            "session_id": session_id,
            "issues": [i.to_dict() for i in merged],
            "score": score.to_dict(),
            "report": report.to_dict(),
            "detected_content_type": content_type,
        })


def _run_languagetool_phase(prep: dict[str, Any]) -> list[IssueResponse]:
    """Run LanguageTool analysis on prose blocks.

    Called in a background thread, parallel with the LLM granular pass.
    Gracefully returns an empty list on any failure.

    Args:
        prep: Preprocessed text data containing blocks and original text.

    Returns:
        List of IssueResponse from LanguageTool, empty on failure.
    """
    try:
        from app.services.analysis.languagetool_client import check_blocks
        blocks = prep.get("blocks", [])
        if not blocks:
            return []
        original_text = prep.get("original_text", "")
        return check_blocks(blocks, original_text=original_text)
    except ImportError:
        logger.warning("languagetool_client not available")
        return []
    except Exception as exc:
        logger.warning("LanguageTool phase error: %s", exc)
        return []


def _run_deterministic_with_blocks(
    prep: dict[str, Any],
    content_type: str,
    acronym_context: dict[str, str] | None = None,
) -> tuple[list[IssueResponse], list[IssueResponse]]:
    """Run deterministic rules, iterating per-block when blocks are available.

    When parsed blocks are present, runs the deterministic analyzer once
    per block with the block's ``block_type`` so that rules scoped to
    headings, list items, or code blocks actually trigger.  Also runs a
    full-document pass for cross-block rules.

    Per-block issues are mapped directly to original-text coordinates
    (no remap needed).  Full-text issues remain in cleaned-text
    coordinates and need ``_remap_issues_to_original()`` by the caller.

    Falls back to single-pass behavior when blocks are not available.

    Args:
        prep: Preprocessed data from ``preprocess()``.
        content_type: Modular documentation type.

    Returns:
        Tuple of ``(block_issues, full_issues)`` where block_issues are
        already in original-text coordinates and full_issues need remap.
    """
    parsed_blocks = prep.get("blocks", [])
    cleaned_text = prep["text"]
    original_text = prep.get("original_text", "")

    if not parsed_blocks:
        logger.debug("No blocks, running full-text only")
        full_issues = run_deterministic(
            cleaned_text, prep["sentences"], prep["spacy_doc"],
            content_type=content_type,
            acronym_context=acronym_context,
        )
        return [], full_issues

    logger.debug("%d blocks, running per-block + full-text", len(parsed_blocks))
    block_issues = _analyze_blocks_deterministic(
        parsed_blocks, content_type, original_text, acronym_context,
    )
    # Filter failed block remaps
    block_issues = [i for i in block_issues if i.span != [-1, -1]]
    logger.debug("Per-block produced %d issues", len(block_issues))
    for i, iss in enumerate(block_issues[:10]):
        logger.debug(
            "block_iss[%d]: rule=%s flagged=%.60r span=%s",
            i, iss.rule_name, iss.flagged_text, iss.span,
        )
    full_issues = run_deterministic(
        cleaned_text, prep["sentences"], prep["spacy_doc"],
        content_type=content_type,
        acronym_context=acronym_context,
    )
    logger.debug("Full-text produced %d issues", len(full_issues))
    for i, iss in enumerate(full_issues[:10]):
        logger.debug(
            "full_iss[%d]: rule=%s flagged=%.60r span=%s",
            i, iss.rule_name, iss.flagged_text, iss.span,
        )
    return block_issues, full_issues


def _analyze_blocks_deterministic(
    blocks: list,
    content_type: str,
    original_text: str,
    acronym_context: dict[str, str] | None = None,
) -> list[IssueResponse]:
    """Run deterministic rules on each block individually.

    Each block is analysed with its own ``block_type``, and the
    resulting spans are mapped directly to original-text coordinates
    using ``block.char_map`` and ``block.start_pos``.

    Args:
        blocks: Parsed Block objects from the parser.
        content_type: Modular documentation type.
        original_text: Whitespace-normalized but uncleaned text.

    Returns:
        Accumulated issues with spans in original-text coordinates.
    """
    from app.extensions import get_nlp
    nlp = get_nlp()
    all_issues: list[IssueResponse] = []

    for block in blocks:
        if block.should_skip_analysis or not (block.content and block.content.strip()):
            continue
        issues = _analyze_single_block_deterministic(
            block, content_type, nlp, original_text, acronym_context,
        )
        all_issues.extend(issues)

    # Cross-block dedup: remove issues with the same rule_name and
    # flagged_text that appear across different blocks (e.g. AsciiDoc
    # conditional ifdef/endif branches that contain near-identical text).
    # Per-block dedup (inside deterministic.analyze) uses the stricter
    # key rule_name|flagged_text|sentence, so same-text issues from
    # different blocks survive it. This pass catches them.
    pre_dedup = len(all_issues)
    seen: set[str] = set()
    deduped: list[IssueResponse] = []
    for issue in all_issues:
        key = f"{issue.rule_name}|{issue.flagged_text}"
        if key in seen:
            logger.debug(
                "Cross-block dedup: skipping duplicate %s '%s'",
                issue.rule_name, issue.flagged_text,
            )
            continue
        seen.add(key)
        deduped.append(issue)
    if len(deduped) < pre_dedup:
        logger.info(
            "Cross-block dedup removed %d duplicate issues",
            pre_dedup - len(deduped),
        )

    return deduped


def _run_structural_analysis(
    blocks: list,
    content_type: str,
    original_text: str,
) -> list[IssueResponse]:
    """Run inter-block structural analysis on the full block sequence.

    Unlike per-block deterministic rules that analyze text in isolation,
    structural rules inspect the ordering and relationships between
    blocks (e.g., admonition placement, section structure).

    Args:
        blocks: Full list of parsed Block objects.
        content_type: Modular documentation type.
        original_text: Original document text for span resolution.

    Returns:
        List of structural issues with spans in original-text coordinates.
    """
    if not blocks:
        return []

    try:
        from rules.modular_compliance.structural_rules import run_structural_rules
        issues = run_structural_rules(blocks, content_type, original_text)
        logger.info("Structural analysis found %d issues", len(issues))
        return issues
    except (ImportError, ValueError, RuntimeError) as exc:
        logger.warning("Structural analysis failed: %s", exc)
        return []


def _extract_abstract(blocks: list) -> str | None:
    """Extract the first paragraph after the first heading.

    Returns the abstract text for targeted LLM quality analysis,
    or None if no heading/paragraph structure is found.
    """
    found_heading = False
    for block in blocks:
        if block.block_type == "heading":
            found_heading = True
            continue
        if not found_heading:
            continue
        if block.block_type in ("attribute_entry", "comment", "block_title"):
            continue
        if block.block_type == "paragraph":
            return (block.content or "").strip()
        break  # Non-paragraph content block = no clear abstract
    return None


def _compute_content_code_ranges(
    inline_content: str,
    char_map: list[int] | None,
) -> list[tuple[int, int]]:
    """Map backtick ranges from inline_content to content coordinates.

    Finds all backtick-delimited spans in *inline_content* (Tier 2),
    then uses *char_map* to translate those positions into *content*
    (Tier 3) coordinates.  Rules can directly check whether a position
    falls inside an inline-code range without needing the char_map.

    Args:
        inline_content: Block text with inline markers preserved.
        char_map: Maps content[i] -> inline_content position.

    Returns:
        List of ``(start, end)`` tuples in content coordinates.
    """
    if not inline_content:
        return []
    # Find backtick ranges in inline_content
    raw_ranges = [
        (m.start(), m.end())
        for m in re.finditer(r'`[^`]+`', inline_content)
    ]
    if not raw_ranges:
        return []

    if not char_map:
        # Identity mapping: content == inline_content
        return raw_ranges

    # Build set of inline_content positions inside backticks
    in_code: set[int] = set()
    for s, e in raw_ranges:
        in_code.update(range(s, e))

    # Walk char_map to find corresponding content positions
    ranges: list[tuple[int, int]] = []
    start: int | None = None
    for i, mapped in enumerate(char_map):
        if mapped in in_code:
            if start is None:
                start = i
        else:
            if start is not None:
                ranges.append((start, i))
                start = None
    if start is not None:
        ranges.append((start, len(char_map)))
    return ranges


# Pattern for bold wrapping inline code (e.g. **`curl`**)
# Italic wrapping detection (_`text`_) is intentionally omitted:
# `_` is too common as a literal character inside code/variable names
# (e.g. `_namespace_id_`), causing false positives.
_BOLD_CODE_RE = re.compile(r'\*\*`[^`]+`\*\*')


def _find_bold_code_in_inline(
    inline_content: str,
) -> list[tuple[int, int, str, str]]:
    """Find bold-wrapped code spans in inline_content.

    Detects ``**`text`**`` patterns.  Italic wrapping (``_`text`_``)
    is intentionally not detected because ``_`` appears frequently as a
    literal character inside code spans (e.g. ``_namespace_id_``),
    producing false positives.

    Args:
        inline_content: Block text with inline markers preserved.

    Returns:
        List of ``(start, end, "bold", code_text)`` tuples in
        inline_content coordinates.
    """
    results: list[tuple[int, int, str, str]] = []
    for m in _BOLD_CODE_RE.finditer(inline_content):
        inner = m.group()       # e.g. **`curl`**
        results.append((m.start(), m.end(), "bold", inner[3:-3]))
    return results


def _map_ranges_to_content(
    ranges: list[tuple[int, int, str, str]],
    char_map: list[int],
) -> list[tuple[int, int, str, str]]:
    """Translate inline_content ranges to content coordinates via char_map.

    Args:
        ranges: ``(ic_start, ic_end, fmt, code_text)`` in inline coords.
        char_map: Maps content[i] -> inline_content position.

    Returns:
        Ranges remapped to content coordinates.
    """
    mapped: list[tuple[int, int, str, str]] = []
    for ic_start, ic_end, fmt, code_text in ranges:
        c_start: int | None = None
        c_end: int | None = None
        for i, mapped_pos in enumerate(char_map):
            if c_start is None and mapped_pos >= ic_start:
                c_start = i
            if mapped_pos < ic_end:
                c_end = i + 1
        if c_start is not None and c_end is not None:
            mapped.append((c_start, c_end, fmt, code_text))
    return mapped


def _compute_bold_code_ranges(
    inline_content: str,
    char_map: list[int] | None,
) -> list[tuple[int, int, str, str]]:
    """Find bold-wrapped code in inline_content.

    Detects ``**`curl`**`` (bold wrapping monospace) which violates
    IBM Style Guide formatting rules.  Code should use monospace only.

    Args:
        inline_content: Block text with inline markers preserved (Tier 2).
        char_map: Maps content[i] -> inline_content position.

    Returns:
        List of ``(start, end, format_type, code_text)`` tuples in
        content coordinates.  *format_type* is ``"bold"`` or ``"italic"``.
    """
    if not inline_content:
        return []

    results = _find_bold_code_in_inline(inline_content)
    if not results:
        return []

    if not char_map:
        return results

    return _map_ranges_to_content(results, char_map)


def _analyze_single_block_deterministic(
    block: Any,
    content_type: str,
    nlp: Any,
    original_text: str,
    acronym_context: dict[str, str] | None = None,
) -> list[IssueResponse]:
    """Analyse a single block with its block_type and remap spans.

    Maps issue spans directly to original-text coordinates using
    ``block.char_map`` (inline-stripping map) and ``block.start_pos``,
    then refines with a text search in the original text.  This bypasses
    the cleaned-text offset map, which can drift due to different inline
    markup handling between the parser and preprocessor.

    Args:
        block: A parsed Block object.
        content_type: Modular documentation type.
        nlp: SpaCy language model instance.
        original_text: The whitespace-normalized but uncleaned text.

    Returns:
        Issues with spans mapped to original-text coordinates.
    """
    block_text = block.content
    block_type = block.block_type or "paragraph"

    doc = nlp(block_text)
    sentences = [s.text.strip() for s in doc.sents if s.text.strip()]
    if not sentences:
        sentences = [block_text]

    inline_code_ranges = _compute_content_code_ranges(
        block.inline_content, block.char_map,
    )
    bold_code_ranges = _compute_bold_code_ranges(
        block.inline_content, block.char_map,
    )

    issues = run_deterministic(
        block_text, sentences, doc,
        block_type=block_type,
        content_type=content_type,
        inline_code_ranges=inline_code_ranges,
        bold_code_ranges=bold_code_ranges,
        acronym_context=acronym_context,
    )

    _map_block_issues_to_original(issues, block, original_text)
    return issues


def _shift_issue_spans(
    issues: list[IssueResponse],
    offset: int,
) -> None:
    """Shift issue spans by *offset* characters.

    Args:
        issues: Issues whose spans are relative to block start.
        offset: Character offset of the block within the full text.
    """
    for issue in issues:
        if issue.span and len(issue.span) >= 2:
            issue.span = [issue.span[0] + offset, issue.span[1] + offset]


def _map_block_issues_to_original(
    issues: list[IssueResponse],
    block: Any,
    original_text: str,
) -> None:
    """Map per-block issue spans to original-text coordinates.

    Uses ``block.char_map`` (from inline-marker stripping) and
    ``block.start_pos`` to compute an approximate original-text
    position, then refines with :func:`_find_flagged_in_text`.

    Modifies issues in place.  Issues whose flagged text cannot be
    found in the original text get the ``[-1, -1]`` sentinel.

    Args:
        issues: Issues with spans relative to ``block.content``.
        block: The parsed Block object that produced these issues.
        original_text: The whitespace-normalized but uncleaned text.
    """
    char_map = getattr(block, "char_map", None)
    orig_len = len(original_text)

    for issue in issues:
        if not issue.span or not issue.flagged_text:
            continue

        span_start = issue.span[0]

        # Map block-content position to raw-content position
        if char_map and span_start < len(char_map):
            raw_offset = char_map[span_start]
        else:
            raw_offset = span_start

        orig_approx = block.start_pos + raw_offset
        flagged = issue.flagged_text

        # Search near the approximate position first
        search_from = max(0, orig_approx - len(flagged) - 20)
        search_to = min(orig_len, orig_approx + len(flagged) * 3 + 200)

        result = _find_flagged_in_text(
            original_text, flagged, search_from, search_to,
        )
        if result:
            issue.span = [result[0], result[1]]
            issue.flagged_text = result[2]
            continue

        # Widen to the full block range
        block_from = max(0, block.start_pos - 20)
        block_to = min(orig_len, block.end_pos + 200)
        result = _find_flagged_in_text(
            original_text, flagged, block_from, block_to,
        )
        if result:
            issue.span = [result[0], result[1]]
            issue.flagged_text = result[2]
            continue

        # Mark as failed remap
        logger.debug(
            "_map_block: FAILED for %r block=%s pos=%d",
            flagged[:60], block.block_type, block.start_pos,
        )
        issue.span = [-1, -1]


def _merge_block_and_full_issues(
    block_issues: list[IssueResponse],
    full_issues: list[IssueResponse],
) -> list[IssueResponse]:
    """Merge per-block issues with full-document issues, deduplicating.

    Keeps all block-level issues. From the full-document pass, only adds
    issues not already found at the block level.

    Args:
        block_issues: Issues from per-block analysis.
        full_issues: Issues from full-document analysis.

    Returns:
        Merged and deduplicated list.
    """
    seen = {f"{i.rule_name}|{i.flagged_text}" for i in block_issues}
    for issue in full_issues:
        key = f"{issue.rule_name}|{issue.flagged_text}"
        if key not in seen:
            block_issues.append(issue)
    return block_issues


def _resolve_llm_text_sources(
    prep: dict[str, Any],
) -> tuple[list[str], str, list[int]]:
    """Choose text blocks, resolve text, and offset map for LLM analysis.

    When lite_markers (Markdown from parsed blocks) are available,
    uses semantic chunking; otherwise falls back to paragraph splitting.

    Args:
        prep: Preprocessed text data from ``preprocess()``.

    Returns:
        Tuple of (text_blocks, resolve_text, remap_offset).
    """
    parsed_blocks = prep.get("blocks", [])
    has_lite_markers = bool(parsed_blocks) and prep.get("lite_markers")

    if has_lite_markers:
        text_blocks = _split_into_semantic_chunks(parsed_blocks)
        resolve_text = prep["lite_markers"]
        remap_offset = prep.get("lite_markers_offset_map", [])
    else:
        text_blocks = _split_into_blocks(prep["text"])
        resolve_text = prep["text"]
        remap_offset = prep.get("offset_map", [])

    return text_blocks, resolve_text, remap_offset


def _run_llm_granular(
    session_id: str,
    socket_sid: Optional[str],
    prep: dict[str, Any],
    content_type: str,
    acronym_context: dict[str, str] | None = None,
    style_guide_excerpts: list[dict] | None = None,
    document_outline: str | None = None,
) -> list[IssueResponse]:
    """Run the LLM granular (per-block) analysis pass.

    Supports incremental analysis: when re-analysing the same session,
    only changed blocks are sent to the LLM.  Unchanged blocks reuse
    cached results from the previous run via the session store.

    Args:
        session_id: Analysis session identifier.
        socket_sid: Socket.IO session ID.
        prep: Preprocessed text data.
        content_type: Modular documentation type.
        acronym_context: Known acronym definitions from the document.
        style_guide_excerpts: Relevant style guide excerpt dicts.
        document_outline: Compact heading outline of the full document.

    Returns:
        List of LLM-detected issues, empty on failure.
    """
    _emit_progress(socket_sid, session_id, "llm_granular", "Running AI analysis", 60)

    try:
        if analyze_block is not None:
            text_blocks, resolve_text, remap_offset = _resolve_llm_text_sources(prep)
            progress_ctx = {
                "socket_sid": socket_sid,
                "session_id": session_id,
                "blocks_total": len(text_blocks),
            }
            results = _run_incremental_blocks(
                session_id, text_blocks, prep["sentences"],
                content_type, acronym_context,
                style_guide_excerpts=style_guide_excerpts,
                document_outline=document_outline,
                progress_context=progress_ctx,
            )
            issues = _parse_llm_results(results, "llm_granular", resolve_text)
            for i, iss in enumerate(issues):
                logger.debug(
                    "LLM granular[%d] BEFORE remap: rule=%s span=%s "
                    "flagged=%r",
                    i, iss.rule_name, iss.span, iss.flagged_text[:80] if iss.flagged_text else "",
                )
            _remap_issues_to_original(
                issues, remap_offset, prep.get("original_text", ""),
            )
            for i, iss in enumerate(issues):
                logger.debug(
                    "LLM granular[%d] AFTER remap: rule=%s span=%s "
                    "flagged=%r",
                    i, iss.rule_name, iss.span, iss.flagged_text[:80] if iss.flagged_text else "",
                )
            issues = _validate_llm_issues(issues)
            issues = _strip_backtick_suggestions(
                issues, prep.get("original_text", ""),
            )
            _emit_event(socket_sid, "llm_granular_complete", {
                "session_id": session_id,
                "issues": [i.to_dict() for i in issues],
            })
            return issues
    except (ConnectionError, TimeoutError, ValueError, KeyError) as exc:
        logger.warning("LLM granular pass failed: %s", exc)
        _emit_event(socket_sid, "llm_skipped", {
            "session_id": session_id,
            "phase": "granular",
            "reason": str(exc),
        })

    return []


def _run_incremental_blocks(
    session_id: str,
    blocks: list[str],
    sentences: list[str],
    content_type: str,
    acronym_context: dict[str, str] | None = None,
    style_guide_excerpts: list[dict] | None = None,
    document_outline: str | None = None,
    progress_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Analyze blocks incrementally, skipping unchanged ones.

    Compares current block hashes against the session store.  Only
    changed blocks are sent to ``_analyze_blocks()``.  Results for
    unchanged blocks are reused from the previous run.  After analysis
    the new hashes and per-block issues are stored for the next run.

    Falls back to full analysis when the session store is unavailable
    or the session has no previous block data.

    Args:
        session_id: Analysis session identifier.
        blocks: Current text blocks.
        sentences: Full document sentences.
        content_type: Modular documentation type.
        acronym_context: Known acronym definitions.
        style_guide_excerpts: Relevant style guide excerpt dicts.
        document_outline: Compact heading outline of the full document.

    Returns:
        Combined list of raw issue dicts from all blocks.
    """
    block_hashes = [
        _block_cache_key(b, content_type) for b in blocks
    ]

    # Try to get previous block data from the session store
    prev = _get_previous_block_data(session_id)
    if prev is None:
        # No previous data — full analysis
        results = _analyze_blocks(
            blocks, sentences, content_type, acronym_context,
            style_guide_excerpts=style_guide_excerpts,
            document_outline=document_outline,
            progress_context=progress_context,
        )
        _store_block_data(
            session_id, block_hashes, blocks, results,
        )
        return results

    prev_hashes, prev_issues = prev
    changed_indices = [
        i for i, h in enumerate(block_hashes)
        if i >= len(prev_hashes) or h != prev_hashes[i]
    ]

    if not changed_indices:
        logger.info("Incremental: all %d blocks unchanged", len(blocks))
        all_results: list[dict[str, Any]] = []
        for h in block_hashes:
            all_results.extend(prev_issues.get(h, []))
        return all_results

    logger.info(
        "Incremental: %d/%d blocks changed, re-analysing",
        len(changed_indices), len(blocks),
    )

    changed_blocks = [blocks[i] for i in changed_indices]
    new_results = _analyze_blocks(
        changed_blocks, sentences, content_type, acronym_context,
        style_guide_excerpts=style_guide_excerpts,
        document_outline=document_outline,
        progress_context=progress_context,
    )

    # Build per-block issue mapping for changed blocks
    per_block: dict[str, list[dict[str, Any]]] = dict(prev_issues)
    for i, idx in enumerate(changed_indices):
        per_block[block_hashes[idx]] = []
    # Distribute new results to the changed block buckets (best-effort:
    # results don't carry block index, so store all new results under
    # each changed hash proportionally is impractical — store the full
    # batch under all changed hashes combined, which is correct for
    # downstream processing since they're merged anyway)
    for idx in changed_indices:
        per_block[block_hashes[idx]] = new_results

    _store_block_data(
        session_id, block_hashes, blocks, [],
        per_block_override=per_block,
    )

    # Combine reused + new results
    reused: list[dict[str, Any]] = []
    for i, h in enumerate(block_hashes):
        if i not in changed_indices:
            reused.extend(prev_issues.get(h, []))

    return reused + new_results


def _get_previous_block_data(
    session_id: str,
) -> Optional[tuple[list[str], dict[str, list[dict[str, Any]]]]]:
    """Retrieve previous block data from the session store.

    Args:
        session_id: The analysis session identifier.

    Returns:
        Tuple of (hashes, per-block issues) or None.
    """
    try:
        store = _get_session_store()
        return store.get_block_results(session_id)
    except (ImportError, RuntimeError, AttributeError):
        return None


def _store_block_data(
    session_id: str,
    block_hashes: list[str],
    blocks: list[str],
    results: list[dict[str, Any]],
    per_block_override: Optional[dict[str, list[dict[str, Any]]]] = None,
) -> None:
    """Store block hashes and per-block issues in the session store.

    Args:
        session_id: The analysis session identifier.
        block_hashes: Ordered list of block content hashes.
        blocks: The text blocks (used for hash-to-issues mapping).
        results: Raw issue dicts from the LLM (for initial full analysis).
        per_block_override: Pre-built per-block mapping (for incremental).
    """
    if per_block_override is not None:
        per_block = per_block_override
    else:
        # For full analysis, store all results under each block hash.
        # The block cache (Change 2) handles per-block deduplication.
        per_block = dict.fromkeys(block_hashes, results)

    try:
        store = _get_session_store()
        store.store_block_results(session_id, block_hashes, per_block)
    except (ImportError, RuntimeError, AttributeError) as exc:
        logger.debug("Could not store block data: %s", exc)


def _run_llm_global(
    session_id: str,
    socket_sid: Optional[str],
    prep: dict[str, Any],
    content_type: str,
    style_guide_excerpts: list[dict] | None = None,
    document_outline: str | None = None,
    abstract_context: str | None = None,
) -> list[IssueResponse]:
    """Run the LLM global (full-document) analysis pass.

    Sends the full document text (lite-markers Markdown when available)
    to the LLM for tone, flow, minimalism, wordiness, audience,
    structure, and accessibility checks.

    Args:
        session_id: Analysis session identifier.
        socket_sid: Socket.IO session ID.
        prep: Preprocessed text data.
        content_type: Modular documentation type.
        style_guide_excerpts: Relevant style guide excerpt dicts.
        document_outline: Compact heading outline for structural review.
        abstract_context: First paragraph after heading (module abstract)
            for targeted short-description quality evaluation.

    Returns:
        List of LLM-detected issues, empty on failure or skip.
    """
    if prep["word_count"] < _GLOBAL_PASS_MIN_WORDS:
        logger.info(
            "Skipping LLM global pass: %d words below minimum of %d",
            prep["word_count"], _GLOBAL_PASS_MIN_WORDS,
        )
        return []

    _emit_progress(socket_sid, session_id, "llm_global", "Running global review", 80)

    # Prefer lite_markers (Markdown with structure) over cleaned text
    global_text = prep.get("lite_markers") or prep["text"]
    global_offset_map = prep.get("lite_markers_offset_map") or prep.get("offset_map", [])

    try:
        if analyze_global is not None:
            results = analyze_global(
                global_text, content_type,
                style_guide_excerpts=style_guide_excerpts,
                document_outline=document_outline,
                abstract_context=abstract_context,
            )
            issues = _parse_llm_results(results, "llm_global", global_text)
            for i, iss in enumerate(issues):
                logger.debug(
                    "LLM global[%d] BEFORE remap: rule=%s span=%s "
                    "flagged=%r",
                    i, iss.rule_name, iss.span, iss.flagged_text[:80] if iss.flagged_text else "",
                )
            _remap_issues_to_original(
                issues, global_offset_map, prep.get("original_text", ""),
            )
            for i, iss in enumerate(issues):
                logger.debug(
                    "LLM global[%d] AFTER remap: rule=%s span=%s "
                    "flagged=%r",
                    i, iss.rule_name, iss.span, iss.flagged_text[:80] if iss.flagged_text else "",
                )
            issues = _validate_llm_issues(issues)
            issues = _strip_backtick_suggestions(
                issues, prep.get("original_text", ""),
            )
            _emit_event(socket_sid, "llm_global_complete", {
                "session_id": session_id,
                "issues": [i.to_dict() for i in issues],
            })
            return issues
    except (ConnectionError, TimeoutError, ValueError, KeyError) as exc:
        logger.warning("LLM global pass failed: %s", exc)
        _emit_event(socket_sid, "llm_skipped", {
            "session_id": session_id,
            "phase": "global",
            "reason": str(exc),
        })

    return []


# ---------------------------------------------------------------------------
# LLM judge self-correction (Phase 2C)
# ---------------------------------------------------------------------------


def _run_judge_pass(
    issues: list[IssueResponse],
    document_excerpt: str,
    content_type: str,
) -> list[IssueResponse]:
    """Run self-correction judge pass on LLM issues.

    Batches issues into groups of ``_JUDGE_BATCH_SIZE`` for quality
    (LLMs review shorter lists more reliably). Fail-open: on any
    error, all issues are kept.

    Args:
        issues: LLM-generated issues to review.
        document_excerpt: Representative excerpt for context.
        content_type: Modular documentation type.

    Returns:
        Filtered list with false positives removed.
    """
    if not issues or judge_issues is None:
        return issues

    if len(issues) <= _JUDGE_BATCH_SIZE:
        return _judge_single_batch(issues, document_excerpt, content_type)

    kept: list[IssueResponse] = []
    for batch_start in range(0, len(issues), _JUDGE_BATCH_SIZE):
        batch = issues[batch_start:batch_start + _JUDGE_BATCH_SIZE]
        kept.extend(_judge_single_batch(batch, document_excerpt, content_type))

    logger.info(
        "Judge pass: %d → %d issues (%d dropped)",
        len(issues), len(kept), len(issues) - len(kept),
    )
    return kept


def _judge_single_batch(
    issues: list[IssueResponse],
    document_excerpt: str,
    content_type: str,
) -> list[IssueResponse]:
    """Run judge on a single batch of issues.

    Converts IssueResponse instances to dicts for the judge prompt,
    then filters based on the keep/drop verdict.

    Args:
        issues: Batch of issues to review.
        document_excerpt: Representative excerpt for context.
        content_type: Modular documentation type.

    Returns:
        Issues that the judge decided to keep.
    """
    issue_dicts = [
        {
            "flagged_text": iss.flagged_text,
            "message": iss.message,
            "category": iss.category,
            "confidence": iss.confidence,
            "suggestions": iss.suggestions,
        }
        for iss in issues
    ]

    keep_indices, drop_indices = judge_issues(
        issue_dicts, document_excerpt, content_type,
    )

    keep_set = set(keep_indices)
    kept = [iss for i, iss in enumerate(issues) if i in keep_set]

    if drop_indices:
        for idx in drop_indices:
            if 0 <= idx < len(issues):
                logger.debug(
                    "Judge dropped: flagged=%r category=%s",
                    issues[idx].flagged_text[:60], issues[idx].category,
                )
    return kept


# ---------------------------------------------------------------------------
# Acronym collection
# ---------------------------------------------------------------------------

# Matches "Full Name (ACRONYM)" — e.g. "Container Storage Interface (CSI)"
# Requires at least two words in the expansion to avoid matching articles
# like "The (CSI)" as acronym definitions.
_ACRONYM_DEF_RE = re.compile(
    r"([A-Z][a-zA-Z]+(?:\s+[a-zA-Z]+)+)\s+\(([A-Z][A-Z0-9]{1,10})\)",
)
# Matches "(ACRONYM) Full Name" — reverse pattern.
# Uses title-case heuristic (each word starts uppercase) to avoid
# greedily matching lowercase words beyond the expansion.
_ACRONYM_DEF_REV_RE = re.compile(
    r"\(([A-Z][A-Z0-9]{1,10})\)\s+([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)+)",
)


def _collect_acronyms(text: str) -> dict[str, str]:
    """Scan text for acronym definitions.

    Finds patterns like "Full Name (ACRONYM)" and "(ACRONYM) Full Name"
    so the LLM can avoid flagging defined acronyms as undefined.

    Args:
        text: Full document text (cleaned and normalized).

    Returns:
        Dict mapping abbreviation to expansion, e.g.
        ``{"CSI": "Container Storage Interface"}``.
    """
    acronyms: dict[str, str] = {}
    for match in _ACRONYM_DEF_RE.finditer(text):
        expansion, abbrev = match.group(1).strip(), match.group(2)
        acronyms[abbrev] = expansion
    for match in _ACRONYM_DEF_REV_RE.finditer(text):
        abbrev, expansion = match.group(1), match.group(2).strip()
        if abbrev not in acronyms:
            acronyms[abbrev] = expansion
    return acronyms


def _build_document_outline(blocks: list) -> str:
    """Build a compact heading outline from parsed blocks.

    Extracts heading blocks and formats them as a numbered hierarchy
    so the LLM can see the overall document structure when analysing
    individual chunks.

    Args:
        blocks: List of Block dataclass instances from a parser.

    Returns:
        Formatted outline string, or empty string if no headings found.
    """
    headings: list[tuple[int, str]] = []
    for block in blocks:
        if getattr(block, "block_type", "") == "heading" and getattr(block, "content", ""):
            level = getattr(block, "level", 1) or 1
            headings.append((level, block.content))

    if not headings:
        return ""

    lines: list[str] = []
    counters: dict[int, int] = {}
    for level, text in headings:
        counters[level] = counters.get(level, 0) + 1
        # Reset deeper-level counters when a higher-level heading appears
        deeper_keys = [k for k in counters if k > level]
        for deeper in deeper_keys:
            del counters[deeper]
        indent = "  " * (level - 1)
        lines.append(f"{indent}{counters[level]}. {text}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Block-level LLM response cache
# ---------------------------------------------------------------------------

# Thread-safe cache keyed by sha256(block_text|content_type).
# Prevents duplicate LLM calls when the same block is re-analysed
# (re-analysis, repeated paragraphs, unchanged blocks).
_block_cache: dict[str, dict[str, Any]] = {}
_block_cache_lock = threading.Lock()


def _block_cache_key(block_text: str, content_type: str) -> str:
    """Compute a deterministic cache key for a text block.

    Args:
        block_text: The raw block content.
        content_type: Modular documentation type.

    Returns:
        Hex digest string.
    """
    return hashlib.sha256(
        f"{block_text}|{content_type}".encode(),
    ).hexdigest()


def _get_cached_block(key: str) -> list[dict[str, Any]] | None:
    """Retrieve cached LLM results for a block if still valid.

    Args:
        key: Cache key from ``_block_cache_key()``.

    Returns:
        Cached issue list, or ``None`` on miss / expiry.
    """
    ttl = Config.BLOCK_CACHE_TTL
    with _block_cache_lock:
        entry = _block_cache.get(key)
        if entry and time.time() - entry["ts"] < ttl:
            return entry["issues"]
        if entry:
            del _block_cache[key]
    return None


def _cache_block(key: str, issues: list[dict[str, Any]]) -> None:
    """Store LLM results for a block in the cache.

    Args:
        key: Cache key from ``_block_cache_key()``.
        issues: Raw issue dicts returned by the LLM.
    """
    with _block_cache_lock:
        _block_cache[key] = {"issues": issues, "ts": time.time()}


# ---------------------------------------------------------------------------
# Block splitting and parallel execution
# ---------------------------------------------------------------------------

# Minimum character count per block; smaller paragraphs are merged together.
_MIN_BLOCK_CHARS = 1500

# Maximum characters per semantic chunk (larger budget since blocks are
# semantic units and never split mid-block).
_MAX_SEMANTIC_CHUNK_CHARS = 6000

# Number of trailing blocks to repeat at the start of the next chunk
# for cross-boundary context continuity.
_OVERLAP_BLOCK_COUNT = 3

# Minimum word count for the global (full-document) LLM pass.
_GLOBAL_PASS_MIN_WORDS = 30


def _split_into_blocks(text: str) -> list[str]:
    """Split text into paragraph blocks for parallel LLM processing.

    Groups adjacent paragraphs until each block exceeds
    ``_MIN_BLOCK_CHARS`` characters. This balances parallelism against
    per-call overhead.

    Args:
        text: Full document text.

    Returns:
        List of text blocks (at least one).
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return [text]

    blocks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for para in paragraphs:
        current_parts.append(para)
        current_len += len(para)
        if current_len >= _MIN_BLOCK_CHARS:
            blocks.append("\n\n".join(current_parts))
            current_parts = []
            current_len = 0

    if current_parts:
        blocks.append("\n\n".join(current_parts))

    return blocks if blocks else [text]


def _split_into_semantic_chunks(
    blocks: list,
    max_chars: int = _MAX_SEMANTIC_CHUNK_CHARS,
) -> list[str]:
    """Group parsed blocks into LLM-sized Markdown chunks with overlap.

    Never splits inside a block. Only splits on block boundaries.
    Repeats the last ``_OVERLAP_BLOCK_COUNT`` blocks from the previous
    chunk at the start of the next chunk so the LLM has cross-boundary
    context continuity.

    Args:
        blocks: List of Block dataclass instances from a parser.
        max_chars: Maximum characters per chunk.

    Returns:
        List of Markdown text chunks (at least one).
    """
    block_parts = _collect_block_markdown(blocks)
    return _group_with_overlap(block_parts, max_chars)


def _collect_block_markdown(blocks: list) -> list[str]:
    """Convert analysable blocks to Markdown strings.

    Args:
        blocks: List of Block dataclass instances from a parser.

    Returns:
        List of Markdown strings, one per analysable block.
    """
    parts: list[str] = []
    for block in blocks:
        if block.should_skip_analysis and block.block_type != "code_block":
            continue
        if not block.content and block.block_type != "code_block":
            continue
        parts.append(_block_to_markdown(block))
    return parts


def _group_with_overlap(
    parts: list[str],
    max_chars: int,
) -> list[str]:
    """Group Markdown parts into chunks with trailing-block overlap.

    The last ``_OVERLAP_BLOCK_COUNT`` blocks of each chunk are
    repeated at the start of the next chunk for context continuity.

    Args:
        parts: Markdown strings for each block.
        max_chars: Maximum characters per chunk.

    Returns:
        List of joined Markdown chunks (at least one).
    """
    if not parts:
        return [""]

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for part in parts:
        part_len = len(part)
        if current_len + part_len > max_chars and current:
            chunks.append("\n\n".join(current))
            # Carry the last N blocks as overlap into the next chunk
            overlap = current[-_OVERLAP_BLOCK_COUNT:]
            current = list(overlap)
            current_len = sum(len(p) for p in current)

        current.append(part)
        current_len += part_len

    if current:
        chunks.append("\n\n".join(current))

    return chunks if chunks else [""]


def _analyze_blocks(
    blocks: list[str],
    sentences: list[str],
    content_type: str,
    acronym_context: dict[str, str] | None = None,
    style_guide_excerpts: list[dict] | None = None,
    document_outline: str | None = None,
    progress_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run LLM analysis on blocks, using parallelism when beneficial.

    For a single block, calls the LLM directly. For multiple blocks,
    uses a ThreadPoolExecutor capped at ``LLM_MAX_CONCURRENT`` workers.

    Args:
        blocks: List of text blocks to analyse.
        sentences: Full document sentences (used for single-block path).
        content_type: Modular documentation type.
        acronym_context: Known acronym definitions from the document.
        style_guide_excerpts: Relevant style guide excerpt dicts.
        document_outline: Compact heading outline of the full document.
        progress_context: Optional dict with socket_sid, session_id,
            blocks_total for per-block progress events.

    Returns:
        Combined list of raw issue dicts from all blocks.
    """
    assert analyze_block is not None  # guarded by caller
    if len(blocks) <= 1:
        key = _block_cache_key(blocks[0], content_type)
        cached = _get_cached_block(key)
        if cached is not None:
            logger.debug("Single-block cache hit (key=%s)", key[:12])
            return cached
        results = analyze_block(
            blocks[0], sentences, content_type,
            acronym_context=acronym_context,
            style_guide_excerpts=style_guide_excerpts,
            document_outline=document_outline,
        )
        _cache_block(key, results)
        return results

    return _analyze_blocks_parallel(
        blocks, content_type, acronym_context,
        style_guide_excerpts=style_guide_excerpts,
        document_outline=document_outline,
        progress_context=progress_context,
    )


def _analyze_blocks_parallel(
    blocks: list[str],
    content_type: str,
    acronym_context: dict[str, str] | None = None,
    style_guide_excerpts: list[dict] | None = None,
    document_outline: str | None = None,
    progress_context: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Execute multiple block analyses concurrently.

    Checks the block cache before submitting each block to the LLM.
    Cached results are merged with freshly computed ones.  Failures on
    individual blocks are logged and skipped so that successful blocks
    still contribute results.

    Args:
        blocks: List of text blocks.
        content_type: Modular documentation type.
        acronym_context: Known acronym definitions from the document.
        style_guide_excerpts: Relevant style guide excerpt dicts.
        document_outline: Compact heading outline of the full document.
        progress_context: Optional dict for per-block progress events.

    Returns:
        Combined list of raw issue dicts from all successful blocks.
    """
    max_workers = min(len(blocks), Config.LLM_MAX_CONCURRENT)
    logger.info(
        "Running %d blocks in parallel (max_workers=%d)",
        len(blocks), max_workers,
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures, cached_results = _submit_block_futures(
            executor, blocks, content_type, acronym_context,
            style_guide_excerpts=style_guide_excerpts,
            document_outline=document_outline,
        )
        # Account for cached blocks in progress counter
        cached_offset = len(cached_results) if progress_context else 0
        new_results = _collect_block_results(
            futures, progress_context, cached_offset,
        )

    return cached_results + new_results


def _submit_block_futures(
    executor: ThreadPoolExecutor,
    blocks: list[str],
    content_type: str,
    acronym_context: dict[str, str] | None = None,
    style_guide_excerpts: list[dict] | None = None,
    document_outline: str | None = None,
) -> tuple[dict[Any, int], list[dict[str, Any]]]:
    """Submit each block to the executor, skipping cache hits.

    Checks the block cache before submitting.  Cached results are
    returned directly and the block is not submitted to the executor.

    Args:
        executor: The thread pool executor.
        blocks: List of text blocks.
        content_type: Modular documentation type.
        acronym_context: Known acronym definitions from the document.
        style_guide_excerpts: Relevant style guide excerpt dicts.
        document_outline: Compact heading outline of the full document.

    Returns:
        Tuple of (futures mapping, cached issue list).
    """
    futures: dict[Any, int] = {}
    cached_results: list[dict[str, Any]] = []

    for i, block in enumerate(blocks):
        key = _block_cache_key(block, content_type)
        cached = _get_cached_block(key)
        if cached is not None:
            logger.debug("Block %d cache hit (key=%s)", i, key[:12])
            cached_results.extend(cached)
            continue

        block_sentences = _extract_block_sentences(block)
        future = executor.submit(
            _analyze_and_cache_block, block, block_sentences,
            content_type, key, acronym_context, style_guide_excerpts,
            document_outline,
        )
        futures[future] = i

    return futures, cached_results


def _analyze_and_cache_block(
    block: str,
    sentences: list[str],
    content_type: str,
    cache_key: str,
    acronym_context: dict[str, str] | None = None,
    style_guide_excerpts: list[dict] | None = None,
    document_outline: str | None = None,
) -> list[dict[str, Any]]:
    """Analyze a single block and store results in the cache.

    Args:
        block: The text block to analyse.
        sentences: Extracted sentences from the block.
        content_type: Modular documentation type.
        cache_key: Pre-computed cache key for this block.
        acronym_context: Known acronym definitions from the document.
        style_guide_excerpts: Relevant style guide excerpt dicts.
        document_outline: Compact heading outline of the full document.

    Returns:
        Raw issue dicts from the LLM.
    """
    assert analyze_block is not None  # guarded by caller
    results = analyze_block(
        block, sentences, content_type,
        acronym_context=acronym_context,
        style_guide_excerpts=style_guide_excerpts,
        document_outline=document_outline,
    )
    _cache_block(cache_key, results)
    return results


def _collect_block_results(
    futures: dict[Any, int],
    progress_context: dict[str, Any] | None = None,
    cached_offset: int = 0,
) -> list[dict[str, Any]]:
    """Collect results from completed block futures.

    Emits per-block ``stage_progress`` events when a progress context
    is provided, enabling a live counter on the frontend.  Results are
    sorted by block index before returning so that deduplication
    ordering is deterministic regardless of thread completion timing.

    Args:
        futures: Mapping of Future objects to block indices.
        progress_context: Optional dict with socket_sid, session_id,
            blocks_total for progress events.
        cached_offset: Number of already-cached blocks to add to
            the done counter (incremental analysis).

    Returns:
        Combined list of raw issue dicts, ordered by block index.
    """
    indexed_results: list[tuple[int, list[dict[str, Any]]]] = []
    blocks_done = cached_offset
    for future in as_completed(futures):
        block_idx = futures[future]
        block_issues: list[dict[str, Any]] = []
        try:
            block_issues = future.result()
        except (ConnectionError, TimeoutError, RuntimeError) as exc:
            logger.warning("Block %d analysis failed: %s", block_idx, exc)
        indexed_results.append((block_idx, block_issues))
        blocks_done += 1
        if progress_context:
            _emit_event(
                progress_context["socket_sid"],
                "stage_progress",
                {
                    "session_id": progress_context["session_id"],
                    "phase": "llm_granular",
                    "status": "progress",
                    "blocks_done": blocks_done,
                    "blocks_total": progress_context["blocks_total"],
                },
            )
    # Sort by block index for deterministic dedup ordering
    indexed_results.sort(key=lambda x: x[0])
    all_results: list[dict[str, Any]] = []
    for _, issues in indexed_results:
        all_results.extend(issues)
    return all_results


def _extract_block_sentences(block_text: str) -> list[str]:
    """Extract sentences from a text block for LLM context.

    Uses line-level splitting suitable for technical documentation
    where each line is typically a sentence or list item.

    Args:
        block_text: A single text block.

    Returns:
        List of non-empty sentence strings.
    """
    sentences = [
        line.strip() for line in block_text.split("\n")
        if line.strip()
    ]
    return sentences if sentences else [block_text]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_llm_results(
    results: list[dict[str, Any]],
    source: str,
    original_text: str = "",
) -> list[IssueResponse]:
    """Convert raw LLM result dicts to IssueResponse instances.

    Computes character spans by finding ``flagged_text`` in the original
    text, and maps LLM categories to backend rule names for proper
    frontend group assignment.

    Args:
        results: List of dicts from the LLM client.
        source: Source label for the issues (e.g., "llm_granular").
        original_text: The original (pre-cleanup) text for span resolution.

    Returns:
        List of IssueResponse instances.
    """
    issues: list[IssueResponse] = []
    for raw in results:
        try:
            raw["source"] = source
            raw.setdefault("id", str(uuid.uuid4()))
            raw.setdefault("status", IssueStatus.OPEN.value)
            _resolve_llm_rule_name(raw)
            issue = IssueResponse.from_dict(raw)

            # Filter out issues that flag synthetic placeholder text
            if _is_placeholder_issue(issue):
                logger.debug(
                    "Filtered placeholder LLM issue: flagged=%r msg=%r",
                    issue.flagged_text[:80], (issue.message or "")[:80],
                )
                continue

            _resolve_llm_span(issue, original_text)

            # Strip lite-markers Markdown prefixes from suggestions,
            # message, and flagged_text so Accept doesn't insert
            # "- " or "1. " and issue cards don't show raw Markdown.
            issue.suggestions = [
                _strip_lite_markers(s) for s in issue.suggestions
            ]
            issue.message = _strip_lite_markers(issue.message)
            issue.flagged_text = _strip_lite_markers(issue.flagged_text)

            issues.append(issue)
        except (KeyError, TypeError, ValueError) as exc:
            logger.warning("Failed to parse LLM result: %s", exc)
    return issues


def _is_placeholder_issue(issue: IssueResponse) -> bool:
    """Check if an LLM issue is about synthetic placeholder text.

    The preprocessor replaces backtick code, attribute references, and
    plus-monospace with the word ``placeholder``. Only filter issues
    where the flagged text itself contains ``placeholder`` (the
    underline would show nonsense) or the message is specifically about
    placeholder being vague. Do NOT filter based on sentence context
    or suggestions — valid issues on real text near code references
    would be lost.

    Args:
        issue: The LLM-detected issue to check.

    Returns:
        True if the issue appears to be about placeholder text.
    """
    flagged = (issue.flagged_text or "").lower()
    if "placeholder" in flagged:
        return True
    msg = (issue.message or "").lower()
    if "placeholder" in msg and "vague" in msg:
        return True
    return False


def _validate_llm_issues(
    issues: list[IssueResponse],
) -> list[IssueResponse]:
    """Drop LLM issues whose flagged_text cannot be found in the source.

    After ``_resolve_llm_span()`` tries all search strategies, issues
    with unresolvable ``flagged_text`` retain a ``[0, 0]`` span.  These
    are either hallucinated by the LLM or too mangled to highlight and
    should be silently removed before they reach the frontend.

    Document-level issues without ``flagged_text`` (e.g., tone or flow
    observations) are kept because they don't need a text anchor.

    Args:
        issues: LLM issues after span resolution and remapping.

    Returns:
        Filtered list with hallucinated issues removed.
    """
    validated: list[IssueResponse] = []
    for issue in issues:
        # Issue has a resolved span — keep it
        if issue.span and issue.span != [0, 0] and issue.span != [-1, -1]:
            validated.append(issue)
            continue
        # Document-level issue without flagged text — keep it
        if not issue.flagged_text:
            validated.append(issue)
            continue
        # Span is [0,0] and flagged_text is set — hallucinated
        logger.info(
            "Dropped hallucinated LLM issue: flagged_text=%r not in source",
            issue.flagged_text[:80],
        )
    return validated


def _strip_backtick_suggestions(
    issues: list[IssueResponse],
    original_text: str,
) -> list[IssueResponse]:
    """Strip redundant backticks from LLM suggestions on already-backticked text.

    When the LLM flags text that is already inside backtick-delimited inline
    code in the original source (e.g., ``\u0060ostree\u0060``), suggestions like
    ``\u0060OSTree\u0060`` would produce double backticks on accept.

    This function:
    - Drops false-positive issues whose only suggestion is to add backtick
      formatting to text that already has it.
    - Strips the outer backticks from suggestions when the flagged text is
      already inside backticks (keeping the content change, e.g., casing fix).

    Args:
        issues: Validated LLM issues with resolved spans.
        original_text: The original (un-cleaned) document text.

    Returns:
        Filtered list with backtick-safe suggestions.
    """
    if not original_text:
        return issues

    filtered: list[IssueResponse] = []
    for issue in issues:
        s, e = issue.span[0], issue.span[1]

        # Check if the flagged text is surrounded by backticks
        if not (s > 0 and e < len(original_text)
                and original_text[s - 1] == '`'
                and original_text[e] == '`'):
            filtered.append(issue)
            continue

        # The flagged text is already inside backticks.
        flagged = issue.flagged_text or ""
        new_suggestions: list[str] = []
        all_redundant = True

        for sug in (issue.suggestions or []):
            stripped = sug.strip()
            # Suggestion is just the flagged text with backticks → redundant
            if stripped == f"`{flagged}`":
                continue
            # Suggestion has outer backticks → strip them
            if (stripped.startswith('`') and stripped.endswith('`')
                    and len(stripped) > 2):
                new_suggestions.append(stripped[1:-1])
                all_redundant = False
            else:
                new_suggestions.append(sug)
                all_redundant = False

        if all_redundant and not new_suggestions:
            # All suggestions just added backticks to already-backticked text.
            # This is a false positive — drop the issue.
            logger.debug(
                "Dropped LLM false positive: '%s' already backticked at [%d,%d]",
                flagged, s, e,
            )
            continue

        issue.suggestions = new_suggestions
        filtered.append(issue)

    return filtered


# Mapping from LLM category values to rule_name strings that the
# frontend's TYPE_TO_GROUP map can resolve to proper style guide groups.
_LLM_CATEGORY_TO_RULE: dict[str, str] = {
    "style": "llm_style",
    "grammar": "llm_grammar",
    "punctuation": "llm_punctuation",
    "structure": "llm_structure",
    "audience": "llm_audience",
}


def _resolve_llm_rule_name(raw: dict[str, Any]) -> None:
    """Set rule_name for an LLM issue based on its category.

    Maps LLM categories (style, grammar, punctuation, audience) to
    dedicated rule names (llm_style, llm_grammar, etc.) so the frontend
    can assign them to proper IBM Style Guide groups.

    Args:
        raw: Mutable LLM result dict — modified in place.
    """
    if not raw.get("rule_name"):
        category = raw.get("category", "style")
        raw["rule_name"] = _LLM_CATEGORY_TO_RULE.get(category, "llm_style")


def _resolve_via_sentence_context(
    issue: IssueResponse,
    text: str,
    text_lower: str,
    flagged: str,
    flagged_lower: str,
) -> Optional[list[int]]:
    """Find flagged_text within its containing sentence in the source text.

    Searches for the sentence first, then locates flagged_text within it.

    Args:
        issue: The LLM issue containing sentence context.
        text: Original source text.
        text_lower: Lowercased source text.
        flagged: The flagged text to locate.
        flagged_lower: Lowercased flagged text.

    Returns:
        A [start, end] span if found, or None.
    """
    if not issue.sentence:
        return None
    sent_idx = text.find(issue.sentence)
    if sent_idx < 0:
        sent_idx = text_lower.find(issue.sentence.lower())
    if sent_idx < 0:
        return None
    sub_idx = issue.sentence.find(flagged)
    if sub_idx < 0:
        sub_idx = issue.sentence.lower().find(flagged_lower)
    if sub_idx < 0:
        return None
    start = sent_idx + sub_idx
    return [start, start + len(flagged)]


def _resolve_llm_span(issue: IssueResponse, text: str) -> None:
    """Compute character span for an LLM issue by text search.

    Finds the ``flagged_text`` in the original text and sets the span
    to [start, end].  Uses three strategies: exact match, case-insensitive
    match, and sentence-context search.

    Args:
        issue: IssueResponse to update — modified in place.
        text: The original text to search in.
    """
    if not text or not issue.flagged_text:
        return
    if issue.span != [0, 0]:
        return

    flagged = issue.flagged_text
    logger.debug(
        "_resolve_llm_span: rule=%s flagged=%r (len=%d) text_len=%d",
        issue.rule_name, flagged[:80], len(flagged), len(text),
    )

    # Strategy 1: exact substring match
    idx = text.find(flagged)
    if idx >= 0:
        issue.span = [idx, idx + len(flagged)]
        return

    # Strategy 2: case-insensitive match (LLMs sometimes alter casing)
    text_lower = text.lower()
    flagged_lower = flagged.lower()
    idx = text_lower.find(flagged_lower)
    if idx >= 0:
        issue.span = [idx, idx + len(flagged)]
        return

    # Strategy 3: stripped/collapsed whitespace match
    flagged_collapsed = " ".join(flagged.split())
    if flagged_collapsed != flagged:
        idx = text.find(flagged_collapsed)
        if idx >= 0:
            issue.span = [idx, idx + len(flagged_collapsed)]
            return

    # Strategy 4: sentence-context search
    span = _resolve_via_sentence_context(issue, text, text_lower, flagged, flagged_lower)
    if span:
        issue.span = span
        return

    # Strategy 5: strip Markdown formatting from flagged text (lite-markers
    # prefix + inline backticks/bold) and search with inline-marker tolerance
    # in original text.  Handles LLM copying Markdown formatting from the
    # lite-markers format that doesn't exist in the original AsciiDoc.
    cleaned_flagged = _strip_lite_markers(flagged)
    cleaned_flagged = _strip_markdown_inline(cleaned_flagged)
    if cleaned_flagged != flagged and len(cleaned_flagged) >= 5:
        idx = text.find(cleaned_flagged)
        if idx >= 0:
            issue.span = [idx, idx + len(cleaned_flagged)]
            return
        s, e = _find_ignoring_inline_markers(text, cleaned_flagged)
        if s >= 0:
            issue.span = [s, e]
            return

    # Strategy 6: fuzzy anchor — LLM may return slightly altered text
    _resolve_llm_span_fuzzy(issue, text)


# Minimum similarity ratio for fuzzy anchor matching (SK-11).
# Raised from 0.75 to 0.85 to prevent false matches on short strings
# (e.g. "apply" matching "apple" at ~80%).
_FUZZY_MATCH_THRESHOLD = 0.85


def _resolve_llm_span_fuzzy(
    issue: IssueResponse, text: str,
) -> None:
    """Find an approximate match for flagged_text using SequenceMatcher.

    Slides a window across the source text at multiple length variants
    (``len(flagged) ± 2``), scoring each window with
    ``SequenceMatcher.ratio()``.  The best match above
    ``_FUZZY_MATCH_THRESHOLD`` wins.

    Length variants handle the common case where the LLM corrected a
    typo by adding or removing a character (e.g., source ``"utilizess"``
    [9 chars] but LLM reports ``"utilizes"`` [8 chars]).

    Only triggered after all exact strategies have failed, so this
    handles LLM-altered whitespace, minor word reordering, or
    punctuation differences.

    Args:
        issue: IssueResponse to update — modified in place.
        text: The source text to search in.
    """
    flagged = issue.flagged_text
    if not flagged or len(flagged) < 8:
        return

    best_ratio = 0.0
    best_start = -1
    best_window = 0

    # Slide in steps for performance — step of 1 char would be slow
    step = max(1, len(flagged) // 4)

    for delta in (-2, -1, 0, 1, 2):
        window = len(flagged) + delta
        if window < 4:
            continue

        for start in range(0, len(text) - window + 1, step):
            candidate = text[start:start + window]
            ratio = SequenceMatcher(None, flagged, candidate).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_start = start
                best_window = window

    if best_ratio >= _FUZZY_MATCH_THRESHOLD and best_start >= 0:
        issue.span = [best_start, best_start + best_window]
        logger.debug(
            "Fuzzy anchor matched at [%d,%d] ratio=%.2f for %r",
            best_start, best_start + best_window, best_ratio, flagged[:60],
        )


def _remap_issues_to_original(
    issues: list[IssueResponse],
    offset_map: list[int],
    original_text: str,
) -> None:
    """Remap issue spans from cleaned-text to original-text coordinates.

    Uses the preprocessor offset map for approximate positioning, then
    refines with a proximity-based text search to find the exact
    ``flagged_text`` location in the original text. This handles cases
    where markup stripping shifts character positions.

    Modifies issues in place.

    Args:
        issues: List of issues with spans in cleaned-text coordinates.
        offset_map: Character-level mapping from cleaned to original positions.
        original_text: The whitespace-normalized but uncleaned text.
    """
    if not offset_map or not original_text:
        return

    map_len = len(offset_map)
    orig_len = len(original_text)

    for issue in issues:
        _remap_single_issue(issue, offset_map, original_text, map_len, orig_len)


# Regexes to strip Markdown markers added by lite_markers format.
_LITE_HEADING_RE = re.compile(r'^#{1,6}\s+')
_LITE_LIST_RE = re.compile(r'^(?:\d+\.\s+|-\s+|\*\s+)')
_LITE_BLOCKQUOTE_RE = re.compile(r'^>\s*(?:\*\*\w+:\*\*\s*)?')

# Characters treated as inline markers to skip during tolerant search.
_INLINE_MARKERS = frozenset({'*', '`'})


def _strip_lite_markers(text: str) -> str:
    """Strip Markdown formatting markers from lite-markers flagged text.

    The LLM may include prefixes copied from the lite-markers Markdown
    format (headings, list markers, blockquote markers).  These don't
    exist in the original AsciiDoc so they must be removed before
    searching in the original text.

    Args:
        text: Flagged text that may start with Markdown markers.

    Returns:
        Text with leading markers removed.
    """
    text = _LITE_HEADING_RE.sub('', text)
    text = _LITE_LIST_RE.sub('', text)
    text = _LITE_BLOCKQUOTE_RE.sub('', text)
    return text


_MARKDOWN_INLINE_RE = re.compile(r'\*\*|`')


def _strip_markdown_inline(text: str) -> str:
    """Remove Markdown inline formatting markers from text.

    Strips ``**`` (bold) and single backtick (code) markers that the
    LLM copies from the lite-markers Markdown representation.  These
    don't exist in the original AsciiDoc and prevent span resolution.

    Args:
        text: Text that may contain Markdown inline markers.

    Returns:
        Text with inline markers removed.
    """
    return _MARKDOWN_INLINE_RE.sub('', text)


def _find_ignoring_inline_markers(
    text: str, target: str,
) -> tuple[int, int]:
    """Find *target* in *text*, skipping ``**`` and backtick markers.

    Builds a marker-stripped copy of *text* with a position map back
    to the original, then searches for *target* in the stripped copy.

    Args:
        text: The region of original text to search in (may contain
            inline formatting markers like ``**bold**``).
        target: The clean text to find (without markers).

    Returns:
        ``(start, end)`` positions in the original *text*, or
        ``(-1, -1)`` if not found.
    """
    stripped_chars: list[str] = []
    pos_map: list[int] = []
    i = 0
    while i < len(text):
        # Skip ** (bold marker — two consecutive asterisks)
        if i + 1 < len(text) and text[i] == '*' and text[i + 1] == '*':
            i += 2
            continue
        # Skip single backtick (inline code marker)
        if text[i] == '`':
            i += 1
            continue
        stripped_chars.append(text[i])
        pos_map.append(i)
        i += 1

    stripped = ''.join(stripped_chars)
    idx = stripped.find(target)
    if idx < 0:
        return -1, -1

    start = pos_map[idx]
    end_idx = idx + len(target) - 1
    end = pos_map[end_idx] + 1 if end_idx < len(pos_map) else len(text)
    return start, end


def _find_flagged_in_text(
    text: str,
    flagged: str,
    search_from: int = 0,
    search_to: int | None = None,
) -> tuple[int, int, str] | None:
    """Search for flagged text in a region using multiple strategies.

    Tries in order: exact match, case-insensitive match, heading-marker
    stripped match, and inline-marker-tolerant match.

    Args:
        text: The text to search in.
        flagged: The flagged text to find.
        search_from: Start of the search region.
        search_to: End of the search region (default: end of text).

    Returns:
        Tuple of ``(start, end, matched_text)`` or ``None`` if not found.
    """
    if search_to is None:
        search_to = len(text)

    # Strategy 1: exact substring match
    idx = text.find(flagged, search_from, search_to)
    if idx >= 0:
        return idx, idx + len(flagged), flagged

    # Strategy 2: case-insensitive match
    region = text[search_from:search_to]
    idx_lower = region.lower().find(flagged.lower())
    if idx_lower >= 0:
        actual = search_from + idx_lower
        return actual, actual + len(flagged), text[actual:actual + len(flagged)]

    # Strategy 3: strip Markdown markers from lite-markers format
    stripped = _strip_lite_markers(flagged)
    if stripped != flagged:
        idx = text.find(stripped, search_from, search_to)
        if idx >= 0:
            return idx, idx + len(stripped), stripped

    # Strategy 4: tolerate inline markers (**, `) in both text and target.
    # LLM flagged text may have Markdown backticks/bold from lite-markers
    # while the original text has AsciiDoc formatting. Strip both.
    cleaned_target = _strip_markdown_inline(_strip_lite_markers(flagged))
    s, e = _find_ignoring_inline_markers(region, cleaned_target)
    if s >= 0:
        actual_s = search_from + s
        actual_e = search_from + e
        return actual_s, actual_e, text[actual_s:actual_e]

    return None


def _remap_single_issue(
    issue: IssueResponse,
    offset_map: list[int],
    original_text: str,
    map_len: int,
    orig_len: int,
) -> None:
    """Remap a single issue's span to original-text coordinates.

    Strategy:
      1. Map the span start via offset_map to get an approximate position.
      2. Search for ``flagged_text`` near that position in the original text.
      3. If found, use the exact match position.
      4. Fall back to direct offset_map translation if text search fails.

    Args:
        issue: IssueResponse to update — modified in place.
        offset_map: Character-level mapping from cleaned to original positions.
        original_text: The uncleaned text to search in.
        map_len: Length of offset_map.
        orig_len: Length of original_text.
    """
    span = issue.span
    flagged = issue.flagged_text or ""

    logger.debug(
        "_remap rule=%s: input span=%s flagged=%r",
        issue.rule_name, span, flagged[:60] if flagged else "",
    )

    if not span or span == [0, 0]:
        _remap_unresolved_span(issue, original_text, flagged)
        return

    start, end = span[0], span[1]
    orig_start = offset_map[min(start, map_len - 1)]
    logger.debug(
        "_remap: cleaned span=[%d,%d] -> orig_start=%d",
        start, end, orig_start,
    )

    if not flagged:
        orig_end = offset_map[min(end, map_len - 1)]
        issue.span = [min(orig_start, orig_len), min(max(orig_end, orig_start + 1), orig_len)]
        return

    # Search for flagged_text near the remapped position in original text.
    # Wide window accounts for offset drift from placeholder substitutions.
    search_from = max(0, orig_start - len(flagged) * 3 - 200)
    search_to = min(orig_len, orig_start + len(flagged) * 3 + 200)

    result = _find_flagged_in_text(original_text, flagged, search_from, search_to)
    if result:
        issue.span = [result[0], result[1]]
        issue.flagged_text = result[2]
        logger.debug("_remap: match -> span=%s", issue.span)
        return

    # Fallback: search entire document for issues that drifted far
    result = _find_flagged_in_text(original_text, flagged, 0, orig_len)
    if result:
        issue.span = [result[0], result[1]]
        issue.flagged_text = result[2]
        logger.debug("_remap: global fallback match -> span=%s", issue.span)
        return

    # Mark as failed remap — will be filtered out downstream
    logger.debug(
        "_remap: ALL searches FAILED for %r in window [%d,%d], "
        "original_text[%d:%d]=%r",
        flagged[:60], search_from, search_to,
        search_from, min(search_to, search_from + 100),
        original_text[search_from:search_from + 100],
    )
    issue.span = [-1, -1]


def _remap_unresolved_span(
    issue: IssueResponse,
    original_text: str,
    flagged: str,
) -> None:
    """Search for flagged_text in the full original text for unresolved spans.

    Called when the issue has a ``[0, 0]`` span (no position from analysis).

    Args:
        issue: IssueResponse to update — modified in place.
        original_text: The uncleaned source text to search in.
        flagged: The flagged text to locate.
    """
    if not flagged:
        return

    result = _find_flagged_in_text(original_text, flagged)
    if result:
        issue.span = [result[0], result[1]]
        issue.flagged_text = result[2]
        logger.debug("_remap: [0,0] -> span=%s", issue.span)
    else:
        logger.debug("_remap: [0,0] FAILED for %r", flagged[:60])


def _build_report(
    prep: dict[str, Any],
    score: ScoreResponse,
) -> ReportResponse:
    """Build a statistical report from preprocessed data and scoring.

    Args:
        prep: Preprocessed text data.
        score: Calculated score response.

    Returns:
        ReportResponse with document statistics and breakdowns.
    """
    from app.services.reporting.llm_consumability import (
        calculate_llm_consumability,
    )
    from app.services.reporting.readability import calculate_readability

    readability = calculate_readability(prep["text"])

    llm_consumability = calculate_llm_consumability(
        blocks=prep.get("blocks", []),
        prep=prep,
        file_type=prep.get("file_type"),
        readability=readability,
    )

    word_count = prep["word_count"]
    minutes = max(1, word_count // 200)
    if minutes < 60:
        reading_time = f"{minutes} min"
    else:
        reading_time = f"{minutes // 60}h {minutes % 60}m"

    return ReportResponse(
        word_count=word_count,
        sentence_count=prep["sentence_count"],
        paragraph_count=prep["paragraph_count"],
        avg_words_per_sentence=prep["avg_words_per_sentence"],
        avg_syllables_per_word=prep["avg_syllables_per_word"],
        readability=readability,
        category_breakdown=dict(score.category_counts),
        compliance=dict(score.compliance),
        unique_words=prep.get("unique_words", 0),
        vocabulary_diversity=prep.get("vocabulary_diversity", 0.0),
        estimated_reading_time=reading_time,
        llm_consumability=llm_consumability,
    )


def _is_cancelled(session_id: str) -> bool:
    """Check whether an analysis session has been superseded.

    Args:
        session_id: The session identifier to check.

    Returns:
        True if the session should be aborted.
    """
    try:
        store = _get_session_store()
        return not store.is_analysis_current(session_id)
    except (ImportError, AttributeError, TypeError):
        return False


def _store_session(session_id: str, response: AnalyzeResponse) -> None:
    """Store the analysis session in the session store.

    Uses the orchestrator's session_id to ensure consistency between
    WebSocket events, the HTTP response, and the session store.

    Args:
        session_id: The orchestrator-generated session identifier.
        response: The analysis response to store.
    """
    try:
        store = _get_session_store()
        store.store_session(session_id, response)
        logger.debug("Stored session %s with %d issues", session_id, len(response.issues))
    except (ImportError, AttributeError, TypeError, RuntimeError) as exc:
        logger.warning("Failed to store session %s: %s", session_id, exc)


def _update_stored_session(session_id: str, response: AnalyzeResponse) -> None:
    """Update the stored session with merged results after LLM phases.

    Args:
        session_id: The session identifier.
        response: The updated analysis response with merged issues.
    """
    try:
        store = _get_session_store()
        store.update_session_response(session_id, response)
        logger.debug("Updated session %s with %d issues", session_id, len(response.issues))
    except (ImportError, AttributeError, TypeError, RuntimeError) as exc:
        logger.warning("Failed to update session %s: %s", session_id, exc)


def _emit_progress(
    socket_sid: Optional[str],
    session_id: str,
    stage: str,
    message: str,
    percent: int,
) -> None:
    """Emit a progress event via Socket.IO if a session ID is provided.

    Args:
        socket_sid: Socket.IO session ID (None to skip emission).
        session_id: Analysis session identifier.
        stage: Current pipeline stage name.
        message: Human-readable progress message.
        percent: Completion percentage (0-100).
    """
    if socket_sid is None:
        return
    _emit_event(socket_sid, "progress_update", {
        "session_id": session_id,
        "step": stage,
        "status": "running",
        "detail": message,
        "progress": percent,
    })


def _emit_event(
    socket_sid: Optional[str], event: str, data: dict[str, Any]
) -> None:
    """Emit a named Socket.IO event to the session room or specific client.

    Prefers room-based emission using ``session_id`` from the data
    payload so that any client in the session room receives the event.
    Falls back to direct ``socket_sid`` targeting when no session_id
    is available.

    Args:
        socket_sid: Socket.IO session ID (fallback target).
        event: Event name to emit.
        data: Event payload dictionary.
    """
    target = data.get("session_id") or socket_sid
    if target is None:
        return
    try:
        from app.extensions import socketio as sio
        sio.emit(event, data, to=target)
    except (ImportError, AttributeError, RuntimeError) as exc:
        logger.debug("Socket.IO emit skipped for event '%s': %s", event, exc)

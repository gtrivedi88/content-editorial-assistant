"""Prompt templates for LLM analysis.

Provides three prompt builders for the Content Editorial Assistant:

1. **Granular** -- per-block style and grammar analysis.
2. **Global** -- full-document tone, flow, and minimalism checks.
3. **Suggestion** -- rewrite suggestions for individual flagged spans.

Each function returns a ``(system_prompt, user_prompt)`` tuple.
The system prompt contains invariant instructions (role, constraints,
response format); the user prompt carries the variable data (text,
excerpts, content type).  Separating them enables provider-side
prompt caching and reduces per-call token overhead.

Usage:
    from app.llm.prompts import build_granular_prompt

    system_prompt, user_prompt = build_granular_prompt(
        text, sentences, excerpts,
    )
"""

import json
import logging
import os
from typing import Optional

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Multi-shot example database (lazy-loaded from multishot_examples.yaml)
# ---------------------------------------------------------------------------

_EXAMPLES_DB: dict = {}

# Maps deterministic rule_name to multishot_examples.yaml category key
_RULE_TO_EXAMPLE_KEY: dict[str, str] = {
    "verbs": "passive_voice",
    "passive_voice": "passive_voice",
    "contractions": "contractions",
    "claims": "legal_claims",
    "legal_claims": "legal_claims",
    "headings": "headings",
    "citations": "citations",
    "spacing": "spacing",
    "currency": "currency",
    "word_usage_y": "word_usage_y",
    "technical_files_directories": "technical_files_directories",
}


def _load_examples() -> dict:
    """Load multi-shot examples on first use (lazy singleton).

    Reads ``multishot_examples.yaml`` from the project root and caches
    the result in ``_EXAMPLES_DB``.  Returns an empty dict if the file
    is missing or malformed.

    Returns:
        Dict mapping category keys to lists of example dicts.
    """
    global _EXAMPLES_DB
    if _EXAMPLES_DB:
        return _EXAMPLES_DB
    examples_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "multishot_examples.yaml",
    )
    try:
        with open(examples_path, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        _EXAMPLES_DB = data.get("examples", {})
        # Store analysis examples under a reserved key
        analysis_ex = data.get("analysis_examples")
        if analysis_ex:
            _EXAMPLES_DB["__analysis__"] = analysis_ex
        # Store negative boundary examples under a reserved key
        neg_ex = data.get("negative_examples")
        if neg_ex:
            _EXAMPLES_DB["__negative__"] = neg_ex
        logger.info(
            "Loaded %d multi-shot example categories", len(_EXAMPLES_DB),
        )
    except FileNotFoundError:
        logger.debug("Multi-shot examples file not found at %s", examples_path)
    except yaml.YAMLError as exc:
        logger.warning("Could not parse multi-shot examples: %s", exc)
    return _EXAMPLES_DB


def _select_examples(rule_name: str, max_count: int = 3) -> list[dict]:
    """Select multi-shot examples for a rule, graduated by difficulty.

    Picks up to one example per difficulty level (simple, medium,
    complex), choosing the highest ``success_rate`` within each level.

    Args:
        rule_name: The deterministic rule identifier.
        max_count: Maximum number of examples to return.

    Returns:
        List of example dicts (may be empty).
    """
    db = _load_examples()
    key = _RULE_TO_EXAMPLE_KEY.get(rule_name, rule_name)
    examples = db.get(key, [])
    if not examples:
        return []

    by_difficulty: dict[str, list[dict]] = {}
    for ex in examples:
        by_difficulty.setdefault(
            ex.get("difficulty", "medium"), [],
        ).append(ex)

    selected: list[dict] = []
    for diff in ("simple", "medium", "complex"):
        candidates = by_difficulty.get(diff, [])
        if candidates and len(selected) < max_count:
            best = max(candidates, key=lambda x: x.get("success_rate", 0))
            selected.append(best)

    return selected


def _format_examples_section(rule_name: str) -> str:
    """Format multi-shot examples for injection into a suggestion prompt.

    Args:
        rule_name: The deterministic rule identifier.

    Returns:
        Formatted prompt section, or empty string if no examples match.
    """
    examples = _select_examples(rule_name)
    if not examples:
        return ""

    lines = ["## Examples\n\n"]
    for idx, ex in enumerate(examples, 1):
        lines.append(
            f"**Example {idx}** ({ex.get('difficulty', 'medium')}):\n"
            f"- Before: `{ex['before']}`\n"
            f"- After: `{ex['after']}`\n"
            f"- Reasoning: {ex.get('reasoning', '')}\n\n"
        )
    return "".join(lines)

def _format_analysis_examples(content_type: str) -> str:
    """Format few-shot analysis examples for a granular analysis prompt.

    Retrieves good-flag and bad-flag examples for the given content type
    from ``multishot_examples.yaml`` and formats them as a prompt section
    that teaches the LLM the boundary between real issues and false
    positives.

    Args:
        content_type: Modular documentation type (concept, procedure, etc.).

    Returns:
        Formatted prompt section, or empty string if no examples match.
    """
    db = _load_examples()
    analysis = db.get("__analysis__", {})
    type_examples = analysis.get(content_type, {})

    good = type_examples.get("good_flags", []) if type_examples else []
    bad = list(type_examples.get("bad_flags", [])) if type_examples else []

    # Inject boundary-defining negative examples for confidence calibration
    _append_negative_boundary_examples(bad, content_type)

    if not good and not bad:
        return ""

    lines = ["## Analysis Examples\n\n"]
    _append_good_flags(good, lines)
    _append_bad_flags(bad, lines)
    return "".join(lines)


def _append_good_flags(flags: list[dict], lines: list[str]) -> None:
    """Append formatted good-flag examples to *lines*.

    Args:
        flags: List of good-flag example dicts.
        lines: Accumulator for formatted lines (mutated).
    """
    for ex in flags[:2]:
        lines.append(
            f"**Flag this** (real issue):\n"
            f"- Text: `{ex.get('text', '')}`\n"
            f"- Issue: {ex.get('issue', '')}\n"
            f"- Suggestion: `{ex.get('suggestion', '')}`\n\n"
        )


def _append_bad_flags(flags: list[dict], lines: list[str]) -> None:
    """Append formatted bad-flag examples to *lines*.

    Renders up to 4 examples (2 original bad-flags + 2 injected
    negative boundary examples for confidence calibration).

    Args:
        flags: List of bad-flag example dicts.
        lines: Accumulator for formatted lines (mutated).
    """
    for ex in flags[:4]:
        lines.append(
            f"**Do NOT flag** (false positive):\n"
            f"- Text: `{ex.get('text', '')}`\n"
            f"- Reason: {ex.get('reason', '')}\n\n"
        )


# Map content types to relevant negative example categories
_NEGATIVE_EXAMPLE_CATEGORIES: dict[str, list[str]] = {
    "procedure": ["passive_voice_appropriate", "word_usage_contextual"],
    "concept": ["passive_voice_appropriate", "contractions_appropriate"],
    "reference": ["passive_voice_appropriate", "word_usage_contextual"],
    "release_notes": ["passive_voice_appropriate"],
}


def _append_negative_boundary_examples(
    bad_flags: list[dict], content_type: str,
) -> None:
    """Inject boundary-defining negative examples into bad_flags.

    Pulls from the root-level ``negative_examples`` section of
    ``multishot_examples.yaml`` to teach the LLM where rules do NOT
    apply, calibrating confidence scores on genuine violations.

    Args:
        bad_flags: List of bad-flag example dicts (mutated).
        content_type: Modular documentation type.
    """
    db = _load_examples()
    negatives = db.get("__negative__", {})
    if not negatives:
        return

    categories = _NEGATIVE_EXAMPLE_CATEGORIES.get(
        content_type, ["passive_voice_appropriate"],
    )

    for cat_key in categories:
        examples = negatives.get(cat_key, [])
        if examples:
            best = max(examples, key=lambda x: x.get("success_rate", 0))
            bad_flags.append({
                "text": best.get("before", ""),
                "reason": best.get("reasoning", "Acceptable — do not flag"),
            })


def build_granular_prompt(
    text: str,
    sentences: list[str],
    style_guide_excerpts: list[dict],
    content_type: str = "concept",
    acronym_context: dict[str, str] | None = None,
    document_outline: str | None = None,
) -> tuple[str, str]:
    """Build a per-block granular analysis prompt.

    Returns a ``(system_prompt, user_prompt)`` tuple.  The system
    prompt is invariant across blocks; the user prompt carries the
    variable content.

    Args:
        text: The text block to analyse.
        sentences: Individual sentences extracted from the block.
        style_guide_excerpts: Relevant style guide excerpts as dicts
            with ``guide_name``, ``category``, ``topic``, ``excerpt``.
        content_type: Modular documentation type (concept, procedure,
            reference, assembly, release_notes). Adjusts evaluation.
        acronym_context: Optional dict mapping acronyms to their
            expansions collected from the full document. Prevents
            false "undefined acronym" flags when a definition
            appears in a different block.
        document_outline: Optional compact outline of the full
            document's heading structure, giving the LLM section-level
            awareness for the block being analysed.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    excerpt_section = _format_excerpt_section(style_guide_excerpts)
    acronym_section = _format_acronym_section(acronym_context, text)
    examples_section = _format_analysis_examples(content_type)
    outline_section = _format_document_outline(document_outline)
    sentences_json = json.dumps(sentences, ensure_ascii=False)
    content_guidance = _content_type_guidance(content_type)

    system_prompt = (
        "# ROLE\n"
        "Technical documentation editor (IBM Style, Red Hat Supplementary, "
        "accessibility, modular docs). Analyze text for judgment-based "
        "editorial issues only.\n\n"
        "## IN SCOPE — CHECK these issues\n"
        "- Comma splices, run-on sentences, semicolons, colons\n"
        "- Unclear pronouns and complex sentence structure\n"
        "- Inconsistent tone\n"
        "- Wordiness — unnecessary words or phrases that can be simplified\n"
        "- Minimalism — excessive detail or background that does not help "
        "the reader complete the task\n"
        "- Anthropomorphism — attributing human actions to software/"
        "systems (e.g., 'the system wants' or 'the system applies')\n"
        "- Technical term formatting — specific commands, CLI utilities, "
        "file paths, directory names, configuration parameters, package "
        "names, environment variables, and code elements mentioned in "
        "prose should use backtick formatting (e.g., 'ostree' should be "
        "`ostree`, 'systemctl' should be `systemctl`). Do NOT flag "
        "general technical concepts or descriptive phrases (e.g., "
        "'kernel modules', 'system extensions', 'command line options' "
        "are prose concepts, not code). Do NOT flag text already "
        "wrapped in **bold** markers (e.g., **Edit**, **Apply**, "
        "**Routes**) — these are UI element names already formatted "
        "with bold per the source document\n"
        "- Future tense — use simple present tense instead of 'will' "
        "(e.g., 'the installation will fail' → 'the installation fails'; "
        "'will be used' → 'is used')\n"
        "- Official naming and capitalization — use the official project "
        "name capitalization (e.g., 'ostree' should be 'OSTree', "
        "'openshift' should be 'OpenShift')\n"
        "- Lead-in sentence case — definition list lead-ins after a colon "
        "should be lowercase (e.g., 'Where:' → 'where:' when following "
        "a sentence)\n\n"
        "## OUT OF SCOPE — SKIP (deterministic rules handle reliably)\n"
        "- Spelling errors\n"
        "- Product name casing for Red Hat product names specifically\n"
        "- Number formatting (numerals vs words)\n"
        "- List punctuation (trailing commas/semicolons)\n\n"
        "## OUT OF SCOPE — SKIP (standard technical writing)\n"
        "- 'placeholder' text\n"
        "- CLI tool names inside backticks\n"
        "- Text already between single backtick (`) markers in the input — "
        "this text is ALREADY code-formatted. NEVER suggest backtick "
        "formatting for text that already has backticks "
        "(e.g., `ostree` is already formatted, do not flag it)\n"
        "- Imperative verb at start of procedure steps\n"
        "- Technical jargon in appropriate context\n"
        "- Single-step procedures using a bullet instead of a numbered "
        "list — correct format per modular docs convention\n"
        "- List items starting with bare verbs — in technical documentation, "
        "bullet and definition list items commonly begin with present-tense "
        "verbs ('Provides', 'Prohibits', 'Includes', 'Built for') when the "
        "subject is implied by a heading or definition term above. Do NOT "
        "add subjects (e.g., 'The system provides') or restructure these "
        "items for parallelism — bare-verb list items are standard "
        "technical writing convention\n"
        "- Content inside triple-backtick code blocks — code examples "
        "are context, not prose to edit\n"
        "- Markdown structural markers (#, -, 1., >, **, `) — these are "
        "document formatting, not prose to edit\n"
        "- Text wrapped in **bold** markers — words like **Edit**, "
        "**Apply**, **Save** are UI element names (button labels, menu "
        "items, tab names) already formatted with bold. Do NOT suggest "
        "backtick formatting for these\n"
        "- Missing lead-in sentences for standard modular docs sections "
        "(Prerequisites, Verification, Troubleshooting, Additional resources) "
        "— these section headings are self-explanatory labels that do not "
        "require introductory text before their content\n\n"
        "## BIAS DIRECTIVE\n"
        "Flag all clear violations of the style guide rules provided. "
        "When a pattern clearly violates a rule, flag it regardless of "
        "severity — the scoring engine handles severity weighting. Only skip "
        "when the text is genuinely ambiguous or when an alternative reading "
        "makes the usage correct.\n\n"
        "## RESPONSE FORMAT\n"
        "Respond with a JSON object containing a \"reasoning\" string "
        "and an \"issues\" array.\n"
        "Keep the \"reasoning\" field concise — 2-3 sentences maximum. "
        "Prioritize the \"issues\" array over detailed reasoning.\n"
        "In \"reasoning\", briefly confirm which of the above IN SCOPE "
        "checks you applied and note any categories where you found "
        "no issues.\n"
        "Each object in the \"issues\" array:\n"
        '{"flagged_text":"exact span","message":"explanation",'
        '"suggestions":["corrected text"],"severity":"low|medium|high",'
        '"category":"style|grammar|punctuation|structure|audience",'
        '"sentence":"full sentence","sentence_index":0,"confidence":0.8}\n\n'
        "IMPORTANT: suggestions must contain at least one concrete "
        "replacement for the flagged_text. Provide the corrected version "
        "of the flagged span that fixes the issue. Do not leave "
        "suggestions empty. Keep suggestions scoped to the flagged_text "
        "span only — do not rewrite surrounding text.\n\n"
        "No issues → {\"reasoning\":\"...\",\"issues\":[]}. "
        "Return ONLY JSON, no additional text."
    )

    user_prompt = (
        f"## Document Type: {content_type}\n\n"
        f"{content_guidance}\n\n"
        f"{outline_section}"
        f"{excerpt_section}"
        f"{acronym_section}"
        f"{examples_section}"
        "## Text Block\n\n"
        f"```\n{text}\n```\n\n"
        "## Sentences\n\n"
        f"{sentences_json}"
    )

    return system_prompt, user_prompt


def build_global_prompt(
    full_text: str,
    content_type: str,
    style_guide_excerpts: list[dict],
    document_outline: str | None = None,
    abstract_context: str | None = None,
) -> tuple[str, str]:
    """Build a full-document global analysis prompt.

    Returns a ``(system_prompt, user_prompt)`` tuple.  Sends the full
    document text (or lite-markers Markdown) to leverage the LLM's
    large context window.

    Args:
        full_text: Complete document text (or lite-markers Markdown).
        content_type: Modular documentation type
            (concept/procedure/reference/assembly).
        style_guide_excerpts: Relevant style guide excerpts.
        document_outline: Optional document heading outline for
            structural awareness.
        abstract_context: Module abstract (first paragraph after heading)
            for targeted short-description quality evaluation.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    excerpt_section = _format_excerpt_section(style_guide_excerpts)
    outline_section = _format_document_outline(document_outline)

    system_prompt = (
        "# ROLE\n"
        "Technical documentation editor. Global document review.\n\n"
        "## IN SCOPE — CHECK these document-level issues ONLY\n"
        "Focus on cross-section, whole-document concerns that per-block "
        "analysis cannot detect:\n"
        "- Tone consistency — voice shifts between sections of the document\n"
        "- Audience level — inconsistent technical depth (beginner "
        "language next to expert-only jargon without explanation)\n"
        "- Accessibility — instructions that rely solely on visual cues "
        "(color, position, shape) with no text alternative\n"
        "- Short description quality — every module must have a short "
        "description (abstract) that includes both WHAT the user will do "
        "and WHY it is important or beneficial. Abstracts should be 2-3 "
        "sentences, use active voice, avoid self-referential language "
        "('This topic covers...'), and avoid feature-focused language "
        "('This product allows you to...'). Use customer-centric language "
        "('You can... by...' or 'To..., configure...')\n\n"
        "## OUT OF SCOPE — SKIP these\n"
        "- Step numbering in procedures — the rendering engine handles "
        "sequential numbering automatically; do not flag step order, "
        "restart, or numbering issues\n"
        "- Single-step procedures using a bullet instead of a numbered "
        "list — correct format per modular docs convention\n"
        "- Content inside triple-backtick code blocks — code examples "
        "are context, not prose to edit\n"
        "- Markdown structural markers (#, -, 1., >, **, `) — document "
        "formatting, not prose to edit\n"
        "- Text wrapped in **bold** markers — UI element names already "
        "formatted with bold, do not suggest backtick formatting\n"
        "- Missing lead-in sentences for standard modular docs sections "
        "(Prerequisites, Verification, Troubleshooting, Additional resources) "
        "— these section headings are self-explanatory labels that do not "
        "require introductory text before their content\n\n"
        "## RESPONSE FORMAT\n"
        "Respond with a JSON object containing a \"reasoning\" string "
        "and an \"issues\" array.\n"
        "Keep the \"reasoning\" field concise — 2-3 sentences maximum. "
        "Prioritize the \"issues\" array over detailed reasoning.\n"
        "In \"reasoning\", briefly note which document-level checks you "
        "applied and any areas with no issues.\n"
        "Each object in the \"issues\" array:\n"
        '{"flagged_text":"exact span","message":"explanation",'
        '"suggestions":["corrected text"],"severity":"low|medium|high",'
        '"category":"style|grammar|punctuation|structure|audience",'
        '"sentence":"passage","sentence_index":0,"confidence":0.8}\n\n'
        "IMPORTANT: suggestions must contain at least one concrete "
        "replacement for the flagged_text. Provide the corrected version "
        "of the flagged span that fixes the issue. Do not leave "
        "suggestions empty. Keep suggestions scoped to the flagged_text "
        "span only — do not rewrite surrounding text.\n\n"
        "No issues → {\"reasoning\":\"...\",\"issues\":[]}. "
        "Return ONLY JSON, no additional text."
    )

    user_prompt = (
        f"## Document Type: {content_type}\n\n"
        f"{outline_section}"
        f"{excerpt_section}"
        "## Document\n\n"
        f"```\n{full_text}\n```"
    )

    if abstract_context:
        user_prompt += (
            f"\n\n## Module Abstract (evaluate for short description quality)\n"
            f"{abstract_context}\n"
        )

    return system_prompt, user_prompt


def build_suggestion_prompt(
    flagged_text: str,
    context_sentences: list[str],
    rule_info: dict,
    style_guide_excerpt: dict,
    sentence: str = "",
) -> tuple[str, str]:
    """Build a rewrite suggestion prompt for a flagged text span.

    When ``sentence`` is provided and contains ``flagged_text``, the
    prompt embeds the flagged text within its containing sentence using
    ``\u27e8\u27e9`` markers.  This anchors the LLM to the exact word
    and prevents over-scoped rewrites.  Falls back to isolated code
    block format when sentence is unavailable.

    Args:
        flagged_text: The exact text span that was flagged.
        context_sentences: Sentences surrounding the flagged text.
        rule_info: Dict with ``rule_name``, ``category``, ``message``,
            ``severity`` describing the detected issue.
        style_guide_excerpt: Relevant style guide excerpt dict.
        sentence: The containing sentence (optional).

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    excerpt_section = _format_single_excerpt(style_guide_excerpt)
    context_json = json.dumps(context_sentences, ensure_ascii=False)

    rule_name = rule_info.get("rule_name", "unknown")
    category = rule_info.get("category", "style")
    message = rule_info.get("message", "")
    severity = rule_info.get("severity", "medium")
    examples_section = _format_examples_section(rule_name)

    system_prompt = (
        "Technical documentation editor. Rewrite ONLY the flagged text "
        "to fix the issue while preserving technical accuracy.\n\n"
        "Requirements: fix ONLY the identified issue; preserve technical "
        "terms, product names, code references; maintain same detail and "
        "meaning; keep sentence structure when possible; do not introduce "
        "new issues; do NOT rewrite surrounding sentences.\n\n"
        "## Style constraints for rewrites\n"
        "- Use active voice (not passive) unless the actor is irrelevant\n"
        "- Use present tense (not future 'will') for descriptions\n"
        "- Do not introduce self-referential language ('this section', "
        "'this topic', 'this document')\n"
        "- Preserve imperative voice in procedure steps — do not convert "
        "'Click X' to 'You should click X'\n\n"
        "Respond with a JSON object:\n"
        '{"rewritten_text":"corrected text",'
        '"explanation":"what changed and why",'
        '"confidence":0.9}\n\n'
        "Return ONLY JSON, no additional text."
    )

    # Build context section: embed flagged text in sentence when possible
    has_sentence = bool(sentence and flagged_text and flagged_text in sentence)
    if has_sentence:
        marked_sentence = sentence.replace(
            flagged_text,
            f"\u27e8{flagged_text}\u27e9",
            1,
        )
        context_section = (
            "## Context\n\n"
            "In the following sentence, the text between \u27e8\u27e9 "
            "markers has been flagged:\n\n"
            f'"{marked_sentence}"\n\n'
            "## Surrounding Sentences (for context only "
            "\u2014 do NOT rewrite these)\n\n"
            f"{context_json}\n\n"
        )
    else:
        context_section = (
            "## Flagged Text\n\n"
            f"```\n{flagged_text}\n```\n\n"
            "## Surrounding Context\n\n"
            f"{context_json}\n\n"
        )

    user_prompt = (
        "## Issue Details\n\n"
        f"- **Rule**: {rule_name}\n"
        f"- **Category**: {category}\n"
        f"- **Severity**: {severity}\n"
        f"- **Problem**: {message}\n\n"
        f"{context_section}"
        f"{excerpt_section}"
        f"{examples_section}"
    )

    return system_prompt, user_prompt


def build_judge_prompt(
    issues: list[dict],
    document_excerpt: str,
    content_type: str,
) -> tuple[str, str]:
    """Build a self-correction judge prompt for LLM issue review.

    The judge reviews a batch of LLM-generated issues and decides
    which to keep (real issue) and which to drop (false positive).

    Args:
        issues: List of issue dicts with ``flagged_text``, ``message``,
            ``category``, ``confidence`` keys.
        document_excerpt: A representative excerpt of the document
            for context.
        content_type: Modular documentation type.

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    issues_json = json.dumps(issues, ensure_ascii=False, indent=2)

    system_prompt = (
        "You are reviewing editorial flags generated by an AI editor "
        "for technical documentation. For each flag, decide: KEEP "
        "(real issue worth fixing) or DROP (false positive).\n\n"
        "## DROP criteria (false positive)\n"
        "- Flagged text is standard technical writing for the document type\n"
        "- Suggestion would change technical meaning\n"
        "- Issue is subjective preference, not a style guide rule\n"
        "- Flagged text is inside a code reference, CLI command, or "
        "configuration parameter\n"
        "- State-of-being constructions flagged as passive voice "
        "(e.g., 'is configured', 'is installed', 'is stored')\n"
        "- Imperative verbs at procedure step starts flagged as "
        "incomplete sentences\n"
        "- Text wrapped in bold or backtick formatting flagged for "
        "additional formatting\n"
        "- UI element names (button labels, menu items) flagged for "
        "backtick formatting when already bold\n\n"
        "## KEEP criteria (real issue)\n"
        "- Clearly supported by IBM Style Guide or Red Hat "
        "Supplementary Style Guide\n"
        "- Fix improves clarity without changing technical meaning\n"
        "- Real grammar or punctuation error\n"
        "- Future tense ('will fail') where present tense works\n"
        "- Anthropomorphism ('the system wants', 'the tool tries')\n"
        "- Wordiness that can be cut without losing information\n"
        "- Unofficial capitalization of known project names\n\n"
        f"## Document type: {content_type}\n"
        + _judge_content_type_note(content_type)
        + "\n\n"
        "Respond with a JSON object:\n"
        '{"keep": [0, 2, 4], "drop": [1, 3]}\n\n'
        "Indices refer to the issues array (0-based). Return ONLY JSON."
    )

    user_prompt = (
        f"## Document Type: {content_type}\n\n"
        "## Document Excerpt\n\n"
        f"```\n{document_excerpt[:2000]}\n```\n\n"
        "## Issues to Review\n\n"
        f"{issues_json}"
    )

    return system_prompt, user_prompt


def _judge_content_type_note(content_type: str) -> str:
    """Return content-type-specific guidance for the judge prompt.

    Helps the judge make accurate keep/drop decisions based on the
    norms of the document type being reviewed.

    Args:
        content_type: Modular documentation type.

    Returns:
        Guidance string, or empty string for unknown types.
    """
    notes = {
        "procedure": (
            "Procedure: imperative voice and short fragments are correct. "
            "Passive voice in state-of-being patterns is acceptable. "
            "Do not drop issues about future tense or wordiness."
        ),
        "concept": (
            "Concept: explanatory prose. Passive voice for state-of-being "
            "is acceptable. Anthropomorphism and wordiness are real issues."
        ),
        "reference": (
            "Reference: terse factual descriptions. Sentence fragments "
            "and passive voice are expected. Drop issues about brevity."
        ),
        "release_notes": (
            "Release notes: past tense passive is standard. "
            "Drop passive voice flags. Keep first-person flags."
        ),
    }
    return notes.get(content_type, "")


# ------------------------------------------------------------------
# Private helpers
# ------------------------------------------------------------------


def _content_type_guidance(content_type: str) -> str:
    """Return content-type-specific editorial guidance.

    Different modular documentation types have different style norms.
    A procedure uses imperative voice and short sentences by design;
    a concept uses more explanatory prose. Release notes allow past
    passive constructions that would be flagged in other doc types.

    Args:
        content_type: Modular documentation type.

    Returns:
        Guidance string for inclusion in the prompt.
    """
    guidance_map = {
        "procedure": (
            "This is a **procedure** module — task-oriented with steps.\n"
            "- Imperative voice ('Click', 'Run', 'Enter') is correct and expected.\n"
            "- Single-step procedures use a bullet (not a numbered list) by convention.\n"
            "- Prerequisites and verification sections are standard structure.\n"
            "- 'the user' is acceptable when referring to a role, not the reader.\n"
            "- DO FLAG: single-step procedures that use a numbered list (1.) instead "
            "of an unnumbered bullet — Red Hat guidelines require a bullet for "
            "single-step procedures.\n"
            "- DO FLAG: anthropomorphism ('the system does X'), unclear instructions, "
            "modal hedging ('You can X', 'You may X') — rewrite as direct imperative ('X').\n"
            "- DO FLAG: procedure abstracts that lead with the action instead of the "
            "goal. The opening sentence should state WHY the user needs this task "
            "before HOW to do it. Preferred: 'To [achieve goal], [perform action]' "
            "(goal-first). Flag: '[perform action] to [achieve goal]' (action-first). "
            "Example: write 'To share the /var/lib/containers partition between "
            "stateroots, apply a MachineConfig...' not 'Apply a MachineConfig to "
            "share the /var/lib/containers partition...'. (Red Hat SSG)\n"
            "- DO FLAG: definition lists after 'Where:' where variable descriptions "
            "start with 'Specify' instead of 'Specifies' (Red Hat SSG requires "
            "'Specifies' for variable descriptions).\n"
            "- DO FLAG: procedures, procedure word, or steps inside admonitions (NOTE, IMPORTANT, "
            "WARNING) — Red Hat guidance prohibits procedural content inside "
            "admonitions; move it to the main procedure body.\n"
            "- DO NOT flag: imperative voice, formal terminology in CLI instructions, "
            "short direct sentences in steps."
        ),
        "concept": (
            "This is a **concept** module — explanatory content.\n"
            "- Passive voice is acceptable when the actor is irrelevant.\n"
            "- State-of-being ('is deployed', 'is stored') is NOT passive voice.\n"
            "- Longer explanatory sentences (25-35 words) are acceptable if clear.\n"
            "- Technical terms ('implement', 'leverage', 'scalable') are precise, not jargon.\n"
            "- Focus on: wordiness, unclear explanations, inconsistent terminology."
        ),
        "reference": (
            "This is a **reference** module — structured lookup material.\n"
            "- Terse, factual descriptions are expected.\n"
            "- Passive constructions are common and acceptable.\n"
            "- Formal language is appropriate (do NOT flag 'utilize', 'facilitate').\n"
            "- 'the user' refers to a system role, not the reader.\n"
            "- Focus on: completeness, consistency, unclear descriptions."
        ),
        "release_notes": (
            "This is a **release notes** document.\n"
            "- Past tense passive is acceptable ('was fixed', 'was added', 'was removed').\n"
            "- 'the user' refers to end users of the software, not the reader.\n"
            "- Focus on: clarity of change descriptions, completeness."
        ),
        "assembly": (
            "This is an **assembly** module — includes other modules.\n"
            "- Introductory text should provide context for the included content.\n"
            "- Focus on: coherence between sections, clear transitions."
        ),
    }
    return guidance_map.get(content_type, guidance_map["concept"])


def _format_document_outline(outline: str | None) -> str:
    """Format a document outline section for inclusion in a prompt.

    The outline gives the LLM awareness of the overall document
    structure (section headings and hierarchy) so it can evaluate
    the current block in context.

    Args:
        outline: Pre-formatted outline string, or None.

    Returns:
        Formatted prompt section, or empty string if no outline.
    """
    if not outline:
        return ""
    return f"## Document Outline\n\n{outline}\n\n"


def _format_acronym_section(
    acronym_context: dict[str, str] | None,
    block_text: str,
) -> str:
    """Format known acronym definitions for injection into a prompt.

    Only includes acronyms that actually appear in the current block
    to keep the prompt focused and avoid wasting tokens.

    Args:
        acronym_context: Full dict of acronym expansions collected from
            the document, or None.
        block_text: The text of the current block being analysed.

    Returns:
        Formatted prompt section, or empty string if no relevant
        acronyms are found.
    """
    if not acronym_context:
        return ""

    relevant: dict[str, str] = {}
    upper_text = block_text.upper()
    for abbrev, expansion in acronym_context.items():
        if abbrev in upper_text:
            relevant[abbrev] = expansion

    if not relevant:
        return ""

    lines = ["## Known Acronym Definitions\n\n"]
    for abbrev, expansion in sorted(relevant.items()):
        lines.append(f"- {abbrev} = {expansion}\n")
    lines.append(
        "\nDo NOT flag these acronyms as undefined.\n\n",
    )
    return "".join(lines)


def _format_excerpt_section(excerpts: list[dict]) -> str:
    """Format style guide excerpts into a prompt section.

    Args:
        excerpts: List of excerpt dicts with ``guide_name``,
            ``category``, ``topic``, and ``excerpt`` keys.

    Returns:
        Formatted string for inclusion in a prompt, or empty string
        if no excerpts are provided.
    """
    if not excerpts:
        return ""

    lines = ["## Style Guide Context\n\n"]
    for item in excerpts:
        guide = item.get("guide_name", "Style Guide")
        topic = item.get("topic", "General")
        excerpt_text = item.get("excerpt", "")
        if not excerpt_text:
            continue
        lines.append(f"### {guide} -- {topic}\n\n{excerpt_text}\n\n")

    # Return empty if all excerpts were blank
    if len(lines) <= 1:
        return ""

    return "".join(lines)


def _format_single_excerpt(excerpt: dict) -> str:
    """Format a single style guide excerpt for a suggestion prompt.

    Args:
        excerpt: Dict with ``guide_name``, ``topic``, ``excerpt``.

    Returns:
        Formatted string, or empty string if the excerpt is empty.
    """
    if not excerpt:
        return ""

    guide = excerpt.get("guide_name", "Style Guide")
    topic = excerpt.get("topic", "General")
    text = excerpt.get("excerpt", "")

    if not text:
        return ""

    return (
        "## Style Guide Reference\n\n"
        f"**{guide} -- {topic}**\n\n"
        f"{text}\n\n"
    )



# Plan: Detection + UI + Rule Coverage + HTML Parser + LLM Span Fixes (Parts A-F)

## Context

Multi-session improvement plan for CEA. Parts A-E are DONE. Part F fixes three bugs discovered during HTML paste testing: LLM span misplacement, sentence replacement fallback, and suggestion content filtering.

---

## Parts A-E — DONE

- **A1-A5**: Detection rate improvements (reasoning wrapper, confidence 0.70, Judge enabled, truncation recovery, negative examples)
- **B1-B2**: UI fixes (instruction detection, sentence replacement)
- **C1-C2**: Rule coverage expansion (accessibility + 22 rules to list/dlist/admonition block types)
- **D1-D9**: HTML parser multi-block fix (container recursion, typed list items, bold/code markers, tests)
- **E1-E2**: LanguageTool sidecar hardening (skip rules, redundancy patterns)

---

## Part F: LLM Issue Span + Suggestion Bugs (TO DO)

Three bugs found during real-world HTML paste testing with a Red Hat procedure page.

### Bug Description

When the LLM flags the word "using" in a bullet item ("Configuring a network bond by **using** the RHEL web console"), the highlight lands on the first occurrence of "using" in the introductory paragraph instead ("manage network settings **using** a web browser-based interface"). The suggestion "settings by using" confirms the issue was meant for the paragraph, not the bullet. Three independent failures compound:

1. **Bug 5 (Span Misplacement)**: `_resolve_llm_span` uses `text.find(flagged)` as Strategy 1, grabbing the first document-wide occurrence of common words instead of anchoring to the LLM-provided sentence context.
2. **Bug 4 (Sentence Stuffed into Mark)**: When `_replaceSentence` fails (LLM hallucinated a comma so DOM match fails), the fallback at line 281 blindly shoves a 25-word sentence into a 1-word `<mark>` tag.
3. **Bug 2/3 (Chatty Suggestion as Replacement)**: `_normalize_issue_fields` in parser.py does zero content filtering on suggestions. The `_autoFetchSuggestion` path bypasses `extractReplacement` entirely, putting raw LLM output directly into the chip.

---

### F1. Promote sentence-context to Strategy 1 in `_resolve_llm_span`

**File**: `app/services/analysis/orchestrator.py` (line 2216)

**Root cause**: `text.find(flagged)` at line 2239 is Strategy 1. For the word "using" it finds position 45 (intro paragraph) instead of position 312 (bullet item). The LLM provides `issue.sentence` specifically for disambiguation, but sentence-context search is Strategy 4 — it never runs because Strategy 1 already matched.

**Fix**: Reorder strategies. When `issue.sentence` is available, try sentence-context first. Fall back to `text.find` only if sentence-context fails (e.g., sentence drift from editing).

```python
def _resolve_llm_span(issue: IssueResponse, text: str) -> None:
    if not text or not issue.flagged_text:
        return
    if issue.span != [0, 0]:
        return

    flagged = issue.flagged_text
    text_lower = text.lower()
    flagged_lower = flagged.lower()

    # Strategy 1: sentence-context search (highest accuracy for disambiguation)
    # The LLM provides issue.sentence specifically to anchor flagged_text
    # to the correct occurrence. Always try this first.
    span = _resolve_via_sentence_context(
        issue, text, text_lower, flagged, flagged_lower,
    )
    if span:
        issue.span = span
        return

    # Strategy 2: exact substring match (only first-match, OK when
    # sentence context is unavailable or sentence itself drifted)
    idx = text.find(flagged)
    if idx >= 0:
        issue.span = [idx, idx + len(flagged)]
        return

    # Strategy 3: case-insensitive match
    idx = text_lower.find(flagged_lower)
    if idx >= 0:
        issue.span = [idx, idx + len(flagged)]
        return

    # Strategy 4: collapsed whitespace match
    flagged_collapsed = " ".join(flagged.split())
    if flagged_collapsed != flagged:
        idx = text.find(flagged_collapsed)
        if idx >= 0:
            issue.span = [idx, idx + len(flagged_collapsed)]
            return

    # Strategy 5: strip Markdown formatting
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

    # Strategy 6: fuzzy anchor
    _resolve_llm_span_fuzzy(issue, text)
```

**Key change**: `text_lower` and `flagged_lower` are computed once at the top (before they're needed by any strategy), and sentence-context moves from Strategy 4 to Strategy 1. The debug log statement is preserved at the start.

---

### F2. Hard abort on failed sentence replacement

**File**: `static/js/editor/underline-renderer.js` (line 249)

**Root cause**: Lines 259-261 try `_replaceSentence`. If it returns `false` (DOM sentence match fails), code falls through to line 281: `mark.textContent = text` — which shoves a full sentence into a 1-word mark, destroying surrounding text.

**Fix**: When `isSentenceRewrite` is true AND `_replaceSentence` returns false, `return` immediately instead of falling through to the simple replacement path. Log a warning for debugging.

```javascript
export function replaceUnderlineText(editorEl, errorId, newText, sentence) {
    const mark = editorEl.querySelector(`.cea-underline[data-error-id="${errorId}"]`);
    if (!mark) return;

    const markText = mark.textContent;
    const isSentenceRewrite = sentence
        && newText.length > markText.length * 2
        && newText.length > 40;

    // Sentence-level rewrite: replace the full sentence, not just the mark
    if (isSentenceRewrite) {
        if (_replaceSentence(editorEl, mark, newText, sentence)) {
            return;
        }
        // DOM sentence mapping failed — abort rather than stuffing
        // a 25-word sentence into a 1-word mark
        console.warn(
            '[UnderlineRenderer] Sentence replacement failed for error',
            errorId, '— cannot safely apply edit',
        );
        return;
    }

    // Simple replacement: swap the mark's text content
    // ... (rest unchanged)
```

**Key change**: The `if (isSentenceRewrite && _replaceSentence(...))` one-liner splits into a nested block. If `_replaceSentence` returns false, we `return` immediately. No fallback to `mark.textContent = text`.

---

### F3. Backend suggestion scrubbing in `_normalize_issue_fields`

**File**: `app/llm/parser.py` (line 364)

**Root cause**: `_normalize_issue_fields` normalizes `suggestions` into a list but never validates content. When the LLM returns chatty/explanatory text (e.g., "Consider rephrasing to use active voice by restructuring the sentence..."), that raw text survives all the way to the frontend. The `_autoFetchSuggestion` path puts `rewriteText` directly into the chip without going through `extractReplacement`.

**Fix**: After normalizing `suggestions` to a list, scrub each entry. Drop suggestions that are clearly explanatory text (>3x `flagged_text` length AND >20 chars). This catches the "rule text as suggestion" pattern at the source.

```python
def _normalize_issue_fields(item: dict) -> None:
    # Suggestions
    suggestions = item.get("suggestions")
    if not isinstance(suggestions, list):
        item["suggestions"] = [suggestions] if suggestions else []

    # Scrub suggestions: drop entries that are clearly explanatory
    # text rather than concrete replacements for the flagged span.
    flagged = item.get("flagged_text", "")
    flagged_len = len(flagged) if flagged else 1
    scrubbed = []
    for s in item["suggestions"]:
        if not isinstance(s, str) or not s.strip():
            continue
        # A concrete replacement should be roughly the same length as
        # the flagged text. Suggestions >3x longer AND >20 chars are
        # almost certainly instructions/explanations, not drop-in text.
        if len(s) > 20 and len(s) > flagged_len * 3:
            logger.debug(
                "Scrubbed chatty suggestion (len=%d vs flagged_len=%d): %s",
                len(s), flagged_len, s[:80],
            )
            continue
        scrubbed.append(s)
    item["suggestions"] = scrubbed

    # ... rest of function unchanged (sentence, sentence_index, etc.)
```

**Key change**: After the list normalization, iterate and filter. Threshold: `len(s) > 20 AND len(s) > flagged_len * 3`. This is the same heuristic used by `_isInstruction` on the frontend (line 126: `suggestion.length > 35 && suggestion.length > flaggedLen * 3`) but applied at the backend before data crosses the network. The `>20` floor (vs frontend's `>35`) is deliberately tighter at the source — better to scrub early. Single-word replacements ("use" for "utilize") always survive since they're ≤20 chars.

---

### F4. Tests

**File**: `tests/services/test_orchestrator_spans.py`

Add 4 tests to the existing test file:

**Sentence-context priority (2 tests):**
1. `test_resolve_llm_span_sentence_context_first` — When `issue.sentence` is set and `flagged_text` appears multiple times in the document, span anchors to the occurrence inside the sentence, not the first document-wide occurrence.
2. `test_resolve_llm_span_falls_back_to_text_find` — When `issue.sentence` is empty or doesn't match, falls back to `text.find`.

**File**: `tests/test_parser.py`

Add 2 tests:

**Suggestion scrubbing (2 tests):**
3. `test_normalize_scrubs_chatty_suggestions` — A suggestion >3x flagged_text length and >20 chars is dropped.
4. `test_normalize_keeps_short_suggestions` — Short concrete replacements survive scrubbing.

---

## Files Modified

| File | Changes | Status |
|------|---------|--------|
| `app/llm/prompts.py` | A1, A3, A5 | DONE |
| `app/llm/parser.py` | A4, F3 | A4 DONE, F3 TO DO |
| `app/config.py` | A2, A3 | DONE |
| `static/js/issues/issue-card.js` | B1 | DONE |
| `static/js/editor/underline-renderer.js` | B2, F2 | B2 DONE, F2 TO DO |
| `rules/rule_mappings.yaml` | C1, C2 | DONE |
| `app/services/parsing/html_parser.py` | D1-D8 | DONE |
| `tests/services/test_html_parser.py` | D9 | DONE |
| `app/services/analysis/languagetool_client.py` | E1 | DONE |
| `rules/word_usage/config/simple_words_config.yaml` | E2 | DONE |
| `app/services/analysis/orchestrator.py` | F1 | TO DO |
| `tests/services/test_orchestrator_spans.py` | F4 | TO DO |
| `tests/test_parser.py` | F4 | TO DO |

## Verification

1. `python -m pytest tests/ --ignore=tests/rules/test_lt_examples.py -v` — full test suite must pass
2. `python -m pytest tests/services/test_orchestrator_spans.py -v` — span resolution tests including new F4 tests
3. `python -m pytest tests/test_parser.py -v` — parser tests including suggestion scrubbing

# CEA Post-Perfection Fixes: LLM Hallucinations, Deduplication, and Per-Block Progress



## Context



The Perfection Plan (Phases 1-4) was fully implemented and all 388 tests pass. However, live testing on `test.adoc` revealed three issues:



1. **LLM global pass hallucinating step numbering errors** — CHECK item (6) "document structure" combined with the "Flag all clear violations" bias directive causes the LLM to falsely flag "Incorrect step numbering" on AsciiDoc procedures. The lite-markers counter IS working correctly (verified in code), producing sequential `1. 2. 3. 4. 5.` numbering. The LLM is hallucinating.



2. **Duplicate issues appearing on screen** — same flagged text shown as multiple cards from different categories (GRAMMAR + STRUCTURE, etc.). Root cause: two layers of intentional but user-hostile dedup behavior: (a) `_deduplicate_llm_issues()` only deduplicates within the SAME source, keeping granular+global duplicates; (b) `_is_span_duplicate()` intentionally keeps different-category issues on overlapping spans.



3. **Per-block progress missing** — AI Analysis phase shows static "AI-powered analysis (N blocks)" label instead of live "3/15 blocks" counter. `_collect_block_results()` lacks `socket_sid`/`session_id` to emit per-block progress.



---



## Fix 1: Stop LLM Global Step Numbering Hallucinations



**Root Cause**: The global prompt CHECK item (6) says "verify modular docs patterns (procedure needs Prerequisites/Procedure/Verification sections; concept needs clear topic sentence; reference needs consistent format)." The LLM interprets this broadly and hallucates step numbering issues, even though lite-markers has correct sequential numbers.



**File**: `app/llm/prompts.py` lines 323-333



**Fix**: Add a SKIP instruction to the global prompt, immediately after the CHECK list:



```python

"SKIP: step numbering in procedures — the rendering engine handles "

"sequential numbering automatically. Do not flag step order, restart, "

"or numbering issues.\n\n"

```



This narrowly blocks the hallucination without removing the useful structural checks (Prerequisites/Procedure/Verification presence, topic sentences, consistent format).



---



## Fix 2: Cross-Source LLM Deduplication



**Root Cause**: Two dedup gaps allow duplicate cards for the same flagged text:



### Gap A: `_deduplicate_llm_issues()` — source-aware text matching



**File**: `app/services/analysis/merger.py` lines 96-142



`_composite_text_matches_any()` (line 145) only matches within the same source:

```python

if seen_source != source:

continue # ← Skips cross-source matches

```



So granular "see above" + global "see above" → both pass (different sources).



**Fix**: Change `_composite_text_matches_any()` to match across sources for text dedup. The source-awareness was added to "keep separate entries" but in practice it produces user-visible duplicates. The span-based dedup (`_span_overlaps_seen`) already handles the cross-chunk overlap case where different `flagged_text` matches the same span.



In `_composite_text_matches_any()`, remove the `if seen_source != source: continue` guard:

```python

def _composite_text_matches_any(

normalized: str,

source: str,

seen_keys: set[tuple[str, str]],

) -> bool:

for seen_source, seen_text in seen_keys:

# Match across all sources — same flagged text is a duplicate

# regardless of whether it came from granular or global pass

if normalized == seen_text:

return True

if seen_source == source and _words_overlap(

_to_words(normalized), _to_words(seen_text),

):

return True

return False

```



Keep word-overlap matching source-aware (it's fuzzy and could over-match cross-source), but make exact text matching cross-source.



### Gap B: `_is_span_duplicate()` — category-aware overlap



**File**: `app/services/analysis/merger.py` lines 234-274



```python

det_cat = _find_category_for_span(det_span, accepted_issues)

if det_cat and llm_category and det_cat != llm_category:

continue # Different category — not a duplicate

```



This keeps LLM issues that overlap deterministic issues if categories differ. Example: deterministic flags "see above" as self-referential text (structure) → LLM flags "see above" as grammar → both kept → user sees 2 cards.



**Fix**: Remove the category-aware exception. If an LLM issue overlaps an existing issue by >80% of the shorter span, it's a duplicate regardless of category. The deterministic issue is already flagging the problem; the LLM adding a different-category angle on the same text doesn't help the user.



```python

def _is_span_duplicate(

issue: IssueResponse,

det_spans: list[list[int]],

accepted_issues: list[IssueResponse] | None,

) -> bool:

llm_start, llm_end = issue.span[0], issue.span[1]



for det_span in det_spans:

if len(det_span) < 2:

continue

d_start, d_end = det_span[0], det_span[1]



# No overlap at all — skip

if not (llm_start < d_end and d_start < llm_end):

continue



# Any overlap with existing issue → duplicate

return True



return False

```



Remove `_find_category_for_span()` and the category comparison — simplify to pure span overlap.



### Test Updates



**File**: `tests/services/test_merger.py`



Update tests that verify category-aware behavior:

- Tests asserting "different categories kept despite overlap" → update to assert dedup

- Tests asserting granular+global same text kept separately → update to assert dedup

- Keep tests for: span overlap threshold (>80%), cross-block demotion, word-level fallback



---



## Fix 3: Per-Block Progress Counter



**Root Cause**: `_collect_block_results()` (line 1670) iterates over completed futures with `as_completed()` — the perfect place to emit per-block progress — but lacks `socket_sid`, `session_id`, and `blocks_total`.



### Backend Changes



**File**: `app/services/analysis/orchestrator.py`



Thread a `progress_context` dict through 4 functions:



| Function | Line | Add parameter |

|----------|------|---------------|

| `_run_incremental_blocks()` | 918 | `progress_context: dict | None = None` |

| `_analyze_blocks()` | 1502 | `progress_context: dict | None = None` |

| `_analyze_blocks_parallel()` | 1549 | `progress_context: dict | None = None` |

| `_collect_block_results()` | 1670 | `progress_context: dict | None = None` |



**In `_run_llm_granular()` (line 847)**, build the context:

```python

progress_ctx = {

"socket_sid": socket_sid,

"session_id": session_id,

"blocks_total": len(text_blocks),

"blocks_done": 0,

}

```

Pass to `_run_incremental_blocks()`, which passes to `_analyze_blocks()`, etc.



**In `_collect_block_results()` (line 1670)**, emit after each future:

```python

def _collect_block_results(

futures: dict[Any, int],

progress_context: dict | None = None,

) -> list[dict[str, Any]]:

all_results: list[dict[str, Any]] = []

blocks_done = 0

blocks_total = len(futures)

for future in as_completed(futures):

block_idx = futures[future]

try:

results = future.result()

all_results.extend(results)

except (ConnectionError, TimeoutError, RuntimeError) as exc:

logger.warning("Block %d analysis failed: %s", block_idx, exc)

blocks_done += 1

if progress_context:

_emit_event(progress_context["socket_sid"], "stage_progress", {

"session_id": progress_context["session_id"],

"phase": "llm_granular",

"status": "progress",

"blocks_done": blocks_done,

"blocks_total": progress_context["blocks_total"],

})

return all_results

```



Note: `blocks_total` comes from `progress_context` (total document blocks), not `len(futures)` (which only counts non-cached blocks in incremental mode).



Also account for cached blocks in `_analyze_blocks_parallel()`: add `len(cached_results)` to the initial `blocks_done` counter if cached blocks exist.



### Frontend Changes



**File**: `static/js/issues/checking-indicator.js`



In `_onStageProgress()`, handle `status: 'progress'`:

```javascript

} else if (data.phase === 'llm_granular') {

if (data.status === 'started') {

this._markAllGroupsDone();

this._showAiPhase(data.blocks_total);

} else if (data.status === 'progress') {

this._updateAiProgress(data.blocks_done, data.blocks_total);

} else if (data.status === 'done') {

this._markAiDone();

this._showGlobalPhase();

}

}

```



Add `_updateAiProgress()` method:

```javascript

_updateAiProgress(blocksDone, blocksTotal) {

if (!this._aiRow) return;

const label = this._aiRow.querySelector('span:last-child');

if (label) {

label.textContent = `AI-powered analysis (${blocksDone}/${blocksTotal} blocks)`;

}

}

```



---



## Critical Files



| File | Fix | Change |

|------|-----|--------|

| `app/llm/prompts.py` | 1 | Add SKIP for step numbering to global prompt |

| `app/services/analysis/merger.py` | 2 | Cross-source text dedup, remove category-aware span exception |

| `tests/services/test_merger.py` | 2 | Update dedup tests for new behavior |

| `app/services/analysis/orchestrator.py` | 3 | Thread `progress_context` through 4 functions |

| `static/js/issues/checking-indicator.js` | 3 | Handle `status: 'progress'`, add `_updateAiProgress()` |



## Verification



1. **Fix 1**: Run analysis on `test.adoc` → no "Incorrect step numbering" issues from global pass

2. **Fix 2**: Run analysis on `test.adoc` → no duplicate cards for same flagged text with different categories. Run `python -m pytest tests/services/test_merger.py -v` → all updated tests pass

3. **Fix 3**: Run analysis on `test.adoc` → UI shows "AI-powered analysis (1/15 blocks)" updating in real time

4. **Full suite**: `python -m pytest tests/ -v` → all 388+ tests pass
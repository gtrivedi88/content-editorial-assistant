# Maximize Suggestion/Replacement Text Coverage

## Context

Issue cards in the CEA UI sometimes show only an error description with a Dismiss button, without any replacement text or Accept button. The user wants every issue to have actionable replacement text wherever possible, so they can click Accept/Replace instead of manually rewriting.

The current pipeline has four gaps that cause issues to lack suggestions. This plan addresses each gap in order of impact.

---

## Fix 1: Add Suggestions to `do_not_use_terms_rule`

The only deterministic rule that passes `suggestions=[]`. 15 terms in the YAML config. Some have concrete alternatives in their `message` text but these aren't extracted into suggestions.

### `rules/word_usage/config/do_not_use_config.yaml`

Add `alternatives` list to 4 terms that have concrete replacements:

| Term | `alternatives` |
|------|---------------|
| `kerberize` | `["Kerberos-aware", "Kerberos-enabled"]` |
| `kerberized` | `["Kerberos-aware", "Kerberos-enabled"]` |
| `quiescent` | `["inactive", "safe"]` |
| `resides` | `["is in", "is located in"]` |

The remaining 11 terms have no clear single replacement — they get instruction-style suggestions generated in the rule code.

### `rules/word_usage/do_not_use_terms_rule.py`

- Update `_load_config()` return type from `Dict[str, Dict[str, str]]` to `Dict[str, Dict[str, Any]]`
- Add `_build_suggestions()` helper that:
  - If `info.get('alternatives')` has entries → returns `["Change 'X' to 'Y'"]` for each (parseable by frontend's `extractReplacement()`)
  - Otherwise → returns `["Rewrite to avoid using 'X'."]` (instruction-style, routes to LLM auto-fetch)
- Change line 66 from `suggestions=[]` to `suggestions=_build_suggestions(info, found)`
- `_build_suggestions()` includes type safety: `if not isinstance(alternatives, list): alternatives = []`
- Add `_match_case(replacement, original)` helper: if `original[0].isupper()`, capitalize first char of replacement. Called before formatting the "Change 'X' to 'Y'" string so "Resides" → "Is in" (not "is in")

**Instruction routing is already handled** — both frontend `_isInstruction()` (matches `"Rewrite"` prefix) and backend `_is_instruction_suggestion()` (matches `"rewrite"` prefix) detect instruction-style text and route to LLM. `"Rewrite to avoid using 'X'."` will never appear as literal Accept replacement text.

**Result**: Every do_not_use issue now has at least one suggestion. Terms with `alternatives` get immediate Accept buttons; others route to LLM for rewrite.

---

## Fix 2: Strengthen LLM Prompts to Require Suggestions

Both granular and global analysis prompts show `"suggestions":["fix"]` as a format example but never explicitly mandate non-empty suggestions. The LLM sometimes returns empty arrays.

### `app/llm/prompts.py`

**Granular prompt** (`build_granular_prompt()`, lines 275-280) — After the response format JSON, add:

```
"IMPORTANT: suggestions must contain at least one concrete replacement "
"for the flagged_text. Provide the corrected version of the flagged span "
"that fixes the issue. Do not leave suggestions empty.\n\n"
```

Also change `"suggestions":["fix"]` to `"suggestions":["corrected text"]` for clarity.

Add scope constraint to prevent paragraph-level replacements on tone/flow issues:
```
"Keep suggestions scoped to the flagged_text span only — do not rewrite "
"surrounding text.\n\n"
```

**Global prompt** (`build_global_prompt()`, lines 341-346) — Same changes (mandate + scope constraint).

**Result**: LLM-sourced issues will consistently include replacement text scoped to the flagged span, which the frontend can display immediately or use for Accept buttons.

---

## Fix 3: Suggestion Engine Fallback When LLM Unavailable

When LLM is unavailable, `_request_llm_suggestion()` returns `{"error": "LLM not available", "suggestions": []}` for issues with empty suggestions. No replacement text reaches the frontend.

### `app/services/suggestions/engine.py`

- Add `import re` at top
- Add `_CHANGE_TO_RE` regex to extract quoted alternatives from message text (patterns: `Use 'X'`, `Change to 'X'`, `Replace with 'X'`, `Refer to ... as 'X'`)
- Add `_extract_alternative_from_message(message)` helper
- In `_request_llm_suggestion()`, when LLM is unavailable AND `issue.suggestions` is empty, try extracting from `issue.message`. If found, apply case matching (capitalize extracted text if `issue.flagged_text` starts uppercase), then return `{"rewritten_text": extracted, "explanation": message, "confidence": 0.7}` instead of the error dict

**Result**: Issues whose messages contain quoted alternatives (e.g., "Use 'inactive' instead") get a suggestion even when the LLM is down.

---

## Fix 4: Frontend Fallback for Error Responses

When `_autoFetchSuggestion()` gets an error response with a `suggestions` array, it currently discards everything. If no deterministic Accept button exists, the user sees only Dismiss.

### `static/js/issues/issue-card.js`

In `_autoFetchSuggestion()`, after the `!result || result.error` check (line 301), add fallback logic:

- If `result.suggestions` has entries AND no `existingAcceptBtn` exists
- Try `extractReplacement()` on the first suggestion
- If it yields replacement text, create an Accept button dynamically
- Otherwise, clear spinner as before

Guard: only runs when there's no existing Accept button (`!existingAcceptBtn`), so it never interferes with deterministic suggestions.

**Result**: When LLM fails but the error response carries deterministic suggestions (e.g., "Change 'kerberize' to 'Kerberos-aware'"), the frontend can still show an Accept button.

---

## Fix 5: Score Update on Accept/Dismiss

Pre-existing gap: `acceptSuggestion()` in `actions.js:155` calls `acceptIssue()` fire-and-forget — the backend returns the recalculated score in the response, but the frontend ignores it. The `qualityScore` in the store never updates after accepting or dismissing issues. This affects ALL Accept/Dismiss buttons, not just the Fix 4 fallback.

### `static/js/state/actions.js`

**`acceptSuggestion()`** (line 155) — Make async, use returned score:
- After `acceptIssue(sessionId, errorId)` resolves, read `result.score` from the response
- Update store: `store.setState({ qualityScore: score })`
- Use same score extraction pattern as `socket-client.js:109`: `typeof result.score === 'object' ? result.score.score : result.score`

**`dismissError()`** (line 181) — Same pattern: use returned score from `dismissIssue()`.

Both functions keep their synchronous state updates (error removal, card disappearance) immediate — only the score update awaits the backend response.

**Result**: Score ring updates in real-time when users accept or dismiss issues, for both deterministic and fallback Accept buttons.

---

## Critical Files

| File | Fix | Change |
|------|-----|--------|
| `rules/word_usage/config/do_not_use_config.yaml` | 1 | Add `alternatives` to 4 terms |
| `rules/word_usage/do_not_use_terms_rule.py` | 1 | Use alternatives, add instruction fallback |
| `app/llm/prompts.py` | 2 | Mandate non-empty suggestions in format spec |
| `app/services/suggestions/engine.py` | 3 | Add `_extract_alternative_from_message()` fallback |
| `static/js/issues/issue-card.js` | 4 | Use error-response suggestions as fallback |
| `static/js/state/actions.js` | 5 | Update qualityScore from accept/dismiss API response |

## Tests

- `tests/rules/test_fp_guards.py` — Add tests: `kerberize` has suggestions, `please` gets instruction-style suggestion
- `tests/llm/test_prompts.py` — Verify granular and global prompts contain "suggestions must contain" requirement
- `tests/services/test_suggestion_engine.py` — Test `_extract_alternative_from_message()` patterns and LLM-unavailable fallback path

## Verification

1. `python -m pytest tests/ -v` — all 389+ tests pass (plus new tests)
2. `python -m pytest tests/rules/test_fp_guards.py -v` — no FP regressions
3. Manual: analyze text containing "please" and "kerberize" — both should show suggestions in the UI

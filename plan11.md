Updated plan:

# Plan 11 (Revised): Dynamic Token Budget with Thinking Control



## Context



Every LLM call currently gets `MODEL_MAX_TOKENS=16384`. Gemini 2.5 Flash is a thinking model — it expands internal `<think>` tokens to consume ~96% of whatever `max_tokens` budget is given (documented in Google GenAI SDK issue #2062). A 3-sentence block that needs 300 output tokens still triggers ~15K thinking tokens, wasting latency and API cost.



**Root cause**: `max_tokens` is a *combined* budget for thinking + output. Without controlling thinking separately, predictive output sizing is defeated — the model just thinks more.



**Solution**: Google's OpenAI-compatible endpoint supports `reasoning_effort` parameter (`"none"`, `"low"`, `"medium"`, `"high"` → 0, ~1K, ~8K, ~24K thinking tokens). This caps thinking at a known ceiling. Whether `max_tokens` is a combined budget (thinking + output) or output-only depends on Google's compatibility layer implementation, so we defensively add a low thinking buffer to each output prediction. Result: predictable budgets much smaller than 16K, with room for both thinking and JSON output.



## Execution Order



**Plan 11 (this)** → Plan 13 (prompt cleanup) → Plan 12 (Judge enrichment)



---



## Step 0: Thinking Budget Control (prerequisite)



### 0a. `models/config.py` — Add env var



After line 32 (`TOP_K`), add:



```python

REASONING_EFFORT = os.getenv('GEMINI_REASONING_EFFORT', None)

```



Default `None` = don't send the parameter (model uses its own default). Set `GEMINI_REASONING_EFFORT=low` in `.env` for CEA's pattern-matching editorial tasks.



### 0b. `models/config.py` — Add to API provider config dict



In `get_active_config()`, inside the `elif cls.MODEL_PROVIDER == 'api':` block (line 51-58), add `reasoning_effort`:



```python

elif cls.MODEL_PROVIDER == 'api':

config.update({

'base_url': cls.BASE_URL,

'model': cls.MODEL_ID,

'api_key': cls.ACCESS_TOKEN,

'timeout': cls.TIMEOUT,

'cert_path': cls.CERT_PATH,

'reasoning_effort': cls.REASONING_EFFORT, # NEW

})

```



### 0c. `models/providers/api_provider.py` — Add to payload in `_build_request()`



After the `seed` block (~line 248), add Gemini-specific `reasoning_effort`:



```python

# Gemini thinking control — decouple thinking from output budget

_VALID_REASONING_EFFORTS = frozenset({'none', 'low', 'medium', 'high'})



# In _build_request(), after seed block:

if self._is_gemini_api():

reasoning_effort = self.config.get('reasoning_effort')

if reasoning_effort and reasoning_effort.lower() in self._VALID_REASONING_EFFORTS:

payload['reasoning_effort'] = reasoning_effort.lower()

```



`_VALID_REASONING_EFFORTS` is a class-level frozenset. Validates against the 4 values Google supports for Gemini 2.5 (`"none"` is explicitly supported per Google docs to disable thinking). Prevents arbitrary strings from reaching the API. Non-Gemini providers never see this parameter.



### 0d. `.env` — Set reasoning effort



Add: `GEMINI_REASONING_EFFORT=low`



### 0e. `app/config.py` — Add config attr + log it



Add class attribute (after `MODEL_MAX_TOKENS` line 74):



```python

GEMINI_REASONING_EFFORT: str | None = os.environ.get("GEMINI_REASONING_EFFORT")

```



Add to `log_summary()` after the `MODEL_MAX_TOKENS` log line:



```python

logger.info(" GEMINI_REASONING_EFFORT=%s",

cls.GEMINI_REASONING_EFFORT or 'not set')

```



This is needed because `client.py` imports from `app.config.Config`, not `models.config.ModelConfig`. Both configs read the same env var.



---



## Step 1: Parser — Surface truncation signal



**File:** `app/llm/parser.py`



Add `parse_analysis_response_ex()` after `parse_analysis_response()` (after line 63). Rewrite `parse_analysis_response()` as thin wrapper.



```python

def parse_analysis_response_ex(raw_text: str) -> tuple[list[dict], bool]:

"""Parse LLM analysis response, surfacing truncation status.



Returns:

Tuple of (validated issue list, truncated flag).

"""

cleaned = _strip_code_fences(raw_text)

cleaned = _strip_trailing_commas(cleaned)



try:

parsed = json.loads(cleaned)

issues = _normalize_to_list(parsed)

if issues is None:

return [], False

return _validate_and_filter_issues(issues), False

except json.JSONDecodeError:

pass



salvaged = _salvage_truncated_array(cleaned)

if salvaged is not None:

logger.info("Salvaged %d items from truncated response", len(salvaged))

issues = _normalize_to_list(salvaged)

if issues is None:

return [], True

return _validate_and_filter_issues(issues), True



logger.warning("Failed to parse LLM response (first 200: %s)", cleaned[:200])

return [], False





def parse_analysis_response(raw_text: str) -> list[dict]:

# ... existing docstring ...

issues, _ = parse_analysis_response_ex(raw_text)

return issues

```



**Do NOT touch:** `_parse_json_text()`, `parse_suggestion_response()`, `parse_judge_response()`



---



## Step 2: Provider — Capture finish_reason via `_result_meta`



### 2a. `models/providers/base_provider.py` (line 47-64)



In `_prepare_generation_params()`, pop internal keys before they leak into the API payload:



```python

def _prepare_generation_params(self, **kwargs: object) -> Dict[str, Any]:

# ... existing token config setup ...



params.update(kwargs)



# Pop internal keys — must not leak into API payloads

params.pop('_result_meta', None)

params.pop('_timeout_override', None)



return params

```



### 2b. `models/providers/api_provider.py` (line 157-219)



In `generate_text()`:

1. Pop `_result_meta` from kwargs BEFORE `_prepare_generation_params` (since base pops it too, belt-and-suspenders)

2. Pop `_timeout_override` from kwargs, use it to override timeout

3. After successful 200 response, populate `_result_meta` with finish_reason + usage



```python

def generate_text(self, prompt: str, **kwargs: object) -> str:

if not self.is_available():

logger.error("API is not available")

return ""



# Extract internal keys before param preparation

result_meta = kwargs.pop('_result_meta', None)

timeout_override = kwargs.pop('_timeout_override', None)



params = self._prepare_generation_params(**kwargs)

endpoint, payload = self._build_request(prompt, params)

headers = self._get_headers()



use_case = kwargs.get('use_case', 'default')

timeout = timeout_override or self._get_timeout_for_use_case(use_case)



try:

# ... existing request code ...



if response.status_code == 200:

resp_json = response.json()



# Populate metadata side-channel

if result_meta is not None:

self._extract_result_meta(resp_json, result_meta)



generated_text = self._extract_response(resp_json)

# ... rest unchanged ...

```



Add helper method to `APIProvider`:



```python

@staticmethod

def _extract_result_meta(resp_json: dict, meta: dict) -> None:

"""Extract API response metadata into the caller's dict."""

choices = resp_json.get('choices', [])

if choices:

meta['finish_reason'] = choices[0].get('finish_reason', '')

usage = resp_json.get('usage', {})

meta['completion_tokens'] = usage.get('completion_tokens', 0)

meta['prompt_tokens'] = usage.get('prompt_tokens', 0)

```



---



## Step 3: Client — Predictive token budget + truncation retry



**File:** `app/llm/client.py`



### 3a. Add `_dynamic_max_tokens()` static method to `LLMClient`



The thinking buffer must scale with `GEMINI_REASONING_EFFORT` from `.env`. If someone changes to `medium` (8K thinking), a hardcoded 1K buffer would cause truncation. The function reads `Config.GEMINI_REASONING_EFFORT` and scales accordingly:



| Effort | Thinking budget | `base_think` |

|--------|----------------|--------------|

| `none` | 0 tokens | 200 (safety margin) |

| `low` | ~1K tokens | 1000 |

| `medium` | ~8K tokens | 8000 |

| `high` | ~24K tokens | return cap (bypass math) |

| not set | model default | 1000 (assume low) |



```python

_CONTENT_TYPE_MULTIPLIERS: dict[str, float] = {

'procedure': 1.2, 'assembly': 1.15, 'release_notes': 1.1,

'concept': 1.0, 'reference': 0.9,

}



@staticmethod

def _dynamic_max_tokens(phase, input_text_len=0, num_issues=0,

content_type='concept', sentence_count=0,

rule_count=0, det_issue_count=0) -> int:

cap = Config.MODEL_MAX_TOKENS



# Scale thinking buffer to match configured reasoning effort

effort = (Config.GEMINI_REASONING_EFFORT or 'low').lower()

if effort == 'high':

return cap # No restriction — model needs full budget

elif effort == 'medium':

base_think = 8000

elif effort == 'none':

base_think = 200

else: # 'low' or unrecognized

base_think = 1000



if phase == 'granular':

predicted_issues = max(3, sentence_count // 2, det_issue_count // 3)

output_tokens = 200 + (predicted_issues * 85)

thinking_buffer = base_think + (sentence_count * 15)

budget = output_tokens + thinking_buffer

elif phase == 'global':

budget = (300 + (input_text_len // 40)) + int(base_think * 1.5)

elif phase == 'judge':

budget = (100 + (num_issues * 15)) + int(base_think * 0.8)

elif phase == 'suggest':

budget = base_think + 500

else:

budget = cap



multiplier = LLMClient._CONTENT_TYPE_MULTIPLIERS.get(content_type, 1.0)

budget = max(1024, min(int(budget * multiplier), cap))

return budget

```



Budget = **output prediction** + **effort-scaled thinking buffer**:

- **granular**: output (200 + issues×85) + thinking (base_think + sentences×15)

- **global**: output (300 + input_len//40) + thinking (base_think × 1.5)

- **judge**: output (100 + issues×15) + thinking (base_think × 0.8)

- **suggest**: base_think + 500

- **high effort**: bypass math, return cap

- Floor at 1024, cap at `MODEL_MAX_TOKENS`



### 3b. Truncation detection + retry in `_safe_analysis_call()`



Add `max_tokens` parameter. Pass `_result_meta={}` dict through `_generate()` to provider. After parse:

- Check `parse_analysis_response_ex()` returned `truncated=True`

- OR `finish_reason` in `{'LENGTH', 'MAX_TOKENS'}` (uppercase-normalized for provider-agnostic matching)

- If truncated AND budget < cap: single retry with 1.5× budget, 75s timeout override

- Return whichever call produced more issues



Add `_retry_truncated_analysis()` helper method.



### 3c. Update `analyze_block()` and `analyze_global()`



Add `det_issue_count: int = 0` parameter. Compute dynamic budget and pass to `_safe_analysis_call()`:



```python

def analyze_block(self, text, sentences, style_guide_excerpts,

content_type="concept", acronym_context=None,

document_outline=None, det_issue_count=0):

# ...

max_tokens = self._dynamic_max_tokens(

'granular', len(text), content_type=content_type,

sentence_count=len(sentences),

rule_count=len(style_guide_excerpts),

det_issue_count=det_issue_count,

)

return self._safe_analysis_call(

user_prompt, system_prompt=system_prompt,

max_tokens=max_tokens,

)

```



Same pattern for `analyze_global()` (phase `'global'`).



### 3d. Update module-level wrappers



Add `det_issue_count: int = 0` to both `analyze_block()` and `analyze_global()` wrapper functions (lines 363-419). Forward to client methods.



### 3e. Add import



```python

from app.llm.parser import parse_analysis_response_ex

```



(Keep existing `parse_analysis_response` import for backward compat.)



---



## Step 4: Orchestrator — Thread `det_issue_count`



**File:** `app/services/analysis/orchestrator.py`



### 4a. `_run_llm_phases()` (line 341)



Already has `det_issues` parameter. Pass `det_issue_count=len(det_issues)` to both `_run_llm_granular()` and `_run_llm_global()`:



```python

llm_issues = _run_llm_granular(

session_id, socket_sid, prep, content_type, acronym_context,

style_guide_excerpts=excerpts,

document_outline=doc_outline,

det_issue_count=len(det_issues), # NEW

)

```



### 4b. Thread through the call chain



Add `det_issue_count: int = 0` to these function signatures:

- `_run_llm_granular()` (line 1037) → forward to `_run_incremental_blocks()`

- `_run_incremental_blocks()` (line 1117) → forward to `_analyze_blocks()`

- `_run_llm_global()` (line 1268) → forward to `analyze_global()`

- `_analyze_blocks()` (line 1711) → forward to `analyze_block()` and `_analyze_blocks_parallel()`

- `_analyze_blocks_parallel()` (line 1762) → forward to `_submit_block_futures()`

- `_submit_block_futures()` (line 1809) → forward to `_analyze_and_cache_block()`

- `_analyze_and_cache_block()` (line 1855) → forward to `analyze_block()`



Each function gains `det_issue_count: int = 0` as a keyword arg, passes it down.



---



## Step 5: Tests



### 5a. `tests/llm/test_parser.py` — 3 new tests



- `test_parse_analysis_response_ex_clean` — valid JSON → `(issues, False)`

- `test_parse_analysis_response_ex_truncated` — truncated array → `(salvaged, True)`

- `test_parse_analysis_response_backward_compat` — `parse_analysis_response()` returns `list[dict]`



### 5b. `tests/llm/test_client.py` — 8 new tests



- `test_truncation_parser_triggers_retry` — salvaged + retry returns more issues

- `test_truncation_finish_reason_max_tokens` — Gemini `MAX_TOKENS` triggers retry

- `test_truncation_finish_reason_length` — OpenAI `length` triggers retry

- `test_truncation_retry_timeout_keeps_original` — retry fails, original kept

- `test_dynamic_budget_procedure_higher` — procedure > concept

- `test_dynamic_budget_det_issues_scale` — more det_issues = higher budget

- `test_dynamic_budget_floor_1024` — budget never below 1024

- `test_reasoning_effort_in_gemini_payload` — reasoning_effort in Gemini payload, absent for non-Gemini



---



## Files Modified (summary)



| File | Changes |

|------|---------|

| `models/config.py` | Add `REASONING_EFFORT` class attr, add to API config dict |

| `models/providers/api_provider.py` | Add `reasoning_effort` to Gemini payload, pop+populate `_result_meta`, support `_timeout_override`, add `_extract_result_meta()` |

| `models/providers/base_provider.py` | Pop `_result_meta` and `_timeout_override` in `_prepare_generation_params()` |

| `app/llm/parser.py` | Add `parse_analysis_response_ex()`, rewrite `parse_analysis_response()` as wrapper |

| `app/llm/client.py` | Add `_dynamic_max_tokens()`, `_CONTENT_TYPE_MULTIPLIERS`, `_TRUNCATION_FINISH_REASONS`, rewrite `_safe_analysis_call()`, add `_retry_truncated_analysis()`, add `det_issue_count` to methods + wrappers, add import |

| `app/config.py` | Add reasoning effort to `log_summary()` |

| `app/services/analysis/orchestrator.py` | Thread `det_issue_count` through 7 functions in the call chain |

| `.env` | Add `GEMINI_REASONING_EFFORT=low` |

| `tests/llm/test_parser.py` | 3 new tests |

| `tests/llm/test_client.py` | 8 new tests |



## Verification



```bash

# Unit tests

python -m pytest tests/llm/test_parser.py -v

python -m pytest tests/llm/test_client.py -v



# Full suite

python -m pytest tests/ --ignore=tests/rules/test_lt_examples.py -v



# Manual: run app and check logs for

# "GEMINI_REASONING_EFFORT=low"

# "Dynamic max_tokens: phase=granular ... → NNNN"

# "Truncation detected — retrying with NNNN tokens"

```
# Fix Three Structural Rule Gaps: Continuation-Aware Checks + Abstract Prompt



## Context



Testing CEA against `test.adoc` revealed three gaps where deterministic rules failed to fire, leaking issues to the LLM (which only catches the first occurrence) or missing them entirely. All three stem from the same root: AsciiDoc continuation markers (`+`) create structural noise that breaks the assumptions of the block-by-block checks.



**The AsciiDoc structure in `test.adoc`:**

```

.Procedure

* Apply a `MachineConfig` to create a separate partition:

+

[source,yaml]

----

sizeMiB: <partition_size> ← MiB (binary unit)

----

+

Where:

+

* `<root_disk>`: Specify the root disk. ← should be "Specifies"

* `<start_of_partition>`: Specify the start... ← should be "Specifies"

* `<partition_size>`: Specify a minimum size for the partition of 500 GB ← GB vs MiB mismatch

```



**Parser facts** (from `asciidoc_parser.py`):

- `+` lines → `block_type="comment"`, `should_skip_analysis=True`

- `content_blocks` filter in `run_structural_rules()` removes them

- `block.content` = Tier 3 (fully stripped, no backticks)

- `block.inline_content` = Tier 2 (block markers stripped, backticks/bold/italic preserved)



---



## Gap 1: `_check_where_list_specifies` — Regex vs Stripped Content



**File:** `rules/modular_compliance/structural_rules.py` (lines 176-248)



**Root cause:** The regex `_SPECIFY_PATTERN` requires backtick-wrapped variables (`` `[^`]+` ``), but the check uses `block.content` (Tier 3) which has backticks stripped. The pattern can never match.



The user diagnosed this as a continuation `+` problem, but continuation blocks are already filtered from `content_blocks` (they're `block_type="comment"` with `should_skip_analysis=True`). The actual bug is the Tier 3 vs Tier 2 mismatch — same class of bug as the `_block_to_markdown()` FP fixed in the previous session.



**Fix:** Use `block.inline_content` (Tier 2, preserves backticks) instead of `block.content`:



```python

# Line 219: change from

content = block.content or ""

# To

content = block.inline_content or block.content or ""

```



Same change on line 199 for the "Where:" detection (though `Where:` has no inline markers, using `inline_content` is consistent):

```python

# Line 198-199: change from

if block.block_type == "paragraph" and block.content:

stripped = block.content.strip()

# To

if block.block_type == "paragraph":

stripped = (block.inline_content or block.content or "").strip()

```



**Also:** Add `"continuation"` to the context-preserving skip list (defensive, in case future parser changes assign a different block_type):



```python

# Line 215: add "continuation" to skip set

if block.block_type not in ("comment", "attribute_entry", "continuation"):

```



**Result:** All three `Specify` instances (root_disk, start_of_partition, partition_size) get flagged deterministically instead of relying on the LLM sniper.



---



## Gap 2: `_check_unit_consistency` — System-Level Mismatch



**File:** `rules/modular_compliance/structural_rules.py` (lines 342-434)



**Root cause:** `_UNIT_CONFLICTS` only maps same-scale pairs (MiB↔MB, GiB↔GB). When code uses `sizeMiB` (binary, MiB) and prose says "500 GB" (decimal, GB), the lookup for `gb` returns `gib` — but `gib` is NOT in `code_units` (which has `mib`). No flag fires.



The fix: detect binary/decimal **system** conflicts, not just same-scale conflicts. If code uses ANY binary unit and prose uses ANY decimal unit → flag.



**Changes:**



Add unit system sets:

```python

_BINARY_UNITS = frozenset({"kib", "mib", "gib", "tib"})

_DECIMAL_UNITS = frozenset({"kb", "mb", "gb", "tb"})

```



In `_check_unit_consistency`, after collecting `code_units`, classify the system:

```python

code_has_binary = bool(code_units & _BINARY_UNITS)

code_has_decimal = bool(code_units & _DECIMAL_UNITS)

```



In the prose-checking loop, add a system-level check AFTER the existing same-scale check:

```python

for m in _PROSE_UNIT_RE.finditer(content):

prose_unit = m.group(2).lower()



# Existing: same-scale conflict (MiB↔MB)

conflicting = _UNIT_CONFLICTS.get(prose_unit)

if conflicting and conflicting in code_units:

# ... existing issue creation ...

continue



# NEW: cross-scale system conflict (code=MiB, prose=GB)

prose_is_binary = prose_unit in _BINARY_UNITS

prose_is_decimal = prose_unit in _DECIMAL_UNITS

if (prose_is_decimal and code_has_binary) or (prose_is_binary and code_has_decimal):

code_system = "binary (KiB/MiB/GiB)" if code_has_binary else "decimal (KB/MB/GB)"

prose_system = "decimal" if prose_is_decimal else "binary"

# Create issue with cross-scale messaging

```



**Message for cross-scale:** "Unit system mismatch: prose uses 'GB' (decimal) but code blocks use binary units (MiB). Use consistent unit systems — either binary (KiB/MiB/GiB) or decimal (KB/MB/GB) throughout. (IBM Style Guide)"



**Suggestion:** "Change '500 GB' to the binary equivalent, or update the code block to use decimal units."



---



## Gap 3: Sharpen Abstract Prompt for Goal-Oriented Procedures



**File:** `app/llm/prompts.py` (lines 531-532)



**Root cause:** The current procedure guidance says `DO FLAG: abstracts that describe only WHAT without explaining WHY` — but the test.adoc abstract has a "to create..." clause, so the LLM treats it as having a WHY. The LLM misses that the abstract is **action-first** ("Apply X to create Y") instead of **goal-first** ("To create Y, apply X").



**Fix:** Sharpen the abstract flagging guidance in `_content_type_guidance()` procedure section:



Replace lines 531-532:

```python

"- DO FLAG: abstracts that describe only WHAT without explaining WHY "

"the action is important or beneficial to the user.\n"

```



With:

```python

"- DO FLAG: procedure abstracts that lead with the action instead of the "

"goal. The opening sentence should state WHY the user needs this task "

"before HOW to do it. Preferred: 'To [achieve goal], [perform action]' "

"(goal-first). Flag: '[perform action] to [achieve goal]' (action-first). "

"Example: write 'To share the /var/lib/containers partition between "

"stateroots, apply a MachineConfig...' not 'Apply a MachineConfig to "

"share the /var/lib/containers partition...'. (Red Hat SSG)\n"

```



---



## Critical Files



| File | Change |

|------|--------|

| `rules/modular_compliance/structural_rules.py` | Fix where-list (use inline_content), fix unit consistency (system-level check) |

| `app/llm/prompts.py` | Sharpen procedure abstract guidance (goal-first pattern) |

| `tests/rules/test_structural_rules.py` | Add tests for inline_content regex, cross-scale unit mismatch |



---



## Verification



1. `python -m pytest tests/rules/test_structural_rules.py -v` — all tests pass including new ones

2. `python -m pytest tests/rules/test_fp_guards.py -v` — no FP regressions

3. `python -m pytest tests/ -v` — full suite passes (497+ tests)

4. Re-analyze `test.adoc` — verify:

- "Specify" flagged 3 times (deterministic, not AI)

- "500 GB" flagged for MiB/GB system mismatch (deterministic)

- Abstract flagged for action-first pattern (AI)
# Structural Auditor: Upgrade CEA from Sentence Linter to Information Architecture Editor



## Context



CEA currently processes text block-by-block in isolation, looking at strings. The parser builds a rich `List[Block]` AST with `block_type`, `level`, `start_pos`, and structural metadata — but the deterministic engine discards this structure by iterating blocks one at a time (`_analyze_single_block_deterministic()`). This makes CEA blind to inter-block rules (admonition placement, section ordering, cross-referencing code-to-prose).



The user identified 5 true-positive gaps in `test.adoc` that all stem from this architectural limit. The fix is a **Structural Auditor** layer that operates on the `List[Block]` sequence deterministically, plus targeted LLM enhancements for semantic-only checks.



**Division of responsibilities:**

- **Syntax** (within a sentence) → Existing deterministic regex rules

- **Structure** (between blocks) → **New Structural Auditor** (this plan)

- **Semantics** (tone, intent) → LLM prompts (targeted, not structural)



---



## Change 1: Create Structural Auditor Pipeline Step



**File:** `app/services/analysis/orchestrator.py`



### 1a. New function: `_run_structural_analysis()`



Insert after `_run_deterministic_with_blocks()` (after line ~481). This function receives the full blocks array and runs structural sequence rules.



```python

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



from rules.modular_compliance.structural_rules import run_structural_rules

try:

issues = run_structural_rules(blocks, content_type, original_text)

logger.info("Structural analysis found %d issues", len(issues))

return issues

except (ImportError, ValueError, RuntimeError) as exc:

logger.warning("Structural analysis failed: %s", exc)

return []

```



### 1b. Wire into `analyze()` pipeline



In `analyze()` (around line 158), after `_run_deterministic_with_blocks()`:



```python

# Phase 1b: Structural analysis (inter-block rules)

parsed_blocks = prep.get("blocks", blocks or [])

structural_issues = _run_structural_analysis(

parsed_blocks, content_type, prep.get("original_text", text),

)

```



Then merge structural issues into `det_issues` before proceeding to LLM phases:



```python

det_issues = _merge_block_and_full_issues(block_det, full_det)

det_issues.extend(structural_issues) # Structural issues already in original coords

```



### 1c. Extract abstract block for targeted LLM analysis



In `analyze()`, after structural analysis but before the LLM global pass, extract the abstract (first paragraph after the first heading) and pass it to `_run_llm_global()` as `abstract_context`:



```python

# Extract abstract for targeted LLM short-description quality check

abstract_text = _extract_abstract(parsed_blocks)

```



New helper function in orchestrator:



```python

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

break # Non-paragraph content block = no clear abstract

return None

```



Thread `abstract_context` through `_run_llm_global()` → `analyze_global()` → `build_global_prompt()`:



```python

# In _run_llm_global signature, add:

abstract_context: str | None = None,



# Pass to analyze_global:

results = analyze_global(

global_text, content_type,

style_guide_excerpts=style_guide_excerpts,

document_outline=document_outline,

abstract_context=abstract_context,

)

```



---



## Change 2: Create Structural Rules Module



**New file:** `rules/modular_compliance/structural_rules.py`



This module contains the runner function and individual structural check functions. Each check operates on the `List[Block]` sequence.



```python

"""Structural sequence rules — inter-block deterministic analysis.



These rules inspect the ordering and relationships between blocks

in the parsed document, not individual block text. They enforce

Red Hat SSG and IBM Style Guide structural requirements.

"""



import logging

import re

import uuid

from typing import Any



from app.models.enums import IssueCategory, IssueSeverity

from app.models.schemas import IssueResponse



logger = logging.getLogger(__name__)





def run_structural_rules(

blocks: list,

content_type: str,

original_text: str,

) -> list[IssueResponse]:

"""Run all structural sequence checks on the block array.



Args:

blocks: Full list of parsed Block objects.

content_type: Modular documentation type.

original_text: Original document text.



Returns:

List of structural issues.

"""

issues: list[IssueResponse] = []



# Filter to analyzable blocks (skip comments, attributes, etc.)

content_blocks = [b for b in blocks if not b.should_skip_analysis]



issues.extend(_check_admonition_placement(content_blocks, original_text))

issues.extend(_check_where_list_specifies(content_blocks, original_text))

# Pre-compute inline code ranges per block for technical markup check.

# Reuses _compute_content_code_ranges from orchestrator.py (same function

# that powers in_code_range() for all 31 deterministic rules).

from app.services.analysis.orchestrator import _compute_content_code_ranges

block_code_ranges: dict[int, list[tuple[int, int]]] = {}

for i, b in enumerate(content_blocks):

block_code_ranges[i] = _compute_content_code_ranges(

b.inline_content or b.content or "", b.char_map,

)



# IMPORTANT: pass content_blocks (not unfiltered blocks) so enumerate()

# indices inside the function match block_code_ranges keys exactly.

issues.extend(_check_technical_term_markup(content_blocks, original_text, block_code_ranges))

issues.extend(_check_unit_consistency(content_blocks, original_text))



return issues

```



### 2a. Admonition Placement Check



```python

def _check_admonition_placement(

blocks: list,

original_text: str,

) -> list[IssueResponse]:

"""Flag admonitions that appear before the first paragraph (abstract).



Red Hat SSG p29: "Do not start a module or assembly with an

admonition, even when adding the Technology Preview admonition.

Always include a short description before including an admonition."



Logic: After the first heading, the next content block must be

a paragraph (the abstract), not an admonition. Also catches

document fragments that start with an admonition before any title.

"""

issues: list[IssueResponse] = []

found_heading = False

found_paragraph_after_heading = False



for block in blocks:

# Pre-heading admonition: module starts with admonition before title

if not found_heading and block.block_type == "admonition":

admonition_text = (block.content or "")[:80]

issues.append(IssueResponse(

id=str(uuid.uuid4()),

source="deterministic",

category=IssueCategory.STRUCTURE,

rule_name="admonition_placement",

message=(

"Do not start a module with an admonition. A title and "

"short description (abstract) must appear before the "

"first admonition. (Red Hat SSG)"

),

severity=IssueSeverity.HIGH,

flagged_text=admonition_text,

sentence=admonition_text,

sentence_index=0,

suggestions=[

"Add a title and short description paragraph before "

"this admonition.",

],

span=[block.start_pos, block.start_pos + len(admonition_text)],

confidence=0.95,

))

return issues # One flag is enough



if block.block_type == "heading":

found_heading = True

found_paragraph_after_heading = False

continue



if not found_heading:

continue



# Skip non-content blocks (block titles, attributes, etc.)

if block.block_type in ("attribute_entry", "comment", "block_title"):

continue



if block.block_type == "paragraph":

found_paragraph_after_heading = True

continue



if block.block_type == "admonition" and not found_paragraph_after_heading:

# Admonition appears before any paragraph after heading

admonition_text = (block.content or "")[:80]

issues.append(IssueResponse(

id=str(uuid.uuid4()),

source="deterministic",

category=IssueCategory.STRUCTURE,

rule_name="admonition_placement",

message=(

"Do not start a module with an admonition. Include a short "

"description (abstract) between the title and the first "

"admonition. (Red Hat SSG)"

),

severity=IssueSeverity.HIGH,

flagged_text=admonition_text,

sentence=admonition_text,

sentence_index=0,

suggestions=[

"Add a short description paragraph before this admonition.",

"The abstract should describe WHAT the user will do and "

"WHY it matters.",

],

span=[block.start_pos, block.start_pos + len(admonition_text)],

confidence=0.95,

))

break # Only flag the first occurrence per heading



return issues

```



### 2b. Where-List "Specifies" Check



```python

# Regex: backtick-wrapped variable followed by colon/dash and "Specify" (not "Specifies")

# Supports both `: Specify` and `- Specify` separators (Red Hat uses both)

_SPECIFY_PATTERN = re.compile(

r'`[^`]+`\s*[:：\-–—]\s*Specify\b(?!ing|ies)',

)





def _check_where_list_specifies(

blocks: list,

original_text: str,

) -> list[IssueResponse]:

"""Flag variable descriptions using 'Specify' instead of 'Specifies'.



Red Hat SSG p20: "Introduce definition lists with 'where:' and

begin each variable description with 'Specifies'."



Logic: Find paragraph blocks containing "Where:" or "where:".

Check subsequent list items for "Specify" vs "Specifies".

"""

issues: list[IssueResponse] = []

in_where_context = False



for block in blocks:

# Detect "Where:" paragraph

if block.block_type == "paragraph" and block.content:

stripped = block.content.strip()

if re.search(r'\bwhere\s*:\s*$', stripped, re.IGNORECASE):

in_where_context = True

continue

else:

in_where_context = False



# Check list items after "Where:"

if not in_where_context:

continue



if block.block_type not in (

"list_item_unordered", "list_item_ordered",

"list_item", "paragraph",

):

# Non-list block ends the "Where:" context

if block.block_type not in ("comment", "attribute_entry"):

in_where_context = False

continue



content = block.content or ""

match = _SPECIFY_PATTERN.search(content)

if match:

# Find "Specify" within the match to get precise span

specify_start = content.find("Specify", match.start())

if specify_start >= 0:

# Map to original text coordinates

orig_pos = block.start_pos + specify_start

issues.append(IssueResponse(

id=str(uuid.uuid4()),

source="deterministic",

category=IssueCategory.STRUCTURE,

rule_name="where_list_format",

message=(

"Use 'Specifies' (third person declarative) instead "

"of 'Specify' (imperative) in variable description "

"lists after 'Where:'. (Red Hat SSG)"

),

severity=IssueSeverity.LOW,

flagged_text="Specify",

sentence=content.strip(),

sentence_index=0,

suggestions=[

"Change 'Specify' to 'Specifies'.",

],

span=[orig_pos, orig_pos + 7],

confidence=0.95,

))



return issues

```



### 2c. Technical Term Markup Check



```python

# Technical terms that must be in backtick monospace (Red Hat/OpenShift ecosystem)

_TECHNICAL_TERMS = frozenset({

"ostree", "rpm-ostree", "systemd", "bootc", "podman", "buildah",

"skopeo", "crio", "crictl", "kubelet", "etcd", "coredns",

"haproxy", "keepalived", "firewalld", "NetworkManager",

"nmcli", "nmstatectl", "butane", "ignition", "coreos",

"rhcos", "fcos", "microshift", "crun", "runc",

})



# Pattern: word boundary + term + word boundary, case-insensitive

# to catch "Ostree" at sentence start, "SYSTEMD" in caps, etc.

_TERM_PATTERN = re.compile(

r'\b(' + '|'.join(re.escape(t) for t in _TECHNICAL_TERMS) + r')\b',

re.IGNORECASE,

)





def _check_technical_term_markup(

blocks: list,

original_text: str,

block_code_ranges: dict[int, list[tuple[int, int]]],

) -> list[IssueResponse]:

"""Flag technical terms in prose that lack backtick formatting.



IBM Style Guide p184-191: Commands, utilities, and system

components should use monospace formatting.



Logic: Search paragraph/heading content for known technical terms.

Uses pre-computed inline code ranges (from _compute_content_code_ranges)

and in_code_range() to verify the term is NOT already inside backticks.

This is the same guard logic used by all 31 deterministic rules.



IMPORTANT: ``blocks`` must be the same filtered list used to build

``block_code_ranges`` (i.e., ``content_blocks`` from the caller).

Passing the unfiltered block list will cause index mismatches.

"""

from rules.base_rule import in_code_range



issues: list[IssueResponse] = []

seen_terms: set[str] = set() # Deduplicate across blocks



for idx, block in enumerate(blocks):

if block.block_type not in ("paragraph", "heading", "preamble"):

continue



content = block.content or ""

code_ranges = block_code_ranges.get(idx, [])



for match in _TERM_PATTERN.finditer(content):

term = match.group(1)



# Skip if already flagged this term

if term.lower() in seen_terms:

continue



# Skip if term is inside inline code (backticks)

# Uses the same in_code_range() guard as all deterministic rules

if in_code_range(match.start(), code_ranges):

continue



seen_terms.add(term.lower())

orig_pos = block.start_pos + match.start()

issues.append(IssueResponse(

id=str(uuid.uuid4()),

source="deterministic",

category=IssueCategory.TECHNICAL,

rule_name="technical_markup",

message=(

f"Format '{term}' as inline code (`{term}`) — technical "

f"terms, commands, and system components should use "

f"monospace formatting. (IBM Style Guide)"

),

severity=IssueSeverity.LOW,

flagged_text=term,

sentence=content.strip()[:120],

sentence_index=0,

suggestions=[f"`{term}`"],

span=[orig_pos, orig_pos + len(term)],

confidence=0.9,

))



return issues

```



### 2d. Unit Consistency Check (Code Block vs. Prose)



```python

# Binary unit prefixes in code

_CODE_UNIT_RE = re.compile(

r'\b(size|capacity|limit|max|min|memory|disk|storage|partition)'

r'[_-]?'

r'(Ki?B|Mi?B|Gi?B|Ti?B|bytes?|KB|MB|GB|TB)\b',

re.IGNORECASE,

)



# Units mentioned in prose

_PROSE_UNIT_RE = re.compile(

r'(\d+[\d,.]*)\s*(KiB|MiB|GiB|TiB|KB|MB|GB|TB|bytes?)\b',

re.IGNORECASE,

)



# Binary ↔ decimal mismatch pairs

_UNIT_CONFLICTS = {

"kib": "kb", "kb": "kib",

"mib": "mb", "mb": "mib",

"gib": "gb", "gb": "gib",

"tib": "tb", "tb": "tib",

}





def _check_unit_consistency(

blocks: list,

original_text: str,

) -> list[IssueResponse]:

"""Flag mismatched binary/decimal units between code blocks and prose.



IBM Style Guide p161-164: Use consistent unit prefixes.

Binary prefixes (KiB, MiB, GiB) must not be mixed with decimal

prefixes (KB, MB, GB) for the same quantity.



Logic: Extract unit references from code blocks. Check adjacent

paragraphs for conflicting unit prefixes.

"""

issues: list[IssueResponse] = []



# Collect units from code blocks

code_units: set[str] = set()

for block in blocks:

if block.block_type in ("code_block", "listing", "literal"):

raw = block.raw_content or block.content or ""

for m in _CODE_UNIT_RE.finditer(raw):

code_units.add(m.group(2).lower())

# Also check for bare unit field names like "sizeMiB"

for m in re.finditer(r'(MiB|GiB|KiB|TiB|MB|GB|KB|TB)', raw):

code_units.add(m.group(1).lower())



if not code_units:

return issues



# Check prose blocks for conflicting units

for block in blocks:

if block.block_type not in ("paragraph", "list_item_unordered",

"list_item_ordered", "list_item"):

continue



content = block.content or ""

for m in _PROSE_UNIT_RE.finditer(content):

prose_unit = m.group(2).lower()

conflicting = _UNIT_CONFLICTS.get(prose_unit)

if conflicting and conflicting in code_units:

orig_pos = block.start_pos + m.start()

flagged = m.group(0)

issues.append(IssueResponse(

id=str(uuid.uuid4()),

source="deterministic",

category=IssueCategory.NUMBERS,

rule_name="unit_consistency",

message=(

f"Unit mismatch: prose uses '{m.group(2)}' but code "

f"blocks use '{conflicting.upper()}'. Use consistent "

f"unit prefixes — do not mix binary (KiB/MiB/GiB) "

f"with decimal (KB/MB/GB). (IBM Style Guide)"

),

severity=IssueSeverity.MEDIUM,

flagged_text=flagged,

sentence=content.strip()[:120],

sentence_index=0,

suggestions=[

f"Change '{m.group(2)}' to '{conflicting.upper()}' "

f"to match the code block units.",

],

span=[orig_pos, orig_pos + len(flagged)],

confidence=0.85,

))



return issues

```



---



## Change 3: Enhance LLM Prompts for Semantic-Only Checks



These are the checks that genuinely need LLM judgment — not structural ordering.



**File:** `app/llm/prompts.py`



### 3a. Add short description quality check to global prompt (line ~340)



Append to CHECK list after accessibility check (7). When `abstract_context` is provided, inject it as a dedicated variable so the LLM examines the exact abstract block:



```python

"(8) short description quality — every module must have a short "

"description (abstract) that includes both WHAT the user will do "

"and WHY it is important or beneficial. Abstracts should be 2-3 "

"sentences, use active voice, avoid self-referential language "

"('This topic covers...'), and avoid feature-focused language "

"('This product allows you to...'). Use customer-centric language "

"('You can... by...' or 'To..., configure...'). "

```



Add `abstract_context` parameter to `build_global_prompt()` signature. When present, append to the user prompt:



```python

# In build_global_prompt, add parameter: abstract_context: str | None = None

# Then in user_prompt construction:

if abstract_context:

user_prompt += (

f"\n\n## Module Abstract (evaluate for short description quality)\n"

f"{abstract_context}\n"

)

```



This forces the LLM to look exactly where the violation occurs rather than scanning the full document.



### 3b. Enhance procedure content-type guidance (line ~508)



Append to existing procedure guidance:



```python

"- DO FLAG: abstracts that describe only WHAT without explaining WHY "

"the action is important or beneficial to the user.\n"

"- DO FLAG: definition lists after 'Where:' where variable descriptions "

"start with 'Specify' instead of 'Specifies' (Red Hat SSG requires "

"'Specifies' for variable descriptions).\n"

```



### 3c. Add technical term formatting to granular CHECK list (line ~262)



Append after anthropomorphism check:



```python

"technical term formatting — technical terms, commands, utilities, "

"and system components mentioned in prose should use backtick "

"formatting (e.g., 'ostree' should be `ostree`), "

```



### Rationale:

- Short description quality is a judgment call (what vs why) → LLM appropriate

- "Specifies" and technical markup are deterministic (Change 2) but LLM provides defense-in-depth

- Structural checks (admonition placement, unit consistency) are NOT in LLM prompts — handled 100% deterministically in Change 2



---



## Change 4: Add `enforcement_type` to Style Guide Mappings (Future-Proofing)



**Files:** `style_guides/ibm/ibm_style_mapping.yaml`, `style_guides/red_hat/red_hat_style_mapping.yaml`



Add an `enforcement_type` field to each rule entry. Three values:



| Type | Meaning | Handler |

|------|---------|---------|

| `token_match` | Word swaps, regex patterns | Existing deterministic rules |

| `structural` | Document ordering, block relationships | New Structural Auditor |

| `semantic_llm` | Tone, flow, intent quality | LLM prompts |



### Example additions to `red_hat_style_mapping.yaml`:



```yaml

admonition_placement:

rule_id: "admonition_placement"

display_name: "Admonition Placement"

category: "formatting"

severity: "high"

enforcement_type: "structural" # ← NEW

red_hat_ssg:

topic: "Admonitions"

section: "admonitions"

verification_status: "verified"

guidance: "Do not start a module with an admonition. Always include a short description before including an admonition."



where_list_format:

rule_id: "where_list_format"

display_name: "Where List Format"

category: "formatting"

severity: "low"

enforcement_type: "structural" # ← NEW

red_hat_ssg:

topic: "Explanation of commands and variables"

section: "commands-variables"

verification_status: "verified"

guidance: "Introduce definition lists with 'where:' and begin each variable description with 'Specifies'."



unit_consistency:

rule_id: "unit_consistency"

display_name: "Unit Consistency"

category: "numbers_and_measurement"

severity: "medium"

enforcement_type: "structural" # ← NEW

ibm_style:

topic: "Units of measurement"

pages: [161, 162, 163, 164]

verification_status: "verified"

guidance: "Use consistent unit prefixes. Do not mix binary (KiB, MiB, GiB) with decimal (KB, MB, GB)."



technical_markup:

rule_id: "technical_markup"

display_name: "Technical Term Markup"

category: "technical_elements"

severity: "low"

enforcement_type: "token_match" # ← NEW (deterministic pattern)

ibm_style:

topic: "Technical elements formatting"

pages: [184, 185, 186, 187, 188, 189, 190, 191]

verification_status: "verified"

guidance: "Use monospace formatting for command names, file paths, package names, and system components."

```



### Add `enforcement_type` to existing entries:



Tag the existing 20 Red Hat SSG entries and key IBM entries with their enforcement type. This is an incremental audit — we tag the critical rules first, then sweep the remaining 124 IBM entries over time.



---



## Change 5: Add Tests



### `tests/rules/test_structural_rules.py` (NEW FILE)



```python

"""Tests for inter-block structural analysis rules."""

import pytest

from app.services.parsing.base import Block





def _make_block(block_type, content, start_pos=0, level=0, skip=False):

"""Helper to create test Block objects."""

return Block(

block_type=block_type,

content=content,

raw_content=content,

start_pos=start_pos,

end_pos=start_pos + len(content),

level=level,

should_skip_analysis=skip,

)





class TestAdmonitionPlacement:

"""Verify admonition placement structural check."""



def test_admonition_after_heading_flagged(self) -> None:

blocks = [

_make_block("heading", "Configuring shared partition", 0, level=1),

_make_block("admonition", "You must complete this at install time.", 50),

]

from rules.modular_compliance.structural_rules import _check_admonition_placement

issues = _check_admonition_placement(blocks, "")

assert len(issues) == 1

assert "admonition" in issues[0].message.lower()



def test_admonition_after_paragraph_ok(self) -> None:

blocks = [

_make_block("heading", "Title", 0, level=1),

_make_block("paragraph", "This is the abstract.", 20),

_make_block("admonition", "Important note.", 60),

]

from rules.modular_compliance.structural_rules import _check_admonition_placement

issues = _check_admonition_placement(blocks, "")

assert len(issues) == 0



def test_skipped_blocks_ignored(self) -> None:

blocks = [

_make_block("heading", "Title", 0, level=1),

_make_block("attribute_entry", ":context: value", 20),

_make_block("paragraph", "Abstract text.", 40),

_make_block("admonition", "Note.", 70),

]

from rules.modular_compliance.structural_rules import _check_admonition_placement

issues = _check_admonition_placement(blocks, "")

assert len(issues) == 0





class TestWhereListSpecifies:

"""Verify Where: list formatting check."""



def test_specify_flagged_after_where(self) -> None:

blocks = [

_make_block("paragraph", "Where:", 0),

_make_block("list_item_unordered", "`<root_disk>`: Specify the root disk.", 10),

]

from rules.modular_compliance.structural_rules import _check_where_list_specifies

issues = _check_where_list_specifies(blocks, "")

assert len(issues) == 1

assert "Specifies" in issues[0].message



def test_specifies_not_flagged(self) -> None:

blocks = [

_make_block("paragraph", "Where:", 0),

_make_block("list_item_unordered", "`<root_disk>`: Specifies the root disk.", 10),

]

from rules.modular_compliance.structural_rules import _check_where_list_specifies

issues = _check_where_list_specifies(blocks, "")

assert len(issues) == 0



def test_no_where_context_not_flagged(self) -> None:

blocks = [

_make_block("paragraph", "Some other text.", 0),

_make_block("list_item_unordered", "`<var>`: Specify something.", 20),

]

from rules.modular_compliance.structural_rules import _check_where_list_specifies

issues = _check_where_list_specifies(blocks, "")

assert len(issues) == 0





class TestUnitConsistency:

"""Verify unit consistency check between code and prose."""



def test_mib_vs_gb_flagged(self) -> None:

blocks = [

_make_block("code_block", "sizeMiB: 500000", 0, skip=True),

_make_block("paragraph", "Specify a minimum size of 500 GB.", 30),

]

# Override should_skip_analysis for code block in content_blocks filter

from rules.modular_compliance.structural_rules import _check_unit_consistency

issues = _check_unit_consistency(blocks, "")

assert len(issues) == 1

assert "mismatch" in issues[0].message.lower()



def test_consistent_units_ok(self) -> None:

blocks = [

_make_block("code_block", "sizeMiB: 500000", 0, skip=True),

_make_block("paragraph", "Specify a minimum size of 500 MiB.", 30),

]

from rules.modular_compliance.structural_rules import _check_unit_consistency

issues = _check_unit_consistency(blocks, "")

assert len(issues) == 0





class TestTechnicalMarkup:

"""Verify technical term backtick check."""



def test_ostree_without_backticks_flagged(self) -> None:

blocks = [

_make_block("heading", "Configuring ostree stateroots", 0, level=1),

]

from rules.modular_compliance.structural_rules import _check_technical_term_markup

# No code ranges — term is not inside backticks

block_code_ranges = {0: []}

issues = _check_technical_term_markup(blocks, "", block_code_ranges)

assert len(issues) == 1

assert "ostree" in issues[0].flagged_text



def test_term_in_backticks_not_flagged(self) -> None:

blocks = [

_make_block("paragraph", "Configure the ostree stateroots.", 0),

]

from rules.modular_compliance.structural_rules import _check_technical_term_markup

# Simulate code ranges covering the "ostree" position (index 14-20)

# as _compute_content_code_ranges would produce from inline_content

# "Configure the `ostree` stateroots."

block_code_ranges = {0: [(14, 20)]}

issues = _check_technical_term_markup(blocks, "", block_code_ranges)

assert len(issues) == 0

```



### `tests/llm/test_prompts.py` — add prompt content tests



```python

def test_global_prompt_includes_short_description_check(self) -> None:

from app.llm.prompts import build_global_prompt

sys_prompt, _ = build_global_prompt("text", "procedure", [])

assert "short description" in sys_prompt.lower()



def test_granular_prompt_includes_technical_term_check(self) -> None:

from app.llm.prompts import build_granular_prompt

sys_prompt, _ = build_granular_prompt("text", ["text"], [])

assert "technical term" in sys_prompt.lower()



def test_procedure_guidance_includes_specifies(self) -> None:

from app.llm.prompts import _content_type_guidance

guidance = _content_type_guidance("procedure")

assert "Specifies" in guidance

```



---



## Critical Files



| File | Change | Type |

|------|--------|------|

| `rules/modular_compliance/structural_rules.py` | **NEW** — 4 structural checks (admonition, where-list, tech markup, units) | New file |

| `app/services/analysis/orchestrator.py` | Add `_run_structural_analysis()` + wire into `analyze()` pipeline | Edit (~10 lines) |

| `app/llm/prompts.py` | Add short description quality (global), tech term formatting (granular), procedure guidance | Edit (~15 lines) |

| `style_guides/red_hat/red_hat_style_mapping.yaml` | Add 4 new rule entries with `enforcement_type` tags | Edit |

| `style_guides/ibm/ibm_style_mapping.yaml` | Add `enforcement_type` to unit_consistency and technical_markup entries | Edit |

| `tests/rules/test_structural_rules.py` | **NEW** — 10+ tests for structural rules | New file |

| `tests/llm/test_prompts.py` | Add 3 prompt content tests | Edit |



---



## Verification



1. `python -m pytest tests/ -v` — all existing + new tests pass

2. Run `test.adoc` analysis end-to-end — verify all 5 gaps caught:

- **Admonition placement** → Deterministic structural rule (100% accuracy)

- **"Specify" → "Specifies"** → Deterministic structural rule (100% accuracy)

- **Unit mismatch (MiB vs GB)** → Deterministic structural rule (100% accuracy)

- **`ostree` missing backticks** → Deterministic structural rule (100% accuracy)

- **Short description quality** → LLM global prompt (semantic judgment)

3. Verify zero false positives on existing test fixtures (`tests/fixtures/errors_sample.adoc`)

4. Verify structural rules produce spans that map correctly to original text

5. Verify `enforcement_type` tags don't break existing YAML loading (field is additive)
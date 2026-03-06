# E2E Style Guide Coverage: Excerpt Pipeline + Gap Analysis + Structural Rules



## Context



CEA has 111 deterministic rules, 1,200+ term corrections, and 192 rule mappings — but the **excerpt fields are empty** across all 192 rules. The entire excerpt infrastructure (registry, selector, prompt injection, citations API) is built and operational, falling back to 1-2 sentence `guidance` strings because `scripts/extract_excerpts.py` is 100% stubs. Implementing this script is the single highest-leverage task: it enriches every LLM prompt without writing any new rules.



Additionally, Red Hat SSG coverage is thin (20 mappings vs ~50 needed), and 6 structural rules remain unimplemented. The user wants all three workstreams executed in parallel with PDFs available on disk.



**Current state:**

- 192 rule mappings with 0 excerpt fields populated (all use `guidance` fallback)

- `scripts/extract_excerpts.py` — 5 functions, all stubs returning `""`, `[]`, `{}`

- 663 A-Z word usage terms (estimated ~150-300 missing from IBM PDF pp.284-419)

- 20 Red Hat SSG mappings (estimated ~30 unmapped topics)

- 4 structural rules implemented (admonition, where-list, tech markup, units)



---



## Workstream 1: Implement `scripts/extract_excerpts.py`



**File:** `scripts/extract_excerpts.py` (all stubs → full implementation)



### 1a. `extract_pdf_text(pdf_path, page_numbers) -> str`



Currently returns `""`. Implement with PyMuPDF:



```python

import fitz # PyMuPDF



def extract_pdf_text(pdf_path: Path, page_numbers: List[int]) -> str:

doc = fitz.open(str(pdf_path))

pages_text = []



# First pass: detect repeated text (headers/footers/watermarks)

block_counts: dict[str, int] = {}

for pn in page_numbers:

page = doc[pn - 1] # 1-based → 0-based

rect = page.rect

margin_y = rect.height * 0.08

clip = fitz.Rect(rect.x0, rect.y0 + margin_y, rect.x1, rect.y1 - margin_y)

for block in page.get_text("blocks", clip=clip, sort=True):

key = block[4].strip()[:80]

block_counts[key] = block_counts.get(key, 0) + 1



repeated = {k for k, v in block_counts.items() if v >= 3 and len(page_numbers) >= 3}



# Second pass: extract text excluding repeated blocks

for pn in page_numbers:

page = doc[pn - 1]

rect = page.rect

margin_y = rect.height * 0.08

clip = fitz.Rect(rect.x0, rect.y0 + margin_y, rect.x1, rect.y1 - margin_y)

blocks = page.get_text("blocks", clip=clip, sort=True)

# PyMuPDF sort=True handles columns natively (left-to-right, top-to-bottom)

page_text = []

for block in blocks:

text = block[4].strip()

if text[:80] not in repeated and len(text) > 5:

page_text.append(text)

pages_text.append("\n".join(page_text))



doc.close()

return "\n\n".join(pages_text)

```



Key decisions:

- Margin crop: 8% top/bottom (per CLAUDE.md spec)

- Repeated text: blocks appearing 3+ times across pages → excluded

- Column handling: use PyMuPDF's built-in `sort=True` parameter (handles columns natively). If garbled output detected on first run, fall back to manual 5px y-binning

- Page numbers are 1-based (matches YAML `pages` fields), converted to 0-based for fitz



### 1b. `extract_xlsx_data(xlsx_path) -> List[Dict]`



```python

import openpyxl



def extract_xlsx_data(xlsx_path: Path) -> List[Dict[str, Any]]:

wb = openpyxl.load_workbook(str(xlsx_path), read_only=True, data_only=True)

ws = wb.active

headers = [cell.value for cell in next(ws.iter_rows(min_row=1, max_row=1))]

entries = []

for row in ws.iter_rows(min_row=2, values_only=True):

try:

entry = dict(zip(headers, row))

# Skip blank spacer rows and rows with no product name

if not entry.get("product_name"):

continue

entries.append(entry)

except (TypeError, ValueError) as exc:

# Merged cells or malformed rows — log and skip

logger.debug("Skipping malformed XLSX row: %s", exc)

continue

wb.close()

return entries

```



### 1c. `extract_markdown_sections(md_path) -> Dict[str, str]`



```python

import re



def extract_markdown_sections(md_path: Path) -> Dict[str, str]:

text = md_path.read_text(encoding="utf-8")

sections: Dict[str, str] = {}

current_heading = None

current_content: list[str] = []



for line in text.splitlines():

match = re.match(r'^(#{1,3})\s+(.+)', line)

if match:

if current_heading:

sections[current_heading] = "\n".join(current_content).strip()

current_heading = match.group(2).strip()

current_content = []

elif current_heading is not None:

current_content.append(line)



if current_heading:

sections[current_heading] = "\n".join(current_content).strip()



return sections

```



### 1d. `update_yaml_excerpts(yaml_path, excerpts) -> None`



```python

def update_yaml_excerpts(yaml_path: Path, excerpts: Dict[str, str]) -> None:

with open(yaml_path, 'r', encoding='utf-8') as f:

data = yaml.safe_load(f) or {}



updated = 0

for category_key, category_data in data.items():

if not isinstance(category_data, dict):

continue

# Handle nested rule entries (category -> rule_id -> ...)

for rule_key, rule_data in category_data.items():

if not isinstance(rule_data, dict):

continue

rule_id = rule_data.get("rule_id", rule_key)

if rule_id in excerpts:

# Find the guide sub-dict (ibm_style, red_hat_ssg, etc.)

for guide_key in ("ibm_style", "red_hat_ssg", "modular_docs", "accessibility"):

if guide_key in rule_data:

rule_data[guide_key]["excerpt"] = excerpts[rule_id]

updated += 1

break



with open(yaml_path, 'w', encoding='utf-8') as f:

yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)



logger.info("Updated %d excerpt fields in %s", updated, yaml_path)

```



### 1e. `main()` orchestration



Wire up the stubs to process each source document:



1. **IBM PDF**: Load `ibm_style_mapping.yaml`, iterate rules with `pages` fields, call `extract_pdf_text()` for each page set, truncate to 800 chars (focused on topic heading + 2-3 paragraphs), write back via `update_yaml_excerpts()`

2. **Red Hat PDF**: Same flow for `red_hat_style_mapping.yaml`

3. **Modular Docs PDF**: Same flow for `modular_docs_mapping.yaml`

4. **Accessibility MD**: Call `extract_markdown_sections()`, map sections to rule IDs

5. **Product Names XLSX**: Call `extract_xlsx_data()`, generate merge candidates for `product_names_config.yaml`



**Excerpt truncation**: Each excerpt should be 100-200 tokens (400-800 chars). Longer excerpts dilute signal in the LLM prompt. The current token budget (100K) can handle 192 rules × 200 tokens = ~38K tokens comfortably.



---



## Workstream 2: Gap Analysis Script



**New file:** `scripts/gap_analysis.py`



### 2a. A-Z Word List Gap Analysis



Parse IBM PDF pages 284-419 (the A-Z word usage section):



1. Extract all headword entries from the A-Z section using pattern matching

2. Load all existing term configs (`word_usage_config.yaml`, `do_not_use_config.yaml`, `terminology_config.yaml`, `simple_words_config.yaml`)

3. Build coverage sets and diff

4. Output:

- Missing terms (in PDF, not in YAML) with auto-generated YAML snippets

- Coverage percentage per letter

- Priority candidates (terms marked "Do not use" that are missing)



```

$ python scripts/gap_analysis.py \

--ibm-pdf style_guides/ibm/ibm-style-documentation.pdf \

--output-report gap_report.md

```



### 2b. Chapter-to-Rule Coverage Audit



1. Extract PDF table of contents or heading structure from pages 1-283

2. Map each chapter to existing rule IDs in `ibm_style_mapping.yaml`

3. Classify gaps: "needs rule", "covered by LLM", "informational only"

4. Generate a coverage matrix



### 2c. Red Hat SSG Topic Coverage



1. Parse Red Hat SSG PDF or use section headings from known structure

2. Compare against 20 existing mappings

3. Identify unmapped sections with classification



---



## Workstream 3: Expand Red Hat SSG Mappings + Structural Rules



### 3a. Expand Red Hat YAML from 20 to ~50 entries



**File:** `style_guides/red_hat/red_hat_style_mapping.yaml`



Missing topic areas to add (grouped by category):



**Grammar/Language (~8 new):**

- `date_format` — Red Hat uses DD Month YYYY

- `numbers_red_hat` — Red Hat-specific numbering

- `pronouns_red_hat` — gender-neutral guidance

- `passive_voice` — stricter than IBM for procedures

- `sentence_length` — max 25 words recommended

- `verb_tense` — present tense required

- `spelling` — US English overrides

- `prepositions_red_hat` — specific phrasal verbs



**Product-specific (~10 new):**

- `product_names_ansible`, `product_names_rhel_ai`, `product_names_openshift_ai`

- `product_names_middleware`, `product_names_storage`, `product_names_virtualization`

- `product_names_cloud_services`, `product_names_networking`

- `product_names_security`, `product_names_developer_tools`



**Technical content (~6 new):**

- `api_references`, `yaml_json_examples`, `container_pod_references`

- `operator_references`, `crd_terminology`, `cli_output_formatting`



**Content structure (~6 new):**

- `prerequisites_format`, `verification_format`, `additional_resources`

- `assembly_structure`, `module_attributes`, `title_format`



Each entry follows the existing pattern:

```yaml

date_format:

rule_id: "date_format"

display_name: "Date Format"

category: "numbers_and_measurement"

severity: "medium"

enforcement_type: "token_match"

red_hat_ssg:

topic: "Date formats"

section: "date-formats"

verification_status: "verified"

guidance: "Use DD Month YYYY format (e.g., 15 January 2025)."

```



### 3b. New Structural Rules (6 rules)



**File:** `rules/modular_compliance/structural_rules.py`



Add to `run_structural_rules()` and create individual check functions:



**Rule 1: `heading_level_skip`** (Priority 1 — low FP risk)

- Heading levels must not skip (h1→h3 without h2)

- Track level across blocks, flag when `current > previous + 1`

- **Edge case**: AsciiDoc heading levels are 1-based (count of `=` symbols): `= Title` → level 1, `== Section` → level 2. Block titles (`.Prerequisites`) → level 0. The check must: (a) skip level 0 blocks (they're labels, not structural headings), (b) only compare consecutive non-zero heading levels, (c) allow `1 → 2` as normal progression

- Source: IBM p181-183



**Rule 2: `prerequisites_position`** (Priority 1 — low FP risk)

- In procedures, `.Prerequisites` must appear before `.Procedure`

- Track block_title ordering

- Source: Modular Docs Reference Guide

- Only fires for `content_type == "procedure"`



**Rule 3: `empty_section`** (Priority 1 — low FP risk)

- Flag headings with no content before the next heading

- Track heading blocks, check for intervening content

- Source: IBM p181



**Rule 4: `admonition_stacking`** (Priority 2 — low FP risk)

- Flag 2+ consecutive admonition blocks without prose between them

- Track consecutive admonitions

- Source: Red Hat SSG



**Rule 5: `procedure_step_count`** (Priority 2 — medium FP risk)

- Flag procedures with >10 consecutive ordered list items

- Severity: LOW (advisory, not error)

- Source: Minimalism principles



**Rule 6: `verification_section`** (Priority 2 — medium FP risk)

- Procedure modules should include `.Verification` block title

- Only fires for `content_type == "procedure"`

- Source: Modular Docs Reference Guide



Each follows the established pattern:

```python

def _check_heading_level_skip(

blocks: list, original_text: str,

) -> list[IssueResponse]:

...

```



Register in `run_structural_rules()`:

```python

issues.extend(_check_heading_level_skip(content_blocks, original_text))

issues.extend(_check_prerequisites_position(content_blocks, original_text, content_type))

issues.extend(_check_empty_section(content_blocks, original_text))

issues.extend(_check_admonition_stacking(content_blocks, original_text))

issues.extend(_check_procedure_step_count(content_blocks, original_text, content_type))

issues.extend(_check_verification_section(content_blocks, original_text, content_type))

```



Note: `run_structural_rules()` signature already has `content_type` — thread it to rules that need it. `preprocessor._detect_content_type()` already handles detection (`:_mod-docs-content-type:` attribute first, falls back to structural markers like `.Procedure`/`.Prerequisites`). Add a `logger.debug` when `content_type` is empty/unknown to catch detection failures. The procedure-specific rules (`prerequisites_position`, `verification_section`) will simply not fire when `content_type != "procedure"` — safe default behavior.



### 3c. YAML Mapping Entries for New Structural Rules



Add to `red_hat_style_mapping.yaml` under `structural:`:

```yaml

heading_level_skip:

rule_id: "heading_level_skip"

display_name: "Heading Level Skip"

category: "structure_and_format"

severity: "medium"

enforcement_type: "structural"



prerequisites_position:

rule_id: "prerequisites_position"

...

```



Also add to `ibm_style_mapping.yaml` where applicable (heading_level_skip, empty_section).



---



## Critical Files



| File | Change | Workstream |

|------|--------|------------|

| `scripts/extract_excerpts.py` | Implement 5 stub functions + main orchestration | 1 |

| `scripts/gap_analysis.py` | **NEW** — A-Z diff + chapter coverage audit | 2 |

| `style_guides/ibm/ibm_style_mapping.yaml` | Populate `excerpt` fields (post-extraction) + new structural entries | 1, 3 |

| `style_guides/red_hat/red_hat_style_mapping.yaml` | Expand from 20→~50 entries + populate excerpts + structural entries | 1, 3 |

| `rules/modular_compliance/structural_rules.py` | Add 6 structural check functions + register in runner | 3 |

| `rules/word_usage/config/word_usage_config.yaml` | Merge ~150-300 new terms (from gap analysis output) | 2 |

| `tests/rules/test_structural_rules.py` | Add tests for 6 new structural rules | 3 |

| `tests/scripts/test_extract_excerpts.py` | **NEW** — unit tests for extraction functions | 1 |

| `style_guides/registry.py` | Swap guide order: Red Hat before IBM (override hierarchy fix) | 3 |



---



## Verification



1. **Extract excerpts**: `python scripts/extract_excerpts.py --ibm-pdf <path> --output-dir style_guides/` — verify `excerpt` fields populated in YAMLs

2. **Gap analysis**: `python scripts/gap_analysis.py --ibm-pdf <path>` — review gap report for missing terms

3. **Structural rules tests**: `python -m pytest tests/rules/test_structural_rules.py -v` — all tests pass

4. **Full test suite**: `python -m pytest tests/ -v` — 475+ tests pass, zero regressions

5. **FP guards**: `python -m pytest tests/rules/test_fp_guards.py -v` — new structural rules pass FP tests

6. **End-to-end**: Run analysis on `test.adoc` — verify new structural issues appear, excerpt-enriched LLM results are higher quality

7. **Excerpt verification**: Check that `GET /api/v1/citations/<rule_type>` returns populated excerpt text (not just guidance fallback)



---



## Override Hierarchy



Per CLAUDE.md: **Red Hat SSG overrides IBM** when conflicting.



**Bug found**: `style_guides/registry.py` line 27-32 lists IBM **first** in `_GUIDE_MODULES`. The `_find_in_guides()` function returns the first non-empty result, so IBM currently wins on conflicts — opposite of the intended hierarchy.



**Fix**: Swap order in `_GUIDE_MODULES` so Red Hat is checked before IBM:

```python

_GUIDE_MODULES = [

('Red Hat Supplementary Style Guide', 'style_guides.red_hat.red_hat_style_mapping'), # Red Hat overrides IBM

('IBM Style Guide', 'style_guides.ibm.ibm_style_mapping'),

('Getting Started with Accessibility for Writers', ...),

('Modular Documentation Reference Guide', ...),

]

```



The `enforcement_type` field disambiguates rule handling: `structural` → deterministic Python, `token_match` → regex/YAML, `semantic_llm` → LLM-only.
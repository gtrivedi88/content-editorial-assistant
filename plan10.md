# Plan: FP Reduction — Format Detector, LT Suppression, HTML-Aware Paste

## Context

Three root causes of false positives identified:

1. **Format misclassification**: AsciiDoc content without header attributes is scored as Markdown (AsciiDoc=5, Markdown=13) because the detector misses AsciiDoc-exclusive patterns like `[id="..."]`, `[role="..."]`, `term::`.

2. **LanguageTool flags known terms**: LT flags known-good technical terms (`initramfs`, `systemd`, `x86_64`) that our 52 YAML configs (~12K entries) already know about. Only spelling rule is currently filtered.

3. **Pasted HTML loses structure**: When users paste from rendered Red Hat docs pages, the frontend captures `text/html` from the clipboard and renders it correctly in the editor — but sends only stripped `textContent` to the backend. All structure (headings, code blocks, tables, lists) is lost. The plain text parser treats everything as paragraphs.

---

## Workstream 1: Format Detector Hardening

**File**: [format_detector.py](app/services/parsing/format_detector.py)

### Problem

10 AsciiDoc patterns, but misses exclusively-AsciiDoc constructs. `* ` bullets score +1 each for Markdown; 8 bullets overwhelm a single `= Heading` (+5).

### Changes

**Add AsciiDoc-exclusive patterns** to `_ASCIIDOC_PATTERNS`:

| Pattern | Matches | Weight |
|---------|---------|--------|
| `^\[id=` | Block anchors `[id="intro"]` | 5 |
| `^\[role=` | Role attributes `[role="_abstract"]` | 5 |
| `^\[(source\|listing)` | Source blocks `[source,bash]` | 4 |
| `^\+\s*$` | List continuation | 3 |
| `^(ifdef\|ifndef\|endif)::` | Conditional directives | 5 |
| `.*::\s*$` | Definition list terms `Components of UKI::` | 5 |
| `^\[.*\]\s*$` | Block attributes `[options="header"]` | 3 |

**Fix greedy pattern**: `^\..+` → `^\.[A-Z]` (block titles start `.Prerequisites`, not arbitrary dots).

**Guard against `::` Markdown false scoring**: In `detect_format()` loop, if a line ends with `::`, skip Markdown scoring for that line (definition lists are AsciiDoc-only).

### Implementation

1. Add 7 new patterns to `_ASCIIDOC_PATTERNS`
2. Fix `^\..+` → `^\.[A-Z]`
3. In `detect_format()` loop: `if stripped.endswith('::'):` skip Markdown scoring
4. Test: `test.adoc` content without lines 1-3 detects as AsciiDoc

---

## Workstream 2: Unified Term Registry + Heuristic Code Detection

### 2A: Term Registry

**New file**: [term_registry.py](rules/term_registry.py)

Build a `frozenset` at module import from these configs:

| Config file | Extract | Entries |
|-------------|---------|---------|
| `rules/config/spelling_allowlist.yaml` | All terms | ~293 |
| `rules/technical_elements/config/case_sensitive_terms_config.yaml` | Values (correct forms) | ~5,539 |
| `rules/word_usage/config/product_names_config.yaml` | Product name values | ~725 |
| `rules/language_and_grammar/config/abbreviations_config.yaml` | Abbreviation keys | ~679 |
| `rules/language_and_grammar/config/terminology_config.yaml` | All terms | ~160 |
| `rules/structure_and_format/config/camelcase_exceptions.yaml` | Exception terms | ~58 |
| `rules/legal_information/config/companies.yaml` | Company names | ~115 |

**NOT included** (contain wrong terms): `word_usage_config`, `simple_words_config`, `do_not_use_config`.

### 2B: Heuristic Code Detector

Add `is_likely_code(text: str) -> bool` in term_registry.py for unknown terms not in any config:

```python
_CODE_PATTERNS = [
    re.compile(r'[a-z][A-Z]'),           # camelCase
    re.compile(r'^[A-Z][a-z]+[A-Z]'),    # PascalCase
    re.compile(r'_[a-z]'),               # snake_case
    re.compile(r'^/[\w/]+'),             # file paths /usr/bin/
    re.compile(r'^\w+[-]\w+[-]\w+'),     # hyphenated-multi-word (skip-tokenizer-init)
    re.compile(r'^v?\d+\.\d+'),          # version numbers v2.1.3
    re.compile(r'^[A-Z]{2,}$'),          # ALL-CAPS acronyms (RBAC, YAML)
    re.compile(r'[{}\[\]<>|&;$]'),       # shell/code characters
    re.compile(r'\.\w{1,4}$'),           # file extensions .yaml, .py
    re.compile(r'^--?\w'),               # CLI flags --namespace, -v
]
```

### 2C: Registry Safety — Case-Sensitive Exact Match (Surprise 3 Guard)

**Problem**: Configs contain `ok`→`OK`, `ram`→`RAM`, `mom`→`MOM`, `popup`→`pop-up`. A naive case-insensitive frozenset would suppress legitimate LT errors.

**Solution**: Case-sensitive exact matching on **correct forms only**, single frozenset:

```python
def is_known_term(text: str) -> bool:
    # Case-sensitive exact match — covers both single and multi-word terms.
    # "initramfs" matches "initramfs" (spelling_allowlist)
    # "OK" matches "OK" (case_sensitive_terms value)
    # "ok" does NOT match "OK" — LT casing error passes through
    # "Red Hat" matches "Red Hat" (product_names value) — exact multi-word
    # "Red" does NOT match "Red Hat Enterprise Linux" — no substring matching
    return text in _REGISTRY
```

**Trap 1 guard**: No substring matching (`text in term` or `term in text`). When LT flags "Red Hat" as a multi-word phrase, `flagged_text` is exactly "Red Hat" — exact match handles it. Substring matching would cause "Red" to match inside "Red Hat Enterprise Linux", suppressing legitimate errors.

**Config extraction rules**:
- `spelling_allowlist.yaml` → all terms as-is (already lowercase domain terms, curated to exclude dictionary words)
- `case_sensitive_terms_config.yaml` → values only (correct forms: "OK", "RAM", "MOM" — NOT keys: "ok", "ram", "mom")
- `product_names_config.yaml` → values only (correct product names: "Red Hat Enterprise Linux", "Podman")
- `abbreviations_config.yaml` → keys (abbreviation forms: "API", "CLI", "RBAC")
- `terminology_config.yaml` → all terms as-is
- `camelcase_exceptions.yaml` → exception terms as-is
- `companies.yaml` → company names (proper nouns)

**Why this is safe**: If LT flags "ok" (lowercase) as a casing error, `is_known_term("ok")` returns False because only "OK" is in the registry. The LT error passes through. If LT somehow flags "OK" (correct form), `is_known_term("OK")` returns True and suppresses it — which is correct, because "OK" is already the right form.

### Integration in LT Client

**File**: [languagetool_client.py](app/services/analysis/languagetool_client.py)

In `_should_skip_match()`, add after existing spelling allowlist check:

```python
from rules.term_registry import is_known_term, is_likely_code

# Guard: unified term registry (case-sensitive exact match)
if lt_category in ('TYPOS', 'CASING', 'CONFUSED_WORDS', 'STYLE'):
    if is_known_term(flagged_text):
        return True

# Guard: heuristic code detection
if is_likely_code(flagged_text):
    return True
```

**Category restriction**: Do NOT suppress `GRAMMAR` — known terms can still have grammar errors around them.

---

## Workstream 3: HTML-Aware Paste Analysis

### Problem

The frontend already captures `text/html` from clipboard (editor-controller.js line 109), sanitizes it (whitelisting `p`, `h1-h6`, `ul`, `ol`, `li`, `code`, `pre`, `table`, etc.), and renders it in the contenteditable editor. But on analyze, it sends only `textContent` — all HTML structure is discarded.

The HTML parser already handles: headings (h1-h6), code blocks (`should_skip_analysis=True`), lists (ul/ol/li), tables (table/tr/td/th), blockquotes, images. This gives us proper block types with **zero heuristics**.

### 3A: Frontend — Always Send innerHTML (Trap 3 Fix)

**File**: [editor-controller.js](static/js/editor/editor-controller.js)

**Trap 3 guard**: No boolean `_isHtmlPaste` flag. The contenteditable `<div>` always has structured innerHTML — even typed text gets wrapped in `<div>` or `<p>` by the browser. Always send it.

In `triggerAnalysis()` (line 400):
1. If `this._rawContent` is set → markup detected (AsciiDoc/Markdown/DITA) → send only `text` (existing behavior, format detector picks the right parser)
2. If `this._rawContent` is NOT set → send both `text: getPlainText()` AND `html_content: this._editor.innerHTML`

```javascript
triggerAnalysis() {
    const raw = this._rawContent || getPlainText(this._editor);
    const text = normalizeWhitespace(raw);
    if (!text.trim()) return;

    // When no markup detected, always send innerHTML for structure-aware parsing.
    // The browser wraps typed text in <p>/<div>, and pasted HTML preserves
    // <h1>, <code>, <table>, <li> — the HTML parser handles all of it.
    const htmlContent = this._rawContent ? null : this._editor.innerHTML;

    this._store.setState({ content: text, htmlContent });
}
```

No paste handler changes needed — the existing three-branch logic stays as-is.

**File**: [api-client.js](static/js/services/api-client.js)

In `postAnalyze()`:
1. Accept optional `htmlContent` parameter
2. If provided, include `html_content` field in the JSON body

**File**: [actions.js](static/js/state/actions.js)

In `analyzeContent()`:
1. Read `htmlContent` from store and pass to `postAnalyze()`

### 3B: Backend — Use HTML Parser When HTML Provided

**File**: [analysis.py](app/api/v1/analysis.py)

In the analyze endpoint:
1. Extract optional `html_content` from request body
2. If `html_content` provided:
   - Set `file_type = FileType.HTML`
   - Parse with HTML parser: `parse_result = html_parser.parse(html_content)`
   - Use `text` field for span mapping (same as now)
3. If not provided: existing flow (format detection + auto-parsing)

### 3C: HTML Parser — Admonition Detection

**File**: [html_parser.py](app/services/parsing/html_parser.py)

Add class-based admonition detection for Red Hat docs HTML patterns:

```python
_ADMONITION_CLASSES = {'note', 'tip', 'important', 'warning', 'caution', 'admonition'}

def _is_admonition(element) -> bool:
    classes = set((element.get('class') or '').lower().split())
    return bool(classes & _ADMONITION_CLASSES)
```

In `_element_to_block()`: if `_is_admonition(element)`, set `block_type="admonition"`.

### 3D: HTML Parser — Inline Code Range Computation (Surprise 1 Fix)

**Problem**: When `<p>Use the <code>systemctl</code> command</p>` is parsed, `text_content()` strips the `<code>` tags. `inline_content` becomes `"Use the systemctl command"` — no backticks, zero code ranges, zero protection. Multi-word code like `--namespace my-project` gets zero protection from both the term registry and the heuristic.

**File**: [html_parser.py](app/services/parsing/html_parser.py)

In `_element_to_block()`, when building text from a paragraph/list-item element that contains inline `<code>` children, preserve them as backticks in `inline_content`.

**Trap 2 guard**: Do NOT manually stitch `node.text` and `node.tail` via `element.iter()` — nested tags like `<b><code>systemctl</code></b>` break manual stitching. Instead, clone the element, mutate `<code>` tags in-place, and let lxml's `text_content()` handle stitching:

```python
import copy

def _extract_text_with_code_markers(element) -> tuple[str, str]:
    """Extract content and inline_content from an element.

    Returns:
        (content, inline_content) where inline_content preserves
        <code> as backticks for code range computation.
    """
    # 1. Plain content — lxml handles all text stitching
    content = element.text_content()

    # 2. Clone element, wrap <code> text with backticks in-place
    el_copy = copy.deepcopy(element)
    for code_el in el_copy.xpath('.//code'):
        code_text = code_el.text_content() or ''
        code_el.text = f'`{code_text}`'
        # Clear children inside <code> to prevent duplicate text
        for child in list(code_el):
            code_el.remove(child)

    # 3. Let lxml stitch text+tails safely
    inline_content = el_copy.text_content()

    return content, inline_content
```

For block types that can contain inline code (`paragraph`, `list_item_ordered`, `list_item_unordered`, `blockquote`):
1. Call `_extract_text_with_code_markers(element)` → `(content, inline_content)`
2. Set `block.content = content` (stripped, for rules)
3. Set `block.inline_content = inline_content` (with backticks, for code range computation)
4. Build `char_map` mapping content positions → inline_content positions (same as AsciiDoc parser does)

**Result**: `_compute_content_code_ranges()` in the orchestrator finds backticks in `inline_content`, computes ranges, and rules skip code content via `in_code_range()`. Works for single words (`systemctl`), multi-word strings (`--namespace my-project`), and CLI flags (`-v`).

### 3E: Plain Text Parser — Fallback Hardening

**File**: [plaintext_parser.py](app/services/parsing/plaintext_parser.py)

For manually typed content or paste from non-HTML sources (text editors, terminals), harden `_classify_chunk()`:

```python
_ADMONITION_LABELS = frozenset({
    "note", "tip", "important", "warning", "caution",
})
_UI_ARTIFACTS = frozenset({
    "expand", "collapse", "show more", "show less",
    "copy", "download", "back to top", "table of contents",
})
_TABLE_CAPTION_RE = re.compile(r"^Table\s+\d+[\.\d]*\.\s+")
_STRUCTURED_HEADING_RE = re.compile(
    r"^(Chapter\s+\d+\.|"
    r"\d+\.\d+[\.\d]*\.\s|"
    r"(Appendix|Part|Section)\s+[A-Z0-9])"
)
# Surprise 2 fix: browser-injected Unicode bullets
_BROWSER_BULLET_RE = re.compile(r"^[•○▪►‣◦⁃∙]\s+")
```

Classification order:
1. UI artifacts → `should_skip_analysis=True`
2. Admonition labels → `should_skip_analysis=True`
3. Table captions → `should_skip_analysis=True`
4. Tabular data (2+ tabs per line) → `should_skip_analysis=True`
5. Browser bullet lines (`_BROWSER_BULLET_RE`) → `block_type="list_item_unordered"`, strip the bullet character from content
6. Structured heading → `block_type="heading"`
7. Existing heading heuristic → `block_type="heading"`
8. Default → `block_type="paragraph"` with backtick `inline_code_ranges`

**Browser bullet handling**: When Chrome/Edge copy a `<ul>` as plain text, they inject Unicode bullets (•, ○, ▪). The regex detects these and classifies the chunk as `list_item_unordered`. The bullet character is stripped from `content` so rules and LT don't flag it as punctuation. This only matters for the plain text fallback path — the HTML-aware paste path (3A-3B) uses the HTML parser which handles `<li>` elements directly.

---

## Files Summary

| Action | File | Change |
|--------|------|--------|
| Modify | `app/services/parsing/format_detector.py` | Add 7 AsciiDoc-exclusive patterns, fix greedy `.` pattern |
| Create | `rules/term_registry.py` | Case-sensitive frozenset (~7,500 terms) + heuristic code detector |
| Modify | `app/services/analysis/languagetool_client.py` | Add registry + code heuristic guards in `_should_skip_match()` |
| Modify | `static/js/editor/editor-controller.js` | Store sanitized HTML on paste, send on analyze |
| Modify | `static/js/services/api-client.js` | Accept and send `html_content` field |
| Modify | `static/js/state/actions.js` | Pass `htmlContent` to API client |
| Modify | `app/api/v1/analysis.py` | Accept `html_content`, route to HTML parser |
| Modify | `app/services/parsing/html_parser.py` | Admonition detection + inline `<code>` → backtick preservation in `inline_content` (Surprise 1) |
| Modify | `app/services/parsing/plaintext_parser.py` | Heuristic block types + browser bullet detection (Surprise 2) + backtick ranges |

## DO NOT Modify

| File | Reason |
|------|--------|
| `app/services/analysis/orchestrator.py` | Already handles all block types and `char_map` correctly |
| `app/services/analysis/merger.py` | Merge logic unchanged |
| `app/services/parsing/markdown_parser.py` | Already handles backticks correctly |
| Any rule file | Rules already use `in_code_range()` — they just need correct ranges |
| Any YAML config | Registry reads existing configs, doesn't modify them |

## Verification

1. **Format detector**: `test.adoc` without lines 1-3 → detects as AsciiDoc (not Markdown)
2. **Format detector**: Pure Markdown content → still detects as Markdown
3. **LT suppression**: Content with `initramfs`, `systemd` → LT does not flag these
4. **LT code heuristic**: `skip-tokenizer-init`, `v2.1.3`, `PascalCase`, `--namespace` → LT suppressed
5. **LT grammar**: Grammar errors around known terms still pass through
6. **LT registry safety (Surprise 3)**: `is_known_term("ok")` → False (only "OK" in registry). `is_known_term("ram")` → False. `is_known_term("initramfs")` → True
7. **HTML paste**: Copy from Red Hat docs page → headings, code blocks, tables, lists all get proper block types. Code blocks have `should_skip_analysis=True`
8. **HTML inline code (Surprise 1)**: `<p>Use the <code>systemctl</code> command</p>` → `inline_content` = `` "Use the `systemctl` command" `` → `inline_code_ranges` computed → rules skip "systemctl". Also works for `<code>--namespace my-project</code>`
9. **Browser bullets (Surprise 2)**: Plain text with "• Click the button" → classified as `list_item_unordered`, bullet stripped from content
10. **Plain text fallback**: Manually typed content with "Note" label → skipped. Table data → skipped
11. **Run tests**: `python -m pytest tests/ --ignore=tests/rules/test_lt_examples.py -v` — all 713 pass

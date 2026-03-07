# Full Vale Parity + Reviewer Bug Fixes

## Context

CEA and Vale use the same fundamental approach for terminology rules: strip markup → regex match against dictionaries → report issues. CEA's `BaseWordUsageRule._match_terms()`, `CompoundWordsRule`, and YAML configs are architecturally equivalent to Vale's `substitution` pattern type. There is no technical barrier to importing all Vale dictionary entries — it's a data completeness problem, not an engineering problem.

Vale has **72 rules** across 3 rule sets. Of these:
- **~40 are substitution/dictionary rules** → import directly into CEA YAML configs
- **~20 are already covered** by CEA's SpaCy-enhanced equivalents (better implementations)
- **~12 are AsciiDoc structural rules** → partially covered by CEA's structural_rules.py

The user's directive: **"We need to be 100% accurate and should have imported everything from vale."**

---

## Phase 1: Import ALL Vale Substitution Dictionaries (YAML-only)

### 1.1 TermsErrors.yml → word_usage_config.yaml

**Vale:** 457 entries, level: error, ignorecase: true
**CEA:** ~450 entries in word_usage_config.yaml

Import ALL missing entries. Skip only:
- Terms already in compound_words_config.yaml (avoid double-flagging)
- Terms handled by dedicated CEA rules with better FP guards (e.g., "please" → messages_rule has quoted-text and code guards)

**File:** `rules/word_usage/config/word_usage_config.yaml`

### 1.2 TermsWarnings.yml → word_usage_config.yaml

**Vale:** 77 entries, level: warning, ignorecase: true
**CEA:** Partial coverage scattered across configs

Import ALL missing entries. Many have complex lookaheads that `_match_pattern_terms()` already supports. Key entries: "click on" → "click", "execute" → "run", "in order to" → "to", "leverage" → "use", "terminate" → "end", "host name" → "hostname", etc.

**File:** `rules/word_usage/config/word_usage_config.yaml`

### 1.3 TermsSuggestions.yml → word_usage_config.yaml

**Vale:** 55 entries, level: suggestion, ignorecase: false (sentence scope)
**CEA:** Partial coverage

Import entries where CEA doesn't already have better coverage. Key entries: "k8s" → "Kubernetes", "via" → "through", "launch" → "start", "legacy" → "existing", "once" → "after/when", "thus" → "therefore", "segfault" → "segmentation fault".

**File:** `rules/word_usage/config/word_usage_config.yaml`

### 1.4 Hyphens.yml → compound_words_config.yaml

**Vale:** 237 entries, level: warning, ignorecase: true
**CEA:** 235 entries in compound_words_config.yaml

Import ~105 missing entries. Mostly prefix corrections (pre-, post-, non-, sub-, super-, multi-, over-, un-, re-, off-).

**File:** `rules/punctuation/config/compound_words_config.yaml`

### 1.5 SimpleWords.yml → conversational_vocabularies.yaml

**Vale:** 107 entries, level: suggestion, ignorecase: true
**CEA:** 22 entries in conversational_vocabularies.yaml

Import ~85 missing entries. Vale's list covers formal→simple substitutions: "accentuate" → "stress", "acquiesce" → "agree", "ameliorate" → "improve", "ascertain" → "discover", "endeavor" → "try", "enumerate" → "count", "expedite" → "hurry", "facilitate" → "ease", "jeopardize" → "risk", "procure" → "buy", "solicit" → "request", "utilize" → "use", etc.

**File:** `rules/word_usage/config/conversational_vocabularies.yaml`

### 1.6 DoNotUseTerms.yml → do_not_use_config.yaml

**Vale:** 28 entries, level: warning
**CEA:** 17 entries in do_not_use_config.yaml

Import ~11 missing entries. Key gaps: "ACK" (without "flag"/"packet"), color names without non-visual description, "respective/respectively", "overhead", "resides".

**File:** `rules/word_usage/config/do_not_use_config.yaml`

### 1.7 ConsciousLanguage.yml → inclusive_language_terms.yaml

**Vale:** 4 entries (blacklist, master, slave, whitelist)
**CEA:** 22 entries — CEA has MORE coverage here

Verify CEA covers Vale's negative lookaheads: Vale exempts "master broker", "master boot record", "slave broker". CEA should have equivalent guards.

**File:** `rules/audience_and_medium/config/inclusive_language_terms.yaml`

### 1.8 Contractions.yml — verify parity

**Vale:** 34 contractions
**CEA:** 30 contractions in contractions_rule.py

Verify CEA covers Vale's 4 missing entries: "how'll", "how's", "when'll", "where'll". CEA's SpaCy-based possessive detection is already better than Vale's regex.

**File:** `rules/language_and_grammar/contractions_rule.py` (may need code addition for 4 entries)

### 1.9 SmartQuotes.yml — verify parity

**Vale:** Flags curly quotes (' ' " ‟ ″ ‶)
**CEA:** quotation_marks_rule.py Check 2 handles curly quotes in code blocks

Verify CEA's quotation_marks_rule catches curly quotes in ALL blocks, not just code. If not, extend the check.

**File:** `rules/punctuation/quotation_marks_rule.py`

### 1.10 ReleaseNotes.yml → word_usage_config.yaml

**Vale:** 2 entries — "Now" → "With this update", "Previously" → "Before this update"
**CEA:** No equivalent

Add these 2 entries to word_usage_config.yaml with a release_notes content-type guard (only flag in release notes context).

**File:** `rules/word_usage/config/word_usage_config.yaml`

### 1.11 Slash allowlist fix (Mbit/s)

**Root cause:** SlashesRule flags `Mbit/s` because it's not in the allowlist.

**File:** `rules/punctuation/config/slash_allowlist.yaml`

Add to networking section:
```yaml
- MBIT/S
- GBIT/S
- KBIT/S
- TBIT/S
```

### 1.12 Add webserver/mailserver/fileserver

Not in Vale OR CEA. User reported these as missing.

**File:** `rules/word_usage/config/word_usage_config.yaml`

```yaml
"webserver": "web server"
"mailserver": "mail server"
"fileserver": "file server"
```

---

## Phase 2: CaseSensitiveTerms (Small Python + YAML)

### 2.1 Create CaseSensitiveTermsRule

**Vale:** 323 entries, level: warning, ignorecase: FALSE
**CEA:** No case-sensitive matching capability — word_usage rules use `re.IGNORECASE`

**Why this isn't a big architecture change:** CEA's `BaseWordUsageRule._match_terms()` uses `re.IGNORECASE` by default. A `CaseSensitiveTermsRule` is the same logic with that flag removed. The matching infrastructure already exists.

**Implementation:**
1. Create `rules/technical_elements/case_sensitive_terms_rule.py` — subclass of `BaseRule`, loads from YAML, uses `_match_terms()` pattern but with case-sensitive regex (no `re.IGNORECASE`)
2. Create `rules/technical_elements/config/case_sensitive_terms_config.yaml` — import all 323 entries from Vale
3. Register in `rule_mappings.yaml` for paragraph, heading, list_item block types

**Key entries:** kubernetes→Kubernetes, openshift→OpenShift, yaml→YAML, nodejs→Node.js, systemd (correct lowercase), SELinux (correct mixed case), etc.

**Word boundary trap for dotted terms:** Terms like `Node.js` contain a period which breaks `\b` word boundaries (`.` is not a word character, so `\bNode.js\b` won't match correctly). For dotted entries, use `re.escape()` on the term and anchor with `(?<!\w)` / `(?!\w)` instead of `\b`:
```python
if '.' in wrong_term:
    pattern = r'(?<!\w)' + re.escape(wrong_term) + r'(?!\w)'
else:
    pattern = r'\b' + re.escape(wrong_term) + r'\b'
```

**Files:**
- `rules/technical_elements/case_sensitive_terms_rule.py` (new, ~60 lines)
- `rules/technical_elements/config/case_sensitive_terms_config.yaml` (new, 323 entries)
- `rules/technical_elements/__init__.py` (register rule)
- Config for rule_mappings.yaml (add to block types)

---

## Phase 3: Close Verified Gaps in Existence Rules

Audit confirmed 33/36 Vale rules are covered. Two are genuinely missing, two are partial. All others verified:

### Verified Covered (no action needed)

| Vale Rule | CEA Equivalent | Status |
|-----------|---------------|--------|
| Ellipses | ellipses_rule.py (both `...` and `...`) | Covered |
| EmDash | dashes_rule.py (`—` and `--`) | Covered |
| Symbols (& and !) | punctuation_and_symbols_rule.py + exclamation_points_rule.py | Covered |
| Spacing | spacing_rule.py | Covered |
| PassiveVoice | verbs_rule.py (SpaCy, better) | Covered |
| Abbreviations | definitions_rule.py | Covered |
| Conjunctions | conjunctions_rule.py | Covered |
| SelfReferentialText | self_referential_text_rule.py | Covered |
| Definitions | definitions_rule.py | Covered |
| RepeatedWords | repeated_words_rule.py (23 allowed repeats) | Covered |
| ObviousTerms | obvious_terms_rule.py | Covered |
| OxfordComma | oxford_comma_rule.py | Covered |
| Slash | slashes_rule.py (fixing Mbit/s in 1.11) | Covered |
| Headings | headings_rule.py (4 checks) | Covered |
| HeadingPunctuation | headings_rule.py Check 1 (trailing period) + Check 2 (trailing colon) | Covered |
| Using | using_rule.py (SpaCy POS tagging) | Covered |
| Spelling | spelling_rule.py + spelling_config.yaml | Covered |
| SentenceLength | LLM (intentional — not deterministic) | Covered |
| ReadabilityGrade | LLM (intentional — not deterministic) | Covered |
| MergeConflictMarkers | Not a style rule | N/A |
| GitLinks | Not a style rule | N/A |
| SessionId | personal_information_rule.py | Covered |

### 3.1 ProductCentricWriting — MISSING

**Vale:** Flags "allows you", "enables you", "lets you", "permits you/customers/users" when the subject is a product/system.
**CEA:** `anthropomorphism_rule.py` targets cognitive agency verbs (think, know, believe) — does NOT cover transitive-agency patterns.

**Fix:** Add a check to `anthropomorphism_rule.py` or create a new lightweight rule. The pattern is narrow and deterministic:
```python
_PRODUCT_CENTRIC_RE = re.compile(
    r'\b(allows?|enables?|lets?|permits?)\s+(you|users?|customers?|administrators?|developers?)\b',
    re.IGNORECASE,
)
```
Flag with message: "Rewrite to focus on the user's action, not the product's agency. Example: 'You can configure...' instead of 'Product X allows you to configure...'"

**File:** `rules/language_and_grammar/anthropomorphism_rule.py` (add new check method)

### 3.2 PascalCamelCase — MISSING

**Vale:** Flags unformatted camelCase/PascalCase identifiers that should be in backticks. Has 237 exceptions (GitHub, OpenShift, etc.).
**CEA:** `highlighting_rule.py` only checks all-caps emphasis — no camelCase/PascalCase detection.

**Fix:** Add Check 2 to `highlighting_rule.py` (currently disabled as "too context-dependent"). Use a conservative approach:
```python
_CAMEL_CASE_RE = re.compile(r'\b[a-z]+[A-Z]\w*\b')  # camelCase only
```
Skip if: inside inline code ranges, is a known product name (load exception list from YAML), or is a single character after a lowercase prefix.

**FP risk:** Medium-high for PascalCase (too many product names). Start with **camelCase only** (lowercase first letter + uppercase interior) which is almost always a code identifier. PascalCase detection deferred to LLM.

**File:** `rules/technical_elements/highlighting_rule.py` (add Check 2)
**Config:** `rules/technical_elements/config/camelcase_exceptions.yaml` (new, product name exceptions)

### 3.3 SmartQuotes — PARTIAL

**Vale:** Flags curly/smart quotes in ALL contexts.
**CEA:** `quotation_marks_rule.py` only flags smart quotes in code blocks.

**Fix:** Extend Check 2 to flag smart quotes in prose blocks too (not just code). Smart quotes should never appear in AsciiDoc source — they cause rendering issues.

**File:** `rules/punctuation/quotation_marks_rule.py` (extend scope of Check 2)

### 3.4 Spelling Config Scale

**CEA:** `spelling_config.yaml` covers common US/UK variants.
**Vale:** 598 spelling filter patterns.

**Fix:** Cross-reference Vale's spelling dictionary against CEA's `spelling_config.yaml` during Phase 1 import. Add any missing non-US spelling variants. This is YAML-only work.

**File:** `rules/language_and_grammar/config/spelling_config.yaml`

---

## Phase 4: Reviewer Bug Fixes (Code changes)

### 4.1 Admonition Placement FP on Block Titles
**File:** `rules/modular_compliance/structural_rules.py`
**Fix:** Skip level-0 headings, stop after first abstract paragraph

### 4.2 Suggestion Prompt Style Constraints
**File:** `app/llm/prompts.py`
**Fix:** Add 4 style constraint bullets (active voice, present tense, no self-ref, preserve imperative)

### 4.3 Spatial Reference Safe Contexts
**File:** `rules/structure_and_format/self_referential_text_rule.py`
**Fix:** Expand `_ABOVE_SAFE`/`_BELOW_SAFE` with quantitative/comparative patterns. Account for formatting markers between the spatial word and the number:
```python
# Instead of: r'above\s+\d'
# Use: r'above\s+(?:the\s+)?(?:[*_~`]\s*)?\d'
# Handles: "above 50", "above the 50th", "above *50*", "above `50`"
```

### 4.4 Messages Rule — Quoted Text Guard
**File:** `rules/structure_and_format/messages_rule.py`
**Fix:** Add `_QUOTED_RANGES_RE` check to all 6 methods

### 4.5 Cross-Reference Introductory Comma
**File:** `rules/references/citations_rule.py`
**Fix:** Add Check 4: "For more information see" → needs comma. Keep the regex strictly adjacent — do NOT try to match separated forms like "For more information about configuring the proxy, see..." with a greedy `.*`. The strict pattern catches 80% safely; the LLM granular pass handles the complex separated cases.

---

## NOT Implementing (With Reasoning)

| Issue | Reason |
|-------|--------|
| List Introduction Colons | HIGH FP RISK — not all pre-list paragraphs are introductions |
| Nested List Depth | NEEDS PARSER VERIFICATION — parser may not populate nesting depth |
| xref: Syntax Check | MEDIUM FP RISK — quoted references may be intentional |
| CPUs as Verb | NOT A BUG — all rules have proper guards |
| Vale AsciiDoc structural rules (13) | CEA's structural_rules.py covers these differently via parsed Block objects |
| Vale OpenShift rules (19) | CEA's modular_compliance rules cover these (7 pending structural_parsing port) |

---

## Files to Modify

| File | Type | Change |
|------|------|--------|
| `rules/word_usage/config/word_usage_config.yaml` | YAML | Import ~200 TermsErrors + ~50 TermsWarnings + ~40 TermsSuggestions + webserver/mailserver/fileserver + 2 ReleaseNotes |
| `rules/word_usage/config/conversational_vocabularies.yaml` | YAML | Import ~85 SimpleWords entries |
| `rules/word_usage/config/do_not_use_config.yaml` | YAML | Import ~11 DoNotUseTerms entries |
| `rules/punctuation/config/compound_words_config.yaml` | YAML | Import ~105 Hyphens entries |
| `rules/punctuation/config/slash_allowlist.yaml` | YAML | Add Mbit/s, Gbit/s, kbit/s, Tbit/s |
| `rules/language_and_grammar/config/spelling_config.yaml` | YAML | Cross-reference Vale spelling patterns, add missing variants |
| `rules/audience_and_medium/config/inclusive_language_terms.yaml` | YAML | Verify ConsciousLanguage parity |
| `rules/technical_elements/case_sensitive_terms_rule.py` | Python (new) | Case-sensitive matching rule with dotted-term word boundary handling (~60 lines) |
| `rules/technical_elements/config/case_sensitive_terms_config.yaml` | YAML (new) | 323 CaseSensitiveTerms entries |
| `rules/language_and_grammar/anthropomorphism_rule.py` | Python | Add ProductCentricWriting check (allows/enables/lets/permits you) |
| `rules/technical_elements/highlighting_rule.py` | Python | Add camelCase detection (Check 2) |
| `rules/technical_elements/config/camelcase_exceptions.yaml` | YAML (new) | Product name exceptions for camelCase check |
| `rules/punctuation/quotation_marks_rule.py` | Python | Extend smart quotes check to all blocks, not just code |
| `rules/modular_compliance/structural_rules.py` | Python | Fix admonition placement |
| `app/llm/prompts.py` | Python | Add suggestion style constraints |
| `rules/structure_and_format/self_referential_text_rule.py` | Python | Expand spatial reference safe contexts |
| `rules/structure_and_format/messages_rule.py` | Python | Add quoted text guard |
| `rules/references/citations_rule.py` | Python | Add introductory comma check |

---

## Execution Order

1. **Phase 1** (YAML-only, highest priority) — systematic import of all Vale dictionaries
2. **Phase 2** — CaseSensitiveTermsRule (small Python + large YAML, dotted-term boundary handling)
3. **Phase 3** — Close verified gaps: ProductCentricWriting, camelCase, SmartQuotes scope, spelling scale
4. **Phase 4** — Reviewer bug fixes (code changes)

---

## Implementation Traps (Must-Read Before Coding)

### Trap 1: Vale Regex Import (Phase 1)

Vale uses Go-flavored regex for its YAML keys, not literal strings. Examples:
- `'\b(?:B|b)ack-up\b'` — NOT a literal string
- `'(?<!make the )transition'` — negative lookbehind

**Guard:** During import, sanitize Vale entries: strip `\b` boundaries, remove `(?:...)` non-capturing groups, convert to lowercase literal strings. CEA's `_match_terms()` already adds word boundaries and handles case-insensitivity natively. For entries with lookaheads/lookbehinds, use `_match_pattern_terms()` with the `pattern` key in YAML.

### Trap 2: Preamble vs Paragraph (Phase 4.1)

The AsciiDoc parser may classify text immediately after the document title as `block_type="preamble"`, not `"paragraph"`. If the admonition fix only checks for `"paragraph"`, it will miss preamble blocks and keep looking, hitting the nested `[NOTE]` and falsely flagging it.

**Guard:** Accept both block types:
```python
if block.block_type in ("paragraph", "preamble"):
    found_abstract = True
```

### Trap 3: Cross-Reference Greedy Regex (Phase 4.5)

Writers frequently insert context between "For more information" and "see": *"For more information about configuring the proxy, see..."*. Do NOT write `r'For more information.*see'` to catch this — greedy regex over sentence boundaries causes catastrophic FPs.

**Guard:** Keep the regex strictly adjacent. Accept 80% coverage from the strict pattern. LLM granular pass catches the rest.

### Trap 4: Slash Allowlist Word Boundary (Phase 1.11)

`/` is not a regex word character, so `\b` behaves unexpectedly around slashes. Also, trailing punctuation like `.` in `"100 Mbit/s."` means the token extracted may include the period.

**Guard:** Strip trailing punctuation before checking the allowlist:
```python
clean_token = token.text.strip('.,;!?')
if clean_token.upper() in _SLASH_ALLOWLIST:
    continue
```

---

## Verification

1. `python -m pytest tests/rules/test_fp_guards.py -v` — FP guard tests pass
2. `python -m pytest tests/llm/test_prompts.py -v` — prompt tests pass
3. `python -m pytest tests/ -q` — full test suite passes
4. Manual verification — Phase 1 (Vale dictionaries):
   - "webserver" flagged → "web server"
   - "100 Mbit/s" NOT flagged by slashes rule
   - "utilize" flagged → "use" (SimpleWords import)
   - "click on" flagged → "click" (TermsWarnings import)
   - "in order to" flagged → "to" (TermsWarnings import)
5. Manual verification — Phase 2 (CaseSensitiveTerms):
   - "kubernetes" flagged → "Kubernetes"
   - "nodejs" flagged → "Node.js" (dotted-term boundary works)
   - "Node.js" NOT flagged (already correct)
   - "systemd" NOT flagged (correct lowercase)
6. Manual verification — Phase 3 (gap closures):
   - "The product allows you to configure" flagged (ProductCentricWriting)
   - "variableName" in prose flagged → suggest backticks (camelCase)
   - "OpenShift" NOT flagged by camelCase check (exception list)
   - Curly quote `\u201c` in prose flagged (SmartQuotes scope fix)
7. Manual verification — Phase 4 (reviewer bugs):
   - `[NOTE]` after `.Procedure` NOT flagged
   - "above 50°C" NOT flagged as positional reference
   - Quoted "Please wait" NOT flagged in messages
   - "For more information see X" flagged with comma suggestion

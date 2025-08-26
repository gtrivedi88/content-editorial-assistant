## Validation System Priority Upgrades (1–10)

This plan details enterprise-grade enhancements to the validation system to drive near-zero false positives while preserving strong positives. Each upgrade includes design, implementation steps, tests, performance budgets, and acceptance criteria.

Goals
- Enterprise ready: deterministic behavior, explainability, and observability
- No performance regressions: keep latency within existing budgets
- No legacy code: use centralized, configurable mechanisms

Scope
- Validation pipeline and calculators only; rule logic is evidence-based already
- Error consolidation behavior for confidence and messaging
- Configuration and tests in `validation/tests`

Pre-requisites
- Ensure current test suite is green: `pytest -q`
- Validate universal threshold (0.35) in `validation/config/validation_thresholds.yaml` is in place

---

### 1) Evidence-first validation shortcut

Design
- When a rule provides strong evidence (evidence_score ≥ 0.85) and rule reliability ≥ 0.85, short-circuit the pipeline to ACCEPT unless a strong negative-evidence validator contradicts it.
- Rationale: high-confidence, evidence-based detections should not be diluted by weaker contextual signals.

Implementation
- Forward evidence score into validation context:
  - File: `rules/base_rule.py`
  - In `_calculate_enhanced_error_fields` when building `ValidationContext`, add `additional_context['evidence_score'] = extra_data.get('evidence_score')`.
- Add shortcut in pipeline:
  - File: `validation/multi_pass/validation_pipeline.py`
  - After validator executions and before consensus: inspect `context.additional_context.get('evidence_score')` and rule reliability (via `validation.confidence.rule_reliability.get_rule_reliability_coefficient(context.rule_type)`).
  - If both thresholds are met, set `final_result` to ACCEPT with `confidence_score = max(existing, 0.75)` UNLESS a negative-evidence marker exists (see Upgrade 2). Mark `metadata['shortcut_applied'] = True`.

Tests
- New: `validation/tests/test_multi_pass/test_evidence_shortcut.py`
  - High evidence + high reliability → ACCEPT with confidence ≥ 0.75
  - High evidence + negative-evidence present → no shortcut; falls back to consensus
- Integration: update `validation/tests/test_production_validation.py` to assert shortcut application does not degrade other paths.

Performance
- O(1) additional checks; no extra NLP. Budget: <1ms per error.

Acceptance Criteria
- Shortcut triggers only on strong evidence and reliability
- No changes to decisions when evidence is weak or absent
- All tests pass

---

### 2) Negative-evidence guards in Context Validator

Design
- Introduce explicit negative-evidence detection that can veto the shortcut and reduce FPs: quoted text, legacy/migration disclaimers, code samples, and deprecation contexts.
- Emit `ValidationEvidence` with high negative confidence when detected; allow early REJECT if strong.

Implementation
- File: `validation/multi_pass/pass_validators/context_validator.py`
  - Add `_detect_negative_context_evidence(error_context, validation_context)` that scans the sentence around `error_position` for:
    - Quotation context (balanced quotes around span)
    - Legacy/migration markers: legacy, deprecated, migrating, previously called, historically
    - Code indicators: inline backticks, code fences near error
  - Produce `ValidationEvidence(evidence_type='negative_context', confidence in [0.7, 1.0], description='…')` when matched.
  - In decision logic, if cumulative negative evidence ≥ 0.85 → `ValidationDecision.REJECT` with high confidence.
- Ensure results are added to `ValidationResult.evidence` and reasoning.

Tests
- New: `validation/tests/test_multi_pass/test_negative_evidence_guards.py`
  - Quoted legacy term → REJECT or lower confidence appropriately
  - Code snippet usage → REJECT or low confidence
  - No negative indicators → no penalty

Performance
- Use existing doc from analyzer if present; avoid extra spaCy runs.
- Budget: <2ms per error.

Acceptance Criteria
- Demonstrated reductions in FP contexts without harming genuine cases
- Clear evidence entries in results

---

### 3) Provenance-aware confidence blending (explainability)

Design
- Augment normalized confidence with provenance details: evidence weight, model weight, content modifier, reliability, and guard activation.
- Improves audits and trust, aiding enterprise support.

Implementation
- File: `validation/confidence/confidence_calculator.py`
  - In `calculate_normalized_confidence`, when blending evidence, compute and attach:
    - `provenance = { 'evidence_weight': x, 'model_weight': y, 'rule_reliability': r, 'content_modifier': m, 'floor_guard_triggered': bool }`
  - Return this via the existing `confidence_breakdown` (e.g., add `breakdown.metadata['provenance'] = provenance`) or include a sibling field in BaseRule enhanced fields: `confidence_provenance`.
- File: `rules/base_rule.py`
  - Include the provenance on the error dictionary under `confidence_provenance` for UI/debug.

Tests
- Update: `validation/tests/test_confidence_normalization.py`
  - Assert presence and ranges of `evidence_weight`, `model_weight`, and correct guard flag behavior.

Performance
- Pure arithmetic/meta additions; negligible.

Acceptance Criteria
- Provenance always present when evidence is supplied
- Values in valid ranges; no user-visible regressions

---

### 4) Consolidation truthiness preservation (don’t dilute strong evidence)

Design
- During merging, if any grouped error has strong evidence (evidence_score ≥ 0.90), preserve its specific message and set merged confidence to at least that error’s confidence (or a minimal soft floor). Add `evidence_sources` to merged error metadata.

Implementation
- File: `error_consolidation/consolidator.py`
  - In `_merge_error_group`:
    - Scan `group` for `evidence_score` (if present on member errors).
    - If any ≥ 0.90, set `preserve_primary_message = True`, and set `merged_error['confidence_score'] = max(existing, primary_confidence, 0.75)`.
    - Add `merged_error['evidence_sources'] = sorted({e['type'] for e in group if e.get('evidence_score', 0) >= 0.90})`.

Tests
- Update: `validation/tests/test_error_consolidator_enhanced.py`
  - New case: high-evidence member ensures merged preserves message and confidence not diluted

Performance
- O(n) over group size; small.

Acceptance Criteria
- No dilution of strong-evidence messages/confidence after merge

---

### 5) Soft confidence floors per rule (configurable)

Design
- Maintain universal hard threshold (0.35). Add optional per-rule soft floors that activate only when evidence is strong for that rule.
- Example: `inclusive_language` with evidence ≥ 0.85 → min confidence 0.60.

Implementation
- Config: extend `validation/config/validation_thresholds.yaml` or add `validation/config/confidence_soft_floors.yaml`:
  - Example entry: `inclusive_language: { evidence_min: 0.85, floor: 0.60 }`
- File: `error_consolidation/consolidator.py`
  - Load soft floors config at init (optional).
  - In `_apply_confidence_filtering`, before comparing to hard threshold, compute adjusted confidence: if `error.type` matches and `error.get('evidence_score', 0) >= evidence_min`, set `confidence = max(confidence, floor)`.

Tests
- Update: `validation/tests/test_error_consolidator_enhanced.py`
  - Assert that for configured rules with strong evidence, soft floor is applied
  - Assert that rules without config or weak evidence are unaffected

Performance
- Constant-time check per error; negligible.

Acceptance Criteria
- Soft floors only apply when configured and evidence is strong
- Universal threshold unchanged for other cases

---

### 6) Feedback‑informed reliability calibration (closed loop)

Design
- Periodically adjust rule reliability coefficients based on aggregated user feedback (precision/false‑positive rate) with safe bounds and smoothing.

Implementation
- File (new): `validation/feedback/reliability_tuner.py`
  - Functions: `compute_rule_precision(feedback_entries)`, `propose_adjustments(current_coeffs)`, `apply_adjustments(storage_path)`
  - Bound adjustments to ±0.02 per run; clamp to [0.70, 0.98].
- File: `validation/confidence/rule_reliability.py`
  - Load optional overrides from a JSON/YAML produced by tuner on startup.
- CLI/Job: add script entry point to run tuner daily; log diffs.

Tests
- New: `validation/tests/test_feedback/test_reliability_tuner.py`
  - Synthetic feedback sets → expected coefficient nudges within bounds
  - Idempotency and clamping behavior
- Update: `validation/tests/test_rule_reliability.py` to accept override path.

Performance
- Offline job; no runtime impact.

Acceptance Criteria
- Safe, incremental adjustments; reproducible and auditable

---

### 7) Mixed‑content safeguard for strong evidence

Design
- Do not penalize confidence due to mixed content when evidence is strong (evidence_score ≥ 0.85). Prevents dilution in heterogeneous docs.

Implementation
- File: `validation/confidence/confidence_calculator.py`
  - When `domain_analysis.mixed_content_detected` and `evidence_score ≥ 0.85`, skip/limit domain/content‑type penalties.

Tests
- Update: `validation/tests/test_confidence_normalization.py`
  - Mixed‑content with strong evidence → no penalty; with weak evidence → penalty applies

Performance
- No extra analysis.

Acceptance Criteria
- Mixed‑content no longer drags down strong evidence cases

---

### 8) Deterministic caching for session stability

Design
- Ensure identical inputs within a session yield identical confidence outputs; add optional TTL invalidation.

Implementation
- File: `validation/confidence/confidence_calculator.py`
  - Accept optional `session_id` in cache key generation; allow TTL per entry.
- File: `rules/base_rule.py`
  - Pass `session_id` from context (when available) into calculator via `additional_context`.

Tests
- New: `validation/tests/test_confidence/test_deterministic_caching.py`
  - Same input + session → identical scores; different session → allowed to differ only if underlying state differs
  - TTL expiry behavior

Performance
- Slightly larger cache key; negligible.

Acceptance Criteria
- No score flapping within a user session

---

### 9) Production guardrails and observability

Design
- Add counters for key events; surface in a lightweight metrics interface (logger or optional Prometheus hook).

Implementation
- File (new): `validation/monitoring/metrics.py`
  - Simple in‑process counters: `shortcut_applied`, `confidence_floor_triggered`, `consolidation_confidence_adjustments`
- Increment in:
  - Pipeline shortcut path (Upgrade 1)
  - Consolidation merged confidence adjustments (existing hook)
  - Soft floors application (Upgrade 5)
- Optional Prometheus exporter if env flag set.

Tests
- New: `validation/tests/test_enhanced_validation_performance.py`
  - Assert counters increment under synthetic scenarios (skip if exporter not present)

Performance
- O(1) increments; negligible.

Acceptance Criteria
- Metrics available in logs or /metrics when enabled

---

### 10) Robust early termination on decisive negative evidence

Design
- If any validator emits decisive negative evidence (e.g., `negative_context` ≥ 0.9), terminate pipeline with REJECT to save time and prevent false positives.

Implementation
- File: `validation/multi_pass/validation_pipeline.py`
  - During `_execute_validators` or right after, scan results; if decisive negative, short‑circuit to final result.
- Ensure feature flag (e.g., `ENABLE_NEGATIVE_EARLY_TERMINATION`) default on.

Tests
- New: `validation/tests/test_multi_pass/test_early_termination.py`
  - Negative‑evidence decisive → early REJECT; ensure timing is lower than non‑terminated path
  - Non‑decisive negatives → no early termination

Performance
- Saves time when triggered; no overhead otherwise.

Acceptance Criteria
- Correct early termination behavior without harming positives

---
### End-to-end testing and performance guardrails

Test Plan
- Run full suite: `pytest -q`
- Key suites to update/extend:
  - `validation/tests/test_confidence_normalization.py`
  - `validation/tests/test_error_consolidator_enhanced.py`
  - `validation/tests/test_production_validation.py`
  - New multi-pass tests under `validation/tests/test_multi_pass/` for shortcut and negative guards

Performance Budgets
- Confidence calculation: unchanged; <15ms per document (existing)
- Validation pipeline overhead from shortcut/guards: <2ms per error
- Consolidation overhead: unchanged; group-scoped O(n)

Monitoring & Observability (follow-up after 1–5)
- Add metrics: `confidence_floor_triggered`, `shortcut_applied`, `consolidation_confidence_adjustments`
- Track estimated FP via feedback correlation (reliability tuner; see Upgrade 6)

Rollback Plan
- Each upgrade isolated; feature flags can be added if needed:
  - `ENABLE_EVIDENCE_SHORTCUT`, `ENABLE_NEGATIVE_GUARDS`, `ENABLE_SOFT_FLOORS`

Completion Criteria
- All new and existing tests pass
- No performance regressions in CI timings
- Manual QA confirms fewer false positives on legacy/quoted/code contexts and higher confidence on strong-evidence detections



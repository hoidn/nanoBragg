# Source Weighting Implementation Plan (`[SOURCE-WEIGHT-002]`)

**Initiative:** `[TEST-SUITE-TRIAGE-001]` Sprint 1.2  
**Owner:** ralph  
**Priority:** High (Critical Path — Spec Compliance)  
**Status Snapshot (2026-01-19):** Phase A complete (Attempt #1 @ `20251011T062017Z`). Phase B artifacts (Attempt #15 @ `20251011T062955Z`) approved with Option A; Phase C implementation now active following `[TEST-SUITE-TRIAGE-001]` Phase K tracker refresh (C3 failures 6→4).

---

## Context
- Initiative: Restore AT-SRC-001 compliance so cluster C3 (six failures) can be cleared from the full pytest backlog.
- Phase Goal: Deliver spec-aligned source weighting semantics, implement them in PyTorch nanoBragg, and verify via Tier 1/Tier 2 tests.
- Dependencies:
  - `specs/spec-a-core.md` §§142–166 and AT-SRC-001 acceptance criteria (per-source λ + weight application).
  - `arch.md` §8 (physics scaling) and §15 (dtype/differentiability guardrails).
  - `docs/architecture/pytorch_design.md` §1.1.5 (current equal-weight assumption — must revisit).
  - `reports/2026-01-test-suite-triage/phase_j/20251011T062017Z/source_weighting/` (Phase A evidence bundle).
  - `docs/development/testing_strategy.md` §§1.4–2 for required pytest selectors and device coverage.

### Failure Summary (from Phase A)
- dtype mismatch: `read_sourcefile()` defaults to `torch.float32`, tests expect float64 (5/6 failures).
- Wavelength column ignored: simulator always uses CLI wavelength, diverging from current AT-SRC-001 expectations (2/6 failures).
- Weight column preserved but unused by simulator normalization (confirmed acceptable via Option A semantics).

---

### Phase A — Baseline Capture (Evidence-Only) ✅
Goal: Archive reproducible failure evidence and environment snapshot before modifying code.
Prereqs: None — kickoff step complete.
Exit Criteria: Baseline artifacts logged under `reports/.../<STAMP>/source_weighting/` with failure categorisation.

| ID | Task Description | State | How/Why & Guidance (including API / document / artifact / source file references) |
| --- | --- | --- | --- |
| A1 | Provision timestamped artifact bundle | [D] | `reports/2026-01-test-suite-triage/phase_j/20251011T062017Z/source_weighting/` (commands/env/logs). |
| A2 | Execute baseline pytest run | [D] | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py`; exit code + junit archived. |
| A3 | Capture environment snapshot | [D] | Python 3.13.5, torch 2.7.1+cu126, CUDA 12.6; see `env/`. |
| A4 | Categorise failures | [D] | `summary.md` documents dtype & wavelength gaps; ready for design work. |

---

### Phase B — Semantics Alignment & Design ✅
Goal: Resolve spec/test contradiction, lock the target behaviour, and outline the implementation/test plan before touching code.
Prereqs: Review Phase A artifacts; read spec/arch references listed above.
Exit Criteria: Design memo approved + fix_plan updated with Phase B decisions; ready to delegate implementation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Draft semantics brief | [D] | Attempt #15 → `semantics.md` reconciles spec §§142-166 vs AT-SRC-001, endorses Option A (equal weighting, CLI λ authority), and documents C reference inspection (`nanoBragg.c:2570-2720`). |
| B2 | Decide dtype strategy | [D] | Attempt #15 → Defines parser signature change to `dtype: Optional[torch.dtype] = None` with `torch.get_default_dtype()` fallback; preserves device neutrality. |
| B3 | Map implementation touchpoints | [D] | Attempt #15 → `implementation_map.md` inventories `io/source.py`, `tests/test_at_src_001*.py`, and spec update anchors with guardrail notes. |
| B4 | Define verification checklist | [D] | Attempt #15 → `verification_checklist.md` fixes Phase C/D selectors, artifact bundles, and success metrics for dtype + acceptance test alignment.

---

### Phase C — Implementation & Unit Tests (Active)
Goal: Implement Option A fixes (dtype neutrality + acceptance test alignment) while maintaining vectorized flows.
Prereqs: Phase B artifacts accepted; update docs/fix_plan Next Actions accordingly.
Exit Criteria: Code changes landed with targeted acceptance tests passing locally (no full suite yet).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Update source parser dtype handling | [ ] | Implement Option A dtype-neutral parser update; archive diff + before/after dtype inspection under new Phase C timestamp (Attempt #17). |
| C2 | Add dtype propagation regression test | [ ] | Author regression test covering caller-specified dtype/device; ensure parity with Option A semantics before moving on. |
| C3 | Align AT-SRC-001 expectations | [ ] | Refresh test assertions/spec excerpts to match Option A behaviour, documenting deltas in `verification_checklist.md`. |
| C4 | Targeted validation run | [ ] | Re-run `tests/test_at_src_001*.py` (CPU first, GPU when available) and capture logs under Phase C artifacts directory. |

---

### Phase D — Parity & Documentation Closure (Pending)
Goal: Verify Option A behaviour, refresh documentation, and archive artifacts for Sprint 1 handoff.
Prereqs: Phase C code merged into feature branch; initial targeted tests passing.
Exit Criteria: Updated docs + passing Tier 1/Tier 2 tests recorded; fix-plan item ready to close.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Run acceptance suite | [ ] | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py` on CPU and GPU (if available). Archive logs under new timestamp. |
| D2 | Full-suite regression delta | [ ] | `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ --maxfail=5`; confirm C3 cluster clears (36→≤30 failures). |
| D3 | Documentation updates | [ ] | Update `specs/spec-a-core.md` AT-SRC-001 wording, annotate `docs/development/pytorch_runtime_checklist.md` with dtype reminder, and record outcomes in docs/fix_plan.md. |
| D4 | Fix-plan closure | [ ] | Log Phase D artifacts (cpu/gpu logs, spec diff) and mark `[SOURCE-WEIGHT-002]` done once validations succeed. |

---

## References
- `reports/2026-01-test-suite-triage/phase_j/20251011T062017Z/source_weighting/` — Phase A evidence bundle.
- `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_sequence.md` — Sprint 1.2 roadmap.
- `docs/fix_plan.md` §[SOURCE-WEIGHT-002] — Ledger + attempts history.
- `specs/spec-a-core.md` §§142–166; `arch.md` §8, §15; `docs/architecture/pytorch_design.md` §1.1.5.
- `docs/development/testing_strategy.md` §§1.4–2 for required test cadence.

---

**Plan Status:** Phase B complete — Option A endorsed; Phase C active with Attempt #17 targeting dtype-neutral parser + AT-SRC-001 alignment.

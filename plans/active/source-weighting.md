# Source Weighting Implementation Plan (`[SOURCE-WEIGHT-002]`)

**Initiative:** `[TEST-SUITE-TRIAGE-001]` Sprint 1.2
**Owner:** ralph
**Priority:** High (Critical Path — Spec Compliance)
**Status Snapshot (2025-10-11):** Phase A complete (Attempt #1 @ `20251011T062017Z`). Phase B artifacts (Attempt #15 @ `20251011T062955Z`) approved with Option A. Phase C implementation COMPLETE (Attempt #17 @ `reports/2026-01-test-suite-triage/phase_j/20251011T064811Z/` — targeted pytest 10/10 passing). **Phase D1+D3 COMPLETE** (Attempt #18 @ `20251011T090906Z` — acceptance tests pass, spec updated); Phase D2 regression + D4 closure deferred per supervisor guidance.

---

## Context
- Initiative: Restore AT-SRC-001 compliance so cluster C3 (six failures) can be cleared from the full pytest backlog.
- Phase Goal: Deliver spec-aligned source weighting semantics, implement them in PyTorch nanoBragg, and verify via Tier 1/Tier 2 tests.
- Dependencies:
  - `specs/spec-a-core.md` §§142–166 and AT-SRC-001 acceptance criteria (per-source λ + weight application).
  - `arch.md` §8 (physics scaling) and §15 (dtype/differentiability guardrails).
  - `docs/architecture/pytorch_design.md` §1.1.5 (current equal-weight assumption — must revisit).
  - `reports/2026-01-test-suite-triage/phase_j/20251011T062017Z/source_weighting/` (Phase A evidence bundle).
  - `docs/development/testing_strategy.md` §§1.4–2 for required pytest selectors and device coverage.

### Failure Summary (from Phase A)
- dtype mismatch: `read_sourcefile()` defaults to `torch.float32`, tests expect float64 (5/6 failures).
- Wavelength column ignored: simulator always uses CLI wavelength, diverging from current AT-SRC-001 expectations (2/6 failures).
- Weight column preserved but unused by simulator normalization (confirmed acceptable via Option A semantics).

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
Prereqs: Review Phase A artifacts; read spec/arch references listed above.
Exit Criteria: Design memo approved + fix_plan updated with Phase B decisions; ready to delegate implementation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Draft semantics brief | [D] | Attempt #15 → `semantics.md` reconciles spec §§142-166 vs AT-SRC-001, endorses Option A (equal weighting, CLI λ authority), and documents C reference inspection (`nanoBragg.c:2570-2720`). |
| B2 | Decide dtype strategy | [D] | Attempt #15 → Defines parser signature change to `dtype: Optional[torch.dtype] = None` with `torch.get_default_dtype()` fallback; preserves device neutrality. |
| B3 | Map implementation touchpoints | [D] | Attempt #15 → `implementation_map.md` inventories `io/source.py`, `tests/test_at_src_001*.py`, and spec update anchors with guardrail notes. |
| B4 | Define verification checklist | [D] | Attempt #15 → `verification_checklist.md` fixes Phase C/D selectors, artifact bundles, and success metrics for dtype + acceptance test alignment.

---

### Phase C — Implementation & Unit Tests ✅
Goal: Implement Option A fixes (dtype neutrality + acceptance test alignment) while maintaining vectorized flows.
Prereqs: Phase B artifacts accepted; update docs/fix_plan Next Actions accordingly.
Exit Criteria: Code changes landed with targeted acceptance tests passing locally (no full suite yet).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Update source parser dtype handling | [D] | ✅ Attempt #17 logged in `source.py.diff`; no code change required beyond confirming `dtype: Optional[torch.dtype] = None` fallback. |
| C2 | Add dtype propagation regression test | [D] | ✅ Attempt #17 added parametrised `test_sourcefile_dtype_propagation` (float32/float64/None) with artifacts under `pytest_final.log`. |
| C3 | Align AT-SRC-001 expectations | [D] | ✅ Attempt #17 refreshed wavelength/dtype assertions in `tests/test_at_src_001*.py`; rationale captured in `summary.md`. |
| C4 | Targeted validation run | [D] | ✅ Attempt #17 `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001_simple.py tests/test_at_src_001.py` (10 passed, 1 warning) recorded in `pytest_final.log`. |

---

### Phase D — Parity & Documentation Closure (Partially Complete)
Goal: Verify Option A behaviour, refresh documentation, and archive artifacts for Sprint 1 handoff.
Prereqs: Phase C code merged into feature branch; initial targeted tests passing.
Exit Criteria: Updated docs + passing Tier 1/Tier 2 tests recorded; fix-plan item ready to close.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Run acceptance suite | [D] | ✅ Attempt #18 executed `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py -x` on CPU; 10 passed, 1 warning, runtime 3.93s. Artifacts: `reports/2026-01-test-suite-triage/phase_d/20251011T090906Z/source_weighting/`. |
| D2 | Full-suite regression delta | [ ] | Blocked until AT-SRC-001 tests become dtype-neutral. First update `tests/test_at_src_001_simple.py` expectations to use parser dtypes and add a float64-default fixture; rerun targeted selectors on both defaults. Then execute `CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/ --maxfail=0 --durations=25` to capture the new C3 counts. |
| D3 | Documentation updates | [D] | ✅ Attempt #18 updated `specs/spec-a-core.md:637` AT-SRC-001 text (references spec §151-155 + runtime checklist item #4); confirmed `docs/development/pytorch_runtime_checklist.md` item #4 already compliant (no edits needed). |
| D4 | Fix-plan closure | [ ] | ⏸ Pending D2 full-suite run. Then: mark `[SOURCE-WEIGHT-002]` done in docs/fix_plan.md with Phase D artifacts + remediation tracker update. |

---

## References
- `reports/2026-01-test-suite-triage/phase_j/20251011T062017Z/source_weighting/` — Phase A evidence bundle.
- `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_sequence.md` — Sprint 1.2 roadmap.
- `docs/fix_plan.md` §[SOURCE-WEIGHT-002] — Ledger + attempts history.
- `specs/spec-a-core.md` §§142–166; `arch.md` §8, §15; `docs/architecture/pytorch_design.md` §1.1.5.
- `docs/development/testing_strategy.md` §§1.4–2 for required test cadence.

---

**Plan Status:** Phases A–C complete (Attempt #17 delivers Option A implementation); **Phase D1+D3 complete (Attempt #18 @ 20251011T090906Z)**; Phase D2 regression + D4 closure deferred before closing `[SOURCE-WEIGHT-002]` and clearing C3.

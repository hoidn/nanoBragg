# Source Weighting Implementation Plan (`[SOURCE-WEIGHT-002]`)

**Initiative:** `[TEST-SUITE-TRIAGE-001]` Sprint 1.2  
**Owner:** ralph  
**Priority:** High (Critical Path — Spec Compliance)  
**Status Snapshot (2026-01-17):** Phase A complete (Attempt #1 @ `20251011T062017Z`). Phase B pending supervisor go-ahead.

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
- Wavelength column ignored: simulator always uses CLI wavelength, violating AT-SRC-001 (2/6 failures).
- Weight column preserved but unused by simulator normalization (needs confirmation during design).

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

### Phase B — Semantics Alignment & Design (Active)
Goal: Resolve spec/test contradiction, lock the target behaviour, and outline the implementation/test plan before touching code.
Prereqs: Review Phase A artifacts; read spec/arch references listed above.
Exit Criteria: Design memo approved + fix_plan updated with Phase B decisions; ready to delegate implementation.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Draft semantics brief | [ ] | Produce `reports/2026-01-test-suite-triage/phase_j/<STAMP>/source_weighting/semantics.md` summarising spec text vs AT expectations, proposing final rule (per-source λ + weight). Include recommendation for spec amendment (specs/spec-a-core.md) and architecture doc alignment. |
| B2 | Decide dtype strategy | [ ] | Document how `read_sourcefile()` and downstream configs honour caller-provided dtype/device while satisfying float64 tests (e.g., boundary conversion helper). Capture in semantics brief + update plan if additional helpers required. |
| B3 | Map implementation touchpoints | [ ] | Inventory modules requiring edits (`io/source.py`, `config.py`, `simulator.py`, potential BeamConfig plumbing). Provide file:line anchors and note existing guardrails (vectorization, differentiability). |
| B4 | Define verification checklist | [ ] | List required tests/commands (Tier 1 selectors, potential new regression, gradient checks) and artifact expectations for Phase C/Phase D. |

---

### Phase C — Implementation & Unit Tests (Pending)
Goal: Apply agreed semantics across parser + simulator while maintaining vectorized flows and dtype neutrality.
Prereqs: Phase B brief approved; update docs/fix_plan Next Actions accordingly.
Exit Criteria: Code changes landed with unit/acceptance tests passing locally (no full suite yet).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Update source parser | [ ] | Modify `io/source.py` to honour per-source λ/weight, default to caller dtype if provided, and issue targeted warnings only when spec requires. Ensure normalization of direction vectors stays differentiable. |
| C2 | Thread weights/λ through configs | [ ] | Ensure `BeamConfig` stores weights/wavelengths as tensors respecting dtype/device; adjust serialization/cache if needed. |
| C3 | Apply weighting in simulator | [ ] | Update `_compute_physics_for_position` + accumulation path to multiply intensities by weights and use per-source λ in q calculations. Maintain vectorization (no Python loops) and device/dtype neutrality. Reference `docs/architecture/pytorch_design.md` broadcast shapes. |
| C4 | Extend regression tests | [ ] | Augment `tests/test_at_src_001*.py` if additional asserts needed; add unit tests for dtype propagation if absent. Keep CPU/GPU parametrisation per testing_strategy §1.4. |

---

### Phase D — Parity & Documentation Closure (Pending)
Goal: Verify spec compliance, refresh documentation, and archive artifacts for Sprint 1 handoff.
Prereqs: Phase C code merged into feature branch; initial targeted tests passing.
Exit Criteria: Updated docs + passing Tier 1/Tier 2 tests recorded; fix_plan item ready to close.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Run acceptance suite | [ ] | `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_src_001.py tests/test_at_src_001_simple.py` on CPU and GPU (if available). Archive logs under new timestamp. |
| D2 | Gradient/edge validation | [ ] | Add/confirm gradcheck or targeted gradient tests touching source parameters; capture under `reports/` per testing_strategy. |
| D3 | Documentation updates | [ ] | Sync `specs/spec-a-core.md` (if amendment approved), `docs/architecture/pytorch_design.md` §1.1.5, and `docs/development/pytorch_runtime_checklist.md` to reflect new semantics. |
| D4 | Fix-plan closure | [ ] | Update `docs/fix_plan.md` attempts + exit criteria; note artifact paths; mark `[SOURCE-WEIGHT-002]` as done when tests + docs finalized. |

---

## References
- `reports/2026-01-test-suite-triage/phase_j/20251011T062017Z/source_weighting/` — Phase A evidence bundle.
- `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_sequence.md` — Sprint 1.2 roadmap.
- `docs/fix_plan.md` §[SOURCE-WEIGHT-002] — Ledger + attempts history.
- `specs/spec-a-core.md` §§142–166; `arch.md` §8, §15; `docs/architecture/pytorch_design.md` §1.1.5.
- `docs/development/testing_strategy.md` §§1.4–2 for required test cadence.

---

**Plan Status:** Phase B in progress — execute semantics/design tasks before code changes.

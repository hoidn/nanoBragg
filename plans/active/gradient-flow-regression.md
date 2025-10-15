## Context
- Initiative: GRADIENT-FLOW-001 — restore end-to-end gradients for the full simulation so `tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation` passes without manual skips.
- Phase Goal: Produce a reproducible remediation path that isolates where cell-parameter gradients vanish, implements the minimal fix, and verifies Tier-2/Tier-3 gradient coverage.
- Dependencies:
  - tests/test_gradients.py:360-444 — failing acceptance test for gradient flow.
  - arch.md §15 — gradient guardrails (device/dtype neutrality, compile guard requirements).
  - docs/development/testing_strategy.md §4.1 — Tier-2 gradient execution requirements and canonical commands.
  - docs/development/pytorch_runtime_checklist.md §"Gradient Tests" — environment guards for gradcheck/grad flow runs.
  - reports/2026-01-test-suite-triage/phase_o/20251015T043128Z/chunks/chunk_03/summary.md — latest failure evidence (C19 cluster) and timing data.
  - plans/active/test-suite-triage.md Phase O — establishes baseline counts (552/3/137) and follow-on remediation expectations.

### Phase A — Baseline Failure Capture
Goal: Reproduce the gradient failure with fresh artifacts and quantify current gradient magnitudes.
Prereqs: Editable install, `KMP_DUPLICATE_LIB_OK=TRUE`, `NANOBRAGG_DISABLE_COMPILE=1`, CPU execution (per testing_strategy §4.1).
Exit Criteria: Targeted pytest log + gradient snapshot stored under new phase directory with STAMP, documenting zero gradients per parameter.

| ID | Task Description | State | How/Why & Guidance (including commands) |
| --- | --- | --- | --- |
| A1 | Reproduce failure via targeted pytest run | [D] | Attempt #1 (20251015T052020Z) — artifacts stored under `reports/2026-01-gradient-flow/phase_a/20251015T052020Z/` with pytest log, XML, and exit code. |
| A2 | Record per-parameter gradient magnitudes | [D] | Attempt #1 captured `gradients.json`; all cell parameter gradients = 0.0 with loss 0.0. |
| A3 | Summarise baseline findings | [D] | `summary.md` in the same bundle documents zero-intensity observation and identifies missing structure-factor inputs as leading hypothesis. |

> Phase A exit criteria satisfied on 2025-10-15 (Attempt #1). Baseline evidence confirmed the simulation returns a zero-intensity image and zero gradients when the gradient-flow test uses default configuration values.

### Phase B — Gradient Path Audit (Callchain + Hooks)
Goal: Map where gradients are severed between `CrystalConfig` tensors and the simulator output using instrumentation without modifying production code.
Prereqs: Phase A artifacts complete; prompts/callchain.md reviewed.
Exit Criteria: Callchain bundle + hook-based tap notes pinpointing candidate breakpoints (e.g., config caching, `.detach()` usage).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B0 | Zero-intensity probe | [D] | Attempt #2 (20251015T053254Z) — executed control experiment comparing `default_F=0.0` vs `default_F=100.0`. Control case proves gradient graph **intact** (all six cell parameters have non-zero gradients when intensity > 0). Artifacts: `zero_intensity_probe.json`, `zero_intensity.md`, `summary.md`. |
| B1 | Run callchain tracing per SOP | [S] | SKIPPED — zero-intensity probe confirmed root cause without need for callchain instrumentation. Gradient path is not broken; zero gradients are mathematical result of zero intensity input. |
| B2 | Instrument autograd hooks | [S] | SKIPPED — no gradient break to instrument. Control experiment validated gradient graph integrity. |
| B3 | Consolidate findings | [D] | Completed in `summary.md` (20251015T053254Z). Root cause: missing structure factors (`default_F=0`) in test fixture. Gradient graph confirmed functional via control case. |

> Phase B exit criteria satisfied on 2025-10-15 (Attempt #2). Root cause identified (missing structure factors), gradient integrity validated (control case), environment captured. Callchain/hooks unnecessary — zero-intensity probe provided decisive evidence.

### Phase C — Hypothesis Testing & Fix Design
Goal: Validate leading hypotheses (e.g., cached `.detach()`, `.item()` use, tensor cloning without grad) and outline minimal remediation.
Prereqs: Phase B synopsis enumerating suspect sites.
Exit Criteria: Ranked hypotheses with supporting evidence, proposed code touchpoints, and acceptance checks recorded.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Audit Crystal caches for `.detach()` / `.item()` usage | [ ] | Review `src/nanobrag_torch/models/crystal.py` (focus on `get_real_space_vectors`, `get_misset_rotation`) and log any detaching operations. Document findings with file:line anchors in `reports/2026-01-gradient-flow/phase_c/$STAMP/cache_audit.md`. |
| C2 | Inspect simulator accumulation | [ ] | Examine `src/nanobrag_torch/simulator.py` sections that build the image tensor (vectorized loops, scaling). Confirm no intermediate uses `.detach()`/`.data` or converts tensors to numpy. Note any suspect operations (e.g., `.to(device)` on scalars). |
| C3 | Draft remediation options | [ ] | Based on audits, propose minimal fix alternatives in `design.md` (e.g., ensure config tensors are reused directly, remove `.detach()`). Include success metrics: targeted test passes, chunk 03 rerun (part3b) clean, gradcheck unaffected. |

### Phase D — Remediation & Verification
Goal: Implement agreed fix, validate across targeted and suite-level tests, and sync documentation.
Prereqs: Approved design from Phase C.
Exit Criteria: Gradient flow test green, chunk 03 summary updated, docs/fix_plan + remediation_tracker synced, plan ready for archive/move to done.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Land code fix with instrumentation cleanup | [ ] | Apply changes in src modules identified in Phase C; ensure compliance with arch.md §15 and vectorization guardrails. Add brief comments only where logic is non-obvious. |
| D2 | Run targeted + shard tests | [ ] | Execute `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 pytest -vv tests/test_gradients.py::TestAdvancedGradients::test_gradient_flow_simulation --maxfail=1`; rerun chunk 03 Part 3b selector with same guard to capture updated runtime stats. Store artifacts under `reports/2026-01-gradient-flow/phase_d/$STAMP/`. |
| D3 | Sync ledger & documentation | [ ] | Update `docs/fix_plan.md` `[GRADIENT-FLOW-001]` section, `reports/2026-01-test-suite-triage/remediation_tracker.md`, and append resolution notes to `plans/active/test-suite-triage.md` Phase O (or new Phase P). Stage plan for archive once tests remain green across one additional rerun. |

## Exit Criteria Summary
- Phase A baseline artifacts confirm failure state with reproducible commands.
- Phase B callchain + hooks identify the exact gradient break location.
- Phase C design packet captures minimal fix decision with documented hypotheses.
- Phase D validates fix via targeted tests and updates ledgers, restoring C19 to passing state.

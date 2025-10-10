## Context
- Initiative: VECTOR-PARITY-001 — unblock long-term Goals 1 and 2 by restoring ≥0.999 correlation for the 4096² warm-run benchmark so vectorization profiling (VECTOR-GAPS-002) and performance recovery (PERF-PYTORCH-004) can resume.
- Phase Goal: Produce a reproducible diagnosis track (evidence → scope → divergence → regression isolation) that explains the recurring 0.721 correlation and yields a validated fix with updated guardrails.
- Dependencies:
  - `specs/spec-a-core.md` §§4–5 — authoritative sampling, source handling, and scaling equations.
  - `arch.md` §§2, 8, 15 — broadcast shapes, device/dtype discipline, and differentiability guardrails.
  - `docs/architecture/pytorch_design.md` §1.1 & §1.1.5 — vectorization flows and equal-weight source contract.
  - `docs/development/testing_strategy.md` §§1.4–2 — authoritative parity/benchmark commands and acceptance thresholds.
  - `docs/development/pytorch_runtime_checklist.md` — runtime guardrail reminders (especially item #4 on source weighting).
  - `docs/fix_plan.md` `[VECTOR-GAPS-002]` Attempts #3–#8 and `[PERF-PYTORCH-004]` baseline expectations.
  - Existing artifacts: good run `reports/benchmarks/20251009-161714/`; failing bundles under `reports/2026-01-vectorization-gap/phase_b/20251009T09*` and `20251010T02*`.
- Status Snapshot (2026-01-07 → refreshed 2026-01-07 PM): Phase C traces complete; Phase D1–D5 are closed. Attempt #15 converted the rotated lattice vectors to meters (1e-10 factor) and recovered ROI parity (corr≈0.9999999985, |sum_ratio−1|≈1.3e-5). Attempt #16 retired NB_TRACE_SIM_F_LATT instrumentation with ROI parity intact (corr≈0.999999999, |sum_ratio−1|≈1.3e-5). Phase E now focuses on full-frame validation and ledger handback before reopening downstream vectorization/perf work.

### Phase A — Evidence Audit & Baseline Ledger
Goal: Canonicalise the good vs bad benchmark evidence and capture parameter parity so future loops operate from a single source of truth.
Prereqs: Read the referenced fix_plan attempts and gather artifact paths from `reports/`.
Exit Criteria: `reports/2026-01-vectorization-parity/phase_a/<STAMP>/` contains `artifact_matrix.md`, `param_diff.md`, and `commands.txt` documenting good/bad runs, CLI args, environment metadata, and unresolved questions; fix_plan `[VECTOR-PARITY-001]` updated with Attempt #1 summarising findings and linking the bundle.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Build artifact matrix | [D] | ✅ Attempt #1 (2025-10-09 ralph loop) captured seven runs in `reports/2026-01-vectorization-parity/phase_a/20251010T023622Z/artifact_matrix.md`, contrasting the 0.999998 good baseline (`reports/benchmarks/20251009-161714/`) with six 0.721175 failures (`reports/2026-01-vectorization-gap/phase_b/20251009T09*/`, `20251010T02*/`). |
| A2 | Diff benchmark parameters | [D] | ✅ Same bundle `param_diff.md` summarises commands/env metadata and notes missing git SHA for the good run; verified parity inputs match spec using `docs/development/c_to_pytorch_config_map.md`. |
| A3 | Record open questions & ledger hooks | [D] | ✅ Attempt #1 logged unresolved items (git provenance, absent sum_ratio) and updated `docs/fix_plan.md` `[VECTOR-PARITY-001]` with metrics, artifact paths, and Phase B focus. |

### Phase B — Reproduction Scope & Test Matrix
Goal: Confirm the regression on current HEAD, determine whether it affects smaller ROIs/tests, and document authoritative reproduction commands for debugging.
Prereqs: Phase A bundle published; repo clean; NB_C_BIN set to instrumented binary.
Exit Criteria: New evidence bundle under `reports/2026-01-vectorization-parity/phase_b/<STAMP>/` containing fresh 4096² run results, parity test outcomes, Option A golden-data assets, the high-resolution pytest selector log (expected FAIL), and ROI sanity checks; fix_plan Attempt #2 + forthcoming Attempt #6 summarise scope findings.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Re-run 4096² benchmark on HEAD | [D] | ✅ 2025-10-10 (Attempt #4) — Bundle copied to `reports/2026-01-vectorization-parity/phase_b/20251010T030852Z/` with profiler trace, benchmark_results.json (corr≈0.721 cold/warm, speedup≈1.13×), nb-compare summary (corr≈0.063, sum_ratio≈225×), and env metadata (git SHA fadee7f). `summary.md` documents the deterministic failure and 225× intensity inflation. |
| B2 | Run AT parity selectors (evidence capture) | [D] | ✅ 2025-10-10 (Attempt #5) — `KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg NB_RUN_PARALLEL=1 pytest -v tests/test_at_parallel_*.py -k 4096` produced 128 deselected tests / 0 selected (exit 5). Artifact: `reports/2026-01-vectorization-parity/phase_b/20251010T031841Z/pytest_parallel.log`. Result: **no active 4096² pytest parity coverage**, blocking downstream parity confirmation. |
| B3 | Decide 4096² validation path | [D] | ✅ 2025-10-10 (ralph Attempt #5) — `validation_path.md` in `reports/2026-01-vectorization-parity/phase_b/20251010T032937Z/` recommends **Option A** (un-skip high-res pytest using golden data) over harness/bootstrap alternatives. |
| B3a | Generate 4096² golden float image | [D] | ✅ 2025-10-10 (Attempt #6) — Generated C floatfile with canonical command; artifacts stored under `reports/2026-01-vectorization-parity/phase_b/20251010T034152Z/c_golden/` (command.log, checksum.txt, git_info.txt) and committed to `tests/golden_data/high_resolution_4096/image.bin` (64 MB, SHA recorded). |
| B3b | Document golden-data provenance | [D] | ✅ 2025-10-10 (Attempt #6) — Updated `tests/golden_data/README.md` Section 5 with command, ROI (512×512), acceptance thresholds, SHA256 checksum, and git provenance; summary captured in `reports/2026-01-vectorization-parity/phase_b/20251010T034152Z/summary.md`. |
| B3c | Implement ROI-based pytest body | [D] | ✅ 2025-10-10 (Attempt #6) — Replaced skip stub in `tests/test_at_parallel_012.py::test_high_resolution_variant` with ROI slice `[1792:2304, 1792:2304]`, NaN/Inf guards, Pearson correlation, and peak matching (≤1.0 px). Implementation remains batched and device/dtype neutral. |
| B3d | Execute targeted pytest (expected FAIL) | [D] | ✅ 2025-10-10 (Attempt #6) — Captured failure evidence in `reports/2026-01-vectorization-parity/phase_b/20251010T034152Z/pytest_highres.log` (corr=0.7157, 50/50 peak matches within ≤1.0 px, runtime ≈5.8 s). |
| B3e | Update ledgers with Option A progress | [D] | ✅ 2025-10-10 (Attempt #6) — Logged Attempt #6 in `docs/fix_plan.md` with metrics/artifact paths and refreshed this plan status; `summary.md` notes support downstream ROI tasks. |
| B4a | ROI sanity sweep via nb-compare | [D] | ✅ 2025-10-10 (Attempt #7) — `nb-compare --resample --roi 1792 2304 1792 2304` completed with **perfect correlation 0.999999999** (≈1.0) and sum_ratio 0.999987. Artifacts: `reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/`. **Critical finding**: ROI shows perfect parity, contradicting full-frame 0.721 → suggests edge/boundary artifact, not physics bug. |
| B4b | Summarise ROI findings | [D] | Completed `reports/2026-01-vectorization-parity/phase_b/20251010T035732Z/roi_compare/roi_scope.md` summarising full-frame vs ROI metrics, spec thresholds, and next-ROI recommendations; ready to brief Phase C trace staging. |

### Phase C — Divergence Localisation (Trace & Configuration)
Goal: Identify the first numeric divergence between C and PyTorch for the failing configuration, following the parallel trace SOP.
Prereqs: Phase B reproduction complete; confirm failure persists.
Exit Criteria: `reports/2026-01-vectorization-parity/phase_c/<STAMP>/` contains matched C/Py traces, diff annotations, and config audit notes pinpointing the first mismatched quantity; fix_plan Attempt #3 records locus and hypotheses.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Capture instrumented C trace | [D] | ✅ Attempt #8 (`reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/`) logged 72-point TRACE_C taps for pixels (2048,2048), (1792,2048), (4095,2048) with commands/env metadata. Note: current pixels sit in low-intensity background (F_cell=0) — retain observation for C3 hypothesis drafting. |
| C2 | Capture PyTorch trace | [D] | ✅ Attempt #9 (`reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/`) — Extended `scripts/debug_pixel_trace.py`, captured 72 tap points per pixel, validated via `pytest --collect-only -q`. Logs stored under `py_traces/` with commands/env metadata.
| C3 | Diff & hypothesise | [D] | ✅ Attempt #10 (`reports/2026-01-vectorization-parity/phase_c/20251010T061605Z/first_divergence.md`) — First divergence at `scattering_vec_A_inv` (10⁷× unit gap). Documented secondary hypotheses for fluence (10⁹×) and F_latt (~100×). Fix plan updated with sequenced remediation path. |
### Phase D — Physics Remediation (Scattering Vector & Scaling)
Goal: Implement and validate the three physics corrections identified in Phase C (scattering vector units, fluence scaling, F_latt normalisation) while keeping vectorization guardrails intact.
Prereqs: Phase C evidence reviewed; spec references (`specs/spec-a-core.md` §§4–5) confirmed; updated supervisor memo (input.md) delegates code changes to engineer.
Exit Criteria: Trace helper and simulator corrections merged locally with trace-backed verification, targeted pytest/nb-compare evidence captured, and fix_plan `[VECTOR-PARITY-001]` Next Actions advanced to validation stage.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Correct scattering vector units | [D] | ✅ Attempt #11 (`reports/2026-01-vectorization-parity/phase_d/20251010T062949Z/`) patched `src/nanobrag_torch/simulator.py` to emit m⁻¹, regenerated TRACE_PY for pixel (1792,2048) with rel_err ≤4.3e-14, and logged `diff_scattering_vec.md`. Pytest collection (692 tests) still passes. |
| D2 | Fix fluence scaling | [D] | ✅ Attempt #12 (`reports/2026-01-vectorization-parity/phase_d/20251010T070307Z/fluence_parity.md`) switched the trace helper to emit `beam_config.fluence`, removing the 1e9× underflow. Post-fix TRACE_PY vs TRACE_C rel_err=7.9e-16 (≤1e-3 target), pytest --collect-only (692 tests) clean. |
| D3 | Restore F_latt normalisation (trace helper) | [D] | ✅ Attempt #13 (`reports/2026-01-vectorization-parity/phase_d/20251010T071935Z/`) imports production `sincg` into the trace helper; TRACE_PY now matches TRACE_C within 5e-15. ROI `nb-compare` remains red only because the simulator still held Å-based lattice vectors prior to D4. |

| D4 | Diagnose simulator F_latt regression | [D] | ✅ Attempt #14 (`reports/2026-01-vectorization-parity/phase_d/20251010T073708Z/simulator_f_latt.md`) used NB_TRACE_SIM_F_LATT to show `h/k/l` were 10^10× too large (rot_a/b/c still in Å). Recommended fix: convert the rotated lattice vectors to m⁻¹ before calling `compute_physics_for_position()`. |
| D5 | ROI parity restore | [D] | ✅ Attempt #15 (`reports/2026-01-vectorization-parity/phase_d/roi_compare_post_fix2/summary.json`) multiplied `rot_a/b/c` by 1e-10 (Å→meters) inside `Simulator._compute_physics_for_position()`, reran the 512² ROI nb-compare, and achieved corr=0.9999999985 with |sum_ratio−1|≈1.3e-5. TRACE_PY logs refreshed under `py_traces_post_fix/`. |
| D6 | Instrumentation cleanup & guard | [D] | ✅ Attempt #16 (`reports/2026-01-vectorization-parity/phase_d/20251010T081102Z/cleanup/`) removed NB_TRACE_SIM_F_LATT hooks, reran `pytest --collect-only -q` (695 tests collected) and the ROI nb-compare command, and confirmed corr≈0.999999999 with |sum_ratio−1|≈1.3e-5. Phase D complete; proceed to Phase E full-frame validation. |

### Phase E — Fix Verification & Handback
Goal: Validate the eventual fix, restore guardrails, and unblock downstream plans.
Prereqs: Phase D tables [D] (including new simulator diagnostics); code changes staged with passing targeted validations.
Exit Criteria: Clean 4096² parity metrics archived, fix_plan & plans updated, blockers lifted; downstream vectorization/perf plans reactivated.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Verify fix across benchmarks/tests | [ ] | After D1–D5 work lands, rerun full 4096² benchmark (`scripts/benchmarks/benchmark_detailed.py` command from Phase B1) and the high-resolution pytest (`pytest tests/test_at_parallel_012.py::test_high_resolution_variant -v`). Archive outputs under `reports/2026-01-vectorization-parity/phase_e/<STAMP>/` and require corr ≥0.999, |sum_ratio−1| ≤5e-3. |
| E2 | Update ledgers & guardrails | [ ] | Refresh `docs/fix_plan.md` entries `[VECTOR-GAPS-002]`, `[PERF-PYTORCH-004]`, `[VECTOR-PARITY-001]`; update `plans/active/vectorization.md` Status Snapshot to unblock downstream Phases D–F; document guardrail adjustments (e.g., PyTorch unit expectations) in `docs/development/pytorch_runtime_checklist.md` if changed. |
| E3 | Archive plan | [ ] | Once parity + documentation updates are complete, move this plan to `plans/archive/vectorization-parity-regression.md` with closure summary + residual risks; log completion in `galph_memory.md`. |

## Reporting & Artifact Conventions
- Store all new evidence under `reports/2026-01-vectorization-parity/` grouped by phase and timestamp (`<STAMP>` = `YYYYMMDDTHHMMSSZ`). Never commit large raw traces; reference paths in fix_plan attempts.
- When invoking subagents (per CLAUDE.md), provide prompts including this plan, relevant spec sections, command templates, and required outputs.
- Default Mode: `Parity`. If a loop pivots to performance optimisation, ensure parity is locked first or document the temporary waiver in fix_plan.
- Re-run `pytest --collect-only -q` after any trace instrumentation or benchmark harness edits to confirm suite health before committing artifacts.

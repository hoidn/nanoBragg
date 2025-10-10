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
- Status Snapshot (2026-01-06): Phases A–B (including B4 ROI sweeps) are complete; the Phase C trace plan lives at `reports/2026-01-vectorization-parity/phase_c/20251010T040739Z/trace_plan.md`. Awaiting instrumented C/Py trace capture for pixels (2048,2048), (1791,2048), and (4095,2048) to localise the first divergence and unblock VECTOR-GAPS-002 / PERF-PYTORCH-004.

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
| C1 | Capture instrumented C trace | [ ] | Instrument `golden_suite_generator/nanoBragg.c` for pixels (2048,2048), (1791,2048), (4095,2048); print aggregated tap points (pix0_vector, pixel_pos, scattering_vec, hkl, F_cell, omega_pixel, steps, intensity). Rebuild and run the authoritative 4096² command (λ=0.5 Å, distance=500 mm, pixel=0.05 mm, MOSFLM convention), saving logs to `reports/2026-01-vectorization-parity/phase_c/<STAMP>/c_traces/`. Keep artifacts git-ignored (verify `git status` stays clean). |
| C2 | Capture PyTorch trace | [ ] | Extend `scripts/debug_pixel_trace.py` to accept the same pixel coordinates; run the 4096² parity config with `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel ${slow} ${fast}` (float64 CPU) so the tap points mirror the C trace, writing outputs to `reports/2026-01-vectorization-parity/phase_c/<STAMP>/py_traces/`. Run `pytest --collect-only -q` after script edits to confirm import health. |
| C3 | Diff & hypothesise | [ ] | Generate `reports/2026-01-vectorization-parity/phase_c/<STAMP>/first_divergence.md` plus `diff_*.txt` per pixel, recording the earliest mismatched variable and relative error; refresh fix_plan Attempts with findings and gate Phase D accordingly. |

### Phase D — Regression Isolation (Commit Forensics)
Goal: Identify the change that reintroduced the 0.721 correlation and document impact radius.
Prereqs: Divergence locus understood well enough to drive automation; good vs bad git commits enumerated.
Exit Criteria: `reports/2026-01-vectorization-parity/phase_d/<STAMP>/` hosts `git_walk.md`, bisect notes, and culprit summary; fix_plan Attempt #4 records offending commit(s) and affected modules/tests.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Identify known-good git_sha | [ ] | Use `git log --format="%h %ad %s" --since "2025-12-24" --until "2025-12-26"` plus Phase A metadata to pin the revision used for Attempt #5 (likely galph commit `05b648a`). Document findings in `git_walk.md`. |
| D2 | Run guided bisect | [ ] | `git bisect start` (bad = HEAD, good = identified known-good). For each candidate commit, run the Phase B1 benchmark command with `--outdir` set to `reports/2026-01-vectorization-parity/phase_d/<STAMP>/bisect/<commit>/`. Record correlation; abort bisect when culprit isolated; log results in `bisect_log.md`. |
| D3 | Summarise regression impact | [ ] | Draft `culprit_summary.md` outlining the change set, suspected subsystem, and affected tests/benchmarks. Flag whether follow-up work should reopen existing fix_plan items (e.g., SOURCE-WEIGHT-001) or create new ones. |

### Phase E — Fix Verification & Handback
Goal: Validate the eventual fix, restore guardrails, and unblock downstream plans.
Prereqs: Culprit commit understood; fix landed or patch ready for review.
Exit Criteria: Clean 4096² parity metrics archived, fix_plan & plans updated, blockers lifted.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E1 | Verify fix across benchmarks/tests | [ ] | After patch application, rerun Phase B commands plus any targeted pytest selectors from divergence analysis. Store outputs under `reports/2026-01-vectorization-parity/phase_e/<STAMP>/` and ensure correlation ≥0.999, |sum_ratio−1| ≤5e-3. |
| E2 | Update ledgers & guardrails | [ ] | Refresh `docs/fix_plan.md` entries `[VECTOR-GAPS-002]`, `[PERF-PYTORCH-004]`, `[VECTOR-PARITY-001]` with closure notes, and adjust `plans/active/vectorization-gap-audit.md`/`plans/active/vectorization.md` Status Snapshots to reflect unblocked state. |
| E3 | Archive plan | [ ] | Once evidence is green and downstream work resumes, move this plan to `plans/archive/vectorization-parity-regression.md` with summary + residual risks; log completion in `galph_memory.md`. |

## Reporting & Artifact Conventions
- Store all new evidence under `reports/2026-01-vectorization-parity/` grouped by phase and timestamp (`<STAMP>` = `YYYYMMDDTHHMMSSZ`). Never commit large raw traces; reference paths in fix_plan attempts.
- When invoking subagents (per CLAUDE.md), provide prompts including this plan, relevant spec sections, command templates, and required outputs.
- Default Mode: `Parity`. If a loop pivots to performance optimisation, ensure parity is locked first or document the temporary waiver in fix_plan.
- Re-run `pytest --collect-only -q` after any trace instrumentation or benchmark harness edits to confirm suite health before committing artifacts.

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
- Status Snapshot (2025-12-30): Eight consecutive Phase B1 profiler runs show deterministic correlation 0.721175 despite cache speedups; the last known-good run (Attempt #5) captured correlation 0.999998 but lacks git provenance. Downstream profiling and perf work remain blocked pending a parity root cause.

### Phase A — Evidence Audit & Baseline Ledger
Goal: Canonicalise the good vs bad benchmark evidence and capture parameter parity so future loops operate from a single source of truth.
Prereqs: Read the referenced fix_plan attempts and gather artifact paths from `reports/`.
Exit Criteria: `reports/2026-01-vectorization-parity/phase_a/<STAMP>/` contains `artifact_matrix.md`, `param_diff.md`, and `commands.txt` documenting good/bad runs, CLI args, environment metadata, and unresolved questions; fix_plan `[VECTOR-PARITY-001]` updated with Attempt #1 summarising findings and linking the bundle.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Build artifact matrix | [ ] | Catalogue known-good vs failing runs (paths, correlation, sum_ratio, commit if known) into `artifact_matrix.md`. Use `reports/benchmarks/20251009-161714/benchmark_results.json` for the good baseline and the `reports/2026-01-vectorization-gap/phase_b/20251009T09*/` + `20251010T02*/` bundles for failures. | 
| A2 | Diff benchmark parameters | [ ] | Extract command lines and env metadata from each run (`commands.txt`, `env.json` when present) and document differences in `param_diff.md`. Verify NB_C_BIN, ROI, dtype, and device align with the spec via `docs/development/c_to_pytorch_config_map.md`. |
| A3 | Record open questions & ledger hooks | [ ] | List unknowns (e.g., missing git_sha for good run) and note required follow-ups (AT suite coverage, trace status) inside `artifact_matrix.md`. Update `docs/fix_plan.md` `[VECTOR-PARITY-001]` with Attempt #1 referencing the Phase A bundle and outstanding items. |

### Phase B — Reproduction Scope & Test Matrix
Goal: Confirm the regression on current HEAD, determine whether it affects smaller ROIs/tests, and document authoritative reproduction commands for debugging.
Prereqs: Phase A bundle published; repo clean; NB_C_BIN set to instrumented binary.
Exit Criteria: New evidence bundle under `reports/2026-01-vectorization-parity/phase_b/<STAMP>/` containing fresh 4096² run results, parity test outcomes, and ROI sanity checks; fix_plan Attempt #2 summarises scope findings.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Re-run 4096² benchmark on HEAD | [ ] | Execute `NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-parity/phase_b/<STAMP>/profile/`. Capture `benchmark_results.json`, `profile_run.log`, `env.json`. Stop immediately if correlation ≥0.999 (document surprise). |
| B2 | Run AT parity selectors | [ ] | Invoke `KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg NB_RUN_PARALLEL=1 pytest -v tests/test_at_parallel_*.py -k 4096` (exact selectors per `docs/development/testing_strategy.md` §2). Store logs in `pytest_parallel.log`; note any failures/XFAIL transitions. |
| B3 | ROI sanity check via nb-compare | [ ] | Use `nb-compare --resample --outdir reports/2026-01-vectorization-parity/phase_b/<STAMP>/nb_compare -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 512` (small ROI) to verify whether the regression appears at reduced detector sizes. Include summary with correlation metrics. |

### Phase C — Divergence Localisation (Trace & Configuration)
Goal: Identify the first numeric divergence between C and PyTorch for the failing configuration, following the parallel trace SOP.
Prereqs: Phase B reproduction complete; confirm failure persists.
Exit Criteria: `reports/2026-01-vectorization-parity/phase_c/<STAMP>/` contains matched C/Py traces, diff annotations, and config audit notes pinpointing the first mismatched quantity; fix_plan Attempt #3 records locus and hypotheses.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Capture instrumented C trace | [ ] | Instrument `golden_suite_generator/nanoBragg.c` per `docs/debugging/debugging.md` and `docs/architecture/pytorch_design.md` §1.1.5; run the failing benchmark config to produce `c_trace.log` (focus on S, F_latt, polarization, scaling terms). Store under `phase_c/<STAMP>/c_trace.log`. |
| C2 | Capture PyTorch trace | [ ] | Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --config scripts/configs/benchmark_4096.json --pixel <hot_pixel>` (match ROI/pixel to C trace) to produce `py_trace.log`. Ensure tensor device/dtype align per runtime checklist. |
| C3 | Diff & hypothesise | [ ] | Create `trace_diff.md` summarising the first divergence, its magnitude, and suspected subsystem (e.g., steps normalisation, tricubic, polarization). Cross-reference spec clauses and fix_plan hypotheses. Update `docs/fix_plan.md` Attempt #3 with findings and recommended next debugging steps. |

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

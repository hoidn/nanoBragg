## Context
- Initiative: CLI-FLAGS-003 — unlock the supervisor parity command by aligning PyTorch CLI behavior with nanoBragg.c for `-nonoise` and `-pix0_vector_mm`.
- Current Objective: Finish the remaining φ=0 parity, scaling, and normalization work so the authoritative command below produces ≥0.9995 correlation, sum ratio 0.99–1.01, and ≤1 px mean peak distance.
  - Authoritative command (C + PyTorch parity harness):
    ```bash
    nanoBragg  -mat A.mat -floatfile img.bin -hkl scaled.hkl  -nonoise  -nointerpolate -oversample 1  -exposure 1  -flux 1e18 -beamsize 1.0  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080  -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866  -beam_vector 0.00051387949 0.0 -0.99999986  -Na 36  -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0
    ```
- Dependencies & references:
  - `specs/spec-a-cli.md` — Canonical CLI semantics for noise suppression and detector vectors.
  - `specs/spec-a-core.md:204-240` — Normative φ rotation pipeline (no carryover).
  - `docs/architecture/detector.md §5` — pix0 geometry formulas for BEAM/SAMPLE pivots.
  - `docs/development/c_to_pytorch_config_map.md` — Flag mapping and implicit pivot/convention rules.
  - `docs/development/testing_strategy.md §§1.4–2` — Required device/dtype smoke cadence and CLI acceptance tests.
  - `docs/bugs/verified_c_bugs.md:166-204 (C-PARITY-001)` — Source of the φ carryover bug that parity mode must emulate.
  - `plans/active/cli-phi-parity-shim/plan.md` — Companion plan governing the opt-in parity shim (Phase C complete, Phase D docs pending).
  - `reports/2025-10-cli-flags/phase_l/` — Canonical evidence directory (rot_vector, parity_shim, scaling_audit, nb_compare, supervisor_command).
- Status Snapshot (2025-12-02):
  - `-nonoise` CLI plumbing merged and covered by tests; noise writers are skipped when flag present.
  - pix0 precedence fixes landed; SAMPLE pivot error corrected to ≤0.2 µm (Attempt #129).
  - Spec-compliant φ rotation restored; optional C-parity shim implemented with dual tolerance decision (|Δk| ≤ 1e-6 spec, ≤5e-5 c-parity) pending documentation sync.
  - Scaling audit still shows first divergence at `I_before_scaling` (F_latt mismatch around HKL ≈ (−7,−1,−14)). Normalization fix + ROI nb-compare remain blocking.
  - Supervisor command parity run still outstanding; latest nb-compare attempt shows correlation ≈0.9965 and intensity ratio ≈1.26e5.
- Artifact Storage Convention: place new work in `reports/2025-10-cli-flags/phase_l/<phase_folder>/<timestamp>/` with `commands.txt`, raw logs, metrics JSON, and SHA256 hashes. Reference these paths in docs/fix_plan.md attempt logs and `fix_checklist.md`.

### Completed Foundations (Phases A–K)
Goal: Preserve provenance for earlier detector parity, pix0 precedence, and CLI parsing fixes while keeping this plan focused on the remaining gates.
Prereqs: Review archived evidence under `reports/2025-10-cli-flags/phase_[a-k]/` and Attempt log #1–#115 in `docs/fix_plan.md`.
Exit Criteria: Maintain pointers so regressions can be traced quickly; no further action required unless new bugs surface.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| K0 | Summary of prior phases | [D] | Parity pivots, pix0 precedence, and CLI parsing updates are recorded in `docs/fix_plan.md` Attempts #12–#115 and `reports/2025-10-cli-flags/` subfolders (phase_a … phase_k). See `PHASE_5_FINAL_VALIDATION_REPORT.md` for the last successful alignment before current regressions. |
| K1 | References for regression context | [D] | Use `reports/2025-10-cli-flags/phase_l/scaling_audit/` for current normalization deltas, and `parity_shim/` directories for φ carryover evidence. These remain authoritative until superseded. |

### Phase L — φ=0 Parity & Documentation Sync
Goal: Align documentation, checklists, and tests with the dual-mode (spec vs c-parity) behavior so VG‑1 tolerances are unambiguous.
Prereqs: `plans/active/cli-phi-parity-shim/plan.md` Phase C complete (C1–C4 ✅), dtype probe artifacts stored under `parity_shim/20251201_dtype_probe/`.
Exit Criteria: Updated documentation/tests/checklists reflecting the 1e-6 (spec) vs 5e-5 (c-parity) tolerances, Attempt log recorded, and plan ready to advance to scaling fixes.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| L1 | Sync tolerance notes into plan/checklists | [D] | ✅ Updated this plan, `plans/active/cli-phi-parity-shim/plan.md` Phase D tasks, and `reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md` dual-threshold section to cite spec (≤1e-6) vs c-parity (≤5e-5) tolerances. Artifacts: `reports/.../20251007T212159Z/`. |
| L2 | Refresh documentation set | [D] | ✅ Edited `reports/.../diagnosis.md` with Phase L sync note, updated `docs/bugs/verified_c_bugs.md` C-PARITY-001 entry to reference parity shim. Collected test selectors in `collect.log`. Commit sha will be recorded in fix_plan Attempt. |
| L3 | Log Attempt + fix_checklist updates | [D] | ✅ Appended Attempt #136 to `docs/fix_plan.md` CLI-FLAGS-003 with doc sync summary, tolerance thresholds (spec ≤1e-6, c-parity ≤5e-5), and artifact paths. Phase L complete. |

### Phase M0 — Trace Instrumentation Hygiene
Goal: Ensure CLI-FLAGS-003 debug instrumentation stays scoped to trace loops and remains device/dtype neutral before continuing Phase M.
Prereqs: Phase L complete; instrumentation from commit 9a8c2f5 captured in trace harness.
Exit Criteria: Debug helpers guarded behind the trace flag, tensors allocated on caller device/dtype, and findings logged in fix_plan with artifact paths under `reports/2025-10-cli-flags/phase_l/scaling_validation/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| M0a | Audit tricubic neighborhood cache scope | [D] | ✅ Attempt #144 (20251008T070513Z) guarded `_last_tricubic_neighborhood` behind `Crystal._enable_trace`; production runs clear the field. Evidence: `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T070513Z/instrumentation_audit.md`. |
| M0b | Keep debug tensors device/dtype neutral | [D] | ✅ Same attempt verified gather outputs already live on caller device/dtype; targeted pytest suite (CPU+CUDA, float32/float64) passes. Artifacts: `commands.txt`, `trace_py_scaling.log` under the 20251008T070513Z directory. |
| M0c | Document instrumentation toggle | [D] | ✅ Harness + audit describe enabling via `debug_config={'trace_pixel': ...}` and capture commands/SHA256. Fix-plan Attempt #144 logged with git SHA + artifact path. |

### Phase M — Structure-Factor & Normalization Parity (VG‑2)
Goal: Eliminate the `I_before_scaling` divergence by ensuring PyTorch fetches the same HKL amplitudes and lattice factors as C for the supervisor ROI pixels.
Prereqs: Phase L complete and Phase M0 instrumentation tasks marked [D] so traces/tests use aligned tolerances. Instrumentation from Phase L2b (`trace_harness.py`, simulator taps) already in place.
Exit Criteria: `trace_harness.py` comparisons show `F_cell`, `F_latt`, and `I_before_scaling` deltas ≤1e-6 relative, with artifacts under `reports/.../scaling_validation/`. Regression tests cover the fixed code path.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| M1 | Audit HKL lookup parity | [D] | ✅ **COMPLETE** (2025-10-08T07:25:13Z). `compare_scaling_traces.py` verified operational. Script successfully processes traces, generates metrics.json, and identifies I_before_scaling as first divergence (Δrel -2.086e-03, ~0.2%). All scaling factors downstream match C within tolerance (≤1e-6). Latest evidence: `20251008T072513Z` with validation_report.md, metrics.json, scaling_validation_summary.md. Previous SIGKILL issues resolved. Targeted tests 35/35 pass. Artifacts under `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T072513Z/`. |
| M2 | Fix lattice factor propagation | [ ] | Investigate `_compute_structure_factors` and `Crystal._tricubic_interpolation` for cases returning zero F_cell. Implement fix with nanoBragg.c reference (lines 2604–3278). Add targeted pytest (`tests/test_cli_scaling_phi0.py::test_I_before_scaling_matches_c`) covering the problematic HKL. |
| M3 | Re-run scaling comparison | [ ] | Execute `python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039` (CPU + CUDA). Confirm `metrics.json` reports first_divergence=None. Update Attempt log and `scaling_audit/scaling_comparison.md`. |
| M4 | Documentation + checklist | [ ] | Summarize findings in `scaling_audit/summary.md`, update `fix_checklist.md` VG-2 row, and log Attempt with metrics (I_before_scaling ratio, F_latt deltas). |

### Phase N — ROI nb-compare Parity (VG‑3 & VG‑4)
Goal: Once scaling is fixed, prove end-to-end image parity on the supervisor ROI using nb-compare and refreshed C/PyTorch outputs.
Prereqs: Phase M complete (scaling metrics green). Ensure documentation sync from Phase L2 finished.
Exit Criteria: nb-compare metrics satisfy correlation ≥0.9995, sum_ratio 0.99–1.01, peak alignment thresholds, with evidence stored under `reports/.../nb_compare_phi_fix/`.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| N1 | Regenerate outputs | [ ] | Run the supervisor command for both C (`NB_C_BIN=./golden_suite_generator/nanoBragg`) and PyTorch (`KMP_DUPLICATE_LIB_OK=TRUE nanoBragg --phi-carryover-mode c-parity ...`). Store float images and metadata under a new timestamp directory. |
| N2 | Execute nb-compare | [ ] | `nb-compare --roi 100 156 100 156 --resample --outdir reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/<timestamp>/ -- [command args]`. Capture `summary.json`, PNG visualizations, and CLI stdout. |
| N3 | Analyze + log | [ ] | Document correlation, RMSE, peak deltas in `analysis.md`. Update `docs/fix_plan.md` Attempts (VG-3/VG-4) and `fix_checklist.md` with pass/fail, thresholds, and artifact paths. |

### Phase O — Supervisor Command Closure (VG‑5)
Goal: Perform the final supervisor parity rerun, close out CLI-FLAGS-003, and archive artifacts.
Prereqs: Phases L–N complete with green metrics.
Exit Criteria: Supervisor command parity rerun recorded, Attempt logged with metrics, all documentation updated, and plan ready for archival.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| O1 | Final parity rerun | [ ] | Execute authoritative command via harness (CPU mandatory, CUDA optional) and store outputs in `reports/2025-10-cli-flags/phase_l/supervisor_command_rerun/<timestamp>/`. Include stdout/stderr, SHA256, and environment JSON. |
| O2 | Attempt + documentation | [ ] | Add Attempt entry summarizing metrics (correlation, sum_ratio, mean_peak_distance), update `fix_checklist.md` VG-5 row, and note closure in `docs/bugs/verified_c_bugs.md` if behavior changes. |
| O3 | Archive + handoff | [ ] | Move stabilized artifacts to `reports/archive/cli-flags-003/`, update this plan’s status to “ready for archive,” and provide final supervisor notes for future maintenance. |

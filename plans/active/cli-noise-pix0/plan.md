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
- Status Snapshot (2025-12-07 refresh):
  - `-nonoise` CLI plumbing merged and covered by tests; noise writers are skipped when flag present.
  - pix0 precedence fixes landed; SAMPLE pivot error corrected to ≤0.2 µm (Attempt #129).
  - Spec-compliant φ rotation restored; optional c-parity shim implemented with dual tolerance decision (|Δk| ≤ 1e-6 spec, ≤5e-5 c-parity); Phase C5 documentation still pending.
  - Commit 3269f6d (2025-10-08) introduced `_phi_carryover_cache` and `test_cli_scaling_parity`, yet the latest scaling harness (`reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T081932Z/`) still reports F_latt = -2.380134 vs C = -2.383196653 (ΔI_before_scaling = -1968.57, -0.209% relative), so VG-2 remains red.
  - Attempt #151 (2025-10-22) added `reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md`, confirming the cache never fires within a run, `.detach().clone()` severs gradients, and Option 1 (pixel-indexed cache with deferred substitution) is the required redesign before metrics can improve.
  - Attempt #152 (2025-10-22) archived paired-pixel traces (`reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T100653Z/carryover_probe/`) and extended the Option 1 design with explicit tensor shapes, lifecycle rules, and gradient guarantees, so implementation work can proceed with concrete requirements.
  - Canonical artifacts (`scaling_validation_summary.md`, `metrics.json`, `run_metadata.json`) under `20251008T072513Z/` remain the last synchronized baseline; newer timestamps document the failing attempt and should be referenced when diagnosing carryover behavior.
  - Supervisor command parity run still outstanding; latest nb-compare attempt shows correlation ≈0.9965 and intensity ratio ≈1.26e5.
- Next Actions (2025-12-07 refresh):
  1. **M2e scaling-parity test harness** — Keep `tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c` red but reproducible; capture current failure output (CPU float64, Δ≈0.209%) under a fresh timestamp and link it in `lattice_hypotheses.md` before code edits.
  2. **M2g–M2h implementation & validation** — Implement the Option 1 pixel-indexed cache per the 20251008T100653Z design notes (no `.detach()`, device/dtype neutral). Validate with targeted pytest (CPU mandatory, CUDA when available) plus a minimal gradcheck, archiving logs under `reports/.../carryover_cache_validation/<timestamp>/`.
  3. **M2i + M3 reruns** — Regenerate cross-pixel traces and `trace_harness.py` metrics post-fix (CPU float64, `--roi 684 686 1039 1040`) to confirm `first_divergence=None`, then execute the single-pixel harness for Phase M3.
  4. **M4 documentation and downstream phases** — Once VG‑2 is green, refresh scaling documentation (M4), then advance to nb-compare (Phase N) and the supervisor parity rerun (Phase O).
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
| M1 | Audit HKL lookup parity | [D] | Scripted workflow confirmed healthy (see `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T072513Z/validation_report.md`). Retain 20251008T060721Z manual summary for historical context, but treat 20251008T072513Z artifacts as the active baseline while chasing the F_latt delta. |
| M2 | Fix φ=0 carryover parity | [P] | Commit 3269f6d added `_phi_carryover_cache` and `test_cli_scaling_parity`, but `trace_harness.py` (20251008T081932Z) still reports F_latt=-2.380134 vs C=-2.383196653 (ΔI_before_scaling=-1968.57, -0.209% relative). Attempt #151 isolated the cache scope issue; Attempt #152 captured the paired-pixel probe and expanded `phi_carryover_diagnosis.md` with Option 1 tensor shapes/lifecycle. Execute the remaining M2e–M2i tasks to keep the regression test red yet reproducible, land the pixel-indexed cache implementation, and validate gradients/device parity before rerunning metrics. |
| M3 | Re-run scaling comparison | [ ] | Execute `python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039` (CPU + CUDA). Confirm `metrics.json` reports first_divergence=None. Update Attempt log and `scaling_audit/scaling_comparison.md`. |
| M4 | Documentation + checklist | [ ] | Summarize findings in `scaling_audit/summary.md`, update `fix_checklist.md` VG-2 row, and log Attempt with metrics (I_before_scaling ratio, F_latt deltas). |

#### M1 Tooling Checklist — Restore Scripted Scaling Comparison
| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| M1a | Capture failing repro | [D] | Documented in `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T060721Z/commands.txt` (manual summary plus exit status). No new repro needed unless the script regresses again. |
| M1b | Patch `compare_scaling_traces.py` | [D] | Stability verified via 20251008T072513Z run; script handles `TRACE_PY_TRICUBIC*` payloads without crashing (Attempt #145). |
| M1c | Regenerate canonical artifacts | [D] | `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T072513Z/` contains refreshed summary, metrics.json, run_metadata.json, and device/dtype pytest logs. |
| M1d | Update plan + ledger | [D] | M1 reopened on 2025-12-06; re-closed now referencing Attempt #145 artifacts. Ensure docs/fix_plan.md references the same timestamp (see Attempt #145). |

#### M2 Analysis Checklist — Diagnose `F_latt` Drift
| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| M2a | Refresh trace & scaling summary | [D] | ✅ Created `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/` and executed `trace_harness.py` (CPU, float64, `--phi-mode c-parity`) plus `scripts/validation/compare_scaling_traces.py`. All artifacts stored: `commands.txt`, `trace_py_scaling.log`, `scaling_validation_summary.md`, `metrics.json`, `run_metadata.json`, `compare_scaling_traces.stdout`, `pytest_collect.log`, `dir_listing.txt`, `sha256.txt`. Git SHA: f522958. |
| M2b | Manual `sincg` reproduction | [D] | ✅ Generated `20251008T075949Z/manual_sincg.md` with per-axis sincg calculations. Key findings: PyTorch product using sincg(π·(frac-h0)) = 2.380125274 vs C F_latt = -2.383196653 (0.13% relative delta). Individual axis comparisons show all three axes (a, b, c) contribute small deltas to the overall 0.13% mismatch. |
| M2c | Hypothesis log | [D] | ✅ `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md` captures HKL deltas, rotated-vector mismatches, and the follow-up probes (float64 rerun + per-φ taps). Ready to progress to implementation work. |
| M2d | Cross-pixel carryover probe | [D] | ✅ `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T100653Z/carryover_probe/` stores paired traces for pixels (684,1039)→(685,1039) plus analysis.md confirming φ=0 uses fresh vectors. `lattice_hypotheses.md` updated with deltas and Option 1 requirements (Attempt #152). |
| M2e | Validate scaling parity test | [D] | ✅ Attempt #153 (20251008T102155Z) captured failing parity test with F_latt relative error 157.88% (expected -2.383197, got 1.379484). Artifacts stored in `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T102155Z/parity_test_failure/` including `pytest.log` (182 lines), `commands.txt`, `env.json`, `collect.log`, and `sha256.txt`. Test documented in `lattice_hypotheses.md` with root cause confirmation: current cache operates between `run()` invocations, not per-pixel. Ready for M2g–M2i implementation. |

#### M2 Implementation Checklist — Pixel-Indexed Cache (Option 1)
| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| M2f | Finalise Option 1 data flow | [D] | ✅ Attempt #152 extended `phi_carryover_diagnosis.md` with cache tensor shape `(S,F,N_mos,3)`, lifecycle/reset rules, call sequence (Option 1A), gradient guarantees, and C-code citations (`nanoBragg.c:2797,3044-3095`). |
| M2g | Implement vectorised cache plumbing | [ ] | Introduce a pixel-indexed cache on the crystal (shape `(S,F,N_mos,3)` per vector) that stores φ=final outputs on the active device/dtype. Add an `apply_phi_carryover(pixel_s, pixel_f, real_vecs, recip_vecs)` helper invoked from `_compute_physics_for_position` (and trace harness) when `phi_carryover_mode="c-parity"`. Use tensor indexing/scatter ops—no `.detach()`, no in-place writes that would break autograd. Document code with required C snippets per CLAUDE Rule #11. |
| M2h | Gradient & device validation | [ ] | Run targeted selectors `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c --device=cpu` and, when CUDA available, the GPU parametrisation. Add a minimal gradcheck (float64, 2×2 ROI) to confirm carryover keeps gradients alive. Store logs under `reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/carryover_cache_validation/` with `commands.txt`, `env.json`, and exit codes. |
| M2i | Regenerate cross-pixel traces | [ ] | After implementation, rerun `python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --roi 684 686 1039 1040 --phi-mode c-parity` (CPU float64) and stash outputs (`trace_py_scaling.log`, `metrics.json`, `diff.md`) under `reports/.../carryover_probe/<timestamp>/`. Update `lattice_hypotheses.md` and `scaling_validation_summary.md` with the new evidence (expect first_divergence=None) before moving to M3. |

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

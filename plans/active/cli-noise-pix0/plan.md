## Context
- Initiative: CLI Parity for nanoBragg PyTorch vs C (supports long-term goal in prompts/supervisor.md)
- Phase Goal: Accept `-nonoise` and `-pix0_vector_mm` flags with C-equivalent semantics so the parallel comparison command in prompts/supervisor.md executes end-to-end.
- Dependencies: specs/spec-a-cli.md §§3.2–3.4, docs/architecture/detector.md §5, docs/development/c_to_pytorch_config_map.md (detector pivot + noise), golden_suite_generator/nanoBragg.c lines 720–1040 & 1730–1860 (flag behavior), docs/debugging/detector_geometry_checklist.md (pix0 validation), docs/development/testing_strategy.md §2 (CLI parity tests).
- Gap snapshot update (2025-11-23 PM): Attempt #109 regenerated the TRACE_C_PHI log under `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/` and re-ran `compare_per_phi_traces.py`; Δk now measures 1.8116e-2 at φ_tic=0 while φ≥1 stay within 2.85e-5, confirming the carryover mismatch and leaving VG-1 blocked until the remediation lands.
- Current gap snapshot (2025-10-18 refresh): Phase H4 parity landed (Attempt #25) with pix0 deltas < 2e-8 m and regression tolerances tightened; the remaining blocker before executing the supervisor command end-to-end is Phase I polarization alignment.
- Gap snapshot refresh (2025-10-07 08:41): Attempt #101 activated TRACE_C_PHI (C instrumentation) and captured matching Py per-φ traces. Divergence isolated to φ_tic=0 (Δk≈1.81e-2) while φ>0 steps remain within 3e-5. Phase L3k.3 moves to φ=0 initialization parity (L3k.3c) plus ROI/nb-compare follow-ups.
- Gap snapshot update (2025-10-19): Attempt #27 parity run reveals 1.24538e5× intensity scaling mismatch despite polarization fix; Phases J–L track the normalization diagnosis, fix, and closure required before long-term Goal #1 completes.
- Gap snapshot refresh (2025-10-22): Attempt #31 restored C precedence for custom detector vectors (pix0 override now gated again). Outstanding work: H5c PyTorch traces and Phase K normalization to eliminate the `F_latt`-driven intensity gap.
- Gap snapshot update (2025-10-24): Attempt #35 reran the PyTorch trace harness post-unit-fix; metrics still show |Δpix0| ≈ 1.145 mm, so a fresh diagnostics phase is required before resuming normalization work.
- Gap snapshot refresh (2025-10-26): Attempt #40 completed Phase H6f — custom detector vectors now force SAMPLE pivot parity, parity visuals relocated under `reports/2025-10-cli-flags/phase_h6/visuals/`, and targeted regression tests cover pivot selection. Outstanding work at that point: Phase H6g trace rerun to confirm |Δpix0| < 5e-5 m before returning to Phase K scalings.
- Gap snapshot update (2025-10-27): Attempt #41 validated Phase H6g — SAMPLE pivot parity holds with pix0 deltas ≤2.85 µm, beam center deltas 0.0, and supporting artifacts under `reports/2025-10-cli-flags/phase_h6/post_fix/`. Remaining blockers: rerun the scaling chain (Phase K2), execute the scaling regression + doc updates (Phase K3), then resume Phase L parity once normalization matches C.
- Gap snapshot refresh (2025-11-09): Attempt #49 closed Phase K3g3 — `tests/test_cli_scaling.py::test_f_latt_square_matches_c` now passes after isolating the HKL cache, but the full supervisor command still shows correlation ≈ 0.9965 and sum_ratio ≈ 1.26×10⁵. Need fresh HKL/normalization parity evidence (Phase L) before rerunning nb-compare.
- Gap snapshot refresh (2025-11-10): Attempt #56 (evidence loop) proved the existing `TRACE_PY` path prints placeholder scaling data (`capture_fraction 1`, `polar 1.0`, `steps`=φ-steps only). Without exposing the real per-pixel factors computed in `Simulator.run`, Phase L2b cannot produce a trustworthy PyTorch trace. Instrumentation must pull actual values from `_apply_detector_absorption`, polarization kernels, and total-step calculation before rerunning the harness.
- Gap snapshot update (2025-10-17): Attempt #53 (Phase L1c) realigned HKL Fdump I/O with C padding (`read_fdump`/`write_fdump`) and added regression coverage (`TestHKLFdumpParity::test_scaled_hkl_roundtrip`) with max |ΔF| = 0.0. Proceed to L1d to regenerate parity metrics before reviving scaling traces.
- Gap snapshot update (2025-11-11): Discovered the trace harness omitted `-beam_vector`, `-flux`, and `-beamsize`, forcing oversample=4 and a +Z beam; Py traces zeroed `F_cell` and inflated `steps`. Marked unresolved pending harness fix.
- Gap snapshot refresh (2025-11-12): Attempt #66 (commit 1d2e6ac) completed Phase L2b0 — the trace harness now feeds the full supervisor flag set, and the refreshed `trace_py_scaling.log` confirms `steps=10`, `fluence≈1.0e24`, and `r_e^2` parity with C. TRACE_PY still reports `I_before_scaling NOT_EXTRACTED`, `polar=0`, and `I_pixel_final=0`, so Phase L2b instrumentation must surface the real polarization/absorption tensors before we can quantify the K3e k_frac drift.
- Gap snapshot update (2025-11-13): Latest harness rerun aborted because `trace_harness.py` still expected the legacy `read_hkl_file` return tuple (see `trace_py_fullrun.log`). **Resolved in Attempt #74, which updated the harness to the `(F_grid, metadata)` signature.**
- Gap snapshot refresh (2025-11-14): Attempt #73 showed `Crystal.hkl_data` unset (leading to `F_cell=0`), keeping L2b open; **Attempt #74 fixed this by wiring the HKL tensor/metadata before Simulator construction.**
- Gap snapshot refresh (2025-11-15): Attempts #69/#71/#74 finished Phase L2 — TRACE_PY now reports real scaling factors, `scaling_audit_summary.md` flags `I_before_scaling` as the lone divergence, and C shows `F_cell=190.27` for hkl=(-7,-1,-14) while PyTorch remains at 0. Next phase focuses on understanding how C derives that amplitude (likely via generated `Fdump.bin`) before touching normalization code.
- Gap snapshot update (2025-11-22): Attempt #101 (L3k.3b evidence loop) regenerated per-φ PyTorch traces and confirmed k_frac span=1.8088e-2. No matching `TRACE_C_PHI` lines exist in the current C trace, so the comparison tooling falsely reports "parity achieved." Phase L3k now requires explicit instrumentation of the golden C binary plus a guard that treats missing C data as a blocking failure before nb-compare/ROI work resumes.
- Gap snapshot refresh (2025-11-17): Attempt #77 reran Phase L3a probe on the current workstation, logged `probe_20251117.log` (F_cell=190.270004 for hkl=(-7,-1,-14)), and confirmed scaled.hkl already covers the supervisor reflection. Remaining blockers shift to wiring that data through the harness/CLI path (Phase L3c onward).
- Gap snapshot update (2025-11-17 late): Attempt #78 completed the Phase L3c harness rerun; TRACE_PY now reports F_cell=190.27 with matching metadata, so the immediate focus moves to auditing CLI ingestion (L3c) and adding regression coverage (L3d).
- Gap snapshot refresh (2025-11-18): Attempt #80 (evidence loop) closed Phase L3c — `cli_hkl_audit.md` now documents the missing `.to(device=device)` transfer at `__main__.py:1073`, confirmed probe artifacts, and queued the device fix + regression test for L3d.
- Gap snapshot update (2025-11-18 late): Attempt #81 implemented `.to(device=device, dtype=dtype)` and added the `TestHKLDevice::test_hkl_tensor_respects_device` regression (CPU/CUDA × float32/float64). Next blocker: Phase L3e scaling validation to prove all factors match C (≤1e-6) before rerunning nb-compare in Phase L4.
- Gap snapshot addendum (2025-10-06T17:59 replayed 2025-11-09): Re-running Phase L1 with `Fdump_scaled_20251006175946.bin` shows the cache stores 182,700 doubles (≈9,534 more than the 173,166 expected from header ranges) and that reflections shift by Δk≈+10–12 / Δl≈−2…−8 relative to HKL indices. Use this dataset to reverse-engineer the C layout before touching PyTorch HKL IO.
- Gap insight (2025-10-31): Scaling evidence shows MOSFLM matrix runs still rescale real vectors using formula lengths; C skips that step unless `-cell` is provided, so PyTorch must gate the `vector_rescale` analogue when `mosflm_a_star` is set. The same trace confirms the polarization Kahn factor should default to 0.0 (C’s `polarization`), not 1.0, so BeamConfig defaults need to be realigned before Phase L.
- Gap correction (2025-10-22): Fresh C evidence (`reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md`) proves nanoBragg ignores `-pix0_vector_mm` whenever custom detector vectors are present. PyTorch now deviates because the lattice factor uses fractional indices (h−h0); fix required before normalization parity.
- Gap recap (2025-11-05): Manual inspection of `src/nanobrag_torch/models/crystal.py` shows the cross-product rescale still runs even when MOSFLM reciprocal vectors are supplied (lines 681-705), and `BeamConfig.polarization_factor` defaults to 1.0, so scaling remains off despite SAMPLE pivot parity.
- Gap snapshot update (2025-11-06): Traces (`reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log`) show the SAMPLE pivot fix leaves residual close-distance deltas (~2.8 µm), which push the fractional Miller index from 2.0012 (C) to 1.9993 (PyTorch). Those 0.002 shifts around integer values amplify sincg results (F_latt_b ≈ +21.6%). Need dtype diagnostics to confirm float32 rounding vs geometry formula drift before coding a fix.
- Gap snapshot refresh (2025-11-07): dtype sweep (`reports/2025-10-cli-flags/phase_k/f_latt_fix/dtype_sweep/`) rules out precision and exposes a φ-grid mismatch—PyTorch logs `k≈1.9997` (φ=0°) while C logs `k≈1.9928` (φ=0.09°). Next action: capture per-φ traces to align sampling before rerunning normalization tests.
- Gap snapshot refresh (2025-11-19): Latest scaling audit (`reports/2025-10-cli-flags/phase_l/scaling_validation/analysis_20251119.md`) shows `F_cell` parity restored while per-phi instrumentation (Attempt #86) now emits the expected `TRACE_PY_PHI` entries. The refreshed log exposes a residual phi=0 mismatch (`k_frac` -0.589 in PyTorch vs -0.607 in C) that flips `F_latt_b`’s sign, so Phase L3 needs a dedicated rotation-vector audit before touching normalization again.
- Gap snapshot refresh (2025-11-20): Attempt #89 (ralph loop i=90) completed the Phase L3g spindle/volume probe. `spindle_audit.log` and `volume_probe.md` confirm reciprocal vectors retain ≤1e-9 alignment while real-space Y components drift (b_y +6.8%). Hypothesis H2 (V_formula vs V_actual) is ruled out; remaining blocker is capturing `TRACE_PY: spindle_axis` output so spindle normalization can be proven (or disproven) before code edits.
- Gap snapshot update (2025-11-20 evening): Attempt #93 diff confirmed MOSFLM base vectors align ≤1e-7 Å, promoting **H5 (φ rotation application)** as the primary suspect. Before implementation, Phase L3j must lock verification gates (per-φ trace, targeted pytest, nb-compare ROI) so the eventual fix can be validated against specs/spec-a-cli.md §3.3 and CLAUDE Rules 12/13.
- Gap snapshot recap (2025-11-22): L3k.2 landed (Attempt #97) with reciprocal recompute + docstring, VG-2 passed (Attempt #98), but VG-1/VG-3 failed (Attempt #99) — k_frac span 1.8×10⁻², correlation 0.985, sum_ratio 1.16×10⁵ because the C ROI sum came back ≈0. Attempt #100 realigned the φ=0 tests to the supervisor spindle axis so the drift is now captured in red tests. Focus next: diagnose the residual φ rotation error, fix the nb-compare ROI anomaly, then rerun VG-1⇢VG-4 before logging L3k.4.
- Diagnostic note (2025-11-08 galph audit): `scripts/trace_per_phi.py` currently subtracts `pix0_vector` from `detector.get_pixel_coords()`, yielding plane-relative vectors instead of sample-to-pixel paths. Fix this double subtraction in the Phase K3f PyTorch harness before recording new parity traces.
- Gap confirmation (2025-11-08 trace diff): Phase K3f base-lattice traces show PyTorch keeps the placeholder unit cell volume (`V≈1 Å^3`) when MOSFLM vectors are supplied, so `Crystal.compute_cell_tensors` fails to rescale the real vectors. C multiplies `b*×c*` by `V_cell≈2.4682×10^4 Å^3` before converting to meters, yielding |a|≈26.75 Å; PyTorch leaves |a|≈5.8×10^3 Å, which in turn inflates h/k/l by ≈6 units. Fix requires mirroring the MOSFLM derivation pipeline in `Crystal.compute_cell_tensors` (see `specs/spec-a-core.md` Geometry + `golden_suite_generator/nanoBragg.c` 3135-3210).
- Gap snapshot update (2025-11-08 evening): Commit 46ba36b implements the MOSFLM rescale path and new regression test `TestMOSFLMCellVectors::test_mosflm_cell_vectors` passes (see `reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/cell_tensors_py.txt`). Base-lattice summary now records the fix; remaining blocker is Phase K3g3 to rerun scaling evidence and refresh nb-compare/pytest artifacts.
- Evidence status: Phase E artifacts (`reports/2025-10-cli-flags/phase_e/`) hold C/PyTorch traces, diffs, and beam-vector checks. Phase H3b1 also stashes WITH/without override traces under `reports/2025-10-cli-flags/phase_h/implementation/` for reference.
- Documentation anchors for this focus:
  * `specs/spec-a-core.md` — canonical lattice-factor formulas (SQUARE uses sincg(π·h, Na); ROUND/GAUSS definitions used to verify Phase K).
  * `golden_suite_generator/nanoBragg.c` (≈2993-3151) — definitive implementation of the sincg calls and rounding logic.
  * `docs/architecture/pytorch_design.md` — simulator reference; docstring currently claims full-h usage and must be updated post-fix.
  * `docs/development/testing_strategy.md` — authoritative pytest/trace commands for CLI parity evidence.

### Phase A — Requirements & Trace Alignment
Goal: Confirm the authoritative semantics for both flags and capture the C reference behavior (including unit expectations) before touching implementation.
Prereqs: Ability to run instrumented C binary via `NB_C_BIN` and collect traces.
Exit Criteria: Documented parity notes under `reports/2025-10-cli-flags/phase_a/` with explicit decisions on unit conversions and noise toggle ordering.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Extract C reference for `-nonoise` | [D] | ✅ 2025-10-05: Supervisor command captured with/without `-nonoise`; logs stored under `reports/2025-10-cli-flags/phase_a/`. |
| A2 | Capture pix0 vector ground truth | [D] | ✅ 2025-10-05: Instrumented C trace recorded pix0 vector values; confirms outputs remain in meters even for `_mm` flag. |
| A3 | Update findings memo | [D] | ✅ 2025-10-05: Phase A summary authored in `reports/2025-10-cli-flags/phase_a/README.md` documenting semantics and CUSTOM convention side effects. |

### Phase B — CLI & Config Wiring
Goal: Teach the PyTorch CLI to parse both flags, thread them through configs, and respect overrides in Detector/Noise handling without breaking existing behavior.
Prereqs: Phase A report published; confirm existing CLI regression tests green (run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_entrypoint.py -q` if available).
Exit Criteria: `nanoBragg --help` lists both flags; manual dry run of supervisor command completes argument parsing and produces float image without raising.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Extend argparse surface | [D] | `create_parser()` now exposes both flags (see `src/nanobrag_torch/__main__.py:187-206`); keep help text aligned with `nanoBragg.c` usage block. |
| B2 | Thread `-nonoise` to simulator | [D] | `parse_and_validate_args()` records `suppress_noise`, and the noise writer at `__main__.py:1170-1199` skips SMV noise output when true. Add warning copy before closing Phase C. |
| B3 | Support pix0 overrides | [D] | Fixed detector override assignment bug (2025-10-05). `_calculate_pix0_vector()` now assigns to `self.pix0_vector` and sets `r_factor=1.0`, `distance_corrected=distance`. Device/dtype coercion preserved via `.to()`. Verified: CLI `-pix0_vector_mm 100 200 300` → tensor([0.1, 0.2, 0.3]). |
| B4 | Preserve meter and mm flag parity | [D] | Run paired parser smoke checks proving `-pix0_vector` (meters) and `-pix0_vector_mm` (millimetres) yield identical `pix0_override_m` tensors and that dual-flag usage raises `ValueError`. Record commands + stdout in `reports/2025-10-cli-flags/phase_b/detector/pix0_override_equivalence.txt`. ✅ 2025-10-05: Verified parser equivalence and dual-flag ValueError handling. |
| B5 | Unit & cache hygiene | [D] | Capture a detector mini-harness (`PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY' …`) showing `Detector(..., pix0_override_m=...)` preserves device/dtype after `invalidate_cache()` and when moved across CPU/CUDA. Store log in `reports/2025-10-cli-flags/phase_b/detector/cache_handoff.txt`; note any follow-on assertions needed in code/tests. ✅ 2025-10-05: Cache stability confirmed on CPU/CUDA with device/dtype preservation. |

### Phase C — Validation & Documentation
Goal: Prove parity via targeted tests and update docs/fix_plan so future loops know the flags are supported.
Prereqs: Phase B code ready; editable install available for CLI tests.
Exit Criteria: Tests and documentation changes landed; supervisor command successfully runs PyTorch CLI and reaches simulator without flag errors.

**Parity risk reminder:** C instrumentation shows `DETECTOR_PIX0_VECTOR` emitted in meters even when using `-pix0_vector_mm`. During Phase C2 parity run, capture both C and PyTorch pix0 traces to confirm we are not double-converting the override.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Add CLI regression tests | [D] | ✅ 2025-10-16 (commit b6c6a61). `tests/test_cli_flags.py` covers meters/mm aliases, mutual exclusion, override persistence (CPU/CUDA), dtype preservation, and `-nonoise` suppression. |
| C2 | Golden parity smoke | [D] | ✅ 2025-10-05: Supervisor command executed for both binaries. C max_I=446.254 (img.bin), PyTorch max_I≈1.15e5 (torch_img.bin). Logs + float images archived under `reports/2025-10-cli-flags/phase_c/parity/`. Intensity scale mismatch noted for follow-up. |
| C3 | Update documentation | [ ] | Refresh `specs/spec-a-cli.md` and `README_PYTORCH.md` flag tables, note alias in `docs/architecture/c_parameter_dictionary.md`, and reference this plan from `docs/fix_plan.md` (new item) so future loops close it. |
| C4 | Fix-plan & plan closure | [ ] | Add new fix_plan entry (e.g., `[CLI-FLAGS-003]`) pointing to this plan; set completion criteria (tests, docs, command run). Once tasks pass, close plan and archive per SOP. |

### Phase D — Integration Follow-Through
Goal: Confirm no regressions in noise/geometry subsystems and capture open risks for longer-term initiatives.
Prereqs: Phases A–C complete.
Exit Criteria: Regression sweep documented, outstanding risks rolled into relevant plans (e.g., detector caching, noise modeling).

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| D1 | Run targeted regression suite | [ ] | Execute `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_noise_generation.py tests/test_detector_pix0.py -v`; ensure existing tolerances hold with overrides. |
| D2 | Record residual risks | [ ] | Append summary to `reports/2025-10-cli-flags/phase_d/notes.md` covering any limitations (e.g., lack of `_mm` alias upstream, CUSTOM convention edge cases). Link to relevant active plans if work remains. |
| D3 | Investigate intensity scaling gap | [D] | ✅ 2025-10-06: Phase C2 artifacts analysed; determined discrepancy is geometric (zero correlation, peaks displaced by 1.5k pixels). Artifacts under `reports/2025-10-cli-flags/phase_d/`. See Notes below for mandatory follow-up trace work. |

### Phase E — Parallel Trace Root Cause
Goal: Pinpoint the first physics divergence between C and PyTorch for the supervisor command using the mandated parallel trace workflow.
Prereqs: Phase D3 report published; C binary ready for instrumentation (`NB_C_BIN=./golden_suite_generator/nanoBragg`).
Exit Criteria: Trace comparison identifies first divergent variable; findings logged in `reports/2025-10-cli-flags/phase_e/trace_comparison.md` and summarized in docs/fix_plan.md `[CLI-FLAGS-003]` Attempts.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| E0 | Verify beam vector parity | [D] | ✅ 2025-10-16: `reports/2025-10-cli-flags/phase_e/beam_vector_check.txt` shows PyTorch Detector beam direction `[0., 0., 1.]` vs C trace override `[0.00051387949, 0, -0.99999986]`; confirms CLI wiring gap. |
| E1 | Instrument C trace for peak pixel | [D] | ✅ 2025-10-16: `c_trace_beam.log` captured via instrumented binary (pixel 1039,685) with pix0, beam, scattering, h/k/l, F_latt entries. |
| E2 | Generate matching PyTorch trace | [D] | ✅ 2025-10-16: `pytorch_trace_beam.log` generated with `trace_harness.py` (double precision). Harness currently overrides beam vector manually to mimic the supervisor command. |
| E3 | Diff traces and identify first divergence | [D] | ✅ 2025-10-16: `trace_diff_beam.txt` + `trace_summary.md` pinpoint pix0 mismatch (1.14 mm Y error) and reveal lost crystal orientation + polarization delta. docs/fix_plan.md Attempts updated with evidence requirements for implementation phases. |

### Phase F — Detector Implementation (beam + pix0 parity)
Goal: Port CUSTOM detector wiring so CLI overrides reproduce C behavior without ad-hoc harness patches.
Prereqs: Phase E traces complete; docs/fix_plan.md Attempt log captures pix0/beam/orientation findings.
Exit Criteria: Detector trace matches C for pix0 and incident beam; CLI parity run no longer relies on manual overrides.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| F1 | Thread `custom_beam_vector` through Detector | [D] | ✅ 2025-10-05 (ralph): Refactored `_calculate_pix0_vector()` to use `self.beam_vector` property instead of hardcoded beam vectors (lines 438-440, 519-521). Beam vector now exactly matches C trace. Artifacts in `reports/2025-10-cli-flags/phase_f/`. See docs/fix_plan.md Attempt #11. |
| F2 | Port CUSTOM pix0 transform for overrides | [D] | ✅ 2025-10-05: CUSTOM pathway from nanoBragg.c:1739-1846 ported (pivot override, MOSFLM vs CUSTOM offsets, close_distance recompute). Validation report at `reports/2025-10-cli-flags/phase_f2/pix0_transform_refit.txt`. Follow-up: ensure downstream uses keep `close_distance` as a tensor (no `.item()` detaches) when further tuning detector gradients. |
| F3 | Re-run Phase C2 parity smoke | [P] | 2025-10-17 Attempt #12 captured C vs PyTorch artifacts under `reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/`; correlation ≈−5e-06 confirms geometry still diverges. Defer rerun until Phase G (A* orientation) lands so parity failure isn’t repeated; once orientation is wired, rerun parity and refresh metrics. |

### Phase G — MOSFLM Matrix Orientation Support
Goal: Preserve full crystal orientation from `-mat` files so PyTorch matches C lattice vectors and downstream physics.
Prereqs: Detector parity (Phase F) achieved or at least traced; clarity on orientation data flow.
Exit Criteria: Crystal trace (rotated a/b/c vectors) aligns with C for the supervisor command; CLI accepts orientation without manual overrides.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| G1 | Extend CLI config to retain A* vectors | [D] | ✅ Commit 28fc584 stores MOSFLM reciprocal vectors from `-mat` in `parse_and_validate_args` and threads them into `CrystalConfig`; 26-case CLI regression sweep captured in Attempt #15 notes. |
| G2 | Teach `Crystal` to ingest orientation | [D] | ✅ 2025-10-17 Attempt #17 (ralph). Modified `Crystal.compute_cell_tensors()` (lines 545-603) to detect MOSFLM orientation in config, convert to tensors with proper device/dtype, and integrate with Core Rules 12-13 pipeline. Tests: 26/26 passed (CLI), 35/35 passed (crystal). Metric duality perfect. Artifacts: `reports/2025-10-cli-flags/phase_g/README.md`. |
| G3 | Trace verification + parity rerun | [D] | ✅ 2025-10-06 Attempt #18 (ralph). Fixed MOSFLM matrix transpose bug (`src/nanobrag_torch/io/mosflm.py:88`). Reciprocal vectors now match C exactly (9/9 components to 16 decimals). Miller indices match: (2,2,-13). F_cell perfect match: 300.58. Real vectors within 0.05Å (<0.2% error). Artifacts: `reports/2025-10-cli-flags/phase_g/trace_summary_orientation_fixed.md`, `traces/trace_c.log`, `traces/trace_py_fixed.log`. Intensity parity still divergent (deferred to Phase H polarization). |

### Phase H — Lattice Structure Factor Alignment
Goal: Ensure the CLI-provided beam vector propagates through Detector→Simulator and bring scattering/lattice parity back in line before polarization work.
Prereqs: Phases F and G complete; orientation traces captured (Phase G3 artifacts in place).
Exit Criteria: Trace comparison shows `pix0_vector` components matching C within 5e-5 m, `h`, `k`, `l` fractional components within 1e-3, `F_latt_a/b/c` within 0.5% (signed), and a parity rerun demonstrates ≥0.95 correlation improvement attributable to lattice fixes (polarization still disabled).

Update 2025-10-17: Attempt #22 proved the projection-based override mapping pushes pix0 off by 2.16e-1 m; Attempt #23 (now superseded) inferred the C code ignored `-pix0_vector_mm` when custom detector vectors are present. Phase J traces captured on 2025-10-21 demonstrate the override IS honoured (C recomputes `Fbeam/Sbeam` ≈0.2179/0.2139 m), so PyTorch must re-apply overrides even in the custom-vector path.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| H1 | Refresh trace evidence post-orientation | [D] | ✅ 2025-10-17: `reports/2025-10-cli-flags/phase_h/trace_harness.py` + `trace_comparison.md` captured the no-override trace and logged Attempt #19 (beam vector divergence documented). |
| H2 | Fix incident beam propagation from CLI | [D] | ✅ 2025-10-17 Attempt #20 (ralph). Simulator now clones `detector.beam_vector` (commit 8c1583d); regression covered by `tests/test_cli_flags.py::TestCLIBeamVector::test_custom_beam_vector_propagates`. Pending: rerun `phase_h/trace_harness.py` to confirm `incident_vec` parity before Phase H3. |
| H3a | Diagnose residual lattice mismatch | [D] | ✅ 2025-10-17 Attempt #21 (ralph). `trace_py_after_H3_refresh.log`, `pix0_reproduction.md`, and `implementation_notes.md` quantify the ~1.14 mm pix0 delta and show the cascade into scattering vector and `F_latt` disparities; `attempt_log.txt` restored with evidence summary. |
| H3b1 | Capture C vs PyTorch pix0/F/S references (override on/off) | [D] | ✅ 2025-10-17 Attempt #23: Stored paired C traces (`reports/2025-10-cli-flags/phase_h/implementation/c_trace_with_override.log` / `_without_override.log`), PyTorch traces, and `pix0_mapping_analysis.md`; evidence proves C geometry is identical with or without `-pix0_vector_mm` when custom vectors are supplied. |
| H3b2 | Implement pix0 precedence (custom vectors > override) | [D] | ✅ 2025-10-06 Attempt #24 (commit d6f158c). `Detector._calculate_pix0_vector` now skips overrides when any custom detector vector is supplied; override logic only executes in the no-custom-vectors path. Validation: `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot` (CPU) and evidence log `reports/2025-10-cli-flags/phase_h/implementation/pix0_override_validation.md`. Residual pix0 Y-delta (≈3.9 mm) traced to missing post-rotation `Fbeam/Sbeam` recomputation and deferred to H4. |
| H3b3 | Repair CLI regression + artifacts for precedence | [D] | ✅ 2025-10-06 Attempt #24. Regression test now covers BOTH precedence cases (custom vectors ignored, standard path applies override) and records expected C pix0 vector in `pix0_expected.json`. CUDA parametrisation remains skipped until parity fix lands; tolerance temporarily relaxed to 5 mm pending H4 geometry alignment. |
| H4a | Port post-rotation beam-centre recomputation | [D] | ✅ 2025-10-17 Attempt #25: Ported nanoBragg.c lines 1846-1860 into `Detector._calculate_pix0_vector`; see `reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/implementation.md`. |
| H4b | Refresh traces and parity evidence | [D] | ✅ 2025-10-17 Attempt #25: Stored C/PyTorch traces in `reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/trace_c.log` and `trace_py.log`; `summary.md` records pix0 deltas ≤1.3e-8 m and `F_latt` agreement <0.2%. |
| H4c | Tighten regression test + targeted pytest | [D] | ✅ 2025-10-17 Attempt #25: Updated regression tolerance to 5e-5 m (CPU and CUDA parametrised) and captured `pytest_h4c.log`; Attempt #25 logged in docs/fix_plan.md. |

### Phase H5 — Custom Vector Pix0 Override Parity
Goal: Bring PyTorch pix0 precedence back in line with C when custom detector vectors accompany `-pix0_vector_mm`, eliminating the 1.14 mm delta driving the `F_latt` mismatch.
Prereqs: Phase H4 artifacts available; C precedence proof in `reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md`.
Exit Criteria: Detector traces with custom vectors show `pix0_vector`, `Fbeam`, and `Sbeam` matching C within 5e-5 m, and fractional h/k/l plus `F_latt_a/b/c` align within 1e-3 relative difference before resuming normalization work.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| H5a | Verify C precedence with explicit derivation | [D] | ✅ 2025-10-22 Attempt #30. C traces stored under `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/` prove geometry is identical with or without `-pix0_vector_mm` when custom vectors are present. `c_precedence_2025-10-22.md` carries the dot-product derivation. |
| H5b | Revert PyTorch override when custom vectors supplied | [D] | ✅ 2025-10-22 Attempt #31 (commit 831b670). `Detector._calculate_pix0_vector` now gates pix0 overrides behind a `has_custom_vectors` check; regression log captured in `reports/2025-10-cli-flags/phase_h5/pytest_h5b_revert.log`. Comments cite `c_precedence_2025-10-22.md`. |
| H5c | Capture updated PyTorch traces & compare | [P] | ✅ Attempt #35 (2025-10-24) captured `reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/trace_py.stdout` and refreshed `parity_summary.md`, but deltas remain large (ΔF = −1136 µm, ΔS = +139 µm). Keep this row in progress until follow-up Phase H6 diagnostics shrink |Δpix0| below the 5e-5 m threshold. |

### Phase H6 — Pix0 Divergence Isolation
Goal: Instrument both implementations to pinpoint the exact step in `_calculate_pix0_vector()` where the PyTorch BEAM-pivot math diverges from nanoBragg.c when custom detector vectors are present.
Prereqs: Phase H5 artifacts archived (`reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-24/`), C precedence proof in `reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md`, familiarity with `docs/architecture/detector.md` §5 and specs/spec-a-cli.md precedence rules.
Exit Criteria: New traces under `reports/2025-10-cli-flags/phase_h6/` showing matched step-by-step values, the first divergence documented in `parity_summary.md`, and docs/fix_plan Attempt #36 logging the diagnosis with remediation guidance.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| H6a | Instrument C pix0 calculation | [D] | ✅ Attempt #36 (2025-10-24) captured `reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0.log` plus clean extracts/README. SAMPLE pivot confirmed with C pix0 = (-0.216475836, 0.216343050, -0.230192414) m and basis vectors logged post-rotation. |
| H6b | Extend PyTorch trace harness | [D] | ✅ Attempt #37 (2025-10-06) patched `reports/2025-10-cli-flags/phase_h/trace_harness.py` to emit matching `TRACE_PY` lines after Detector geometry setup, removed the hard-coded BEAM pivot, and executed via `PYTHONPATH=src` to guarantee the editable implementation. Trace archived at `phase_h6/py_trace/trace_py_pix0.log` with env/git snapshots; residual ΔF = −1136 µm confirms instrumentation succeeded and Phase H6c analysis is next. |
| H6c | Diff traces & isolate first divergence | [D] | ✅ Attempt #38 (2025-10-26) produced `phase_h6/analysis.md` and `trace_diff.txt`; first divergence is the trace harness labeling beam-center values in millimetres while C logs meters. Pix0 deltas (ΔF = −1.136 mm, ΔS = +0.139 mm) persist, so the physical mismatch remains unresolved. `phase_h5/parity_summary.md` now records these findings. |
| H6d | Update fix_plan attempt log | [D] | ✅ Attempt #36 logged in `docs/fix_plan.md` with trace artifacts, pivot confirmation, and marching orders for H6b/H6c. |
| H6e | Confirm pivot parity (SAMPLE vs BEAM) | [D] | ✅ Attempt #39 (2025-10-06) documented pivot mismatch in `reports/2025-10-cli-flags/phase_h6/pivot_parity.md`. C evidence: `grep "pivoting"` shows "pivoting detector around sample". PyTorch evidence: inline config snippet shows DetectorPivot.BEAM. Root cause confirmed: `DetectorConfig` missing custom-vector-to-SAMPLE-pivot forcing rule. Spec citations and impact analysis complete. Updated `phase_h5/parity_summary.md` with cross-reference. |
| H6f | Align pivot selection when custom vectors provided | [D] | ✅ Attempt #40 (2025-10-26) updated `DetectorConfig.__post_init__` to force SAMPLE pivot whenever custom detector basis vectors (fdet/sdet/odet/beam) are supplied, added regression suite `TestCLIPivotSelection` (CPU+CUDA, float32/float64), relocated visuals under `reports/2025-10-cli-flags/phase_h6/visuals/`, and logged implementation notes at `pivot_fix.md`. |
| H6g | Re-run pix0 traces after pivot fix | [D] | ✅ Attempt #41 (2025-10-27) reran the harness with SAMPLE pivot enforced; `phase_h6/post_fix/trace_py.log`, `trace_diff.txt`, and `metadata.json` show |Δpix0| ≤ 2.85 µm and zero beam-center deltas. nb-compare smoke stored alongside traces; docs/fix_plan Attempt #41 updated. |
| H5d | Update fix_plan Attempt log | [D] | ✅ 2025-10-22 Attempt #31. docs/fix_plan.md logs the revert metrics and artifacts (Attempt #31), so Phase K normalization work can proceed with the restored baseline. |
| H5e | Correct beam-center→F/S mapping units | [D] | ✅ 2025-10-24 Attempt #33. `Detector._configure_geometry` now converts `self.config.beam_center_f/s` (mm) to meters via `/1000.0` before computing Fbeam/Sbeam, resolving the 1.1mm ΔF error. All 26 CLI flags tests passing. Artifacts: `src/nanobrag_torch/models/detector.py:490-515`, `docs/fix_plan.md` Attempt #33. Original task: Investigate the 2025-10-22 trace deltas showing ΔF≈-1.1 mm. Confirm `DetectorConfig.beam_center_*` is stored in millimetres (see `__main__.py:915-937`) and update `Detector._configure_geometry` so BEAM-pivot F/S values convert mm→m before constructing pix0 (match `nanoBragg.c:1184-1239`). Add targeted trace demonstrating the fix under `reports/2025-10-cli-flags/phase_h5/unit_fix/` and record Attempt #33 in fix_plan with metrics. |

### Phase I — Polarization Alignment (follow-up)
Goal: Match C’s Kahn polarization factor once lattice geometry aligns.
Prereqs: Phases F–H complete; traces show `F_latt` parity.
Exit Criteria: Polarization entries in C/PyTorch traces agree (≈0.9126 for supervisor command) and parity smoke stays green.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| I1 | Audit polarization inputs | [D] | ✅ Completed 2025-10-17. C defaults polar=1.0/polarization=0.0/nopolar=0 verified at nanoBragg.c:308-309. PyTorch BeamConfig.polarization_factor was defaulting to 0.0 instead of 1.0. |
| I2 | Implement polarization parity | [P] | ✅ 2025-10-17 update set BeamConfig.polarization_factor default to 1.0, but C traces (2025-10-31) confirm the Kahn factor defaults to 0.0 when `-polar` is absent. Reopen to: (a) restore 0.0 default, (b) keep -polar/-nopolar overrides working, and (c) adjust TestCLIPolarization expectations accordingly. |
| I3 | Final parity sweep | [P] | Attempt #27 (2025-10-06) failed with 124,538× intensity scaling gap; remains blocked pending Phase K fixes (orientation rescale + polarization default). |

### Phase J — Intensity Scaling Evidence
Goal: Isolate the first divergence in the normalization chain (steps, ω, r_e², fluence) responsible for the 1.2×10⁵ intensity mismatch.
Prereqs: Phase I2 complete; beam/pix0/orientation traces from Phases F–H archived.
Exit Criteria: Report under `reports/2025-10-cli-flags/phase_j/scaling_chain.md` documenting C vs PyTorch values for `steps`, `I_before_scaling`, `omega`, `polarization`, `r_e²`, `fluence`, and the resulting per-pixel intensities, with the first mismatched quantity identified and logged in docs/fix_plan.md Attempt history.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| J1 | Capture single-pixel scaling traces | [D] | ✅ 2025-10-19: C trace (`trace_c_scaling.log`) and PyTorch trace (`trace_py_scaling.log`) captured for pixel (1039,685) with full scaling chain (`steps`, `I_before_scaling`, `r_e²`, `fluence`, `polar`, `omega`). |
| J2 | Compute factor-by-factor ratios | [D] | ✅ 2025-10-19: `analyze_scaling.py` created and executed; identifies first divergence as `I_before_scaling` with Py/C ratio=3.6e-7. Root cause: F_latt components differ by ~463× (C: 35636 vs PyTorch: 76.9). Markdown report at `scaling_chain.md`. |
| J3 | Update fix_plan Attempt log | [D] | ✅ 2025-10-19: Attempt #28 logged in `docs/fix_plan.md` with complete metrics, artifacts, and hypothesis (F_latt calculation error in sincg lattice shape factor). Phase I3 remains blocked pending Phase K F_latt fix. |

### Phase K — Normalization Implementation
Goal: Align PyTorch normalization logic with C based on Phase J evidence (steps division, fluence, r_e², omega/polarization application order).
Prereqs: Phase J report pinpoints the mismatched factor; existing regression suite green.
Exit Criteria: Code changes merged with targeted tests covering the corrected scaling, and docs/fix_plan.md records Attempt #29 metrics before moving to Phase L.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| K1 | Align lattice factor math with C (SQUARE case) | [D] | ✅ 2025-10-24 Attempt #34 (commit 0fef8f7). `Simulator._compute_physics_for_position` now uses `sincg(torch.pi * h, Na)` with embedded C-code reference; regression `tests/test_cli_scaling.py::test_f_latt_square_matches_c` added (skips unless `NB_RUN_PARALLEL=1`). |
| K2 | Recompute scaling chain & extend diagnostics | [D] | ✅ 2025-10-06 Attempt #42. Fresh PyTorch trace captured (trace_py_after.log); scaling chain refreshed showing F_latt_b=46.98 (Py) vs 38.63 (C) = 21.6% error, polar=1.0 (Py) vs 0.913 (C) = 9.6% error. Updated scaling_chain.md with post-SAMPLE-pivot ratios. |
| K2b | Document MOSFLM rescale mismatch | [D] | ✅ 2025-10-06 Attempt #42. Created mosflm_rescale.py and orientation_delta.md. Finding: C skips vector_rescale when `user_cell==0`, but PyTorch still rescales, leading to persistent F_latt_b drift. |
| K3a | Guard MOSFLM rescale path in `Crystal.compute_cell_tensors` | [D] | ✅ 2025-11-06 Attempt #43 (`a89f6fd`): added `mosflm_provided` guard; `mosflm_rescale.py` now reports Δa/b/c=0.0 Å against C (`orientation_delta.md`). |
| K3b | Realign polarization defaults with C | [D] | ✅ 2025-11-06 Attempt #43: `BeamConfig.polarization_factor` defaults to 0.0; CLI regression updated; scaling harness will be re-run once K3e/K3f land. |
| K3d | Diagnose dtype sensitivity of F_latt | [D] | ✅ 2025-11-06 Attempt #44 (`271e2b6`): float64 sweep stored under `phase_k/f_latt_fix/dtype_sweep/` proved precision is not the culprit (F_latt_b error persists at 93.98%). |
| K3c | Regression & documentation close-out | [ ] | `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v` plus any new normalization tests. Save log as `phase_k/f_latt_fix/pytest_post_fix.log`, update `docs/architecture/pytorch_design.md` normalization notes and `docs/development/testing_strategy.md`, then record Attempt #43 with metrics and artifacts. |
| K3e | Capture per-φ Miller index parity | [D] | ✅ 2025-10-06 Attempt #45 (ralph). Created `scripts/trace_per_phi.py`, generated PyTorch trace (`per_phi_pytorch_20251006-151228.json`), added TRACE_C_PHI to nanoBragg.c:3156-3160, ran C trace, compared via `scripts/compare_per_phi_traces.py`. **Finding:** Δk≈6.042 at φ=0° (C k_frac=−3.857, Py k_frac=−9.899), persists across all φ steps. **Root cause:** Not a φ-sampling issue—base lattice vectors or scattering geometry differ before φ rotation. |
#### Phase K3f — Base lattice & scattering parity
Goal: Eliminate the Δk≈6.0 mismatch uncovered in K3e by proving base lattice vectors, pixel geometry, and scattering-vector math match C before φ rotation.
Prereqs: K3e per-φ evidence archived; MOSFLM rescale guard (K3a) merged; pix0 SAMPLE pivot parity validated (H6g).
Exit Criteria: Trace comparison shows |Δh|, |Δk|, |Δl| < 5e-4 at φ=0° with matching lattice vectors and scattering vectors; scaling_chain.md refreshed with post-fix numbers; docs/fix_plan Attempt #46 logged.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| K3f1 | Capture C baseline for lattice + scattering | [D] | ✅ Artifacts captured in `base_lattice/c_trace.log` & `c_stdout.txt` (2025-11-08); trace logs include MOSFLM scaling, real vectors, and φ=0 scattering lines. |
| K3f2 | Extend PyTorch trace harness with matching fields | [D] | ✅ `trace_harness.py` now emits `TRACE_PY_BASE` using the corrected pixel vector path; output stored in `base_lattice/trace_py.log` (float64, CPU). |
| K3f3 | Diff base traces & isolate first divergence | [D] | ✅ `base_lattice/summary.md` compares logs and flags the first divergence at `a_star`/real vectors with ~40.5× magnitude gap, confirming Δh≈6.0 stems from unit-scale drift. |
| K3f4 | Record root cause & fix outline | [D] | 2025-11-08 update appended to `base_lattice/summary.md` documenting the placeholder-volume root cause and the 46ba36b fix; evidence lives under `reports/2025-10-cli-flags/phase_k/base_lattice/post_fix/`. Coordinate docs/fix_plan Next Actions so K3g3 focuses on scaling parity. |

#### Phase K3g — MOSFLM real-vector rescale implementation
Goal: Mirror nanoBragg.c’s MOSFLM branch so PyTorch recomputes real lattice vectors, volumes, and reciprocal duals from the supplied A* matrix before φ/mosaic rotations.
Prereqs: K3f4 root-cause doc committed; guard tasks K3a/K3b still green.
Exit Criteria: `Crystal.compute_cell_tensors` updates documented with in-code C reference, `tests/test_cli_scaling.py::test_f_latt_square_matches_c` passes at default tolerances, Δh/Δk/Δl in base trace <5e-4, and fix_plan Attempt #46 records parity metrics.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| K3g1 | Recompute MOSFLM cell metrics inside `Crystal.compute_cell_tensors` | [D] | Commit 46ba36b landed MOSFLM branch with C reference, recomputing `V_star`, `V_cell`, `a/b/c` and updating reciprocal duals. See `tests/test_cli_scaling.py::TestMOSFLMCellVectors` and `reports/.../post_fix/cell_tensors_py.txt`. |
| K3g2 | Add regression coverage for MOSFLM cell rebuild | [D] | Added `TestMOSFLMCellVectors::test_mosflm_cell_vectors` validating V_cell and |a|,|b|,|c| to ≤5e-4 against C reference; artifacts stored under `phase_k/base_lattice/post_fix/`. |
| K3g3 | Re-run scaling & parity evidence | [D] | ✅ Attempt #49 (2025-10-06) — `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v` now passes after isolating HKL caches; `phase_k/f_latt_fix/post_fix/` holds refreshed traces and nb-compare artifacts. |

### Phase L — Supervisor Command Normalization
Goal: Isolate and resolve the 1.26×10⁵ intensity mismatch that persists when running the full supervisor command after Phase K fixes.
Prereqs: Phase K3g artifacts refreshed (Attempt #49), nb-compare data in `phase_k/f_latt_fix/post_fix/`, instrumentation from Phase J available.
Exit Criteria: Structure-factor grids, scaling chain, and final intensities match C within thresholds (|Δh|,|Δk|,|Δl| < 5e-4; sum_ratio 0.99–1.01; mean_peak_distance ≤ 1 px); nb-compare rerun archived under `phase_l/supervisor_command/`; docs/fix_plan Attempt log updated; plan ready for archival.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| L1a | Run HKL ↔ Fdump parity script and capture metrics | [D] | Attempt #50 (2025-10-06) produced `summary_20251006175032.md` / `metrics_20251006175032.json`; this loop repeated the run with `Fdump_scaled_20251006175946.bin`, confirming max |ΔF|=5.22e2, 99,209 mismatched voxels, and storing `c_fdump_20251006175946.log`. Artefacts live under `reports/2025-10-cli-flags/phase_l/hkl_parity/`. |
| L1b | Diagnose binary-layout mismatch between HKL and Fdump | [D] | ✅ Attempt #52 (2025-10-06) produced `scripts/validation/analyze_fdump_layout.py` plus `reports/2025-10-cli-flags/phase_l/hkl_parity/layout_analysis.md`. Confirmed nanoBragg writes `(h_range+2)×(k_range+2)×(l_range+2)` voxels via `for(h0=0; h0<=h_range; h0++)` loops (see `nanoBragg.c:2400-2486`), leaving 9,534 zero-padded entries. PyTorch reader must drop the padded plane per axis. |
| L1c | Align PyTorch HKL cache reader/writer with confirmed layout | [D] | ✅ Attempt #53 (2025-10-17): Updated `src/nanobrag_torch/io/hkl.py` to honour `(range+1)` padding, added C-code docstring quotes per Rule #11, and introduced `tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip` (max |ΔF| = 0.0, mismatches = 0). |
| L1d | Re-run parity script after fixes and update artefacts | [D] | ✅ Attempt #54 (2025-10-17): Regenerated C cache using supervisor command flags, achieved perfect HKL parity (max |ΔF|=0.0, 0 mismatches). Artifacts: `reports/2025-10-cli-flags/phase_l/hkl_parity/{Fdump_c_20251109.bin, summary_20251109.md, metrics_20251109.json}`. Phase L2 prerequisites now met—structure factors match C exactly. |

### Phase L2 — Scaling Chain Audit
Goal: Capture a side-by-side breakdown of the intensity scaling pipeline (I_before_scaling → ω → polarization → r_e² → fluence → steps) for the supervisor command to isolate the first divergence that drives the 1.26×10⁵ sum ratio.
Prereqs: Phase L1d artifacts in place; Ralph working under `prompts/debug.md`; C binary instrumentable via `golden_suite_generator/` per CLAUDE Rule #0.3.
Exit Criteria: C and PyTorch traces capturing scaling factors are stored under `reports/2025-10-cli-flags/phase_l/scaling_audit/`, a comparison summary identifies the first mismatched term with quantitative deltas, and docs/fix_plan.md Attempt log references the findings.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| L2a | Instrument C scaling chain | [D] | ✅ 2025-10-06 Attempt #55: Reused existing TRACE_C hooks (nanoBragg.c 3367-3382), captured `c_trace_scaling.log` for pixel (685,1039), and recorded setup in `instrumentation_notes.md`. Artifacts live under `reports/2025-10-cli-flags/phase_l/scaling_audit/`; ready to mirror fields on the PyTorch side. |
| L2b | Expose and log PyTorch scaling factors | [D] | ✅ Attempts #69, #72, and #74 (commits `1cf77b5`, `0f3de26`) now drive the harness through the updated HKL API, attach `crystal.hkl_data` / `crystal.hkl_metadata`, and capture live TRACE_PY output for pixel (685,1039). `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log` shows real polarization/omega/steps, and `harness_hkl_state_fixed.txt` confirms the HKL tensor lives on the simulator device. |
| L2c | Diff traces & record first divergence | [D] | ✅ Attempt #71 refreshed `scaling_audit_summary.md` via `scripts/validation/compare_scaling_traces.py`, highlighting `I_before_scaling` as the first divergence (C=9.4365e5, Py=0) while all downstream scaling factors match within 2e-3%. This establishes that the remaining gap stems from missing structure-factor coverage rather than normalization math. |

### Phase L3 — Normalization Fix Implementation
Goal: Patch the PyTorch scaling pipeline so every factor (omega, polarization, capture_fraction, r_e², fluence, steps) matches the C implementation within 1e-6 relative error.
Prereqs: L2 comparison summary pointing to the exact divergent factor; relevant C references documented; regression tests identified.
Exit Criteria: PyTorch source changes with inline C-code docstring references are merged, targeted regression tests cover the corrected scaling semantics, and new artifacts demonstrate matching intermediate values. docs/fix_plan.md records the fix attempt and resulting metrics.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| L3a | Verify structure-factor coverage for supervisor pixel | [D] | ✅ 2025-11-17 Attempt #77: `reports/2025-10-cli-flags/phase_l/structure_factor/probe.py` recorded `probe_20251117.log` showing scaled.hkl returns `F_cell=190.270004` for hkl=(-7,-1,-14). Keep the log + timestamped copies alongside a brief summary in `analysis.md`, then proceed to L3c to thread the same attachment pattern through the harness/CLI path. |
| L3b | Mirror probe attachment in harness | [D] | ✅ 2025-11-17 Attempt #78: `trace_harness.py` now assigns both `hkl_data` and `hkl_metadata` before simulator construction (see `trace_py_scaling_20251117.log`, `harness_hkl_state_20251117.txt`). Keeps harness behavior aligned with probe results and removes F_cell=0 divergence. |
| L3c | Audit CLI HKL loading path | [D] | ✅ 2025-10-18 Attempt #80: Refreshed `cli_hkl_audit.md` with precise line refs (line 1073) showing dtype-only transfer; confirmed probe artifacts and logged device gap blocking CUDA parity. |
| L3d | Add targeted regression tests | [D] | ✅ Attempt #81 (2025-11-18): Added `TestHKLDevice::test_hkl_tensor_respects_device` covering CPU/CUDA × float32/float64; ensures HKL tensors honor requested device/dtype and lookups return F≈190.27 for (-7,-1,-14). |
| L3e | Refresh per-phi scaling validation | [D] | ✅ Attempt #86 (2025-10-07 timestamp, replayed 2025-11-19 artifacts): Harness now captures 10 `TRACE_PY_PHI` lines plus JSON, reruns `compare_scaling_traces.py`, and stores outputs under `reports/2025-10-cli-flags/phase_l/{per_phi,scaling_validation}/`. Remaining delta isolated to `k_frac`/`F_latt_b` at phi=0. |
| L3f | Rotation-vector audit (new) | [D] | ✅ Attempts #86/#88 (2025-11-18/19) produced `rot_vector_comparison.md`, `invariant_probe.md`, and per-φ JSON showing φ=0 real vectors drifting in Y while reciprocal vectors remain aligned ≤1e-9. Evidence archived under `reports/2025-10-cli-flags/phase_l/rot_vector/`. |
| L3g | Fractional Miller alignment plan | [D] | ✅ 2025-10-07 Attempt #91: Instrumented simulator.py:1313-1322 to emit `spindle_axis_raw/normalized/magnitude`, reran φ=0 trace (43 TRACE_PY lines), confirmed Δ(magnitude)=0.0 (tolerance ≤5e-4). H1 **RULED OUT**: spindle is exact unit vector [-1,0,0], normalization is no-op. H3 (MOSFLM matrix semantics) promoted to primary suspect. Artifacts: `rot_vector/spindle_audit.log`, `analysis.md` (updated with H3 ranking). |
| L3h | MOSFLM matrix probe & diff | [D] | ✅ Attempt #92 (2025-10-07, ralph evidence loop i=92): Created `trace_harness.py` in rot_vector/, captured 12 MOSFLM probe lines (post-misset reciprocals, reconstructed reals, re-derived reciprocals), proved V_formula ≈ V_actual (Δ=1.5e-11 Å³), **ruled out Hypothesis H2**. Reciprocal re-derivation exact to 15 digits. Artifacts: `mosflm_matrix_probe.md` (primary doc), `mosflm_matrix_probe_output.log`, `trace_harness.py`, `harness_run.log`. pytest: 579 tests collected. Next: Phase L3i C instrumentation to complete C vs PyTorch diff. |
| L3i | C instrumentation & diff | [D] | ✅ Attempt #93 (2025-10-07, ralph loop i=93): Captured full C MOSFLM pipeline trace (291 lines) via instrumented `golden_suite_generator/nanoBragg.c:2050-2199`, executed supervisor command, performed component-level diff. **H3 (MOSFLM transpose) RULED OUT** — real-space b_Y matches to O(1e-7) Å. Artifacts: `c_trace_mosflm.log`, `c_trace_extract.txt`, `mosflm_matrix_diff.md`, `analysis.md` (updated with H5-H7 hypotheses). pytest: 652 tests collected. Next: L3j fix checklist focusing on H5 (phi rotation) verification. |
| L3j.1 | Refresh correction memo | [D] | ✅ 2025-10-07 Attempt #94 (ralph, documentation loop): Extended `mosflm_matrix_correction.md` with "Post-L3i Findings" section citing H3 ruling (b_Y matches C at φ=0 to 1.35e-07 Å), promoted H5 (φ rotation application) as primary suspect, documented quantitative deltas (b_Y +6.8%, k_frac Δ≈0.018, I_ratio 0.755), and spelled out φ samples (0°, 0.05°, 0.1°) with supervisor command context. Artifact: `mosflm_matrix_correction.md` lines 57-208. |
| L3j.2 | Author fix checklist | [D] | ✅ 2025-10-07 Attempt #94: Created `fix_checklist.md` with 5 verification gates (VG-1: per-φ harness rerun; VG-2: pytest lattice tests; VG-3: nb-compare ROI parity; VG-4: component-level delta audit; VG-5: documentation updates). Includes thresholds (b_Y ≤1e-6 relative, correlation ≥0.9995, sum_ratio 0.99–1.01), detailed command templates, spec/doc references, and implementation notes. Artifact: `reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md` (5 gates, 19 rows). |
| L3j.3 | Sync plan + fix_plan | [D] | ✅ 2025-11-21 Attempt #96: Updated `docs/fix_plan.md` CLI-FLAGS-003 with Attempt #96 entry documenting Phase L3k.1 completion (implementation memo), artifact paths, root cause analysis, proposed fix strategy, and next actions for code implementation loop. Documented Mode: Docs constraint (no code changes this loop). Updated this plan to mark L3k.1 complete. pytest --collect-only deferred to implementation loop. |

### Phase L3k — φ Rotation Fix Implementation
Goal: Implement the φ rotation correction in `Crystal.get_rotated_real_vectors`, prove parity via the established verification gates, and prepare for the supervisor-command rerun.
Prereqs: Phase L3 instrumentation/memo/checklist complete; `fix_checklist.md` available; C trace (`c_trace_mosflm.log`) and PyTorch harness outputs captured under `reports/2025-10-cli-flags/phase_l/`.
Exit Criteria: Code patch lands with in-code C reference per CLAUDE Rule #11, all VG-1⇢VG-5 rows in `fix_checklist.md` flipped to ✅ with artifacts stored in the designated directories, and plan/fix_plan entries updated with attempt log + metrics.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| L3k.1 | Author implementation memo + docstring reference | [D] | ✅ 2025-11-21 Attempt #96 (ralph Mode: Docs): Appended Phase L3k Implementation Memo to `mosflm_matrix_correction.md:187-297` documenting root cause (independent rotation of real+reciprocal vectors), C reference (nanoBragg.c:3044-3066), proposed fix (rotate only real, recompute reciprocal from cross products), implementation strategy (preserve vectorization/device neutrality), and verification thresholds (VG-1⇢VG-5). C-code docstring reference requirement documented for L3k.2. Artifacts: implementation memo, updated fix_plan Attempt #96, updated this plan L3j.3→[D]. Mode: Docs → no code changes; docstring addition deferred to implementation loop. |
| L3k.2 | Implement φ rotation fix | [D] | ✅ 2025-11-21 Attempt #97 (ralph loop i=97): Fixed `Crystal.get_rotated_real_vectors` (crystal.py:1008-1035) to rotate ONLY real vectors, then recompute reciprocal via cross products and V_actual per CLAUDE Rule #13. Added C-code docstring reference (lines 1010-1013) per CLAUDE Rule #11. Preserved vectorization, device neutrality, gradient flow. Metrics: test_f_latt_square_matches_c PASSED (5.79s), 57 crystal/geometry tests PASSED, 653 tests collected. Artifacts: crystal.py:1008-1035 (fixed implementation), Attempt #97 in fix_plan.md. |
| L3k.3 | Execute verification gates VG-1⇢VG-5 | [P] | Attempt #98 cleared VG-2, Attempt #99 exposed the remaining gaps (k_frac span 1.8e-2, correlation 0.985, sum_ratio 1.16e5), and Attempt #108 captured φ=0 PyTorch state probes while flagging the C trace dependency. Re-open VG-1 workflow: re-run TRACE_C_PHI under the 20251123 timestamp (or update the harness to consume the 202510070839 asset), regenerate per-φ comparisons, then continue through the nb-compare ROI repair and documentation gates. Artifacts live under `reports/2025-10-cli-flags/phase_l/rot_vector/` (base_vector_debug/, per_phi_postfix/) and `reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/`. |

#### L3k.3 Checklist — φ=0 Verification Recovery

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| L3k.3a | Align φ=0 harness/tests with supervisor spindle axis | [D] | ✅ Attempt #100 updated `tests/test_cli_scaling_phi0.py` to set `spindle_axis=[-1,0,0]`, producing the expected red baseline (rot_b drift, k_frac delta). Keep these tests red until the physics fix lands; rerun `pytest tests/test_cli_scaling_phi0.py -k "phi0" -vv` after each patch. |
| L3k.3b | Restore C↔Py per-φ comparison pipeline | [D] | ✅ Attempt #109 (2025-11-23) rebuilt the instrumented C binary, captured `c_trace_phi_20251123.log`, reran `scripts/compare_per_phi_traces.py`, and populated `delta_metrics.json` (Δk=1.8116e-2 @ φ=0, Δk≤2.85e-5 elsewhere). Artifacts: `base_vector_debug/20251123/` trace set, updated comparison summary. |
| L3k.3c | Patch φ rotation & confirm VG-1 thresholds | [ ] | **Regression alert:** Attempt #102 rewrote `tests/test_cli_scaling_phi0.py` to treat the PyTorch base-vector output as canonical, masking the failing VG-1 gate. Attempt #103 restored the C-aligned assertions; keep them red until VG-1 passes. With the C trace refreshed (L3k.3b), implement the carryover fix, rerun the per-φ harness, ensure k_frac span ≤1e-6 and rot_b_y relative error ≤1e-6, and update `comparison_summary.md` plus `per_phi_postfix/` artifacts before flipping VG-1 rows to ✅. |
| L3k.3d | Resolve nb-compare ROI parity (VG-3/VG-4) | [ ] | Investigate the C ROI zero-sum issue (ROI bounds, image loader, dtype). Once resolved, rerun `nb-compare --roi` to hit correlation ≥0.9995, sum_ratio 0.99–1.01, and component deltas meeting VG-4 thresholds. Record metrics in `vg3_metrics.txt` and update `fix_checklist.md`. |
| L3k.3e | Finalize documentation + checklist (VG-5) | [ ] | When VG-1/VG-3/VG-4 pass, mark remaining rows in `fix_checklist.md` ✅, append resolutions to `mosflm_matrix_correction.md`, and prep notes for the L3k.4 attempt log. |
| L3k.4 | Log Attempt + plan sync | [ ] | **BLOCKED on L3k.3 completion.** Append new Attempt entry in `docs/fix_plan.md` CLI-FLAGS-003 with metrics (correlation, sum_ratio, b_Y delta, k_frac delta from VG artifacts), reference all artifact paths (per-φ traces, pytest log, nb-compare summary, updated checklist), document observations (H5 confirmed, thresholds met), and flip L3k.1–L3k.4 rows to [D] in this plan. Update Next Actions to proceed to Phase L4 supervisor command parity rerun. |

#### L3k.3c Tasks — Restore φ=0 Parity with C Reference

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| L3k.3c.1 | Reinstate C-aligned assertions | [D] | ✅ Attempt #103 (2025-10-07) restored the C expectations in `tests/test_cli_scaling_phi0.py`, leaving both φ=0 parity tests failing against the C reference. Artifact: `reports/.../pytest_phi0_regression.log`. Keep these assertions active so the fix cannot be masked. |
| L3k.3c.2 | Diagnose φ=0 state carryover | [D] | Attempt #109 captured paired traces under `base_vector_debug/20251123/`, recorded Δk=1.8116×10⁻² and Δb_y=4.573155×10⁻² Å in `diagnosis.md` + `delta_by.txt`, and documented the carryover remediation plan (cache φ_last → reuse at φ_tic=0 with nanoBragg.c:3044 guard). |
| L3k.3c.3 | Implement + validate fix | [ ] | **Reopened 2025-11-24 (galph loop)** after review found the Phase L3k implementation breaks device/dtype neutrality and gradients. Complete the φ=0 carryover emulation in `Crystal.get_rotated_real_vectors` (cache φ_last real vectors and reuse them at φ_tic=0 with nanoBragg.c:3044 guard) **without** detaching tensors or hard-coding devices. Ensure `_phi_last_cache` tensors migrate in `Crystal.to()` and that `last_phi_deg` uses `.to(...)` rather than `torch.tensor(...)` so gradients propagate. Align the per-φ instrumentation in `simulator.py` to use the spec formula `phi = phi_start + (osc/phisteps)*phi_tic` (no division by `phi_steps-1`). After the fix, rebuild traces (new timestamp under `base_vector_debug/`), rerun `python scripts/compare_per_phi_traces.py ...` to show Δk ≤ 1e-6, execute `pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c`, and update `comparison_summary.md` plus `fix_checklist.md` VG-1.4 to ✅. |

### Phase L4 — Supervisor Command Parity Rerun
Goal: Demonstrate end-to-end parity for the supervisor command (correlation ≥ 0.9995, sum_ratio 0.99–1.01, mean_peak_distance ≤ 1 px) and close CLI-FLAGS-003.
Prereqs: L3 validation artifacts show ≤1e-6 deltas for scaling factors; regression tests green.
Exit Criteria: nb-compare metrics meet thresholds, artifacts stored under `reports/2025-10-cli-flags/phase_l/supervisor_command_rerun/`, docs/fix_plan.md Attempt #56 documents the pass, and this plan is ready for archival.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| L4a | Rerun supervisor command parity | [ ] | Execute the authoritative command from `reports/2025-10-cli-flags/phase_i/supervisor_command/README.md`, writing outputs to a new timestamped directory. Capture `summary.json`, stdout/stderr, and SHA256 hashes. |
| L4b | Analyze results & log attempt | [ ] | Update `supervisor_command_rerun/README.md` with metrics, confirm thresholds met, and log Attempt #56 in docs/fix_plan.md summarizing deltas. |
| L4c | Finalize documentation | [ ] | If parity passes, move key artifacts to `reports/archive/` per SOP, update plan status to ready-for-archive, and prepare closing notes for CLI-FLAGS-003. If parity fails, loop back to L2 with findings. |

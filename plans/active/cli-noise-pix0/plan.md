## Context
- Initiative: CLI Parity for nanoBragg PyTorch vs C (supports long-term goal in prompts/supervisor.md)
- Phase Goal: Accept `-nonoise` and `-pix0_vector_mm` flags with C-equivalent semantics so the parallel comparison command in prompts/supervisor.md executes end-to-end.
- Dependencies: specs/spec-a-cli.md §§3.2–3.4, docs/architecture/detector.md §5, docs/development/c_to_pytorch_config_map.md (detector pivot + noise), golden_suite_generator/nanoBragg.c lines 720–1040 & 1730–1860 (flag behavior), docs/debugging/detector_geometry_checklist.md (pix0 validation), docs/development/testing_strategy.md §2 (CLI parity tests).
- Current gap snapshot (2025-10-18 refresh): Phase H4 parity landed (Attempt #25) with pix0 deltas < 2e-8 m and regression tolerances tightened; the remaining blocker before executing the supervisor command end-to-end is Phase I polarization alignment.
- Gap snapshot update (2025-10-19): Attempt #27 parity run reveals 1.24538e5× intensity scaling mismatch despite polarization fix; Phases J–L track the normalization diagnosis, fix, and closure required before long-term Goal #1 completes.
- Gap snapshot refresh (2025-10-22): Attempt #31 restored C precedence for custom detector vectors (pix0 override now gated again). Outstanding work: H5c PyTorch traces and Phase K normalization to eliminate the `F_latt`-driven intensity gap.
- Gap snapshot update (2025-10-24): Attempt #35 reran the PyTorch trace harness post-unit-fix; metrics still show |Δpix0| ≈ 1.145 mm, so a fresh diagnostics phase is required before resuming normalization work.
- Gap correction (2025-10-22): Fresh C evidence (`reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md`) proves nanoBragg ignores `-pix0_vector_mm` whenever custom detector vectors are present. PyTorch now deviates because the lattice factor uses fractional indices (h−h0); fix required before normalization parity.
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
| H6a | Instrument C pix0 calculation | [ ] | Add targeted `TRACE_C` lines around `golden_suite_generator/nanoBragg.c` pix0 math (beam_center → Fbeam/Sbeam, `close_distance`, `r_factor`, final pix0 vector). Run supervisor command with `NB_C_BIN=./golden_suite_generator/nanoBragg`, stash stdout under `reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0.log`, and record build context in `c_trace/README.md`. |
| H6b | Extend PyTorch trace harness | [ ] | Update `reports/2025-10-cli-flags/phase_h/trace_harness.py` (or companion script) to emit matching `TRACE_PY` lines from `_calculate_pix0_vector()` via instrumentation hooks. Capture output under `phase_h6/py_trace/trace_py_pix0.log` with env snapshot + git context. |
| H6c | Diff traces & isolate first divergence | [ ] | Use `diff -u` or notebook tooling to compare C vs PyTorch logs. Document the first mismatched quantity (units included) in `phase_h6/analysis.md`, update `phase_h5/parity_summary.md` with the new findings, and propose the corrective action (e.g., missing MOSFLM +0.5 offset or incorrect `beam_vector` scaling). |
| H6d | Update fix_plan attempt log | [ ] | File Attempt #36 in `docs/fix_plan.md` summarizing the divergence location, evidence paths, and unblock criteria for returning to Phase K. |
| H5d | Update fix_plan Attempt log | [D] | ✅ 2025-10-22 Attempt #31. docs/fix_plan.md logs the revert metrics and artifacts (Attempt #31), so Phase K normalization work can proceed with the restored baseline. |
| H5e | Correct beam-center→F/S mapping units | [D] | ✅ 2025-10-24 Attempt #33. `Detector._configure_geometry` now converts `self.config.beam_center_f/s` (mm) to meters via `/1000.0` before computing Fbeam/Sbeam, resolving the 1.1mm ΔF error. All 26 CLI flags tests passing. Artifacts: `src/nanobrag_torch/models/detector.py:490-515`, `docs/fix_plan.md` Attempt #33. Original task: Investigate the 2025-10-22 trace deltas showing ΔF≈-1.1 mm. Confirm `DetectorConfig.beam_center_*` is stored in millimetres (see `__main__.py:915-937`) and update `Detector._configure_geometry` so BEAM-pivot F/S values convert mm→m before constructing pix0 (match `nanoBragg.c:1184-1239`). Add targeted trace demonstrating the fix under `reports/2025-10-cli-flags/phase_h5/unit_fix/` and record Attempt #33 in fix_plan with metrics. |

### Phase I — Polarization Alignment (follow-up)
Goal: Match C’s Kahn polarization factor once lattice geometry aligns.
Prereqs: Phases F–H complete; traces show `F_latt` parity.
Exit Criteria: Polarization entries in C/PyTorch traces agree (≈0.9126 for supervisor command) and parity smoke stays green.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| I1 | Audit polarization inputs | [D] | ✅ Completed 2025-10-17. C defaults polar=1.0/polarization=0.0/nopolar=0 verified at nanoBragg.c:308-309. PyTorch BeamConfig.polarization_factor was defaulting to 0.0 instead of 1.0. |
| I2 | Implement polarization parity | [D] | ✅ Completed 2025-10-17. Updated BeamConfig.polarization_factor default to 1.0 (config.py:483-487). Added TestCLIPolarization with 3 tests (test_cli_flags.py:591-675). Tests verify default=1.0, -nopolar flag, and -polar override. |
| I3 | Final parity sweep | [P] | Attempt #27 (2025-10-06) failed with 124,538× intensity scaling gap; blocked until Phase J evidence resolves normalization divergence. |

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
| K1 | Align lattice factor math with C (SQUARE case) | [D] | ✅ 2025-10-24 Attempt #34 (commit 0fef8f7). `Simulator._compute_physics_for_position` now uses `sincg(torch.pi * h, Na)` (and k/l analogues) with the C-code snippet embedded. Regression `tests/test_cli_scaling.py::test_f_latt_square_matches_c` added (skips unless `NB_RUN_PARALLEL=1`). |
| K2 | Recompute scaling chain & extend to other shapes | [ ] | With SQUARE fixed, rerun the Phase J harness to generate `reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log` and refresh `phase_j/scaling_chain.md`. Spot-check ROUND/GAUSS/TOPHAT against C and document any deviations before closing this row. |
| K3 | Regression tests & documentation | [ ] | Once H5c/K2 evidence is green, run `env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest tests/test_cli_scaling.py::test_f_latt_square_matches_c -v`, archive the log under `phase_k/f_latt_fix/pytest.log`, and update `docs/architecture/pytorch_design.md` plus `phase_k/notes.md` with the corrected lattice-factor flow.

### Phase L — Final Parity & Regression Sweep
Goal: Demonstrate full parity for the supervisor command and close CLI-FLAGS-003.
Prereqs: Phases J–K complete; scaling regression tests green.
Exit Criteria: `nb-compare` metrics meet thresholds (correlation ≥0.999, sum_ratio 0.99–1.01, peak distance ≤1 px), targeted pytest nodes pass, docs/fix_plan.md Attempt #30 logs metrics, and this plan is ready for archival.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| L1 | Rerun supervisor command parity | [ ] | Execute the authoritative nb-compare command, stash outputs under `reports/2025-10-cli-flags/phase_l/supervisor_command/`, and verify metrics within thresholds. |
| L2 | Regression confirmation | [ ] | Run the CLI flag suite plus any new scaling tests (`env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py tests/test_cli_scaling.py -v`) with results saved to `phase_l/pytest.log`. |
| L3 | Closeout documentation | [ ] | Update docs/fix_plan.md exit criteria, archive this plan per SOP, and note parity completion in `docs/development/testing_strategy.md` if thresholds changed. |

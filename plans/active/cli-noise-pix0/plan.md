## Context
- Initiative: CLI Parity for nanoBragg PyTorch vs C (supports long-term goal in prompts/supervisor.md)
- Phase Goal: Accept `-nonoise` and `-pix0_vector_mm` flags with C-equivalent semantics so the parallel comparison command in prompts/supervisor.md executes end-to-end.
- Dependencies: specs/spec-a-cli.md §§3.2–3.4, docs/architecture/detector.md §5, docs/development/c_to_pytorch_config_map.md (detector pivot + noise), golden_suite_generator/nanoBragg.c lines 720–1040 & 1730–1860 (flag behavior), docs/debugging/detector_geometry_checklist.md (pix0 validation), docs/development/testing_strategy.md §2 (CLI parity tests).
- Current gap snapshot (2025-10-17 refresh): Phase F1/F2 delivered custom beam-vector wiring and the full CUSTOM pix0 transform, with validation artifacts under `reports/2025-10-cli-flags/phase_f*/`. The parity rerun (F3) remains outstanding, and C traces continue to show the MOSFLM orientation missing because `-mat` still collapses to canonical vectors. Polarization (C Kahn ≈0.913 vs PyTorch 1.0) stays deferred until geometry parity lands.
- Evidence status: Phase E artifacts (`reports/2025-10-cli-flags/phase_e/`) hold C/PyTorch traces, diffs, and beam-vector checks. Current harness injects the custom beam vector manually; CLI parity requires native wiring.

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

### Phase H — Polarization Alignment (follow-up)
Goal: Match C’s Kahn polarization factor once geometry aligns.
Prereqs: Phases F and G complete; traces confirm geometry parity.
Exit Criteria: Polarization entries in C/PyTorch traces agree (≈0.9126 for supervisor command) and parity smoke stays green.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| H1 | Audit polarization inputs | [ ] | Review CLI defaults/flags (`-polar`, `-nopolar`) and C calculations (nanoBragg.c:2080-2155); map them to PyTorch simulator inputs. |
| H2 | Implement polarization parity | [ ] | Update simulator polarization handling to compute Kahn factor per spec/C reference. Document conversions and add targeted regression tests. |
| H3 | Final parity sweep | [ ] | Rerun supervisor command traces verifying polarization parity; update docs/fix_plan.md with closure summary and archive plan. |

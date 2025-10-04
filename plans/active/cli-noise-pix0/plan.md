## Context
- Initiative: CLI Parity for nanoBragg PyTorch vs C (supports long-term goal in prompts/supervisor.md)
- Phase Goal: Accept `-nonoise` and `-pix0_vector_mm` flags with C-equivalent semantics so the parallel comparison command in prompts/supervisor.md executes end-to-end.
- Dependencies: specs/spec-a-cli.md §§3.2–3.4, docs/architecture/detector.md §5, docs/development/c_to_pytorch_config_map.md (detector pivot + noise), golden_suite_generator/nanoBragg.c lines 720–1040 & 1730–1860 (flag behavior), docs/debugging/detector_geometry_checklist.md (pix0 validation), docs/development/testing_strategy.md §2 (CLI parity tests).
- Current gap snapshot: CLI already stores `config['custom_pix0_vector']`, but `DetectorConfig`/`Detector` ignore it and always recompute pix0; there is no parser support for `-nonoise` or `-pix0_vector_mm`.

### Phase A — Requirements & Trace Alignment
Goal: Confirm the authoritative semantics for both flags and capture the C reference behavior (including unit expectations) before touching implementation.
Prereqs: Ability to run instrumented C binary via `NB_C_BIN` and collect traces.
Exit Criteria: Documented parity notes under `reports/2025-10-cli-flags/phase_a/` with explicit decisions on unit conversions and noise toggle ordering.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| A1 | Extract C reference for `-nonoise` | [ ] | Run the supervisor command with and without `-nonoise` using `NB_C_BIN=./nanoBragg`; capture stdout/stderr diff and note whether `noisefile` is suppressed despite flag order. |
| A2 | Capture pix0 vector ground truth | [ ] | Instrument C (add `TRACE_C:pix0_vector`) for the supervisor command; store logs under `reports/2025-10-cli-flags/phase_a/pix0_trace/`. Confirm units (meters vs mm) and whether C honors custom pix0 overrides. |
| A3 | Update findings memo | [ ] | Summarise results in `reports/2025-10-cli-flags/phase_a/README.md`, including conclusions on `beam_convention=CUSTOM` interactions and required unit conversions. |

### Phase B — CLI & Config Wiring
Goal: Teach the PyTorch CLI to parse both flags, thread them through configs, and respect overrides in Detector/Noise handling without breaking existing behavior.
Prereqs: Phase A report published; confirm existing CLI regression tests green (run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_entrypoint.py -q` if available).
Exit Criteria: `nanoBragg --help` lists both flags; manual dry run of supervisor command completes argument parsing and produces float image without raising.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| B1 | Extend argparse surface | [ ] | Add `-nonoise` (store_true) and `-pix0_vector_mm` (nargs=3) to `create_parser()`. Mirror help text from C usage strings. |
| B2 | Thread `-nonoise` to simulator | [ ] | Carry a `suppress_noise` boolean through `parse_and_validate_args`, set `NoiseConfig.generate_noise_image` (or skip noise writer entirely) when true, and ensure `-noisefile` is ignored with a parity warning. |
| B3 | Support pix0 overrides | [ ] | Extend `DetectorConfig` with a single `pix0_override_m` tensor slot; map both `-pix0_vector` (meters) and `-pix0_vector_mm` (millimetres) to this field inside `parse_and_validate_args`, normalising units and dtype/device. Update `Detector.__init__`/`_calculate_pix0_vector` to respect the override instead of recomputing. |
| B4 | Preserve meter and mm flag parity | [ ] | Ensure the existing `-pix0_vector` path (meters) now threads through the same override field so CUSTOM convention consumers regain functionality; add validation errors for mixed units or partial vectors. |
| B5 | Unit & cache hygiene | [ ] | Update detector cache invalidation so supplying pix0 overrides still triggers `invalidate_cache()` for dependent tensors; add assertions ensuring the stored tensor lives on the detector device/dtype and keeps gradient flow intact. |

### Phase C — Validation & Documentation
Goal: Prove parity via targeted tests and update docs/fix_plan so future loops know the flags are supported.
Prereqs: Phase B code ready; editable install available for CLI tests.
Exit Criteria: Tests and documentation changes landed; supervisor command successfully runs PyTorch CLI and reaches simulator without flag errors.

| ID | Task Description | State | How/Why & Guidance |
| --- | --- | --- | --- |
| C1 | Add CLI regression tests | [ ] | Create/extend pytest case under `tests/test_cli_flags.py` asserting arg parsing accepts both `-pix0_vector` (meters) and `-pix0_vector_mm` (millimetres) plus `-nonoise`; verify resulting configs normalise to identical meter-space tensors and that `noisefile` is skipped when suppressed. |
| C2 | Golden parity smoke | [ ] | Execute the supervisor command twice: once using C reference (`NB_C_BIN`), once via PyTorch CLI. Confirm CLI completes image generation; stash outputs under `reports/2025-10-cli-flags/phase_c/`. |
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

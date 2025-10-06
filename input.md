Timestamp: 2025-10-06 04:21:10Z
Commit: 1fcf3d3
Author: galph
Active Focus: [CLI-FLAGS-003] Phase G orientation + detector gradient hygiene
Summary: Implement Phase G orientation wiring and restore differentiable close_distance
Phase: Implementation
Focus: [CLI-FLAGS-003] Phase G — MOSFLM matrix orientation
Branch: feature/spec-based-2
Mapped tests: env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py tests/test_at_geo_003.py -v
Artifacts: reports/2025-10-cli-flags/phase_g/

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm (Phase G1) — env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py tests/test_at_geo_003.py -v

If Blocked: Capture C & PyTorch crystal-vector traces for the supervisor command at pixel (1039,685); save diff as reports/2025-10-cli-flags/phase_g/orientation_blocked_trace.md and add the divergence summary to docs/fix_plan.md Attempts.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:80 — Phase G (G1–G3) is the bottleneck preventing parity rerun; orientation from -mat must reach Crystal intact.
- docs/fix_plan.md:448 — Fix-plan next actions call out MOSFLM A* retention and the close_distance tensor regression; both must be cleared before Phase H.
- docs/architecture/pytorch_design.md:140 — Architecture requires reciprocal vectors to remain tensor-valued and reusable across rotations; orientation wiring must honor this.
- docs/development/c_to_pytorch_config_map.md:40 — CLI↔PyTorch parity mandates storing MOSFLM A* exactly as parsed; use this mapping when threading through configs.
- docs/debugging/debugging.md:34 — Parallel trace workflow remains mandatory; Phase G3 evidence must use TRACE_C/TRACE_PY comparison.
- reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/metrics.json — Current correlation ≈−5e-06 sets the baseline we must beat once orientation is fixed.
- src/nanobrag_torch/models/detector.py:480 — r-factor computation couples to close_distance; gradient fix must respect this codepath.
- tests/test_at_geo_006.py:46 — Solid-angle assertions rely on close_distance staying tensor-valued; keep these tests in mind during verification.

How-To Map:
- Export required env vars upfront:
- `export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md`
- `export NB_C_BIN=./golden_suite_generator/nanoBragg`
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` on every Python/pytest run.
- Phase G1 implementation steps:
- In `src/nanobrag_torch/__main__.py`, after `read_mosflm_matrix`, store Å⁻¹ reciprocal vectors on the config dict (`config['a_star']`, etc.).
- Convert numpy arrays to tensors lazily in Crystal to preserve device/dtype neutrality.
- Document decisions in `reports/2025-10-cli-flags/phase_g/config_notes.md`.
- Phase G2 implementation steps:
- Extend `CrystalConfig` dataclass to accept optional reciprocal vectors; default to None when CLI did not supply `-mat`.
- Update `Crystal` to use supplied vectors before constructing canonical ones; still perform misset + metric duality recalculations per Core Rules 12–13.
- Ensure reciprocal→real→reciprocal cycle recreates `V_actual` volume when orientation is provided.
- Keep new tensors differentiable; no `.item()`, `.numpy()`, or `.cpu()` inside the main pipeline.
- Record design reasoning in `reports/2025-10-cli-flags/phase_g/orientation_design.md`.
- Detector gradient hygiene:
- Replace the `.item()` assignment for `self.close_distance` with tensor-safe storage.
- Audit simulator usages (`src/nanobrag_torch/simulator.py:933`, `:1014`) to accept tensor inputs without implicit detaches.
- Create a quick grad sanity check (e.g., differentiate intensity w.r.t. distance) and log results to `reports/2025-10-cli-flags/phase_g/close_distance_gradcheck.md`.
- Testing sequence:
- `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py tests/test_at_geo_003.py -v`
- If CUDA available, rerun `pytest` with `--device cuda` (document availability in reports).
- Capture full pytest output into `reports/2025-10-cli-flags/phase_g/pytest.log`.
- Parity harness (Phase G3):
- Run C binary with supervisor command; log stdout/stderr to `parity/c_reference/command.log` and keep float image.
- Run PyTorch CLI with identical command; log to `parity/pytorch/command.log` and archive new float image.
- Execute `nb-compare --outdir reports/2025-10-cli-flags/phase_g/parity -- -mat A.mat ...` (full args from prompts/supervisor.md) to compute metrics.json.
- Parallel trace validation:
- Use `scripts/debug_pixel_trace.py` with updated configs to dump lattice vectors; store logs under `reports/2025-10-cli-flags/phase_g/trace_pytorch.log` and diff vs C trace (`trace_c.log`).
- Summarize first divergence (or lack thereof) in `trace_summary_orientation.md`.
- Documentation updates:
- Append Attempt #14 to `[CLI-FLAGS-003]` in docs/fix_plan.md summarizing Phase G progress, metrics, and close_distance fix.
- Update `plans/active/cli-noise-pix0/plan.md` by marking G1/G2/G3 status and linking artifact paths.
- Archive parity outputs under `reports/2025-10-cli-flags/phase_g/` per Protected Assets expectations.
- After implementation, run `git status` to verify only intentional files (plan docs, code) are staged; no stray artifacts should remain unstaged.
- Prepare commit message referencing SUPERVISOR guidelines if you hand back with supervisor changes bundled with code.
- Note any remaining TODOs in docs/fix_plan.md Attempts so future loops inherit accurate context.

Pitfalls To Avoid:
- Leaving `self.close_distance` as float breaks gradients; keep it tensor-valued.
- Recomputing canonical reciprocal axes when orientation is supplied will destroy MOSFLM intent; only fall back when vectors missing.
- Introducing device mismatches (CPU temp tensors inside CUDA runs) will break parity and perf; coerce via `.to()` as needed.
- Forgetting to update Crystal caches after injecting orientation will result in stale pixel coordinates; invalidate caches properly.
- Skipping trace comparison violates debugging SOP; always capture TRACE_C/TRACE_PY when parity fails.
- Editing or deleting assets listed in docs/index.md (e.g., loop.sh, input.md) is forbidden.
- Neglecting to rerun CLI tests risks regressing existing flag behavior; keep `tests/test_cli_flags.py` green.
- Deviating from vectorized tensor math (e.g., loops over pixels) will tank performance and fail guardrails.
- Forgetting to log artifacts under `reports/2025-10-cli-flags/phase_g/` leaves plan evidence incomplete.
- Allowing `scaled.hkl.1` cleanup before parity succeeds risks losing reproduction inputs; defer hygiene until plan closure.
- Skipping CUDA smoke validation (when available) violates device/dtype neutrality requirements.
- Overwriting reports from earlier phases without archival copies will erase audit trail; create new subdirectories per attempt.
- Bypassing AUTHORITATIVE_CMDS_DOC export can lead to stale command usage; keep the env var set for every test run.

Pointers:
- plans/active/cli-noise-pix0/plan.md:87 — Phase G checklist.
- docs/fix_plan.md:448 — Fix-plan status and updated next actions.
- docs/architecture/pytorch_design.md:140 — Reciprocal vector handling guidance.
- docs/development/c_to_pytorch_config_map.md:45 — MOSFLM config parity.
- docs/debugging/debugging.md:32 — Parallel trace SOP.
- nanoBragg.c:3135 — C reference for MOSFLM orientation + reciprocal conversion.
- src/nanobrag_torch/__main__.py:426 — Current -mat parsing location to augment.
- src/nanobrag_torch/models/crystal.py:520 — Reciprocal vector construction entry point.
- src/nanobrag_torch/models/detector.py:626 — close_distance assignment requiring tensor fix.
- scripts/debug_pixel_trace.py:35 — Trace harness for Phase G3.
- reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/metrics.json — Baseline parity failure metrics.
- prompts/supervisor.md:15 — Authoritative parity command to reproduce.
- docs/architecture/detector.md:70 — Pivot and pix0 formulas used while porting CUSTOM transform.
- docs/development/testing_strategy.md:72 — Device/dtype discipline checklist to cite in fix-plan updates.
- reports/2025-10-cli-flags/phase_f/beam_vector_after_fix.txt — Confirms beam-vector parity; reuse as reference while validating orientation.
- archive/fix_plan_archive.md:1 — Historical context for CLI flag work; check before pruning plan details.

Next Up:
- [CLI-FLAGS-003] Phase H polarization alignment once geometry parity is proven.
- [VECTOR-TRICUBIC-001] Phase A evidence capture after CLI flag parity stabilizes.
- [AT-TIER2-GRADCHECK] Phase A gradient audit resumes once detector tensors stay differentiable.

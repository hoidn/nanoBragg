timestamp: 2025-10-06 06:52:17Z
commit: e339f48
author: galph
Active Focus: [CLI-FLAGS-003] Phase H3b pix0 transform implementation
Summary: Implement the BEAM-pivot pix0 override transform, prove it with a targeted regression test, and archive full Phase H3b artifacts so parity work can resume.
Phase: Implementation
Focus: CLI-FLAGS-003
Branch: feature/spec-based-2
Mapped tests: pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_override_beam_pivot_transform -v
Artifacts: reports/2025-10-cli-flags/phase_h/implementation/

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — author the pix0 override regression test, apply the BEAM-pivot transform fix, then run `pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_override_beam_pivot_transform -v`.
If Blocked: Capture failing command output under `reports/2025-10-cli-flags/phase_h/implementation/blocked/`, log the first divergence and hypothesis in `implementation_notes.md`, append the attempt to `attempt_log.txt`, and stop before reverting code or running unrelated suites.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:102 — Phase H3b details the implementation and testing checklist; completing it is the gate to Phase H4 parity work.
  Use the plan checklist to tick tasks as you produce artifacts; update it if additional guidance emerges during coding.
- docs/fix_plan.md:468 — Next Actions now require the BEAM-pivot transform when overrides are provided and demand logged artifacts in a dedicated folder.
  Keep the fix_plan entry current by referencing new artifact paths once the regression test is in place.
- docs/architecture/detector.md:205 — Contains the normative derivation for pix0 under BEAM pivot; the PyTorch implementation must match this math exactly.
  Cross-check units (meters inside detector) before finalising tensor math to avoid mm↔m confusion.
- docs/development/c_to_pytorch_config_map.md:33 — Confirms how `-pix0_vector_mm` maps into detector config fields; consult before touching the parser output.
  This guard prevents accidental double conversion when you refactor override handling.
- golden_suite_generator/nanoBragg.c:1833 — Ground-truth C code computing pix0; port this verbatim to avoid drift.
  Reference the line numbers in comments to satisfy Core Implementation Rule 11.
- reports/2025-10-cli-flags/phase_h/pix0_reproduction.md:1 — Provides numeric targets (pix0 delta, pixel positions, scattering vector, h/k/l) used for assertions.
  Embed these values into the regression test to lock in expectations.
- reports/2025-10-cli-flags/phase_h/trace_py_after_H3_refresh.log:1 — Shows the current divergence; use it as a before snapshot when writing notes.
  After the fix, capture a new trace for Phase H4; today just reference the existing "before" metrics.
- reports/2025-10-cli-flags/phase_h/implementation_notes.md:120 — Captures the proposed fix; update with implementation outcomes so future loops inherit context.
  Note any open risks (polarization, scaled.hkl cleanup) so they remain visible.
- docs/development/testing_strategy.md:14 — Enforces device/dtype neutrality; new tests and code must uphold this rule on CPU and CUDA.
  Mention CPU/GPU coverage in the attempt log to document compliance.
- docs/debugging/debugging.md:18 — Parallel trace SOP underpins Phase H4; keeping today’s fix faithful prevents rework when running traces later.
  Cite the SOP in notes to remind future loops that parity validation is queued next.

How-To Map:
- Step 1: Export the authoritative command doc before executing anything (`export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md`).
- Step 2: Prepare the artifact directories (`mkdir -p reports/2025-10-cli-flags/phase_h/implementation/{blocked,notes,logs}`).
- Step 3: Review `pix0_reproduction.md` and `implementation_notes.md` to refresh the targeted deltas and the proposed fix steps.
- Step 4: Update `src/nanobrag_torch/models/detector.py` within `_calculate_pix0_vector`.
- Step 4a: When `pix0_override_m` is supplied and pivot == BEAM, compute `Fbeam`/`Sbeam` with existing helpers (respect convention-dependent +0.5 offsets).
- Step 4b: Form `pix0_calc = -Fbeam * self.fdet_vec - Sbeam * self.sdet_vec + self.distance_corrected * beam_vector`; ensure all tensors are on `self.device` with `self.dtype` and gradients preserved.
- Step 4c: Assign `self.pix0_vector = pix0_calc` instead of the raw override, leaving SAMPLE pivot logic unchanged.
- Step 4d: Update any relevant caching or `close_distance` recalculation paths to use the transformed tensor without breaking existing assertions.
- Step 4e: Leave comments referencing the exact nanoBragg.c lines (1833-1835) as required by Core Implementation Rule 11.
- Step 5: Implement safety checks so dual use of override + SAMPLE pivot still follows spec (override ignored with explanatory comment).
- Step 6: Author regression tests under `tests/test_cli_flags.py`.
- Step 6a: Add class `TestCLIPix0Override` reusing parser fixtures; include docstring referencing plan H3b.
- Step 6b: Create helper computing the analytic pix0 vector via the same formula using CLI inputs and compare against detector output.
- Step 6c: Parameterise over `(device, dtype)` pairs: `(cpu, torch.float32)` always, `(cuda, torch.float32)` when `torch.cuda.is_available()`; use `pytest.skip` gracefully when CUDA missing.
- Step 6d: Assert per-component error ≤1e-6 m and record the absolute delta in the test failure message.
  Mirror the structure used in existing CLI flag tests for consistency (use `pytest.approx`).
- Step 6e: Also verify derived pixel position/hkl deltas shrink below the measured thresholds (optional but encouraged) to mirror the reproduction notebook.
  Store the intermediate values in local variables so they can be re-used when writing parity notes later.
- Step 7: Run targeted pytest with logging (`env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_override_beam_pivot_transform -v | tee reports/2025-10-cli-flags/phase_h/implementation/pytest_pix0_override.log`).
  Inspect the log for both CPU and CUDA branches, and annotate pass/skip outcomes directly in the file for quick review.
- Step 8: If CUDA path ran, append the GPU device name and results summary to the log; otherwise note the skip reason in a short text file.
- Step 9: Capture a refreshed formula check after the fix by reusing the analytic script (`python scripts` snippet or inline) and append output to `reports/2025-10-cli-flags/phase_h/implementation/formula_check.md`.
  Include both raw numbers and the absolute delta so future loops can diff without rerunning the script.
- Step 10: Update `implementation_notes.md` with sections for code changes, test evidence, remaining risks (e.g., polarization), and next tasks (Phase H4).
  Cite file paths and command output filenames so the attempt log stays self-contained.
- Step 11: Append Attempt #22 in `reports/2025-10-cli-flags/phase_h/attempt_log.txt` summarising commands, metrics, devices, and outcomes.
  Include start/end timestamps plus any skips to keep chronological auditing simple.
- Step 12: Stage modifications (`git add src/nanobrag_torch/models/detector.py tests/test_cli_flags.py docs/fix_plan.md plans/active/cli-noise-pix0/plan.md reports/... input.md`) and commit once satisfied.
  Double-check `git status` to ensure only intentional files are staged; no stray notebooks or editor backups.
- Step 13: Include the pytest node in the commit message and cross-reference plan H3b.

Pitfalls To Avoid:
- Avoid introducing Python loops in detector pix0 code; rely on existing tensor ops so vectorization and autograd stay intact.
  Regressing to loops will undo past performance work and violate vectorization guardrails.
- Skip `.cpu()`, `.numpy()`, `.item()` inside the production path; those detach tensors and will violate device neutrality requirements.
  Use `.to()` / `.type_as()` to align devices and dtypes instead.
- Preserve SAMPLE pivot override semantics—C ignores overrides there, so the PyTorch port must continue to do the same.
  Changing this would break spec alignment and complicate future parity checks.
- Maintain `_cached_pix0_vector` updates; failing to refresh the cache will cause stale geometry downstream and spurious detector diffs.
  After assigning the transformed pix0, update the cache clone exactly as today.
- Stay focused on the targeted pytest node; running the full suite burns time and risks masking regressions with unrelated failures.
  If import issues arise, `pytest --collect-only -q` is the only extra command to run.
- Treat Protected Assets (docs/index.md list) as immutable; never rename/remove `input.md`, `loop.sh`, `supervisor.sh`, or other guarded files.
  The Protected Assets rule is now a hard guard rail—violations block automation.
- Ensure the CUDA branch of the regression test skips gracefully when no GPU exists.
  Use `pytest.skip` with a clear message; do not rely on `assert torch.cuda.is_available()`.
- Convert mm inputs to meters in tests; mixing units silently reintroduces the 1.14 mm delta we just diagnosed.
  Keep tolerances tight (≤1e-6 m) to catch future drift immediately.
- Do not touch trace harnesses or parity scripts in this loop; Phase H4 will handle trace regeneration after the fix lands.
  Today’s scope is confined to implementation + regression test only.

Pointers:
- plans/active/cli-noise-pix0/plan.md:99 — Phase H3b checklist with exit criteria and artifact expectations.
- docs/fix_plan.md:464 — Status, attempts history, and updated Next Actions for `[CLI-FLAGS-003]`.
- docs/architecture/detector.md:205 — Detailed BEAM pivot derivation and unit conventions to replicate.
- docs/development/c_to_pytorch_config_map.md:21 — Mapping of CLI detector flags into config fields.
- golden_suite_generator/nanoBragg.c:1833 — Exact C implementation of the pix0 calculation for BEAM pivot.
- reports/2025-10-cli-flags/phase_h/pix0_reproduction.md:1 — Numeric targets for pix0, pixel positions, scattering vectors, and h/k/l deltas.
- reports/2025-10-cli-flags/phase_h/trace_py_after_H3_refresh.log:1 — Current divergence snapshot to compare against after the fix.
- reports/2025-10-cli-flags/phase_h/implementation_notes.md:120 — Prior hypothesis log that today’s implementation should resolve.
- tests/test_cli_flags.py:1 — Existing CLI regression test patterns; follow fixtures and naming conventions.
- docs/development/testing_strategy.md:14 — Device/dtype neutrality checklist to cite when logging results.
- docs/debugging/debugging.md:18 — Parallel trace SOP for the upcoming Phase H4 parity run.
- CLAUDE.md: Protected Assets Rule reminders; ensure compliance while editing scripts/docs.

Next Up: Phase H4 parity smoke (rerun trace harness, diff against C, capture <0.5% `F_latt` deltas and <10× intensity ratios) once the pix0 fix lands cleanly and regression tests pass.

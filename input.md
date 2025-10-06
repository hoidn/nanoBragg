Summary: Restore pix0 precedence with custom detector vectors so PyTorch reproduces C `F_latt` for the supervisor command.
Phase: Implementation
Focus: CLI-FLAGS-003 / Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_flags.py::TestCLIPix0Override
Artifacts: reports/2025-10-cli-flags/phase_h5/pytest_h5b_revert.log, reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/, reports/2025-10-cli-flags/phase_h5/parity_summary.md, docs/fix_plan.md (Attempt #31 entry)
Do Now: CLI-FLAGS-003 H5b — revert custom-vector pix0 override (`env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override -v`)
Do Now note: Commit d6f158c kept overrides disabled; Attempt #29 reintroduced them. Restore the pre-Attempt-29 behavior while preserving new r-factor math.
Do Now note: Annotate code comments referencing `reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md` so future readers know why overrides are skipped with custom vectors.
If Blocked: Halt after editing the detector; log the failure cause, git diff, and current pix0 deltas in `reports/2025-10-cli-flags/phase_h5/attempt_h5b_blocked.md`, then wait for supervisor guidance.
If Blocked note: Include command output (tail 20 lines) and environment details (device availability, torch version).
If Blocked note: Mention whether pytest or trace harness failed; do not attempt ad-hoc fixes.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md §Phase H5 — Newly revised tasks require undoing the override for custom vectors before Phase K normalization.
- docs/fix_plan.md:506-551 — Next actions and Attempt #30 observations explicitly call for the revert + fresh PyTorch traces.
- reports/2025-10-cli-flags/phase_j/scaling_chain.md — Shows the 3.6e-7 `F_latt` ratio driven by the 1.14 mm pix0 delta; reverting restores geometry parity.
- specs/spec-a-cli.md §§Precedence — Custom vectors supersede pix0 overrides; implementation must follow the normative spec.
- docs/architecture/detector.md §5.3 — Contains BEAM pivot formulas and projection math that must remain intact after the revert.
- docs/debugging/detector_geometry_checklist.md — Provides mandatory unit/orientation checks when validating the updated traces.
- AUTHORITATIVE_CMDS_DOC=docs/development/testing_strategy.md — Confirms targeted pytest cadence and CPU/CUDA smoke expectations.

How-To Map:
1. Code change
   - Open `src/nanobrag_torch/models/detector.py`.
   - Locate the pix0 override block inside `_calculate_pix0_vector`.
   - Guard the override projection with `if pix0_override_tensor is not None and not self.has_custom_vectors():` (or equivalent helper).
   - Keep device/dtype coercion and comments; cite `c_precedence_2025-10-22.md` when explaining the guard.
   - Ensure CUSTOM path still updates `beam_center_{f,s}` when overrides apply in the no-custom case.
2. Targeted tests
   - Run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override -v | tee reports/2025-10-cli-flags/phase_h5/pytest_h5b_revert.log`.
   - Confirm CPU and CUDA parametrisations respect the new guard (CUDA will auto-skip if unavailable).
   - If assertions change, adjust expectations but keep tolerances ≤5e-5 m.
3. PyTorch traces
   - Reuse the Phase H harness: `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log`.
   - Diff against `reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/with_override.log` (expect identical pix0/F/S, h/k/l, `F_latt`).
   - Record deltas in `parity_summary.md` (<5e-5 m pix0, <1e-3 relative `F_latt`).
4. Documentation updates
   - Append a new Attempt (#31) in `docs/fix_plan.md` summarising the revert, pytest results, and trace metrics.
   - Update `reports/2025-10-cli-flags/phase_h5/parity_summary.md` with a table of old vs new values.
   - Note any test changes in `reports/2025-10-cli-flags/phase_h5/implementation_notes.md`.

Pitfalls To Avoid:
- Do not edit reference logs under `reports/2025-10-cli-flags/phase_h5/c_traces/`; they are protected evidence.
- Avoid reintroducing `.cpu()`, `.detach()`, or `.item()` inside `_calculate_pix0_vector`; differentiability must remain intact.
- Keep MOSFLM/XDS behavior untouched; only guard the override when custom vectors are explicitly provided.
- No ad-hoc scripts—reuse existing harnesses and pytest selectors per testing_strategy.md.
- Maintain Protected Assets; consult docs/index.md before moving or deleting tooling.
- Run the targeted pytest exactly once; no full suite this loop.
- Preserve device/dtype neutrality in regression tests; adjust tolerances only with justification logged in parity_summary.md.
- When updating docs/fix_plan.md, keep Attempt chronology intact and cite plan cross-references.
- Ensure new logs land under `reports/2025-10-cli-flags/phase_h5/` with the 2025-10-22 stamp to prevent clobbering earlier attempts.
- Capture git diff prior to commit; only include detector.py, parity docs, reports, and fix_plan updates.

Pointers:
- plans/active/cli-noise-pix0/plan.md:95-146 — Phase H5 checklist, exit criteria, and reporting expectations.
- docs/fix_plan.md:506-551 — Attempt #29/#30 narrative + updated Next Actions.
- reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md — Authoritative C precedence evidence.
- reports/2025-10-cli-flags/phase_j/scaling_chain.md — Quantifies the current F_latt gap you are closing.
- docs/architecture/detector.md §5 — Pix0 computation details and convention nuances.
- docs/development/testing_strategy.md §1.5 — Targeted pytest requirements and logging conventions.
- docs/debugging/detector_geometry_checklist.md — Mandatory validation steps before claiming detector parity.
- reports/2025-10-cli-flags/phase_h/trace_harness.py — Reusable script for PyTorch trace capture.
- tests/test_cli_flags.py:375-452 — Regression tests covering override precedence scenarios.
- plans/active/vectorization.md — Leave untouched; vectorization remains pending until CLI parity is restored.

Next Up: Phase H5c PyTorch trace verification and docs/fix_plan Attempt #31 closure once override parity is restored.
Next Up note: After traces align, you can pivot to Phase K normalization tasks per plan (steps ordering + scaling fix).

Verification Checklist:
- Confirm `Detector.has_custom_vectors()` (or equivalent) accurately reflects CLI inputs (custom f/s/o or None).
- Print temporary debug (guarded by `if __debug__`) only if needed; remove before commit to keep traces clean.
- Validate that `self.beam_center_f/s` remain tensors post-revert; avoid silent Python floats.
- Double-check `distance_corrected` and `close_distance` invariants via trace harness output.
- Ensure new Attempt entry references plan lines and artifacts explicitly (dates, commands, metrics).

Metrics To Capture:
- Pix0 delta (PyTorch - C) in meters for each component (target <5e-5).
- `F_latt` ratio Py/C (target 0.999–1.001) reported in parity_summary.md.
- `h`, `k`, `l` fractional offsets compared to C trace (should match within 1e-6).
- pytest duration and device coverage recorded in pytest log header.
- Git SHA in parity_summary.md for reproducibility.

Reporting Notes:
- Update `phase_h5/parity_summary.md` intro paragraph to mention Attempt #31 and cite new artifacts.
- Cross-link `phase_h5/implementation_notes.md` with the exact detector.py lines changed.
- When editing docs/fix_plan.md, keep markdown bullet indentation consistent (two spaces before hyphen inside Attempts).
- Record command invocations verbatim in the relevant report to aid future reproductions.
- Tag parity summary tables with "after Attempt #31" so later archives distinguish versions.

Command Log Expectations:
- `pytest_h5b_revert.log` should include command header, environment variables, and summary lines.
- Trace harness output should preserve `TRACE_PY` ordering; no manual edits to log lines.
- Diff commands (e.g., `diff -u .../trace_c .../trace_py`) may go into `parity_summary.md` as fenced code for clarity.
- If additional sanity checks are run (e.g., quick smoke ROI), document them separately under `reports/2025-10-cli-flags/phase_h5/sanity/`.
- Document wall-clock timing for trace harness to monitor any regressions.

Fallback Plan:
- If revert causes broader regressions, capture `git diff` output into `reports/.../attempt_h5b_blocked.md` and ping supervisor with summary + hypothesis.
- Should tests reveal stale fixtures, update them in a separate patch queued after parity is restored.
- If CUDA skips unexpectedly, note availability status and driver version in the report.
- Maintain clean workspace; stash unrelated files before proceeding.
- Escalate if evidence suggests C actually honors overrides—include new C traces before any PyTorch edits.

Coding Reminders:
- Respect Core Rule #16 (device/dtype neutrality) when modifying helper methods.
- Use small helper (e.g., `_has_custom_vectors`) if readability improves; include docstring referencing C behavior.
- Keep magnet for gradient flow by reusing existing tensors where possible (no fresh tensor creation on every call).
- Re-run static type checks if available (optional) to ensure signature parity.
- Update docstrings/comments to clarify precedence decisions for future maintainers.

Documentation Touchpoints:
- Mention revert rationale in `docs/development/pytorch_runtime_checklist.md` if override rules affect guardrails.
- Consider adding a short FAQ note in `README_PYTORCH.md` under CLI flags about custom vectors vs pix0 overrides (optional, only if time).
- Ensure `plans/active/cli-noise-pix0/plan.md` Phase H5 table state transitions ([ ], [D]) are accurate after work.
- Archive any superseded parity summaries under `reports/archive/` if file size balloons.
- Keep Attempt numbering monotonic; if Attempt #31 already used externally, bump to next free number.

Coordination Notes:
- Log progress in Attempts History within docs/fix_plan.md even if partial (e.g., revert complete, traces pending).
- If time remains, outline next steps for Phase K in a short note for supervisor review.
- Avoid overlapping plan phases (no Phase K edits until H5 marked complete).
- Mention in parity_summary.md whether override revert changed runtime metrics (if measurable).
- Maintain chronological ordering in `reports/2025-10-cli-flags/phase_h5/` directories (YYYY-MM-DD).

Housekeeping:
- Verify `input.md` is not touched by Ralph; only supervisor writes to it.
- Keep repo clean: remove temporary diff files after use.
- Run `git status` before finishing to ensure only intended files changed.
- Prepare commit message referencing "CLI-FLAGS-003 H5b revert" and list tests run.
- Push branch after commit; supervisor expects remote sync for next loop.

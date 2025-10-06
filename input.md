timestamp: 2025-10-06 05:41:11Z
commit: 7f55b09
author: galph
Active Focus: CLI-FLAGS-003 — Phase H beam vector propagation

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — Phase H2 beam vector propagation; env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIBeamVector::test_custom_beam_vector_propagates -v
If Blocked: Re-run KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py and capture a fresh trace diff under reports/2025-10-cli-flags/phase_h/blockers/ before logging the blocker in docs/fix_plan.md Attempt history.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:99 — Phase H2 explicitly targets the missing Detector→Simulator beam propagation; finishing it unblocks the rest of Phase H.
- docs/fix_plan.md:448 — Current Next Actions call out H2–H4; keeping docs aligned requires closing H2 first.
- src/nanobrag_torch/simulator.py:463 — Hard-coded MOSFLM/XDS defaults override CLI `-beam_vector`, producing the incident_vec divergence in Attempt #19; this is the root to fix.
- reports/2025-10-cli-flags/phase_h/trace_comparison.md — Evidence log shows beam mismatch cascading into wrong `hkl_frac` and `F_latt`; new traces must demonstrate the fix.
- arch.md:107 — Architecture contract demands Simulator incident beam direction match detector convention; CUSTOM overrides must survive to physics kernels.
- specs/spec-a-cli.md:58 — Spec confirms `-beam_vector` is part of the CUSTOM flag cluster; CLI parity fails until we honour that mapping end-to-end.
- specs/spec-a-parallel.md:265 — Selecting any custom vector forces CUSTOM convention; our implementation must keep that side effect intact post-fix.
- docs/development/testing_strategy.md:82 — Parallel trace SOP obligates before/after artifacts when closing parity gaps; tracing is not optional here.
- reports/2025-10-cli-flags/phase_g/trace_summary_orientation_fixed.md — Orientation parity is already clean; the remaining delta isolates to beam/lattice, so H2 is the next logical lever.
- plans/active/vectorization.md:1 — Long-term goal #2 stays paused until CLI parity stabilises; completing H2 keeps vectorization work from being blocked by upstream physics bugs.

Context Notes:
- Phase F2 already ports the CUSTOM pix0 transform; do not revisit that logic unless new evidence surfaces.
- MOSFLM orientation ingestion (Phase G2/G3) is confirmed; expect rotated lattice vectors to match C exactly before your changes.
- The supervisor command runs with BEAM pivot because distance is set; ensure this remains true post-fix.
- Oversample is forced to 1; if the simulator infers a different value, document and correct it before proceeding.
- The harness currently imports `scaled.hkl`; do not switch to `scaled.hkl.1` to avoid Protected Asset issues.
- Detector basis vectors come from CLI custom inputs; verify the simulator does not recompute them implicitly during the fix.
- Beam fluence/flux math is already validated; avoid touching scaling while debugging beam direction.
- Keep polarization disabled while testing to isolate lattice physics; log that choice in the summary.
- Check that `trace_pixel` remains `(1039, 685)` so parity compares the same pixel.
- After the fix, expect `incident_vec` to match C within 1e-9 per component; deviations beyond that hint at normalization slip.
- Document any temporary harness edits so they can be reverted or archived cleanly in later loops.
- Note that Attempt #19 already stored pre-fix traces; keep file names distinct to avoid confusion.

How-To Map:
- Create output folders (`mkdir -p reports/2025-10-cli-flags/phase_h`) so new logs do not overwrite Phase G artifacts.
- Update src/nanobrag_torch/simulator.py to fetch `self.detector.beam_vector`, normalise it, and cache it as a tensor with the caller’s device/dtype; keep the old convention defaults as fallbacks when no detector is present.
- Ensure the beam vector pull happens before torch.compile invocation to avoid graph rebuilds; reuse existing cloning logic in `_compute_physics_for_position`.
- Add an inline helper (pure function) if needed to normalise the vector without introducing device churn; keep it private to simulator.py.
- Instrument the fix with lightweight asserts in the harness only (no production prints) to confirm the vector is length-one before/after.
- Refresh the trace harness: `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py > reports/2025-10-cli-flags/phase_h/trace_py_after_beam_fix.log 2>&1` and diff against the existing C trace (`diff -u reports/2025-10-cli-flags/phase_g/traces/trace_c.log reports/2025-10-cli-flags/phase_h/trace_py_after_beam_fix.log > reports/2025-10-cli-flags/phase_h/trace_diff_after_beam_fix.log`).
- Capture a short markdown summary (`reports/2025-10-cli-flags/phase_h/beam_fix_summary.md`) noting incident_vec, hkl_frac, and F_latt deltas before rerunning parity.
- Add a focused pytest in tests/test_cli_flags.py (e.g., class TestCLIBeamVector) that invokes the CLI parser, constructs Detector/Simulator, and asserts the simulator’s incident vector matches the CLI override; keep execution under one second.
- Run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIBeamVector::test_custom_beam_vector_propagates -v` and copy the log to `reports/2025-10-cli-flags/phase_h/pytest_beam_vector.log`.
- After tests, update docs/fix_plan.md Attempt history with artifact paths (`trace_py_after_beam_fix.log`, `trace_diff_after_beam_fix.log`, pytest log) and mark plan task H2 as [D] if criteria met.
- Leave polarization disabled during checks to isolate beam/lattice behaviour; document this in the summary so later phases know the conditions.
- Before finishing, stage only intentional files and keep prompts/debug.md untouched; mention any remaining dirty files in the Attempt note if they persist.
- Re-read plans/active/cli-noise-pix0/plan.md after edits to ensure Phase H guidance still matches the work being done.
- Prepare a brief note for Phase H3 describing any residual mismatches so the next loop can start quickly.
- Update reports index if new artifact filenames differ from previous conventions.
- Double-check that CLI argument parsing still routes custom beam vectors correctly by running the parser in isolation (`PYTHONPATH=src python - <<'PY' ...`).

Verification Checklist:
- Confirm git diff for src/nanobrag_torch/simulator.py only touches the beam-direction block and related helpers.
- Validate `trace_py_after_beam_fix.log` prints `TRACE_PY: incident_vec` matching the C log within tolerance.
- Ensure the new pytest fails pre-fix and passes post-fix (document the before/after result in the Attempt note).
- Check that docs/fix_plan.md gains a new Attempt with status + artifact list; no stale placeholders.
- Verify plan task H2 is toggled to `[D]` once evidence is archived.
- Confirm `reports/2025-10-cli-flags/phase_h/beam_fix_summary.md` references all relevant artifacts with relative paths.
- Make sure no new files appear outside `reports/` and `tests/`; repo hygiene must stay intact.
- Run `pytest --collect-only -q` if pytest emits collection warnings; log any anomalies.
- Ensure timestamps in artifacts follow ISO-8601 or match existing naming conventions.
- Capture any outstanding TODOs for H3/H4 in the summary so supervision continuity holds.

Pitfalls To Avoid:
- Do not reintroduce `.item()` or `.cpu()` inside compiled physics paths; keep tensors differentiable per Core Rule #9.
- Maintain device/dtype neutrality—source the beam vector on whatever device the detector currently uses.
- Avoid adding Python loops; keep the change purely tensor-based so vectorization is preserved.
- Preserve CUSTOM side effects: if any custom vector is provided, ensure convention stays CUSTOM and no implicit fallback occurs.
- Respect Protected Assets; never touch files referenced by docs/index.md.
- Run only the targeted pytest configured above; defer full test suites until the implementation loop that lands a fix.
- Keep trace harness modifications confined to reports/; production code must not gain debug prints.
- Ensure the new pytest uses `pytest.mark.parametrize` sparingly to avoid long runtimes; focus on the single supervisor configuration.
- Watch for normalization drift—unit test should assert `torch.allclose(norm, 1.0, atol=1e-6)`.
- Update plan + fix_plan promptly; stale coordination docs are considered regressions for supervisor loops.
- Do not delete or rename `reports/2025-10-cli-flags/phase_*` directories; Protected Assets rule extends via docs/index.md references.
- Avoid editing scripts under `golden_suite_generator/` during this loop; scope is restricted to PyTorch parity.
- When writing new tests, import simulator via installed package path (`from nanobrag_torch import ...`) to mirror CLI usage.
- Avoid committing temporary harness prints; keep output clean for future diffs.

Pointers:
- plans/active/cli-noise-pix0/plan.md:99 — Phase H task table with updated guidance.
- docs/fix_plan.md:448 — [CLI-FLAGS-003] ledger entry and Attempts context.
- src/nanobrag_torch/simulator.py:463 — Beam initialization block to modify.
- reports/2025-10-cli-flags/phase_h/trace_harness.py — Harness to reuse for before/after traces.
- reports/2025-10-cli-flags/phase_h/trace_comparison.md — Current divergence analysis to update post-fix.
- docs/development/testing_strategy.md:70 — Parallel trace-driven debugging SOP reference.
- arch.md:107 — Incident beam direction architecture requirement.
- specs/spec-a-cli.md:58 — CLI flag definition covering -beam_vector within CUSTOM cluster.
- specs/spec-a-parallel.md:265 — CUSTOM convention behaviour expectations.
- plans/active/vectorization.md:1 — Deferred vectorization roadmap (for context on long-term priorities).
- reports/2025-10-cli-flags/phase_g/traces/trace_c.log — C reference trace; do not regenerate.
- reports/2025-10-cli-flags/phase_g/trace_summary_orientation_fixed.md — Orientation evidence baseline.
- reports/2025-10-cli-flags/phase_h/beam_fix_summary.md — New artifact to populate after the fix.
- tests/test_cli_flags.py — Location to house the new beam propagation test.
- reports/2025-10-cli-flags/phase_h/pytest_beam_vector.log — Pytest artifact path for this loop.

Next Up:
- Option 1: Phase H3 — Diagnose remaining lattice mismatch once beam parity evidence is green.
- Option 2: Phase H4 — Execute parity rerun without polarization and archive metrics after H3 succeeds.
- Option 3: Prep notes for Phase I polarization alignment (no implementation yet) if H2 closes early.
- Option 4: If time remains, stage groundwork for removing manual incident-beam overrides from other harnesses (docs-only update).

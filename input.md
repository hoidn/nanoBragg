# 2025-10-06 05:21 UTC | 4dab2ea | galph | Active Focus: CLI-FLAGS-003 Phase H lattice alignment
Summary: Capture fresh C↔PyTorch traces without manual overrides to pinpoint the lattice/F_latt divergence before polarization work.
Phase: Evidence
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_h/

Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — Phase H1 trace refresh; run `env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py > reports/2025-10-cli-flags/phase_h/trace_py.log 2> reports/2025-10-cli-flags/phase_h/trace_py.stderr`

If Blocked: Document the blocker in `reports/2025-10-cli-flags/phase_h/blockers.md` and log an Attempt entry in docs/fix_plan.md before switching tasks.

Priorities & Rationale:
- Phase H1 requires a clean PyTorch trace without manual beam overrides so we can trust the `hkl_frac` deltas (plans/active/cli-noise-pix0/plan.md:110).
- docs/development/c_to_pytorch_config_map.md stresses CUSTOM convention parity; lattice mismatches trace back to Na/Nb/Nc handling, so we need raw traces first.
- `trace_summary_orientation_fixed.md` shows reciprocal parity yet F_latt differs by 3 orders; reproducing that gap is prerequisite to Phase H2 edits.
- Long-term Goal #1 hinges on closing CLI parity before vectorization; without lattice evidence we risk guessing at fixes.
- `reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/metrics.json` already captured the pre-orientation correlation (~-5e-06); we need a new baseline after orientation to measure improvement.
- Capturing evidence now keeps docs/fix_plan Attempts synchronized, preventing drift when we later commit implementation fixes.

Context Notes:
- The C trace at `reports/2025-10-cli-flags/phase_g/traces/trace_c.log` is authoritative; do not regenerate it unless we re-instrument the C code.
- PyTorch trace currently lives in `phase_g/trace_py_fixed.log` and still shows `F_latt` off by ~5.7e2×.
- The harness still forces `simulator.incident_beam_direction`; removing it lets Detector.apply_custom_vectors() run end-to-end.
- `scaled.hkl.1` duplicates `scaled.hkl`; leave it untouched until Phase H3/H plan closure to avoid Protected Asset confusion.
- C run uses BEAM pivot because distance is specified; verify PyTorch trace logs the same pivot selection after your edits.
- Oversample=1 in the supervisor command — note in trace summary if you see accidental oversample toggles.
- Keep phi/osc/phisteps consistent with C (0, 0.1, 10); double-check the harness doesn’t revert to defaults.
- Ensure the harness still writes float image to avoid lazy evaluation; `simulator.run()` must execute.

How-To Map:
- `mkdir -p reports/2025-10-cli-flags/phase_h` before writing new outputs.
- Copy the existing harness for edits: `cp reports/2025-10-cli-flags/phase_e/trace_harness.py reports/2025-10-cli-flags/phase_h/trace_harness.py` (edit the copy to remove the manual `simulator.incident_beam_direction` override and to write outputs under phase_h/).
- In the copied harness, update output paths so any intermediate dumps land in `phase_h/` (protect prior artifacts).
- Strip the manual incident-beam override and add an inline comment noting that Detector now consumes CLI vectors directly.
- Verify the harness imports `CrystalConfig` MOSFLM vectors from `read_mosflm_matrix` so Phase G fixes stay in play.
- Sanity-check the harness still loads `scaled.hkl` (not `.1`) and the same A.mat; log their `stat` output in the summary.
- After editing, run `env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py` and redirect stdout/stderr as in Do Now.
- Capture a unified diff vs the latest C trace using `diff -u reports/2025-10-cli-flags/phase_g/traces/trace_c.log reports/2025-10-cli-flags/phase_h/trace_py.log > reports/2025-10-cli-flags/phase_h/trace_diff.log`.
- Generate a TSV with key variables (`paste` or custom script) to make `hkl_frac` and `F_latt` comparisons easy: `paste reports/2025-10-cli-flags/phase_g/traces/trace_c.log reports/2025-10-cli-flags/phase_h/trace_py.log > ...` (optional but useful).
- Summarize findings (first divergence, metrics) in `reports/2025-10-cli-flags/phase_h/trace_comparison.md` — include `F_latt_a/b/c`, `hkl_frac`, intensities, and note beam vector equality.
- Add a short bullet to the summary covering detector pivot, oversample setting, and phi-step count taken from the new trace.
- Update docs/fix_plan.md Attempts with Phase H1 evidence once artifacts exist (reference the new files explicitly).
- Leave the old Phase E harness intact; Phase H should stand alone so we can archive it later.
- Keep environment variable `KMP_DUPLICATE_LIB_OK=TRUE` set ahead of any torch import to avoid MKL crashes.
- If CUDA is available, note whether harness runs CPU-only; GPU runs are optional for this evidence pass but record device in the summary.
- Save command transcripts (e.g., `reports/.../commands.txt`) so future loops can repeat the evidence precisely.

Pitfalls To Avoid:
- Do not restore the manual beam-direction override; we need the CLI wiring to drive the detector.
- Avoid `.item()` on tensors in the harness — traces must preserve gradients for later phases.
- Stay within Protected Assets policy: never move/delete files listed in docs/index.md (e.g., loop.sh, supervisor.sh, input.md).
- Do not rerun parity with polarization tweaks yet; Phase H isolates lattice math only.
- No ad-hoc scripts outside `reports/` or `scripts/`; keep new helpers under the phase_h directory.
- Refrain from editing C reference binaries; rely on existing `NB_C_BIN` artifacts.
- Maintain device/dtype neutrality if you touch simulator code — but today is evidence-only, so avoid implementation changes unless required for harness cleanup.
- Capture stderr (trace header lines) so future comparisons are reproducible.
- Keep attempts history synchronized: if the loop fails, log the failure in docs/fix_plan.md before moving on.
- Don’t delete `scaled.hkl.1` this loop; document it during plan closure when parity succeeds.
- Avoid switching to vectorization work mid-loop; Phase H evidence must land before plan hopping.
- Don’t drop the `AUTHORITATIVE_CMDS_DOC` env var — we need the command provenance recorded.
- Resist editing `reports/2025-10-cli-flags/phase_g/` artifacts; they remain the comparison baseline.
- If you need to tweak harness imports, preserve relative paths so the script works after repository moves.
- Do not commit without attaching artifacts; incomplete evidence breaks supervisor audit trails.

Pointers:
- plans/active/cli-noise-pix0/plan.md:96 — Phase H tasks and exit criteria.
- docs/fix_plan.md:448 — Next Actions + exit criteria for CLI-FLAGS-003.
- reports/2025-10-cli-flags/phase_g/trace_summary_orientation_fixed.md — reference reciprocal parity baseline.
- docs/development/c_to_pytorch_config_map.md — CUSTOM beam/pix0 rules.
- docs/debugging/debugging.md — Parallel trace SOP for logging format.
- docs/architecture/detector.md#L210 — CUSTOM convention geometry expectations.
- reports/2025-10-cli-flags/phase_e/trace_harness.py:108 — remove the manual incident beam override when cloning.
- specs/spec-a-cli.md — CLI semantics for -nonoise, -pix0_vector_mm, -beam_vector.
- docs/architecture/pytorch_design.md#vectorization-strategy — vectorization guardrails to keep in mind when adjusting lattice code later.
- reports/2025-10-cli-flags/phase_f/pix0_transform_refit.txt — reminder of current pix0 state used by Phase H.
- docs/architecture/c_parameter_dictionary.md — cross-check Na/Nb/Nc interpretation.
- reports/2025-10-cli-flags/phase_f/beam_vector_check.md — baseline for incident beam vectors after Phase F1.
- docs/development/testing_strategy.md#parallel-validation-matrix — artifacts expectations for trace comparisons.
- plans/active/vectorization.md:8 — context on future tricubic work; note we pause until CLI parity lands.

Reference Metrics:
- C `F_latt`: 35636.0822038919 (reports/2025-10-cli-flags/phase_g/traces/trace_c.log).
- PyTorch `F_latt` (current): 62.6805702411159 (reports/2025-10-cli-flags/phase_g/traces/trace_py_fixed.log).
- C `hkl_frac`: (2.0012033, 1.9927979, -12.9907669).
- PyTorch `hkl_frac` (current): (2.0979805, 2.0171122, -12.8706105).
- Peak intensities: C 446.254, PyTorch 3.56e-03 (polarization still 1.0 in PyTorch).
- Detector pix0: C -0.216475836, PyTorch -0.216336293 (0.14 mm delta yet to reconcile).
- Beam vector: both `[0.00051387949, 0.0, -0.99999986]` after Phase F1 fix.
- Oversample: both 1; mosaic domains currently 1.
- Keep these numbers in the Phase H summary to track improvements.

Reporting Checklist:
- [ ] Trace harness copy created under `reports/2025-10-cli-flags/phase_h/`.
- [ ] Manual beam override removed; comment noting rationale added.
- [ ] `trace_py.log`, `trace_py.stderr`, and `trace_diff.log` captured.
- [ ] `trace_comparison.md` summarizing key deltas committed.
- [ ] docs/fix_plan.md Attempts updated with Phase H1 details (metrics + artifact paths).
- [ ] commands.txt (or equivalent) listing executed commands stored beside trace artifacts.
- [ ] Any harness edits respect device/dtype neutrality (no `.item()`), confirmed via quick inspection.
- [ ] Supervisor note: record whether the harness runs faster/slower post-orientation for future perf context.

Next Up:
- 1) Phase H2 — Diagnose sincg/NaNbNc mismatch once trace evidence is logged.
- 2) Phase H3 — Parity rerun without polarization to validate lattice fix.
- 3) Optional stretch: prep a TODO list for polarization (Phase I) but do not implement yet.

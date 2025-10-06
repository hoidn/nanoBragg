Summary: Capture and archive a PyTorch pix0 trace that mirrors the C SAMPLE-pivot instrumentation so we can finally identify (or dispel) the Δpix0 gap blocking CLI parity. Include harness fixes, logging parity, and reproducibility metadata.
Phase: Evidence
Focus: CLI-FLAGS-003 — Phase H6b (PyTorch pix0 trace capture)
Branch: feature/spec-based-2
Mapped tests: none — evidence-only (do not run pytest; diffing comes later)
Background: The supervisor command uses custom detector vectors, forcing SAMPLE pivot in C (see reports/2025-10-cli-flags/phase_h6/c_trace/README.md). The current PyTorch harness still forces BEAM and appears to run against a stale site-package build when PYTHONPATH is omitted, which reproduces the 1.1 mm ΔF. We need a fresh TRACE_PY that (a) exercises SAMPLE pivot, (b) prints the same fields as TRACE_C, and (c) lives under reports/2025-10-cli-flags/phase_h6/ for future diffing.
Artifacts: reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log; reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.stderr; reports/2025-10-cli-flags/phase_h6/py_trace/env_snapshot.txt; reports/2025-10-cli-flags/phase_h6/py_trace/git_context.txt; reports/2025-10-cli-flags/phase_h5/parity_summary.md (append Attempt #36 follow-up note).
Deliverables: (1) Updated trace_harness.py committed with SAMPLE pivot and TRACE_PY instrumentation. (2) New PyTorch trace artifacts mirrored to the C log. (3) env/git context files proving reproducibility. (4) parity_summary.md updated to reference the new trace and capture immediate observations.
Do Now: CLI-FLAGS-003 – Phase H6b (PyTorch pix0 trace). Command: PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py > reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log 2> reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.stderr
If Blocked: If the harness imports a stale site-package build or throws ModuleNotFoundError, run PYTHONPATH=src python -c "import nanobrag_torch, pathlib; print('using', nanobrag_torch.__file__); print('cwd', pathlib.Path().resolve())" and stash the output plus the failing command under reports/2025-10-cli-flags/phase_h6/py_trace/attempts.md before pausing.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:130 — Phase H6 explicitly demands a PyTorch trace with identical structure to the C log; the table now calls out correcting the harness pivot, so this loop must deliver that.
  The Phase H6 exit criteria also mandate new artifacts under reports/2025-10-cli-flags/phase_h6/, which we currently lack on the PyTorch side.
- docs/fix_plan.md:521 — Attempt #35 shows ΔF ≈ -1.136 mm remains, blocking Phase K; without a parallel TRACE_PY we cannot tell whether the core implementation or the harness is responsible.
  Attempt #36 already captured the C instrumentation; pairing it with a PyTorch trace is the last missing evidence item before we resume normalization work.
- docs/fix_plan.md:547 — Next Actions now warn about stale site-packages and the BEAM hardcode; we must satisfy both guardrails (force PYTHONPATH=src and pivot=SAMPLE) when capturing the trace.
- reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0_clean.log:1 — Provides the canonical TRACE_C ordering and precision; mirroring these lines is the quickest path to a meaningful diff.
- docs/architecture/detector.md §“Pivot Calculations” — Documents the pix0 formulas for SAMPLE vs BEAM; use it to validate that the harness is exercising the Sample path before we diff.
- specs/spec-a-cli.md §3.3 — Clarifies that custom detector vectors imply SAMPLE pivot precedence even when -distance is present; the harness must reflect the same rule to stay spec-compliant.
- reports/2025-10-cli-flags/phase_h/pix0_reproduction.md — Recaps the target pixel (slow=1039, fast=685) and ROI context; reuse those coordinates so C and PyTorch traces remain comparable.
- docs/development/testing_strategy.md §2 — Parallel-trace SOP: every evidence run must capture env + git context alongside the logs and leave code changes minimal.
How-To Map:
1. Open reports/2025-10-cli-flags/phase_h/trace_harness.py (lines 96-120) and change DetectorConfig to honour the SAMPLE pivot.
  a. Remove the hard-coded DetectorPivot.BEAM; either derive the pivot from the CLI precedence or set DetectorPivot.SAMPLE explicitly.
  b. While editing, confirm the beam center assignments still map Xbeam→fast, Ybeam→slow (mosflm custom convention) and keep values in millimetres (DetectorConfig will handle conversion).
  c. Double-check that pix0_override_m remains in meters and matches the -pix0_vector_mm flag from the supervisor command (divide by 1000 once).
2. Instrument the harness so it prints TRACE_PY lines that match TRACE_C.
  a. Hook into Simulator/Detector to log detector_convention, angles, Fclose, Sclose, close_distance, ratio, distance, term_fast/slow/close, pix0_before_rotation, pix0_after_rotz, pix0_after_twotheta, and basis vectors after rotation.
  b. Use the same formatting as the C trace (e.g., f"TRACE_PY: term_fast_before_rot {x:.15g} {y:.15g} {z:.15g}").
  c. Keep dtype=torch.float64 and device=cpu in the harness so rounding aligns with the C trace.
  d. Ensure the harness prints exactly one TRACE_PY block per run to avoid polluting the diff; if additional debug prints are needed, send them to stderr with a clear prefix.
3. Ensure the harness imports the editable repo.
  a. Verify sys.path.insert(0, str(repo_root / 'src')) remains at the top.
  b. Avoid relative imports that might bypass the editable install; rely on nanobrag_torch.* modules under src/.
  c. Confirm no lingering references to site-packages (e.g., print nanobrag_torch.__file__ during debugging if needed) and remove any temporary prints before saving the log.
4. Execute the harness with the exact command:
  PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py \
    > reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.log \
    2> reports/2025-10-cli-flags/phase_h6/py_trace/trace_py_pix0.stderr
  a. Stdout should contain TRACE_PY lines only; stderr already logs "# Tracing pixel …".
  b. If the harness emits extra debug noise, filter it before saving or clearly annotate the log so diffing remains easy.
  c. Confirm the pix0 values reported align with the C trace to within a few microns; if they still differ by millimetres, revisit the pivot fix before proceeding.
5. Capture reproducibility context immediately after the run.
  a. env | sort > reports/2025-10-cli-flags/phase_h6/py_trace/env_snapshot.txt
  b. git rev-parse HEAD > reports/2025-10-cli-flags/phase_h6/py_trace/git_context.txt
  c. Optional: python -c "import torch, sys; print('torch', torch.__version__, 'python', sys.version)" >> env_snapshot.txt for library provenance.
  d. Record the exact command used (with arguments) in reports/2025-10-cli-flags/phase_h6/py_trace/README.md if that file exists; otherwise create it.
6. Update reports/2025-10-cli-flags/phase_h5/parity_summary.md (Attempt #36 section).
  a. Note that the PyTorch trace harness now uses SAMPLE pivot and cite the log path.
  b. Record any immediate observations (e.g., pix0 vector visually aligns with the C values, detailed diff pending Phase H6c).
  c. Mention the env/git snapshot files to make the evidence discoverable later.
7. Leave diff analysis for the next loop (Phase H6c).
  a. Do not run diff yet; first confirm both traces are structurally identical and committed to reports.
  b. Ensure no pytest, nb-compare, or large simulations are launched in this evidence loop.
  c. Flag in parity_summary.md that diffing is the next step so the plan stays aligned.
Harness Change Checklist:
- Remove DetectorPivot.BEAM hardcode and replace with DetectorPivot.SAMPLE or a derived pivot that respects CLI precedence.
- Ensure beam_center_f/s remain in mm when passed to DetectorConfig; do not convert to pixels upfront.
- Confirm pix0_override_m uses tuple values in meters (converted once from mm).
- Add TRACE_PY logging that mirrors TRACE_C (names, ordering, precision).
- Retain the existing target pixel (1039, 685) and configuration constants to maintain comparability with the C trace.
Verification Notes:
- Quick sanity check: after running the harness, load trace_py_pix0.log and confirm the first few lines read "TRACE_PY:detector_convention=CUSTOM" and "TRACE_PY:angles_rad=rotx:0 roty:0 rotz:0 twotheta:0".
- Compare the pix0 vector in the log against the C value (-0.216475836, 0.216343050, -0.230192414); the difference should be within a few microns (<5e-6 m).
- Validate that Fclose and Sclose lines roughly equal 0.217742295 and 0.213907080 respectively; large deviations suggest the pivot fix did not take.
- Ensure that the harness still traces the same pixel (slow=1039, fast=685); mismatched coordinates will nullify the diff.
Pitfalls To Avoid:
- Running without PYTHONPATH=src will hit the stale site-package build that still hardcodes DetectorPivot.BEAM.
- Forgetting to remove DetectorPivot.BEAM in the harness will reproduce the old 1.1 mm delta and waste the run.
- Do not modify golden_suite_generator/nanoBragg.c instrumentation; the C trace is already captured.
- Avoid running pytest or any CLI parity suite; Evidence phase forbids tests.
- Maintain TRACE_PY precision at ~15 significant digits so diff granularity matches TRACE_C.
- Keep output paths under reports/2025-10-cli-flags/phase_h6/py_trace/; do not overwrite earlier logs in phase_h/.
- Respect Protected Assets (docs/index.md list); do not move or rename referenced files.
- Ensure BeamConfig settings remain consistent (polarization_factor=1.0) to avoid introducing new divergences.
- Do not leave temporary floatimage outputs in the repo; discard or redirect them outside the workspace.
- Commit code changes only after supervisor review; this loop is evidence-gathering focused.
- Avoid mixing devices or dtypes in the harness; keep everything on CPU float64 for parity.
- Do not strip existing comments referencing earlier phases; they provide context for future loops.
Pointers:
- plans/active/cli-noise-pix0/plan.md:130 — Phase H6 guidance now emphasises fixing the harness pivot and capturing the new trace.
- docs/fix_plan.md:521 — Latest attempt history for CLI-FLAGS-003; use it when updating parity_summary.md.
- reports/2025-10-cli-flags/phase_h/trace_harness.py:1 — Harness to edit; note the existing comments referencing Phase H1.
- reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0_clean.log:1 — Clean C trace reference for field order.
- reports/2025-10-cli-flags/phase_h/trace_py_after_H3.log:1 — Previous PyTorch trace (BEAM pivot) for comparison; expect the new log to differ in Fclose/Sclose lines.
- docs/architecture/detector.md §“Pivot Calculations” — Mathematical reference for pix0 formulas.
- specs/spec-a-cli.md §3.3 — CLI precedence rules for pivots and custom detector vectors.
- docs/development/testing_strategy.md §2 — Evidence capture expectations (env/git context, diff-first workflow).
- reports/2025-10-cli-flags/phase_h/pix0_reproduction.md:1 — Historical notes on ROI and target pixel selection.
- reports/2025-10-cli-flags/phase_h6/c_trace/README.md:1 — Command and build context used for the C trace; the PyTorch harness should mirror these inputs where applicable.
- docs/architecture/pytorch_design.md §2.4 — Detector vectorisation overview; useful if additional instrumentation is needed later.
- docs/architecture/c_parameter_dictionary.md — Cross-reference for CLI flag semantics, handy when double-checking argument parsing.
Next Up (optional):
- Phase H6c — Diff TRACE_PY vs TRACE_C, document the first divergence in reports/2025-10-cli-flags/phase_h6/analysis.md, and update docs/fix_plan.md Attempt history accordingly.
- Phase K2 — Once pix0 parity is confirmed, rerun the scaling chain to regenerate reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log and refresh phase_j/scaling_chain.md.
Resources:
- docs/debugging/debugging.md §Parallel Trace Comparison — Workflow reminder for diffing once traces are captured.
- reports/2025-10-cli-flags/phase_h6/py_trace/ (directory) — Ensure it contains the new log, stderr, env snapshot, and git context before closing the loop.
- scripts/debug_pixel_trace.py — If additional instrumentation examples are needed, review how TRACE_PY lines are emitted there.
- golden_suite_generator/nanoBragg.c:1736-1907 — C reference for pix0 computation; compare against Detector._calculate_pix0_vector when validating.
- docs/development/c_to_pytorch_config_map.md — Parameter parity reference in case CLI mappings need double-checking while editing the harness.

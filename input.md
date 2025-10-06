Summary: Capture post-revert PyTorch traces so pix0/F_latt parity is documented before Phase K starts.
Phase: Evidence
Focus: CLI-FLAGS-003 / Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log; reports/2025-10-cli-flags/phase_h5/parity_summary.md; reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/diff_notes.md
Do Now: CLI-FLAGS-003 / Handle -nonoise and -pix0_vector_mm — PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log
If Blocked: Capture stdout/stderr plus traceback to reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/attempt_h5c_blocked.md, note device availability (`torch.cuda.is_available()`), active commit, and rerun guidance instead of improvising a fix.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:118 — H5c is the final gating task before Phase K; without the refreshed PyTorch trace we cannot prove pix0/Fbeam/Sbeam parity after Attempt #31.
  The plan explicitly requires storing TRACE_PY output under `phase_h5/py_traces/2025-10-22/` and updating parity_summary.md before normalization can resume.
- docs/fix_plan.md:507 — Next actions list H5c evidence first, followed by the lattice-factor correction; adhering keeps fix_plan chronology synchronized with plan execution.
  Logging Attempt #32 hinges on producing the trace and metrics this loop.
- reports/2025-10-cli-flags/phase_h5/parity_summary.md — Updated on 2025-10-22 to reflect the revert; it now contains explicit thresholds (<5e-5 m pix0, <1e-3 F_latt ratio) that must be populated with fresh numbers.
  Leaving the table empty blocks Phase K sign-off.
- specs/spec-a-core.md:217 — Canonical definition for the SQUARE lattice factor (sincg(π·h, Na)); today’s trace will help confirm PyTorch still feeds `(h - h0)` so we can justify the upcoming fix.
  Cross-referencing the spec while inspecting the log prevents accidental formula drift.
- golden_suite_generator/nanoBragg.c:3063 — C implementation of the same sincg calls; diffing TRACE_PY against TRACE_C requires pointing engineers to this snippet to understand the expected values.
  Maintaining this evidence loop is part of the parallel trace SOP.

Context Snapshot:
- Attempt #31 reverted the override logic and restored C precedence; Phase H5b/H5d are closed.
- The outstanding gap is purely evidentiary—the PyTorch trace needs to be recaptured to prove pix0, Fbeam/Sbeam, and h/k/l match the C baseline captured on 2025-10-22.
- Once that parity is confirmed, Phase K1 will modify the lattice-factor formula; having before/after logs prevents regressions and streamlines review.

How-To Map:
1. Prepare the workspace
   - `mkdir -p reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22`
   - Confirm the directory is empty or archive old scratch files to avoid mixing evidence.
2. Run the PyTorch trace harness exactly once (Evidence phase ⇒ no pytest):
   - `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log`
   - The harness prints progress to stdout; tee output into `trace_py.stdout` if you want quick reference, but keep logs inside the py_traces folder.
3. Generate comparison notes for parity_summary.md:
   - `python - <<'PY'` snippet suggestion: load both trace files, compute per-field deltas, and write them to `diff_notes.md`.
   - Highlight pix0 components, Fbeam/Sbeam, fractional h/k/l, each F_latt component, and the aggregate F_latt product.
4. Update documentation artifacts:
   - Append the metric table + command provenance to `reports/2025-10-cli-flags/phase_h5/parity_summary.md`.
   - Draft Attempt #32 summary (even if partial) so docs/fix_plan.md can record the outcome next loop.
5. Housekeeping commands before handoff:
   - `ls -R reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22` to verify only expected files exist.
   - `git status --short` to review staged/unstaged files.

Pitfalls To Avoid:
- Do not run pytest, nb-compare, or any CLI parity commands; Evidence phase forbids test execution.
- Leave C-side logs untouched; they are the reference for diffing and must not be edited or rewritten.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` in the environment; forgetting it causes MKL duplicate symbol crashes mid-run.
- Avoid `.cpu()` or `.item()` when post-processing tensors inside the harness; copy numbers using `.detach().clone()` if necessary.
- Record the exact command in parity_summary.md; undocumented commands break reproducibility.
- Do not modify Detector or Simulator code; today is evidence-only, not implementation.
- Respect Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md); no edits outside assigned files.
- Store new artifacts only inside the `reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/` directory to keep evidence tidy.
- No ad-hoc scripts in the repo root; reuse `reports/2025-10-cli-flags/phase_h/trace_harness.py` exclusively.
- Capture command failures verbatim in attempt_h5c_blocked.md if anything goes wrong; partial fixes without documentation force rework.

Pointers:
- plans/active/cli-noise-pix0/plan.md:159 — Phase K1 description you will unblock after recording today’s trace.
- docs/fix_plan.md:448 — CLI-FLAGS-003 ledger where Attempt #32 must be logged once metrics are computed.
- specs/spec-a-core.md:217 — Normative lattice-factor formula that the upcoming code change must follow.
- golden_suite_generator/nanoBragg.c:3063 — C sincg implementation for cross-checking TRACE_PY values.
- docs/development/testing_strategy.md:63 — Parallel trace SOP mandating trace comparison before implementation work.
- reports/2025-10-cli-flags/phase_h5/c_precedence_2025-10-22.md — Evidence baseline you must match when interpreting today’s logs.
- reports/2025-10-cli-flags/phase_j/scaling_chain.md — Prior scaling analysis showing the 3.6e-7 ratio; use it to verify improvements once Phase K begins.

Next Up:
- Begin Phase K1 (`plans/active/cli-noise-pix0/plan.md:159`) to replace `(h - h0)` with full-`h` sincg usage in Simulator once H5c metrics are published.

Trace Fields Checklist:
- pix0_vector (meters) — confirm Δ < 5e-5 m per component; document absolute and relative differences.
- Fbeam/Sbeam (meters) — expect ≈0.2179 m; record signed deltas for each axis.
- Fractional h/k/l — capture both rounded integers and residuals; highlight any deviation beyond 1e-6.
- F_latt components — list F_latt_a/b/c plus the product; contrast against C values (35636 baseline).
- I_before_scaling — optional sanity check to show improvement versus Phase J ratios.
- Polarization & omega — note values even if unchanged to provide complete trace context.

Evidence Logging Template (fill inside diff_notes.md):
```
Command:
  PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py --out reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22/trace_py.log

Metrics Summary:
  pix0 ΔS = _____ m, ΔF = _____ m, ΔO = _____ m
  Fbeam Δ = _____ m; Sbeam Δ = _____ m
  h/k/l residuals = (____, ____, ____)
  F_latt components: PyTorch (____, ____, ____), product = ____
  C reference: reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-22/trace_c_with_override.log

Notes:
  - …
```

Post-Run Review Steps:
- Validate that `trace_py.log` includes TRACE_PY headers for every variable listed above; rerun harness if truncated.
- Double-check timestamps on generated files to ensure they reflect the current loop (should match today’s date).
- Stage artifacts with `git add reports/2025-10-cli-flags/phase_h5/py_traces/2025-10-22` once satisfied; leave parity_summary.md unstaged until wording is final.
- Update Attempt history draft (docs/fix_plan.md) in a temporary note so the supervisor can promote it during the next review cycle.
- Snapshot `git diff --stat` for personal reference; attach to Attempt entry if anomalies appear.

Attempt Naming Guidance:
- Title new entry “Attempt #32 — Phase H5c PyTorch trace refresh” when drafting in docs/fix_plan.md.
- Include the command, timestamp, and a one-line verdict (e.g., “pix0 parity achieved / pending”).
- Reference both trace files explicitly so reviewers can reproduce the diff without guessing file paths.
- Note any unexpected deltas even if they fall within tolerance; these inform Phase K prioritisation.

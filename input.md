Summary: Align PyTorch `I_before_scaling` trace output with the C reference so Phase M scaling parity can move forward without false divergences.
Summary Detail: This loop is instrumentation-only—no physics edits—focused on making the trace harness compare apples-to-apples before returning to structure-factor parity work.
Summary Detail: Success criterion is a new trace/summary pair showing ≤1e-6 relative delta for `I_before_scaling_pre_polar` while preserving the existing post-polar field.
Summary Detail: Record all findings in docs/fix_plan.md Attempt log immediately after completion so the supervisory history stays linear.
Mode: Parity
Mode Detail: Treat every change through the lens of cross-implementation agreement; no new physics allowed until evidence proves traces line up.
Mode Detail: Evidence over execution—capture logs, metrics, and diffs so supervisor review can proceed without re-running commands.
Focus: CLI-FLAGS-003 — Phase M instrumentation parity (trace harness + simulator taps)
Focus Detail: Specifically target the I_before_scaling instrumentation described in plan tasks M1–M3; defer scaling bug fixes until trace output is trustworthy.
Branch: main (expected)
Branch Detail: Stay on the shared branch; do not create feature branches for this instrumentation tweak unless conflicts arise during commit.
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_phi0.py
Mapped tests Detail: Collection only this loop—full execution deferred until code paths change beyond instrumentation.
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<new_timestamp>/; reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T044933Z/galph_debug_20251203.md
Artifacts Detail: The new directory should include trace logs, harness stdout/stderr, summary.md, metrics.json, collect.log, commands.txt, and sha256.txt; keep the previous galph memo as a reference for before/after comparison.
Do Now: docs/fix_plan.md §CLI-FLAGS-003 Phase M — update the simulator trace so it emits both pre- and post-polarization `I_before_scaling`, then rerun the harness with `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --phi-mode c-parity --out reports/2025-10-cli-flags/phase_l/scaling_validation/<new_timestamp>/trace_py_scaling_cpu.log` followed by `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_validation/<new_timestamp>/trace_py_scaling_cpu.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/<new_timestamp>/summary.md --tolerance 1e-6`.
Do Now Detail: Ensure `<new_timestamp>` is unique (UTC ISO8601 without punctuation) and reuse the same value for all generated files so the evidence bundle remains coherent.
Do Now Detail: After the comparison, open `summary.md` to confirm both the pre-polar and post-polar metrics are recorded and note any residual delta in docs/fix_plan.md.
If Blocked:
- Create `reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/attempt_failed/` and dump all logs there (stdout, stderr, partial traces, compare output).
- Append a short README.md inside the folder summarizing the failure mode, commands executed, and suspected root cause.
- Update docs/fix_plan.md Attempt log (CLI-FLAGS-003) with the failure summary and the new artifact path so the supervisor has immediate context.
- Do not push partial code changes; wait for supervisor guidance once the failure package is prepared.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md Phase M1–M3 block on having a trustworthy trace; without this fix the entire scaling parity chain remains stalled.
- docs/fix_plan.md (CLI-FLAGS-003 entry) was amended this loop to highlight the polarization mismatch; acting immediately keeps plan text and reality aligned.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T044933Z/galph_debug_20251203.md contains quantified evidence (C value × polar); a new report should replace its provisional status with verified metrics.
- specs/spec-a-core.md §Sampling & Accumulation states that `I_term` is the pre-polarization sum, so parity comparisons must occur at that stage to respect the normative contract.
- Aligning trace taps prevents false positives and ensures subsequent debugging (F_cell, lattice factors, scaling) targets real physics gaps.
- Updating instrumentation now will make future nb-compare runs cleaner because `compare_scaling_traces.py` will no longer flag I_before errors.
- Resolving this also unblocks documentation updates in Phase M4 (summary + checklist) since the narrative will match collected data.
- The longer the mismatch persists, the greater the risk that additional attempts misinterpret the data and open unnecessary follow-up tasks.
How-To Map:
- Step 0 — Preparation:
  - Read `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T044933Z/galph_debug_20251203.md` so the numerical target (pre-polar value) is clear.
  - Confirm working tree is clean except for intentional edits; stash or document anything unrelated before proceeding.
- Step 1 — Simulator instrumentation:
  - Open `src/nanobrag_torch/simulator.py` and locate `_apply_debug_output`.
  - Identify the section where `I_total` is accepted and `TRACE_PY: I_before_scaling` is printed.
  - Before polarization multiplies the accumulator, insert a tensor clone (on the same device/dtype) and print it using the new label `TRACE_PY: I_before_scaling_pre_polar`.
  - Leave the existing logic in place but rename the current print statement to `TRACE_PY: I_before_scaling_post_polar` so post-factor data remains available.
  - Guard the new prints behind the existing trace conditions; avoid extra branching that could break torch.compile caching.
- Step 2 — Validation script alignment:
  - Review `scripts/validation/compare_scaling_traces.py`; update token parsing to recognise the `_pre_polar` label while keeping backward compatibility (if the label is absent, fall back to the post-polar value so older logs still work).
  - Extend the metrics dictionary so `summary.md` and any JSON output include both `pre_polar` and `post_polar` values, making it obvious which stage is compared.
- Step 3 — Harness update:
  - Modify `reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py` to capture both values:
    * Write both to the main log via the simulator trace (already handled after Step 1).
    * Append the new key/value pair to the per-φ JSON structure so future analyses can see which stage is recorded.
    * When dumping `metrics.json`, ensure the `I_before_scaling_pre_polar` value is stored separately from the post-polar number.
- Step 4 — Evidence directory setup:
  - Create a new directory named `reports/2025-10-cli-flags/phase_l/scaling_validation/$(date +%Y%m%dT%H%M%SZ)`.
  - Inside the directory, touch placeholder files: `commands.txt`, `summary.md`, `metrics.json`, `sha256.txt`, `harness_stdout.log`, `harness_stderr.log`, `collect.log`.
  - Document the intended contents at the top of `commands.txt` so the directory remains self-describing.
- Step 5 — Harness execution:
  - Run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --phi-mode c-parity --out <dir>/trace_py_scaling_cpu.log` with `<dir>` replaced by the new path.
  - Redirect stdout and stderr into `harness_stdout.log` and `harness_stderr.log` to capture warnings.
  - Verify the generated trace now contains both `TRACE_PY: I_before_scaling_pre_polar` and `TRACE_PY: I_before_scaling_post_polar` entries.
- Step 6 — Trace comparison:
  - Execute `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py <dir>/trace_py_scaling_cpu.log --out <dir>/summary.md --tolerance 1e-6`.
  - Inspect the resulting `summary.md` to confirm the pre-polar delta is ≤1e-6 relative; highlight both pre and post values in the markdown for clarity.
  - If the comparison emits auxiliary files (JSON, diff text), store them alongside the summary.
- Step 7 — Test discovery & documentation:
  - Run `pytest --collect-only -q tests/test_cli_scaling_phi0.py` and append the console output to `<dir>/collect.log`.
  - Update `commands.txt` with every command executed (in chronological order) including environment variables and working directories.
  - Record the current git SHA via `git rev-parse HEAD >> sha256.txt` (label the entry so it is distinguishable from file hashes).
- Step 8 — Checksums & wrap-up:
  - From inside `<dir>`, run `shasum -a 256 * > sha256.txt` (append mode) so each artifact is fingerprinted.
  - Re-open `summary.md` and add a brief note referencing the polarization adjustment and linking back to the older report for context.
  - Stage the new directory for commit once all manual inspections are complete.
Pitfalls To Avoid:
- Never overwrite `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T044933Z`; it remains a historical reference for Attempt #137.
- Avoid adding Python-side loops or branching that reintroduce per-φ iteration—vectorization must stay intact for performance and correctness.
- Keep all new trace labels prefixed with `TRACE_PY:` and use snake_case consistent with existing instrumentation.
- Do not coerce tensors to CPU just for printing; rely on `.item()` sparingly and only in non-differentiable debug paths.
- Maintain dtype/device neutrality by constructing helper tensors with `torch.as_tensor(..., device=existing.device, dtype=existing.dtype)`.
- Respect Protected Asset policy: confirm every file you touch is absent from `docs/index.md` before moving or renaming it.
- Limit test execution to the collect-only selector; running the full suite would violate supervisor guidance for this loop.
- Generate SHA256 checksums from within the new directory to avoid mixing hashes from previous attempts.
- Preserve CLI compatibility in `trace_harness.py`; new arguments must be optional and default to previous behaviour.
- Confirm `compare_scaling_traces.py` handles the new key before committing; add explicit assertion or warning if the pre-polar label is missing.
- Watch for interaction with torch.compile caching—if new tensors break graph capture, add explanatory comments per PERF plan guidelines.
- Keep code comments succinct but informative, referencing plan IDs where appropriate.
- Remember to update docs/fix_plan.md Attempt history after the run, citing the new artifact directory and summarising the pre/post polar deltas.
- Avoid committing directly from a dirty worktree; run `git status` frequently and stage only intentional files.
- Re-run the harness if the first pass accidentally uses an existing timestamp—each attempt must have its own directory for traceability.
Pointers:
- plans/active/cli-noise-pix0/plan.md — Phase M checklist plus artifact layout guidance.
- plans/active/cli-phi-parity-shim/plan.md — background on φ carryover (ensures no inadvertent regressions while touching traces).
- docs/fix_plan.md lines 445-520 — updated divergence note referencing the new galph debug memo.
- docs/bugs/verified_c_bugs.md §C-PARITY-001 — reminder that φ carryover is quarantined; instrumentation changes must keep dual-mode behaviour intact.
- specs/spec-a-core.md:190-270 — normative sampling order citing when polarization enters the chain.
- docs/development/testing_strategy.md §2 — expectations for trace-driven validation; follow when storing artifacts.
- scripts/validation/compare_scaling_traces.py — logic that must recognise new labels; read before editing.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py — harness to extend; comments explain required metadata.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T044933Z/trace_py_scaling_cpu.log — baseline trace to compare against once new values exist.
- tests/test_cli_scaling_phi0.py — eventual regression target after instrumentation parity is restored (collect-only now).
- arch.md §1 — notes on scaling factors and polarization pipeline for cross-checks.
Next Up: After pre-polar parity is green, proceed to plan tasks M2 (HKL lookup parity diagnostic) and M3 (regression run + metrics refresh), then transition to Phase N nb-compare ROI validation and finally the supervisor command rerun in Phase O.
Next Up Detail: When moving to M2, reuse the updated harness to capture per-φ F_cell/F_latt contributions so structure-factor mismatches can be isolated quickly.

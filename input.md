Summary: Tighten supervisor-command scaling parity by extending the scaling trace comparison to enforce sub-micro tolerances.
Mode: Parity
Focus: CLI-FLAGS-003 Phase L3e — scaling validation script update
Branch: feature/spec-based-2
Mapped tests:
- pytest --collect-only -q tests/test_cli_scaling.py
  - Confirms pytest discovers the CLI scaling suite after script edits.
- pytest tests/test_cli_scaling.py::TestHKLDevice::test_hkl_tensor_respects_device -vv
  - Runs CPU and GPU (skip-if unavailable) parametrisations to ensure HKL-device regression stays green.
- pytest tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c -vv
  - Optional confidence pass once metrics align, but only after updated script reports success.
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md
  - Markdown narrative describing per-factor deltas, first-divergence verdict, and next steps.
- reports/2025-10-cli-flags/phase_l/scaling_validation/metrics.json
  - Machine-readable thresholds (≤1e-6 relative) for each scaling factor compared.
- reports/2025-10-cli-flags/phase_l/scaling_validation/run_metadata.json
  - Captures git SHA, torch version, device availability, and command invocations for reproducibility.
Do Now: CLI-FLAGS-003 Phase L3e — extend compare_scaling_traces to emit ≤1e-6 parity metrics and run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md`
If Blocked: If traces look stale or missing factors, rerun `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --out reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log` and recapture the JSON/env snapshots before repeating the comparison.
Priorities & Rationale:
- docs/fix_plan.md:450-463 — Next actions promote L3e as the gate before parity reruns and specify required artifacts.
- plans/active/cli-noise-pix0/plan.md:252-264 — Phase L3 table defines deliverables, tolerance, and the scaling_validation directory for outputs.
- scripts/validation/compare_scaling_traces.py:1-210 — Current script emits markdown only; must grow structured output and enforce the tighter tolerance band.
- docs/development/testing_strategy.md:118-150 — Reinforces device/dtype neutrality expectations for parity diagnostics.
- specs/spec-a-cli.md:5-120 — CLI contract for scaling-sensitive flags; confirms the supervisor command’s parameter set.
- reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md — Existing markdown baseline whose structure should inform the upgraded summary.
How-To Map:
- Ensure editable install active (`pip install -e .` if needed) and export `KMP_DUPLICATE_LIB_OK=TRUE` before any torch-based command.
- After script edits, run `pytest --collect-only -q tests/test_cli_scaling.py` to verify collection, then execute `pytest tests/test_cli_scaling.py::TestHKLDevice::test_hkl_tensor_respects_device -vv` to ensure regression remains green.
- Generate parity metrics with `python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/scaling_validation_summary.md`.
- Extend the script so it also writes `metrics.json` (per-factor absolute/relative deltas) and `run_metadata.json` (env snapshot, command parameters) alongside the markdown.
- Summarize thresholds met, flag any ≥1e-6 deltas, and reference both artifacts when updating docs/fix_plan Attempt notes.
- If tolerances fail, annotate the markdown with failing factors and stop for supervisor review—do not patch simulator code in this loop.
- Cross-check the JSON metrics against the markdown table to confirm consistency before marking the attempt complete.
- Store command invocations (including environment variables) in run_metadata.json to aid reproducibility next loop.
- After artifacts exist, stage them plus script changes, but defer commits until supervisor review of results.
Pitfalls To Avoid:
- Do not modify simulator or production scaling code; this loop is evidence-only.
- Preserve device/dtype neutrality when parsing tensors; no hidden `.cpu()`/`.item()` calls.
- Keep Protected Assets intact (docs/index.md references, loop.sh, input.md).
- Avoid rerunning full parity suites; stay within targeted traces and pytest selectors.
- Ensure new artifacts live under `reports/2025-10-cli-flags/phase_l/scaling_validation/` with timestamps.
- Capture CUDA availability in run_metadata.json; note skips explicitly if GPU absent.
- Do not overwrite prior scaling audit logs—write new files or timestamped copies.
- Resist editing plan docs unless you discover new evidence gaps; supervisor will reconcile.
- Maintain the existing trace log filenames so downstream scripts keep working; only add new outputs.
- Do not relax tolerances below 1e-6 without supervisor approval; failing factors must be investigated instead.
Pointers:
- docs/fix_plan.md:460-470
- plans/active/cli-noise-pix0/plan.md:252-264
- scripts/validation/compare_scaling_traces.py:1-210
- reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md
- reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit.md:3-72
- docs/development/testing_strategy.md:118-150
- prompts/debug.md: entire file — Required SOP while executing parity evidence loops.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_env.json — Latest env snapshot to mirror in run_metadata.json.
Next Up: If scaling validation closes cleanly, proceed to Phase L3f documentation sync before scheduling the nb-compare rerun (L4).

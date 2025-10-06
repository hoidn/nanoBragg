Summary: Close CLI-FLAGS-003 Phase I by aligning polarization defaults and parity with nanoBragg.c.
Phase: Implementation
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm (Phase I polarization)
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_flags.py::TestCLIPolarization::test_default_polarization_parity | tests/test_at_parallel_011.py::TestATParallel011PolarizationFactor::test_polarized_kahn_model
Artifacts: reports/2025-10-cli-flags/phase_i/
Do Now: CLI-FLAGS-003 Phase I polarization — author targeted CLI polarization parity test, then run env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPolarization::test_default_polarization_parity -v
If Blocked: Capture evidence via KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_h/trace_harness.py --mode polarization --outdir reports/2025-10-cli-flags/phase_i/blocked && log findings in reports/2025-10-cli-flags/phase_i/blocked.md before paging supervisor.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:119 keeps Phase I (I1–I3) as the final blocker; follow each task sequentially.
  - Re-read Phase I goal statement to ensure the CLI command parity criteria are satisfied before closing the plan.
- plans/active/cli-noise-pix0/plan.md:108 summarises Phase H artifacts; reuse those traces as baseline when comparing polarization on/off.
  - The parity_after_lattice_fix summary proves geometry parity with -nopolar, which Phase I artifacts must extend.
- docs/fix_plan.md:448 records CLI-FLAGS-003 status now waiting for Attempt #26; evidence must update this ledger entry with polarization metrics.
  - Note the updated Next Actions already reference Phase I, so deliverables must target polarization.
- docs/fix_plan.md:859 highlights exit criteria with Phase H marked complete; only polarization and nb-compare remain unchecked.
  - Ensure Attempt #26 flips those ❌ entries to ✅.
- golden_suite_generator/nanoBragg.c:308 shows C defaults polar=1.0/polarization=0.0; mismatched PyTorch defaults explain the ~0.09 trace gap.
  - Keep this reference handy when writing Attempt #26 notes or commit message.
- golden_suite_generator/nanoBragg.c:3254-3290 documents polarization_factor; mirror its vector math when verifying tensor implementation.
  - Pay attention to E/B vector cross products and atan2 usage during parity checks.
- src/nanobrag_torch/config.py:483 currently sets polarization_factor=0.0; update to 1.0 and cite C default in the comment.
  - Reflect the change in tests so defaults remain covered.
- src/nanobrag_torch/simulator.py:485 constructs kahn_factor tensor; verify nopolar still zeroes it and dtype/device neutrality persists.
  - After edits, log resulting tensor dtype in phase_i/notes.md for audit.
- docs/architecture/pytorch_design.md:72 warns against device shims and `.item()`; keep those guardrails while editing polarization paths.
  - Mention compliance in Attempt #26 summary.
- docs/development/testing_strategy.md:1 (AUTHORITATIVE_CMDS_DOC) demands precise pytest selectors; cite it when summarising Do Now execution.
  - Update testing docs if new CLI polarization test becomes canonical.
- reports/2025-10-cli-flags/phase_e/trace_summary.md captures the current polarization mismatch (~0.9126 vs 1.0); use it as the 'before' metric.
  - Include numeric delta and path in phase_i/summary.md for contrast.
- reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/summary.md confirms pix0 parity with -nopolar; Phase I needs a similar summary with polarization enabled.
  - Keep naming consistent to simplify archiving.
How-To Map:
1. Export AUTHORITATIVE_CMDS_DOC=docs/development/testing_strategy.md in your shell; note the export in phase_i/notes.md for provenance.
2. Inspect nanoBragg defaults via `rg -n "polar=" golden_suite_generator/nanoBragg.c` and capture the snippet in reports/2025-10-cli-flags/phase_i/c_reference.txt.
   - Highlight lines assigning polar=1.0, polarization=0.0, nopolar=0 to justify PyTorch changes.
3. Update BeamConfig defaults in src/nanobrag_torch/config.py:480-500 to set polarization_factor=1.0 and document the rationale.
   - Ensure dataclass initialisation still respects explicit CLI overrides and programmatic configs.
4. Review CLI parsing in src/nanobrag_torch/__main__.py:240-320 so -polar/-nopolar flags map into config['polarization_factor']/nopolar.
   - Add assertions or a small unit test if gaps appear.
5. Audit simulator initialisation (src/nanobrag_torch/simulator.py:460-520) to confirm kahn_factor remains tensor-valued on detector.device/dtype.
   - Use `.to(self.device, self.dtype)` for any new constants and avoid `.item()`.
6. Cross-check polarization_factor helper at src/nanobrag_torch/utils/physics.py:183-236 with nanoBragg.c lines 3254-3290.
   - Document any deviations (e.g., numerical precision) in phase_i/analysis.md.
7. Create TestCLIPolarization in tests/test_cli_flags.py replicating the supervisor command arguments.
   - Use CLI harness to execute PyTorch with polarization on/off and assert trace values match C within 5e-5.
8. Run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_h/trace_harness.py --mode polarization --outdir reports/2025-10-cli-flags/phase_i/` to capture PyTorch trace.
   - Store outputs as trace_py.log plus trace_py.stderr; keep consistent naming.
9. Produce matching C trace via `timeout 180 NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/c_reference_runner.py --config prompts/supervisor_command.yaml --out reports/2025-10-cli-flags/phase_i/trace_c.log`.
   - Verify prompts/supervisor_command.yaml uses the exact CLI arguments (especially -polar/-nopolar state).
10. Diff traces with `PYTHONPATH=src python scripts/validation/diff_traces.py --c reports/2025-10-cli-flags/phase_i/trace_c.log --py reports/2025-10-cli-flags/phase_i/trace_py.log --out reports/2025-10-cli-flags/phase_i/trace_diff.log`.
    - Note polarization line deltas and confirm ≤5e-5 absolute difference.
11. Write reports/2025-10-cli-flags/phase_i/summary.md capturing defaults, trace deltas, pytest outputs, and residual risks.
    - Use tables for polarization values and correlation metrics to mirror earlier summaries.
12. Execute env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPolarization::test_default_polarization_parity -v once test exists.
    - Archive log as phase_i/pytest_cli_polar.log and reference it in fix_plan.
13. Run env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_parallel_011.py::TestATParallel011PolarizationFactor::test_polarized_kahn_model -v for broader coverage.
    - Save log as phase_i/pytest_parallel_011.log.
14. Update docs/fix_plan.md Attempt #26 with metrics (polarization delta, intensity ratio, correlation) and link to phase_i artifacts.
15. Mark plan tasks I1–I3 complete in plans/active/cli-noise-pix0/plan.md with references to new evidence.
    - Include artifact paths and note any follow-up (e.g., nb-compare once polarization passes).
Pitfalls To Avoid:
- Do not leave BeamConfig default at 0.0; matching nanoBragg's polar=1.0 baseline is required for parity.
- Avoid `.item()`, `.cpu()`, or `.detach()` when handling polarization tensors; keep gradients intact.
- Maintain device/dtype neutrality by creating tensors on detector.device/dtype (no hidden CPU allocations).
- Respect Protected Assets (docs/index.md); limit changes to targeted source/tests/reports.
- Skip full pytest; follow testing_strategy.md and run only targeted nodes plus evidence scripts.
- Ensure `-nopolar` still zeroes Kahn factor and produces identity polarization; add regression coverage if behavior shifts.
- Keep polarization_factor vectorized across pixels/sources; avoid Python loops that break performance.
- Preserve trace formatting (TRACE_C/TRACE_PY) so diff tools remain effective.
- Archive every artifact under reports/2025-10-cli-flags/phase_i/ with descriptive filenames (summary, traces, pytest logs, notes).
- Update plan and fix_plan immediately after evidence capture; stale metadata will confuse the next loop.
- Maintain MOSFLM vs CUSTOM offsets (±0.5 only for MOSFLM); polarization changes must not alter beam center conventions.
- Keep KMP_DUPLICATE_LIB_OK=TRUE set for all Python/pytest runs to prevent MKL conflicts.
- Retain temporary C traces until parity validated; they may be reused for regression analysis.
- Ensure new tests remain deterministic (set seeds if required) and reuse fixtures when possible.
Pointers:
- plans/active/cli-noise-pix0/plan.md:119 — Phase I task list (audit, implementation, parity).
- plans/active/cli-noise-pix0/plan.md:96 — Completed Phase H notes for comparison.
- docs/fix_plan.md:448 — CLI-FLAGS-003 ledger awaiting Attempt #26 entry.
- docs/fix_plan.md:859 — Exit criteria table showing remaining actions.
- golden_suite_generator/nanoBragg.c:308 — default polar/polarization values (1.0 / 0.0).
- golden_suite_generator/nanoBragg.c:3254 — polarization_factor helper for numeric parity.
- src/nanobrag_torch/config.py:483 — BeamConfig defaults to update.
- src/nanobrag_torch/simulator.py:485 — kahn_factor/polarization_axis tensor setup.
- src/nanobrag_torch/utils/physics.py:183 — vectorized polarization_factor implementation.
- src/nanobrag_torch/__main__.py:240 — CLI flag parsing for -polar/-nopolar.
- reports/2025-10-cli-flags/phase_e/trace_summary.md — polarization divergence baseline (~0.9126 vs 1.0).
- reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/summary.md — pix0 parity (-nopolar) summary to build upon.
- docs/development/testing_strategy.md:1 — authoritative pytest command source.
- docs/architecture/pytorch_design.md:72 — device/dtype guardrails to obey.
Next Up: 1) If polarization parity closes quickly, rerun nb-compare for the supervisor command with polarization enabled and store results under reports/2025-10-cli-flags/phase_i/nb_compare/; 2) Begin Phase A evidence capture for plans/active/vectorization.md (tricubic baselines) once CLI parity is signed off.
Validation Notes:
- When comparing traces, include both polarization factor and any downstream intensity scaling in summary tables.
- Capture a screenshot or textual snippet of the diff output highlighting the polarization line for Attempt #26.
- If polarization parity requires additional config tweaks (e.g., polarization axis), document the rationale in phase_i/analysis.md.
- Record whether the CLI emits the expected console log lines (`Polarization factor: ...`) to ensure user feedback remains accurate.
- After tests pass, run `git grep` to confirm no lingering references to the old 0.0 default remain.
- Note any follow-up work (e.g., documentation updates) directly in docs/fix_plan.md to keep the ledger current.
- Keep an eye on performance: if polarization changes alter runtime significantly, capture timings in phase_i/perf.md.

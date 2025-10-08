Summary: Align c-parity φ=0 carryover with nanoBragg.c so lattice factors and I_before_scaling hit the ≤1e-6 gate.
Mode: Parity
Focus: CLI-FLAGS-003 — Phase M2 Fix φ=0 carryover parity
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_phi0.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<new timestamp>/carryover_probe/
Do Now: CLI-FLAGS-003 — Phase M2 carryover parity fix; KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestScalingParity::test_I_before_scaling_matches_c
If Blocked: Capture spec vs c-parity traces for consecutive pixels (684/1039 → 685/1039) and log blocker details + deltas in docs/fix_plan.md Attempt history.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md M2 table — carryover parity is the remaining gate before scaling metrics can clear VG-2.
- docs/fix_plan.md#cli-flags-003-handle-nonoise-and-pix0_vector_mm — Next Actions now demand evidence of previous-pixel φ reuse plus the simulator fix.
- docs/bugs/verified_c_bugs.md:166-204 — C bug definition proves φ=0 must replay prior pixel vectors; PyTorch must emulate this in c-parity mode only.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md — New 2025-12-07 entry documents the current gap and required carryover probe.
- specs/spec-a-core.md:204-240 — Normative rotation pipeline (spec path) must remain untouched while parity mode gains the stateful bug emulation.
How-To Map:
- export PYTHONPATH=src; KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 684 1039 --phi-mode spec --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/carryover_probe/spec_pixel_684.log
- Repeat harness for pixel 685 1039 with --phi-mode spec and --phi-mode c-parity; store logs + commands.txt + env.json under the same <ts>/carryover_probe/ directory.
- Diff φ=0 rot_*_star and hkl_frac between spec and c-parity runs; summarise in carryover_probe/summary.md and append findings to lattice_hypotheses.md.
- Update simulator/crystal code so c-parity caches the previous pixel’s φ-final vectors (consult nanoBragg.c:3044-3095). Preserve spec mode behavior; keep tensors differentiable.
- Re-run harness for pixel 685 1039 (spec + c-parity) after the fix and verify deltas ≤1e-6 before running compare_scaling_traces.py.
- KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --py reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/trace_py_scaling.log --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --json reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/metrics.json --summary reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/scaling_validation_summary.md
Pitfalls To Avoid:
- Do not regress spec mode: guard the new cache behind phi_carryover_mode == "c-parity".
- Preserve vectorization; no Python loops per pixel or φ.
- Keep tensors on caller device/dtype; no .cpu() or .double() inside production paths.
- Maintain Protected Assets (loop.sh, supervisor.sh, input.md) untouched.
- Update docs/fix_plan.md Attempts with timestamp, command log, pytest selector, and git SHA.
- Add C-code references (nanoBragg.c line numbers) to any edited functions per CLAUDE Rule #11.
- Record SHA256 checksums in the new report directory before closing the loop.
- No full pytest suite; run only the targeted selector unless follow-up guidance changes.
- Avoid .item() on differentiable tensors in the carryover cache path.
Pointers:
- plans/active/cli-noise-pix0/plan.md (Phase M2 table, new M2d row)
- docs/fix_plan.md#cli-flags-003-handle-nonoise-and-pix0_vector_mm
- docs/bugs/verified_c_bugs.md:166-204
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md
- specs/spec-a-core.md:204-240
Next Up: After scaling parity is green, proceed to Phase M3 rerun of compare_scaling_traces.py (CPU + CUDA) before nb-compare.
Execution Steps:
1. Create reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/carryover_probe/ with commands.txt, env.json, and SHA skeleton.
2. Run trace_harness for pixel 684 (spec) and pixels 685 (spec & c-parity); save logs + taps.
3. Summarise φ=0 vector deltas in carryover_probe/summary.md and extend lattice_hypotheses.md with results.
4. Implement carryover cache in c-parity path (reuse previous pixel φ-final vectors); add nanoBragg.c citation.
5. Re-run trace_harness and compare_scaling_traces.py for pixel 685 (post-fix) to ensure first_divergence=None.
6. Execute pytest selector tests/test_cli_scaling_phi0.py::TestScalingParity::test_I_before_scaling_matches_c; archive pytest.log under the new timestamp.
7. Update docs/fix_plan.md Attempt entry with evidence, metrics.json summary, pytest selector, and git SHA; mark plan M2 rows accordingly.
8. Stage changes, run pre-commit lint if required, and prepare commit titled "CLI-FLAGS-003 Phase M2 carryover parity" once selector passes.
Validation Targets:
- |rot_b_star_phi0^Py − rot_b_star_phi0^C| ≤ 1e-6 for c-parity mode.
- |k_frac_phi0^Py − k_frac_phi0^C| ≤ 1e-6.
- |F_latt^Py − F_latt^C| / |F_latt^C| ≤ 1e-6.
- compare_scaling_traces metrics.json reports first_divergence: null.
- pytest selector passes on CPU; run CUDA variant only if code touched device-sensitive paths.
Documentation Updates After Fix:
- Append carryover summary to reports/.../<ts>/carryover_probe/summary.md (include nanoBragg.c references).
- Update lattice_hypotheses.md with resolution note + new artifact path.
- Refresh plans/active/cli-noise-pix0/plan.md (mark M2d, M2 row) and docs/fix_plan.md Attempt log with timestamp + metrics.
Notes:
- Keep the carryover cache stubbed behind simulator trace toggles if needed; ensure trace output still reflects the cached φ=final vectors.
Re-run Checklist Before Hand-off:
- commands.txt covers harness runs, compare_scaling_traces.py, pytest command (with env vars).
- sha256.txt lists trace logs, summary.md, metrics.json, pytest.log, env.json.
- git_status.txt stored in the report directory before commit.

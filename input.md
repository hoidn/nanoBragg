Summary: Capture fresh scaling-trace evidence for the supervisor command so we can root-cause the missing F_cell contribution at pixel (685,1039).
Mode: Parity
Focus: CLI-FLAGS-003 / Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling_cpu.log; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/metrics.json; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/summary.md
Do Now: export ts=$(date -u +%Y%m%dT%H%M%SZ) out=reports/2025-10-cli-flags/phase_l/scaling_validation/$ts && mkdir -p $out && KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --out $out/trace_py_scaling_cpu.log && KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py $out/trace_py_scaling_cpu.log --out $out/summary.md && mv scaling_metrics.json $out/metrics.json
If Blocked: If the harness fails due to missing HKL data, rerun with --dtype float64 and capture the full exception plus `ls reports/2025-10-cli-flags/phase_l/scaling_audit` in $out/blocked.log before escalating.
Priorities & Rationale:
- docs/fix_plan.md:451 reminds us the open gap is the zeroed F_cell during scaling, so the trace must expose that divergence.
- plans/active/cli-noise-pix0/plan.md:67 calls for a refreshed HKL lookup audit using the existing harness.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py documents the exact supervisor configuration we must reuse.
- scripts/validation/compare_scaling_traces.py enforces the ≤1e-6 tolerance that currently fails at `I_before_scaling`.
- specs/spec-a-core.md:211 keeps the φ rotation contract front-of-mind while interpreting lattice deltas.
How-To Map:
- `export ts=$(date -u +%Y%m%dT%H%M%SZ)` then `out=reports/2025-10-cli-flags/phase_l/scaling_validation/$ts` and `mkdir -p "$out"`.
- `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --device cpu --dtype float32 --out "$out"/trace_py_scaling_cpu.log`.
- `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py "$out"/trace_py_scaling_cpu.log --out "$out"/summary.md --tolerance 1e-6`.
- `mv scaling_metrics.json "$out"/metrics.json` (script currently drops metrics beside cwd).
- `sha256sum "$out"/* > "$out"/sha256.txt` and append command history to `$out/commands.txt`.
Pitfalls To Avoid:
- Do not edit production code yet; stay in evidence-gathering mode until the divergence is quantified.
- Keep PYTHONPATH=src so the harness imports the editable install rather than an older wheel.
- Avoid touching files listed in docs/index.md; reports live under the existing `phase_l` tree.
- Capture CPU evidence first; defer CUDA until we understand the scalar mismatch.
- Preserve device/dtype neutrality when summarising results—note dtype in summary.md.
- Do not delete or overwrite older artifacts; create a new timestamped directory.
Pointers:
- docs/fix_plan.md:451 — CLI-FLAGS-003 status and revised Next Actions.
- plans/active/cli-noise-pix0/plan.md:62 — Task block M1–M4 details.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1 — Harness entry point and arguments.
- scripts/validation/compare_scaling_traces.py:1 — Scaling comparison utility.
- specs/spec-a-core.md:204 — φ rotation pipeline expectations.
- docs/development/c_to_pytorch_config_map.md:16 — HKL flag mapping for parity debugging.
Next Up: 1) Re-run the harness on CUDA once CPU traces match; 2) Extend tests/test_cli_scaling_phi0.py with the new scaling-parity regression once the fix lands.

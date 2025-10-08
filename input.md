Summary: Fix the scaling comparison pipeline so Phase M1 evidence reliably captures the residual 0.21% lattice mismatch.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<new_timestamp>/{trace_py_scaling.log,summary.md,metrics.json,commands.txt,sha256.txt}
Do Now: [CLI-FLAGS-003] Phase M1 — repair `scripts/validation/compare_scaling_traces.py` so it processes the fresh c-parity trace, then run `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_validation/<new_timestamp>/trace_py_scaling.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/<new_timestamp>/scaling_validation_summary.md`
If Blocked: Capture the failing command’s stdout/stderr to `reports/2025-10-cli-flags/phase_l/scaling_validation/<new_timestamp>/compare_failure.log` and snapshot the trace heads; do not proceed until the script runs cleanly.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:53 keeps Phase M1 open until `I_before_scaling` matches within ≤1e-6; we now have 0.21% residual that must be closed.
- docs/fix_plan.md:510 logs the new Attempt #140 evidence but flags the comparison script crash as a blocker for Phase M2.
- specs/spec-a-core.md:211 mandates fresh φ rotations each step; verify c-parity results stay aligned with the documented C bug shim.
- docs/bugs/verified_c_bugs.md:166 reiterates why spec mode should diverge—use c-parity for the C comparison and keep the spec path untouched.
- scripts/validation/compare_scaling_traces.py coordinates downstream parity gates; without it we cannot prove VG-2.
How-To Map:
- `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_validation/<new_timestamp>/trace_py_scaling.log --config supervisor --device cpu --dtype float64 --phi-mode c-parity`
- After fixing the compare script, rerun it with the command in Do Now; expect `metrics.json` first_divergence to still be `I_before_scaling` until Phase M2 lands.
- Validate selectors only: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py --collect-only -q`.
- Store manual notes in `reports/2025-10-cli-flags/phase_l/scaling_validation/<new_timestamp>/analysis.md` if you need interim calculations.
Pitfalls To Avoid:
- Don’t touch spec-mode plumbing; parity work stays behind the `phi_carryover_mode` switch.
- Keep all tensors on the caller’s device/dtype—no stray `.cpu()` or `.item()` (see arch.md §15).
- Respect Protected Assets (docs/index.md): no moving `loop.sh`, `supervisor.sh`, or `input.md`.
- Avoid reusing the 20251008 timestamps; create a fresh directory per run.
- Do not skip SHA256 manifests; every artifact bundle needs hashes.
- No full pytest suites this loop; evidence-only.
- Preserve vectorization in any script edits—no new Python loops in trace extraction.
- Document any script fixes with the relevant nanoBragg.c line references per CLAUDE Rule #11.
- If you touch `compare_scaling_traces.py`, ensure pre- and post-polar handling still maps to `I_before_scaling` as per Attempt #139.
- Always set `PYTHONPATH=src` and `KMP_DUPLICATE_LIB_OK=TRUE` before running harnesses.
Pointers:
- plans/active/cli-noise-pix0/plan.md:46
- docs/fix_plan.md:509
- specs/spec-a-core.md:211
- docs/bugs/verified_c_bugs.md:166
- scripts/validation/compare_scaling_traces.py:1
Next Up: Once the script is stable and metrics hit ≤1e-6, move to Phase M2 lattice-factor fixes.

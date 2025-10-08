Summary: Capture a c-parity PyTorch trace so the rotated lattice vectors match C before rerunning scaling metrics.
Mode: Parity
Focus: CLI-FLAGS-003 / Handle -nonoise and -pix0_vector_mm (M2i.2)
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_c_parity.log; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/scaling_validation_summary.md; reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/{commands.txt,env.json,sha256.txt,trace_harness.stdout}
Do Now: CLI-FLAGS-003 / M2i.2 — KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 1039 685 --config supervisor --device cpu --dtype float64 --phi-mode c-parity --emit-rot-stars --out reports/2025-10-cli-flags/phase_l/scaling_validation/${timestamp}/trace_py_c_parity.log
If Blocked: Re-run the harness in spec mode (note this explicitly in commands.txt) and archive the evidence under an `_spec_probe` suffix so we can compare cache behavior in Attempts History.
Priorities & Rationale:
- specs/spec-a-core.md:204 — Canonical φ rotation pipeline; confirms spec mode must recompute ap/bp/cp each step while parity shim is strictly optional.
- docs/bugs/verified_c_bugs.md:166 — States the φ=0 carryover bug is C-only; PyTorch default must stay spec-compliant, so we prove bug emulation only via shim.
- plans/active/cli-noise-pix0/plan.md:28 — M2i.2 gate remains blocked pending a c-parity trace that aligns rotated vectors; our new memo is referenced there.
- docs/fix_plan.md:3810 — Attempt #173 captured the drift; the next attempt must supply matching rot_* vectors before metrics rerun.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T182512Z/rotated_lattice_divergence.md — Baseline numeric comparison showing Δh ≈ 0.102; your run should replace this with a parity-aligned result.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py — Harness already supports `--phi-mode c-parity`; use its CLI rather than ad-hoc scripts.
- CLAUDE.md / PyTorch guardrails — Device/dtype neutrality + vectorization must remain intact; keep the probe float64 CPU unless instructed otherwise.
How-To Map:
- export timestamp=$(date -u +%Y%m%dT%H%M%SZ); outdir=reports/2025-10-cli-flags/phase_l/scaling_validation/${timestamp}; mkdir -p "$outdir".
- tee "$outdir"/commands.txt with the exact commands you run (include timestamp export, harness invocation, compare script, pytest collect).
- Ensure PYTHONPATH=src (editable install contract) and run: KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 1039 685 --config supervisor --device cpu --dtype float64 --phi-mode c-parity --emit-rot-stars --out "$outdir"/trace_py_c_parity.log |& tee "$outdir"/trace_harness.stdout.
- Verify the harness logs `TRACE_PY_ROTSTAR` lines for all 10 φ steps; absence means the shim did not seed caches—capture this in observations if it happens.
- Reuse the canonical C trace: reports/2025-10-cli-flags/phase_j/trace_c_scaling.log. Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_j/trace_c_scaling.log --py "$outdir"/trace_py_c_parity.log --out "$outdir"/scaling_validation_summary.md` and append output to trace_harness.stdout.
- Capture pytest collect evidence: pytest --collect-only -q tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c | tee "$outdir"/pytest_collect.log (keeps test selector validated without running it).
- Record environment metadata via python - <<'PY' ... to emit git SHA, torch version, CUDA availability into "$outdir"/env.json (mirror prior attempt format) and compute sha256 sums for every artifact into "$outdir"/sha256.txt.
- Update docs/fix_plan.md Attempts with the new timestamp, key metrics (Δh, ΔF_latt, lattice ratio), and note whether parity matched; link to the new `scaling_validation_summary.md` and trace logs.
- If parity succeeds, rerun `compare_scaling_traces` with the old spec trace as control (optional) to demonstrate improvement; summarize findings inside the new summary.md so Phase N has clean prerequisites.
- Keep workspace clean (git status) and do not commit during evidence loops; log all deviations in commands.txt / Attempt entry.
Pitfalls To Avoid:
- Avoid touching simulator/crystal source files; today is diagnostics-only.
- Do not skip `--phi-mode c-parity`; running default spec mode will recreate the mismatch we just documented.
- Ensure harness tensors inherit the device/dtype (float64 CPU) — no `.to('cpu')` or `.float()` conversions mid-probe.
- Store artifacts under a unique timestamp directory; never overwrite `20251008T182512Z` or earlier bundles.
- Keep per-φ outputs enabled; we need to see cache substitution across phi_tic 0..9.
- No full pytest runs; stick to the collect-only selector outlined above.
- Respect Protected Assets listed in docs/index.md (loop.sh, supervisor.sh, input.md, etc.).
- Preserve trace format (TRACE_PY prefixes) so compare_scaling_traces.py parses successfully.
- Document any anomalies (missing shim log, unexpected tensor shapes) immediately in commands.txt and the Attempt entry.
- Do not push commits from this loop; this is an evidence capture step.
- Keep `env.json` and `sha256.txt` in sync with the artifact list for reproducibility.
- When editing docs/fix_plan.md, append to Attempts History under CLI-FLAGS-003 and mention the new timestamp explicitly.
Pointers:
- plans/active/cli-noise-pix0/plan.md:28 — M2i.2 gate + Next Actions ladder.
- docs/fix_plan.md:3810 — Attempt #173 divergence memo to supersede.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T182512Z/rotated_lattice_divergence.md — Reference baseline comparison before your rerun.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py:1-200 — Harness options and supervisor config wiring.
- specs/spec-a-core.md:204-244 — Normative lattice computation, sincg definitions, φ rotation pipeline.
- docs/bugs/verified_c_bugs.md:166-213 — C-PARITY-001 classification; reminds us spec remains clean.
- reports/2025-10-cli-flags/phase_j/scaling_chain.md — Shows first divergence at `I_before_scaling`; confirm this clears after shim trace.
- CLAUDE.md: PyTorch Runtime Guardrails §PyTorch Runtime Checklist — obey device/vectorization requirements while collecting traces.
- input.md (this file) — follow instructions verbatim; log deviations in commands.txt.
Next Up:
1. When the c-parity trace reproduces C rotated vectors, re-run scripts/validation/compare_scaling_traces.py to refresh M2i.2 metrics and note VG-2 status in fix_plan.
2. With VG-2 green, prep Phase N nb-compare harness (CPU first, CUDA optional) so the supervisor parity command can finally be executed end-to-end.

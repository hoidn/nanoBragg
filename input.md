Summary: Chase the 0.21% supervisor scaling delta by drilling into the lattice/interpolation path before Phase M2.
Mode: Parity
Focus: CLI-FLAGS-003 Phase M1 — Audit HKL lookup parity
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py --collect-only -q
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T060721Z/ (trace_py_scaling.log, trace_py_scaling_per_phi.{log,json}, manual_summary.md, manual_metrics.json, commands.txt, sha256.txt, trace_py_env.json, config_snapshot.json)
Do Now: CLI-FLAGS-003 Phase M1 — run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_validation/<new_ts>/trace_py_scaling.log --config supervisor --device cpu --dtype float64 --phi-mode c-parity` and extend the harness to emit the 4×4×4 tricubic weight grid so the new manual_summary captures the exact F_latt drift vs C.
If Blocked: Document the failure in attempts history, stash logs under reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/attempts_blocked.md, and fall back to regenerating the raw harness traces for confirmation.
Priorities & Rationale:
- specs/spec-a-core.md:211 — φ rotation should not mutate the base vectors, so the ∼1e-5 h-drift means interpolation/reciprocal regeneration is still misaligned.
- docs/bugs/verified_c_bugs.md:166 — C-parity shim exists only to mirror the bug; spec mode must stay clean while we chase the c-parity delta.
- plans/active/cli-noise-pix0/plan.md:53 — Phase M1 requires concrete HKL/f_latt evidence; new 20251008T060721Z artifacts quantify the gap we must close.
- docs/fix_plan.md:518 — Attempt #141 logs F_latt_a/b/c discrepancies and the persistent compare_scaling_traces.py SIGKILL; closing Phase M1 depends on addressing both.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T060721Z/manual_summary.md — Shows lattice factors off by ∼0.13%, directly feeding the 0.21% intensity drop.
How-To Map:
- Reproduce PyTorch trace: `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>/trace_py_scaling.log --config supervisor --device cpu --dtype float64 --phi-mode c-parity`.
- C reference: reuse `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log` (no rerun needed).
- After instrumentation, regenerate manual summary via `python - <<'PY' ...` (see commands.txt template) so metrics land beside the trace.
- Fix compare script: replicate failing command from commands.txt, debug `scripts/validation/compare_scaling_traces.py`, and ensure it emits metrics.json + summary.md without manual intervention.
Pitfalls To Avoid:
- Do not edit production code without adding the mandated C-code docstring excerpts (CLAUDE Rule #11).
- Keep new instrumentation batched; no per-pixel Python loops when exposing tricubic weights.
- Preserve device/dtype neutrality — avoid hard-coded `.cpu()` or float conversions when logging weights.
- Respect Protected Assets: leave docs/index.md references intact when touching reports or plans.
- Capture new evidence in fresh timestamped directories; never overwrite prior artifacts.
- Update attempts history and plan tables once evidence exists; unlogged work is considered incomplete.
- Keep compare_scaling_traces.py fix minimal — no speculative refactors while debugging the crash.
- When touching manual summaries, stick to ASCII and mirror the existing table schema for downstream tooling.
Pointers:
- docs/fix_plan.md:510 — Current Attempt #141 details and next steps for Phase M1.
- plans/active/cli-noise-pix0/plan.md:46 — Phase M overview and evidence expectations.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py — Existing harness ready for extension.
- scripts/validation/compare_scaling_traces.py — Needs stabilization before automation resumes.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T060721Z/manual_summary.md — Latest measured deltas to beat.
Next Up: Phase M1 → instrument `_tricubic_interpolation` internals, then progress to Phase M2 once F_latt parity closes.

Summary: Capture per-φ Miller index + lattice traces (C vs PyTorch) so we can nail the φ-grid mismatch before touching normalization.
Phase: Implementation
Focus: CLI-FLAGS-003 — Phase K3e per-φ Miller index parity
Branch: main
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/
Do Now: CLI-FLAGS-003 K3e per-φ parity; PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_k/f_latt_fix/analyze_scaling.py --per-phi --outdir reports/2025-10-cli-flags/phase_k/f_latt_fix/per_phi/
If Blocked: If the script lacks `--per-phi`, scaffold it first; if C trace instrumentation fails to build, save the compile error to per_phi/attempt_failed.log and fall back to copying Attempt #43 trace with manual φ annotations.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:176 — K3e mandates a per-φ dump before any further normalization work.
- docs/fix_plan.md:451 — Next Actions now pivot on resolving the φ-grid mismatch (k≈1.9997 vs 1.9928).
- reports/2025-10-cli-flags/phase_k/f_latt_fix/trace_py_after.log — Current log only shows φ₀; we need the full 0…9 sweep.
- reports/2025-10-cli-flags/phase_j/trace_c_scaling.log — Baseline C trace to mirror when instrumenting φ ticks.
- specs/spec-a-core.md §4.3 — Sincg sensitivity confirms why Δk≈7e-3 blows up F_latt_b, so evidence must quantify k per φ.
How-To Map:
- Extend `reports/…/analyze_scaling.py` to accept `--per-phi` and emit JSON/markdown tables of `φ_tic`, `h`, `k`, `l`, `F_latt_{a,b,c}` for both C and PyTorch; store files under the timestamped folder inside per_phi/.
- Patch `golden_suite_generator/nanoBragg.c` instrumentation (copy Attempt #43 scaffolding) to log `TRACE_C_PHI φ_tic=<idx> k=<val> F_latt_b=<val>`; rebuild via `make -C golden_suite_generator`.
- Run the PyTorch side command (above) with `NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg` so the script can invoke C and PyTorch back-to-back.
- Capture stdout/stderr to `per_phi/<timestamp>/run.log`, and drop a summary markdown (`per_phi_summary.md`) with the first φ where Δk > 5e-4.
- Leave the dtype sweep artifacts untouched; reference them when summarising findings.
Pitfalls To Avoid:
- Do not regress existing scaling artifacts—create a fresh timestamped subdir.
- No pytest in this loop; focus on traces.
- Keep edits confined to the script + instrumentation; core simulator code stays untouched until φ mismatch is proven.
- Respect Protected Assets (docs/index.md listings).
- Clean rebuild the C binary after instrumentation to avoid stale traces.
- Ensure command runs with `KMP_DUPLICATE_LIB_OK=TRUE` to prevent MKL clashes.
- Document commit hash + torch version in the summary for reproducibility.
- Avoid hard-coded `.cpu()`/`.cuda()` in new logging helpers.
- Don’t push; hand back evidence first.
Pointers:
- plans/active/cli-noise-pix0/plan.md:180
- docs/fix_plan.md:451
- reports/2025-10-cli-flags/phase_k/f_latt_fix/analyze_scaling.py
- reports/2025-10-cli-flags/phase_j/trace_c_scaling.log
- src/nanobrag_torch/models/crystal.py:828
- golden_suite_generator/nanoBragg.c:3038
- specs/spec-a-core.md §4.3
Next Up:
1. After per-φ evidence, implement φ sampling fix (K3f) and rerun scaling-chain validation.
2. Once F_latt parity holds, close K3c with targeted pytest + doc refresh before attempting Phase L.

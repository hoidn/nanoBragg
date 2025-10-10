Summary: Capture Phase C3 first-divergence evidence for the 4096² parity regression.
Mode: Parity
Focus: docs/fix_plan.md#[VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_c/$STAMP/{commands.txt,env/trace_env.json,first_divergence.md,diff_pixel_*.txt,summary.md}
Do Now: `[VECTOR-PARITY-001] Restore 4096² benchmark parity` — build Phase C3 `first_divergence.md` by comparing the existing C/Py trace logs and documenting the earliest mismatch per pixel (use `compare_c_python_traces.py`).
If Blocked: If the comparison script fails (e.g., schema mismatch), fall back to manual `diff -u` for each pixel, capture the raw diff under the same reports/ directory, and log the issue plus mitigation in Attempt History.
Priorities & Rationale:
- plans/active/vectorization.md — Phase C requires `first_divergence.md` before profiling can resume.
- docs/fix_plan.md#[VECTOR-PARITY-001] — Next Actions call for Phase C3 trace analysis before any further work.
- reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/ — authoritative C logs for pixels (2048,2048), (1792,2048), (4095,2048).
- reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/py_traces/ — matching PyTorch logs that must be compared.
- compare_c_python_traces.py — in-repo utility to automate tap-by-tap diffing with tolerance control.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`
- `mkdir -p reports/2026-01-vectorization-parity/phase_c/$STAMP/env`
- `python compare_c_python_traces.py --c-trace reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_2048_2048.log --py-trace reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/py_traces/pixel_2048_2048.log --tolerance 1e-12 > reports/2026-01-vectorization-parity/phase_c/$STAMP/diff_pixel_2048_2048.txt`
- Repeat the compare command for `pixel_1792_2048` and `pixel_4095_2048` (update output filenames accordingly).
- `python - <<'PY'` block to write `reports/2026-01-vectorization-parity/phase_c/$STAMP/env/trace_env.json` capturing git SHA, branch, python version, tolerance used, and the three pixel filenames.
- `printf` the executed commands into `reports/2026-01-vectorization-parity/phase_c/$STAMP/commands.txt` (one per line).
- Author `reports/2026-01-vectorization-parity/phase_c/$STAMP/first_divergence.md` summarising for each pixel: first mismatched tap (variable name + line numbers), numeric values (C vs Py), %/absolute delta, suspected unit mismatch, and next-step recommendation.
- Add a concise roll-up (`summary.md`) noting whether any divergences are common across pixels and whether fluence / structure factor differences explain the parity gap.
Pitfalls To Avoid:
- Do not modify C or Python trace generators; use existing logs only.
- Keep `STAMP` unique per loop; do not reuse `unknown/` folders.
- Ensure tolerance is ≤1e-12; higher tolerances can mask true divergences.
- Note units explicitly in `first_divergence.md` (m, Å, Å⁻¹) to avoid mixing conventions.
- Capture every command in `commands.txt`; missing provenance blocks future audits.
- Do not delete or move the legacy trace bundles referenced in fix_plan.
- Avoid editing production code or committing new scripts; this loop is evidence-only.
- Maintain device/dtype neutrality when interpreting diffs (PyTorch traces should remain float64 CPU).
- If results are inconclusive, stop and document rather than guessing.
- Keep report files ASCII; no spreadsheets or binary artifacts.
Pointers:
- plans/active/vectorization-parity-regression.md — Phase C tables describe expected artifacts for trace analysis.
- plans/active/vectorization.md — Phase C gate now depends on this divergence report.
- docs/development/testing_strategy.md#14-pytorch-device--dtype-discipline — reminder to state device/dtype in reports.
- reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/summary.md — prior C-trace attempt context.
- reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/PHASE_C2_SUMMARY.md — Py trace notes including fluence discrepancy to revisit.
Next Up: If time remains after authoring `first_divergence.md`, draft bullet hypotheses for parity root cause to accelerate supervisor review.

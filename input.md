Summary: Implement Phase D1 scattering-vector unit fix and capture proof that the PyTorch trace now matches the C log.
Mode: Parity
Focus: docs/fix_plan.md#[VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_d/$STAMP/{commands.txt,env/trace_env.json,py_traces_post_fix/,diff_scattering_vec.md,diff_scattering_vec.txt,phase_d_summary.md}
Do Now: `[VECTOR-PARITY-001] Phase D1` — update the PyTorch scattering-vector computation so `scattering_vec_A_inv` is emitted in m^-1, then run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 1792 2048 --tag post_fix_scattering --out-dir reports/2026-01-vectorization-parity/phase_d/$STAMP/py_traces_post_fix` to capture the post-fix trace.
If Blocked: If the trace script fails (schema/arg regressions), revert the last code edit, note the failure in Attempt History, and capture the stderr output under `reports/2026-01-vectorization-parity/phase_d/$STAMP/attempt_failure.log` before stopping.
Priorities & Rationale:
- plans/active/vectorization-parity-regression.md:60 — Phase D1 requires the m^-1 unit fix plus fresh trace evidence before moving to fluence.
- docs/fix_plan.md:48 — Next Actions explicitly gate progress on the scattering-vector correction with ≤1e-6 relative parity.
- specs/spec-a-core.md:446 — Normative unit definition for `q` (scattering vector) equals m^-1; PyTorch must align with this and the C trace.
- reports/2026-01-vectorization-parity/phase_c/20251010T061605Z/first_divergence.md — Documents the 10^7 mismatch and sets the acceptance metric you must close.
- scripts/debug_pixel_trace.py (usage block near top) — Existing CLI that already mirrors the TRACE_C tap schema; reuse it for parity confirmation.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` (use a fresh stamp) and `mkdir -p reports/2026-01-vectorization-parity/phase_d/$STAMP/{env,py_traces_post_fix}`.
- Edit the scattering-vector path (expected in `src/nanobrag_torch/simulator.py` or `src/nanobrag_torch/utils/physics.py`) so wavelength/geometry units yield m^-1; keep vectorization and differentiability intact.
- Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 1792 2048 --tag post_fix_scattering --out-dir reports/2026-01-vectorization-parity/phase_d/$STAMP/py_traces_post_fix`.
- Compare against the C trace: `python compare_c_python_traces.py --c-trace reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log --py-trace reports/2026-01-vectorization-parity/phase_d/$STAMP/py_traces_post_fix/pixel_1792_2048.log --tolerance 1e-6 > reports/2026-01-vectorization-parity/phase_d/$STAMP/diff_scattering_vec.txt`.
- Summarise the key before/after numbers (scattering_vec components + relative deltas) in `reports/2026-01-vectorization-parity/phase_d/$STAMP/diff_scattering_vec.md`; include table + commentary that tolerances are met.
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` to ensure no module import regressions after the code edit.
- Capture `git rev-parse HEAD`, Python/PyTorch versions, and command list into `env/trace_env.json` and `commands.txt` inside the same STAMP directory.
- Append a brief Attempt note to docs/fix_plan.md under `[VECTOR-PARITY-001]` summarising what changed, artifact paths, and measured error.
Pitfalls To Avoid:
- Do not change the TRACE_C logs or overwrite existing Phase C artifacts.
- Maintain device/dtype neutrality; the fix must work identically on CPU/GPU without `.cpu()`/`.cuda()` shims.
- Keep the scattering-vector math fully vectorized; no Python loops or `.item()` extractions.
- Avoid touching fluence or F_latt yet; keep Phase D2/D3 scoped for follow-up loops.
- Ensure the new units propagate consistently (no mixed Å^-1 vs m^-1 intermediates) and document conversions in comments only if clarifying.
- Record every command in `commands.txt`; missing provenance blocks reproducibility.
- Do not downgrade tolerances—comparison uses 1e-6 relative; raise an issue if that cannot be met.
- Preserve ASCII output formatting for all new artifacts.
- Re-run `pytest --collect-only` after edits even if the trace succeeds; this guards against accidental import regressions.
- Stage only intentional code/doc changes; avoid sweeping formatter diffs.
Pointers:
- plans/active/vectorization-parity-regression.md:60 — Detailed acceptance criteria for Phase D1 artifacts.
- docs/fix_plan.md:48 — Supervisor ledger expectations for D1 evidence.
- specs/spec-a-core.md:446 — Canonical definition of scattering-vector units.
- arch.md:36 — Architecture unit system summary that must remain consistent post-fix.
- reports/2026-01-vectorization-parity/phase_c/20251010T055346Z/py_traces/pixel_1792_2048.log — Pre-fix PyTorch baseline for diffing.
Next Up: Phase D2 — fix fluence scaling once the scattering-vector parity diff lands.

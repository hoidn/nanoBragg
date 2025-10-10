Summary: Align TRACE_PY fluence with C by reusing the spec-computed `BeamConfig.fluence` and refreshing the Phase D2 evidence bundle.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_d/$STAMP/
Do Now: [VECTOR-PARITY-001] Phase D2 – Update `scripts/debug_pixel_trace.py` to emit `beam_config.fluence` (and not recompute from flux), then run `STAMP=$(date -u +%Y%m%dT%H%M%SZ) KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 1792 2048 --tag fluence_post_fix --out-dir reports/2026-01-vectorization-parity/phase_d/$STAMP/py_traces_post_fix/` and record the comparison in `reports/2026-01-vectorization-parity/phase_d/$STAMP/fluence_parity.md`.
If Blocked: Capture existing Py trace into `reports/2026-01-vectorization-parity/phase_d/blocked/` with notes on the blocker and stop; flag in Attempts History.
Priorities & Rationale:
- plans/active/vectorization-parity-regression.md:61 — Phase D2 calls for fluence parity verification before Phase D3.
- docs/fix_plan.md:34 — Latest observations list H2 as the next open issue with Trace helper divergence.
- specs/spec-a-core.md:517 — Canonical fluence equation linking flux, exposure, and beamsize.
- golden_suite_generator/nanoBragg.c:1150 — C implementation of the same formula (square beam, meters).
- reports/2026-01-vectorization-parity/phase_d/fluence_gap_analysis.md — Supervisor evidence showing the 9.89e+08 mismatch and root cause (trace helper re-deriving flux).
How-To Map:
- Code edit: Modify `scripts/debug_pixel_trace.py:360-390` so the TRACE_PY line reads the already prepared `beam_config.fluence` (or `simulator.fluence.item()`), keeping dtype/device neutrality.
- Reproduce: `STAMP=$(date -u +%Y%m%dT%H%M%SZ) KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 1792 2048 --tag fluence_post_fix --out-dir reports/2026-01-vectorization-parity/phase_d/$STAMP/py_traces_post_fix/`.
- Analysis: Compare the new `TRACE_PY: fluence_photons_per_m2` against `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log`; document numeric deltas and relative error ≤1e-3 inside `reports/2026-01-vectorization-parity/phase_d/$STAMP/fluence_parity.md`.
- Sanity: `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` once after edits; drop log under the same `$STAMP` directory.
- Recording: Update Attempts History with the new stamp, linking `fluence_parity.md` once supervisor review completes.
Pitfalls To Avoid:
- Do not reintroduce Å↔m mix-ups; keep scattering vector fix intact.
- Avoid recomputing fluence from flux inside simulator paths; reuse the dataclass field.
- No `.item()` on tensors that require gradients outside trace-only code.
- Maintain device/dtype neutrality in the helper (respect `--dtype`, `--device`).
- Keep `STAMP` exported before writing artifacts to avoid `phase_d/unknown/` folders.
- Do not commit large trace logs; reference paths instead.
- Respect Protected Assets listed in `docs/index.md`.
- Retain vectorization; no per-pixel Python loops added.
- Run commands with `KMP_DUPLICATE_LIB_OK=TRUE` set.
- Leave scattering-vector verification artifacts untouched unless the fluence change requires a re-run.
Pointers:
- specs/spec-a-core.md:517
- golden_suite_generator/nanoBragg.c:1150
- scripts/debug_pixel_trace.py:360
- reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log
- reports/2026-01-vectorization-parity/phase_d/fluence_gap_analysis.md
Next Up: Phase D3 – Restore F_latt normalisation once fluence parity evidence lands.

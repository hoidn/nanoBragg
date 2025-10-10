Summary: Bring PyTorch fluence math back into parity with C for the 4096² benchmark (Phase D2).
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_d/$STAMP/
Do Now: [VECTOR-PARITY-001] Phase D2 – Fix fluence scaling; after editing, run `STAMP=\$(date -u +%Y%m%dT%H%M%SZ) KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 1792 2048 --out-dir reports/2026-01-vectorization-parity/phase_d/\$STAMP/py_traces_post_fix/` and write `reports/2026-01-vectorization-parity/phase_d/\$STAMP/fluence_parity.md` summarising C vs PyTorch values.
If Blocked: Capture current Py trace output into `reports/2026-01-vectorization-parity/phase_d/blocked/` with notes on the blocker, then halt and flag in Attempts History.
Priorities & Rationale:
- plans/active/vectorization-parity-regression.md:61 – Phase D2 spells out the required fluence audit + trace parity target.
- docs/fix_plan.md:30 – Attempt #10/11 synopsis lists fluence as the next root cause to remediate.
- specs/spec-a-core.md:516 – Normative fluence equation (flux·exposure / beamsize²) to enforce.
- arch.md:69 – ADR-01 reminds us how unit conversions split between meters and Å for physics.
- reports/2026-01-vectorization-parity/phase_c/20251010T061605Z/first_divergence.md – Quantifies the 10⁹× fluence gap you must eliminate.
How-To Map:
- Code: Work in `src/nanobrag_torch/simulator.py` (respect vectorization; no new Python loops).
- Reproduce: After changes, set `STAMP=\$(date -u +%Y%m%dT%H%M%SZ)` and run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 1792 2048 --out-dir reports/2026-01-vectorization-parity/phase_d/\$STAMP/py_traces_post_fix/`.
- Analysis: Compare `TRACE_PY` fluence entries against existing `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log`; record deltas in `fluence_parity.md` (include relative error ≤1e-3 target).
- Sanity: Re-run `pytest --collect-only -q` once to ensure imports stay intact and log stdout under the same stamp directory.
- Recording: Update `docs/fix_plan.md` Attempts with the new stamp and fluence metrics after supervisor review.
Pitfalls To Avoid:
- Do not downcast to float64; keep device/dtype neutrality per docs/development/testing_strategy.md#14.
- No `.item()` or `.detach()` on tensors that should retain gradients.
- Keep vectorization intact; avoid introducing per-pixel Python loops or branching on scalar tensors.
- Always set `KMP_DUPLICATE_LIB_OK=TRUE` when invoking PyTorch scripts.
- Do not commit large trace logs; reference paths in attempts instead.
- Ensure `STAMP` is exported before writing artifacts (no `phase_d/unknown/`).
- Leave existing scattering-vector fix untouched; focus on fluence-only changes.
- Re-run `pytest --collect-only -q` after editing to catch import regressions.
- Respect Protected Assets listed in docs/index.md.
- Document any assumption about beamsize/flux precedence inside `fluence_parity.md`.
Pointers:
- plans/active/vectorization-parity-regression.md:61
- docs/fix_plan.md:36
- specs/spec-a-core.md:516
- arch.md:69
- reports/2026-01-vectorization-parity/phase_c/20251010T061605Z/first_divergence.md
Next Up: Phase D3 – Restore F_latt normalisation once fluence matches within tolerance.

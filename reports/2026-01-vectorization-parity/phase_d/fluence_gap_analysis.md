# Fluence Discrepancy Notes (Phase D2 pre-work)

## Context
- Initiative: `[VECTOR-PARITY-001]` Phase D2 – fix fluence scaling in the PyTorch trace pipeline.
- Scenario: 4096² warm benchmark trace pixel (1792, 2048), `λ=0.5 Å`, MOSFLM, oversample=1.
- Artifacts compared:
  - C trace: `reports/2026-01-vectorization-parity/phase_c/20251010T053711Z/c_traces/pixel_1792_2048.log`
  - Py trace (post D1 scattering fix): `reports/2026-01-vectorization-parity/phase_d/py_traces_post_fix/pixel_1792_2048.log`

## Observed Gap
- `TRACE_C: fluence_photons_per_m2 = 1.25932015286227e+29`
- `TRACE_PY: fluence_photons_per_m2 = 1.273239544735163e+20`
- Ratio (C / Py) ≈ **9.8906773518742e+08** (~10⁹× mismatch).
- The Py value numerically equals `(4/π) × 10² × flux`, suggesting the trace script is re-deriving fluence instead of echoing the prepared `BeamConfig.fluence` tensor.

## Authoritative References
- Spec requirement: `specs/spec-a-core.md:517` — *"fluence SHALL be set to flux·exposure / beamsize²"* with clipping semantics when beamsize < sample size.
- C implementation: `golden_suite_generator/nanoBragg.c:1148-1167` — applies the spec formula directly after parsing CLI flags.

## PyTorch Findings
- `src/nanobrag_torch/config.py:535-545` already mirrors the C formula inside `BeamConfig.__post_init__`. The simulator (`src/nanobrag_torch/simulator.py:527-539`) consumes `beam_config.fluence` without additional math, so the engine holds the correct value.
- The divergence arises in `scripts/debug_pixel_trace.py:378-382`, where the trace helper recomputes `fluence = flux * exposure / (beamsize_m²)` using whatever flux was present in the config rather than reading back `beam_config.fluence`. This reproduces the legacy 10⁹× underflow when only the default fluence was set (flux stayed at 1e18 for the CLI command; beamsize defaulted to 0.1 m inside the helper).

## Next-Step Recommendations
1. Update the trace helper to emit `TRACE_PY: fluence_photons_per_m2` straight from `beam_config.fluence` (or from `simulator.fluence`) so the Py log faithfully reflects the simulator state.
2. After adjusting the helper (and any simulator fixes, if required), rerun `scripts/debug_pixel_trace.py` with the standard Phase C pixels to confirm `fluence` matches the C trace within ≤1e-3 relative error.
3. Archive the refreshed traces under `reports/2026-01-vectorization-parity/phase_d/<STAMP>/py_traces_post_fix/` and summarize the before/after metrics in `fluence_parity.md` per plan instructions.

## Verification Snippet
```python
from decimal import Decimal
c = Decimal('1.25932015286227e+29')
py = Decimal('1.273239544735163e+20')
print(c / py)  # 9.8906773518742e+08
```

## Residual Questions
- Confirm whether any production paths (CLI or simulator) still recompute fluence from flux after Phase D2 changes. If yes, ensure those use meters² and respect the sample-clipping warning path (`Crystal.clip_sample_dimensions_for_beam`).

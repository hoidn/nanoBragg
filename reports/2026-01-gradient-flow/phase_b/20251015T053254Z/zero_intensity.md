# Zero-Intensity Probe Analysis — Phase B

**STAMP:** 20251015T053254Z
**Test Reference:** tests/test_gradients.py:397-448 (`TestAdvancedGradients::test_gradient_flow_simulation`)
**Objective:** Confirm whether `default_F=0` is the root cause of zero gradients observed in Phase A.

## Methodology

Executed a controlled gradient-flow experiment with two configurations:
1. **default_F=0.0** — reproduces Phase A failure scenario
2. **default_F=100.0** — provides structure factor data to enable intensity generation

Both runs used identical cell parameters (cubic 100Å, 90° angles) as differentiable tensors (`requires_grad=True`, dtype=float64) and invoked `loss.backward()` to compute parameter gradients.

## Results

### Configuration 1: default_F=0.0 (Failure Case)

```json
{
  "loss": 0.0,
  "grads": {
    "cell_a": 0.0,
    "cell_b": 0.0,
    "cell_c": 0.0,
    "cell_alpha": 0.0,
    "cell_beta": 0.0,
    "cell_gamma": 0.0
  }
}
```

**Observation:** Total intensity (loss) is exactly zero, resulting in all parameter gradients being zero. This confirms the simulation generated a completely black image.

### Configuration 2: default_F=100.0 (Control Case)

```json
{
  "loss": 983760.6856256215,
  "grads": {
    "cell_a": 7782.451766913256,
    "cell_b": -2947.4838589999167,
    "cell_c": -2947.4841549209464,
    "cell_alpha": 1.6585118984344818,
    "cell_beta": 5278.156767275025,
    "cell_gamma": -5278.1545015348665
  }
}
```

**Observation:** With structure factor data (`default_F=100`), the simulation produces non-zero intensity (loss ≈ 984k) and **all cell parameters exhibit non-zero gradients**. This proves the gradient computation graph is intact when intensity > 0.

## Conclusion

**Root Cause Confirmed:** The zero gradients in `test_gradient_flow_simulation` are a **direct consequence of zero intensity output**, not a gradient flow break in the autograd graph.

### Why Zero Intensity?

The failing test (tests/test_gradients.py:397-448) creates a `CrystalConfig` with:
- No `-hkl` file provided
- No `-default_F` value set (defaults to 0.0 per CrystalConfig dataclass defaults)

Without structure factor data, `F_cell = 0` for all Miller indices, leading to zero intensity at every pixel.

### Mathematical Chain

1. `F_cell = 0` (no structure factors)
2. `I_pixel ∝ F_cell²` → `I_pixel = 0` for all pixels
3. `loss = ∑ I_pixel = 0`
4. `∂loss/∂θ = 0` for all parameters θ (trivial gradient of constant zero)

## Implications for Phase B/C

**Phase B callchain analysis is MOOT** — the gradient path is not broken. The issue is upstream in the test fixture configuration.

**Recommended Remediation (Phase C):**
1. Update `test_gradient_flow_simulation` to provide structure factor data:
   - Option A: Set `default_F=100.0` in the CrystalConfig
   - Option B: Provide a minimal HKL file with non-zero structure factors
2. Re-run targeted test to confirm gradients become non-zero
3. Verify gradcheck passes for all cell parameters

## Next Actions

1. Skip Phase B1 (callchain tracing) — root cause identified without instrumentation
2. Skip Phase B2 (autograd hooks) — no gradient break to instrument
3. Proceed directly to Phase C hypothesis validation:
   - Draft minimal fix (add `default_F=100.0` to test fixture)
   - Verify fix via targeted pytest run
   - Update test documentation to explain structure factor requirement

## Artifact Manifest

- **zero_intensity_probe.json** — Raw gradient data for both configurations
- **zero_intensity.md** — This analysis document
- **Phase A Reference:** reports/2026-01-gradient-flow/phase_a/20251015T052020Z/summary.md

## Environment

- Python: 3.13.5
- PyTorch: 2.7.1+cu126
- Device: CPU (CUDA_VISIBLE_DEVICES=-1)
- Compile Guard: NANOBRAGG_DISABLE_COMPILE=1
- Dtype: float64

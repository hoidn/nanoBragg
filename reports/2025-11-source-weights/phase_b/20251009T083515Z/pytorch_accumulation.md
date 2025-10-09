# SOURCE-WEIGHT-001 Phase B2 — PyTorch Weighting Path Analysis

**Date:** 2025-10-09
**Task:** Trace the PyTorch implementation's use of source weights and identify where it diverges from spec.

## PyTorch Implementation Call Chain

### Entry Point: `Simulator.run()` → `_compute_physics_for_position()`

The multi-source physics calculation flows through the following call chain:

```
Simulator.run() (line ~743)
  ↓
  _compute_physics_for_position() (lines 253-425)
    ↓
    [Per-source intensity calculation]
    ↓
    Weighted accumulation (lines 404-422)
```

## Divergent Code: Weighted Accumulation

### Location: `src/nanobrag_torch/simulator.py:404-422`

```python
# Handle multi-source weighted accumulation
if is_multi_source:
    # Apply source weights and sum over sources
    # intensity: (n_sources, S, F) or (n_sources, batch)
    # source_weights: (n_sources,) -> (n_sources, 1, 1) or (n_sources, 1)
    if source_weights is not None:
        # Prepare weights for broadcasting
        weight_shape = [n_sources] + [1] * (intensity.dim() - 1)
        weights_broadcast = source_weights.view(*weight_shape)
        # Apply weights and sum over source dimension
        intensity = torch.sum(intensity * weights_broadcast, dim=0)  # ← VIOLATES SPEC
        # CLI-FLAGS-003 Phase M1: Apply same accumulation to pre-polar intensity
        if intensity_pre_polar is not None:
            intensity_pre_polar = torch.sum(intensity_pre_polar * weights_broadcast, dim=0)  # ← VIOLATES SPEC
    else:
        # No weights provided, simple sum
        intensity = torch.sum(intensity, dim=0)  # ← CORRECT behavior
        # CLI-FLAGS-003 Phase M1: Apply same accumulation to pre-polar intensity
        if intensity_pre_polar is not None:
            intensity_pre_polar = torch.sum(intensity_pre_polar, dim=0)  # ← CORRECT behavior
```

**Critical violation:** Lines 413 and 416 multiply per-source intensities by `weights_broadcast` before summing. This directly contradicts the spec requirement that weights are "read but ignored."

### Supporting Evidence: Steps Normalization

**Location:** `src/nanobrag_torch/simulator.py:861-874`

```python
# Calculate normalization factor (steps)
# Per spec AT-SAM-001: "Final per-pixel scale SHALL divide by steps"
# SOURCE-WEIGHT-001 Phase C1: C-parity requires ignoring source weights
# Per spec-a-core.md line 151: "The weight column is read but ignored (equal weighting results)"
# C code (nanoBragg.c:3358) divides by steps = sources*mosaic_domains*phisteps*oversample^2
# where sources is the COUNT of sources, not the sum of weights
phi_steps = self.crystal.config.phi_steps
mosaic_domains = self.crystal.config.mosaic_domains

# Always use n_sources (count) to match C behavior
# The spec explicitly states source weights are "read but ignored"
source_norm = n_sources

steps = source_norm * phi_steps * mosaic_domains * oversample * oversample  # Include sources and oversample^2
```

**Partial correctness:** The normalization correctly uses `n_sources` (count) rather than weight sum. This matches the C code and spec requirement.

**However:** The weighted multiplication at line 413 undermines this correct normalization. The effect is:
- Weighted source file `[1.0, 0.2]` produces intensity `≈ 1.2 × base_per_source` via the weighted sum
- Normalization divides by `steps = 2 × ...` (count-based)
- Net result: Final intensity is `0.6 × expected` (average of [1.0, 0.2])

This explains the observed sum_ratio ≈ 0.728 in Phase A evidence (PyTorch underestimates C by ~27%).

## Tensor Shape Flow

### Input Shapes
- `intensity`: `(n_sources, S, F)` after per-source calculation
- `source_weights`: `(n_sources,)` from `BeamConfig`

### Broadcasting
- `weights_broadcast`: `(n_sources, 1, 1)` via `view(*weight_shape)`

### Output Shape
- After weighted sum: `(S, F)` collapsed along source dimension

## Call-Chain Table

| Component | File:Line | Responsibility | Spec Compliance |
|-----------|-----------|----------------|-----------------|
| `run()` | `simulator.py:743+` | Top-level loop over pixels | ✅ |
| `_compute_physics_for_position()` | `simulator.py:253` | Per-pixel physics | Partial |
| Multi-source branch | `simulator.py:404-422` | Weighted accumulation | ❌ Violates spec |
| Steps calculation | `simulator.py:874` | Normalization factor | ✅ Uses count |
| Final scaling | `simulator.py:876+` | Apply `r_e^2 · fluence / steps` | ✅ (given correct intensity) |

## Diagnosis

**Root cause:** The PyTorch implementation treats `source_weights` as multiplicative factors during accumulation (line 413), interpreting them as physical intensity modulation rather than metadata to be ignored.

**Expected behavior (per spec):** All sources contribute equally to the sum, regardless of weight values. The `source_weights` tensor should remain stored for potential future use (e.g., trace logging, advanced polarization models) but MUST NOT influence the intensity calculation.

**Required fix:** Remove `* weights_broadcast` multiplication at lines 413 and 416, reducing the multi-source path to a simple `torch.sum(intensity, dim=0)` identical to the `else` branch.

## Configuration Entry Point

**Location:** `Simulator.__init__` caches source weights from `BeamConfig`:

```python
self._source_weights = beam_config.source_weights
```

**Observation:** Weights are correctly cached as metadata. The violation occurs only during physics accumulation, not during configuration setup.

## Exit Criterion for Phase B2

✅ Complete. PyTorch call-chain documented with:
- Exact file:line citations for divergent code
- Tensor shape annotations
- Root-cause diagnosis linking weight multiplication to observed Phase A sum_ratio delta

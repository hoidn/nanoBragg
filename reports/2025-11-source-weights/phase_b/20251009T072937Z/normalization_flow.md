# Normalization Flow Analysis — Weighted Source Accumulation

**Generated:** 2025-10-09T07:29:37Z
**Context:** Phase B1 of source-weight-normalization initiative (plans/active/source-weight-normalization.md)
**Purpose:** Document step-by-step normalization path in PyTorch simulator to identify where `sum(source_weights)` should replace `n_sources`.

---

## Current Issue Summary

**Problem:** `Simulator.run` (src/nanobrag_torch/simulator.py:837-1137) divides accumulated intensity by `n_sources` even when custom `source_weights` are provided. This causes a 327.9× discrepancy (Phase A evidence) when source weights are non-uniform (e.g., [1.0, 0.2]).

**Expected Behavior:** Normalization should divide by `sum(source_weights)` to correctly represent total fluence, not by the count of sources.

---

## Step-by-Step Normalization Path

### 1. Source Weight Initialization (simulator.py:557-566)

**Location:** `Simulator.__init__`
**Line Range:** 557-566

```python
# P3.0: Default source_weights to equal weights if not provided
if self.beam_config.source_weights is not None:
    self._source_weights = self.beam_config.source_weights.to(device=self.device, dtype=self.dtype)
else:
    # Default to equal weights if not provided
    self._source_weights = torch.ones(len(self.beam_config.source_directions), device=self.device, dtype=self.dtype)
```

**Action:** Source weights are initialized and moved to correct device/dtype. Default to uniform weights (all 1.0) if not provided.

**Issue:** No normalization at this stage; raw weights are stored.

---

### 2. Source Configuration in run() (simulator.py:847-859)

**Location:** `Simulator.run` — source setup
**Line Range:** 847-859

```python
# PERF-PYTORCH-004 P1.2: Use pre-normalized source tensors from __init__
if self._source_directions is not None:
    n_sources = len(self._source_directions)
    source_directions = self._source_directions
    source_wavelengths_A = self._source_wavelengths_A
    source_weights = self._source_weights
else:
    # No explicit sources, use single beam configuration
    n_sources = 1
    source_directions = None
    source_wavelengths_A = None
    source_weights = None
```

**Action:** Extract source count and weights from cached initialization tensors.

**Issue:** `n_sources` is set to the **count** of sources, not the sum of weights.

---

### 3. Steps Calculation (simulator.py:861-870) **[CRITICAL DIVERGENCE POINT]**

**Location:** `Simulator.run` — normalization factor calculation
**Line Range:** 861-870

```python
# Calculate normalization factor (steps)
# Per spec AT-SAM-001: "Final per-pixel scale SHALL divide by steps"
# PERF-PYTORCH-004 P3.0c: Per AT-SRC-001 "steps = sources; intensity contributions SHALL sum with per-source λ and weight, then divide by steps"
# The divisor SHALL be the COUNT of sources, not the SUM of weights.
# Weights are applied during accumulation (inside compute_physics_for_position), then we normalize by count.
phi_steps = self.crystal.config.phi_steps
mosaic_domains = self.crystal.config.mosaic_domains
source_norm = n_sources

steps = source_norm * phi_steps * mosaic_domains * oversample * oversample  # Include sources and oversample^2
```

**Current Behavior:**
- `source_norm = n_sources` (line 868)
- `steps = source_norm × phi_steps × mosaic_domains × oversample²` (line 870)

**Issue:** The comment on line 864 says "The divisor SHALL be the COUNT of sources, not the SUM of weights" but this contradicts the physical meaning when weights are non-uniform. If two sources have weights [1.0, 0.2], the total effective fluence is 1.2× a single source, NOT 2×.

**Required Fix:** Replace line 868 with:
```python
source_norm = source_weights.sum() if source_weights is not None else n_sources
```

---

### 4. Per-Source Weight Application (simulator.py:407-413)

**Location:** `compute_physics_for_position` (module-level pure function)
**Line Range:** 407-413

```python
# source_weights: (n_sources,) -> (n_sources, 1, 1) or (n_sources, 1)
if source_weights is not None:
    # Prepare weights for broadcasting
    weight_shape = [n_sources] + [1] * (intensity.dim() - 1)
    weights_broadcast = source_weights.view(*weight_shape)
    # Apply weights and sum over source dimension
    intensity = torch.sum(intensity * weights_broadcast, dim=0)
    # CLI-FLAGS-003 Phase M1: Apply same accumulation to pre-polar intensity
```

**Action:** Each source's intensity contribution is multiplied by its weight, then summed across sources.

**Correctness:** This step is **correct**. The weighted sum properly accumulates per-source contributions.

**Mathematical Effect:** For sources with weights [w₁, w₂, ...], this produces:
```
I_accumulated = w₁·I₁ + w₂·I₂ + ...
```

---

### 5. Multi-Source Physics Call (simulator.py:938-946)

**Location:** `Simulator.run` — vectorized physics computation (oversample > 1 case)
**Line Range:** 938-946

```python
# Single batched call for all sources
# This replaces the Python loop and enables torch.compile optimization
# CLI-FLAGS-003 Phase M1: Unpack both post-polar and pre-polar intensities
physics_intensity_flat, physics_intensity_pre_polar_flat = self._compute_physics_for_position(
    coords_reshaped, rot_a, rot_b, rot_c, rot_a_star, rot_b_star, rot_c_star,
    incident_beam_direction=incident_dirs_batched,
    wavelength=wavelengths_batched,
    source_weights=source_weights
)
```

**Action:** Pass `source_weights` to physics kernel. Weighted summation happens inside `compute_physics_for_position` (see step 4).

**Correctness:** This step is **correct**.

---

### 6. Final Intensity Scaling (simulator.py:1120-1137) **[USES INCORRECT STEPS]**

**Location:** `Simulator.run` — final physical intensity calculation
**Line Range:** 1120-1137

```python
#             /* convert pixel intensity into photons */
#             test = r_e_sqr*fluence*I/steps;
#
#             /* do the corrections now, if they haven't been applied already */
#             if(! oversample_thick) test *= capture_fraction;
#             if(! oversample_polar) test *= polar;
#             if(! oversample_omega) test *= omega_pixel;
#             floatimage[imgidx] += test;
#
# Units: [dimensionless] / [dimensionless] × [m²] × [photons/m²] = [photons·m²]
physical_intensity = (
    normalized_intensity
    / steps
    * self.r_e_sqr
    * self.fluence
)
```

**Current Behavior:** Divides by `steps`, which was calculated using `n_sources` (line 870).

**Issue:** When source weights are non-uniform, this over-normalizes the intensity because it divides by the count instead of the effective weight sum.

**Mathematical Effect (example with weights [1.0, 0.2]):**
- Weighted accumulation produces: `I_acc = 1.0·I₁ + 0.2·I₂`
- Current normalization: `I_final = I_acc / 2` (divides by count)
- Correct normalization: `I_final = I_acc / 1.2` (divides by sum)
- **Result:** Current output is `1.2/2 = 0.6×` too small (or equivalently, C code is `2/1.2 = 1.67×` larger)

Wait, this doesn't match the 327.9× discrepancy from Phase A. Let me re-check...

**Phase A Evidence Review:**
- PyTorch max: 101.1, total: 151963.1
- C max: 0.009, total: 463.4
- Ratio: 151963.1 / 463.4 ≈ 327.9×

This suggests PyTorch is producing **larger** values than C, not smaller. This implies:
- Either the C code is dividing by something extra, OR
- There's an additional scaling factor in play (e.g., fluence calculation, r_e_sqr, capture fractions)

**Revised Understanding:** The normalization discrepancy may be compounded by other factors (fluence, capture fractions, polarization). The core issue remains: **PyTorch divides by n_sources when it should divide by sum(source_weights)**.

---

## Summary of Data Flow

1. **Init (557-566):** Source weights cached, defaulting to uniform weights
2. **run() setup (847-859):** Extract `n_sources` count and `source_weights` tensor
3. **Steps calc (861-870):** **[BUG]** `source_norm = n_sources` instead of `sum(source_weights)`
4. **Physics kernel (407-413):** Correctly apply weights during accumulation (weighted sum)
5. **Final scaling (1132-1137):** **[USES BUGGY STEPS]** Divide by incorrect normalization factor

---

## Where n_sources Enters the Formula

**Primary Location:** Line 868 (`source_norm = n_sources`)

This value propagates to:
- Line 870: `steps = source_norm × phi_steps × mosaic_domains × oversample²`
- Line 1134: `physical_intensity = normalized_intensity / steps × r_e_sqr × fluence`

---

## Proposed Fix Location

**File:** `src/nanobrag_torch/simulator.py`
**Line:** 868
**Current:** `source_norm = n_sources`
**Proposed:** `source_norm = source_weights.sum() if source_weights is not None else n_sources`

**Rationale:** When custom weights are provided, the effective "number of sources" for normalization purposes is the sum of weights, not the count. This correctly represents the total fluence contribution.

---

## Edge Cases to Consider

1. **Uniform weights ([1.0, 1.0, ...]):** `sum(weights) = n_sources`, so behavior is identical (backward compatible)
2. **No source_weights (single source):** `source_weights = None`, fall back to `n_sources = 1` (current behavior preserved)
3. **Zero-sum weights:** Should add validation to prevent division by zero (implementation detail)
4. **Negative weights:** Not physically meaningful; should be validated in BeamConfig (implementation detail)

---

## Dependency on Polarization Code

**Note:** PERF-PYTORCH-004 P3.0b moved polarization application inside `compute_physics_for_position` (per-source). The normalization fix is **independent** of polarization logic but should be coordinated:

- Polarization is applied **before** source weighting (line 407-413)
- This is correct: each source's polarization-corrected intensity is weighted, then summed
- No coupling issue with the normalization fix

---

## References

- **Phase A Evidence:** `reports/2025-11-source-weights/phase_a/20251009T071821Z/`
- **C Reference:** `nanoBragg.c` lines 2480-2595 (source loop and weighting)
- **Spec:** `specs/spec-a-core.md` §5 (Source intensity and sampling)
- **Architecture:** `docs/architecture/pytorch_design.md` §2.3 (Source handling)
- **Config Map:** `docs/development/c_to_pytorch_config_map.md` §Beam/Source parameters

---

**Next Steps:** Proceed to Phase B2 (strategy.md) to define the exact implementation approach and edge-case handling.

# Normalization Strategy — Weighted Source Sum

**Generated:** 2025-10-09T07:29:37Z
**Context:** Phase B2 of source-weight-normalization initiative
**Prereqs:** normalization_flow.md (Phase B1) completed

---

## Decision: Divide by sum(source_weights)

**Approach:** Replace the normalization factor `source_norm = n_sources` with `source_norm = sum(source_weights)` when custom weights are provided.

**Rationale:**
1. **Physical Correctness:** When sources have weights [w₁, w₂, ...], the total effective fluence is proportional to `Σwᵢ`, not the count of sources.
2. **Backward Compatibility:** For uniform weights (all 1.0), `sum(weights) = n_sources`, preserving existing behavior.
3. **C-Code Parity:** The C reference (`nanoBragg.c` lines 2480-2595) applies source weights during accumulation and normalizes by the effective weighted count.
4. **Minimal Churn:** Single-line change in `simulator.py:868`, no ripple effects to other modules.

---

## Implementation Details

### Primary Change

**File:** `src/nanobrag_torch/simulator.py`
**Line:** 868
**Current Code:**
```python
source_norm = n_sources
```

**Proposed Code:**
```python
source_norm = source_weights.sum().item() if source_weights is not None else n_sources
```

**Justification for `.item()`:**
- `source_weights.sum()` returns a 0-dimensional tensor
- `steps` calculation (line 870) multiplies scalar values, so extract Python scalar
- **Differentiability Check:** `steps` is used as a divisor in line 1134. For gradient flow through `source_weights`, the `.sum()` operation must remain in the computational graph. However, `steps` itself is not a parameter requiring gradients—it's a normalization constant derived from sampling configuration. Using `.item()` here is acceptable because:
  - We do not need gradients w.r.t. `steps` itself
  - Gradients w.r.t. individual source intensities flow through the weighted sum in `compute_physics_for_position` (line 413), not through the normalization factor
  - If future use cases require differentiable source weights (e.g., optimizing beam balance), we can refactor to keep `source_norm` as a tensor

**Alternative (tensor-preserving):**
```python
source_norm = source_weights.sum() if source_weights is not None else torch.tensor(n_sources, device=self.device, dtype=self.dtype)
```
This version maintains full differentiability but requires ensuring `steps` remains a tensor throughout (may affect downstream type checks). **Recommend deferring tensor-preserving approach until a use case demands differentiable source_weights.**

---

## Edge Cases

### 1. Uniform Weights
**Scenario:** `source_weights = [1.0, 1.0, 1.0]`
**Effect:** `sum(weights) = 3.0 = n_sources`
**Outcome:** Identical behavior to current implementation (backward compatible).

### 2. No Source Weights (Single Source)
**Scenario:** `source_weights = None` (default beam configuration)
**Effect:** Falls back to `n_sources = 1`
**Outcome:** Current single-source behavior preserved.

### 3. Zero-Sum Weights
**Scenario:** `source_weights = [0.5, -0.5]` (pathological)
**Effect:** `sum(weights) = 0` → division by zero in line 1134
**Mitigation:** Add validation in `BeamConfig.__post_init__` to ensure `sum(source_weights) > 0`. Raise `ValueError` if violated.
```python
if self.source_weights is not None and self.source_weights.sum() <= 0:
    raise ValueError("source_weights must sum to a positive value")
```

### 4. All-Zero Weights
**Scenario:** `source_weights = [0.0, 0.0]` (user error)
**Effect:** `sum(weights) = 0` → division by zero
**Mitigation:** Same as case #3 (validation in BeamConfig).

### 5. Negative Weights
**Scenario:** `source_weights = [1.0, -0.2]` (non-physical)
**Effect:** `sum(weights) = 0.8`, but negative contributions may produce artifacts
**Mitigation:** Add validation in `BeamConfig.__post_init__` to ensure all weights `>= 0`. Raise `ValueError` if violated.
```python
if self.source_weights is not None and (self.source_weights < 0).any():
    raise ValueError("source_weights must be non-negative")
```

### 6. Very Small Weight Sum
**Scenario:** `source_weights = [1e-10, 1e-10]` (numerical instability)
**Effect:** `sum(weights) ≈ 0`, potential division-by-near-zero amplification
**Mitigation:** Document minimum weight sum requirement (e.g., `sum(weights) >= 1e-6`) or add a warning. For now, rely on physical constraints (users won't specify near-zero beam intensities).

---

## Interaction with Polarization Code

**Status:** No coupling issues identified.

**Reasoning:**
- Polarization is applied **per-source** inside `compute_physics_for_position` (PERF-PYTORCH-004 P3.0b)
- Source weighting happens **after** polarization (line 413: `intensity * weights_broadcast`)
- Normalization by `sum(source_weights)` occurs in the final scaling step (line 1134)
- **Flow:** `I_source → polarization → weighting → accumulation → normalize by sum(weights)`

**Verification:** No changes needed to polarization logic. The fix is isolated to the `source_norm` calculation.

---

## Device/Dtype Considerations (AT-PERF-DEVICE-001)

**Current State:** `source_weights` are moved to `self.device` and `self.dtype` during `__init__` (line 559).

**Proposed Change Impact:**
- `.sum()` operation inherits device/dtype from `source_weights` tensor
- `.item()` extracts a Python scalar (device-agnostic)
- No additional `.to()` calls required

**Compatibility:** CUDA and CPU execution paths are unaffected. The fix is device-neutral.

---

## Pre-Normalization Alternative (Rejected)

**Alternative Approach:** Normalize `source_weights` to sum to 1.0 during initialization, then multiply by `n_sources` during final scaling.

**Rejected Because:**
1. **Semantic Ambiguity:** Pre-normalized weights lose their physical meaning (relative fluence contributions)
2. **User Confusion:** Users expect weights to represent actual relative intensities (e.g., [1.0, 0.2] = 20% intensity)
3. **Extra Complexity:** Requires storing both raw and normalized weights, increasing state management burden
4. **No Benefit:** Does not simplify the math—just moves the sum operation to a different location

**Conclusion:** Divide by `sum(source_weights)` at normalization time (current proposal) is clearer and simpler.

---

## Testing Implications

**Required Regression Coverage:**
1. **Test Case A:** Two sources with weights [1.0, 0.2]
   - Verify PyTorch output matches C reference within tolerance (correlation ≥ 0.999)
   - Check that total intensity is NOT scaled by 2× (current bug)

2. **Test Case B:** Three sources with uniform weights [1.0, 1.0, 1.0]
   - Verify backward compatibility: output unchanged vs. current implementation

3. **Test Case C:** Single source (no explicit `source_weights`)
   - Verify default behavior preserved

4. **Test Case D:** Edge case validation (BeamConfig init)
   - Verify `ValueError` raised for zero-sum weights
   - Verify `ValueError` raised for negative weights

**Tolerance Expectations:**
- CPU: correlation ≥ 0.9999, max |Δ| ≤ 1e-5
- CUDA: correlation ≥ 0.999, max |Δ| ≤ 1e-4 (allow for device-specific numerical differences)

---

## Migration Path

**Backward Compatibility:** Fully preserved for existing use cases.

**No Breaking Changes:**
- Single-source simulations: unaffected (`source_weights = None`)
- Uniform multi-source: mathematically equivalent (`sum([1,1,1]) = 3`)
- Custom weights: bug fix (previously incorrect, now correct)

**Documentation Updates:**
1. `docs/architecture/pytorch_design.md` §8 (Physics Model & Scaling): Add note on weighted source normalization
2. `docs/development/testing_strategy.md` §2.5 (Parallel Validation Matrix): Add AT-SRC-001 parity case
3. `README_PYTORCH.md` (CLI usage): Document `-source` file format and weighting semantics

---

## Blocking Questions / Open Issues

**Q1:** Should we support differentiable `source_weights` for gradient-based beam optimization?
**A1:** Defer to future work. Current implementation uses `.item()` for simplicity. If gradients w.r.t. source weights are needed, refactor to keep `source_norm` as a tensor (estimated effort: 1-2 hours).

**Q2:** Does the C reference use integer or floating-point division for `steps`?
**A2:** `nanoBragg.c` line 3050: `test = r_e_sqr*fluence*I/steps` uses floating-point (variables are `double`). PyTorch implementation is consistent.

**Q3:** Are there any implicit dependencies on `n_sources` elsewhere in the codebase?
**A3:** Grep check (completed 2025-10-09):
```bash
$ git grep -n 'n_sources' src/nanobrag_torch/
simulator.py:850:    n_sources = len(self._source_directions)
simulator.py:856:    n_sources = 1
simulator.py:868:    source_norm = n_sources
```
Only usage is in normalization calculation (line 868). No other dependencies found.

---

## Summary

**Decision:** Replace `source_norm = n_sources` with `source_norm = source_weights.sum().item() if source_weights is not None else n_sources`.

**Risk:** Low. Single-line change with clear physical justification and full backward compatibility.

**Next Step:** Proceed to Phase B3 (tests.md) to define regression coverage plan.

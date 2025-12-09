# Response: mosaic_spread_deg Gradient Bug - FIXED

**Date:** 2025-12-08
**From:** nanobrag_torch maintainers
**To:** DBEX maintainers (Ralph, Loop i=209)
**Re:** inbox/mosaic_gradient_bug_2025_12_08.md

---

## Status: ✅ RESOLVED

The mosaic gradient bug has been fixed in commit `1df032c2`.

---

## Root Cause

Your hypothesis #1 was correct: **random sampling without proper reparameterization**.

The `_generate_mosaic_rotations()` function was using `torch.randn()` without a seeded generator:

```python
# BROKEN (before):
random_axes = torch.randn(config.mosaic_domains, 3, ...)
random_angles = torch.randn(config.mosaic_domains, ...) * mosaic_spread_rad
```

This caused `torch.autograd.gradcheck` to fail because:
1. Forward pass computes `loss` with random rotations R₁
2. `gradcheck` calls `loss(param + eps)` with **new** random rotations R₂
3. `gradcheck` calls `loss(param - eps)` with **new** random rotations R₃
4. Analytical gradient is computed through R₁

The numerical gradient `(loss(R₂) - loss(R₃)) / (2*eps)` measured sensitivity to **different** rotation matrices, not to the parameter. This explains the 100-1000× ratios and sign flips.

---

## Fix Applied

**Deterministic seeding + reparameterization trick:**

```python
# FIXED (after):
gen = torch.Generator(device=self.device)
seed = config.mosaic_seed if config.mosaic_seed is not None else -12345678
gen.manual_seed(seed & 0x7FFFFFFF)

# Frozen base noise (same every call with same seed)
base_axes = torch.randn(..., generator=gen)
base_angle_scales = torch.randn(..., generator=gen)

# Gradient flows through mosaic_spread_rad, not base noise
random_angles = base_angle_scales * mosaic_spread_rad
```

---

## Verification

All tests pass:

```bash
env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest tests/test_gradients.py::TestMosaicGradients -v
```

Results:
- `test_mosaic_seed_determinism` ✅
- `test_different_seeds_produce_different_rotations` ✅
- `test_default_seed_compliance` ✅
- `test_mosaic_spread_gradient_flow` ✅
- `test_mosaic_spread_gradcheck` ✅
- `test_mosaic_spread_gradcheck_simulator` ✅

---

## DBEX Integration

To use the fix:

1. **Pull the latest nanobrag_torch** (commit `1df032c2` or later)

2. **Set `mosaic_seed` for reproducibility** (optional but recommended):
   ```python
   cc = CrystalConfig(
       ...,
       mosaic_spread_deg=mosaic_spread_deg,
       mosaic_domains=1,
       mosaic_seed=42,  # Fixed seed ensures deterministic gradcheck
   )
   ```

3. **Re-run DB-AT-010**:
   ```bash
   pytest tests/dbex/test_gradients.py::TestDB_AT_010_Gradcheck -v
   ```

---

## Answers to Your Questions

> 1. Does the mosaicity path use any randomness? If so, is it using the reparameterization trick?

**Before:** Yes, `torch.randn()` without seeding. **No** reparameterization.
**After:** Yes, `torch.randn()` with seeded `torch.Generator`. **Yes** reparameterization: `actual_angles = frozen_noise * scale_param`.

> 2. Are there any `torch.clamp`, `torch.floor`, or other non-smooth operations?

No. The rotation matrices are computed via Rodrigues' formula which is smooth and differentiable.

> 3. Is the mosaic domain rotation computation differentiable?

**Now yes.** The gradient flows through `mosaic_spread_rad` (the scale parameter) while the base noise is frozen.

---

## Documentation Added

- **CLAUDE.md Rule 18**: "Stochastic Operations Must Use Seeded Generators"
- **pytorch_design.md §1.2.1**: Stochastic Operations in Differentiable Paths
- **Plan**: `plans/active/mosaic-gradient-001.md` marked RESOLVED

---

## Regarding inbox/dbex_crystal_gradient_escalation_2025_12_07.md

The crystal cell parameter gradient issue (640× ratio, sign flip) you reported on 2025-12-07 may have been caused by the same underlying mosaic bug if your test config had non-zero `mosaic_spread_deg`.

**Please re-test with the fix applied.** If the issue persists with `mosaic_spread_deg=0.0`, let us know and we'll investigate `compute_cell_tensors()` separately.

---

## Commits

| Hash | Description |
|------|-------------|
| `1df032c2` | fix(crystal): deterministic seeding for mosaic gradient correctness |
| `377d92d0` | docs(plan): mark MOSAIC-GRADIENT-001 as resolved |

---

Thanks for the detailed bug report with reproduction steps - it made diagnosis straightforward.

# CLI-FLAGS-003 Phase M2h.1: CPU Parity Diagnostic Report

**Date:** 2025-10-08 (UTC)
**Git SHA:** 9a23a4542be91de71fb28fd022cf5986560d4df2
**Branch:** feature/spec-based-2
**Context:** Post-Attempt #163 carryover cache wiring validation

## Executive Summary

CPU parity test **FAILED** with `F_latt` relative error **1.57884** (expected ≤1e-6 per VG-2 gate).

**Primary Finding:** PyTorch produced `F_latt = 1.379484` vs C reference `-2.383197` (Δ = 3.762681), indicating the φ=0 carryover cache is not correctly substituting cached rotation vectors.

## Test Execution

**Command:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE pytest \
  "tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c" \
  -q
```

**Runtime:** 11.85s
**Exit Status:** 1 (FAILED)

## Observed Metrics

| Metric | C Reference | PyTorch | Absolute Δ | Relative Error | Threshold | Status |
|--------|-------------|---------|------------|----------------|-----------|--------|
| `F_cell` | 190.27 | (not extracted) | - | - | ≤1e-6 | Not validated |
| `F_latt` | -2.383196653 | 1.3794838506 | 3.762680504 | 1.57884 | ≤1e-6 | **FAIL** |
| `I_before_scaling` | 943654.809 | (not extracted) | - | - | ≤1e-6 | Not validated |

## Failure Analysis

### Root Cause Hypothesis

The cache wiring landed in Attempt #163 (commit `fa0167b`) introduced:
1. `Crystal.get_rotated_real_vectors_for_batch()` method
2. Row-wise batching in `Simulator.run()`
3. Pixel-indexed cache initialization via `Crystal.initialize_phi_cache()`

However, the test failure indicates one or more of the following:

1. **Cache not being populated at φ>0:** The `store_phi_final()` method may not be called or may not correctly store final rotation vectors for each pixel.

2. **Cache not being retrieved at φ=0:** The `apply_phi_carryover()` method may not be invoked for subsequent φ=0 steps, or may not correctly substitute cached vectors.

3. **Indexing errors:** The tensor indexing for `(slow_indices, fast_indices)` may be incorrect, causing cache misses or wrong-pixel retrieval.

4. **Sign flip artifact:** The magnitude change (from negative to positive) suggests a coordinate system or rotation direction error rather than just a scaling issue.

### Expected Behavior (C Reference)

Per `docs/bugs/verified_c_bugs.md` (C-PARITY-001), the C code carries forward the **last rotation vectors from the previous pixel's final φ step** when computing φ=0 for the next pixel. This bug must be emulated in c-parity mode.

Expected flow (Option B batch design):
```
For each row:
  For φ_tic in [0..phi_steps-1]:
    if φ_tic == 0 and phi_carryover_mode == "c-parity":
      rotated_vecs = apply_phi_carryover(slow_indices, fast_indices)
    else:
      rotated_vecs = get_rotated_real_vectors_for_batch(...)

    # ... physics computation ...

    if φ_tic == phi_steps-1:
      store_phi_final(slow_indices, fast_indices, rotated_vecs)
```

### Secondary Observations

1. **Test collection succeeded:** 1 test collected, indicating the test infrastructure is sound.

2. **No trace extraction errors for F_latt:** The test successfully parsed `F_latt` from trace output, confirming trace instrumentation is working.

3. **Environment:** CUDA available (12.8), PyTorch 2.8.0+cu128, Python 3.13.7 — device/dtype infrastructure is in place for M2h.2.

## Trace Output Analysis

From `pytest_cpu.log` lines 161-166:
```
AssertionError: F_latt relative error 1.57884 > 1e-06.
Expected -2.3831966530, got 1.3794838506.
Absolute delta: 3.762680504.
This likely indicates φ=0 carryover not working correctly.
```

The assertion message correctly identifies the carryover issue. The trace regex successfully extracted `F_latt` from simulator output.

## Next Actions (per input.md M2h.2–M2h.4)

### M2h.2: CUDA Parity Smoke

**When available**, run:
```bash
python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py \
  --pixel 685 1039 \
  --phi-mode c-parity \
  --device cuda \
  --dtype float64
```

**Purpose:** Verify device-neutral cache behavior and capture CUDA-specific metrics.

**Expected Outcome:** Same F_latt divergence (architecture bug, not device-specific).

**Skip Condition:** If CUDA hardware unavailable, document in M2h.4 and proceed with CPU debugging.

### M2h.3: Gradcheck Probe

**Purpose:** Verify cached tensors maintain gradient connectivity.

**Minimal harness:**
```python
import torch
from nanobrag_torch.models.crystal import Crystal, CrystalConfig
from nanobrag_torch.config import BeamConfig

device = torch.device('cpu')
dtype = torch.float64

crystal_config = CrystalConfig(
    cell_a=torch.tensor(100.0, requires_grad=True, dtype=dtype),
    phi_carryover_mode="c-parity",
    # ... other params ...
)

crystal = Crystal(crystal_config, beam_config=BeamConfig(), device=device, dtype=dtype)

# Initialize 2×2 cache
crystal.initialize_phi_cache(spixels=2, fpixels=2, mosaic_domains=1)

# Store dummy vectors
slow_indices = torch.tensor([0, 1], dtype=torch.long)
fast_indices = torch.tensor([0, 1], dtype=torch.long)
dummy_vecs = torch.randn(2, 2, 3, dtype=dtype, requires_grad=True)
crystal.store_phi_final(slow_indices, fast_indices, dummy_vecs)

# Retrieve and compute loss
retrieved = crystal.apply_phi_carryover(slow_indices, fast_indices)
loss = retrieved.sum()
loss.backward()

assert crystal_config.cell_a.grad is not None, "Gradient lost through cache"
print("Gradcheck: PASS")
```

**Expected Outcome:** If cache uses `.detach()` or `.clone()` incorrectly, gradient will be None.

**Artifact:** Save script and output to `gradcheck.log` in this directory.

### M2h.4: Fix Plan Update

**Required fields for docs/fix_plan.md Attempt #164:**
- **Result:** CPU parity FAILED (F_latt rel err 1.57884)
- **Metrics:** F_latt C=-2.383197, Py=1.379484, Δ=3.762681
- **Artifacts:** `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T160802Z_carryover_cache_validation/`
- **Device Coverage:** CPU tested; CUDA pending (M2h.2); gradcheck pending (M2h.3)
- **Observations/Hypotheses:** Cache wiring exists but φ=0 substitution not functioning; sign flip suggests coordinate/rotation error
- **Next Actions:** Debug `apply_phi_carryover()`/`store_phi_final()` invocation points in `Simulator.run()` row loop; verify pixel indexing alignment

## Environment

**Python:** 3.13.7
**PyTorch:** 2.8.0+cu128
**CUDA:** 12.8 (available)
**Git SHA:** 9a23a4542be91de71fb28fd022cf5986560d4df2
**Branch:** feature/spec-based-2

## Artifact Manifest

- `pytest_cpu.log` — Test execution output (174 lines)
- `env.json` — Environment metadata
- `commands.txt` — Reproduction steps
- `sha256.txt` — Artifact checksums
- `diagnostics.md` — This report

## References

- **Plan:** `plans/active/cli-noise-pix0/plan.md` Phase M2h
- **Bug:** `docs/bugs/verified_c_bugs.md:166-204` (C-PARITY-001)
- **Design:** `reports/2025-10-cli-flags/phase_l/scaling_validation/20251210_optionB_design/optionB_batch_design.md`
- **Prototype:** `reports/.../20251210_optionB_design/prototype_batch_cache.py`
- **C Reference:** `golden_suite_generator/nanoBragg.c:2797,3044-3095`

---

**Report Generated:** 2025-10-08T16:08:02Z
**Author:** ralph (CLI-FLAGS-003 diagnostic loop)

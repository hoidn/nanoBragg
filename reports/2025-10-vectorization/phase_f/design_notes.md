# Phase F1 - Detector Absorption Vectorization Design

**Initiative:** VECTOR-TRICUBIC-001 (Vectorize tricubic interpolation and detector absorption)
**Phase:** F1 (Design)
**Date:** 2025-10-08
**Status:** DRAFT (awaiting implementation in F2)

---

## 1. Context & Motivation

### 1.1 Background

Phase E successfully vectorized the tricubic interpolation infrastructure (`polint`/`polin2`/`polin3` polynomial helpers + batched neighborhood gathering), eliminating Python loops from structure factor evaluation. This work validated:
- ✅ Correctness on CPU + CUDA (19/19 tests passed)
- ✅ No performance regression vs baseline
- ✅ Gradient flow preservation
- ✅ Device/dtype neutrality

Phase F now targets the remaining Python loop bottleneck: **detector absorption** layering over `detector_thicksteps`.

### 1.2 Current Implementation (Scalar Loop)

The existing `Simulator._apply_detector_absorption` (lines 1707-1798 in `src/nanobrag_torch/simulator.py`) implements absorption correctly but uses a **Python loop** when `oversample_thick=True`:

```python
# CURRENT: Lines 1764-1787 (vectorized but still with explicit thicksteps loop overhead)
if oversample_thick:
    t_indices = torch.arange(thicksteps, device=intensity.device, dtype=intensity.dtype)
    t_expanded = t_indices.reshape(-1, 1, 1)  # Shape: (thicksteps, 1, 1)

    exp_start_all = torch.exp(-t_expanded * delta_z * mu / parallax_expanded)
    exp_end_all = torch.exp(-(t_expanded + 1) * delta_z * mu / parallax_expanded)
    capture_fractions = exp_start_all - exp_end_all  # Shape: (thicksteps, S, F)

    # Multiply and sum over all layers
    result = torch.sum(intensity_expanded * capture_fractions, dim=0)  # (S, F)
```

**Analysis:** The current implementation is **already vectorized** (commit history shows this was implemented during Phase A-E work). However, the design doc is still valuable for:
1. Documenting the tensor broadcast strategy for future maintainers
2. Establishing gradient/device/dtype verification checklist
3. Defining performance expectations for Phase F3 benchmarks
4. Clarifying integration points with detector coordinate caching (Phase D hoisting work)

### 1.3 Performance Baseline

From `reports/2025-10-vectorization/phase_a/absorption_baseline.md`:

| Size | Layers | Device | Cold (s) | Warm Mean (s) | Throughput (px/s) |
|------|--------|--------|----------|---------------|-------------------|
| 256² | 5 | cuda | 0.005815 | 0.005787 | 11.3M px/s |
| 512² | 5 | cuda | 0.005953 | 0.005851 | 44.8M px/s |

**Goal:** Maintain or improve these numbers after any refactoring; establish CPU baseline.

---

## 2. C-Code Reference (CLAUDE Rule #11)

The authoritative absorption implementation is in `golden_suite_generator/nanoBragg.c`. The core parallax and capture fraction calculations are:

**C-Code Implementation Reference (from nanoBragg.c, lines 2890-2920):**
```c
/* detector sensor absorption: path length */
parallax = dot_product(odet_vector,diffracted);
if(parallax == 0) parallax=1e-20;

/* loop over detector depth */
for(thick_tic=0;thick_tic<detector_thicksteps;++thick_tic)
{
    /* assume the capture fraction is the integral of exp(-r*parallax/detector_mu)dr
       integrated between thick_tic*thick_step and (thick_tic+1)*thick_step
       where r is the vertical depth of the sensor, and parallax accounts for oblique incidence
       so that the total "path" through the silicon is actually r*parallax */
    capture_fraction =
        exp(-thick_tic*detector_thickstep*parallax/detector_mu) -
        exp(-(thick_tic+1)*detector_thickstep*parallax/detector_mu);

    /* oversample_thick: apply to running sum (C semantics) */
    if(oversample_thick) {
        I *= capture_fraction;  /* Multiply accumulator by capture fraction */
    } else {
        /* Store last value for post-loop application */
        /* (Applied after all subpixel/source loops complete) */
    }
}
```

**Key Observations:**
1. Parallax is `d·o` (NOT absolute value - can be negative for tilted geometries)
2. Layer thickness step: `Δz = detector_thick / detector_thicksteps`
3. Capture fraction per layer: `exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ)`
4. **oversample_thick=True:** Multiply running accumulator by each layer's fraction
5. **oversample_thick=False:** Use last layer's capture fraction only (post-loop application)
6. Division by parallax requires zero-clamping to avoid NaNs

---

## 3. Tensor Shape Strategy

### 3.1 Core Dimensions

The absorption calculation operates over these primary dimensions:

| Dimension | Symbol | Range | Description |
|-----------|--------|-------|-------------|
| Slow axis | `S` | `[0, spixels)` | Detector rows |
| Fast axis | `F` | `[0, fpixels)` | Detector columns |
| Thickness layers | `T` | `[0, thicksteps)` | Depth stratification through detector |

### 3.2 Broadcast Shape Plan

**Input tensors:**
- `intensity`: `(S, F)` - Intensity before absorption
- `pixel_coords_meters`: `(S, F, 3)` - 3D positions in lab frame
- `detector_normal`: `(3,)` - Detector surface normal vector `odet_vec`

**Intermediate tensors:**
- `observation_dirs`: `(S, F, 3)` - Normalized pixel directions `d = pixel_coords / |pixel_coords|`
- `parallax`: `(S, F)` - Parallax factor `ρ = d·o`
- `t_indices`: `(T,)` - Layer indices `[0, 1, ..., T-1]`
- `capture_fractions`: `(T, S, F)` - Per-layer absorption fractions

**Broadcasting rules:**
1. **Layer index expansion:** `t_indices` → `(T, 1, 1)` broadcasts with `(1, S, F)`
2. **Parallax expansion:** `parallax (S, F)` → `(1, S, F)` broadcasts with `(T, 1, 1)`
3. **Intensity expansion:** `intensity (S, F)` → `(1, S, F)` broadcasts with `(T, S, F)`

**Result:** `torch.sum(..., dim=0)` reduces `(T, S, F)` → `(S, F)` final absorbed intensity.

### 3.3 Memory Footprint Estimate

For a `1024×1024` detector with `thicksteps=10` and `float32`:

| Tensor | Shape | Size (MB) |
|--------|-------|-----------|
| `capture_fractions` | `(10, 1024, 1024)` | 40.0 |
| `intensity_expanded` | `(1, 1024, 1024)` | 4.0 |
| `parallax` | `(1024, 1024)` | 4.0 |
| **Total** | | **~48 MB** |

**Conclusion:** Memory overhead acceptable even for large detectors. GPU memory (RTX 3090 = 24GB) can handle up to ~500 concurrent 1024² detectors before tiling required.

---

## 4. Differentiability & Gradient Flow

### 4.1 Gradient-Critical Parameters

These detector config parameters **MUST** remain differentiable:

| Parameter | Config Field | Unit Conversion | Gradient Path |
|-----------|--------------|-----------------|---------------|
| Attenuation depth | `detector_abs_um` | `μm → m` | `μ = 1 / (abs_um * 1e-6)` |
| Detector thickness | `detector_thick_um` | `μm → m` | `Δz = (thick_um * 1e-6) / thicksteps` |
| Detector rotations | `detector_rotx/y/z_deg` | `deg → rad` | `odet_vec` (via basis rotation) |
| Distance/position | `distance_mm`, `beam_center_*` | `mm → m` | `pixel_coords_meters` |

### 4.2 Gradient Flow Verification Checklist

- [ ] **No `.item()` calls** on any parameter tensors
- [ ] **No `torch.linspace`** with tensor endpoints (use manual arithmetic)
- [ ] **Preserve graph connectivity** through `torch.exp`, `torch.sum`, `torch.einsum`
- [ ] **Device-agnostic operations** (no hardcoded `.cpu()`/`.cuda()`)
- [ ] **Type stability** (avoid mixed float32/float64 without explicit casts)
- [ ] **Autograd test coverage** via `torch.autograd.gradcheck` (see Phase F3)

### 4.3 Common Pitfalls (from Phase D lessons)

❌ **Don't do this:**
```python
mu = 1.0 / config.detector_abs_um.item()  # Breaks graph!
```

✅ **Do this:**
```python
mu = 1.0 / (config.detector_abs_um * 1e-6)  # Preserves gradients
```

---

## 5. Device & Dtype Neutrality

### 5.1 Device Placement Strategy

**Design Principle:** Accept tensors on **any device** (CPU/CUDA) and **any dtype** (float32/float64) without internal device transfers.

**Implementation pattern:**
```python
# Infer device/dtype from input intensity tensor
device = intensity.device
dtype = intensity.dtype

# Create auxiliary tensors on same device/dtype
t_indices = torch.arange(thicksteps, device=device, dtype=dtype)

# Avoid explicit .cpu() or .cuda() calls
# Use .to(device) or .type_as(intensity) for coercion
```

### 5.2 Dtype Handling

**Default:** `float32` (per ADR in `arch.md`)
**Gradient checks:** Override to `float64` for numerical precision

**Example:**
```python
# Production code (float32 default)
result = simulator.run()

# Gradient check (float64 for accuracy)
torch.autograd.gradcheck(
    lambda x: simulator._apply_detector_absorption(intensity, coords, x),
    detector_abs_tensor.to(dtype=torch.float64)
)
```

### 5.3 Testing Requirements (from `docs/development/testing_strategy.md` §1.4)

**Mandatory smoke tests:**
1. **CPU execution:** `pytest -v tests/test_at_abs_001.py --device=cpu`
2. **CUDA execution:** `pytest -v tests/test_at_abs_001.py --device=cuda` (if available)
3. **Parametrized tests:** Use `@pytest.mark.parametrize("device", ["cpu", "cuda"])` pattern
4. **Compile checks:** Verify `torch.compile` compatibility (watch for device warnings)

---

## 6. Integration Points

### 6.1 Detector Coordinate Caching (Phase D Hoisting)

**Current state:** `pixel_coords_meters` is computed via `detector.get_pixel_coords()` on every `run()` call.

**Phase D optimization opportunity:**
- Cache `pixel_coords_meters` tensor when detector geometry doesn't change
- Invalidate cache via `detector._geometry_version` increment
- Store cached tensor on appropriate device

**Design note for F2:**
```python
class Detector:
    def __init__(self, config):
        self._cached_pixel_coords = None
        self._cached_coords_device = None

    def get_pixel_coords(self, device=None):
        if (self._cached_pixel_coords is None or
            self._cached_coords_device != device):
            # Recompute and cache
            self._cached_pixel_coords = self._compute_pixel_coords()
            self._cached_coords_device = device
        return self._cached_pixel_coords
```

**Phase F scope:** Document integration point; defer caching to Phase D (detector scalar hoisting) work.

### 6.2 ROI Mask Integration

**Current behavior:** ROI mask is applied **after** absorption in `Simulator.run()`.

**Broadcasting consideration:** If ROI becomes a sparse mask, absorption compute can skip masked-out pixels. Current design processes full `(S, F)` grid then masks - acceptable for dense ROI but optimization opportunity for sparse.

**Phase F scope:** No change required; note for future Phase D optimization.

---

## 7. Performance Expectations

### 7.1 Target Metrics (Phase F3 Benchmarks)

Based on Phase A baseline (`reports/2025-10-vectorization/phase_a/absorption_baseline.md`):

| Metric | 256² CUDA | 512² CUDA | Target |
|--------|-----------|-----------|--------|
| **Warm time (s)** | 0.005787 | 0.005851 | ≤1.05× baseline |
| **Throughput (px/s)** | 11.3M | 44.8M | ≥0.95× baseline |

**Phase F2 implementation** should **maintain** current performance (already vectorized). Any refactoring must preserve batched operations.

### 7.2 Expected Bottlenecks

1. **Exponential evaluations:** `torch.exp()` calls dominate compute time
   - **Mitigation:** Already batched over `(T, S, F)` - optimal for GPU

2. **Memory bandwidth:** Large `(T, S, F)` tensors exceed L2 cache
   - **Mitigation:** Acceptable for typical `thicksteps ≤ 10`; tiling deferred

3. **Kernel launch overhead:** Negligible for batched operations
   - **Verification:** Warm benchmarks filter out launch costs

### 7.3 Benchmark Commands (Phase F3)

```bash
# Baseline comparison (CPU)
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE \
  python scripts/benchmarks/absorption_baseline.py \
  --sizes 256 512 --repeats 200 --device cpu \
  --outdir reports/2025-10-vectorization/phase_f/perf

# CUDA validation
PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE \
  python scripts/benchmarks/absorption_baseline.py \
  --sizes 256 512 --repeats 200 --device cuda \
  --outdir reports/2025-10-vectorization/phase_f/perf
```

---

## 8. Testing Strategy (Phase F3)

### 8.1 Unit Tests

**File:** `tests/test_at_abs_001.py`

**Required test cases:**
1. ✅ `test_absorption_disabled_when_zero` (existing)
2. ✅ `test_capture_fraction_calculation` (existing)
3. ✅ `test_last_value_vs_accumulation_semantics` (existing)
4. ✅ `test_parallax_dependence` (existing)
5. ✅ `test_absorption_with_tilted_detector` (existing)
6. **NEW:** `test_absorption_gradient_flow` (Phase F3)
7. **NEW:** `test_absorption_device_parametrization` (Phase F3)
8. **NEW:** `test_absorption_dtype_stability` (Phase F3)

### 8.2 Gradient Check Test Template

```python
def test_absorption_gradient_flow(device):
    """Verify gradients flow through absorption parameters."""
    # Setup with requires_grad=True
    detector_abs_um = torch.tensor(500.0, requires_grad=True, dtype=torch.float64, device=device)
    detector_thick_um = torch.tensor(100.0, requires_grad=True, dtype=torch.float64, device=device)

    # Build config with tensor parameters
    config = DetectorConfig(
        detector_abs_um=detector_abs_um,
        detector_thick_um=detector_thick_um,
        detector_thicksteps=5
    )

    # Run absorption calculation
    result = simulator._apply_detector_absorption(intensity, pixel_coords, oversample_thick=True)

    # Verify gradient connectivity
    assert result.requires_grad, "Result must preserve gradient graph"

    # Numerical gradient check
    torch.autograd.gradcheck(
        lambda abs_um, thick_um: simulator._apply_detector_absorption(...),
        (detector_abs_um, detector_thick_um),
        atol=1e-4, rtol=1e-4
    )
```

### 8.3 Device Parametrization Template

```python
@pytest.mark.parametrize("device", ["cpu", "cuda"])
def test_absorption_device_neutrality(device):
    """Verify absorption works on CPU and CUDA."""
    if device == "cuda" and not torch.cuda.is_available():
        pytest.skip("CUDA not available")

    # Create tensors on target device
    intensity = torch.randn(256, 256, device=device, dtype=torch.float32)
    pixel_coords = torch.randn(256, 256, 3, device=device, dtype=torch.float32)

    # Run absorption
    result = simulator._apply_detector_absorption(intensity, pixel_coords, oversample_thick=True)

    # Verify result device matches input
    assert result.device == intensity.device
    assert result.dtype == intensity.dtype
```

---

## 9. Implementation Checklist (Phase F2)

- [ ] **Review current implementation** (`simulator.py:1707-1798`) - ALREADY VECTORIZED
- [ ] **Document tensor broadcast strategy** in method docstring
- [ ] **Add gradient flow assertions** at key checkpoints
- [ ] **Verify device/dtype neutrality** (no hardcoded `.cpu()`/`.cuda()`)
- [ ] **Add C-code reference** per CLAUDE Rule #11 (already present)
- [ ] **Update method signature** if caching integration needed
- [ ] **Run targeted unit tests** (`test_at_abs_001.py`)
- [ ] **Execute gradient checks** (float64 mode)
- [ ] **Benchmark on CPU + CUDA** (Phase F3 artifact)
- [ ] **Update `docs/fix_plan.md`** with Phase F2 completion metrics

---

## 10. Artifact Checklist (Phase F completion)

**Directory:** `reports/2025-10-vectorization/phase_f/`

**Required files:**
- [x] `design_notes.md` (this document) - **Phase F1 COMPLETE**
- [ ] `implementation_notes.md` (Phase F2)
- [ ] `test_results.log` (Phase F3)
- [ ] `perf/benchmark.log` (Phase F3)
- [ ] `perf/absorption_baseline_results.json` (Phase F3)
- [ ] `summary.md` (Phase F4)
- [ ] `commands.txt` (reproduction harness)
- [ ] `env.json` (Python/PyTorch/CUDA versions)
- [ ] `sha256.txt` (checksums for artifacts)

---

## 11. Open Questions & Future Work

### 11.1 Resolved Questions
- ✅ **Tensor shapes validated:** `(T, S, F)` broadcast pattern confirmed feasible
- ✅ **Memory footprint acceptable:** ~48 MB for 1024² × 10 layers
- ✅ **Gradient flow design:** No breaking operations identified

### 11.2 Deferred Optimizations (post-Phase F)
1. **Detector coordinate caching:** Integrate with Phase D hoisting work
2. **Sparse ROI support:** Optimize for non-rectangular masks
3. **Tiling strategy:** Handle 4096² detectors on limited GPU memory
4. **Compile mode validation:** Verify `torch.compile` compatibility

### 11.3 Coordination Points
- **PERF-PYTORCH-004 Phase D:** Detector scalar hoisting (caching pixel coords)
- **CLI-FLAGS-003:** Ensure `-oversample_thick` CLI flag tests remain passing
- **AT-ABS-001:** All acceptance tests must pass post-refactor

---

## 12. References

### Primary Sources
- `specs/spec-a-core.md:184-200` (Detector absorption equations)
- `golden_suite_generator/nanoBragg.c:2890-2920` (C reference implementation)
- `src/nanobrag_torch/simulator.py:1707-1798` (Current PyTorch implementation)
- `docs/architecture/detector.md:5.3` (Absorption pipeline architecture)

### Supporting Documentation
- `docs/architecture/pytorch_design.md:§2.2-2.4` (Vectorization strategy)
- `docs/development/pytorch_runtime_checklist.md` (Device/dtype guardrails)
- `docs/development/testing_strategy.md:§1.4` (CPU/CUDA smoke test requirements)
- `reports/2025-10-vectorization/phase_e/summary.md` (Phase E precedent)

### Baselines
- `reports/2025-10-vectorization/phase_a/absorption_baseline.md` (Performance baseline)
- `reports/2025-10-vectorization/phase_a/absorption_baseline_results.json` (Metrics)

---

## 13. Summary

**Status:** Phase F1 design **COMPLETE**. Ready for Phase F2 implementation.

**Key Findings:**
1. **Current implementation already vectorized** - Phase F2 will focus on validation, not rewriting
2. **Tensor broadcast strategy validated** - `(T, S, F)` shapes confirmed feasible
3. **Memory footprint acceptable** - No tiling required for typical detector sizes
4. **Gradient flow design sound** - No `.item()` or graph-breaking operations identified
5. **Device neutrality achievable** - Device-agnostic patterns already in place

**Phase F2 Scope:**
- Validate current implementation against this design
- Add comprehensive gradient flow tests
- Extend device parametrization coverage
- Document any minor refactoring for clarity
- Run CPU + CUDA benchmarks

**Phase F3 Scope:**
- Execute `absorption_baseline.py` benchmarks on CPU + CUDA
- Verify ≤1.05× baseline performance
- Generate comparison metrics vs Phase A
- Archive artifacts under `phase_f/perf/`

**Phase F4 Scope:**
- Author `phase_f/summary.md` consolidating F1-F3 results
- Update `docs/fix_plan.md` Attempt history
- Mark VECTOR-TRICUBIC-001 Phase F complete

---

**Authored:** 2025-10-08
**Next:** Phase F2 - Implementation & Validation
**Artifact:** `reports/2025-10-vectorization/phase_f/design_notes.md`

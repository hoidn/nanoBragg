# PIXEL-BATCH-001: Implement Simulator-Level Pixel Batching for Memory Efficiency

## Context

- **Initiative**: PIXEL-BATCH-001 — Implement the existing but unused `pixel_batch_size` parameter to enable memory-efficient execution on constrained GPUs
- **Source**: `inbox/chunked_interpolation_request_2025_12_09.md` from DBEX maintainers
- **Priority**: MEDIUM — blocks Stage-A smoke tests on 24GB GPUs with mosaic domains
- **Scope**: Simulator-level orchestration change; no kernel modifications required

---

## Problem Statement

### Symptom

OOM on 24GB GPUs when running Stage-A refinement with 1024² detector and 9 mosaic domains:

```
torch.OutOfMemoryError: CUDA out of memory. Tried to allocate 4.50 GiB.
GPU 0 has a total capacity of 23.56 GiB of which 3.44 GiB is free.
```

### Root Cause

The current implementation calls `_compute_physics_for_position()` **once** with all pixels, which flows through to `Crystal._tricubic_interpolation()` creating massive intermediate tensors:

```python
# crystal.py:427-431 - creates (B, 4, 4, 4) tensor where B = S×F×phi×mosaic
sub_Fhkl = self.hkl_data[
    h_array_grid[:, :, None, None],  # (B, 4, 1, 1)
    k_array_grid[:, None, :, None],  # (B, 1, 4, 1)
    l_array_grid[:, None, None, :]   # (B, 1, 1, 4)
]  # Result: (9.44M, 4, 4, 4) = 604M floats = 2.4 GB
```

### Memory Scaling

| Detector | Mosaic | B (batch) | sub_Fhkl | Total Peak |
|----------|--------|-----------|----------|------------|
| 512² | 1 | 262K | 64 MB | ~1 GB |
| 1024² | 1 | 1.05M | 256 MB | ~3 GB |
| 1024² | 9 | 9.44M | 2.4 GB | ~18 GB |
| 2048² | 9 | 37.7M | 9.6 GB | >50 GB |

### Existing (Unused) Mitigation

`Simulator.run()` already declares `pixel_batch_size: Optional[int] = None` but **never implements it**:

```python
def run(
    self,
    pixel_batch_size: Optional[int] = None,  # Declared but unused!
    ...
):
    """
    Args:
        pixel_batch_size: Optional batching for memory management.  # Documented!
    """
    # ... implementation ignores pixel_batch_size entirely ...
```

---

## Solution Design

### Architectural Principle

**Orchestration-level batching is permitted; kernel-level loops are forbidden.**

The vectorization mandate in `pytorch_design.md` targets computational kernels (e.g., `_tricubic_interpolation`, `compute_physics_for_position`). Memory management at the `Simulator.run()` level is an orchestration concern, not a vectorization violation.

Key distinction:
- **Kernel loops (FORBIDDEN):** Python iteration inside physics/interpolation code
- **Orchestration batching (PERMITTED):** `Simulator.run()` processes pixel chunks, each chunk fully vectorized

### Implementation Strategy

Process detector in row-wise chunks along the slow axis:

```
Full detector (S, F):        Chunked execution:
┌─────────────────────┐      ┌─────────────────────┐
│                     │      │ Chunk 0 (rows 0-255)│ → full vectorization
│                     │      ├─────────────────────┤
│   All S×F pixels    │  →   │ Chunk 1 (rows 256-511)│ → full vectorization
│   processed at once │      ├─────────────────────┤
│                     │      │ Chunk 2 (rows 512-767)│ → full vectorization
│                     │      ├─────────────────────┤
└─────────────────────┘      │ Chunk 3 (rows 768-1023)│ → full vectorization
                             └─────────────────────┘
```

Each chunk:
- Contains `pixel_batch_size` rows × F columns × all phi/mosaic/oversample
- Is fully vectorized (no Python loops in physics computation)
- Produces independent pixel intensities (no cross-chunk reduction needed)

---

## Implementation Plan

### Phase 0: Documentation Updates

**Goal:** Clarify architectural intent and document user-facing feature before implementation

| ID | Task | File | Status |
|----|------|------|--------|
| P0.1 | Add Memory Management section | `docs/architecture/pytorch_design.md` | [ ] |
| P0.2 | Clarify orchestration vs kernel batching | `CLAUDE.md` | [ ] |
| P0.3 | Add memory checklist items | `docs/development/pytorch_runtime_checklist.md` | [ ] |
| P0.4 | Add chunking validation tests section | `docs/development/testing_strategy.md` | [ ] |
| P0.5 | Add `--pixel-batch-size` to config map | `docs/development/c_to_pytorch_config_map.md` | [ ] |
| P0.6 | Add memory management to performance guide | `docs/user/performance.md` | [ ] |
| P0.7 | Update CLI reference | `README_PYTORCH.md` | [ ] |
| P0.8 | Update CLI quickstart | `docs/user/cli_quickstart.md` | [ ] |

**P0.1 Content** (`pytorch_design.md`, new section after 1.1.5):

```markdown
## 1.2 Memory Management & Batched Execution

### 1.2.1 Design Principle: Orchestration vs Kernel Batching

The vectorization mandate ("no Python loops") applies to **computational kernels**
(e.g., `_tricubic_interpolation`, `compute_physics_for_position`).

**Orchestration-level batching is permitted** when memory constraints require
processing the detector in tiles. The distinction:

- **Kernel loops (FORBIDDEN):** Python iteration inside physics/interpolation code
- **Orchestration batching (PERMITTED):** Simulator.run() processes pixel chunks,
  each chunk fully vectorized

### 1.2.2 Memory Scaling Model

Peak memory for tricubic interpolation scales as:

```
M_peak ≈ B × 64 × sizeof(dtype) × k_autograd
where:
  B = S × F × N_phi × N_mos × oversample²
  k_autograd ≈ 3-4 (forward intermediates + gradient buffers)
```

Reference values (float32, k=4):
| Config | B | Peak Memory |
|--------|---|-------------|
| 1024², 1 mosaic | 1.05M | ~1 GB |
| 1024², 9 mosaic | 9.44M | ~10 GB |
| 2048², 9 mosaic | 37.7M | ~40 GB |

### 1.2.3 Chunking Strategy

When `pixel_batch_size` is specified, `Simulator.run()` processes the detector
in row-wise chunks:

1. Divide slow axis into chunks of `pixel_batch_size` rows
2. For each chunk, run full vectorized physics (all phi/mosaic/oversample)
3. Assign results to pre-allocated output tensor
4. Gradients accumulate correctly through sliced assignment

### 1.2.4 torch.compile Interaction

Chunked execution disables `torch.compile` by default to avoid graph recompilation
overhead. For performance-critical chunked paths, use uniform chunk sizes with
padding to enable single-graph compilation.
```

**P0.2 Content** (`CLAUDE.md`, update to PyTorch Runtime Guardrails):

```markdown
- **Vectorization is mandatory** for computational kernels (physics, interpolation).
  Do not reintroduce Python loops inside `compute_physics_for_position`,
  `_tricubic_interpolation`, or similar functions.

- **Orchestration-level batching is permitted:** When memory constraints require it,
  `Simulator.run()` may process the detector in chunks via `pixel_batch_size`.
  Each chunk remains fully vectorized. This is NOT a violation of the vectorization
  mandate—the mandate targets kernel-level loops, not memory management.
```

**P0.3 Content** (`pytorch_runtime_checklist.md`, new section 6):

```markdown
## 6. Memory Management

- **Estimate peak memory** before running large simulations:
  ```
  B = S × F × phi_steps × mosaic_domains × oversample²
  Peak ≈ B × 300 bytes (float32 with autograd)
  ```

- **Use `pixel_batch_size`** when peak memory exceeds available GPU RAM:
  ```python
  # For 24GB GPU with 1024² detector and 9 mosaic domains:
  simulator.run(pixel_batch_size=128)  # Process 128 rows at a time

  # For 12GB GPU:
  simulator.run(pixel_batch_size=64)
  ```

- **Monitor actual usage** with `torch.cuda.max_memory_allocated()` during development

- **Chunking does NOT violate vectorization mandate** — each chunk is fully vectorized;
  this is orchestration-level memory management, not kernel-level iteration

- **Chunking disables torch.compile** to avoid graph recompilation overhead;
  this is acceptable for memory-constrained scenarios
```

**P0.4 Content** (`testing_strategy.md`, add to Section 2.5 Parallel Validation Matrix):

```markdown
### 2.5.7 Memory Management Validation

Pixel batching must produce identical results to full vectorization and maintain
gradient correctness.

| Test ID | Test Name | Purpose | Pass Criteria |
|---------|-----------|---------|---------------|
| MEM-001 | Chunked parity | Verify chunked == non-chunked | Bitwise identical (float64) |
| MEM-002 | Chunk size sweep | Test various chunk sizes | All sizes produce same result |
| MEM-003 | Gradient parity | Verify gradients match | `torch.allclose(rtol=1e-10)` |
| MEM-004 | Gradcheck chunked | gradcheck with chunking | Passes with `rtol=0.05` |
| MEM-005 | Memory ceiling | Verify peak < threshold | < 8GB for chunk=128, 1024² det |

**Commands:**
```bash
# Parity tests
env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_pixel_batching.py::TestPixelBatchingParity

# Gradient tests
env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_pixel_batching.py::TestPixelBatchingGradients
```
```

**P0.5 Content** (`c_to_pytorch_config_map.md`, add to Detector Parameters table):

```markdown
### Simulator Parameters (PyTorch-only)

| CLI Flag | PyTorch Config/Method | Default | Notes |
|----------|----------------------|---------|-------|
| `--pixel-batch-size N` | `Simulator.run(pixel_batch_size=N)` | None | Process detector in chunks of N rows. Reduces peak memory. No C equivalent. |
```

**P0.6 Content** (`docs/user/performance.md`, new file or new section):

```markdown
## Memory Management

### Understanding Memory Usage

Peak GPU memory scales with the total number of query points:

```
B = detector_rows × detector_cols × phi_steps × mosaic_domains × oversample²
Peak Memory ≈ B × 300 bytes (float32)
```

Example configurations:

| Detector | Mosaic | Oversample | B | Peak Memory |
|----------|--------|------------|---|-------------|
| 512² | 1 | 1 | 262K | ~80 MB |
| 1024² | 1 | 1 | 1.05M | ~300 MB |
| 1024² | 9 | 1 | 9.44M | ~3 GB |
| 1024² | 9 | 3 | 85M | ~25 GB |

### Using Pixel Batching

For memory-constrained GPUs, use `--pixel-batch-size` to process the detector in chunks:

```bash
# Full vectorization (default) - fastest, highest memory
nanobrag-torch --detpixels 1024 --mosaic_domains 9 ...

# Chunked execution - lower memory, slightly slower
nanobrag-torch --detpixels 1024 --mosaic_domains 9 --pixel-batch-size 128 ...
```

**Recommended chunk sizes:**

| GPU Memory | Chunk Size |
|------------|------------|
| 8 GB | 32-64 |
| 12 GB | 64-128 |
| 24 GB | 128-256 |
| 40+ GB | None (full vectorization) |

### Programmatic Memory Estimation

```python
memory_info = simulator.estimate_memory()
print(f"Batch size: {memory_info['batch_size']}")
print(f"Peak memory: {memory_info['tricubic_peak_gb']:.1f} GB")
print(f"Recommended chunk size: {memory_info['recommended_chunk_size']}")

if not memory_info['full_vectorization_ok']:
    result = simulator.run(pixel_batch_size=memory_info['recommended_chunk_size'])
else:
    result = simulator.run()
```

### Performance Impact

Chunked execution is slightly slower than full vectorization due to:
- Multiple kernel launches (one per chunk)
- Disabled `torch.compile` optimization

Typical overhead: 10-30% slowdown. This is acceptable when the alternative is OOM.
```

**P0.7 Content** (`README_PYTORCH.md`, add to CLI reference section):

```markdown
### Memory Management Options

| Flag | Description |
|------|-------------|
| `--pixel-batch-size N` | Process detector in chunks of N rows. Reduces peak GPU memory at cost of slightly slower execution. Recommended for large detectors or many mosaic domains on memory-constrained GPUs. |

**Example:**
```bash
# OOM on 24GB GPU:
nanobrag-torch --detpixels 2048 --mosaic_domains 9 ...

# Works with chunking:
nanobrag-torch --detpixels 2048 --mosaic_domains 9 --pixel-batch-size 128 ...
```
```

**P0.8 Content** (`docs/user/cli_quickstart.md`, add to advanced usage section):

```markdown
### Running on Memory-Constrained GPUs

If you encounter `CUDA out of memory` errors, use pixel batching:

```bash
# Instead of:
nanobrag-torch -detpixels 1024 -mosaic_domains 9 ...

# Use:
nanobrag-torch -detpixels 1024 -mosaic_domains 9 --pixel-batch-size 128 ...
```

The `--pixel-batch-size` option processes the detector in chunks, reducing peak
memory usage while producing identical results.
```

---

### Phase 1: Core Implementation

**Goal:** Implement `pixel_batch_size` in `Simulator.run()`

| ID | Task | Status |
|----|------|--------|
| P1.1 | Add `_run_chunked()` method to Simulator | [ ] |
| P1.2 | Add `_compute_chunk()` helper for single chunk | [ ] |
| P1.3 | Route to chunked path when `pixel_batch_size` specified | [ ] |
| P1.4 | Disable torch.compile in chunked mode | [ ] |
| P1.5 | Handle last chunk padding (if smaller than batch_size) | [ ] |

**P1.1-P1.3 Implementation** (`simulator.py`):

```python
def run(
    self,
    pixel_batch_size: Optional[int] = None,
    ...
) -> torch.Tensor:
    """
    Run the diffraction simulation.

    Args:
        pixel_batch_size: If specified, process detector in chunks of this many
            rows (slow axis). Reduces peak memory at cost of multiple kernel
            launches. Set to None (default) for full vectorization.

            Memory guidance:
            - None: Full vectorization, peak memory ≈ B × 300 bytes
            - 256: ~256 × F × phi × mosaic × 300 bytes per chunk
            - 128: Half the above, for very constrained GPUs
    """
    # ... existing setup code (lines 838-948) unchanged ...

    S, F, _ = pixel_coords_meters.shape

    # Route to chunked or full path
    if pixel_batch_size is not None and pixel_batch_size < S:
        return self._run_chunked(
            pixel_batch_size=pixel_batch_size,
            pixel_coords_meters=pixel_coords_meters,
            rot_a=rot_a, rot_b=rot_b, rot_c=rot_c,
            rot_a_star=rot_a_star, rot_b_star=rot_b_star, rot_c_star=rot_c_star,
            n_sources=n_sources,
            source_directions=source_directions,
            source_wavelengths_A=source_wavelengths_A,
            source_weights=source_weights,
            steps=steps,
            oversample=oversample,
            oversample_omega=oversample_omega,
            roi_mask=roi_mask,
        )

    # ... existing full-vectorization path unchanged ...


def _run_chunked(
    self,
    pixel_batch_size: int,
    pixel_coords_meters: torch.Tensor,
    rot_a: torch.Tensor,
    rot_b: torch.Tensor,
    rot_c: torch.Tensor,
    rot_a_star: torch.Tensor,
    rot_b_star: torch.Tensor,
    rot_c_star: torch.Tensor,
    n_sources: int,
    source_directions: Optional[torch.Tensor],
    source_wavelengths_A: Optional[torch.Tensor],
    source_weights: Optional[torch.Tensor],
    steps: int,
    oversample: int,
    oversample_omega: bool,
    roi_mask: Optional[torch.Tensor],
) -> torch.Tensor:
    """
    Process detector in row-wise chunks for memory efficiency.

    Each chunk is fully vectorized—this is orchestration-level batching,
    not a violation of the kernel vectorization mandate.

    Memory scaling per chunk:
        Peak ≈ pixel_batch_size × F × phi × mosaic × oversample² × 300 bytes
    """
    S, F, _ = pixel_coords_meters.shape

    # Pre-allocate output tensor
    output = torch.zeros(S, F, device=self.device, dtype=self.dtype)

    # Process chunks along slow axis
    for s_start in range(0, S, pixel_batch_size):
        s_end = min(s_start + pixel_batch_size, S)

        # Extract chunk coordinates
        chunk_coords = pixel_coords_meters[s_start:s_end, :, :]  # (chunk_S, F, 3)

        # Extract chunk ROI mask if present
        chunk_roi = roi_mask[s_start:s_end, :] if roi_mask is not None else None

        # Compute chunk (reuses existing physics path)
        chunk_result = self._compute_chunk_intensity(
            pixel_coords_meters=chunk_coords,
            rot_a=rot_a, rot_b=rot_b, rot_c=rot_c,
            rot_a_star=rot_a_star, rot_b_star=rot_b_star, rot_c_star=rot_c_star,
            n_sources=n_sources,
            source_directions=source_directions,
            source_wavelengths_A=source_wavelengths_A,
            source_weights=source_weights,
            steps=steps,
            oversample=oversample,
            oversample_omega=oversample_omega,
        )

        # Apply ROI mask if present
        if chunk_roi is not None:
            chunk_result = chunk_result * chunk_roi

        # Assign to output (preserves gradient graph via sliced assignment)
        output[s_start:s_end, :] = chunk_result

    return output


def _compute_chunk_intensity(
    self,
    pixel_coords_meters: torch.Tensor,
    rot_a: torch.Tensor,
    rot_b: torch.Tensor,
    rot_c: torch.Tensor,
    rot_a_star: torch.Tensor,
    rot_b_star: torch.Tensor,
    rot_c_star: torch.Tensor,
    n_sources: int,
    source_directions: Optional[torch.Tensor],
    source_wavelengths_A: Optional[torch.Tensor],
    source_weights: Optional[torch.Tensor],
    steps: int,
    oversample: int,
    oversample_omega: bool,
) -> torch.Tensor:
    """
    Compute intensity for a chunk of pixels.

    This is the core physics computation, fully vectorized over:
    - All pixels in chunk (chunk_S × F)
    - All phi steps
    - All mosaic domains
    - All oversample positions

    Returns:
        Tensor of shape (chunk_S, F) with scaled intensities
    """
    # Convert to Angstroms for physics
    pixel_coords_angstroms = pixel_coords_meters * 1e10

    # Use EAGER mode for chunked execution (avoid recompilation per chunk)
    # The pure function is used directly, not the compiled version
    compute_fn = compute_physics_for_position

    # Compute physics (same logic as non-chunked path)
    if n_sources > 1:
        incident_dirs_batched = -source_directions
        wavelengths_batched = source_wavelengths_A

        intensity, _ = compute_fn(
            pixel_coords_angstroms, rot_a, rot_b, rot_c,
            rot_a_star, rot_b_star, rot_c_star,
            incident_beam_direction=incident_dirs_batched,
            wavelength=wavelengths_batched,
            source_weights=source_weights,
            default_F=self.crystal.config.default_F,
            dmin=self.dmin,
            crystal_get_structure_factor=self.crystal.get_structure_factor,
            N_cells_a=self.crystal.config.N_cells[0],
            N_cells_b=self.crystal.config.N_cells[1],
            N_cells_c=self.crystal.config.N_cells[2],
            crystal_shape=self.crystal.config.shape,
            crystal_fudge=self.crystal.config.fudge,
            apply_polarization=not self.beam_config.nopolar,
            kahn_factor=self.kahn_factor,
            polarization_axis=self.polarization_axis,
        )
    else:
        intensity, _ = compute_fn(
            pixel_coords_angstroms, rot_a, rot_b, rot_c,
            rot_a_star, rot_b_star, rot_c_star,
            incident_beam_direction=self.incident_beam_direction,
            wavelength=self.wavelength,
            source_weights=None,
            default_F=self.crystal.config.default_F,
            dmin=self.dmin,
            crystal_get_structure_factor=self.crystal.get_structure_factor,
            N_cells_a=self.crystal.config.N_cells[0],
            N_cells_b=self.crystal.config.N_cells[1],
            N_cells_c=self.crystal.config.N_cells[2],
            crystal_shape=self.crystal.config.shape,
            crystal_fudge=self.crystal.config.fudge,
            apply_polarization=not self.beam_config.nopolar,
            kahn_factor=self.kahn_factor,
            polarization_axis=self.polarization_axis,
        )

    # Apply solid angle correction
    pixel_squared_sum = torch.sum(
        pixel_coords_angstroms * pixel_coords_angstroms, dim=-1, keepdim=True
    ).clamp_min(1e-12)
    pixel_magnitudes = torch.sqrt(pixel_squared_sum)
    airpath_m = pixel_magnitudes.squeeze(-1) * 1e-10

    close_distance_m = torch.as_tensor(
        self.detector.close_distance,
        device=airpath_m.device,
        dtype=airpath_m.dtype
    )
    pixel_size_m = torch.as_tensor(
        self.detector.pixel_size,
        device=airpath_m.device,
        dtype=airpath_m.dtype
    )

    if self.detector.config.point_pixel:
        omega_pixel = 1.0 / (airpath_m * airpath_m)
    else:
        omega_pixel = (
            (pixel_size_m * pixel_size_m)
            / (airpath_m * airpath_m)
            * close_distance_m
            / airpath_m
        )

    # Apply omega and scaling
    scaled_intensity = intensity * omega_pixel

    # Apply fluence and normalization
    r_e_m = 2.8179403262e-15  # classical electron radius in meters
    fluence = self.fluence if hasattr(self, 'fluence') else self.beam_config.fluence

    final_intensity = r_e_m * r_e_m * fluence * scaled_intensity / steps

    return final_intensity
```

**P1.4 torch.compile handling:**

The chunked path uses `compute_physics_for_position` directly (not `_compiled_compute_physics`) to avoid graph recompilation for each chunk shape. This is acceptable because:
- Chunked mode is for memory-constrained scenarios where raw throughput is secondary
- Each chunk is still fully vectorized on GPU
- Compilation overhead would exceed any benefit for varying chunk sizes

---

### Phase 2: Parity Testing

**Goal:** Verify chunked execution produces identical results to full vectorization

| ID | Task | Status |
|----|------|--------|
| P2.1 | Create `tests/test_pixel_batching.py` | [ ] |
| P2.2 | Test bitwise parity (chunked vs full) | [ ] |
| P2.3 | Test various chunk sizes (64, 128, 256, 512) | [ ] |
| P2.4 | Test edge cases (chunk_size > S, chunk_size = 1) | [ ] |
| P2.5 | Test with mosaic domains (1, 3, 9) | [ ] |

**P2.1-P2.2 Test Implementation:**

```python
# tests/test_pixel_batching.py
"""
Parity tests for pixel batching implementation.

Validates that chunked execution produces identical results to full vectorization.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
os.environ['NANOBRAGG_DISABLE_COMPILE'] = '1'

import torch
import pytest
import numpy as np

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.simulator import Simulator


class TestPixelBatchingParity:
    """Verify chunked execution matches full vectorization."""

    @pytest.fixture
    def base_configs(self):
        """Standard test configuration."""
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=100.0,
            mosaic_spread_deg=0.0,
            mosaic_domains=1,
        )
        detector_config = DetectorConfig(
            spixels=256,
            fpixels=256,
            pixel_size_mm=0.1,
            distance_mm=100.0,
        )
        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e28,
        )
        return crystal_config, detector_config, beam_config

    @pytest.mark.parametrize("chunk_size", [64, 128, 256])
    def test_chunked_matches_full(self, base_configs, chunk_size):
        """Chunked execution should produce identical results to full."""
        crystal_config, detector_config, beam_config = base_configs

        device = torch.device('cpu')
        dtype = torch.float64  # Use float64 for exact comparison

        crystal = Crystal(config=crystal_config, beam_config=beam_config,
                         device=device, dtype=dtype)
        detector = Detector(config=detector_config, device=device, dtype=dtype)
        simulator = Simulator(crystal=crystal, detector=detector,
                             beam_config=beam_config, device=device, dtype=dtype)

        # Run full vectorization
        result_full = simulator.run(pixel_batch_size=None)

        # Run chunked
        result_chunked = simulator.run(pixel_batch_size=chunk_size)

        # Verify bitwise equality
        assert torch.equal(result_full, result_chunked), \
            f"Chunked (size={chunk_size}) differs from full vectorization"

    @pytest.mark.parametrize("mosaic_domains", [1, 3, 9])
    def test_chunked_with_mosaic(self, base_configs, mosaic_domains):
        """Chunked execution works correctly with mosaic domains."""
        crystal_config, detector_config, beam_config = base_configs
        crystal_config = CrystalConfig(
            **{**crystal_config.__dict__, 'mosaic_domains': mosaic_domains}
        )

        device = torch.device('cpu')
        dtype = torch.float64

        crystal = Crystal(config=crystal_config, beam_config=beam_config,
                         device=device, dtype=dtype)
        detector = Detector(config=detector_config, device=device, dtype=dtype)
        simulator = Simulator(crystal=crystal, detector=detector,
                             beam_config=beam_config, device=device, dtype=dtype)

        result_full = simulator.run(pixel_batch_size=None)
        result_chunked = simulator.run(pixel_batch_size=64)

        assert torch.equal(result_full, result_chunked), \
            f"Chunked differs from full with {mosaic_domains} mosaic domains"

    def test_chunk_size_larger_than_detector(self, base_configs):
        """chunk_size > S should fall back to full vectorization."""
        crystal_config, detector_config, beam_config = base_configs

        device = torch.device('cpu')
        dtype = torch.float64

        crystal = Crystal(config=crystal_config, beam_config=beam_config,
                         device=device, dtype=dtype)
        detector = Detector(config=detector_config, device=device, dtype=dtype)
        simulator = Simulator(crystal=crystal, detector=detector,
                             beam_config=beam_config, device=device, dtype=dtype)

        result_full = simulator.run(pixel_batch_size=None)
        result_large_chunk = simulator.run(pixel_batch_size=1000)  # > 256

        assert torch.equal(result_full, result_large_chunk)

    def test_chunk_size_one(self, base_configs):
        """chunk_size=1 should work (extreme case)."""
        crystal_config, detector_config, beam_config = base_configs
        # Use smaller detector for speed
        detector_config = DetectorConfig(
            spixels=32, fpixels=32,
            pixel_size_mm=0.1, distance_mm=100.0,
        )

        device = torch.device('cpu')
        dtype = torch.float64

        crystal = Crystal(config=crystal_config, beam_config=beam_config,
                         device=device, dtype=dtype)
        detector = Detector(config=detector_config, device=device, dtype=dtype)
        simulator = Simulator(crystal=crystal, detector=detector,
                             beam_config=beam_config, device=device, dtype=dtype)

        result_full = simulator.run(pixel_batch_size=None)
        result_single = simulator.run(pixel_batch_size=1)

        assert torch.equal(result_full, result_single)
```

---

### Phase 3: Gradient Testing

**Goal:** Verify gradients accumulate correctly across chunks

| ID | Task | Status |
|----|------|--------|
| P3.1 | Test gradient parity (chunked vs full) | [ ] |
| P3.2 | Test gradcheck passes with chunking | [ ] |
| P3.3 | Test multi-parameter gradients | [ ] |

**P3.1-P3.2 Test Implementation:**

```python
# tests/test_pixel_batching.py (continued)

class TestPixelBatchingGradients:
    """Verify gradient correctness with chunked execution."""

    def test_gradient_parity(self):
        """Gradients should match between chunked and full execution."""
        device = torch.device('cpu')
        dtype = torch.float64

        # Create differentiable parameter
        cell_a = torch.tensor(100.0, dtype=dtype, device=device, requires_grad=True)

        crystal_config = CrystalConfig(
            cell_a=cell_a,
            cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(3, 3, 3),
            default_F=100.0,
        )
        detector_config = DetectorConfig(
            spixels=64, fpixels=64,
            pixel_size_mm=0.1, distance_mm=100.0,
        )
        beam_config = BeamConfig(wavelength_A=1.0, fluence=1e28)

        # Full vectorization gradient
        crystal = Crystal(config=crystal_config, beam_config=beam_config,
                         device=device, dtype=dtype)
        detector = Detector(config=detector_config, device=device, dtype=dtype)
        simulator = Simulator(crystal=crystal, detector=detector,
                             beam_config=beam_config, device=device, dtype=dtype)

        result_full = simulator.run(pixel_batch_size=None)
        loss_full = result_full.sum()
        loss_full.backward()
        grad_full = cell_a.grad.clone()

        # Reset gradient
        cell_a.grad = None

        # Chunked gradient (need fresh simulator to reset internal state)
        crystal2 = Crystal(config=crystal_config, beam_config=beam_config,
                          device=device, dtype=dtype)
        detector2 = Detector(config=detector_config, device=device, dtype=dtype)
        simulator2 = Simulator(crystal=crystal2, detector=detector2,
                              beam_config=beam_config, device=device, dtype=dtype)

        result_chunked = simulator2.run(pixel_batch_size=16)
        loss_chunked = result_chunked.sum()
        loss_chunked.backward()
        grad_chunked = cell_a.grad.clone()

        # Gradients should match
        assert torch.allclose(grad_full, grad_chunked, rtol=1e-10), \
            f"Gradient mismatch: full={grad_full.item()}, chunked={grad_chunked.item()}"

    def test_gradcheck_with_chunking(self):
        """torch.autograd.gradcheck should pass with chunked execution."""
        device = torch.device('cpu')
        dtype = torch.float64

        def loss_fn(cell_a_param):
            crystal_config = CrystalConfig(
                cell_a=cell_a_param,
                cell_b=100.0, cell_c=100.0,
                cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
                N_cells=(2, 2, 2),
                default_F=100.0,
            )
            detector_config = DetectorConfig(
                spixels=32, fpixels=32,
                pixel_size_mm=0.1, distance_mm=100.0,
            )
            beam_config = BeamConfig(wavelength_A=1.0, fluence=1e28)

            crystal = Crystal(config=crystal_config, beam_config=beam_config,
                             device=device, dtype=dtype)
            detector = Detector(config=detector_config, device=device, dtype=dtype)
            simulator = Simulator(crystal=crystal, detector=detector,
                                 beam_config=beam_config, device=device, dtype=dtype)

            return simulator.run(pixel_batch_size=8).sum()

        cell_a_test = torch.tensor(100.0, dtype=dtype, device=device, requires_grad=True)

        # This should pass
        assert torch.autograd.gradcheck(loss_fn, cell_a_test, eps=1e-6, rtol=0.05)
```

---

### Phase 4: CLI Integration

**Goal:** Expose `--pixel-batch-size` in command-line interface

| ID | Task | Status |
|----|------|--------|
| P4.1 | Add `--pixel-batch-size` argument to CLI | [ ] |
| P4.2 | Pass through to Simulator.run() | [ ] |
| P4.3 | Add to ExperimentModel.forward() | [ ] |
| P4.4 | Update CLI documentation | [ ] |

**P4.1 Implementation** (`__main__.py`):

```python
parser.add_argument(
    '--pixel-batch-size',
    type=int,
    default=None,
    metavar='N',
    help='Process detector in chunks of N rows. Reduces memory usage for large '
         'detectors or many mosaic domains. Recommended: 128-256 for 24GB GPU, '
         '64-128 for 12GB GPU. Default: None (full vectorization).'
)
```

---

### Phase 5: Memory Profiling & Documentation

**Goal:** Provide memory estimation and usage guidance

| ID | Task | Status |
|----|------|--------|
| P5.1 | Add `estimate_memory()` helper to Simulator | [ ] |
| P5.2 | Add memory guidance to user documentation | [ ] |
| P5.3 | Create memory profiling test | [ ] |

**P5.1 Implementation:**

```python
def estimate_memory(self) -> dict:
    """
    Estimate peak GPU memory for current configuration.

    Returns:
        dict with keys:
        - batch_size: Total query points (S × F × phi × mosaic × oversample²)
        - tricubic_peak_gb: Estimated peak for tricubic interpolation
        - recommended_chunk_size: Suggested pixel_batch_size for 24GB GPU
    """
    S = self.detector.config.spixels
    F = self.detector.config.fpixels
    phi = self.crystal.config.phi_steps
    mos = self.crystal.config.mosaic_domains
    over = self.detector.config.oversample

    B = S * F * phi * mos * over * over
    bytes_per_element = 4 if self.dtype == torch.float32 else 8

    # Peak memory estimate: B × 64 (neighborhood) × dtype × 4 (autograd overhead)
    tricubic_peak = B * 64 * bytes_per_element * 4

    # Recommended chunk size for 24GB GPU (target ~8GB peak)
    target_memory = 8e9  # 8 GB
    target_B = target_memory / (64 * bytes_per_element * 4)
    recommended_chunk = max(1, int(target_B / (F * phi * mos * over * over)))

    return {
        'batch_size': B,
        'tricubic_peak_gb': tricubic_peak / 1e9,
        'recommended_chunk_size': min(S, recommended_chunk),
        'full_vectorization_ok': tricubic_peak < 16e9,  # < 16GB
    }
```

---

## Verification Commands

```bash
# Phase 2: Parity tests
env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_pixel_batching.py::TestPixelBatchingParity

# Phase 3: Gradient tests
env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/test_pixel_batching.py::TestPixelBatchingGradients

# Full test suite regression
env KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 \
  pytest -v tests/

# Memory profiling (manual)
python -c "
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.simulator import Simulator

cc = CrystalConfig(cell_a=100, cell_b=100, cell_c=100, cell_alpha=90, cell_beta=90, cell_gamma=90,
                   N_cells=(5,5,5), default_F=100, mosaic_domains=9)
dc = DetectorConfig(spixels=1024, fpixels=1024, pixel_size_mm=0.1, distance_mm=100)
bc = BeamConfig(wavelength_A=1.0, fluence=1e28)

c = Crystal(config=cc, beam_config=bc)
d = Detector(config=dc)
s = Simulator(crystal=c, detector=d, beam_config=bc)

print(s.estimate_memory())
"
```

---

## Exit Criteria

| Criterion | Metric | Status |
|-----------|--------|--------|
| Parity | Chunked == Full (bitwise, float64) | [ ] |
| Gradients | gradcheck passes with chunking | [ ] |
| Memory | 1024² + 9 mosaic fits in 24GB with chunk=128 | [ ] |
| Regression | All existing tests pass | [ ] |
| Documentation | All Phase 0 docs updated | [ ] |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Numerical drift from chunking | Very Low | High | Chunks are independent; no different math |
| Gradient accumulation bugs | Medium | High | Explicit parity tests; careful testing |
| Performance regression (small detectors) | Low | Low | Chunking is opt-in; full path unchanged |
| torch.compile interaction | Medium | Medium | Disable compile in chunked mode |

---

## Dependencies

- `docs/architecture/pytorch_design.md` — Vectorization strategy documentation
- `docs/development/testing_strategy.md` — Test validation requirements
- `src/nanobrag_torch/simulator.py` — Core implementation target
- `tests/test_gradients.py` — Existing gradient test infrastructure

---

## References

- **Request**: `inbox/chunked_interpolation_request_2025_12_09.md`
- **Architecture**: `docs/architecture/pytorch_design.md` §1.1.1 (Tricubic Pipeline)
- **Memory Analysis**: Conversation analysis (2025-12-09)
- **Related**: `plans/active/dbex-gradient-blockers.md` (gradient issues, separate scope)

# Phase C Documentation Updates Checklist — DETERMINISM-001

**Date:** 2025-10-11T05:29:20Z
**Phase:** C (Documentation & Remediation Blueprint)
**Purpose:** Enumerate concrete documentation edits required to capture the RNG seed contract and pointer-side-effect semantics.

---

## Overview

The C-side seed contract (documented in `reports/determinism-callchain/phase_b3/20251011T051737Z/c_seed_flow.md`) relies on **pointer side effects** to propagate seed state through the RNG pipeline. This non-obvious behavior must be explicitly documented in:

1. Architecture documentation (reference guide for implementers)
2. Source code docstrings (inline guidance for developers)
3. Testing strategy (workflow for determinism validation)

---

## 1. Architecture Documentation

### 1.1 `docs/architecture/c_function_reference.md`

**Target Section:** RNG / Random Number Generation (create if missing)

**Required Content:**

#### 1.1.1 RNG Algorithm Overview
Add subsection documenting:
- Algorithm: Minimal Standard LCG (Park & Miller 1988) + Bays-Durham shuffle
- Implementation: `ran1()` function (lines 4143-4185 in `nanoBragg.c`)
- Constants: `IA=16807`, `IM=2147483647`, `NTAB=32`, etc.
- Output range: `[1.2e-7, 1.0-1.2e-7]` (excludes exact 0.0 and 1.0)

**Reference:** Use excerpts from `reports/determinism-callchain/phase_b3/20251011T051737Z/c_rng_excerpt.c` for algorithm details.

#### 1.1.2 Seed Domains and Defaults
Add table documenting:

| Seed Variable | Default Value | CLI Override | Purpose |
|---------------|---------------|--------------|---------|
| `seed` (noise_seed) | `-time(NULL)` (negative wall-clock) | `-seed <val>` | Poisson noise generation |
| `mosaic_seed` | `-12345678` | `-mosaic_seed <val>` | Mosaic domain rotations |
| `misset_seed` | `seed` (inherits noise_seed) | `-misset_seed <val>` | Static crystal misorientation |

**Spec Reference:** `specs/spec-a-core.md` §5.3 (RNG determinism)

#### 1.1.3 Pointer Side-Effect Contract (CRITICAL)
Add warning box:

> **CRITICAL: Pointer-Based Seed Mutation**
>
> The C implementation uses **pointer side effects** to advance seed state:
> ```c
> double ran1(long *idum)  // ← Pointer allows in-place mutation
> {
>     // ... LCG computation ...
>     *idum = new_state;  // ← Mutates caller's seed variable
>     return random_value;
> }
> ```
>
> Each call to `ran1(&seed)` mutates `seed` in-place, advancing the LCG chain by one step. Functions like `mosaic_rotation_umat(umat, &mosaic_seed)` consume **3 random values** (axis direction + angle scaling), advancing the seed **3 times** per invocation.
>
> **PyTorch Parity Requirement:**
> The PyTorch implementation MUST replicate this deterministic state progression. The `LCGRandom` class wraps seed state and exposes `.uniform()` method to advance state identically to C's `ran1(&seed)`.

#### 1.1.4 Invocation Sites
Add table documenting:

| Function | Invocation Site | Seed Parameter | RNG Calls per Invocation | Purpose |
|----------|----------------|----------------|--------------------------|---------|
| `mosaic_rotation_umat` | Line 2083 (misset) | `&misset_seed` | 3 | Static crystal misorientation (once per sim) |
| `mosaic_rotation_umat` | Line 2689 (mosaic loop) | `&mosaic_seed` | 3 × `mosaic_domains` | Mosaic domain rotations (loop) |
| `poidev` | Multiple sites | `&seed` | Variable | Poisson noise generation |

**Total RNG Consumption Example:** 10 mosaic domains → 30 calls to `ran1(&mosaic_seed)` → seed advances 30 steps.

---

### 1.2 `arch.md` — ADR-05 Enhancement

**Target:** ADR-05 (Deterministic Sampling & Seeds)

**Proposed Addition:**

> **Implementation Note (2025-10-11):**
> The C-code RNG contract uses pointer side effects (`ran1(&seed)`) to advance seed state in-place. PyTorch replicates this via stateful `LCGRandom` class instead of raw pointer manipulation:
> - C: `ran1(&mosaic_seed)` mutates `mosaic_seed` variable directly
> - PyTorch: `LCGRandom(seed).uniform()` advances internal `self.state` attribute
>
> Both approaches produce identical random sequences when seeded identically (verified by `test_lcg_compatibility` in AT-PARALLEL-024). The PyTorch design is functionally equivalent while being memory-safe and thread-compatible.

---

## 2. Source Code Docstrings

### 2.1 `src/nanobrag_torch/utils/c_random.py`

**Target:** Module-level docstring

**Required Content:**

```python
"""
C-compatible Random Number Generator (Minimal Standard LCG + Bays-Durham Shuffle)

This module implements the Minimal Standard Linear Congruential Generator
(Park & Miller 1988) with Bays-Durham shuffle, providing bitwise-exact
compatibility with nanoBragg.c's `ran1()` function.

Algorithm Overview:
-------------------
- Core: LCG with multiplier IA=16807, modulus IM=2147483647 (2^31 - 1)
- Enhancement: 32-element Bays-Durham shuffle table for improved randomness
- Period: ~2.1 billion (IM - 1), sufficient for most simulations
- Output: Uniform random values in [1.2e-7, 1.0-1.2e-7] (excludes exact 0.0/1.0)

Seed Contract (C Pointer Side-Effect Semantics):
------------------------------------------------
The C implementation uses **pointer side effects** to advance seed state:
    double ran1(long *idum) { ... *idum = new_state; ... }

Each call mutates the seed variable in-place. The PyTorch implementation
replicates this via the LCGRandom class:
    rng = LCGRandom(seed=12345)
    val1 = rng.uniform()  # Advances internal state
    val2 = rng.uniform()  # Advances again (deterministic sequence)

Key Functions:
--------------
- mosaic_rotation_umat(): Generates random rotation matrix for mosaic/misset
  Consumes **3 RNG values** per call (axis direction + angle scaling)
- LCGRandom.uniform(): Generates single uniform random value in [0, 1)
  Advances internal state by 1 step (equivalent to C's `ran1(&seed)`)

Determinism Requirements:
--------------------------
1. Same seed → identical random sequence (bitwise reproducible)
2. Independent seeds for noise/mosaic/misset domains (avoid correlation)
3. CPU/GPU neutrality: Results independent of device (CPU vs CUDA)

Validation:
-----------
Bitstream parity verified by test_lcg_compatibility (AT-PARALLEL-024).
Determinism validated by AT-PARALLEL-013 (same-seed runs, correlation ≥0.9999999).

References:
-----------
- C Source: nanoBragg.c lines 4143-4185 (ran1), 3820-3868 (mosaic_rotation_umat)
- Spec: specs/spec-a-core.md §5.3 (RNG determinism)
- Architecture: arch.md ADR-05 (Deterministic Sampling & Seeds)
- Phase B3 Analysis: reports/determinism-callchain/phase_b3/.../c_seed_flow.md
"""
```

**Target:** `mosaic_rotation_umat()` docstring enhancement

**Append to existing docstring:**

```python
    RNG Consumption:
    ----------------
    This function consumes **3 random values** per call:
    1. r1: Axis direction angle (uniform on [-1, 1])
    2. r2: Axis Z-component (uniform on [-1, 1])
    3. r3: Rotation magnitude scaling (uniform on [-1, 1])

    C Equivalent:
    -------------
    Replicates nanoBragg.c lines 3820-3868 (mosaic_rotation_umat).
    C version uses pointer side effects: `ran1(&seed)` mutates seed in-place.
    PyTorch version uses stateful LCGRandom class for memory safety.

    Seed State Progression Example:
    -------------------------------
    rng = LCGRandom(seed=-12345678)
    umat1 = mosaic_rotation_umat(1.0, seed=-12345678)  # Consumes 3 values
    umat2 = mosaic_rotation_umat(1.0, seed=<state_after_3_calls>)  # Next 3 values

    For 10 mosaic domains: Total 30 RNG calls → seed advances 30 steps.
```

---

### 2.2 `src/nanobrag_torch/models/crystal.py`

**Target:** `_generate_mosaic_rotations()` method docstring (line ~720)

**Append to existing docstring:**

```python
    Seed Propagation (Determinism Contract):
    ----------------------------------------
    The mosaic_seed parameter controls the random sequence for mosaic domain
    rotations. Each call to mosaic_rotation_umat() consumes 3 RNG values,
    advancing the seed state deterministically:

    - Domain 0: seed state 0 → consumes values 1-3 → state 3
    - Domain 1: seed state 3 → consumes values 4-6 → state 6
    - Domain N-1: state 3(N-1) → consumes values 3(N-1)+1 to 3N → final state

    This matches the C-code behavior (nanoBragg.c line 2689 mosaic loop) where
    ran1(&mosaic_seed) is called inside the domain loop with pointer side effects.

    References:
    -----------
    - C implementation: nanoBragg.c lines 2689-2700 (mosaic domain loop)
    - RNG helper: src/nanobrag_torch/utils/c_random.py::mosaic_rotation_umat
    - Spec: specs/spec-a-core.md §5.3 (mosaic seed default: -12345678)
```

---

## 3. Testing Strategy Documentation

### 3.1 `docs/development/testing_strategy.md`

**Target:** New subsection under §2 (Configuration Parity) or §1.5 (Loop Execution Notes)

**Proposed Section:**

#### § 2.6 Determinism Validation Workflow

**Purpose:** Ensure reproducible simulations across platforms, devices, and runs.

**Authoritative Tests:**
- `tests/test_at_parallel_013.py` — Cross-platform determinism (same-seed bitwise equality, different-seed independence)
- `tests/test_at_parallel_024.py` — Mosaic/misset RNG determinism and LCG bitstream parity

**Environment Setup:**

Determinism tests require specific environment guards to prevent non-deterministic behavior:

```bash
# Required before pytest execution:
export CUDA_VISIBLE_DEVICES=''           # Force CPU-only (avoid CUDA non-determinism)
export TORCHDYNAMO_DISABLE=1             # Disable TorchDynamo graph capture
export NANOBRAGG_DISABLE_COMPILE=1       # Disable torch.compile in simulator
export KMP_DUPLICATE_LIB_OK=TRUE         # Avoid MKL conflicts

# Execute determinism tests:
pytest -v tests/test_at_parallel_013.py tests/test_at_parallel_024.py
```

**Rationale:**
- `CUDA_VISIBLE_DEVICES=''`: GPU operations may introduce non-deterministic atomics/reductions. CPU execution guarantees bitwise reproducibility.
- `TORCHDYNAMO_DISABLE=1`: Prevents TorchDynamo/Triton CUDA device query crashes when `CUDA_VISIBLE_DEVICES=''` is set (TorchDynamo attempts to index device 0 on zero-length device list).
- `NANOBRAGG_DISABLE_COMPILE=1`: Ensures simulator respects Dynamo disable flag.

**Validation Metrics:**

| Metric | Same-Seed Runs | Different-Seed Runs |
|--------|----------------|---------------------|
| `np.array_equal(img1, img2)` | ✅ PASS (bitwise identical) | ❌ FAIL (expected) |
| Correlation | ≥0.9999999 | ≤0.7 (independence) |
| `np.allclose(rtol=1e-7, atol=1e-12)` | ✅ PASS | ❌ FAIL |

**Reproduction Commands:**

```bash
# AT-PARALLEL-013 (Cross-platform consistency)
CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_013.py

# AT-PARALLEL-024 (Misset/mosaic determinism)
CUDA_VISIBLE_DEVICES='' TORCHDYNAMO_DISABLE=1 NANOBRAGG_DISABLE_COMPILE=1 \
KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_at_parallel_024.py
```

**Artifact Expectations:**
- Test logs: `reports/2026-01-test-suite-triage/phase_d/<STAMP>/determinism/`
- Metrics: Correlation values, `np.array_equal` results, float64 precision checks
- Environment snapshot: `env.json` capturing Python/PyTorch/CUDA versions

**Known Limitations:**
- **CUDA Determinism:** Currently deferred. Tests force CPU-only execution to avoid TorchDynamo device query bug. Future work: Re-enable CUDA execution after upstream fix or local patch, validate GPU determinism with `torch.cuda.manual_seed_all()` and CuDNN deterministic mode.
- **Noise Seed:** Current tests focus on mosaic/misset seeds. Poisson noise determinism (`seed` parameter) validated implicitly but not traced in detail. Add explicit noise seed tests if regressions occur.

**References:**
- Remediation Summary: `reports/determinism-callchain/phase_c/20251011T052920Z/remediation_summary.md`
- C Seed Contract: `reports/determinism-callchain/phase_b3/20251011T051737Z/c_seed_flow.md`
- Spec: `specs/spec-a-core.md` §5.3 (RNG determinism), `specs/spec-a-parallel.md` AT-PARALLEL-013/024

---

## 4. User-Facing Documentation

### 4.1 `README_PYTORCH.md` (Optional Enhancement)

**Target:** Usage Examples section

**Proposed Addition:**

#### Deterministic Simulations

To ensure reproducible results across runs, set seeds explicitly:

```bash
# Command-line interface:
nanoBragg -cell 100 100 100 90 90 90 -default_F 100 -lambda 6.2 \
  -distance 100 -detpixels 128 \
  -mosaic_seed 12345 -misset_seed 67890 -seed 999 \
  -floatfile output.bin

# Python API:
from nanobrag_torch import Simulator, CrystalConfig, DetectorConfig, BeamConfig

crystal = CrystalConfig(
    cell_a=100, cell_b=100, cell_c=100,
    cell_alpha=90, cell_beta=90, cell_gamma=90,
    N_cells=(5, 5, 5),
    mosaic_seed=12345,  # ← Controls mosaic rotations
    misset_seed=67890,  # ← Controls static misorientation
)

simulator = Simulator(crystal=crystal, detector=detector, beam=beam)
image = simulator.run()
```

**Note:** Same seeds → identical output (bitwise reproducible). Different seeds → statistically independent outputs.

---

## 5. Checklist Summary

### 5.1 Architecture Documentation
- [ ] Add RNG section to `docs/architecture/c_function_reference.md`:
  - [ ] Algorithm overview (LCG + Bays-Durham)
  - [ ] Seed domains table (noise/mosaic/misset)
  - [ ] Pointer side-effect warning box
  - [ ] Invocation sites table
- [ ] Enhance `arch.md` ADR-05 with PyTorch parity note

### 5.2 Source Code Docstrings
- [ ] Update `src/nanobrag_torch/utils/c_random.py`:
  - [ ] Module-level docstring (algorithm, seed contract, validation)
  - [ ] `mosaic_rotation_umat()` docstring (RNG consumption, C equivalent)
- [ ] Update `src/nanobrag_torch/models/crystal.py`:
  - [ ] `_generate_mosaic_rotations()` docstring (seed propagation example)

### 5.3 Testing Strategy
- [ ] Add § 2.6 to `docs/development/testing_strategy.md`:
  - [ ] Environment setup (CUDA_VISIBLE_DEVICES, TORCHDYNAMO_DISABLE)
  - [ ] Validation metrics table
  - [ ] Reproduction commands
  - [ ] Known limitations (CUDA deferred, noise seed coverage)

### 5.4 User Documentation (Optional)
- [ ] Add deterministic simulation example to `README_PYTORCH.md`

---

## 6. Execution Plan

### 6.1 Priority 1 (Blocking for [DETERMINISM-001] Closure)
- Architecture documentation (§5.1) — Required for developer reference
- Source code docstrings (§5.2) — Inline guidance for maintainers

### 6.2 Priority 2 (Required for Test Suite Upkeep)
- Testing strategy (§5.3) — Ensures future engineers can reproduce workflows

### 6.3 Priority 3 (User-Facing Enhancement)
- README update (§5.4) — Improves user experience, non-blocking

---

## 7. References

- **Remediation Summary:** `reports/determinism-callchain/phase_c/20251011T052920Z/remediation_summary.md`
- **C Seed Flow:** `reports/determinism-callchain/phase_b3/20251011T051737Z/c_seed_flow.md`
- **Spec:** `specs/spec-a-core.md` §5.3, `specs/spec-a-parallel.md` AT-PARALLEL-013/024
- **Architecture:** `arch.md` ADR-05, `docs/architecture/c_function_reference.md`
- **Testing Strategy:** `docs/development/testing_strategy.md`

---

**Authored by:** ralph (documentation-only loop)
**Next:** Execute checklist items (§5) and mark [DETERMINISM-001] complete upon review.

# Phase A3: Vectorization Gap Classification

**Generated:** 2025-10-09 06:52:38 UTC
**Based on:** Loop inventory from 2025-10-09 06:43:57 UTC (20251009T064345Z)

## Executive Summary

Classification of 24 Python loops detected in src/nanobrag_torch/:

- **Vectorized:** 4 loops (already implemented with batched helpers)
- **Safe:** 17 loops (I/O, configuration, validation, debug-only)
- **Todo:** 2 loops (require vectorization for performance)
- **Uncertain:** 1 loop (needs profiling evidence)

**Top Priority Todo Items:**
1. `utils/noise.py:171` - LCG random number generation (n iterations, variable count)
2. `simulator.py:1568` - Phi-step loop (N_phi iterations, likely hot if N_phi > 1)

## Classification Table

| Module | Line | Loop Type | Status | Priority | Notes |
|--------|------|-----------|--------|----------|-------|
| io/hkl.py | 51 | `for line in f` | Safe | N/A | File I/O, bounded by HKL file size (~thousands) |
| io/hkl.py | 110 | `for (h,k,l,F) in reflections` | Safe | N/A | File I/O, bounded by reflection count |
| io/hkl.py | 208 | `while True` | Safe | N/A | Binary read loop, exits on EOF |
| io/mask.py | 52 | `for line in header...` | Safe | N/A | SMV header parsing, ~10-20 lines |
| io/mask.py | 178 | `for line in header...` | Safe | N/A | SMV header parsing, ~10-20 lines |
| io/mosflm.py | 59 | `for line in f` | Safe | N/A | MOSFLM matrix file, ~20 lines |
| io/mosflm.py | 67 | `for part in parts` | Safe | N/A | Parse matrix row, 3 elements |
| io/smv.py | 46 | `for line in header...` | Safe | N/A | SMV header parsing |
| io/smv.py | 240 | `for (key,value) in header.items()` | Safe | N/A | Dict iteration, small header (~20 keys) |
| io/source.py | 60 | `for (line_num,line) in enumerate(f, 1)` | Safe | N/A | Source file parsing, bounded |
| crystal.py | 180 | `for (angle_name,angle) in [...]` | Safe | N/A | Validation, 3 cell angles only |
| crystal.py | 187 | `for (angle_name,angle) in [...]` | Safe | N/A | Validation warning, 3 angles only |
| crystal.py | 762 | `for angle in self.config.misset_deg` | Safe | N/A | Tensor conversion, 3 misset angles only |
| crystal.py | 1350 | `for i in range(3)` | Safe | LOW | Mosaic rotation matrix construction, N=3 (identity columns), outside hot path |
| simulator.py | 1469 | `for i in range(4)` | Safe | N/A | Debug trace only, guarded by `_enable_trace` flag |
| simulator.py | 1470 | `for j in range(4)` | Safe | N/A | Debug trace only, nested inside debug guard |
| simulator.py | 1471 | `for k in range(4)` | Safe | N/A | Debug trace only, nested inside debug guard |
| simulator.py | 1568 | `for phi_tic in range(phi_steps)` | Uncertain | MEDIUM | Phi-step residual handling (see notes below) |
| utils/physics.py | 393 | `for j in range(4)` | Vectorized | N/A | polin2 helper, vectorized in Phase D2 (`polin2_vectorized`) |
| utils/physics.py | 439 | `for j in range(4)` | Vectorized | N/A | polin2 helper, vectorized in Phase D2 |
| utils/physics.py | 543 | `for j in range(4)` | Vectorized | N/A | polin3 helper, vectorized in Phase D2 (`polin3_vectorized`) |
| utils/physics.py | 594 | `for j in range(4)` | Vectorized | N/A | polin3 helper, vectorized in Phase D2 |
| utils/c_random.py | 100 | `for j in range(self.NTAB+7, -1, -1)` | Safe | N/A | RNG shuffle table initialization, ~39 iterations, one-time setup per seed |
| utils/noise.py | 171 | `for i in range(n)` | Todo | **HIGH** | LCG loop generates n random values; n can be large (image size); vectorizable via tensor ops |

## Detailed Classification Notes

### Vectorized (4 loops)

Already implemented with batched tensor helpers in Phase D2 (tricubic vectorization initiative):

- **utils/physics.py:393, 439** - `polin2` helper loops replaced by `polin2_vectorized` (handles batched 2D interpolation)
- **utils/physics.py:543, 594** - `polin3` helper loops replaced by `polin3_vectorized` (handles batched 3D tricubic interpolation)

**Validation:** Tests in `tests/test_at_parallel_012.py` and tricubic golden data verify batched interpolation correctness.

**Rationale:** These loops were identified as hot during tricubic interpolation profiling (Phase C) and vectorized in Phase D2 to avoid scalar Python loops over 4×4×4 neighborhoods.

### Safe (17 loops)

#### I/O Loops (10 loops)
All file I/O loops are safe because:
- Operate on finite, external data (HKL files, SMV headers, matrix files)
- Bounded by file size (typically thousands of reflections, tens of header lines)
- Not in simulator hot path
- Vectorization offers no practical gain for one-time file parsing

**Modules:** `io/hkl.py` (lines 51, 110, 208), `io/mask.py` (52, 178), `io/mosflm.py` (59, 67), `io/smv.py` (46, 240), `io/source.py` (60)

#### Configuration & Validation Loops (3 loops)
- **crystal.py:180** - Iterate over 3 cell angles (alpha, beta, gamma) for range validation
- **crystal.py:187** - Iterate over 3 cell angles for numerical stability warning
- **crystal.py:762** - Convert 3 misset angles from scalar/tensor to tensor list

**Rationale:** Fixed N=3 iterations per validation/conversion call; total negligible overhead; spec requires explicit parameter-by-parameter validation (specs/spec-a-core.md Unit Cell Requirements).

#### Setup & Initialization Loops (2 loops)
- **crystal.py:1350** - Apply mosaic rotations to 3 columns of identity matrix (N=3)
- **c_random.py:100** - Initialize C-compatible RNG shuffle table (NTAB+7 = ~39 iterations, one-time per seed)

**Rationale:** Fixed small N; initialization happens once per configuration, outside simulator hot path; no GPU benefit.

#### Debug-Only Loops (3 loops)
- **simulator.py:1469-1471** - Nested 4×4×4 tricubic grid trace output

**Rationale:** Guarded by `_enable_trace` flag (default False); only active when `--trace-pixel` CLI flag is used; production runs never execute these loops (see CLI-FLAGS-003 Phase M0a instrumentation discipline).

### Todo (2 loops)

#### 1. utils/noise.py:171 - LCG Random Number Generation (HIGH Priority)

**Loop:**
```python
for i in range(n):
    current = (RAND_MULT * current + RAND_ADD) & RAND_MAX
    values[i] = float(current) / float(RAND_MAX)
```

**Hotness:** Variable `n` (can be large, e.g., image size = 1024×1024 = 1M iterations for noise generation)

**Vectorization Opportunity:** LCG formula is embarrassingly parallel; can compute all n iterations upfront using tensor parallel scan or recursive doubling.

**Design Reference:** See `docs/architecture/pytorch_design.md §1.1` (batch shapes) and `docs/development/pytorch_runtime_checklist.md` (vectorization do/don'ts).

**Expected Speedup:** ~10-100x for large n (CPU), ~100-1000x (GPU) by replacing Python loop with batched tensor ops.

**Affected Tests:** `tests/test_at_noise_001.py`, `tests/test_at_parallel_012.py` (noise image generation)

**Design Notes:**
- LCG recurrence: `x[i+1] = (a * x[i] + c) mod m`
- Vectorizable via matrix exponentiation or parallel prefix scan
- Must preserve C-compatible bitstream (exact determinism requirement per spec AT-NOISE-001)
- Suggest creating `lcg_vectorized(seed, n)` helper in `utils/noise.py`

**Constraints:**
- Must maintain exact C-code parity (use identical RAND_MULT, RAND_ADD, RAND_MAX constants)
- Deterministic output required for golden test validation
- Device/dtype neutral (CPU + CUDA smoke tests mandatory per Core Rule #16)

#### 2. simulator.py:1568 - Phi-Step Residual Loop (MEDIUM Priority, Uncertain)

**Loop:**
```python
for phi_tic in range(phi_steps):
    phi_deg = phi_start_deg + phi_tic * phi_step_size
    a_vec_phi = rot_a[phi_tic, 0]  # First mosaic domain
    b_vec_phi = rot_b[phi_tic, 0]
    c_vec_phi = rot_c[phi_tic, 0]
    # Compute reciprocal vectors, Miller indices, and accumulate intensity
    ...
```

**Context:** This loop appears in a debug/trace context (see simulator.py:1565-1590). It iterates over phi steps to extract and log rotated lattice vectors for the first mosaic domain.

**Hotness:** Uncertain - depends on typical phi_steps value and call frequency:
- If phi_steps is typically 1-10 (static crystals), overhead is negligible
- If phi_steps > 100 (oscillation scans), this may contribute measurable time

**Vectorization Opportunity:** The loop body extracts pre-computed rotated vectors (`rot_a[phi_tic, 0]`) and performs reciprocal vector calculations. This could be batched over phi dimension if needed.

**Classification Uncertainty:** Needs profiling evidence to determine:
- Typical phi_steps distribution in production runs
- % of total runtime spent in this loop
- Whether this is debug-only or production path

**Next Steps:**
- Phase B1 profiler trace will reveal if this loop shows up in hot path
- If profiler shows <1% inclusive time → classify as Safe (document rationale)
- If profiler shows ≥1% inclusive time → promote to Todo HIGH and create design packet

**Provisional Classification:** Uncertain (pending Phase B1 profiling evidence)

**Notes:**
- Loop already accesses pre-computed batched rotations from `get_rotated_real_vectors` (which returns (N_phi, N_mos, 3) tensors)
- Vectorization would batch the reciprocal-from-real recomputation over phi dimension
- Consider whether this is a residual from old implementation that can be eliminated entirely by refactoring to use batch operations on the full (N_phi, N_mos) grid

### Uncertain (1 loop)

See **simulator.py:1568** analysis above under Todo section.

**Blocked By:** Phase B1 profiler trace (requires warm-run profiling with representative phi_steps values)

**Resolution Criteria:**
- If profiler shows <1% time → reclassify as Safe, document in summary.md
- If profiler shows ≥1% time → promote to Todo HIGH, create design packet in Phase C

## Device/Dtype Considerations

**GPU-Specific Concerns:**
- **noise.py:171 (LCG loop):** CPU-only loop currently; GPU acceleration would provide 100-1000x speedup for noise generation
- **Other loops:** All Safe loops are CPU-bound I/O or config operations; no GPU benefit expected

**Dtype Considerations:**
- LCG vectorization must preserve int32 arithmetic (RAND_MAX = 2147483647 = 2³¹-1)
- Ensure no silent float32 → float64 promotion in batched LCG implementation (use explicit dtype kwarg)

## Prerequisites for Phase B (Profiling)

Before profiling work in Phase B can proceed:

1. **Baseline established:** This classification provides static analysis baseline
2. **Profiler targets identified:** noise.py:171 (confirmed todo), simulator.py:1568 (uncertain, needs runtime evidence)
3. **Profiler command ready:** Use `scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile` per input.md guidance
4. **Correlation approach:** Map profiler hotspots (≥1% inclusive time) to this inventory's module:line pairs

**Profiler Focus Areas:**
- Confirm noise.py:171 appears in trace (should be visible during `-noisefile` generation)
- Resolve simulator.py:1568 uncertainty (check if it appears in hot path or is trace-only)
- Identify any dynamic loops introduced by recent commits (compare against 20251009 baseline JSON)

## Open Questions for Phase B

1. **simulator.py:1568 classification:** Is this debug-only or production hot path? (profiler will answer)
2. **noise.py:171 priority:** What % of total runtime is spent in LCG loop? (if high, prioritize for GPU)
3. **Hidden loops:** Are there dynamic loops (comprehensions, map/filter) not detected by AST scan? (profiler may reveal)

## Future Work (Phase C)

Once Phase B profiling completes:

1. **Design packet for noise.py:171:** Create `reports/2026-01-vectorization-gap/phase_c/lcg_vectorization/design.md` with:
   - Tensor shape analysis (input: scalar seed, n; output: (n,) tensor)
   - Parallel scan algorithm or matrix exponentiation approach
   - C-code parity verification strategy (bitwise-identical output requirement)
   - Benchmark harness command (`scripts/benchmarks/vectorization_gap_lcg.py`)

2. **Resolve simulator.py:1568:** If profiler confirms hot, create design packet; if cold, document rationale and archive

3. **Microbench harnesses:** Create under `scripts/benchmarks/` for each HIGH-priority todo loop (per input.md Step C2)

## Appendix: Classification Counts

| Status | Count | % of Total |
|--------|-------|------------|
| Vectorized | 4 | 16.7% |
| Safe | 17 | 70.8% |
| Todo | 2 | 8.3% |
| Uncertain | 1 | 4.2% |
| **Total** | **24** | **100%** |

**Hot Path Coverage:** 4 vectorized + 17 safe = 21/24 (87.5%) loops confirmed non-blocking for performance.

**Remaining Work:** 2 todo + 1 uncertain = 3 loops require follow-up (12.5% of inventory).

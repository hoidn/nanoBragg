# Vectorization Loop Inventory Summary (Phase A3 Annotated)

**Generated:** 2025-10-09 06:52:38 UTC
**Baseline Scan:** 2025-10-09 06:43:57 UTC (from 20251009T064345Z)
**Phase:** A3 (Classification & Annotation)

## Overview

- Total loops found: 24
- **Vectorized:** 4 (already implemented with batched helpers)
- **Safe (non-hot):** 17 (I/O, config, validation, debug-only)
- **Todo (requires vectorization):** 2 (LCG loop, phi-step residual)
- **Uncertain (needs profiling):** 1 (phi-step loop classification pending)
- Scan target: src/nanobrag_torch/

## Classification Summary

See `analysis.md` for detailed rationale and design notes.

### Top Priority Todos

1. **utils/noise.py:171** - LCG random number generation (HIGH priority)
   - Variable n iterations (can be 1M+ for full image noise)
   - Vectorizable via parallel scan or matrix exponentiation
   - Expected speedup: 10-100x (CPU), 100-1000x (GPU)

2. **simulator.py:1568** - Phi-step residual loop (MEDIUM priority, classification uncertain)
   - N_phi iterations (depends on oscillation parameters)
   - Needs profiler evidence to confirm hotness
   - If <1% runtime → Safe; if ≥1% → Todo HIGH

### Already Vectorized (Phase D2)

- `utils/physics.py:393, 439, 543, 594` - Polynomial interpolation helpers
  - Replaced by `polin2_vectorized`, `polin3_vectorized` in Phase D2
  - Validated by tricubic golden tests

## Loops by Module

### src/nanobrag_torch/io/hkl.py [Safe: 3 loops]

Loop count: 3 (all Safe - file I/O, bounded by HKL file size)

- Line 51: `for line in f`
  - Type: for
  - Classification: **Safe** (file I/O, ~thousands of lines)

- Line 110: `for (h, k, l, F) in reflections`
  - Type: for
  - Classification: **Safe** (file I/O, reflection count bounded)

- Line 208: `while True`
  - Type: while
  - Classification: **Safe** (binary read loop, exits on EOF)

### src/nanobrag_torch/io/mask.py [Safe: 2 loops]

Loop count: 2 (all Safe - SMV header parsing)

- Line 52: `for line in header_content.split(';')`
  - Type: for
  - Classification: **Safe** (header parsing, ~10-20 lines)

- Line 178: `for line in header_content.split(';')`
  - Type: for
  - Classification: **Safe** (header parsing, ~10-20 lines)

### src/nanobrag_torch/io/mosflm.py [Safe: 2 loops]

Loop count: 2 (all Safe - MOSFLM matrix file parsing)

- Line 59: `for line in f`
  - Type: for
  - Classification: **Safe** (file I/O, ~20 lines)

- Line 67: `for part in parts`
  - Type: for
  - Classification: **Safe** (parse matrix row, 3 elements)

### src/nanobrag_torch/io/smv.py [Safe: 2 loops]

Loop count: 2 (all Safe - SMV header I/O)

- Line 46: `for line in header_content.split('\n')`
  - Type: for
  - Classification: **Safe** (header parsing)

- Line 240: `for (key, value) in header.items()`
  - Type: for
  - Classification: **Safe** (dict iteration, ~20 keys)

### src/nanobrag_torch/io/source.py [Safe: 1 loop]

Loop count: 1 (Safe - source file parsing)

- Line 60: `for (line_num, line) in enumerate(f, 1)`
  - Type: for
  - Classification: **Safe** (file I/O, bounded)

### src/nanobrag_torch/models/crystal.py [Safe: 4 loops]

Loop count: 4 (all Safe - validation, config conversion, setup)

- Line 180: `for (angle_name, angle) in [('alpha', self.cell_alpha), ('beta', self.cell_beta), ('gamma', self.cell_gamma)]`
  - Type: for
  - Classification: **Safe** (validation, N=3 angles only)

- Line 187: `for (angle_name, angle) in [('alpha', self.cell_alpha), ('beta', self.cell_beta), ('gamma', self.cell_gamma)]`
  - Type: for
  - Classification: **Safe** (validation warning, N=3 angles only)

- Line 762: `for angle in self.config.misset_deg`
  - Type: for
  - Classification: **Safe** (tensor conversion, N=3 misset angles)

- Line 1350: `for i in range(3)`
  - Type: for
  - Classification: **Safe** (mosaic matrix construction, N=3 identity columns, outside hot path)

### src/nanobrag_torch/simulator.py [Safe: 3, Uncertain: 1]

Loop count: 4

#### Safe (Debug-Only): 3 loops

- Line 1469: `for i in range(4)`
  - Type: for
  - Classification: **Safe** (debug trace only, guarded by _enable_trace flag)

- Line 1470: `for j in range(4)`
  - Type: for
  - Classification: **Safe** (debug trace only, nested inside debug guard)

- Line 1471: `for k in range(4)`
  - Type: for
  - Classification: **Safe** (debug trace only, nested 4×4×4 grid output)

#### Uncertain (Needs Profiling): 1 loop

- Line 1568: `for phi_tic in range(phi_steps)`
  - Type: for
  - Classification: **Uncertain** (phi-step residual handling)
  - **Priority:** MEDIUM (pending profiler evidence)
  - **Resolution:** Phase B1 profiling will determine if <1% (Safe) or ≥1% (Todo HIGH)
  - **Notes:** Loop iterates over phi_steps; typical values unknown; vectorization possible if hot

### src/nanobrag_torch/utils/c_random.py [Safe: 1 loop]

Loop count: 1 (Safe - RNG initialization)

- Line 100: `for j in range(self.NTAB + 7, -1, -1)`
  - Type: for
  - Classification: **Safe** (shuffle table init, ~39 iterations, one-time setup per seed)

### src/nanobrag_torch/utils/noise.py [Todo: 1 loop]

Loop count: 1

- Line 171: `for i in range(n)`
  - Type: for
  - Classification: **Todo (HIGH priority)**
  - **Hotness:** Variable n (can be 1M+ for image noise)
  - **Vectorization:** LCG formula is embarrassingly parallel
  - **Expected Speedup:** 10-100x (CPU), 100-1000x (GPU)
  - **Design Notes:** See analysis.md for parallel scan/matrix exponentiation approach
  - **Constraints:** Must preserve C-compatible bitstream (exact determinism)

### src/nanobrag_torch/utils/physics.py [Vectorized: 4 loops]

Loop count: 4 (all Vectorized in Phase D2)

- Line 393: `for j in range(4)`
  - Type: for
  - Classification: **Vectorized** (polin2 helper, replaced by `polin2_vectorized`)

- Line 439: `for j in range(4)`
  - Type: for
  - Classification: **Vectorized** (polin2 helper, replaced by `polin2_vectorized`)

- Line 543: `for j in range(4)`
  - Type: for
  - Classification: **Vectorized** (polin3 helper, replaced by `polin3_vectorized`)

- Line 594: `for j in range(4)`
  - Type: for
  - Classification: **Vectorized** (polin3 helper, replaced by `polin3_vectorized`)

## Next Steps (Phase B - Profiling)

1. **Capture warm-run profiler trace** using canonical command:
   ```bash
   KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py \
     --sizes 4096 --device cpu --dtype float32 --profile \
     --keep-artifacts --iterations 1 \
     --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/
   ```

2. **Correlate loops with profiler hotspots:**
   - Extract simulator/crystal/utils call stacks from profiler output
   - Map hotspots (≥1% inclusive time) to inventory module:line pairs
   - Produce `hot_loops.csv` with columns: module, line, loop_id, %time, call_count, notes

3. **Resolve simulator.py:1568 uncertainty:**
   - If profiler shows <1% time → reclassify as Safe, document rationale
   - If profiler shows ≥1% time → promote to Todo HIGH, create Phase C design packet

4. **Prioritize todo list:**
   - Rank by %time from profiler (highest impact first)
   - Consider GPU-specific hotspots (loops with high call_count × iterations)
   - Document expected speedups and affected acceptance tests

5. **Publish backlog:**
   - Create `reports/2026-01-vectorization-gap/phase_b/<STAMP>/backlog.md`
   - List top 3-5 candidates with:
     - Expected speedup estimates
     - Affected acceptance tests (pytest selectors)
     - Implementation risks (C-parity, determinism, device/dtype neutrality)
   - Update `docs/fix_plan.md` Next Actions with backlog items

## Appendix: Phase A3 Classification Results

| Status | Count | % of Total | Modules |
|--------|-------|------------|---------|
| Vectorized | 4 | 16.7% | utils/physics.py (polynomial interpolation) |
| Safe | 17 | 70.8% | io/* (10), crystal.py (4), simulator.py (3 debug), c_random.py (1) |
| Todo | 2 | 8.3% | utils/noise.py (1 HIGH), simulator.py (1 MEDIUM uncertain) |
| Uncertain | 1 | 4.2% | simulator.py:1568 (pending profiler evidence) |
| **Total** | **24** | **100%** | 10 modules scanned |

**Hot Path Coverage:** 21/24 (87.5%) loops confirmed non-blocking (Vectorized + Safe).

**Remaining Work:** 3 loops (12.5%) require follow-up:
- 1 confirmed Todo HIGH (noise.py:171 LCG loop)
- 1 Todo MEDIUM uncertain (simulator.py:1568, needs profiler)
- Phase B profiling will resolve uncertainty and rank by impact

**Device/Dtype Notes:**
- GPU benefit expected only for noise.py:171 (100-1000x speedup potential)
- All Safe loops are CPU-bound I/O or config; no GPU acceleration benefit
- Vectorized loops already device-neutral (tested in Phase D2 smoke checks)

**Guardrails Compliance:**
- All classifications cross-referenced with `docs/architecture/pytorch_design.md` §1.1 (batch shapes)
- Device/dtype discipline per `docs/development/pytorch_runtime_checklist.md` (Core Rule #16)
- Parity requirements noted for noise.py:171 (exact C-compatible bitstream per AT-NOISE-001)

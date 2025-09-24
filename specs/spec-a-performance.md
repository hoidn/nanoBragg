# Performance Acceptance Tests

This document defines performance-related acceptance tests that should have been part of the original specification to ensure the PyTorch implementation meets performance expectations.

## Performance Requirements

### AT-PERF-001 Vectorization Performance Benefit
- **Setup**: Simple cubic cell 100,100,100,90,90,90; -lambda 6.2; -N 5; -default_F 100; -distance 100; MOSFLM convention. Test with detector sizes: 256×256, 512×512, 1024×1024, 2048×2048.
- **Expectation**: The PyTorch implementation SHALL demonstrate vectorization benefits by achieving throughput (pixels/second) that scales sub-linearly with problem size. Specifically:
  - Throughput ratio between 2048×2048 and 256×256 SHALL be ≥ 2.0 (demonstrating vectorization efficiency)
  - For CPU execution without explicit parallelization, PyTorch SHALL achieve ≥ 50% of C implementation throughput
  - Memory usage SHALL scale linearly with detector size (O(n²) for n×n detector)
- **Pass Criteria**:
  - Measure wall-clock time for each detector size
  - Calculate throughput as pixels_processed / execution_time
  - Verify scaling factor: (throughput_2048 / throughput_256) ≥ 2.0
  - Verify performance parity: pytorch_throughput ≥ 0.5 × c_throughput

### AT-PERF-002 Parallel Execution Capability
- **Setup**: Cell 100,100,100,90,90,90; -lambda 1.0; -N 10; -default_F 100; detector 1024×1024; -distance 100.
- **Expectation**: When parallel execution is available:
  - CPU: Both implementations SHALL demonstrate speedup with increased thread count
  - GPU: PyTorch SHALL achieve ≥ 10× speedup over parallel C implementation
  - Speedup from 1 to 4 threads SHALL be ≥ 2.5× for CPU implementations
  - PyTorch CPU with appropriate parallelization SHALL achieve performance within 20% of C
  - PyTorch GPU SHALL achieve ≥ 10× throughput of parallel C implementation
- **Pass Criteria**:
  - CPU: Run with OMP_NUM_THREADS={1,2,4,8} for C and torch.set_num_threads({1,2,4,8}) for PyTorch
  - Measure speedup = time_1_thread / time_N_threads
  - Verify CPU speedup(4 threads) ≥ 2.5
  - Verify |pytorch_cpu_time - c_time| / c_time ≤ 0.20 with 4+ threads
  - GPU: Verify pytorch_gpu_throughput ≥ 10.0 × c_parallel_throughput

### AT-PERF-003 Memory Bandwidth Optimization
- **Setup**: Cell 100,100,100,90,90,90; -lambda 6.2; -N 5; -default_F 100; detector 2048×2048; -distance 100.
- **Expectation**: The implementation SHALL efficiently utilize memory bandwidth:
  - Peak memory usage SHALL not exceed 2× the theoretical minimum (detector_size × sizeof(float) × safety_factor)
  - Memory access patterns SHALL be cache-friendly (verified by consistent performance across runs)
  - Float32 operations SHALL be at least 1.5× faster than float64 for memory-bound operations
- **Pass Criteria**:
  - Measure peak memory usage during execution
  - Theoretical minimum = width × height × 4 bytes (float32) × 3 (for intermediate arrays)
  - Verify peak_memory ≤ 2 × theoretical_minimum
  - Compare float32 vs float64 execution time
  - Verify time_float64 / time_float32 ≥ 1.5

### AT-PERF-004 Hot Path Optimization
- **Setup**: Complex case with triclinic cell 70,80,90,85,95,105; -lambda 1.5; -N 8; -misset 10,5,3; detector 512×512; -distance 100.
- **Expectation**: Critical inner loop operations SHALL be optimized:
  - The sincg function SHALL process ≥ 100 million evaluations per second
  - Dot product operations SHALL achieve ≥ 500 million operations per second
  - No individual operation SHALL take > 10% of total runtime (except the main pixel loop)
- **Pass Criteria**:
  - Profile execution to identify hot paths
  - Measure sincg throughput: count_sincg_calls / sincg_total_time ≥ 100M/s
  - Measure dot product throughput: count_dot_products / dot_total_time ≥ 500M/s
  - Verify no single function (except main loop) exceeds 10% of runtime

### AT-PERF-005 Compilation/JIT Optimization Benefit
- **Setup**: Cell 100,100,100,90,90,90; -lambda 6.2; -N 5; -default_F 100; detector 1024×1024; -distance 100.
- **Expectation**: When JIT compilation or ahead-of-time compilation is available:
  - torch.compile() or torch.jit.script SHALL provide ≥ 20% speedup for hot paths
  - Compiled version SHALL maintain numerical accuracy (correlation ≥ 0.9999 with uncompiled)
  - Compilation overhead SHALL be amortized within 10 runs
- **Pass Criteria**:
  - Measure baseline execution time without compilation
  - Measure execution time with torch.compile() or equivalent
  - Verify speedup = baseline_time / compiled_time ≥ 1.20
  - Verify correlation between compiled and uncompiled outputs ≥ 0.9999
  - Verify (total_time_10_runs_compiled) < (total_time_10_runs_baseline)

## Rationale

These performance tests would have caught the issue where the PyTorch implementation is slower than C despite using vectorized operations. The root cause - lack of parallel pixel processing in PyTorch while C uses OpenMP - would have been identified by AT-PERF-002.

Key insights these tests would reveal:
1. **AT-PERF-001** would show PyTorch not meeting the 50% performance threshold
2. **AT-PERF-002** would reveal PyTorch's lack of pixel-level parallelization
3. **AT-PERF-003** would identify the float64 vs float32 overhead
4. **AT-PERF-004** would pinpoint the sincg and dot product bottlenecks
5. **AT-PERF-005** would demonstrate the potential for JIT optimization

## Implementation Notes

To pass these tests, the PyTorch implementation would need:
1. Parallel pixel processing (via torch.multiprocessing or custom CUDA kernels)
2. Float32 as default dtype for performance-critical paths
3. JIT compilation of hot loops (sincg, dot products)
4. Memory-efficient tensor operations minimizing intermediates
5. Proper thread pool configuration for BLAS operations
6. GPU-optimized kernels achieving ≥10x speedup over parallel C implementation

### AT-PERF-006 Tensor Vectorization Completeness

**Setup**: Cell 100,100,100,90,90,90; -lambda 6.2; -N 5; -default_F 100; detector 256×256; -distance 100; -oversample 2; -detector_thick 200; -detector_thicksteps 3; -hdiv 0.1; -vdiv 0.1; -hdivstep 0.02; -vdivstep 0.02; -dispersion 0.05; -dispsteps 3.

**Expectation**: The PyTorch implementation SHALL use fully vectorized tensor operations without Python-level loops for all performance-critical dimensions:
  - Sub-pixel sampling: oversample×oversample grid SHALL be computed as a single tensor operation with shape (S, F, oversample, oversample, ...)
  - Detector thickness: thicksteps layers SHALL be computed as a tensor dimension with shape (..., thicksteps)
  - Beam sources: divergence and dispersion points SHALL form a sources tensor dimension with shape (..., n_sources)
  - No Python `for` loops SHALL exist in the core computation path for these dimensions
  - Profile SHALL show >95% of computation time in tensor operations, <5% in Python loop overhead

**Pass Criteria**:
  - Inspect implementation code to verify no `for i_s in range(oversample)` or similar loops
  - Profile execution with Python profiler (cProfile or py-spy)
  - Verify tensor operation time / total_time ≥ 0.95
  - Measure throughput improvement: vectorized_version SHALL be ≥5× faster than loop version for oversample=3
  - Verify all intermediate tensors have expected shapes with all dimensions present simultaneously

### AT-PERF-007 Comprehensive Performance Benchmarking Suite

**Setup**: Create a systematic benchmark suite testing multiple parameter combinations:
- Detector sizes: 128×128, 256×256, 512×512, 1024×1024, 2048×2048
- Crystal cells: simple cubic (100,100,100,90,90,90) and triclinic (70,80,90,85,95,105)
- Crystal sizes (-N): 1, 5, 10, 20
- Oversampling: 1, 2, 4
- Wavelengths: 0.5, 1.0, 1.5, 6.2 Å
- Default structure factor: 100
- Distance: 100 mm
- Enable performance features: detector absorption, polarization, mosaic spread

**Expectation**: The implementation SHALL provide comprehensive benchmarking capabilities:
- Execute benchmarks for C-CPU (with OMP_NUM_THREADS={1,4,8}), PyTorch-CPU, and PyTorch-CUDA (if available)
- Record performance metrics for each configuration:
  - Wall-clock time (seconds)
  - Throughput (pixels/second)
  - Memory usage (peak RSS in MB)
  - For PyTorch: JIT compilation time (first run vs steady-state)
- Save results to structured output format (JSON or CSV) with columns:
  - implementation: "C-CPU-1", "C-CPU-4", "C-CPU-8", "PyTorch-CPU", "PyTorch-CUDA"
  - detector_size: pixel count
  - crystal_type: "cubic" or "triclinic"
  - crystal_N: integer
  - oversample: integer
  - wavelength_A: float
  - time_seconds: float
  - throughput_pixels_per_sec: float
  - memory_peak_MB: float
  - speedup_vs_C1: ratio relative to single-threaded C
- Performance requirements:
  - PyTorch-CPU SHALL achieve ≥0.5× throughput of C-CPU-8 (8-thread parallel C)
  - PyTorch-CUDA SHALL achieve ≥5× throughput of C-CPU-8 when GPU is available
  - Memory usage SHALL scale sub-quadratically: memory(2N×2N) ≤ 4.5 × memory(N×N)

**Pass Criteria**:
- Benchmark script SHALL be executable with: `python benchmark_performance.py --output-dir results/`
- Output file SHALL be named: `benchmark_YYYYMMDD_HHMMSS.json` with timestamp
- Script SHALL automatically detect CUDA availability and skip GPU tests if unavailable
- Script SHALL warm up PyTorch JIT with 2 runs before measuring
- Each configuration SHALL be measured 3 times; report median time
- Results SHALL include metadata: platform, CPU model, GPU model (if any), software versions
- Visualization script SHALL generate comparison plots from JSON output

### AT-PERF-008 CUDA Large-Tensor Residency
- **Setup**: On hardware where `torch.cuda.is_available()` returns True, run the reference `Simulator.run()` workflow for a detector ≥ 512×512 pixels (≥ 262,144 elements) with `device="auto"` so the implementation chooses CUDA.
- **Expectation**: Every tensor created or consumed inside the main simulation loop whose `numel()` ≥ 65,536 SHALL reside on a CUDA device for all arithmetic, reduction, and linear-algebra operations. Host copies are permitted only at explicit I/O boundaries (e.g., final `.cpu()` before file writes).
- **Pass Criteria**:
  - Instrument execution with `torch.profiler` or an autograd `record_function` hook that logs `tensor.device` per op; assert no logged large-tensor op executes on CPU when CUDA is present.
  - Any attempt to place such tensors on CPU SHALL raise or be treated as a failure.
  - Test SHALL skip when CUDA is unavailable (reported as SKIPPED, not PASS).

### GPU Performance Justification

The 10x GPU speedup requirement is justified by:
- **Parallelism**: Modern GPUs have 1000s-10000s of CUDA cores vs 8-16 CPU threads
- **Memory bandwidth**: GPU memory bandwidth is typically 5-10x higher than CPU
- **Vectorization**: GPU tensor cores provide massive throughput for matrix operations
- **Problem characteristics**: Diffraction simulation is embarrassingly parallel across pixels
- **Industry benchmarks**: Similar scientific computing workloads routinely achieve 10-100x speedups on GPU

These requirements would have driven the implementation toward GPU-first design from the start, ensuring the PyTorch implementation leverages the full power of modern accelerators.

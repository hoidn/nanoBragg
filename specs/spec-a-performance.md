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

### GPU Performance Justification

The 10x GPU speedup requirement is justified by:
- **Parallelism**: Modern GPUs have 1000s-10000s of CUDA cores vs 8-16 CPU threads
- **Memory bandwidth**: GPU memory bandwidth is typically 5-10x higher than CPU
- **Vectorization**: GPU tensor cores provide massive throughput for matrix operations
- **Problem characteristics**: Diffraction simulation is embarrassingly parallel across pixels
- **Industry benchmarks**: Similar scientific computing workloads routinely achieve 10-100x speedups on GPU

These requirements would have driven the implementation toward GPU-first design from the start, ensuring the PyTorch implementation leverages the full power of modern accelerators.
#!/usr/bin/env python3
"""
Quick test to verify GPU acceleration is working properly.
"""

import os
import time
import torch
import numpy as np

# Ensure environment is set
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, CrystalShape, DetectorConvention
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

def run_simulation(device, size=256):
    """Run a single simulation on specified device."""

    # Setup configs
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=[5, 5, 5],
        default_F=100.0,
        shape=CrystalShape.SQUARE
    )

    detector_config = DetectorConfig(
        spixels=size,
        fpixels=size,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        oversample=1
    )

    beam_config = BeamConfig(wavelength_A=6.2)

    # Create objects on specified device
    crystal = Crystal(crystal_config, device=device)
    detector = Detector(detector_config, device=device)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    # Warm-up run for JIT compilation
    _ = simulator.run()
    if device.type == 'cuda':
        torch.cuda.synchronize()

    # Timed runs
    times = []
    for i in range(5):
        start = time.time()
        image = simulator.run()
        if device.type == 'cuda':
            torch.cuda.synchronize()
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"    Run {i+1}: {elapsed:.4f}s")

    avg_time = np.mean(times[1:])  # Skip first run (may have additional compilation)
    std_time = np.std(times[1:])

    return avg_time, std_time, image

def main():
    print("=" * 60)
    print("GPU Acceleration Test for nanoBragg PyTorch")
    print("=" * 60)

    print(f"\nPyTorch version: {torch.__version__}")
    print(f"CUDA available: {torch.cuda.is_available()}")

    if not torch.cuda.is_available():
        print("\n⚠️ CUDA is not available. Cannot test GPU acceleration.")
        print("Running CPU-only test instead...")

        print("\nCPU Performance (256x256 detector):")
        cpu_time, cpu_std, _ = run_simulation(torch.device('cpu'), 256)
        print(f"  Average time: {cpu_time:.4f}s ± {cpu_std:.4f}s")
        pixels_per_sec = (256 * 256) / cpu_time
        print(f"  Throughput: {pixels_per_sec/1e6:.2f} MPixels/s")
        return

    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")

    # Test different sizes - GPU benefits show at larger sizes
    test_sizes = [512, 1024]  # Test with larger sizes where GPU shines

    for size in test_sizes:
        print(f"\n{'='*50}")
        print(f"Testing {size}x{size} detector ({size*size:,} pixels)")
        print('-'*50)

        # CPU test
        print(f"\nCPU Performance:")
        cpu_time, cpu_std, cpu_image = run_simulation(torch.device('cpu'), size)
        print(f"  Average: {cpu_time:.4f}s ± {cpu_std:.4f}s")

        # GPU test
        print(f"\nGPU Performance:")
        gpu_time, gpu_std, gpu_image = run_simulation(torch.device('cuda'), size)
        print(f"  Average: {gpu_time:.4f}s ± {gpu_std:.4f}s")

        # Comparison
        speedup = cpu_time / gpu_time
        print(f"\n  🚀 GPU Speedup: {speedup:.1f}x")

        # Verify results match
        cpu_np = cpu_image.cpu().numpy()
        gpu_np = gpu_image.cpu().numpy()
        correlation = np.corrcoef(cpu_np.flatten(), gpu_np.flatten())[0, 1]
        print(f"  ✓ CPU/GPU correlation: {correlation:.6f}")

        # Throughput
        cpu_throughput = (size * size) / cpu_time / 1e6
        gpu_throughput = (size * size) / gpu_time / 1e6
        print(f"  CPU throughput: {cpu_throughput:.2f} MPixels/s")
        print(f"  GPU throughput: {gpu_throughput:.2f} MPixels/s")

        # Memory usage
        if size <= 512:  # Don't test memory for large sizes
            print(f"  GPU memory used: {torch.cuda.memory_allocated()/1024**2:.1f} MB")

    print("\n" + "="*60)
    print("Summary")
    print("="*60)

    if speedup > 10:
        print(f"✅ GPU acceleration is working excellently! ({speedup:.1f}x speedup)")
    elif speedup > 5:
        print(f"✅ GPU acceleration is working well! ({speedup:.1f}x speedup)")
    elif speedup > 1:
        print(f"⚠️ GPU acceleration is working but slower than expected ({speedup:.1f}x speedup)")
    else:
        print(f"❌ GPU is slower than CPU! Something is wrong.")

if __name__ == "__main__":
    main()
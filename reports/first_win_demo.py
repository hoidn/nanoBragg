#!/usr/bin/env python3
"""
Demo script for simple_cubic image reproduction with PyTorch nanoBragg.

This script generates visual assets and timing comparisons for the first win demo,
demonstrating correctness, performance potential, and differentiability.
"""

import os
import time
from pathlib import Path

import fabio
import matplotlib.pyplot as plt
import numpy as np
import torch

# Set environment for PyTorch
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def main():
    """Run the demo and generate all artifacts."""
    print("=== nanoBragg PyTorch First Win Demo ===")
    
    # Set seed for reproducibility
    torch.manual_seed(0)
    print("✓ Set random seed for reproducibility")
    
    # Setup paths
    project_root = Path(__file__).parent.parent
    golden_data_dir = project_root / "tests" / "golden_data"
    hkl_path = project_root / "simple_cubic.hkl"
    output_dir = Path(__file__).parent
    
    print(f"✓ Project root: {project_root}")
    print(f"✓ Golden data: {golden_data_dir}")
    print(f"✓ HKL file: {hkl_path}")
    print(f"✓ Output directory: {output_dir}")
    
    # Load golden image
    print("\n--- Loading Golden Reference ---")
    golden_img_path = golden_data_dir / "simple_cubic.img"
    golden_img = fabio.open(str(golden_img_path))
    golden_data = golden_img.data.astype(np.float64)
    print(f"✓ Loaded golden image: {golden_data.shape}")
    print(f"✓ Golden stats: max={np.max(golden_data):.2e}, mean={np.mean(golden_data):.2e}")
    
    # Create PyTorch simulation
    print("\n--- Setting up PyTorch Simulation ---")
    device_cpu = torch.device("cpu")
    dtype = torch.float64
    
    crystal = Crystal(device=device_cpu, dtype=dtype)
    detector = Detector(device=device_cpu, dtype=dtype)
    simulator = Simulator(crystal, detector, device=device_cpu, dtype=dtype)
    
    # Load HKL data
    crystal.load_hkl(str(hkl_path))
    print(f"✓ Loaded HKL data: {crystal.hkl_data.shape[0] if crystal.hkl_data is not None else 0} reflections")
    
    # Run CPU simulation with timing
    print("\n--- Running CPU Simulation ---")
    start_time = time.time()
    pytorch_image_cpu = simulator.run()
    end_time = time.time()
    cpu_time = end_time - start_time
    
    pytorch_np_cpu = pytorch_image_cpu.cpu().numpy()
    print(f"✓ CPU simulation completed in {cpu_time:.3f} seconds")
    print(f"✓ PyTorch CPU stats: max={np.max(pytorch_np_cpu):.2e}, mean={np.mean(pytorch_np_cpu):.2e}")
    
    # Try GPU simulation if available
    gpu_time = None
    pytorch_np_gpu = None
    if torch.cuda.is_available():
        print("\n--- Running GPU Simulation ---")
        device_gpu = torch.device("cuda")
        crystal_gpu = Crystal(device=device_gpu, dtype=dtype)
        detector_gpu = Detector(device=device_gpu, dtype=dtype)
        simulator_gpu = Simulator(crystal_gpu, detector_gpu, device=device_gpu, dtype=dtype)
        crystal_gpu.load_hkl(str(hkl_path))
        
        # Warm up GPU
        _ = simulator_gpu.run()
        torch.cuda.synchronize()
        
        # Timed run
        torch.cuda.synchronize()
        start_time = time.time()
        pytorch_image_gpu = simulator_gpu.run()
        torch.cuda.synchronize()
        end_time = time.time()
        gpu_time = end_time - start_time
        
        pytorch_np_gpu = pytorch_image_gpu.cpu().numpy()
        print(f"✓ GPU simulation completed in {gpu_time:.3f} seconds")
        print(f"✓ Speedup: {cpu_time/gpu_time:.2f}x")
    else:
        print("\n--- GPU Not Available ---")
        print("ℹ GPU simulation skipped")
    
    # Create visualizations
    print("\n--- Creating Visualizations ---")
    
    # Figure 1: Side-by-side images
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    
    # Golden image
    im1 = axes[0].imshow(golden_data, cmap='inferno', origin='lower')
    axes[0].set_title('Golden Reference (C code)')
    axes[0].set_xlabel('Fast pixels')
    axes[0].set_ylabel('Slow pixels')
    plt.colorbar(im1, ax=axes[0])
    
    # PyTorch image (CPU)
    im2 = axes[1].imshow(pytorch_np_cpu, cmap='inferno', origin='lower')
    axes[1].set_title('PyTorch Implementation (CPU)')
    axes[1].set_xlabel('Fast pixels')
    axes[1].set_ylabel('Slow pixels')
    plt.colorbar(im2, ax=axes[1])
    
    plt.tight_layout()
    plt.savefig(output_dir / 'side_by_side_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: side_by_side_comparison.png")
    plt.close()
    
    # Figure 2: Difference heatmap
    diff_data = np.abs(golden_data - pytorch_np_cpu)
    log_diff = np.log1p(diff_data)  # log(1 + |golden - pytorch|) to make discrepancies visible
    
    plt.figure(figsize=(8, 6))
    im = plt.imshow(log_diff, cmap='plasma', origin='lower')
    plt.title('Difference Heatmap: log(1 + |Golden - PyTorch|)')
    plt.xlabel('Fast pixels')
    plt.ylabel('Slow pixels')
    plt.colorbar(im, label='log(1 + |difference|)')
    plt.tight_layout()
    plt.savefig(output_dir / 'difference_heatmap.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: difference_heatmap.png")
    plt.close()
    
    # Figure 3: Timing comparison
    fig, ax = plt.subplots(figsize=(8, 5))
    devices = ['CPU']
    times = [cpu_time]
    colors = ['skyblue']
    
    if gpu_time is not None:
        devices.append('GPU')
        times.append(gpu_time)
        colors.append('lightcoral')
    
    bars = ax.bar(devices, times, color=colors)
    ax.set_ylabel('Time (seconds)')
    ax.set_title('PyTorch nanoBragg Performance Comparison')
    
    # Add value labels on bars
    for bar, time_val in zip(bars, times):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                f'{time_val:.3f}s', ha='center', va='bottom')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'timing_comparison.png', dpi=150, bbox_inches='tight')
    print("✓ Saved: timing_comparison.png")
    plt.close()
    
    # Test differentiability with gradcheck on a small crop
    print("\n--- Testing Differentiability ---")
    try:
        # Create a smaller version for gradcheck (3x3 to keep memory usage low)
        device_test = torch.device("cpu")
        crystal_test = Crystal(device=device_test, dtype=dtype)
        detector_test = Detector(device=device_test, dtype=dtype)
        
        # Override detector size for small test
        detector_test.spixels = 3
        detector_test.fpixels = 3
        detector_test.invalidate_cache()  # Clear cache
        
        simulator_test = Simulator(crystal_test, detector_test, device=device_test, dtype=dtype)
        crystal_test.load_hkl(str(hkl_path))
        
        # Make cell_a parameter require gradients
        crystal_test.cell_a = torch.tensor(100.0, requires_grad=True, dtype=dtype)
        
        def test_func(cell_a_param):
            # Re-calculate a_star inside the function to keep it in the graph
            a_star_new = crystal_test.calculate_reciprocal_vectors(cell_a_param)
            # Pass the new tensor to the simulator to avoid graph breaks
            result = simulator_test.run(override_a_star=a_star_new)
            return torch.sum(result)  # Return scalar for gradcheck
        
        # Run gradcheck
        input_param = torch.tensor(100.0, requires_grad=True, dtype=torch.float64)
        gradcheck_result = torch.autograd.gradcheck(test_func, input_param, eps=1e-6, atol=1e-4)
        print(f"✓ Gradient check passed: {gradcheck_result}")
        
    except Exception as e:
        print(f"⚠ Gradient check failed: {e}")
        gradcheck_result = False
    
    # Print summary statistics
    print("\n--- Summary Statistics ---")
    max_diff = np.max(diff_data)
    mean_diff = np.mean(diff_data)
    relative_error = mean_diff / np.mean(golden_data) if np.mean(golden_data) > 0 else float('inf')
    
    print(f"Max absolute difference: {max_diff:.2e}")
    print(f"Mean absolute difference: {mean_diff:.2e}")
    print(f"Relative error: {relative_error:.2e}")
    print(f"CPU simulation time: {cpu_time:.3f}s")
    if gpu_time is not None:
        print(f"GPU simulation time: {gpu_time:.3f}s")
        print(f"GPU speedup: {cpu_time/gpu_time:.2f}x")
    print(f"Differentiable: {'✓' if gradcheck_result else '✗'}")
    
    print("\n=== Demo Complete ===")
    print(f"Generated files in: {output_dir}")
    print("- side_by_side_comparison.png")
    print("- difference_heatmap.png")
    print("- timing_comparison.png")


if __name__ == "__main__":
    main()
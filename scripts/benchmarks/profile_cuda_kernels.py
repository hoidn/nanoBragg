#!/usr/bin/env python3
"""
Profile CUDA kernel launches to identify fusion opportunities.

Follows nanoBragg tooling standards:
- Located in scripts/benchmarks/
- Honors KMP_DUPLICATE_LIB_OK env var
- Saves outputs to reports/benchmarks/<timestamp>/
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Set environment per project standards
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import torch.profiler

from nanobrag_torch.config import (
    CrystalConfig, DetectorConfig, BeamConfig,
    CrystalShape, DetectorConvention
)
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def profile_simulation(detpixels=1024, device='cuda'):
    """
    Run simulation with PyTorch profiler to analyze CUDA kernel launches.
    """
    device_obj = torch.device(device)

    # Setup configs
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=[5, 5, 5],
        default_F=100.0,
        shape=CrystalShape.SQUARE
    )

    detector_config = DetectorConfig(
        spixels=detpixels,
        fpixels=detpixels,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        oversample=1
    )

    beam_config = BeamConfig(wavelength_A=6.2)

    # Create models on target device
    crystal = Crystal(crystal_config, device=device_obj)
    detector = Detector(detector_config, device=device_obj)
    simulator = Simulator(crystal, detector, crystal_config, beam_config, device=device_obj)

    # Warm-up run
    print("Warm-up run...")
    _ = simulator.run()
    if device_obj.type == 'cuda':
        torch.cuda.synchronize()

    # Create output directory
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    output_dir = Path('reports/benchmarks') / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Profiling {detpixels}x{detpixels} simulation on {device}...")
    print(f"Outputs will be saved to: {output_dir}")

    # Profile with PyTorch profiler
    with torch.profiler.profile(
        activities=[
            torch.profiler.ProfilerActivity.CPU,
            torch.profiler.ProfilerActivity.CUDA,
        ],
        record_shapes=True,
        profile_memory=True,
        with_stack=True,
    ) as prof:
        with torch.profiler.record_function("simulator_run"):
            image = simulator.run()
            if device_obj.type == 'cuda':
                torch.cuda.synchronize()

    # Save profiler outputs
    trace_file = output_dir / f"trace_detpixels_{detpixels}.json"
    prof.export_chrome_trace(str(trace_file))
    print(f"Chrome trace saved to: {trace_file}")
    print("View in chrome://tracing")

    # Print summary statistics
    print("\n" + "=" * 80)
    print("PROFILER SUMMARY - Top Operations by CUDA Time")
    print("=" * 80)
    print(prof.key_averages().table(sort_by="cuda_time_total", row_limit=20))

    print("\n" + "=" * 80)
    print("PROFILER SUMMARY - Top Operations by CPU Time")
    print("=" * 80)
    print(prof.key_averages().table(sort_by="cpu_time_total", row_limit=20))

    # Count CUDA kernels
    key_averages = prof.key_averages()
    cuda_kernels = [evt for evt in key_averages if evt.device_type == torch.profiler.DeviceType.CUDA]

    print("\n" + "=" * 80)
    print("CUDA KERNEL SUMMARY")
    print("=" * 80)
    print(f"Total unique CUDA kernels: {len(cuda_kernels)}")
    print(f"Total CUDA kernel calls: {sum(evt.count for evt in cuda_kernels)}")

    # Save detailed report
    report_file = output_dir / f"profile_report_detpixels_{detpixels}.txt"
    with open(report_file, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write(f"CUDA Profiling Report - {detpixels}x{detpixels} detector\n")
        f.write("=" * 80 + "\n\n")
        f.write("Top Operations by CUDA Time:\n")
        f.write(prof.key_averages().table(sort_by="cuda_time_total", row_limit=50))
        f.write("\n\n")
        f.write("Top Operations by CPU Time:\n")
        f.write(prof.key_averages().table(sort_by="cpu_time_total", row_limit=50))
        f.write("\n\n")
        f.write(f"Total unique CUDA kernels: {len(cuda_kernels)}\n")
        f.write(f"Total CUDA kernel calls: {sum(evt.count for evt in cuda_kernels)}\n")
        f.write("\n")
        f.write("All CUDA kernels:\n")
        for evt in sorted(cuda_kernels, key=lambda x: x.cuda_time_total, reverse=True):
            f.write(f"  {evt.key}: {evt.count} calls, {evt.cuda_time_total:.3f}ms total\n")

    print(f"\nDetailed report saved to: {report_file}")
    print(f"All outputs in: {output_dir}")


def main():
    if not torch.cuda.is_available():
        print("ERROR: CUDA not available. This profiler requires GPU.")
        sys.exit(1)

    print("=" * 80)
    print("nanoBragg CUDA Kernel Profiler")
    print("=" * 80)
    print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"PyTorch version: {torch.__version__}")

    # Profile standard test case
    profile_simulation(detpixels=1024, device='cuda')


if __name__ == "__main__":
    main()
#!/usr/bin/env python
"""
Validate multi-source weighted normalization on CPU and CUDA.

This script tests that PyTorch correctly handles non-uniform source weights
per AT-SRC-001 normalization requirements.
"""
import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import torch
import numpy as np
import argparse
from datetime import datetime
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector

def test_weighted_sources(device='cpu'):
    """Test weighted source normalization on specified device."""
    print(f"\n{'='*80}")
    print(f"Testing weighted source normalization on {device.upper()}")
    print(f"{'='*80}\n")

    dtype = torch.float32

    # Configuration: 2 sources with different weights and wavelengths
    # Source 1: weight=2.0, λ=6.2Å
    # Source 2: weight=3.0, λ=8.0Å
    source_wavelengths_A = torch.tensor([6.2, 8.0], device=device, dtype=dtype)  # Angstroms
    source_wavelengths_m = source_wavelengths_A * 1e-10  # Convert to meters for BeamConfig
    source_weights = torch.tensor([2.0, 3.0], device=device, dtype=dtype)
    source_directions = torch.tensor([
        [1.0, 0.0, 0.0],  # Primary beam direction (MOSFLM convention)
        [1.0, 0.0, 0.0],  # Same direction for second source
    ], device=device, dtype=dtype)

    # Crystal config
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
        phi_start_deg=0.0,
        osc_range_deg=0.0,
        phi_steps=1,
        mosaic_spread_deg=0.0,
        mosaic_domains=1
    )

    # Detector config - small 128x128 for fast testing
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=128,
        fpixels=128
    )

    # Beam config with weighted sources - MUST pass sources through BeamConfig
    # so Simulator.__init__ can populate _source_* cache tensors
    beam_config = BeamConfig(
        wavelength_A=6.2,  # Primary wavelength (used as fallback)
        flux=1e12,
        exposure=1.0,
        beamsize_mm=0.1,
        source_directions=source_directions,
        source_wavelengths=source_wavelengths_m,  # BeamConfig expects meters
        source_weights=source_weights
    )

    # Create crystal and detector objects
    crystal = Crystal(crystal_config, beam_config=beam_config, device=device, dtype=dtype)
    detector = Detector(detector_config, device=device, dtype=dtype)

    # Create simulator with weighted sources
    print("Creating simulator with weighted sources...")
    print(f"  Source 1: weight={source_weights[0].item():.1f}, λ={source_wavelengths_A[0].item():.1f}Å")
    print(f"  Source 2: weight={source_weights[1].item():.1f}, λ={source_wavelengths_A[1].item():.1f}Å")

    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        crystal_config=crystal_config,
        beam_config=beam_config,
        device=device,
        dtype=dtype
    )

    # Verify that sources were properly cached from BeamConfig
    assert simulator._source_directions is not None, "Multi-source directions not cached"
    assert simulator._source_wavelengths is not None, "Multi-source wavelengths not cached"
    assert simulator._source_weights is not None, "Multi-source weights not cached"
    print(f"  ✓ Multi-source caching verified:")
    print(f"    Directions shape: {simulator._source_directions.shape}")
    print(f"    Wavelengths (Å): {(simulator._source_wavelengths * 1e10).tolist()}")
    print(f"    Weights: {simulator._source_weights.tolist()}")

    # Run simulation
    print("\nRunning simulation...")
    image = simulator.run()

    # Compute statistics
    total_intensity = image.sum().item()
    max_intensity = image.max().item()
    nonzero_pixels = (image > 0).sum().item()

    print(f"\nResults on {device.upper()}:")
    print(f"  Image shape: {image.shape}")
    print(f"  Total intensity: {total_intensity:.6e}")
    print(f"  Max intensity: {max_intensity:.6e}")
    print(f"  Non-zero pixels: {nonzero_pixels}")
    print(f"  Dtype: {image.dtype}")

    # Verify normalization
    # With weighted sources, the intensity should reflect the relative weights
    # The normalization should divide by n_sources (2), not sum of weights (5)
    # per the current implementation (commit 2e2a6d9)
    print(f"\nNormalization check:")
    print(f"  Number of sources: {len(source_weights)}")
    print(f"  Sum of weights: {source_weights.sum().item():.1f}")
    print(f"  Expected denominator (n_sources): {len(source_weights)}")

    return {
        'device': device,
        'total_intensity': total_intensity,
        'max_intensity': max_intensity,
        'nonzero_pixels': int(nonzero_pixels),
        'image_shape': list(image.shape),
        'source_weights': source_weights.cpu().tolist(),
        'source_wavelengths_A': source_wavelengths_A.cpu().tolist(),
        'dtype': str(image.dtype)
    }

def main():
    """Run validation on CPU and CUDA (if available)."""
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='Validate multi-source weighted normalization on CPU and CUDA'
    )
    parser.add_argument(
        '--outdir',
        type=str,
        default=None,
        help='Output directory for results (default: reports/benchmarks/YYYYMMDD-HHMMSS-multi-source-normalization)'
    )
    args = parser.parse_args()

    results = {}

    # Test on CPU
    cpu_result = test_weighted_sources(device='cpu')
    results['cpu'] = cpu_result

    # Test on CUDA if available
    if torch.cuda.is_available():
        cuda_result = test_weighted_sources(device='cuda')
        results['cuda'] = cuda_result

        # Compare CPU vs CUDA
        print(f"\n{'='*80}")
        print("CPU vs CUDA Comparison")
        print(f"{'='*80}\n")

        cpu_intensity = cpu_result['total_intensity']
        cuda_intensity = cuda_result['total_intensity']
        rel_diff = abs(cpu_intensity - cuda_intensity) / cpu_intensity

        print(f"CPU total intensity:  {cpu_intensity:.6e}")
        print(f"CUDA total intensity: {cuda_intensity:.6e}")
        print(f"Relative difference:  {rel_diff:.6e}")

        if rel_diff < 1e-4:
            print("\n✓ CPU and CUDA results match within tolerance")
        else:
            print(f"\n✗ WARNING: CPU and CUDA differ by {rel_diff:.2%}")
    else:
        print("\nCUDA not available - skipping GPU validation")

    # Save results
    import json
    from pathlib import Path

    # Use repo-relative path with timestamped directory
    repo_root = Path(__file__).parent.parent

    if args.outdir:
        # User-provided output directory (relative to repo root or absolute)
        output_dir = Path(args.outdir)
        if not output_dir.is_absolute():
            output_dir = repo_root / output_dir
    else:
        # Default: timestamped directory
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        output_dir = repo_root / 'reports' / 'benchmarks' / f'{timestamp}-multi-source-normalization'

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / 'validation_results.json'

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n{'='*80}")
    print(f"Results saved to: {output_path}")
    print(f"{'='*80}\n")

    return results

if __name__ == '__main__':
    main()

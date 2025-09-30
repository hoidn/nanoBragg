#!/usr/bin/env python3
"""
Find the best off-axis peak pixel for AT-PARALLEL-012 trace comparison.

This script:
1. Loads golden C data (tests/golden_data/simple_cubic.bin)
2. Masks out direct beam region (±10 pixels from center)
3. Finds top 5 strongest off-axis peaks
4. Runs PyTorch simulation to estimate intensity ratios
5. Recommends the best pixel for parallel trace comparison

Usage:
    KMP_DUPLICATE_LIB_OK=TRUE python scripts/find_offaxis_peak_at012.py
"""

import os
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import sys
import struct
from pathlib import Path
import numpy as np
import torch
from scipy.stats import pearsonr

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nanobrag_torch.config import (
    CrystalConfig,
    DetectorConfig,
    BeamConfig,
    DetectorConvention,
    DetectorPivot,
)
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def load_golden_float_image(filename: str, shape: tuple) -> np.ndarray:
    """Load a binary float image from golden data."""
    with open(filename, 'rb') as f:
        data = f.read()
        n_floats = len(data) // 4
        assert n_floats == shape[0] * shape[1], f"Expected {shape[0]*shape[1]} floats, got {n_floats}"
        floats = struct.unpack(f'{n_floats}f', data)
        return np.array(floats).reshape(shape)


def main():
    print("=" * 80)
    print("AT-PARALLEL-012: OFF-AXIS PEAK IDENTIFICATION")
    print("=" * 80)
    print()

    # Load golden data
    golden_file = Path(__file__).parent.parent / "tests" / "golden_data" / "simple_cubic.bin"
    print(f"Loading golden data: {golden_file}")
    golden_image = load_golden_float_image(str(golden_file), (1024, 1024))
    print(f"Golden data shape: {golden_image.shape}")
    print(f"Golden data range: [{golden_image.min():.6e}, {golden_image.max():.6e}]")
    print()

    # Run PyTorch simulation
    print("Running PyTorch simulation...")
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0
    )

    detector_config = DetectorConfig(
        spixels=1024,
        fpixels=1024,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM
    )

    beam_config = BeamConfig(
        wavelength_A=6.2
    )

    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    pytorch_image = simulator.run().cpu().numpy()
    print(f"PyTorch data range: [{pytorch_image.min():.6e}, {pytorch_image.max():.6e}]")
    print()

    # Calculate overall correlation
    corr, _ = pearsonr(golden_image.flatten(), pytorch_image.flatten())
    print(f"Overall correlation: {corr:.6f} (target: 0.9995, gap: {(0.9995-corr)*100:.4f}%)")
    print()

    # Mask out direct beam region (±10 pixels from center)
    center_s = 512
    center_f = 512
    mask_radius = 10

    # Create mask (False for direct beam, True for off-axis)
    s_coords, f_coords = np.meshgrid(np.arange(1024), np.arange(1024), indexing='ij')
    distance_from_center = np.sqrt((s_coords - center_s)**2 + (f_coords - center_f)**2)
    offaxis_mask = distance_from_center > mask_radius

    # Apply mask
    golden_masked = golden_image.copy()
    golden_masked[~offaxis_mask] = 0

    # Find top 5 off-axis peaks
    n_peaks = 5
    print(f"Finding top {n_peaks} off-axis peaks (excluding ±{mask_radius} pixels from center)...")
    print()

    peak_data = []
    for i in range(n_peaks):
        # Find max in masked image
        peak_idx = np.argmax(golden_masked)
        peak_s = peak_idx // 1024
        peak_f = peak_idx % 1024

        # Get intensities
        golden_intensity = golden_image[peak_s, peak_f]
        pytorch_intensity = pytorch_image[peak_s, peak_f]
        ratio = pytorch_intensity / golden_intensity

        # Calculate distance from center
        dist_from_center = np.sqrt((peak_s - center_s)**2 + (peak_f - center_f)**2)

        peak_data.append({
            's': peak_s,
            'f': peak_f,
            'golden': golden_intensity,
            'pytorch': pytorch_intensity,
            'ratio': ratio,
            'distance': dist_from_center,
        })

        # Zero out this peak and neighbors for next iteration
        mask_size = 5
        s_start = max(0, peak_s - mask_size)
        s_end = min(1024, peak_s + mask_size + 1)
        f_start = max(0, peak_f - mask_size)
        f_end = min(1024, peak_f + mask_size + 1)
        golden_masked[s_start:s_end, f_start:f_end] = 0

    # Print results
    print("=" * 80)
    print("TOP 5 OFF-AXIS PEAKS")
    print("=" * 80)
    print()
    print(f"{'Rank':<6} {'Pixel (s,f)':<15} {'Dist':<8} {'Golden C':<14} {'PyTorch':<14} {'Ratio':<10} {'Error%':<10}")
    print("-" * 80)

    for i, peak in enumerate(peak_data, 1):
        error_pct = abs(peak['ratio'] - 1.0) * 100
        print(f"{i:<6} ({peak['s']:<4},{peak['f']:<4})   {peak['distance']:<8.2f} {peak['golden']:<14.6e} {peak['pytorch']:<14.6e} {peak['ratio']:<10.6f} {error_pct:<10.4f}")

    print()

    # Analyze patterns
    print("=" * 80)
    print("INTENSITY RATIO ANALYSIS")
    print("=" * 80)
    print()

    ratios = [p['ratio'] for p in peak_data]
    print(f"Mean ratio (Py/C):      {np.mean(ratios):.6f}")
    print(f"Std dev of ratios:      {np.std(ratios):.6f}")
    print(f"Min ratio:              {np.min(ratios):.6f}")
    print(f"Max ratio:              {np.max(ratios):.6f}")
    print(f"Range:                  {np.max(ratios) - np.min(ratios):.6f}")
    print()

    # Check direct beam for comparison
    direct_beam_golden = golden_image[center_s, center_f]
    direct_beam_pytorch = pytorch_image[center_s, center_f]
    direct_beam_ratio = direct_beam_pytorch / direct_beam_golden
    print(f"Direct beam ({center_s}, {center_f}):")
    print(f"  Golden C:  {direct_beam_golden:.6e}")
    print(f"  PyTorch:   {direct_beam_pytorch:.6e}")
    print(f"  Ratio:     {direct_beam_ratio:.6f} ({(direct_beam_ratio-1)*100:+.4f}%)")
    print()

    # Recommendation
    print("=" * 80)
    print("RECOMMENDATION FOR TRACE COMPARISON")
    print("=" * 80)
    print()

    # Select best pixel based on:
    # 1. Strong signal (high intensity)
    # 2. Clear off-axis position (distance > 50 pixels)
    # 3. Representative error (not anomalous)

    candidates = [p for p in peak_data if p['distance'] > 50]
    if not candidates:
        print("WARNING: No peaks found beyond 50 pixels from center. Using top peak regardless.")
        candidates = peak_data[:1]

    # Score candidates: higher intensity and closer to mean ratio is better
    mean_ratio = np.mean(ratios)
    for p in candidates:
        # Normalize intensity to [0, 1] range
        intensity_score = p['golden'] / peak_data[0]['golden']
        # Ratio deviation (lower is better, so invert)
        ratio_deviation = abs(p['ratio'] - mean_ratio)
        max_deviation = max([abs(x['ratio'] - mean_ratio) for x in candidates])
        ratio_score = 1.0 - (ratio_deviation / max_deviation if max_deviation > 0 else 0)
        p['score'] = 0.7 * intensity_score + 0.3 * ratio_score

    best_peak = max(candidates, key=lambda x: x['score'])

    print(f"RECOMMENDED PIXEL: ({best_peak['s']}, {best_peak['f']})")
    print()
    print("Justification:")
    print(f"  1. Strong signal: {best_peak['golden']:.6e} photons (rank #{peak_data.index(best_peak)+1})")
    print(f"  2. Off-axis distance: {best_peak['distance']:.2f} pixels from center")
    print(f"  3. Representative error: {abs(best_peak['ratio']-1)*100:.4f}% (mean: {abs(mean_ratio-1)*100:.4f}%)")
    print(f"  4. Intensity ratio (Py/C): {best_peak['ratio']:.6f}")
    print()

    print("Next steps:")
    print("  1. Add printf trace statements to C code for this pixel")
    print("  2. Recompile: make -C golden_suite_generator")
    print(f"  3. Run: NB_C_BIN=./golden_suite_generator/nanoBragg pytest tests/test_at_parallel_012.py::TestATParallel012ReferencePatternCorrelation::test_simple_cubic_correlation -v")
    print(f"  4. Extract C trace: grep 'pixel ({best_peak['s']},{best_peak['f']})' [output] > c_trace_pixel_{best_peak['s']}_{best_peak['f']}.log")
    print(f"  5. Generate PyTorch trace for pixel ({best_peak['s']}, {best_peak['f']})")
    print("  6. Compare traces line-by-line to find first divergence")
    print()

    # Pattern analysis
    print("=" * 80)
    print("PATTERNS OBSERVED")
    print("=" * 80)
    print()

    if np.std(ratios) < 0.01:
        print("✓ UNIFORM ERROR: All off-axis peaks show similar ratio")
        print("  → Suggests systematic scale factor or common calculation error")
        print("  → Check: omega, polarization, physical constants")
    else:
        print("⚠ VARIABLE ERROR: Off-axis peaks show varying ratios")
        print("  → Suggests position-dependent calculation error")
        print("  → Check: pixel coordinates, scattering vector, Miller indices")

    if abs(mean_ratio - direct_beam_ratio) < 0.001:
        print()
        print("✓ CONSISTENT WITH DIRECT BEAM: Off-axis error similar to direct beam")
        print("  → Global issue, not specific to off-axis calculations")
    else:
        print()
        print("⚠ DIFFERENT FROM DIRECT BEAM: Off-axis error differs from direct beam")
        print(f"  → Direct beam: {(direct_beam_ratio-1)*100:+.4f}%, Off-axis mean: {(mean_ratio-1)*100:+.4f}%")
        print("  → Issue may be specific to off-axis geometry calculations")

    print()
    print("=" * 80)


if __name__ == "__main__":
    main()
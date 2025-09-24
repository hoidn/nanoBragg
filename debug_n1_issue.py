#!/usr/bin/env python3
"""
Debug N=1 edge case issue.

The problem: N=1 (single unit cell) has correlation of only 0.024 with C reference,
while N≥5 has correlation >0.998. This suggests a fundamental issue with how
the shape factors (F_latt) are calculated for single unit cells.
"""

import os
import sys
import torch
import numpy as np
import tempfile
import subprocess
from pathlib import Path

# Set PyTorch environment
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.nanobrag_torch.config import (
    CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention, CrystalShape
)
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.simulator import Simulator


def get_c_binary():
    """Get path to C binary."""
    if "NB_C_BIN" in os.environ:
        return Path(os.environ["NB_C_BIN"])

    paths = [
        Path("./golden_suite_generator/nanoBragg"),
        Path("./nanoBragg")
    ]

    for p in paths:
        if p.exists():
            return p.resolve()
    return None


def run_pytorch_simulation(N, shape=CrystalShape.SQUARE, debug_output=False):
    """Run PyTorch simulation with given N."""
    # Common parameters matching test_at_parallel_009.py
    crystal_config = CrystalConfig(
        cell_a=100, cell_b=100, cell_c=100,
        cell_alpha=90, cell_beta=90, cell_gamma=90,
        N_cells=(N, N, N),
        default_F=100.0,
        phi_start_deg=0, osc_range_deg=0,
        mosaic_spread_deg=0,
        shape=shape
    )

    detector_config = DetectorConfig(
        spixels=256, fpixels=256,
        pixel_size_mm=0.1, distance_mm=100,
        detector_convention=DetectorConvention.MOSFLM,
        oversample=1, point_pixel=False
    )

    beam_config = BeamConfig(wavelength_A=1.0)

    # Create components and run
    crystal = Crystal(crystal_config)
    detector = Detector(detector_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)
    image = simulator.run()

    if debug_output:
        print(f"\nPyTorch N={N} simulation:")
        print(f"  Crystal size: {crystal.N_cells_a} x {crystal.N_cells_b} x {crystal.N_cells_c}")
        print(f"  Max intensity: {torch.max(image):.2e}")
        print(f"  Mean intensity: {torch.mean(image):.2e}")
        print(f"  Shape factor type: {shape}")

        # Check lattice vectors
        print(f"  |a|: {torch.norm(crystal.a):.3f} Å")
        print(f"  |b|: {torch.norm(crystal.b):.3f} Å")
        print(f"  |c|: {torch.norm(crystal.c):.3f} Å")

        # Get a few pixels to show physics calculations
        # Center pixel (128, 128) - should have strong signal
        pixel_coords = detector.get_pixel_coords()
        center_coord = pixel_coords[128, 128] * 1e10  # Convert to Angstroms

        print(f"  Center pixel coords (Å): {center_coord}")

        # Calculate scattering vector for center pixel
        incident_beam_direction = torch.tensor([1.0, 0.0, 0.0])
        pixel_magnitude = torch.norm(center_coord)
        diffracted_beam_unit = center_coord / pixel_magnitude
        scattering_vector = (diffracted_beam_unit - incident_beam_direction) / beam_config.wavelength_A

        print(f"  Scattering vector: {scattering_vector}")

        # Calculate Miller indices
        h = torch.dot(scattering_vector, crystal.a)
        k = torch.dot(scattering_vector, crystal.b)
        l = torch.dot(scattering_vector, crystal.c)

        print(f"  Miller indices: h={h:.3f}, k={k:.3f}, l={l:.3f}")

        # Get nearest integers
        h0, k0, l0 = torch.round(h), torch.round(k), torch.round(l)
        print(f"  Nearest integers: h0={h0}, k0={k0}, l0={l0}")

        # Calculate shape factors
        from src.nanobrag_torch.utils.physics import sincg

        if shape == CrystalShape.SQUARE:
            u_h = torch.pi * (h - h0)
            u_k = torch.pi * (k - k0)
            u_l = torch.pi * (l - l0)

            F_latt_a = sincg(u_h, torch.tensor(float(N)))
            F_latt_b = sincg(u_k, torch.tensor(float(N)))
            F_latt_c = sincg(u_l, torch.tensor(float(N)))
            F_latt = F_latt_a * F_latt_b * F_latt_c

            print(f"  Shape factor inputs: u_h={u_h:.6f}, u_k={u_k:.6f}, u_l={u_l:.6f}")
            print(f"  Individual shape factors: F_a={F_latt_a:.6f}, F_b={F_latt_b:.6f}, F_c={F_latt_c:.6f}")
            print(f"  Combined lattice factor: F_latt={F_latt:.6f}")

        print(f"  Structure factor F_cell: {crystal_config.default_F}")
        print(f"  Total intensity |F_total|²: {(crystal_config.default_F * F_latt)**2:.6f}")

    return image.detach().cpu().numpy()


def run_c_simulation(N, debug_output=False):
    """Run C reference simulation with given N."""
    c_binary = get_c_binary()
    if not c_binary:
        raise RuntimeError("C binary not found")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        float_file = tmpdir / "floatimage.bin"

        cmd = [
            str(c_binary),
            "-cell", "100", "100", "100", "90", "90", "90",
            "-lambda", "1.0", "-distance", "100", "-detpixels", "256", "-pixel", "0.1",
            "-phi", "0", "-osc", "0", "-mosaic", "0", "-oversample", "1",
            "-default_F", "100", "-N", str(N), "-mosflm",
            "-floatfile", str(float_file)
        ]

        if debug_output:
            print(f"\nC N={N} command: " + " ".join(cmd))

        result = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"C simulation failed: {result.stderr}")

        if debug_output and result.stdout:
            print(f"C stdout:\n{result.stdout}")

        image = np.fromfile(str(float_file), dtype=np.float32).reshape(256, 256)

        if debug_output:
            print(f"C N={N} simulation:")
            print(f"  Max intensity: {np.max(image):.2e}")
            print(f"  Mean intensity: {np.mean(image):.2e}")

        return image


def analyze_correlation(py_image, c_image, N):
    """Analyze correlation between PyTorch and C images."""
    # Flatten images
    py_flat = py_image.flatten()
    c_flat = c_image.flatten()

    # Calculate correlation coefficient
    correlation = np.corrcoef(py_flat, c_flat)[0, 1]

    # Calculate RMSE
    rmse = np.sqrt(np.mean((py_flat - c_flat)**2))

    # Calculate relative RMSE
    c_mean = np.mean(c_flat)
    rel_rmse = rmse / c_mean if c_mean > 0 else np.inf

    # Calculate intensity ratio
    py_max = np.max(py_flat)
    c_max = np.max(c_flat)
    intensity_ratio = py_max / c_max if c_max > 0 else np.inf

    print(f"\nN={N} Analysis:")
    print(f"  Correlation: {correlation:.6f}")
    print(f"  RMSE: {rmse:.2e}")
    print(f"  Relative RMSE: {rel_rmse:.3f}")
    print(f"  PyTorch max intensity: {py_max:.2e}")
    print(f"  C max intensity: {c_max:.2e}")
    print(f"  Intensity ratio (Py/C): {intensity_ratio:.6f}")

    # Find peak positions
    py_peak_idx = np.unravel_index(np.argmax(py_flat), py_image.shape)
    c_peak_idx = np.unravel_index(np.argmax(c_flat), c_image.shape)

    print(f"  PyTorch peak position: {py_peak_idx}")
    print(f"  C peak position: {c_peak_idx}")
    print(f"  Peak offset: {np.array(py_peak_idx) - np.array(c_peak_idx)}")

    return correlation, rmse, rel_rmse, intensity_ratio


def debug_sincg_behavior():
    """Debug sincg function behavior for N=1 vs N=5."""
    from src.nanobrag_torch.utils.physics import sincg

    print("\n" + "="*60)
    print("DEBUGGING sincg FUNCTION BEHAVIOR")
    print("="*60)

    # Test cases: near zero, small values, larger values
    test_u_values = [0.0, 0.001, 0.01, 0.1, 0.5, 1.0, np.pi/4, np.pi/2, np.pi, 2*np.pi]
    N_values = [1, 5]

    print("\nTesting sincg(u, N) for various u and N values:")
    print("u\\N\t", end="")
    for N in N_values:
        print(f"N={N}\t\t", end="")
    print()
    print("-" * 50)

    for u in test_u_values:
        print(f"{u:.3f}\t", end="")
        for N in N_values:
            u_tensor = torch.tensor(u)
            N_tensor = torch.tensor(float(N))
            result = sincg(u_tensor, N_tensor)
            print(f"{result.item():.6f}\t", end="")
        print()

    # Test the specific case that occurs at the detector center
    print(f"\nSpecific test for detector center (likely near u=0):")

    # Simulate what happens at detector center for cubic lattice
    for N in [1, 5]:
        # At detector center, scattering vector is mainly along beam direction
        # For cubic cell with a=100Å, this gives small Miller indices
        h_frac = 0.001  # Small fractional part
        u = np.pi * h_frac

        u_tensor = torch.tensor(u)
        N_tensor = torch.tensor(float(N))
        result = sincg(u_tensor, N_tensor)

        print(f"  N={N}, h_frac={h_frac}, u={u:.6f}, sincg={result.item():.6f}")
        print(f"  Expected limit for u→0: N={N}")
        print(f"  Error from limit: {abs(result.item() - N):.6f}")


def main():
    """Main debugging function."""
    print("DEBUG: N=1 vs N=5 Edge Case Analysis")
    print("="*60)

    # First, debug the sincg function behavior
    debug_sincg_behavior()

    # Test N=1 vs N=5 comparisons
    N_values = [1, 2, 3, 5]

    print(f"\n" + "="*60)
    print("RUNNING SIMULATIONS")
    print("="*60)

    results = []

    for N in N_values:
        print(f"\n{'='*30} N = {N} {'='*30}")

        # Run PyTorch simulation with debug output
        py_image = run_pytorch_simulation(N, debug_output=True)

        # Run C simulation with debug output
        c_image = run_c_simulation(N, debug_output=True)

        # Analyze correlation
        correlation, rmse, rel_rmse, intensity_ratio = analyze_correlation(py_image, c_image, N)

        results.append({
            'N': N,
            'correlation': correlation,
            'rmse': rmse,
            'rel_rmse': rel_rmse,
            'intensity_ratio': intensity_ratio
        })

    # Summary
    print(f"\n" + "="*60)
    print("SUMMARY")
    print("="*60)

    print("N\tCorrelation\tRMSE\t\tRel_RMSE\tIntensity_Ratio")
    print("-" * 60)
    for r in results:
        print(f"{r['N']}\t{r['correlation']:.6f}\t{r['rmse']:.2e}\t{r['rel_rmse']:.3f}\t\t{r['intensity_ratio']:.6f}")

    # Identify the issue
    print(f"\n" + "="*60)
    print("ANALYSIS")
    print("="*60)

    n1_corr = next(r['correlation'] for r in results if r['N'] == 1)
    n5_corr = next(r['correlation'] for r in results if r['N'] == 5)

    print(f"N=1 correlation: {n1_corr:.6f}")
    print(f"N=5 correlation: {n5_corr:.6f}")
    print(f"Ratio: {n5_corr / n1_corr:.1f}x better")

    if n1_corr < 0.1:
        print("\n🔴 CRITICAL ISSUE CONFIRMED: N=1 correlation is very low!")
        print("This suggests a fundamental problem with single unit cell physics.")
        print("\nLikely causes:")
        print("1. Shape factor calculation error for N=1")
        print("2. Normalization issue specific to single unit cells")
        print("3. Different handling of very broad diffraction patterns")
        print("4. Edge case in sincg function for N=1")
    else:
        print("\n🟢 N=1 correlation seems reasonable.")

    # Test different crystal shapes to isolate the issue
    print(f"\n" + "="*60)
    print("TESTING DIFFERENT CRYSTAL SHAPES FOR N=1")
    print("="*60)

    shapes = [CrystalShape.SQUARE, CrystalShape.ROUND]  # Test main shapes

    for shape in shapes:
        print(f"\nTesting N=1 with {shape}:")
        py_image = run_pytorch_simulation(1, shape=shape, debug_output=False)
        c_image = run_c_simulation(1, debug_output=False)
        correlation, _, _, _ = analyze_correlation(py_image, c_image, 1)
        print(f"  Correlation: {correlation:.6f}")


if __name__ == "__main__":
    main()
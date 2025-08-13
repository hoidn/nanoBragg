#!/usr/bin/env python3
"""
Debug script to examine the simple_cubic implementation and compare with golden data.
"""

import os
import sys
from pathlib import Path

import numpy as np
import torch
import matplotlib.pyplot as plt

# Set environment for PyTorch
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def main():
    print("=== Debug simple_cubic Implementation ===")

    # Set seed for reproducibility
    torch.manual_seed(0)

    # Create models
    device = torch.device("cpu")
    dtype = torch.float64

    crystal = Crystal(device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)
    simulator = Simulator(crystal, detector, device=device, dtype=dtype)

    print(f"Crystal parameters:")
    print(f"  a_star: {crystal.a_star}")
    print(f"  b_star: {crystal.b_star}")
    print(f"  c_star: {crystal.c_star}")
    print(f"  N_cells: {crystal.N_cells_a}, {crystal.N_cells_b}, {crystal.N_cells_c}")

    print(f"Detector parameters:")
    print(f"  distance: {detector.distance} mm")
    print(f"  pixel_size: {detector.pixel_size} mm")
    print(f"  spixels x fpixels: {detector.spixels} x {detector.fpixels}")
    print(f"  beam_center: ({detector.beam_center_s}, {detector.beam_center_f})")

    print(f"Simulator parameters:")
    print(f"  wavelength: {simulator.wavelength} Angstrom")
    print(f"  incident_beam_direction: {simulator.incident_beam_direction}")

    # Get pixel coordinates for center and a few other key pixels
    pixel_coords_mm = detector.get_pixel_coords()
    pixel_coords = pixel_coords_mm * 1e7  # Convert mm to Angstrom (1 mm = 10^7 Å)
    print(f"Pixel coords shape: {pixel_coords.shape}")

    # Check center pixel
    center_s, center_f = 250, 250
    center_coord = pixel_coords[center_s, center_f]
    print(f"Center pixel ({center_s}, {center_f}) coord: {center_coord}")

    # Check pixel at edge
    edge_s, edge_f = 249, 249
    edge_coord = pixel_coords[edge_s, edge_f]
    print(f"Edge pixel ({edge_s}, {edge_f}) coord: {edge_coord}")

    # Run simulation
    print("\n--- Running Simulation ---")
    pytorch_image = simulator.run()
    print(f"PyTorch image shape: {pytorch_image.shape}")
    print(f"PyTorch sum: {torch.sum(pytorch_image):.2e}")
    print(f"PyTorch max: {torch.max(pytorch_image):.2e}")
    print(f"PyTorch mean: {torch.mean(pytorch_image):.2e}")

    # Find max intensity pixel
    max_idx = torch.argmax(pytorch_image.flatten())
    max_s = max_idx // pytorch_image.shape[1]
    max_f = max_idx % pytorch_image.shape[1]
    print(
        f"Max intensity at pixel ({max_s}, {max_f}): {pytorch_image[max_s, max_f]:.2e}"
    )

    # Load golden data
    print("\n--- Loading Golden Data ---")
    golden_data_path = Path("tests/golden_data/simple_cubic.bin")
    golden_data = np.fromfile(str(golden_data_path), dtype=np.float32).reshape(500, 500)
    golden_tensor = torch.from_numpy(golden_data).to(dtype=torch.float64)

    print(f"Golden sum: {torch.sum(golden_tensor):.2e}")
    print(f"Golden max: {torch.max(golden_tensor):.2e}")
    print(f"Golden mean: {torch.mean(golden_tensor):.2e}")

    # Find max intensity pixel in golden
    golden_max_idx = torch.argmax(golden_tensor.flatten())
    golden_max_s = golden_max_idx // golden_tensor.shape[1]
    golden_max_f = golden_max_idx % golden_tensor.shape[1]
    print(
        f"Golden max at pixel ({golden_max_s}, {golden_max_f}): {golden_tensor[golden_max_s, golden_max_f]:.2e}"
    )

    # Compare center pixels
    print(f"\nCenter pixel comparison:")
    print(f"  PyTorch: {pytorch_image[center_s, center_f]:.2e}")
    print(f"  Golden:  {golden_tensor[center_s, center_f]:.2e}")

    # Compare golden max location with our values
    print(f"\nGolden max location comparison:")
    print(f"  PyTorch at golden max: {pytorch_image[golden_max_s, golden_max_f]:.2e}")
    print(f"  Golden at golden max:  {golden_tensor[golden_max_s, golden_max_f]:.2e}")

    # Check a few more spots to see the pattern
    print(f"\nPattern comparison (PyTorch / Golden):")
    for s, f in [(200, 200), (300, 300), (400, 400), (250, 300), (300, 250)]:
        pt_val = pytorch_image[s, f]
        gold_val = golden_tensor[s, f]
        print(f"  ({s}, {f}): {pt_val:.2e} / {gold_val:.2e}")

    # Calculate some specific intermediate values for center pixel
    print(f"\n--- Debug Center Pixel Calculation ---")

    # Manually calculate for center pixel
    center_coord = pixel_coords[center_s, center_f]

    # Also check golden max pixel
    print(f"\n--- Debug Golden Max Pixel Calculation ---")
    golden_coord = pixel_coords[golden_max_s, golden_max_f]

    # Golden max pixel calculation
    golden_magnitude = torch.sqrt(torch.sum(golden_coord * golden_coord))
    golden_diffracted_unit = golden_coord / golden_magnitude
    two_pi = 2.0 * torch.pi
    golden_scattering = (two_pi / simulator.wavelength) * (
        golden_diffracted_unit - simulator.incident_beam_direction
    )
    golden_h = torch.dot(golden_scattering, crystal.a_star)
    golden_k = torch.dot(golden_scattering, crystal.b_star)
    golden_l = torch.dot(golden_scattering, crystal.c_star)
    print(f"Golden max pixel coord: {golden_coord}")
    print(f"Golden max h, k, l: {golden_h:.6f}, {golden_k:.6f}, {golden_l:.6f}")

    # Diffracted beam unit vector
    pixel_magnitude = torch.sqrt(torch.sum(center_coord * center_coord))
    diffracted_unit = center_coord / pixel_magnitude
    print(f"Center pixel magnitude: {pixel_magnitude:.6f}")
    print(f"Diffracted unit: {diffracted_unit}")

    # Incident beam unit vector
    incident_unit = simulator.incident_beam_direction
    print(f"Incident unit: {incident_unit}")

    # Scattering vector with 2π factor
    two_pi = 2.0 * torch.pi
    scattering = (two_pi / simulator.wavelength) * (diffracted_unit - incident_unit)
    print(f"Scattering vector: {scattering}")

    # h, k, l
    h = torch.dot(scattering, crystal.a_star)
    k = torch.dot(scattering, crystal.b_star)
    l = torch.dot(scattering, crystal.c_star)
    print(f"h, k, l: {h:.6f}, {k:.6f}, {l:.6f}")

    # F_cell using integer indices
    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)
    F_cell = crystal.get_structure_factor(
        h0.unsqueeze(0), k0.unsqueeze(0), l0.unsqueeze(0)
    )[0]
    print(f"F_cell: {F_cell:.6f}")

    # F_latt components using fractional differences
    from nanobrag_torch.utils.physics import sincg

    pi = torch.pi
    F_latt_a = sincg(pi * (h - h0), torch.tensor(crystal.N_cells_a, dtype=dtype))
    F_latt_b = sincg(pi * (k - k0), torch.tensor(crystal.N_cells_b, dtype=dtype))
    F_latt_c = sincg(pi * (l - l0), torch.tensor(crystal.N_cells_c, dtype=dtype))
    F_latt = F_latt_a * F_latt_b * F_latt_c
    print(f"F_latt components: {F_latt_a:.6f}, {F_latt_b:.6f}, {F_latt_c:.6f}")
    print(f"F_latt total: {F_latt:.6f}")

    # Total intensity
    F_total = F_cell * F_latt
    intensity_base = F_total * F_total

    # Apply scaling factor
    scale_factor = 5.4581e11
    intensity = intensity_base * scale_factor
    print(f"F_total: {F_total:.6f}")
    print(f"Intensity (before scaling): {intensity_base:.2e}")
    print(f"Intensity (after scaling): {intensity:.2e}")

    # Compare with what we got from simulation
    sim_intensity = pytorch_image[center_s, center_f]
    print(f"Simulation intensity: {sim_intensity:.2e}")
    print(f"Match: {torch.allclose(intensity, sim_intensity)}")

    # Create comparison plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # PyTorch image
    im1 = axes[0].imshow(pytorch_image.numpy(), cmap="inferno", origin="lower")
    axes[0].set_title("PyTorch")
    plt.colorbar(im1, ax=axes[0])

    # Golden image
    im2 = axes[1].imshow(golden_data, cmap="inferno", origin="lower")
    axes[1].set_title("Golden")
    plt.colorbar(im2, ax=axes[1])

    # Difference
    diff = np.log1p(np.abs(pytorch_image.numpy() - golden_data))
    im3 = axes[2].imshow(diff, cmap="plasma", origin="lower")
    axes[2].set_title("log(1 + |diff|)")
    plt.colorbar(im3, ax=axes[2])

    plt.tight_layout()
    plt.savefig("debug_comparison.png", dpi=150)
    print(f"\nSaved debug_comparison.png")


if __name__ == "__main__":
    main()

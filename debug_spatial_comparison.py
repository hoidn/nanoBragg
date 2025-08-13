#!/usr/bin/env python3
"""
Debug spatial comparison between C and PyTorch implementations.
"""
import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from c_reference_runner import CReferenceRunner


def main():
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    print("=== SPATIAL SCALE DEBUG COMPARISON ===")

    # Create simple configurations
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=51.2,
        beam_center_f=51.2,
    )

    crystal_config = CrystalConfig(N_cells=[5, 5, 5])
    beam_config = BeamConfig(wavelength_A=6.2)

    # Run PyTorch simulation
    print("\n1. Running PyTorch simulation...")
    detector = Detector(detector_config, device="cpu", dtype=torch.float64)
    crystal = Crystal(crystal_config, device="cpu", dtype=torch.float64)
    simulator = Simulator(crystal, detector, device="cpu", dtype=torch.float64)
    pytorch_image = simulator.run(beam_config)
    pytorch_image_np = pytorch_image.detach().numpy()

    # Run C simulation
    print("\n2. Running C simulation...")
    c_runner = CReferenceRunner()
    c_image_np = c_runner.run_simulation(
        detector_config, crystal_config, beam_config, "debug"
    )

    if c_image_np is None:
        print("❌ C simulation failed")
        return

    # Find brightest spots in both images
    print("\n3. Finding brightest spots...")

    def find_brightest_spots(image, n=5):
        flat_indices = np.argsort(image.flatten())[-n:][::-1]  # Top N, descending
        coords = np.unravel_index(flat_indices, image.shape)
        spots = []
        for i in range(n):
            s, f = coords[0][i], coords[1][i]
            intensity = image[s, f]
            spots.append((s, f, intensity))
        return spots

    pytorch_spots = find_brightest_spots(pytorch_image_np, 10)
    c_spots = find_brightest_spots(c_image_np, 10)

    print("\nPyTorch brightest spots:")
    for i, (s, f, intensity) in enumerate(pytorch_spots):
        print(f"  Spot {i+1}: ({s:3d}, {f:3d}) - Intensity: {intensity:.2e}")

    print("\nC brightest spots:")
    for i, (s, f, intensity) in enumerate(c_spots):
        print(f"  Spot {i+1}: ({s:3d}, {f:3d}) - Intensity: {intensity:.2e}")

    # Calculate spatial offsets
    print("\n4. Spatial offset analysis:")
    if len(pytorch_spots) > 0 and len(c_spots) > 0:
        py_s, py_f = pytorch_spots[0][0], pytorch_spots[0][1]
        c_s, c_f = c_spots[0][0], c_spots[0][1]

        offset_s = c_s - py_s
        offset_f = c_f - py_f
        offset_mag = np.sqrt(offset_s**2 + offset_f**2)

        print(
            f"  Brightest spot offset: Δs={offset_s:+d}, Δf={offset_f:+d}, |Δ|={offset_mag:.1f} pixels"
        )

        if offset_mag > 10:
            print(f"  ⚠️  Large spatial offset detected! ({offset_mag:.1f} pixels)")
        else:
            print(
                f"  ✅ Small spatial offset ({offset_mag:.1f} pixels) - likely acceptable"
            )

    # Image statistics
    print("\n5. Image statistics:")
    print(
        f"  PyTorch: min={pytorch_image_np.min():.2e}, max={pytorch_image_np.max():.2e}, mean={pytorch_image_np.mean():.2e}"
    )
    print(
        f"  C:       min={c_image_np.min():.2e}, max={c_image_np.max():.2e}, mean={c_image_np.mean():.2e}"
    )

    # Create side-by-side comparison plot
    print("\n6. Creating comparison plot...")
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # PyTorch image
    im1 = axes[0].imshow(
        pytorch_image_np,
        origin="lower",
        cmap="viridis",
        vmin=0,
        vmax=np.percentile(pytorch_image_np, 99.9),
    )
    axes[0].set_title("PyTorch Implementation")
    axes[0].set_xlabel("Fast axis (pixels)")
    axes[0].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im1, ax=axes[0])

    # Mark brightest spots
    for i, (s, f, _) in enumerate(pytorch_spots[:3]):
        axes[0].plot(f, s, "r+", markersize=10, markeredgewidth=2)
        axes[0].text(f + 10, s + 10, f"{i+1}", color="red", fontweight="bold")

    # C image
    im2 = axes[1].imshow(
        c_image_np,
        origin="lower",
        cmap="viridis",
        vmin=0,
        vmax=np.percentile(c_image_np, 99.9),
    )
    axes[1].set_title("C Reference Implementation")
    axes[1].set_xlabel("Fast axis (pixels)")
    axes[1].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im2, ax=axes[1])

    # Mark brightest spots
    for i, (s, f, _) in enumerate(c_spots[:3]):
        axes[1].plot(f, s, "r+", markersize=10, markeredgewidth=2)
        axes[1].text(f + 10, s + 10, f"{i+1}", color="red", fontweight="bold")

    # Difference image
    diff_image = pytorch_image_np - c_image_np
    im3 = axes[2].imshow(
        diff_image,
        origin="lower",
        cmap="RdBu_r",
        vmin=-np.percentile(np.abs(diff_image), 95),
        vmax=np.percentile(np.abs(diff_image), 95),
    )
    axes[2].set_title("Difference (PyTorch - C)")
    axes[2].set_xlabel("Fast axis (pixels)")
    axes[2].set_ylabel("Slow axis (pixels)")
    plt.colorbar(im3, ax=axes[2])

    plt.tight_layout()
    plt.savefig("debug_spatial_comparison.png", dpi=150, bbox_inches="tight")
    print("  Saved: debug_spatial_comparison.png")

    print("\n=== DEBUG COMPARISON COMPLETE ===")


if __name__ == "__main__":
    import torch

    main()

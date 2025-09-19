#!/usr/bin/env python
"""Debug script to trace a single reflection through the calculation chain."""

import os
import torch
import numpy as np

# Set up environment
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import PyTorch implementation
from nanobrag_torch.config import (
    CrystalConfig, BeamConfig, DetectorConfig,
    DetectorConvention, DetectorPivot
)
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.simulator import Simulator


def trace_reflection():
    """Trace the (1,0,0) reflection to understand where it should appear."""

    # Create configuration matching the test
    crystal_config = CrystalConfig(
        cell_a=70.0,
        cell_b=80.0,
        cell_c=90.0,
        cell_alpha=85.0,
        cell_beta=95.0,
        cell_gamma=105.0,
        N_cells=(1, 1, 1),
        default_F=100.0
    )

    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
        distance_mm=150.0,
        pixel_size_mm=0.1,
        spixels=256,
        fpixels=256
    )

    beam_config = BeamConfig(
        wavelength_A=1.5
    )

    # Create objects
    crystal = Crystal(crystal_config, beam_config)
    detector = Detector(detector_config)

    print("=" * 60)
    print("CRYSTAL GEOMETRY")
    print("=" * 60)
    print(f"a: {crystal.a.numpy()}")
    print(f"b: {crystal.b.numpy()}")
    print(f"c: {crystal.c.numpy()}")
    print(f"a*: {crystal.a_star.numpy()}")
    print(f"b*: {crystal.b_star.numpy()}")
    print(f"c*: {crystal.c_star.numpy()}")

    # Calculate where (1,0,0) reflection should appear
    h, k, l = 1, 0, 0

    # Reciprocal lattice vector for (1,0,0)
    G = h * crystal.a_star + k * crystal.b_star + l * crystal.c_star
    print(f"\nReciprocal lattice vector G(1,0,0): {G.numpy()}")
    print(f"|G| = {torch.norm(G).item():.6f} Å^-1")

    # For Bragg condition with elastic scattering
    # The scattering vector q must equal G
    # q = (k_out - k_in) / λ
    # With |k_in| = |k_out| = 2π/λ

    wavelength = beam_config.wavelength_A  # Angstroms
    k_mag = 2 * np.pi / wavelength

    # Incident beam direction (MOSFLM: along +X)
    k_in = torch.tensor([k_mag, 0.0, 0.0], dtype=torch.float64)
    print(f"\nIncident wave vector k_in: {k_in.numpy()}")
    print(f"|k_in| = {torch.norm(k_in).item():.6f}")

    # For Bragg condition: k_out - k_in = λ*G (since q = G in our units)
    # Therefore: k_out = k_in + λ*G
    k_out = k_in + wavelength * G
    print(f"\nScattered wave vector k_out: {k_out.numpy()}")
    print(f"|k_out| = {torch.norm(k_out).item():.6f}")

    # Check if this is kinematically allowed
    if abs(torch.norm(k_out) - k_mag) > 0.1 * k_mag:
        print("WARNING: Reflection not kinematically accessible!")
        return

    # Normalize to get scattered beam direction
    scatter_dir = k_out / torch.norm(k_out)
    print(f"\nScattered beam direction: {scatter_dir.numpy()}")

    print("\n" + "=" * 60)
    print("DETECTOR GEOMETRY")
    print("=" * 60)
    print(f"Distance: {detector.distance:.3f} m")
    print(f"Pixel size: {detector.pixel_size:.6f} m")
    print(f"Beam center: ({detector.beam_center_s:.3f}, {detector.beam_center_f:.3f}) mm")
    print(f"pix0_vector: {detector.pix0_vector.numpy()} m")
    print(f"fdet_vec: {detector.fdet_vec.numpy()}")
    print(f"sdet_vec: {detector.sdet_vec.numpy()}")
    print(f"odet_vec: {detector.odet_vec.numpy()}")

    # Find intersection with detector plane
    # For MOSFLM with flat detector, the detector is roughly perpendicular to X
    # The detector plane equation: (r - pix0) · odet = distance (approximately)

    # Simple ray-plane intersection
    # Ray: r = t * scatter_dir (from origin)
    # Plane: normal = odet_vec, point on plane = pix0 + distance*odet_vec

    # For MOSFLM detector at distance d along X:
    # Intersection occurs when X component = distance
    t_intersect = detector.distance / scatter_dir[0] if scatter_dir[0] > 0 else float('inf')

    if t_intersect == float('inf'):
        print("Ray doesn't hit detector!")
        return

    # Point of intersection in lab frame (meters)
    intersection_point = t_intersect * scatter_dir * 1e-10  # Convert Å to meters
    print(f"\nIntersection point (lab frame): {intersection_point.numpy()} m")

    # Vector from pix0 to intersection
    r_det = intersection_point - detector.pix0_vector
    print(f"Vector from pix0: {r_det.numpy()} m")

    # Project onto detector basis to get pixel coordinates
    slow_coord_m = torch.dot(r_det, detector.sdet_vec)
    fast_coord_m = torch.dot(r_det, detector.fdet_vec)

    print(f"\nDetector coordinates: ({slow_coord_m:.6f}, {fast_coord_m:.6f}) m")

    # Convert to pixels (using center-based indexing)
    slow_pixel = slow_coord_m / detector.pixel_size
    fast_pixel = fast_coord_m / detector.pixel_size

    print(f"Pixel coordinates: ({slow_pixel:.2f}, {fast_pixel:.2f})")

    # Now run the full simulation and see where the peak actually appears
    print("\n" + "=" * 60)
    print("SIMULATION RESULT")
    print("=" * 60)

    simulator = Simulator(crystal, detector, crystal_config, beam_config)
    image = simulator.run()

    # Find the maximum in the image
    max_val = torch.max(image)
    max_idx = torch.argmax(image.view(-1))
    max_slow = max_idx // image.shape[1]
    max_fast = max_idx % image.shape[1]

    print(f"Maximum intensity: {max_val:.4f}")
    print(f"Maximum at pixel: ({max_slow}, {max_fast})")

    # Find intensity around the predicted position
    pred_slow = int(slow_pixel)
    pred_fast = int(fast_pixel)

    if 0 <= pred_slow < 256 and 0 <= pred_fast < 256:
        window_size = 5
        slow_min = max(0, pred_slow - window_size)
        slow_max = min(256, pred_slow + window_size)
        fast_min = max(0, pred_fast - window_size)
        fast_max = min(256, pred_fast + window_size)

        window = image[slow_min:slow_max, fast_min:fast_max]

        print(f"\nIntensity around predicted position ({pred_slow}, {pred_fast}):")
        print(f"Max in window: {torch.max(window):.4f}")

        # Find peak in window
        if torch.max(window) > 0.01:
            window_max_idx = torch.argmax(window.view(-1))
            window_slow = window_max_idx // window.shape[1]
            window_fast = window_max_idx % window.shape[1]
            actual_slow = slow_min + window_slow
            actual_fast = fast_min + window_fast

            print(f"Peak in window at: ({actual_slow}, {actual_fast})")
            distance = np.sqrt((actual_slow - pred_slow)**2 + (actual_fast - pred_fast)**2)
            print(f"Distance from predicted: {distance:.2f} pixels")
        else:
            print("No significant intensity near predicted position!")

            # Search for any peaks
            threshold = 0.1 * max_val
            peak_mask = image > threshold
            if torch.any(peak_mask):
                peak_indices = torch.nonzero(peak_mask)
                print(f"\nFound {len(peak_indices)} pixels above {threshold:.4f}")
                print("First few peak positions:")
                for i in range(min(5, len(peak_indices))):
                    s, f = peak_indices[i]
                    print(f"  ({s}, {f}): intensity = {image[s, f]:.4f}")


if __name__ == "__main__":
    trace_reflection()
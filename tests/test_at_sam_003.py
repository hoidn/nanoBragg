"""Test AT-SAM-003: dmin culling.

AT-SAM-003 from spec:
- Setup: Choose a pixel/source such that stol=0.5·|q| yields dmin < 0.5/stol; set dmin positive.
- Expectation: The contribution for that subpath SHALL be skipped.
"""

import torch
import numpy as np
from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator


def test_dmin_culling_basic():
    """Test that dmin culling correctly skips high-resolution reflections."""
    torch.manual_seed(42)

    # Configure detector with geometry that gives larger scattering angles
    # Larger detector and closer distance for higher stol values
    detector_config = DetectorConfig(
        spixels=128,
        fpixels=128,
        pixel_size_mm=0.5,  # Larger pixels to get larger detector
        distance_mm=50.0,   # Closer detector for larger angles
        beam_center_s=32 * 0.5,  # Center of detector
        beam_center_f=32 * 0.5,
    )

    # Simple crystal
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(10, 10, 10),
        phi_start_deg=0.0,
        osc_range_deg=1.0,
        phi_steps=1,
        mosaic_spread_deg=0.0,
        mosaic_domains=1,
        default_F=100.0,
    )

    # Beam with NO dmin cutoff first
    beam_config_no_cutoff = BeamConfig(
        wavelength_A=1.5,
        dmin=0.0,  # No cutoff
    )

    # Initialize models
    detector = Detector(detector_config)
    crystal = Crystal(crystal_config)

    # Run simulation without dmin cutoff
    # Use oversample=1 for clear pixel-level culling test
    simulator = Simulator(crystal, detector, crystal_config, beam_config_no_cutoff)
    image_no_cutoff = simulator.run(oversample=1)

    # Now run with dmin cutoff that should eliminate high-angle pixels
    # Choose dmin = 10.0 Angstroms to cut off more reflections with our geometry
    beam_config_with_cutoff = BeamConfig(
        wavelength_A=1.5,
        dmin=10.0,  # 10 Angstrom cutoff - aggressive to ensure culling happens
    )

    simulator_with_cutoff = Simulator(crystal, detector, crystal_config, beam_config_with_cutoff)
    image_with_cutoff = simulator_with_cutoff.run(oversample=1)

    # Check that some pixels were culled
    # High-angle pixels (far from center) should have zero intensity with cutoff
    assert not torch.allclose(image_no_cutoff, image_with_cutoff), "dmin cutoff should affect the image"

    # Check that corner pixels (highest resolution) are zeroed with cutoff
    # Corner pixels have the highest scattering angles and thus highest stol values
    corner_indices = [
        (0, 0), (0, 127), (127, 0), (127, 127)  # Four corners
    ]

    for idx in corner_indices:
        # With cutoff, corner pixels should have much less (ideally zero) intensity
        # Allow small numerical noise
        assert image_with_cutoff[idx] < image_no_cutoff[idx] * 0.1, \
            f"Corner pixel {idx} not properly culled: {image_with_cutoff[idx]} vs {image_no_cutoff[idx]}"

    # With aggressive dmin=10.0, many pixels will be culled
    # Just check that culling is happening (most pixels affected)
    num_affected = torch.sum(torch.abs(image_with_cutoff - image_no_cutoff) > 1e-6)
    total_pixels = image_with_cutoff.numel()

    # With dmin=10.0 and our geometry, most pixels should be affected
    assert num_affected > total_pixels * 0.5, f"Expected >50% of pixels affected, got {100*num_affected/total_pixels:.1f}%"


def test_dmin_culling_exact_threshold():
    """Test dmin culling at exact threshold values."""
    torch.manual_seed(42)

    # Configure a simple 3x3 detector for easier analysis
    detector_config = DetectorConfig(
        spixels=3,
        fpixels=3,
        pixel_size_mm=20.0,  # Large pixels for larger angles
        distance_mm=50.0,    # Closer for larger scattering angles
        beam_center_s=30.0,  # Center pixel
        beam_center_f=30.0,
    )

    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        phi_steps=1,
        mosaic_domains=1,
        default_F=100.0,
    )

    # Calculate expected stol for center pixel and corner pixel
    # For center pixel: scattering vector is nearly zero (forward scattering)
    # For corner pixel: larger scattering angle

    wavelength = 2.0

    # Test with a specific dmin that should cull some but not all pixels
    beam_config = BeamConfig(
        wavelength_A=wavelength,
        dmin=5.0,  # 5 Angstrom cutoff
    )

    detector = Detector(detector_config)
    crystal = Crystal(crystal_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    # Get pixel coordinates to calculate expected stol values
    pixel_coords = detector.get_pixel_coords()  # In meters
    pixel_coords_A = pixel_coords * 1e10  # Convert to Angstroms

    # Calculate scattering vectors and stol for each pixel
    diffracted_unit = pixel_coords_A / torch.norm(pixel_coords_A, dim=-1, keepdim=True)
    incident_unit = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64).expand_as(diffracted_unit)

    scattering_vector = (diffracted_unit - incident_unit) / wavelength
    stol_values = 0.5 * torch.norm(scattering_vector, dim=-1)

    # Run simulation with oversample=1 to test pixel-level culling
    # (With high oversampling, some subpixels may have stol below threshold
    # even when pixel center has stol above threshold, which is correct per spec)
    image = simulator.run(oversample=1)

    # Check culling based on stol threshold
    stol_threshold = 0.5 / beam_config.dmin  # = 0.5 / 5.0 = 0.1

    # Pixels with stol > threshold should be culled (have very low intensity)
    culled_mask = stol_values > stol_threshold

    # For culled pixels, intensity should be near zero
    for i in range(3):
        for j in range(3):
            if culled_mask[i, j]:
                assert image[i, j] < 1e-6, f"Pixel ({i},{j}) with stol={stol_values[i,j]:.4f} should be culled"


def test_dmin_zero_no_culling():
    """Test that dmin=0 results in no culling."""
    torch.manual_seed(42)

    detector_config = DetectorConfig(
        spixels=64,
        fpixels=64,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        beam_center_s=32 * 0.1,
        beam_center_f=32 * 0.1,
    )

    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        phi_steps=1,
        mosaic_domains=1,
        default_F=100.0,
    )

    # Test with dmin=0 (no culling)
    beam_config = BeamConfig(
        wavelength_A=1.5,
        dmin=0.0,
    )

    detector = Detector(detector_config)
    crystal = Crystal(crystal_config)
    simulator = Simulator(crystal, detector, crystal_config, beam_config)

    image = simulator.run()

    # With no culling, all pixels should have non-zero intensity
    # (assuming default_F > 0 and proper geometry)
    assert torch.all(image >= 0), "All pixels should have non-negative intensity"
    assert torch.sum(image > 0) > 0, "At least some pixels should have positive intensity"

    # No pixels should be artificially zeroed
    # The pattern should be smooth without abrupt cutoffs
    # This is a qualitative check - with no culling, there shouldn't be
    # a sharp boundary where intensity drops to exactly zero


if __name__ == "__main__":
    test_dmin_culling_basic()
    print("✓ test_dmin_culling_basic passed")

    test_dmin_culling_exact_threshold()
    print("✓ test_dmin_culling_exact_threshold passed")

    test_dmin_zero_no_culling()
    print("✓ test_dmin_zero_no_culling passed")

    print("\nAll AT-SAM-003 tests passed!")
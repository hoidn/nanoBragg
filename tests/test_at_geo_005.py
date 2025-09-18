"""
Acceptance Test AT-GEO-005: Curved detector mapping

Per spec:
- AT-GEO-005 Curved detector mapping
  - Setup: Enable -curved_det; choose several off-center pixels.
  - Expectation: The curved mapping SHALL yield |pos| equal for all pixels at a
    given Fdet,Sdet angular offset (spherical arc mapping), and differ from planar
    mapping in a way consistent with the spec's small-angle rotations about s and f
    by Sdet/distance and Fdet/distance respectively.
"""

import torch
import pytest
import numpy as np
from src.nanobrag_torch.config import DetectorConfig
from src.nanobrag_torch.models.detector import Detector


class TestATGEO005CurvedDetector:
    """Tests for AT-GEO-005: Curved detector mapping."""

    def test_curved_detector_equal_distance(self):
        """Test that curved mapping yields equal |pos| for pixels at same angular offset."""
        # Setup: Create detector with curved_detector enabled
        config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=100,
            fpixels=100,
            beam_center_s=50.0,  # Center of detector
            beam_center_f=50.0,
            curved_detector=True  # Enable curved detector
        )
        detector = Detector(config)

        # Get pixel coordinates
        pixel_coords = detector.get_pixel_coords()

        # Choose several pixels at the same angular offset from center
        # These should all be at the same distance from the sample
        center_s = 50
        center_f = 50
        radius_pixels = 20  # Check pixels 20 pixels away from center

        # Collect distances for pixels at this radius
        distances = []
        angles_to_check = [0, np.pi/4, np.pi/2, 3*np.pi/4, np.pi,
                          5*np.pi/4, 3*np.pi/2, 7*np.pi/4]

        for angle in angles_to_check:
            s_idx = int(center_s + radius_pixels * np.sin(angle))
            f_idx = int(center_f + radius_pixels * np.cos(angle))

            # Ensure indices are within bounds
            if 0 <= s_idx < config.spixels and 0 <= f_idx < config.fpixels:
                pos = pixel_coords[s_idx, f_idx]
                distance = torch.norm(pos)
                distances.append(distance.item())

        # All distances should be equal (within numerical tolerance)
        # For spherical mapping, all pixels should be equidistant from the sample
        distances = np.array(distances)
        assert np.allclose(distances, distances[0], rtol=1e-6), \
            f"Curved detector pixels at same angular offset should be equidistant. Got: {distances}"

        # Additionally, verify that all pixels are at the nominal distance
        # (within small tolerance due to small angle approximation)
        expected_distance = config.distance_mm / 1000.0  # Convert to meters
        assert np.allclose(distances, expected_distance, rtol=1e-3), \
            f"All pixels should be approximately at distance {expected_distance}m. Got: {distances}"

    def test_curved_vs_planar_difference(self):
        """Test that curved mapping differs from planar mapping as expected."""
        # Setup: Create two detectors, one planar and one curved
        config_planar = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=100,
            fpixels=100,
            beam_center_s=50.0,
            beam_center_f=50.0,
            curved_detector=False  # Planar detector
        )

        config_curved = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=100,
            fpixels=100,
            beam_center_s=50.0,
            beam_center_f=50.0,
            curved_detector=True  # Curved detector
        )

        detector_planar = Detector(config_planar)
        detector_curved = Detector(config_curved)

        # Get pixel coordinates for both
        coords_planar = detector_planar.get_pixel_coords()
        coords_curved = detector_curved.get_pixel_coords()

        # For curved detector, all pixels should be at the same distance
        # This is the key difference from planar detector
        center_s = 50
        center_f = 50
        center_curved = coords_curved[center_s, center_f]
        dist_center_curved = torch.norm(center_curved).item()

        # Check that center pixel is approximately at the nominal distance
        expected_distance = config_curved.distance_mm / 1000.0  # meters
        assert np.isclose(dist_center_curved, expected_distance, rtol=1e-3), \
            f"Center pixel should be at distance {expected_distance}m, got {dist_center_curved}m"

        # Check off-center pixels - should differ
        # The further from center, the larger the difference
        corner_s = 10
        corner_f = 10
        corner_planar = coords_planar[corner_s, corner_f]
        corner_curved = coords_curved[corner_s, corner_f]

        difference = torch.norm(corner_planar - corner_curved).item()
        assert difference > 1e-6, \
            "Off-center pixels should differ between planar and curved detectors"

        # For curved detector, distance from sample should be constant
        dist_corner_curved = torch.norm(corner_curved).item()
        dist_center_curved = torch.norm(center_curved).item()
        assert np.allclose(dist_corner_curved, dist_center_curved, rtol=1e-3), \
            f"Curved detector: all pixels should be equidistant. Corner: {dist_corner_curved}, Center: {dist_center_curved}"

        # For planar detector, corner pixels are further from sample
        dist_corner_planar = torch.norm(corner_planar).item()
        dist_center_planar = torch.norm(center_planar).item()
        assert dist_corner_planar > dist_center_planar, \
            "Planar detector: corner pixels should be further from sample than center"

    def test_small_angle_rotation_consistency(self):
        """Test that curved mapping is consistent with small-angle rotations."""
        # Setup: Create curved detector
        config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=100,
            fpixels=100,
            beam_center_s=50.0,
            beam_center_f=50.0,
            curved_detector=True
        )
        detector = Detector(config)

        # Get pixel coordinates
        coords = detector.get_pixel_coords()

        # Test a specific pixel offset from center
        center_s = 50
        center_f = 50
        test_s = 60  # 10 pixels offset in slow direction
        test_f = 70  # 20 pixels offset in fast direction

        # Calculate expected angles
        distance_m = config.distance_mm / 1000.0
        pixel_size_m = config.pixel_size_mm / 1000.0

        Sdet_offset = (test_s - center_s) * pixel_size_m
        Fdet_offset = (test_f - center_f) * pixel_size_m

        expected_s_angle = Sdet_offset / distance_m
        expected_f_angle = Fdet_offset / distance_m

        # Get the actual pixel position
        pixel_pos = coords[test_s, test_f]

        # The pixel should be at approximately the expected angular offset
        # We can verify this by checking the projection onto the slow and fast axes

        # Normalize the position to get direction
        pixel_dir = pixel_pos / torch.norm(pixel_pos)

        # The beam direction (negative of beam_vector since beam_vector points toward source)
        beam_dir = -detector.beam_vector

        # Calculate the angle components
        # For small angles, the projection gives approximately the angle

        # Project the deviation onto the slow and fast axes
        deviation = pixel_dir - beam_dir

        s_component = torch.dot(deviation, detector.sdet_vec).item()
        f_component = torch.dot(deviation, detector.fdet_vec).item()

        # For small angles, these should approximately equal the expected angles
        assert np.allclose(s_component, expected_s_angle, rtol=0.1), \
            f"Slow angle component mismatch. Expected: {expected_s_angle}, Got: {s_component}"

        assert np.allclose(f_component, expected_f_angle, rtol=0.1), \
            f"Fast angle component mismatch. Expected: {expected_f_angle}, Got: {f_component}"

    def test_gradient_flow_curved_detector(self):
        """Test that gradients flow through curved detector mapping."""
        # Setup: Create detector with requires_grad distance
        distance_tensor = torch.tensor(100.0, requires_grad=True)

        config = DetectorConfig(
            distance_mm=distance_tensor,
            pixel_size_mm=0.1,
            spixels=50,  # Smaller for faster test
            fpixels=50,
            beam_center_s=25.0,
            beam_center_f=25.0,
            curved_detector=True
        )
        detector = Detector(config)

        # Get pixel coordinates
        coords = detector.get_pixel_coords()

        # Create a loss that depends on the pixel positions
        # For example, sum of distances from origin
        distances = torch.norm(coords, dim=-1)
        loss = distances.sum()

        # Compute gradient
        loss.backward()

        # Check that distance has a gradient
        assert distance_tensor.grad is not None, \
            "Distance parameter should have gradient"

        # The gradient should be non-zero
        assert torch.abs(distance_tensor.grad) > 1e-10, \
            "Distance gradient should be non-zero"

        # For a curved detector where all pixels are at distance from sample,
        # the gradient should be positive (increasing distance increases sum of distances)
        assert distance_tensor.grad > 0, \
            "Distance gradient should be positive for sum of distances loss"

    def test_beam_center_affects_curvature(self):
        """Test that beam center position affects the curved mapping correctly."""
        # Create two curved detectors with different beam centers
        config1 = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=100,
            fpixels=100,
            beam_center_s=30.0,  # Off-center
            beam_center_f=30.0,
            curved_detector=True
        )

        config2 = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=100,
            fpixels=100,
            beam_center_s=70.0,  # Different off-center position
            beam_center_f=70.0,
            curved_detector=True
        )

        detector1 = Detector(config1)
        detector2 = Detector(config2)

        coords1 = detector1.get_pixel_coords()
        coords2 = detector2.get_pixel_coords()

        # The pixel at (50, 50) should be at different positions for the two detectors
        pixel_pos1 = coords1[50, 50]
        pixel_pos2 = coords2[50, 50]

        # They should both be at the same distance from sample (spherical surface)
        dist1 = torch.norm(pixel_pos1).item()
        dist2 = torch.norm(pixel_pos2).item()

        assert np.allclose(dist1, dist2, rtol=1e-3), \
            f"Both pixels should be at same distance. Got: {dist1}, {dist2}"

        # But their positions should be different
        position_diff = torch.norm(pixel_pos1 - pixel_pos2).item()
        assert position_diff > 1e-6, \
            "Pixels should be at different positions with different beam centers"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
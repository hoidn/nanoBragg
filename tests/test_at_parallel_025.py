"""
AT-PARALLEL-025: Maximum Intensity Position Alignment

Spec reference: specs/spec-a.md:955-957
Goal: Verify that the maximum intensity pixel position matches between C and PyTorch
within 0.5 pixels

This test catches systematic coordinate shifts that cause poor correlation with λ=1.0Å
"""

import os
import pytest
import numpy as np
import torch
import tempfile
from pathlib import Path

# Set environment variable for PyTorch MKL
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Add scripts directory to path for imports
import sys
sys.path.append('scripts')
from c_reference_runner import CReferenceRunner
from src.nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from src.nanobrag_torch.simulator import Simulator
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.models.detector import Detector, DetectorConvention


# Skip these tests unless explicitly requested
pytestmark = pytest.mark.skipif(
    os.environ.get("NB_RUN_PARALLEL") != "1",
    reason="AT-PARALLEL tests require NB_RUN_PARALLEL=1"
)


def find_max_position(image):
    """Find the position of maximum intensity in an image.

    Returns: (slow, fast) position as floats
    """
    if isinstance(image, torch.Tensor):
        image_np = image.cpu().numpy()
    else:
        image_np = image

    # Find the maximum value
    max_val = np.max(image_np)

    # Find all positions with the maximum value
    max_positions = np.argwhere(image_np == max_val)

    # Return the last occurrence (per spec)
    if len(max_positions) > 0:
        return max_positions[-1]  # (slow, fast)
    return None


def test_maximum_intensity_simple_case():
    """Test maximum intensity position for simple cubic case, λ=1.0"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Simple case: cubic crystal, λ=1.0, N=1, 64×64 detector
        # Setup configs for both C and PyTorch
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(1, 1, 1),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64,
            fpixels=64
        )

        beam_config = BeamConfig(
            wavelength_A=1.0
        )

        # Run C simulation
        runner = CReferenceRunner(work_dir=str(tmpdir))
        c_image = runner.run_simulation(
            detector_config,
            crystal_config,
            beam_config,
            label="Simple case"
        )
        c_max_pos = find_max_position(c_image)
        assert c_max_pos is not None, "C image has no maximum"

        crystal = Crystal(crystal_config, beam_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        pytorch_image = simulator.run()

        pytorch_max_pos = find_max_position(pytorch_image)
        assert pytorch_max_pos is not None, "PyTorch image has no maximum"

        # Calculate distance between max positions
        distance = np.sqrt((c_max_pos[0] - pytorch_max_pos[0])**2 +
                          (c_max_pos[1] - pytorch_max_pos[1])**2)

        # Report positions
        print(f"\nC max position: {c_max_pos} (slow, fast)")
        print(f"PyTorch max position: {pytorch_max_pos} (slow, fast)")
        print(f"Distance: {distance:.3f} pixels")
        print(f"C max value: {c_image[c_max_pos[0], c_max_pos[1]]:.3f}")
        print(f"PyTorch max value: {pytorch_image[pytorch_max_pos[0], pytorch_max_pos[1]]:.3f}")

        # Check tolerance (0.5 pixels per spec)
        assert distance <= 0.5, f"Max position distance {distance:.3f} exceeds 0.5 pixel tolerance"


def test_maximum_intensity_with_offset():
    """Test maximum intensity position with beam center offset"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Case with offset beam center
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(1, 1, 1),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=128,
            fpixels=128,
            beam_center_f=8.0,  # MOSFLM: Xbeam -> fast (offset beam center in mm)
            beam_center_s=10.0   # MOSFLM: Ybeam -> slow
        )

        beam_config = BeamConfig(
            wavelength_A=1.0
        )

        # Run C simulation
        runner = CReferenceRunner(work_dir=str(tmpdir))
        c_image = runner.run_simulation(
            detector_config,
            crystal_config,
            beam_config,
            label="With offset"
        )
        c_max_pos = find_max_position(c_image)
        assert c_max_pos is not None, "C image has no maximum"

        crystal = Crystal(crystal_config, beam_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        pytorch_image = simulator.run()

        pytorch_max_pos = find_max_position(pytorch_image)
        assert pytorch_max_pos is not None, "PyTorch image has no maximum"

        # Calculate distance between max positions
        distance = np.sqrt((c_max_pos[0] - pytorch_max_pos[0])**2 +
                          (c_max_pos[1] - pytorch_max_pos[1])**2)

        # Report positions
        print(f"\nC max position: {c_max_pos} (slow, fast)")
        print(f"PyTorch max position: {pytorch_max_pos} (slow, fast)")
        print(f"Distance: {distance:.3f} pixels")
        print(f"C max value: {c_image[c_max_pos[0], c_max_pos[1]]:.3f}")
        print(f"PyTorch max value: {pytorch_image[pytorch_max_pos[0], pytorch_max_pos[1]]:.3f}")

        # Check tolerance (0.5 pixels per spec)
        assert distance <= 0.5, f"Max position distance {distance:.3f} exceeds 0.5 pixel tolerance"


def test_maximum_intensity_triclinic():
    """Test maximum intensity position for triclinic case"""

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Triclinic case
        crystal_config = CrystalConfig(
            cell_a=70.0,
            cell_b=80.0,
            cell_c=90.0,
            cell_alpha=85.0,
            cell_beta=95.0,
            cell_gamma=105.0,
            N_cells=(2, 2, 2),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            detector_convention=DetectorConvention.MOSFLM,
            distance_mm=150.0,
            pixel_size_mm=0.1,
            spixels=96,
            fpixels=96
        )

        beam_config = BeamConfig(
            wavelength_A=1.0
        )

        # Run C simulation
        runner = CReferenceRunner(work_dir=str(tmpdir))
        c_image = runner.run_simulation(
            detector_config,
            crystal_config,
            beam_config,
            label="Triclinic"
        )
        c_max_pos = find_max_position(c_image)
        assert c_max_pos is not None, "C image has no maximum"

        crystal = Crystal(crystal_config, beam_config)
        detector = Detector(detector_config)
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        pytorch_image = simulator.run()

        pytorch_max_pos = find_max_position(pytorch_image)
        assert pytorch_max_pos is not None, "PyTorch image has no maximum"

        # Calculate distance between max positions
        distance = np.sqrt((c_max_pos[0] - pytorch_max_pos[0])**2 +
                          (c_max_pos[1] - pytorch_max_pos[1])**2)

        # Report positions
        print(f"\nC max position: {c_max_pos} (slow, fast)")
        print(f"PyTorch max position: {pytorch_max_pos} (slow, fast)")
        print(f"Distance: {distance:.3f} pixels")
        print(f"C max value: {c_image[c_max_pos[0], c_max_pos[1]]:.3f}")
        print(f"PyTorch max value: {pytorch_image[pytorch_max_pos[0], pytorch_max_pos[1]]:.3f}")

        # Check tolerance (0.5 pixels per spec)
        assert distance <= 0.5, f"Max position distance {distance:.3f} exceeds 0.5 pixel tolerance"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "-s"])
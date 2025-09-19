"""
Acceptance Test AT-PARALLEL-026: Absolute Peak Position for Triclinic Crystal

This test validates the entire crystallographic chain for non-orthogonal unit cells
by ensuring the brightest Bragg peak appears at the same absolute pixel position
in both C and PyTorch implementations.
"""

import os
import pytest
import torch
import numpy as np
from pathlib import Path

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.config import DetectorConvention, CrystalShape
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator

# Mark as parallel validation tests
pytestmark = [
    pytest.mark.parallel_validation
]


class TestAT_PARALLEL_026_TriclinicAbsolutePosition:
    """AT-PARALLEL-026: Absolute Peak Position for Triclinic Crystal

    Validates that the brightest Bragg peak appears at the same absolute pixel
    position (±1.0 pixel) in both C and PyTorch implementations for triclinic crystals.
    """

    def setup_triclinic_config(self):
        """Setup configuration for triclinic crystal test case"""

        # Crystal configuration - triclinic cell 70,80,90,85,95,105
        crystal_config = CrystalConfig(
            cell_a=70.0,  # Angstroms
            cell_b=80.0,
            cell_c=90.0,
            cell_alpha=85.0,  # degrees
            cell_beta=95.0,
            cell_gamma=105.0,
            N_cells=[1, 1, 1],  # -N 1
            default_F=100.0,  # -default_F 100
            shape=CrystalShape.SQUARE,
            # Add small misset to bring reflections into diffraction condition
            misset_deg=[5.0, 3.0, 2.0]
        )

        # Detector configuration - 256x256, 0.1mm pixels, 150mm distance, MOSFLM
        detector_config = DetectorConfig(
            spixels=256,
            fpixels=256,
            pixel_size_mm=0.1,
            distance_mm=150.0,
            detector_convention=DetectorConvention.MOSFLM,
            oversample=1
        )

        # Beam configuration - lambda 1.5 Angstroms
        beam_config = BeamConfig(
            wavelength_A=1.5,
            fluence=1e24  # Add fluence for clearer peaks
        )

        return crystal_config, detector_config, beam_config

    def find_peak_position(self, image):
        """Find the position of the brightest peak in the image"""
        # Find maximum value and its position
        max_val = image.max()
        max_idx = (image == max_val).nonzero(as_tuple=True)

        # If multiple pixels have the same max value, take the center of mass
        if len(max_idx[0]) > 1:
            slow_idx = max_idx[0].float().mean()
            fast_idx = max_idx[1].float().mean()
        else:
            slow_idx = max_idx[0][0].float()
            fast_idx = max_idx[1][0].float()

        return slow_idx.item(), fast_idx.item(), max_val.item()

    def test_triclinic_absolute_peak_position_pytorch_only(self):
        """Test that PyTorch produces a peak for triclinic crystal"""

        # Setup configuration
        crystal_config, detector_config, beam_config = self.setup_triclinic_config()

        # Create models
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)

        # Create simulator
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run simulation
        image = simulator.run()

        # Find peak position
        slow, fast, intensity = self.find_peak_position(image)

        # Basic validation - should have a clear peak
        assert intensity > 1e-10, "No significant intensity found"
        assert 0 <= slow < 256, f"Peak slow position {slow} out of bounds"
        assert 0 <= fast < 256, f"Peak fast position {fast} out of bounds"

        # The peak should not be at the edges (indicates calculation error)
        assert 5 < slow < 250, f"Peak too close to slow edge: {slow}"
        assert 5 < fast < 250, f"Peak too close to fast edge: {fast}"

        print(f"PyTorch triclinic peak: ({slow:.1f}, {fast:.1f}) with intensity {intensity:.3e}")

    @pytest.mark.requires_c_binary
    def test_triclinic_absolute_peak_position_vs_c(self):
        """Test that PyTorch and C produce peaks at the same absolute position"""

        from scripts.c_reference_runner import CReferenceRunner

        # Setup configuration
        crystal_config, detector_config, beam_config = self.setup_triclinic_config()

        # Create models
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)

        # Create PyTorch simulator
        simulator = Simulator(crystal, detector, crystal_config, beam_config)

        # Run PyTorch simulation
        pytorch_image = simulator.run()
        pytorch_slow, pytorch_fast, pytorch_intensity = self.find_peak_position(pytorch_image)

        # Setup C runner
        runner = CReferenceRunner()

        # Run C simulation with same configs
        c_image = runner.run_simulation(
            detector_config,
            crystal_config,
            beam_config,
            label="Triclinic absolute position test"
        )

        assert c_image is not None, "C reference run failed"
        c_slow, c_fast, c_intensity = self.find_peak_position(
            torch.from_numpy(c_image).to(dtype=torch.float64)
        )

        # Compare peak positions - should be within 1 pixel
        position_diff = np.sqrt((pytorch_slow - c_slow)**2 + (pytorch_fast - c_fast)**2)

        print(f"PyTorch triclinic peak: ({pytorch_slow:.1f}, {pytorch_fast:.1f})")
        print(f"C-code triclinic peak: ({c_slow:.1f}, {c_fast:.1f})")
        print(f"Position difference: {position_diff:.2f} pixels")

        # Acceptance criterion: peaks within 1.0 pixel
        assert position_diff <= 1.0, (
            f"Peak position mismatch: PyTorch ({pytorch_slow:.1f}, {pytorch_fast:.1f}) "
            f"vs C ({c_slow:.1f}, {c_fast:.1f}), diff = {position_diff:.2f} pixels"
        )

        # Also check that intensities are reasonably similar (within factor of 2)
        intensity_ratio = pytorch_intensity / c_intensity
        assert 0.5 < intensity_ratio < 2.0, (
            f"Peak intensity mismatch: PyTorch {pytorch_intensity:.3e} "
            f"vs C {c_intensity:.3e}, ratio = {intensity_ratio:.2f}"
        )

    def test_triclinic_vs_cubic_peak_difference(self):
        """Test that triclinic and cubic crystals produce peaks at different positions"""

        # Setup triclinic configuration
        crystal_config_tri, detector_config, beam_config = self.setup_triclinic_config()

        # Create triclinic models and simulator
        crystal_tri = Crystal(crystal_config_tri)
        detector = Detector(detector_config)
        simulator_tri = Simulator(crystal_tri, detector, crystal_config_tri, beam_config)

        # Run triclinic simulation
        image_tri = simulator_tri.run()
        slow_tri, fast_tri, _ = self.find_peak_position(image_tri)

        # Setup cubic configuration (same size, cubic angles)
        crystal_config_cubic = CrystalConfig(
            cell_a=80.0,  # Use middle value
            cell_b=80.0,
            cell_c=80.0,
            cell_alpha=90.0,  # Cubic angles
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=[1, 1, 1],
            default_F=100.0,
            shape=CrystalShape.SQUARE,
            # Same misset for fair comparison
            misset_deg=[5.0, 3.0, 2.0]
        )

        # Create cubic models and simulator
        crystal_cubic = Crystal(crystal_config_cubic)
        simulator_cubic = Simulator(crystal_cubic, detector, crystal_config_cubic, beam_config)

        # Run cubic simulation
        image_cubic = simulator_cubic.run()
        slow_cubic, fast_cubic, _ = self.find_peak_position(image_cubic)

        # The peaks should be at different positions due to different unit cells
        position_diff = np.sqrt((slow_tri - slow_cubic)**2 + (fast_tri - fast_cubic)**2)

        print(f"Triclinic peak: ({slow_tri:.1f}, {fast_tri:.1f})")
        print(f"Cubic peak: ({slow_cubic:.1f}, {fast_cubic:.1f})")
        print(f"Position difference: {position_diff:.2f} pixels")

        # Peaks should be at measurably different positions (> 5 pixels)
        assert position_diff > 5.0, (
            f"Triclinic and cubic peaks too close: {position_diff:.2f} pixels apart"
        )
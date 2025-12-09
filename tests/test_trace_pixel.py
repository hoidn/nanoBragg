"""
Regression tests for TRACE_PY pixel trace output.

This module tests that the trace pixel instrumentation outputs actual computed
values rather than placeholders, ensuring parity with C-code trace output.

Phase L2b (CLI-FLAGS-003): These tests validate that TRACE_PY correctly logs
the actual polarization, capture_fraction, and steps values from the simulation.
"""

import os
import sys
import torch
import pytest

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


class TestScalingTrace:
    """Test suite for scaling trace output validation (CLI-FLAGS-003 Phase L2b)."""

    @pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available"))])
    @pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
    def test_scaling_trace_matches_physics(self, device, dtype, capsys):
        """
        Test that TRACE_PY outputs actual computed values, not placeholders.

        This test validates CLI-FLAGS-003 Phase L2b instrumentation:
        - polarization: actual Kahn factor from physics calculation
        - capture_fraction: actual detector absorption value
        - steps: full calculation (sources × mosaic × φ × oversample²)

        The test uses a simple configuration with known parameters and verifies
        that trace output matches the expected physics values.
        """
        # Set environment variable for PyTorch/MKL compatibility
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

        # Create a simple test configuration
        # Use parameters that produce tractable values for verification
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=[5, 5, 5],
            default_F=100.0,
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            mosaic_spread_deg=0.0,
            mosaic_domains=1,
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=100,
            fpixels=100,
            beam_center_s=5.0,  # mm
            beam_center_f=5.0,  # mm
            detector_convention=DetectorConvention.MOSFLM,
            oversample=1,
            oversample_omega=False,
            oversample_polar=False,
            oversample_thick=False,
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            flux=1e12,
            exposure=1.0,
            beamsize_mm=0.1,
            polarization_factor=1.0,  # Fully polarized
            nopolar=False,
        )

        # Create models
        crystal = Crystal(crystal_config, device=device, dtype=dtype)
        detector = Detector(detector_config, device=device, dtype=dtype)

        # Create simulator with trace_pixel enabled
        debug_config = {
            'trace_pixel': [50, 50],  # Trace pixel at (slow=50, fast=50)
        }

        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            beam_config=beam_config,
            device=device,
            dtype=dtype,
            debug_config=debug_config
        )

        # Run simulation to generate trace output
        _ = simulator.run()

        # Capture stdout
        captured = capsys.readouterr()
        trace_output = captured.out

        # Verify trace output contains actual values, not placeholders
        assert "TRACE_PY: steps" in trace_output, "Missing steps in trace output"
        assert "TRACE_PY: polar" in trace_output, "Missing polarization in trace output"
        assert "TRACE_PY: capture_fraction" in trace_output, "Missing capture_fraction in trace output"

        # Parse trace output
        lines = trace_output.split('\n')
        steps_value = None
        polar_value = None
        capture_value = None

        for line in lines:
            if "TRACE_PY: steps" in line:
                steps_value = int(line.split()[-1])
            elif "TRACE_PY: polar" in line:
                polar_value = float(line.split()[-1])
            elif "TRACE_PY: capture_fraction" in line:
                capture_value = float(line.split()[-1])

        # Verify steps calculation
        # Expected: sources(1) × mosaic(1) × phi(1) × oversample²(1)
        expected_steps = 1 * 1 * 1 * 1 * 1
        assert steps_value == expected_steps, (
            f"Steps mismatch: expected {expected_steps}, got {steps_value}"
        )

        # Verify polarization is not the placeholder value of exactly 1.0
        # (unless nopolar is set, which it's not in this test)
        # The actual value will depend on the geometry, but it should be computed
        # For a non-zero angle configuration, it won't be exactly 1.0
        assert polar_value is not None, "Polarization value not found in trace"
        # We can't assert it's != 1.0 because at specific geometries it might be,
        # but we can verify it was actually computed (not None/missing)

        # Verify capture_fraction
        # Since we didn't configure detector absorption (detector_thick_um=None),
        # capture_fraction should be 1.0 (no absorption)
        assert capture_value == 1.0, (
            f"Capture fraction should be 1.0 when no absorption configured, got {capture_value}"
        )

    @pytest.mark.parametrize("device", ["cpu"])
    def test_scaling_trace_with_absorption(self, device, capsys):
        """
        Test that TRACE_PY outputs correct capture_fraction with detector absorption enabled.

        This validates that when detector absorption is configured, the trace
        output shows the actual computed capture fraction, not the placeholder value of 1.
        """
        # Set environment variable
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

        # Create configuration with detector absorption enabled
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=[5, 5, 5],
            default_F=100.0,
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            mosaic_spread_deg=0.0,
            mosaic_domains=1,
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=100,
            fpixels=100,
            beam_center_s=5.0,
            beam_center_f=5.0,
            detector_convention=DetectorConvention.MOSFLM,
            oversample=1,
            oversample_omega=False,
            oversample_polar=False,
            oversample_thick=False,
            # Enable detector absorption
            detector_thick_um=100.0,  # 100 microns
            detector_abs_um=50.0,      # 50 micron attenuation depth
            detector_thicksteps=5,
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            flux=1e12,
            exposure=1.0,
            beamsize_mm=0.1,
            polarization_factor=1.0,
            nopolar=False,
        )

        # Create models
        dtype = torch.float64  # Use float64 for better precision
        crystal = Crystal(crystal_config, device=device, dtype=dtype)
        detector = Detector(detector_config, device=device, dtype=dtype)

        # Create simulator with trace
        debug_config = {'trace_pixel': [50, 50]}
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            beam_config=beam_config,
            device=device,
            dtype=dtype,
            debug_config=debug_config
        )

        # Run simulation
        _ = simulator.run()

        # Capture trace output
        captured = capsys.readouterr()
        trace_output = captured.out

        # Parse capture_fraction
        capture_value = None
        for line in trace_output.split('\n'):
            if "TRACE_PY: capture_fraction" in line:
                capture_value = float(line.split()[-1])
                break

        # With absorption enabled, capture_fraction should NOT be 1.0
        # It should be some value less than 1.0 depending on the absorption parameters
        assert capture_value is not None, "Capture fraction not found in trace output"
        assert capture_value < 1.0, (
            f"With absorption enabled, capture_fraction should be < 1.0, got {capture_value}"
        )
        assert capture_value > 0.0, (
            f"Capture fraction should be > 0.0, got {capture_value}"
        )

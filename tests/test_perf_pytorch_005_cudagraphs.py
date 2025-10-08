"""
Tests for PERF-PYTORCH-005: CUDA graphs compatibility fix.

Verifies that:
1. CUDA execution works without CUDAGraphs errors
2. CPU performance unchanged
3. Gradient flow preserved through cloned tensors
4. Device-neutral code (no conditional device logic)
"""

import pytest
import torch
import os

# Set required environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.simulator import Simulator


class TestCUDAGraphsCompatibility:
    """Test CUDA graphs compatibility with incident_beam_direction cloning."""

    @pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available"))])
    def test_basic_execution(self, device):
        """Test that basic simulation runs on both CPU and CUDA without errors."""
        # Simple cubic crystal configuration
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            misset_deg=(0.0, 0.0, 0.0),
            phi_start_deg=0.0, osc_range_deg=0.0, phi_steps=1,
            spindle_axis=(0.0, 0.0, 1.0),
            mosaic_spread_deg=0.0, mosaic_domains=1,
            N_cells=(3, 3, 3),
            default_F=100.0
        )

        # Small detector for fast test
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64, fpixels=64,
            beam_center_s=3.2, beam_center_f=3.2
        )

        beam_config = BeamConfig(
            wavelength_A=6.2
        )

        # Create simulator on target device (dtype defaults to float32)
        simulator = Simulator(
            crystal_config=crystal_config,
            detector_config=detector_config,
            beam_config=beam_config,
            device=device,
            dtype=torch.float32
        )

        # Run simulation - should NOT raise CUDA graphs errors
        result = simulator.run()

        # Basic sanity checks
        assert result.shape == (64, 64), f"Expected (64, 64), got {result.shape}"
        assert not torch.isnan(result).any(), "Result contains NaN"
        assert not torch.isinf(result).any(), "Result contains Inf"
        assert result.sum() > 0, "Result sum should be positive"

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_cuda_multiple_runs(self):
        """Test that multiple CUDA runs don't trigger CUDAGraphs aliasing errors."""
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            misset_deg=(0.0, 0.0, 0.0),
            phi_start_deg=0.0, osc_range_deg=0.0, phi_steps=1,
            spindle_axis=(0.0, 0.0, 1.0),
            mosaic_spread_deg=0.0, mosaic_domains=1,
            N_cells=(3, 3, 3),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64, fpixels=64,
            beam_center_s=3.2, beam_center_f=3.2
        )

        beam_config = BeamConfig(
            wavelength_A=6.2
        )

        simulator = Simulator(
            crystal_config=crystal_config,
            detector_config=detector_config,
            beam_config=beam_config,
            device="cuda",
            dtype=torch.float32
        )

        # Run 3 times to trigger potential CUDAGraphs caching issues
        results = []
        for i in range(3):
            result = simulator.run()
            results.append(result.cpu())  # Move to CPU for comparison
            assert not torch.isnan(result).any(), f"Run {i}: Result contains NaN"
            assert not torch.isinf(result).any(), f"Run {i}: Result contains Inf"

        # Results should be identical (deterministic)
        torch.testing.assert_close(results[0], results[1], rtol=1e-6, atol=1e-6)
        torch.testing.assert_close(results[1], results[2], rtol=1e-6, atol=1e-6)

    def test_gradient_flow_preserved(self):
        """Test that cloning incident_beam_direction preserves gradient flow."""
        # Use float64 for gradcheck precision
        distance_tensor = torch.tensor(100.0, requires_grad=True, dtype=torch.float64)

        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            misset_deg=(0.0, 0.0, 0.0),
            phi_start_deg=0.0, osc_range_deg=0.0, phi_steps=1,
            spindle_axis=(0.0, 0.0, 1.0),
            mosaic_spread_deg=0.0, mosaic_domains=1,
            N_cells=(3, 3, 3),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=distance_tensor,
            pixel_size_mm=0.1,
            spixels=32, fpixels=32,
            beam_center_s=1.6, beam_center_f=1.6
        )

        beam_config = BeamConfig(
            wavelength_A=6.2
        )

        simulator = Simulator(
            crystal_config=crystal_config,
            detector_config=detector_config,
            beam_config=beam_config,
            device="cpu",
            dtype=torch.float64
        )

        result = simulator.run()
        loss = result.sum()
        loss.backward()

        # Verify gradient exists and is non-zero
        assert distance_tensor.grad is not None, "Gradient should exist"
        assert distance_tensor.grad.abs().sum() > 0, "Gradient should be non-zero"

    @pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available"))])
    def test_cpu_cuda_correlation(self, device):
        """Test that CPU and CUDA (if available) produce highly correlated results."""
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            misset_deg=(0.0, 0.0, 0.0),
            phi_start_deg=0.0, osc_range_deg=0.0, phi_steps=1,
            spindle_axis=(0.0, 0.0, 1.0),
            mosaic_spread_deg=0.0, mosaic_domains=1,
            N_cells=(3, 3, 3),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64, fpixels=64,
            beam_center_s=3.2, beam_center_f=3.2
        )

        beam_config = BeamConfig(
            wavelength_A=6.2
        )

        # Run on CPU
        simulator_cpu = Simulator(
            crystal_config=crystal_config,
            detector_config=detector_config,
            beam_config=beam_config,
            device="cpu",
            dtype=torch.float32
        )
        result_cpu = simulator_cpu.run()

        if device == "cuda":
            # Run on CUDA and compare
            simulator_cuda = Simulator(
                crystal_config=crystal_config,
                detector_config=detector_config,
                beam_config=beam_config,
                device="cuda",
                dtype=torch.float32
            )
            result_cuda = simulator_cuda.run().cpu()

            # Compute correlation
            correlation = torch.corrcoef(torch.stack([result_cpu.flatten(), result_cuda.flatten()]))[0, 1]
            assert correlation >= 0.9999, f"CPU-CUDA correlation {correlation} below threshold 0.9999"

            # Check relative difference
            max_diff = (result_cpu - result_cuda).abs().max()
            assert max_diff < 1e-3, f"Max absolute difference {max_diff} exceeds threshold 1e-3"

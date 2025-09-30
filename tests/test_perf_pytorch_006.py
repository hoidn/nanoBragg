"""
Test PERF-PYTORCH-006: Float32 / Mixed Precision Performance Mode

Validates that the simulator can run in both float32 (performance mode)
and float64 (accuracy mode) with appropriate precision trade-offs.
"""

import pytest
import torch
import numpy as np
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_dtype_support(dtype):
    """Test that simulator works with both float32 and float64 dtypes."""
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(3, 3, 3),
        default_F=100.0,
    )
    crystal = Crystal(crystal_config, beam_config=BeamConfig(wavelength_A=1.0))

    detector_config = DetectorConfig(
        fpixels=64, spixels=64,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
    )
    detector = Detector(detector_config)

    beam_config = BeamConfig(wavelength_A=1.0)

    # Create simulator with specified dtype
    simulator = Simulator(
        crystal, detector,
        beam_config=beam_config,
        device=torch.device('cpu'),
        dtype=dtype
    )

    # Run simulation
    intensity = simulator.run()

    # Verify output dtype matches requested dtype
    assert intensity.dtype == dtype, f"Expected dtype {dtype}, got {intensity.dtype}"

    # Verify output is reasonable
    assert intensity.shape == (64, 64), f"Expected shape (64, 64), got {intensity.shape}"
    assert torch.isfinite(intensity).all(), "Intensity contains NaN or Inf values"
    assert (intensity >= 0).all(), "Intensity contains negative values"
    assert intensity.max() > 0, "All intensities are zero"


def test_float32_float64_correlation():
    """Test that float32 and float64 produce highly correlated results."""
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
    )
    beam_config = BeamConfig(wavelength_A=1.0)

    detector_config = DetectorConfig(
        fpixels=128, spixels=128,
        pixel_size_mm=0.1,
        distance_mm=100.0,
        detector_convention=DetectorConvention.MOSFLM,
    )

    # Run with float64
    crystal64 = Crystal(crystal_config, beam_config=beam_config)
    detector64 = Detector(detector_config)
    simulator64 = Simulator(
        crystal64, detector64,
        beam_config=beam_config,
        device=torch.device('cpu'),
        dtype=torch.float64
    )
    intensity64 = simulator64.run()

    # Run with float32
    crystal32 = Crystal(crystal_config, beam_config=beam_config)
    detector32 = Detector(detector_config)
    simulator32 = Simulator(
        crystal32, detector32,
        beam_config=beam_config,
        device=torch.device('cpu'),
        dtype=torch.float32
    )
    intensity32 = simulator32.run()

    # Convert to numpy for correlation
    img64 = intensity64.cpu().numpy().flatten()
    img32 = intensity32.cpu().numpy().astype(np.float64).flatten()

    # Compute correlation
    correlation = np.corrcoef(img64, img32)[0, 1]
    print(f"Float32 vs Float64 correlation: {correlation:.6f}")

    # Correlation should be very high (>0.999)
    assert correlation > 0.999, f"Correlation {correlation:.6f} < 0.999"

    # Verify intensity scales are similar (within 1%)
    ratio = intensity32.sum().item() / intensity64.sum().item()
    print(f"Float32/Float64 sum ratio: {ratio:.6f}")
    assert 0.99 < ratio < 1.01, f"Sum ratio {ratio:.6f} outside [0.99, 1.01]"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

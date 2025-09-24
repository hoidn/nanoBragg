"""Quick test to check if oversample is working."""

import torch
import numpy as np
from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig, DetectorConvention
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator


def test_oversample_intensity():
    """Test that oversampling doesn't change total intensity (just resolution)."""

    # Crystal config - simple cubic
    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(1, 1, 1),  # Small for fast test
        default_F=100.0,
        phi_start_deg=0.0,
        osc_range_deg=0.0,
        phi_steps=1,
        mosaic_spread_deg=0.0,
        mosaic_domains=1
    )

    results = {}

    for oversample in [1, 2, 4]:
        # Detector config with oversample
        detector_config = DetectorConfig(
            spixels=64,  # Small for fast test
            fpixels=64,
            pixel_size_mm=0.1,
            distance_mm=50.0,
            detector_convention=DetectorConvention.MOSFLM,
            oversample=oversample
        )

        # Beam config
        beam_config = BeamConfig(
            wavelength_A=1.0,
            fluence=1e12
        )

        # Create simulator
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=crystal_config,
            beam_config=beam_config
        )

        # Run simulation
        image = simulator.run()

        if isinstance(image, torch.Tensor):
            image = image.detach().cpu().numpy()

        results[oversample] = {
            'total': np.sum(image),
            'max': np.max(image),
            'mean': np.mean(image),
            'std': np.std(image),
            'nonzero': np.count_nonzero(image > 1e-10)
        }

    print("\n=== Oversample Test Results ===")
    for oversample, data in results.items():
        print(f"\nOversample={oversample}:")
        print(f"  Total intensity: {data['total']:.3e}")
        print(f"  Max pixel: {data['max']:.3e}")
        print(f"  Mean: {data['mean']:.3e}")
        print(f"  Std: {data['std']:.3e}")
        print(f"  Non-zero pixels: {data['nonzero']}")

    # Check that total intensity is approximately conserved
    # (within 10% - some variation expected due to numerical precision)
    ratio_2_1 = results[2]['total'] / results[1]['total']
    ratio_4_1 = results[4]['total'] / results[1]['total']

    print(f"\nIntensity ratios:")
    print(f"  oversample=2 / oversample=1: {ratio_2_1:.3f}")
    print(f"  oversample=4 / oversample=1: {ratio_4_1:.3f}")

    # Total intensity should be approximately conserved
    assert 0.9 < ratio_2_1 < 1.1, f"Total intensity changed too much: {ratio_2_1}"
    assert 0.9 < ratio_4_1 < 1.1, f"Total intensity changed too much: {ratio_4_1}"


if __name__ == "__main__":
    test_oversample_intensity()
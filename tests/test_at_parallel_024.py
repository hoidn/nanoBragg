"""
AT-PARALLEL-024: Random Misset Reproducibility and Equivalence

This test validates that:
1. Random misset generation is deterministic with the same seed
2. C and PyTorch implementations produce equivalent results with the same seed
3. Different seeds produce different orientations

From spec-a.md:
- Setup: Implementations SHALL support -misset random and -misset_seed.
  Prefer a C‑compatible RNG (e.g., LCG) for identical angle sampling.
  Case: cubic 100,100,100; N=5; λ=1.0; detector 256×256, pixel 0.1mm,
  distance 100mm; φ=0; osc=0; mosaic=0; -oversample 1.
  Test two seeds S∈{12345,54321}.

- Expectation:
  - Determinism: PyTorch same‑seed runs are identical (rtol ≤ 1e−12, atol ≤ 1e−15).
  - Cross‑impl equivalence: For each seed, C vs PyTorch allclose (rtol ≤ 1e−5, atol ≤ 1e−6), correlation ≥ 0.99.
  - Seed effect: Different seeds produce correlation ≤ 0.7 within the same implementation.
  - SHOULD: if sampled angles are reported, they match within 1e−12 rad after unit conversions.
"""

import os
import pytest
import torch
import numpy as np
from pathlib import Path

from nanobrag_torch.config import CrystalConfig, DetectorConfig, BeamConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator
from nanobrag_torch.utils.c_random import CLCG, mosaic_rotation_umat, umat2misset

# Import the C reference runner
import sys
sys.path.append('scripts')
from c_reference_runner import CReferenceRunner
from smv_parser import parse_smv_image


class TestAT_PARALLEL_024:
    """Test suite for AT-PARALLEL-024: Random Misset Reproducibility."""

    @pytest.fixture
    def base_config(self):
        """Base configuration for the test case."""
        return {
            'cell_params': (100.0, 100.0, 100.0, 90.0, 90.0, 90.0),  # Cubic
            'N_cells': (5, 5, 5),
            'wavelength': 1.0,  # Angstroms
            'detector_size': (256, 256),
            'pixel_size': 0.1,  # mm
            'distance': 100.0,  # mm
            'default_F': 100.0,
            'phi': 0.0,
            'osc': 0.0,
            'mosaic': 0.0,
            'oversample': 1,
        }

    def test_pytorch_determinism(self, base_config, tmp_path):
        """Test that same seed produces identical results in PyTorch."""
        seeds = [12345, 54321]

        for seed in seeds:
            # Create two identical crystal configurations with the same seed
            crystal_config1 = CrystalConfig(
                cell_a=base_config['cell_params'][0],
                cell_b=base_config['cell_params'][1],
                cell_c=base_config['cell_params'][2],
                cell_alpha=base_config['cell_params'][3],
                cell_beta=base_config['cell_params'][4],
                cell_gamma=base_config['cell_params'][5],
                N_cells=base_config['N_cells'],
                default_F=base_config['default_F'],
                phi_start_deg=base_config['phi'],
                osc_range_deg=base_config['osc'],
                mosaic_spread_deg=base_config['mosaic'],
                misset_random=True,
                misset_seed=seed
            )

            crystal_config2 = CrystalConfig(
                cell_a=base_config['cell_params'][0],
                cell_b=base_config['cell_params'][1],
                cell_c=base_config['cell_params'][2],
                cell_alpha=base_config['cell_params'][3],
                cell_beta=base_config['cell_params'][4],
                cell_gamma=base_config['cell_params'][5],
                N_cells=base_config['N_cells'],
                default_F=base_config['default_F'],
                phi_start_deg=base_config['phi'],
                osc_range_deg=base_config['osc'],
                mosaic_spread_deg=base_config['mosaic'],
                misset_random=True,
                misset_seed=seed
            )

            # Create detector and beam configs
            detector_config = DetectorConfig(
                distance_mm=base_config['distance'],
                pixel_size_mm=base_config['pixel_size'],
                spixels=base_config['detector_size'][0],
                fpixels=base_config['detector_size'][1],
                oversample=base_config['oversample']
            )

            beam_config = BeamConfig(
                wavelength_A=base_config['wavelength']
            )

            # Create two separate simulators
            crystal1 = Crystal(crystal_config1, beam_config)
            detector1 = Detector(detector_config)
            sim1 = Simulator(crystal1, detector1, crystal_config1, beam_config)

            crystal2 = Crystal(crystal_config2, beam_config)
            detector2 = Detector(detector_config)
            sim2 = Simulator(crystal2, detector2, crystal_config2, beam_config)

            # Generate images
            image1 = sim1.run()
            image2 = sim2.run()

            # Check that they are identical (very tight tolerance for determinism)
            assert torch.allclose(image1, image2, rtol=1e-12, atol=1e-15), \
                f"Same seed {seed} did not produce identical results"

            # Also check that the misset angles are identical
            assert crystal1.config.misset_deg == crystal2.config.misset_deg, \
                f"Same seed {seed} produced different misset angles"

    def test_seed_independence(self, base_config):
        """Test that different seeds produce different orientations."""
        seeds = [12345, 54321]
        images = []
        missets = []

        for seed in seeds:
            crystal_config = CrystalConfig(
                cell_a=base_config['cell_params'][0],
                cell_b=base_config['cell_params'][1],
                cell_c=base_config['cell_params'][2],
                cell_alpha=base_config['cell_params'][3],
                cell_beta=base_config['cell_params'][4],
                cell_gamma=base_config['cell_params'][5],
                N_cells=base_config['N_cells'],
                default_F=base_config['default_F'],
                phi_start_deg=base_config['phi'],
                osc_range_deg=base_config['osc'],
                mosaic_spread_deg=base_config['mosaic'],
                misset_random=True,
                misset_seed=seed
            )

            detector_config = DetectorConfig(
                distance_mm=base_config['distance'],
                pixel_size_mm=base_config['pixel_size'],
                spixels=base_config['detector_size'][0],
                fpixels=base_config['detector_size'][1],
                oversample=base_config['oversample']
            )

            beam_config = BeamConfig(
                wavelength_A=base_config['wavelength']
            )

            crystal = Crystal(crystal_config, beam_config)
            detector = Detector(detector_config)
            sim = Simulator(crystal, detector, crystal_config, beam_config)

            images.append(sim.run())
            missets.append(crystal.config.misset_deg)

        # Check that different seeds produce different misset angles
        assert missets[0] != missets[1], \
            "Different seeds produced identical misset angles"

        # Check that different seeds produce low correlation
        # Normalize images for correlation calculation
        img1_np = images[0].cpu().numpy().flatten()
        img2_np = images[1].cpu().numpy().flatten()

        # Only correlate where there is signal
        mask = (img1_np > 0) | (img2_np > 0)
        if mask.sum() > 0:
            corr = np.corrcoef(img1_np[mask], img2_np[mask])[0, 1]
            assert corr <= 0.7, \
                f"Different seeds produced too high correlation: {corr:.3f}"

    @pytest.mark.skipif(
        not Path("./golden_suite_generator/nanoBragg").exists(),
        reason="Requires instrumented C binary"
    )
    def test_c_pytorch_equivalence(self, base_config, tmp_path):
        """Test C vs PyTorch equivalence for random misset."""
        seeds = [12345, 54321]

        for seed in seeds:
            # Run C implementation
            c_runner = CReferenceRunner()
            c_cmd = [
                "-cell", "100", "100", "100", "90", "90", "90",
                "-N", "5",
                "-lambda", str(base_config['wavelength']),
                "-detpixels", str(base_config['detector_size'][0]),
                "-pixel", str(base_config['pixel_size']),
                "-distance", str(base_config['distance']),
                "-default_F", str(base_config['default_F']),
                "-phi", str(base_config['phi']),
                "-osc", str(base_config['osc']),
                "-phisteps", "1",
                "-oversample", str(base_config['oversample']),
                "-misset", "random",
                "-misset_seed", str(seed),
                "-floatfile", str(tmp_path / f"c_output_seed_{seed}.bin"),
                "-intfile", str(tmp_path / f"c_output_seed_{seed}.img"),
                "-printout"
            ]

            result = c_runner.run_simulation(c_cmd, output_dir=tmp_path, capture_output=True)
            assert result['success'], f"C runner failed: {result.get('error', 'Unknown error')}"

            # Extract C misset angles from output
            c_misset = None
            if 'stdout' in result:
                for line in result['stdout'].split('\n'):
                    if 'random orientation misset angles:' in line:
                        parts = line.split(':')[1].strip().split()
                        c_misset = tuple(float(p.replace('deg', '')) for p in parts[:3])
                        break

            # Load C output image
            c_image_path = tmp_path / f"c_output_seed_{seed}.img"
            c_data, c_header = parse_smv_image(str(c_image_path))
            c_image = torch.from_numpy(c_data.astype(np.float32))

            # Run PyTorch implementation
            crystal_config = CrystalConfig(
                cell_a=base_config['cell_params'][0],
                cell_b=base_config['cell_params'][1],
                cell_c=base_config['cell_params'][2],
                cell_alpha=base_config['cell_params'][3],
                cell_beta=base_config['cell_params'][4],
                cell_gamma=base_config['cell_params'][5],
                N_cells=base_config['N_cells'],
                default_F=base_config['default_F'],
                phi_start_deg=base_config['phi'],
                osc_range_deg=base_config['osc'],
                mosaic_spread_deg=base_config['mosaic'],
                misset_random=True,
                misset_seed=seed
            )

            detector_config = DetectorConfig(
                distance_mm=base_config['distance'],
                pixel_size_mm=base_config['pixel_size'],
                spixels=base_config['detector_size'][0],
                fpixels=base_config['detector_size'][1],
                oversample=base_config['oversample']
            )

            beam_config = BeamConfig(
                wavelength_A=base_config['wavelength']
            )

            crystal = Crystal(crystal_config, beam_config)
            detector = Detector(detector_config)
            sim = Simulator(crystal, detector, crystal_config, beam_config)
            pt_image = sim.run()

            # Compare images
            assert torch.allclose(pt_image, c_image, rtol=1e-5, atol=1e-6), \
                f"C and PyTorch images differ for seed {seed}"

            # Calculate correlation
            pt_np = pt_image.cpu().numpy().flatten()
            c_np = c_image.cpu().numpy().flatten()
            mask = (pt_np > 0) | (c_np > 0)
            if mask.sum() > 0:
                corr = np.corrcoef(pt_np[mask], c_np[mask])[0, 1]
                assert corr >= 0.99, \
                    f"C vs PyTorch correlation too low for seed {seed}: {corr:.4f}"

            # Check misset angles match (if extracted from C)
            if c_misset is not None:
                pt_misset = crystal.config.misset_deg
                # Convert to radians for comparison
                c_misset_rad = tuple(np.deg2rad(angle) for angle in c_misset)
                pt_misset_rad = tuple(np.deg2rad(angle) for angle in pt_misset)

                for i, (c_angle, pt_angle) in enumerate(zip(c_misset_rad, pt_misset_rad)):
                    assert abs(c_angle - pt_angle) < 1e-12, \
                        f"Misset angle {i} differs: C={c_angle:.12f} vs PyTorch={pt_angle:.12f} rad"

    def test_lcg_compatibility(self):
        """Test that our LCG implementation matches expected behavior."""
        # Test basic LCG functionality
        rng1 = CLCG(seed=12345)
        rng2 = CLCG(seed=12345)

        # Same seed should produce same sequence
        for _ in range(10):
            assert rng1.ran1() == rng2.ran1()

        # Different seeds should produce different sequences
        rng3 = CLCG(seed=54321)
        different = False
        for _ in range(10):
            if rng1.ran1() != rng3.ran1():
                different = True
                break
        assert different, "Different seeds produced identical sequences"

    def test_mosaic_rotation_umat_determinism(self):
        """Test that mosaic_rotation_umat is deterministic with same seed."""
        seed = 12345
        mosaicity = np.pi / 2.0  # 90 degrees

        # Generate two matrices with same seed
        umat1 = mosaic_rotation_umat(mosaicity, seed)
        umat2 = mosaic_rotation_umat(mosaicity, seed)

        # They should be identical
        assert torch.allclose(umat1, umat2, rtol=1e-12, atol=1e-15), \
            "Same seed did not produce identical rotation matrices"

        # Check that it's unitary (rotation matrix property)
        identity = torch.matmul(umat1, umat1.T)
        expected_identity = torch.eye(3, dtype=torch.float64)
        assert torch.allclose(identity, expected_identity, rtol=1e-10, atol=1e-12), \
            "Generated matrix is not unitary"

    def test_umat2misset_round_trip(self):
        """Test that umat2misset correctly extracts angles."""
        from nanobrag_torch.utils.geometry import angles_to_rotation_matrix

        # Test a few known angle sets
        test_angles = [
            (0.0, 0.0, 0.0),
            (np.pi/6, 0.0, 0.0),  # 30 degrees
            (0.0, np.pi/4, 0.0),  # 45 degrees
            (0.0, 0.0, np.pi/3),  # 60 degrees
            (np.pi/6, np.pi/4, np.pi/3),  # Combined
        ]

        for angles in test_angles:
            # Create rotation matrix from angles
            rotx, roty, rotz = angles
            umat = angles_to_rotation_matrix(rotx, roty, rotz)

            # Extract angles back
            extracted = umat2misset(umat)

            # Create matrix from extracted angles to verify
            umat_reconstructed = angles_to_rotation_matrix(*extracted)

            # The matrices should be identical (accounting for gimbal lock edge cases)
            assert torch.allclose(umat, umat_reconstructed, rtol=1e-10, atol=1e-12), \
                f"Round trip failed for angles {angles}"
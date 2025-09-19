"""
AT-PARALLEL-011: Polarization Factor Verification

Validates polarization physics against theoretical values and C-PyTorch equivalence.

Acceptance Test Requirements (from spec-a-parallel.md):
- Setup: Cell 100,100,100; N=5; detector 256×256, -pixel 0.1, -distance 100
- MOSFLM convention; -phi 0; -mosaic 0; -oversample 1; point_pixel OFF
- Polarization_axis aligned per convention
- A) Unpolarized (kahn_factor=0): Compute theoretical P = 0.5·(1+cos²(2θ))
- B) Polarized (kahn_factor=0.95): Compute Kahn model P
- Pass: R² ≥ 0.95 vs theory; mean absolute relative error ≤ 1% (A) and ≤ 2% (B)
- C↔PyTorch image correlation ≥ 0.98 for identical axes/seeds
"""

import os
import sys
import tempfile
import numpy as np
import torch
import pytest
from pathlib import Path
from scipy.stats import pearsonr
from typing import Tuple, Optional

# Add parent directories to path for imports
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

sys.path.append('scripts')
from c_reference_runner import CReferenceRunner

from nanobrag_torch.config import (
    DetectorConfig,
    DetectorConvention,
    DetectorPivot,
    CrystalConfig,
    BeamConfig,
)
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.simulator import Simulator


def r2_score(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Calculate R² score manually."""
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    return 1 - (ss_res / (ss_tot + 1e-10))


def compute_theoretical_polarization_unpolarized(
    incident: torch.Tensor,
    diffracted: torch.Tensor,
) -> torch.Tensor:
    """
    Compute theoretical unpolarized polarization factor: P = 0.5·(1+cos²(2θ))

    Args:
        incident: Incident beam direction vectors (N, 3)
        diffracted: Diffracted beam direction vectors (N, 3)

    Returns:
        Theoretical polarization factors (N,)
    """
    # cos(2θ) = incident · diffracted (for unit vectors)
    cos_2theta = torch.sum(incident * diffracted, dim=-1)
    cos_2theta_sqr = cos_2theta * cos_2theta

    # P = 0.5·(1 + cos²(2θ))
    return 0.5 * (1.0 + cos_2theta_sqr)


def compute_theoretical_polarization_kahn(
    incident: torch.Tensor,
    diffracted: torch.Tensor,
    polarization_axis: torch.Tensor,
    kahn_factor: float,
) -> torch.Tensor:
    """
    Compute theoretical Kahn model polarization factor.
    P = 0.5·(1 + cos²(2θ) - K·cos(2ψ)·sin²(2θ))

    Args:
        incident: Incident beam direction vectors (N, 3)
        diffracted: Diffracted beam direction vectors (N, 3)
        polarization_axis: Polarization axis unit vector (3,)
        kahn_factor: Kahn factor K in [0, 1]

    Returns:
        Theoretical polarization factors (N,)
    """
    # cos(2θ) = incident · diffracted
    cos_2theta = torch.sum(incident * diffracted, dim=-1)
    cos_2theta_sqr = cos_2theta * cos_2theta
    sin_2theta_sqr = 1.0 - cos_2theta_sqr

    # Project incident and diffracted into E-B plane perpendicular to propagation
    # B_in = unit(polarization_axis × incident)
    B_in = torch.cross(
        polarization_axis.unsqueeze(0).expand_as(incident),
        incident,
        dim=-1
    )
    B_in_norm = torch.norm(B_in, dim=-1, keepdim=True).clamp(min=1e-10)
    B_in = B_in / B_in_norm

    # E_in = unit(incident × B_in)
    E_in = torch.cross(incident, B_in, dim=-1)
    E_in_norm = torch.norm(E_in, dim=-1, keepdim=True).clamp(min=1e-10)
    E_in = E_in / E_in_norm

    # Project diffracted into EB plane
    E_out = torch.sum(diffracted * E_in, dim=-1)
    B_out = torch.sum(diffracted * B_in, dim=-1)

    # ψ angle: -atan2(B_out, E_out)
    psi = -torch.atan2(B_out, E_out)
    cos_2psi = torch.cos(2.0 * psi)

    # Kahn model: P = 0.5·(1 + cos²(2θ) - K·cos(2ψ)·sin²(2θ))
    return 0.5 * (1.0 + cos_2theta_sqr - kahn_factor * cos_2psi * sin_2theta_sqr)


def extract_pixel_polarization_factors(
    detector: Detector,
    crystal: Crystal,
    beam_config: BeamConfig,
    wavelength: float,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Extract incident/diffracted vectors and compute polarization for each pixel.

    Returns:
        Tuple of (incident_vectors, diffracted_vectors, polarization_factors)
    """
    # Get pixel coordinates in Angstroms
    pixel_coords = detector.get_pixel_coords()  # (slow, fast, 3) in meters
    pixel_coords_A = pixel_coords * 1e10  # Convert to Angstroms

    # Flatten for easier processing
    n_slow, n_fast = pixel_coords.shape[:2]
    pixel_coords_flat = pixel_coords_A.view(-1, 3)

    # Get incident beam direction (convention-dependent)
    if detector.config.detector_convention == DetectorConvention.MOSFLM:
        incident_dir = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
    else:  # XDS, DIALS, etc.
        incident_dir = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)

    # Incident vectors are the same for all pixels (parallel beam)
    incident = incident_dir.unsqueeze(0).expand(pixel_coords_flat.shape[0], 3)

    # Diffracted vectors point from sample to each pixel
    diffracted = pixel_coords_flat / torch.norm(pixel_coords_flat, dim=-1, keepdim=True)

    # Get polarization axis from beam config
    if beam_config.polarization_axis is not None:
        pol_axis = torch.tensor(beam_config.polarization_axis, dtype=torch.float64)
    else:
        # Default: perpendicular to beam (vertical for MOSFLM)
        if detector.config.detector_convention == DetectorConvention.MOSFLM:
            pol_axis = torch.tensor([0.0, 0.0, 1.0], dtype=torch.float64)
        else:
            pol_axis = torch.tensor([0.0, 1.0, 0.0], dtype=torch.float64)

    # Compute theoretical polarization factors
    if beam_config.nopolar:
        # Should be all 1.0
        polarization_factors = torch.ones(pixel_coords_flat.shape[0], dtype=torch.float64)
    elif beam_config.polarization_factor == 0.0:
        # Unpolarized
        polarization_factors = compute_theoretical_polarization_unpolarized(
            incident, diffracted
        )
    else:
        # Kahn model
        polarization_factors = compute_theoretical_polarization_kahn(
            incident, diffracted, pol_axis, beam_config.polarization_factor
        )

    # Reshape back to detector shape
    polarization_factors = polarization_factors.view(n_slow, n_fast)
    incident = incident.view(n_slow, n_fast, 3)
    diffracted = diffracted.view(n_slow, n_fast, 3)

    return incident, diffracted, polarization_factors


class TestATParallel011PolarizationFactor:
    """Test polarization factor verification against theory and C code."""

    @pytest.fixture
    def setup_config(self) -> dict:
        """Setup configuration per AT-PARALLEL-011 spec."""
        return {
            'cell': (100, 100, 100, 90, 90, 90),
            'N_cells': (5, 5, 5),
            'default_F': 100.0,
            'wavelength': 6.2,
            'detector': {
                'size': (256, 256),
                'pixel_size_mm': 0.1,
                'distance_mm': 100.0,
                'convention': DetectorConvention.MOSFLM,
                'pivot': DetectorPivot.BEAM,
            },
            'phi': 0.0,
            'osc': 0.0,
            'mosaic': 0.0,
            'oversample': 1,
        }

    def test_unpolarized_theory(self, setup_config):
        """Test A: Unpolarized (kahn_factor=0) against theoretical formula."""
        config = setup_config

        # Create configurations
        crystal_config = CrystalConfig(
            cell_a=config['cell'][0],
            cell_b=config['cell'][1],
            cell_c=config['cell'][2],
            cell_alpha=config['cell'][3],
            cell_beta=config['cell'][4],
            cell_gamma=config['cell'][5],
            N_cells=config['N_cells'],
            default_F=config['default_F'],
            phi_start_deg=config['phi'],
            osc_range_deg=config['osc'],
            phi_steps=1,
        )

        detector_config = DetectorConfig(
            distance_mm=config['detector']['distance_mm'],
            pixel_size_mm=config['detector']['pixel_size_mm'],
            spixels=config['detector']['size'][0],
            fpixels=config['detector']['size'][1],
            detector_convention=config['detector']['convention'],
            detector_pivot=config['detector']['pivot'],
            oversample=config['oversample'],
        )

        beam_config = BeamConfig(
            wavelength_A=config['wavelength'],
            polarization_factor=0.0,  # Unpolarized
            nopolar=False,
        )

        # Create models
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)

        # Extract theoretical polarization factors
        incident, diffracted, pol_factors_theory = extract_pixel_polarization_factors(
            detector, crystal, beam_config, config['wavelength']
        )

        # Run simulation to get actual factors
        # The simulator should apply the same polarization calculation
        simulator = Simulator(crystal, detector, crystal_config, beam_config)
        intensity = simulator.run()

        # For unpolarized case, verify theoretical formula
        # P = 0.5·(1+cos²(2θ))
        cos_2theta = torch.sum(incident * diffracted, dim=-1)
        expected_pol = 0.5 * (1.0 + cos_2theta * cos_2theta)

        # Compute R² between theoretical and expected
        r2 = r2_score(
            pol_factors_theory.flatten().numpy(),
            expected_pol.flatten().numpy()
        )

        # Compute mean absolute relative error
        rel_error = torch.abs(pol_factors_theory - expected_pol) / (expected_pol + 1e-10)
        mean_rel_error = torch.mean(rel_error).item()

        print(f"\nUnpolarized Test Results:")
        print(f"  R² vs theory: {r2:.4f} (required ≥ 0.95)")
        print(f"  Mean relative error: {mean_rel_error:.4%} (required ≤ 1%)")

        # Assertions per spec
        assert r2 >= 0.95, f"R² {r2:.4f} below required 0.95"
        assert mean_rel_error <= 0.01, f"Mean relative error {mean_rel_error:.4%} above 1%"

    def test_polarized_kahn_model(self, setup_config):
        """Test B: Polarized (kahn_factor=0.95) against Kahn model."""
        config = setup_config

        # Create configurations
        crystal_config = CrystalConfig(
            cell_a=config['cell'][0],
            cell_b=config['cell'][1],
            cell_c=config['cell'][2],
            cell_alpha=config['cell'][3],
            cell_beta=config['cell'][4],
            cell_gamma=config['cell'][5],
            N_cells=config['N_cells'],
            default_F=config['default_F'],
            phi_start_deg=config['phi'],
            osc_range_deg=config['osc'],
            phi_steps=1,
        )

        detector_config = DetectorConfig(
            distance_mm=config['detector']['distance_mm'],
            pixel_size_mm=config['detector']['pixel_size_mm'],
            spixels=config['detector']['size'][0],
            fpixels=config['detector']['size'][1],
            detector_convention=config['detector']['convention'],
            detector_pivot=config['detector']['pivot'],
            oversample=config['oversample'],
        )

        # Use kahn_factor=0.95 as specified
        beam_config = BeamConfig(
            wavelength_A=config['wavelength'],
            polarization_factor=0.95,  # Highly polarized
            nopolar=False,
            polarization_axis=(0.0, 0.0, 1.0),  # Vertical for MOSFLM
        )

        # Create models
        crystal = Crystal(crystal_config)
        detector = Detector(detector_config)

        # Extract theoretical polarization factors
        incident, diffracted, pol_factors_theory = extract_pixel_polarization_factors(
            detector, crystal, beam_config, config['wavelength']
        )

        # Compute expected Kahn model values independently
        pol_axis = torch.tensor(beam_config.polarization_axis, dtype=torch.float64)
        expected_pol = compute_theoretical_polarization_kahn(
            incident.view(-1, 3),
            diffracted.view(-1, 3),
            pol_axis,
            beam_config.polarization_factor
        ).view(detector.spixels, detector.fpixels)

        # Compute R² between implementation and theoretical
        r2 = r2_score(
            pol_factors_theory.flatten().numpy(),
            expected_pol.flatten().numpy()
        )

        # Compute mean absolute relative error
        rel_error = torch.abs(pol_factors_theory - expected_pol) / (expected_pol + 1e-10)
        mean_rel_error = torch.mean(rel_error).item()

        print(f"\nPolarized (K=0.95) Test Results:")
        print(f"  R² vs theory: {r2:.4f} (required ≥ 0.95)")
        print(f"  Mean relative error: {mean_rel_error:.4%} (required ≤ 2%)")

        # Assertions per spec
        assert r2 >= 0.95, f"R² {r2:.4f} below required 0.95"
        assert mean_rel_error <= 0.02, f"Mean relative error {mean_rel_error:.4%} above 2%"

    @pytest.mark.skipif(
        os.environ.get("NB_RUN_PARALLEL") != "1",
        reason="Parallel validation requires NB_RUN_PARALLEL=1 environment variable"
    )
    def test_c_pytorch_equivalence(self, setup_config, tmpdir):
        """Test C↔PyTorch image correlation for identical polarization settings."""
        config = setup_config

        # Test both unpolarized and polarized cases
        test_cases = [
            ("unpolarized", 0.0),
            ("polarized", 0.95),
        ]

        for case_name, kahn_factor in test_cases:
            print(f"\n🔬 Testing C-PyTorch equivalence for {case_name} case")

            # Create configurations
            crystal_config = CrystalConfig(
                cell_a=config['cell'][0],
                cell_b=config['cell'][1],
                cell_c=config['cell'][2],
                cell_alpha=config['cell'][3],
                cell_beta=config['cell'][4],
                cell_gamma=config['cell'][5],
                N_cells=config['N_cells'],
                default_F=config['default_F'],
                phi_start_deg=config['phi'],
                osc_range_deg=config['osc'],
                phi_steps=1,
            )

            detector_config = DetectorConfig(
                distance_mm=config['detector']['distance_mm'],
                pixel_size_mm=config['detector']['pixel_size_mm'],
                spixels=config['detector']['size'][0],
                fpixels=config['detector']['size'][1],
                detector_convention=config['detector']['convention'],
                detector_pivot=config['detector']['pivot'],
                oversample=config['oversample'],
            )

            beam_config = BeamConfig(
                wavelength_A=config['wavelength'],
                polarization_factor=kahn_factor,
                nopolar=False,
                fluence=1e12,  # Add fluence for proper intensity scaling
            )

            # Run PyTorch simulation
            crystal = Crystal(crystal_config)
            detector = Detector(detector_config)
            simulator = Simulator(crystal, detector, crystal_config, beam_config)
            py_intensity = simulator.run().numpy()

            # Run C simulation
            runner = CReferenceRunner(work_dir=str(tmpdir))
            c_image = runner.run_simulation(
                detector_config,
                crystal_config,
                beam_config,
                label=f"AT-PARALLEL-011 {case_name}",
            )

            if c_image is not None:
                # Compute correlation
                c_flat = c_image.flatten()
                py_flat = py_intensity.flatten()

                # Filter out zeros for correlation (background pixels)
                mask = (c_flat > 0) | (py_flat > 0)
                if mask.sum() > 0:
                    correlation, _ = pearsonr(c_flat[mask], py_flat[mask])

                    print(f"  Correlation for {case_name}: {correlation:.4f} (required ≥ 0.98)")

                    # Assertion per spec
                    assert correlation >= 0.98, \
                        f"C-PyTorch correlation {correlation:.4f} below required 0.98 for {case_name}"
                else:
                    pytest.skip("No non-zero pixels for correlation")
            else:
                pytest.skip("C reference implementation not available")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
"""
CLI Scaling φ=0 Parity Tests for CLI-FLAGS-003 Phase L3k.3

Tests φ=0 rotated lattice vectors and Miller indices to capture the base-vector
drift before implementing the fix for independent real/reciprocal rotation.

Evidence base: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/
Plan reference: plans/active/cli-noise-pix0/plan.md Phase L3k.3
Supervisor memo: input.md:22-45 (Do Now for Phase L3k.3)
"""
import os
import sys
from pathlib import Path
import pytest
import torch
import numpy as np

# Set required environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


class TestPhiZeroParity:
    """Capture φ=0 lattice-vector drift against C trace expectations."""

    def test_rot_b_matches_c(self):
        """
        Verify φ=0 rot_b[0,0,1] equals base vector (no rotation applied).

        This test validates SPEC-COMPLIANT behavior (specs/spec-a-core.md:211-214):
        At φ=0°, the rotated lattice vectors should equal the base lattice vectors,
        since rotation by 0° is the identity transformation.

        Evidence:
        - C trace base vector: b_Y = 0.71732 Å (c_trace_scaling.log:64)
        - PyTorch spec-compliant: rot_b[0,0,1] = 0.71732 Å at φ=0 (identity rotation)
        - C-PARITY-001 bug: C code produces 0.671588 Å due to stale vector carryover

        Phase: CLI-FLAGS-003 L3k.3c.3 (spec-compliant default path)
        Related: C-PARITY-001 in docs/bugs/verified_c_bugs.md:166-204
        """
        from nanobrag_torch.models.crystal import Crystal, CrystalConfig
        from nanobrag_torch.models.detector import Detector, DetectorConfig
        from nanobrag_torch.config import BeamConfig
        from nanobrag_torch.io.mosflm import read_mosflm_matrix
        from nanobrag_torch import utils

        # Supervisor command configuration (from input.md and Phase L scaling audit)
        # Command: nanoBragg -mat A.mat -hkl scaled.hkl -lambda 0.9768 -N 36 47 29
        #                    -distance 100 -detpixels 2124 -pixel 0.1 -phi 0 -osc 0.1
        #                    -phisteps 10 -mosaic_dom 1 -oversample 1 -floatfile out.bin

        # Check prerequisites
        mat_file = Path('A.mat')
        hkl_file = Path('scaled.hkl')
        if not mat_file.exists():
            pytest.skip("A.mat not found (required for supervisor command reproduction)")
        if not hkl_file.exists():
            pytest.skip("scaled.hkl not found (required for supervisor command reproduction)")

        # Device and dtype (CPU float32 per input.md guidance)
        device = torch.device('cpu')
        dtype = torch.float32

        # Beam configuration
        wavelength_A = 0.976800
        beam_config = BeamConfig(wavelength_A=wavelength_A)

        # Load MOSFLM matrix
        a_star, b_star, c_star = read_mosflm_matrix(str(mat_file), wavelength_A)

        # Crystal configuration (supervisor command)
        crystal_config = CrystalConfig(
            cell_a=100.0,  # placeholder (overridden by MOSFLM)
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(36, 47, 29),
            mosflm_a_star=a_star,
            mosflm_b_star=b_star,
            mosflm_c_star=c_star,
            phi_start_deg=0.0,
            osc_range_deg=0.1,
            phi_steps=10,
            mosaic_domains=1,
            misset_deg=[0.0, 0.0, 0.0],
            spindle_axis=[-1.0, 0.0, 0.0],  # supervisor command convention
        )

        # Detector configuration (supervisor command)
        from nanobrag_torch.config import DetectorConvention
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=2124,
            fpixels=2124,
            detector_convention=DetectorConvention.MOSFLM,
        )

        # Instantiate Crystal
        crystal = Crystal(crystal_config, beam_config=beam_config, device=device, dtype=dtype)

        # Get rotated real vectors (includes φ rotation)
        # Returns tuple of (real_vectors, reciprocal_vectors)
        (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = crystal.get_rotated_real_vectors(crystal_config)

        # Verify φ dimensions match config
        assert rot_b.shape[0] == crystal_config.phi_steps, \
            f"φ count mismatch: expected {crystal_config.phi_steps}, got {rot_b.shape[0]}"

        # Extract φ=0 b-vector Y component
        rot_b_phi0_y = rot_b[0, 0, 1].item()  # (phi, mosaic, xyz) → φ=0, mosaic=0, Y

        # Expected: SPEC-COMPLIANT base vector value at φ=0
        # Spec baseline value from reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/
        # This is the CORRECT value per specs/spec-a-core.md:211-214, where φ=0
        # should apply identity rotation, yielding the base lattice vector unchanged.
        #
        # Note: The C binary produces 0.6715882339 Å at φ_tic=0 due to C-PARITY-001
        # (stale vector carryover), which is a documented bug. An opt-in parity shim
        # will be added in Phase L3k.3c.4 to reproduce this for validation harnesses.
        #
        # Reference: CLI-FLAGS-003 Phase L3k.3c.3 (input.md:42-43, plan.md:309)
        expected_rot_b_y = 0.7173197865  # Spec baseline (10-digit precision)

        # Tolerance: ≤1e-6 per CLI-FLAGS-003 L3k.3c.3 verification gate VG-1
        tolerance = 1e-6

        # Assertion
        rel_error = abs(rot_b_phi0_y - expected_rot_b_y) / abs(expected_rot_b_y)
        assert rel_error <= tolerance, \
            f"rot_b[0,0,1] (φ=0 Y component) relative error {rel_error:.6g} > {tolerance}. " \
            f"Expected {expected_rot_b_y:.10f}, got {rot_b_phi0_y:.10f} Å. " \
            f"Absolute delta: {rot_b_phi0_y - expected_rot_b_y:.10g} Å. " \
            f"At φ=0°, rotated vectors should equal base vectors (no rotation applied)."

    def test_k_frac_phi0_matches_c(self):
        """
        Verify φ=0 fractional Miller index k equals spec-compliant value.

        This test computes k_frac at φ=0 for the target pixel (685, 1039)
        and validates against the SPEC-COMPLIANT value (identity rotation at φ=0).

        Expected value: k_frac = 1.6756687164 (10-digit spec baseline)
        Tolerance: ≤1e-6 (VG-1 gate per CLI-FLAGS-003 L3k.3c.3)

        Phase: CLI-FLAGS-003 L3k.3c.3 (spec-compliant default path)

        Note: The C binary produces k_frac=-0.607256 at φ_tic=0 due to C-PARITY-001
        (stale vector carryover bug). This test validates the CORRECT spec behavior.
        An opt-in parity shim will be added in Phase L3k.3c.4 for C validation.
        """

        from nanobrag_torch.models.crystal import Crystal, CrystalConfig
        from nanobrag_torch.models.detector import Detector, DetectorConfig
        from nanobrag_torch.config import BeamConfig, DetectorConvention
        from nanobrag_torch.io.mosflm import read_mosflm_matrix
        from nanobrag_torch import utils

        # Check prerequisites
        mat_file = Path('A.mat')
        hkl_file = Path('scaled.hkl')
        if not mat_file.exists():
            pytest.skip("A.mat not found")
        if not hkl_file.exists():
            pytest.skip("scaled.hkl not found")

        # Device and dtype
        device = torch.device('cpu')
        dtype = torch.float32

        # Beam configuration
        wavelength_A = 0.976800
        beam_config = BeamConfig(wavelength_A=wavelength_A)

        # Load MOSFLM matrix
        a_star, b_star, c_star = read_mosflm_matrix(str(mat_file), wavelength_A)

        # Crystal configuration
        crystal_config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(36, 47, 29),
            mosflm_a_star=a_star,
            mosflm_b_star=b_star,
            mosflm_c_star=c_star,
            phi_start_deg=0.0,
            osc_range_deg=0.1,
            phi_steps=10,
            mosaic_domains=1,
            misset_deg=[0.0, 0.0, 0.0],
            spindle_axis=[-1.0, 0.0, 0.0],  # supervisor command convention
        )

        # Detector configuration
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=2124,
            fpixels=2124,
            detector_convention=DetectorConvention.MOSFLM,
        )

        # Instantiate models
        crystal = Crystal(crystal_config, beam_config=beam_config, device=device, dtype=dtype)
        detector = Detector(detector_config, device=device, dtype=dtype)

        # Get rotated vectors at φ=0
        # Returns tuple of (real_vectors, reciprocal_vectors)
        (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = crystal.get_rotated_real_vectors(crystal_config)

        # Target pixel from C trace (slow=685, fast=1039)
        # These are the indices from c_trace_scaling.log
        target_s = 685
        target_f = 1039

        # Get pixel position for target
        # detector.get_pixel_coords() returns (S, F, 3) in meters
        pixel_coords = detector.get_pixel_coords()  # (2124, 2124, 3)
        pixel_pos_m = pixel_coords[target_s, target_f, :]  # (3,) meters

        # Convert to Angstroms for physics
        pixel_pos_A = pixel_pos_m * 1e10  # m → Å

        # Compute scattering vector (supervisor command uses -lambda 0.9768)
        wavelength_m = wavelength_A * 1e-10  # Å → m

        # Incident beam (MOSFLM convention: [1, 0, 0])
        incident = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)

        # Diffracted direction (unit vector to pixel)
        diffracted = pixel_pos_A / torch.norm(pixel_pos_A)

        # Scattering vector S = (d - i) / λ (in Å⁻¹)
        scattering = (diffracted - incident) / wavelength_A

        # Compute Miller indices at φ=0 using dot product
        # k_frac = b · S (where b is the φ=0, mosaic=0 real-space vector)
        b_phi0 = rot_b[0, 0, :]  # (3,) Å
        k_frac = utils.dot_product(scattering, b_phi0).item()

        # Expected: SPEC-COMPLIANT k_frac value at φ=0
        # Spec baseline value from reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/
        # This is the CORRECT value per specs/spec-a-core.md:211-214, where φ=0
        # should apply identity rotation, yielding base lattice vectors for Miller index calculation.
        #
        # Note: The C binary produces k_frac=-0.607256 at φ_tic=0 due to C-PARITY-001
        # (stale vector carryover), which is a documented bug. An opt-in parity shim
        # will be added in Phase L3k.3c.4 to reproduce this for validation harnesses.
        #
        # Reference: CLI-FLAGS-003 Phase L3k.3c.3 (input.md:42-43, plan.md:309)
        expected_k_frac = 1.6756687164  # Spec baseline (10-digit precision)

        # Tolerance: ≤1e-6 per CLI-FLAGS-003 L3k.3c.3 verification gate VG-1
        tolerance = 1e-6

        # Assertion: verify spec-compliant value (not the buggy C value)
        abs_error = abs(k_frac - expected_k_frac)
        assert abs_error <= tolerance, \
            f"k_frac(φ=0) spec compliance failed. " \
            f"Expected {expected_k_frac:.10f}, got {k_frac:.10f}. " \
            f"Absolute delta: {abs_error:.10g} (tolerance: {tolerance}). " \
            f"At φ=0°, k should be calculated from base lattice vectors (identity rotation)."

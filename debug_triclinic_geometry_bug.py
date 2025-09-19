#!/usr/bin/env python
"""
Debug script to investigate the triclinic crystal 158-pixel offset bug.

This script performs a comprehensive analysis of triclinic crystal geometry
calculations following the debugging workflow from CLAUDE.md Rules #12 and #13.

The goal is to identify where the triclinic calculation diverges from expected
values and why peaks appear at (196, 254) instead of near beam center.
"""

import os
import torch
import numpy as np
import math

# Set up environment
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# Import PyTorch implementation
from nanobrag_torch.config import CrystalConfig, BeamConfig, DetectorConfig, DetectorConvention, DetectorPivot
from nanobrag_torch.models import Crystal, Detector
from nanobrag_torch.simulator import Simulator


def check_rule_13_compliance(crystal, name):
    """
    Check if Rule #13 reciprocal vector recalculation for self-consistency is implemented correctly.

    According to CLAUDE.md Rule #13, the C-code performs a circular recalculation:
    1. Build initial reciprocal vectors using default orientation convention
    2. Calculate real vectors from reciprocal: a = (b* × c*) × V
    3. Recalculate reciprocal vectors from real: a* = (b × c) / V_actual
    4. Use actual volume: V_actual = a · (b × c) instead of formula volume

    This ensures perfect metric duality (a·a* = 1 exactly).
    """
    print(f"\n{'='*60}")
    print(f"RULE #13 COMPLIANCE CHECK: {name}")
    print(f"{'='*60}")

    # Get the computed vectors
    a, b, c = crystal.a, crystal.b, crystal.c
    a_star, b_star, c_star = crystal.a_star, crystal.b_star, crystal.c_star
    V = crystal.V

    print(f"Volume from crystal object: {V:.6f} Å³")

    # Step 4: Check actual volume calculation
    V_actual = torch.dot(a, torch.cross(b, c, dim=0))
    print(f"V_actual = a · (b × c): {V_actual:.6f} Å³")
    print(f"Volume difference: {abs(V - V_actual):.10f} Å³")

    # Step 3: Check if reciprocal vectors were recalculated from real
    b_cross_c = torch.cross(b, c, dim=0)
    c_cross_a = torch.cross(c, a, dim=0)
    a_cross_b = torch.cross(a, b, dim=0)

    expected_a_star = b_cross_c / V_actual
    expected_b_star = c_cross_a / V_actual
    expected_c_star = a_cross_b / V_actual

    a_star_diff = torch.norm(a_star - expected_a_star)
    b_star_diff = torch.norm(b_star - expected_b_star)
    c_star_diff = torch.norm(c_star - expected_c_star)

    print(f"Reciprocal vector recalculation check:")
    print(f"  |a* - expected_a*|: {a_star_diff:.10f}")
    print(f"  |b* - expected_b*|: {b_star_diff:.10f}")
    print(f"  |c* - expected_c*|: {c_star_diff:.10f}")

    # Metric duality check: a·a* = 1, etc.
    aa_star = torch.dot(a, a_star)
    bb_star = torch.dot(b, b_star)
    cc_star = torch.dot(c, c_star)

    ab_star = torch.dot(a, b_star)
    ac_star = torch.dot(a, c_star)
    ba_star = torch.dot(b, a_star)
    bc_star = torch.dot(b, c_star)
    ca_star = torch.dot(c, a_star)
    cb_star = torch.dot(c, b_star)

    print(f"Metric duality check (should be identity matrix):")
    print(f"  a·a* = {aa_star:.10f} (should be 1.0)")
    print(f"  b·b* = {bb_star:.10f} (should be 1.0)")
    print(f"  c·c* = {cc_star:.10f} (should be 1.0)")
    print(f"  a·b* = {ab_star:.10f} (should be 0.0)")
    print(f"  a·c* = {ac_star:.10f} (should be 0.0)")
    print(f"  b·a* = {ba_star:.10f} (should be 0.0)")
    print(f"  b·c* = {bc_star:.10f} (should be 0.0)")
    print(f"  c·a* = {ca_star:.10f} (should be 0.0)")
    print(f"  c·b* = {cb_star:.10f} (should be 0.0)")

    # Check if implementation follows Rule #13
    rule_13_compliant = (
        a_star_diff < 1e-12 and
        b_star_diff < 1e-12 and
        c_star_diff < 1e-12 and
        abs(aa_star - 1.0) < 1e-12 and
        abs(bb_star - 1.0) < 1e-12 and
        abs(cc_star - 1.0) < 1e-12
    )

    print(f"Rule #13 compliance: {'PASS' if rule_13_compliant else 'FAIL'}")

    return rule_13_compliant


def compare_crystallographic_formulas(crystal, name, cell_params):
    """
    Compare computed vectors against standard crystallographic formulas.
    """
    print(f"\n{'='*60}")
    print(f"CRYSTALLOGRAPHIC FORMULA VALIDATION: {name}")
    print(f"{'='*60}")

    a_len, b_len, c_len, alpha_deg, beta_deg, gamma_deg = cell_params

    # Convert to radians
    alpha_rad = math.radians(alpha_deg)
    beta_rad = math.radians(beta_deg)
    gamma_rad = math.radians(gamma_deg)

    # Standard crystallographic formulas for triclinic system
    cos_alpha = math.cos(alpha_rad)
    cos_beta = math.cos(beta_rad)
    cos_gamma = math.cos(gamma_rad)
    sin_alpha = math.sin(alpha_rad)
    sin_beta = math.sin(beta_rad)
    sin_gamma = math.sin(gamma_rad)

    # Volume formula (same as in C code)
    aavg = (alpha_rad + beta_rad + gamma_rad) / 2.0
    skew = (
        math.sin(aavg) *
        math.sin(aavg - alpha_rad) *
        math.sin(aavg - beta_rad) *
        math.sin(aavg - gamma_rad)
    )
    skew = abs(skew)  # Handle negative values
    skew = max(skew, 1e-12)  # Handle degenerate cases
    V_formula = 2.0 * a_len * b_len * c_len * math.sqrt(skew)

    print(f"Volume from formula: {V_formula:.6f} Å³")
    print(f"Volume from crystal: {crystal.V:.6f} Å³")
    print(f"Volume difference: {abs(V_formula - crystal.V):.6f} Å³")

    # Reciprocal lattice parameters
    V_star = 1.0 / V_formula
    a_star_len = b_len * c_len * sin_alpha * V_star
    b_star_len = c_len * a_len * sin_beta * V_star
    c_star_len = a_len * b_len * sin_gamma * V_star

    cos_alpha_star = (cos_beta * cos_gamma - cos_alpha) / (sin_beta * sin_gamma)
    cos_beta_star = (cos_gamma * cos_alpha - cos_beta) / (sin_gamma * sin_alpha)
    cos_gamma_star = (cos_alpha * cos_beta - cos_gamma) / (sin_alpha * sin_beta)

    print(f"\nReciprocal lattice parameters:")
    print(f"  Expected a* length: {a_star_len:.6f} Å⁻¹")
    print(f"  Computed a* length: {torch.norm(crystal.a_star):.6f} Å⁻¹")
    print(f"  Expected b* length: {b_star_len:.6f} Å⁻¹")
    print(f"  Computed b* length: {torch.norm(crystal.b_star):.6f} Å⁻¹")
    print(f"  Expected c* length: {c_star_len:.6f} Å⁻¹")
    print(f"  Computed c* length: {torch.norm(crystal.c_star):.6f} Å⁻¹")

    print(f"\nReciprocal angles:")
    print(f"  Expected cos(α*): {cos_alpha_star:.6f}")
    print(f"  Expected cos(β*): {cos_beta_star:.6f}")
    print(f"  Expected cos(γ*): {cos_gamma_star:.6f}")

    # Check default orientation convention
    print(f"\nDefault orientation convention check:")
    print(f"  a* should be along X: {crystal.a_star.numpy()}")
    print(f"  a*[1] and a*[2] should be 0: {crystal.a_star[1]:.10f}, {crystal.a_star[2]:.10f}")
    print(f"  b* should be in XY plane: {crystal.b_star.numpy()}")
    print(f"  b*[2] should be 0: {crystal.b_star[2]:.10f}")
    print(f"  c* fills 3D space: {crystal.c_star.numpy()}")


def analyze_miller_index_calculation(crystal, detector, beam_config, name):
    """
    Analyze Miller index calculation for specific pixels to understand the 158-pixel offset.
    """
    print(f"\n{'='*60}")
    print(f"MILLER INDEX ANALYSIS: {name}")
    print(f"{'='*60}")

    # Get pixel coordinates
    pixel_coords_meters = detector.get_pixel_coords()
    pixel_coords_angstroms = pixel_coords_meters * 1e10

    # Test several key pixels
    test_pixels = [
        (128, 128, "Center"),
        (100, 128, "Cubic peak observed location"),
        (196, 254, "Triclinic peak observed location"),
        (0, 0, "Corner"),
        (255, 255, "Opposite corner")
    ]

    # Incident beam (MOSFLM: along +X)
    incident_beam_unit = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)

    for slow, fast, description in test_pixels:
        if slow >= detector.spixels or fast >= detector.fpixels:
            continue

        print(f"\nPixel ({slow}, {fast}) - {description}:")

        # Get pixel position
        pixel_pos = pixel_coords_angstroms[slow, fast]

        # Calculate diffracted beam unit vector
        pixel_distance = torch.norm(pixel_pos)
        diffracted_unit = pixel_pos / pixel_distance

        # Calculate scattering vector
        scattering_vector = (diffracted_unit - incident_beam_unit) / beam_config.wavelength_A

        print(f"  Scattering vector: {scattering_vector.numpy()}")
        print(f"  |S| = {torch.norm(scattering_vector):.6f} Å⁻¹")

        # Calculate Miller indices using real-space vectors
        h = torch.dot(scattering_vector, crystal.a)
        k = torch.dot(scattering_vector, crystal.b)
        l = torch.dot(scattering_vector, crystal.c)

        print(f"  Miller indices: h={h:.4f}, k={k:.4f}, l={l:.4f}")

        # Round to nearest integer
        h0 = torch.round(h)
        k0 = torch.round(k)
        l0 = torch.round(l)
        print(f"  Nearest integers: ({h0:.0f}, {k0:.0f}, {l0:.0f})")

        # Calculate fractional parts
        h_frac = h - h0
        k_frac = k - k0
        l_frac = l - l0
        print(f"  Fractional parts: ({h_frac:.4f}, {k_frac:.4f}, {l_frac:.4f})")


def run_simulation_analysis(crystal, detector, crystal_config, beam_config, name):
    """
    Run simulation and analyze the peak positions.
    """
    print(f"\n{'='*60}")
    print(f"SIMULATION ANALYSIS: {name}")
    print(f"{'='*60}")

    simulator = Simulator(crystal, detector, crystal_config, beam_config)
    image = simulator.run()

    # Find brightest spot
    max_val = torch.max(image)
    max_idx = torch.argmax(image.view(-1))
    max_slow = max_idx // image.shape[1]
    max_fast = max_idx % image.shape[1]

    print(f"Maximum intensity: {max_val:.6f}")
    print(f"Peak position: ({max_slow}, {max_fast})")

    # Distance from beam center
    beam_center_slow = detector.spixels // 2
    beam_center_fast = detector.fpixels // 2
    distance_from_center = math.sqrt(
        (max_slow - beam_center_slow)**2 + (max_fast - beam_center_fast)**2
    )
    print(f"Distance from beam center: {distance_from_center:.1f} pixels")

    # Look for other significant peaks
    threshold = 0.1 * max_val
    peak_mask = image > threshold
    peak_count = torch.sum(peak_mask)
    print(f"Pixels above {threshold:.4f}: {peak_count}")

    return max_slow, max_fast, max_val


def main():
    """
    Main debugging function to investigate the triclinic crystal geometry bug.
    """
    print("TRICLINIC CRYSTAL GEOMETRY BUG INVESTIGATION")
    print("=" * 60)
    print("Goal: Identify why triclinic peaks appear at (196, 254) instead of beam center")
    print("Following CLAUDE.md debugging workflow and Rules #12, #13")

    # Create test configurations exactly matching the failing test
    triclinic_config = CrystalConfig(
        cell_a=70.0,
        cell_b=80.0,
        cell_c=90.0,
        cell_alpha=85.0,
        cell_beta=95.0,
        cell_gamma=105.0,
        N_cells=(5, 5, 5),
        default_F=100.0
    )

    cubic_config = CrystalConfig(
        cell_a=80.0,
        cell_b=80.0,
        cell_c=80.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0
    )

    detector_config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
        distance_mm=150.0,
        pixel_size_mm=0.1,
        spixels=256,
        fpixels=256
    )

    beam_config = BeamConfig(
        wavelength_A=1.5
    )

    # Create crystal objects
    triclinic_crystal = Crystal(triclinic_config, beam_config)
    cubic_crystal = Crystal(cubic_config, beam_config)
    detector = Detector(detector_config)

    # 1. Check Rule #13 compliance for both crystals
    triclinic_rule13_ok = check_rule_13_compliance(triclinic_crystal, "TRICLINIC")
    cubic_rule13_ok = check_rule_13_compliance(cubic_crystal, "CUBIC")

    # 2. Validate against crystallographic formulas
    compare_crystallographic_formulas(
        triclinic_crystal, "TRICLINIC",
        (70.0, 80.0, 90.0, 85.0, 95.0, 105.0)
    )
    compare_crystallographic_formulas(
        cubic_crystal, "CUBIC",
        (80.0, 80.0, 80.0, 90.0, 90.0, 90.0)
    )

    # 3. Analyze Miller index calculations
    analyze_miller_index_calculation(triclinic_crystal, detector, beam_config, "TRICLINIC")
    analyze_miller_index_calculation(cubic_crystal, detector, beam_config, "CUBIC")

    # 4. Run simulations and compare results
    triclinic_slow, triclinic_fast, triclinic_max = run_simulation_analysis(
        triclinic_crystal, detector, triclinic_config, beam_config, "TRICLINIC"
    )
    cubic_slow, cubic_fast, cubic_max = run_simulation_analysis(
        cubic_crystal, detector, cubic_config, beam_config, "CUBIC"
    )

    # 5. Summary analysis
    print(f"\n{'='*60}")
    print("SUMMARY ANALYSIS")
    print(f"{'='*60}")

    position_diff = math.sqrt(
        (triclinic_slow - cubic_slow)**2 + (triclinic_fast - cubic_fast)**2
    )

    print(f"Peak position comparison:")
    print(f"  Cubic peak: ({cubic_slow}, {cubic_fast})")
    print(f"  Triclinic peak: ({triclinic_slow}, {triclinic_fast})")
    print(f"  Position difference: {position_diff:.1f} pixels")
    print(f"  Expected difference: < 5 pixels")
    print(f"  Status: {'PASS' if position_diff < 5.0 else 'FAIL'}")

    print(f"\nRule #13 compliance:")
    print(f"  Cubic: {'PASS' if cubic_rule13_ok else 'FAIL'}")
    print(f"  Triclinic: {'PASS' if triclinic_rule13_ok else 'FAIL'}")

    print(f"\nDiagnostic recommendations:")
    if position_diff >= 5.0:
        print("  ❌ Large position offset detected - triclinic geometry is incorrect")
        if not triclinic_rule13_ok:
            print("  ❌ Rule #13 violation - reciprocal vector recalculation failed")
        print("  🔍 Recommended next steps:")
        print("     1. Check misset rotation application in _apply_static_orientation")
        print("     2. Verify default orientation convention for triclinic cells")
        print("     3. Debug Miller index calculation with parallel trace")
    else:
        print("  ✅ Position offset is acceptable")

    if not (triclinic_rule13_ok and cubic_rule13_ok):
        print("  ❌ Metric duality violation detected")
        print("  🔍 Check compute_cell_tensors implementation")


if __name__ == "__main__":
    main()
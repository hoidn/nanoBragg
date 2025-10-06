#!/usr/bin/env python3
"""
Phase K3f2: PyTorch base lattice trace harness
Emits TRACE_PY_BASE lines matching C baseline for comparison.

CRITICAL: Uses detector.get_pixel_coords() directly as the sample→pixel vector.
Do NOT subtract pix0_vector because coordinates already include that origin offset.
"""

import os
import sys
import torch
import argparse
from pathlib import Path

# Ensure editable install is used
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "src"))

os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

from nanobrag_torch.config import DetectorConfig, CrystalConfig, BeamConfig
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.io.mosflm import read_mosflm_matrix


def main():
    parser = argparse.ArgumentParser(description="K3f2: PyTorch base lattice trace")
    parser.add_argument('--out', type=str, default='trace_py.log', help='Output trace file')
    args = parser.parse_args()

    # Configuration from supervisor command in input.md
    dtype = torch.float64  # Use float64 for trace precision
    device = torch.device('cpu')  # Evidence on CPU for determinism

    print("TRACE_PY_BASE: ========== Phase K3f2 PyTorch Base Lattice Trace ==========", file=sys.stderr)
    print(f"TRACE_PY_BASE: dtype={dtype}, device={device}", file=sys.stderr)

    # Parse MOSFLM matrix file
    wavelength_A = 0.9768  # From supervisor command
    a_star_raw, b_star_raw, c_star_raw = read_mosflm_matrix('A.mat', wavelength_A)
    print(f"TRACE_PY_BASE: Loaded MOSFLM matrix from A.mat", file=sys.stderr)
    print(f"TRACE_PY_BASE:   wavelength = {wavelength_A} Å", file=sys.stderr)

    # Build CrystalConfig with MOSFLM orientation
    # Note: Cell parameters come from MOSFLM matrix dimensions (derived from reciprocal vectors)
    # but for this trace we only need the orientation vectors
    crystal_config = CrystalConfig(
        # Placeholder cell (will be overridden by MOSFLM vectors)
        cell_a=1.0,
        cell_b=1.0,
        cell_c=1.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        # From supervisor command
        N_cells=(36, 47, 29),
        phi_start_deg=0.0,
        osc_range_deg=0.1,
        phi_steps=10,
        spindle_axis=(-1.0, 0.0, 0.0),
        mosaic_spread_deg=0.0,
        mosaic_domains=1,
        default_F=0.0,  # Using HKL file
        # MOSFLM orientation (numpy arrays → tuple for config)
        mosflm_a_star=tuple(a_star_raw),
        mosflm_b_star=tuple(b_star_raw),
        mosflm_c_star=tuple(c_star_raw),
    )

    # Build BeamConfig
    beam_config = BeamConfig(
        wavelength_A=0.9768,
        flux=1e18,
        exposure=1.0,
        beamsize_mm=1.0,
        polarization_factor=0.0,  # Default from K3b
    )

    # Build DetectorConfig with custom vectors (forces SAMPLE pivot)
    detector_config = DetectorConfig(
        distance_mm=231.274660,
        pixel_size_mm=0.172,
        spixels=2527,
        fpixels=2463,
        beam_center_f=217.742295,  # mm (Xbeam)
        beam_center_s=213.907080,  # mm (Ybeam)
        detector_rotx_deg=0.0,
        detector_roty_deg=0.0,
        detector_rotz_deg=0.0,
        detector_twotheta_deg=0.0,
        # Custom detector vectors (forces SAMPLE pivot per H6f)
        custom_fdet_vector=(0.999982, -0.005998, -0.000118),
        custom_sdet_vector=(-0.005998, -0.999970, -0.004913),
        custom_odet_vector=(-0.000088, 0.004914, -0.999988),
        # Custom beam vector
        custom_beam_vector=(0.00051387949, 0.0, -0.99999986),
        # Pix0 override (though C ignores this when custom vectors present)
        pix0_override_m=torch.tensor([-0.216336293, 0.215205512, -0.230200866], dtype=dtype, device=device),
    )

    # Instantiate models
    print("TRACE_PY_BASE: Creating Detector...", file=sys.stderr)
    detector = Detector(detector_config, dtype=dtype, device=device)

    print("TRACE_PY_BASE: Creating Crystal...", file=sys.stderr)
    crystal = Crystal(crystal_config, dtype=dtype, device=device)

    # === Emit base lattice traces ===
    print("TRACE_PY_BASE:", file=sys.stderr)
    print("TRACE_PY_BASE: ========== MOSFLM Reciprocal Vectors (λ-scaled) ==========", file=sys.stderr)

    # Access reciprocal vectors from crystal (property recalculates from config)
    a_star, b_star, c_star = crystal.a_star, crystal.b_star, crystal.c_star

    print(f"TRACE_PY_BASE:   a_star = [{a_star[0].item():.10g}, {a_star[1].item():.10g}, {a_star[2].item():.10g}] |a_star| = {torch.norm(a_star).item():.10g}", file=sys.stderr)
    print(f"TRACE_PY_BASE:   b_star = [{b_star[0].item():.10g}, {b_star[1].item():.10g}, {b_star[2].item():.10g}] |b_star| = {torch.norm(b_star).item():.10g}", file=sys.stderr)
    print(f"TRACE_PY_BASE:   c_star = [{c_star[0].item():.10g}, {c_star[1].item():.10g}, {c_star[2].item():.10g}] |c_star| = {torch.norm(c_star).item():.10g}", file=sys.stderr)

    print("TRACE_PY_BASE:", file=sys.stderr)
    print("TRACE_PY_BASE: ========== Real-Space Vectors (meters) ==========", file=sys.stderr)

    # Access real vectors (base, pre-φ rotation)
    a, b, c = crystal.a, crystal.b, crystal.c

    print(f"TRACE_PY_BASE:   a = [{a[0].item():.10g}, {a[1].item():.10g}, {a[2].item():.10g}] |a| = {torch.norm(a).item():.10g} meters", file=sys.stderr)
    print(f"TRACE_PY_BASE:   b = [{b[0].item():.10g}, {b[1].item():.10g}, {b[2].item():.10g}] |b| = {torch.norm(b).item():.10g} meters", file=sys.stderr)
    print(f"TRACE_PY_BASE:   c = [{c[0].item():.10g}, {c[1].item():.10g}, {c[2].item():.10g}] |c| = {torch.norm(c).item():.10g} meters", file=sys.stderr)

    # Cell volumes
    V_actual = torch.dot(a, torch.linalg.cross(b, c))
    print(f"TRACE_PY_BASE:   V_cell = {V_actual.item():.10g} m³ = {(V_actual * 1e30).item():.10g} Å³", file=sys.stderr)
    print(f"TRACE_PY_BASE:   V_star = {(1.0 / V_actual).item():.10g} m⁻³", file=sys.stderr)

    print("TRACE_PY_BASE:", file=sys.stderr)
    print("TRACE_PY_BASE: ========== Detector Geometry ==========", file=sys.stderr)
    print(f"TRACE_PY_BASE:   pix0_vector = [{detector.pix0_vector[0].item():.10g}, {detector.pix0_vector[1].item():.10g}, {detector.pix0_vector[2].item():.10g}] meters", file=sys.stderr)
    print(f"TRACE_PY_BASE:   beam_vector = [{detector.beam_vector[0].item():.10g}, {detector.beam_vector[1].item():.10g}, {detector.beam_vector[2].item():.10g}]", file=sys.stderr)
    print(f"TRACE_PY_BASE:   Fdet = [{detector.fdet_vec[0].item():.10g}, {detector.fdet_vec[1].item():.10g}, {detector.fdet_vec[2].item():.10g}]", file=sys.stderr)
    print(f"TRACE_PY_BASE:   Sdet = [{detector.sdet_vec[0].item():.10g}, {detector.sdet_vec[1].item():.10g}, {detector.sdet_vec[2].item():.10g}]", file=sys.stderr)
    print(f"TRACE_PY_BASE:   Odet = [{detector.odet_vec[0].item():.10g}, {detector.odet_vec[1].item():.10g}, {detector.odet_vec[2].item():.10g}]", file=sys.stderr)

    print("TRACE_PY_BASE:", file=sys.stderr)
    print("TRACE_PY_BASE: ========== φ=0° Scattering Example (pixel 1039,685) ==========", file=sys.stderr)

    # Get pixel coordinates (sample→pixel vector in meters)
    # CRITICAL: This already includes the pix0 origin; do NOT subtract pix0_vector again!
    pixel_coords = detector.get_pixel_coords()  # Shape: (S, F, 3)

    # Example pixel from Phase K3e: (1039, 685)
    s_idx, f_idx = 1039, 685
    pixel_pos_m = pixel_coords[s_idx, f_idx, :]  # This IS the sample→pixel vector

    print(f"TRACE_PY_BASE:   pixel_coords[{s_idx},{f_idx}] = [{pixel_pos_m[0].item():.10g}, {pixel_pos_m[1].item():.10g}, {pixel_pos_m[2].item():.10g}] meters", file=sys.stderr)

    # Scattering vector (d - i) / λ in Å⁻¹
    d = pixel_pos_m / torch.norm(pixel_pos_m)  # Diffracted direction (unit)
    i = -detector.beam_vector  # Incident direction (opposite of beam)
    wavelength_m = beam_config.wavelength_A * 1e-10
    S = (d - i) / wavelength_m  # m⁻¹
    S_Ainv = S * 1e-10  # Convert to Å⁻¹

    print(f"TRACE_PY_BASE:   diffracted (d) = [{d[0].item():.10g}, {d[1].item():.10g}, {d[2].item():.10g}]", file=sys.stderr)
    print(f"TRACE_PY_BASE:   incident (i) = [{i[0].item():.10g}, {i[1].item():.10g}, {i[2].item():.10g}]", file=sys.stderr)
    print(f"TRACE_PY_BASE:   S (Å⁻¹) = [{S_Ainv[0].item():.10g}, {S_Ainv[1].item():.10g}, {S_Ainv[2].item():.10g}]", file=sys.stderr)

    # Miller indices (fractional) at φ=0° using base real vectors
    h_frac = torch.dot(S_Ainv, a * 1e10)  # S·a (convert a to Å)
    k_frac = torch.dot(S_Ainv, b * 1e10)  # S·b
    l_frac = torch.dot(S_Ainv, c * 1e10)  # S·c

    print(f"TRACE_PY_BASE:   h_frac = {h_frac.item():.10g}", file=sys.stderr)
    print(f"TRACE_PY_BASE:   k_frac = {k_frac.item():.10g}", file=sys.stderr)
    print(f"TRACE_PY_BASE:   l_frac = {l_frac.item():.10g}", file=sys.stderr)

    print(f"TRACE_PY_BASE:", file=sys.stderr)
    print(f"TRACE_PY_BASE: K3f2 complete. Trace written to stderr.", file=sys.stderr)
    print(f"TRACE_PY_BASE: ========================================================", file=sys.stderr)


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""
Utilities for C reference verification.

This module provides utilities for generating files and commands needed
to run parallel verification against the nanoBragg.c reference implementation.
"""

import os
from pathlib import Path
from typing import List

from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig


def generate_identity_matrix(output_path="identity.mat"):
    """Generate MOSFLM-style identity orientation matrix.

    Creates a 3x3 identity matrix file compatible with nanoBragg.c -matrix option.
    This represents no crystal rotation relative to the default orientation.

    The MOSFLM format stores the reciprocal lattice vectors as rows:
    a_star_x a_star_y a_star_z
    b_star_x b_star_y b_star_z
    c_star_x c_star_y c_star_z

    For an identity matrix, this is simply:
    1 0 0
    0 1 0
    0 0 1

    Args:
        output_path: Path where to write the matrix file

    Reference: MOSFLM matrix format in golden_suite_generator/README.md
    """
    output_path = Path(output_path)

    with open(output_path, "w") as f:
        f.write("1.0 0.0 0.0\n")
        f.write("0.0 1.0 0.0\n")
        f.write("0.0 0.0 1.0\n")

    print(f"Generated identity matrix: {output_path}")
    return output_path


def build_nanobragg_command(
    detector_config: DetectorConfig,
    crystal_config: CrystalConfig,
    beam_config: BeamConfig,
    matrix_file: str = "identity.mat",
    default_F: float = 100.0,
    executable_path: str = "golden_suite_generator/nanoBragg",
) -> List[str]:
    """Build nanoBragg.c command with equivalent parameters.

    Maps PyTorch configuration objects to C command-line arguments using
    the -default_F approach to avoid HKL file complexity.

    Args:
        detector_config: DetectorConfig instance
        crystal_config: CrystalConfig instance
        beam_config: BeamConfig instance
        matrix_file: Path to orientation matrix file
        default_F: Constant structure factor value
        executable_path: Path to nanoBragg executable

    Returns:
        List[str]: Command arguments for subprocess.run()

    Reference: Parameter mapping in docs/architecture/c_parameter_dictionary.md
    """
    
    # Debug logging for incoming detector config
    print(f"\n   [build_nanobragg_command] Received detector_config:")
    print(f"      - beam_center_s: {detector_config.beam_center_s}")
    print(f"      - beam_center_f: {detector_config.beam_center_f}")
    print(f"      - detector_twotheta_deg: {detector_config.detector_twotheta_deg}")

    # Start with executable
    cmd = [executable_path]

    # Default structure factor (eliminates need for HKL file)
    cmd.extend(["-default_F", str(default_F)])

    # Beam parameters
    cmd.extend(["-lambda", str(beam_config.wavelength_A)])

    # Detector geometry parameters
    cmd.extend(["-distance", str(detector_config.distance_mm)])
    cmd.extend(["-pixel", str(detector_config.pixel_size_mm)])

    # Use detpixels to specify detector size in pixels (not mm)
    # This matches the PyTorch configuration directly
    cmd.extend(["-detpixels", str(detector_config.spixels)])

    # Beam center
    # Use -Xbeam and -Ybeam (Xbeam->fast, Ybeam->slow)
    cmd.extend(["-Xbeam", str(detector_config.beam_center_f)])
    cmd.extend(["-Ybeam", str(detector_config.beam_center_s)])

    # Crystal unit cell parameters
    cmd.extend(
        [
            "-cell",
            str(crystal_config.cell_a),
            str(crystal_config.cell_b),
            str(crystal_config.cell_c),
            str(crystal_config.cell_alpha),
            str(crystal_config.cell_beta),
            str(crystal_config.cell_gamma),
        ]
    )

    # Crystal size
    N_cells = crystal_config.N_cells
    cmd.extend(["-N", str(N_cells[0])])  # nanoBragg.c uses cubic crystal size

    # Orientation matrix
    cmd.extend(["-matrix", matrix_file])

    # Detector rotations (only add if non-zero)
    if abs(detector_config.detector_rotx_deg) > 1e-6:
        cmd.extend(["-detector_rotx", str(detector_config.detector_rotx_deg)])
    if abs(detector_config.detector_roty_deg) > 1e-6:
        cmd.extend(["-detector_roty", str(detector_config.detector_roty_deg)])
    if abs(detector_config.detector_rotz_deg) > 1e-6:
        cmd.extend(["-detector_rotz", str(detector_config.detector_rotz_deg)])
    
    # Track if we're using twotheta (important for pivot mode logic)
    has_twotheta = abs(detector_config.detector_twotheta_deg) > 1e-6
    
    if has_twotheta:
        cmd.extend(["-twotheta", str(detector_config.detector_twotheta_deg)])
        
        # Also add explicit twotheta_axis if specified
        # CRITICAL: Do NOT pass -twotheta_axis for MOSFLM default [0,0,-1]
        # as this triggers CUSTOM convention in C code!
        if detector_config.twotheta_axis is not None:
            axis = detector_config.twotheta_axis
            if hasattr(axis, 'tolist'):
                axis = axis.tolist()
            # Only pass twotheta_axis if it's NOT the MOSFLM default
            is_mosflm_default = (abs(axis[0]) < 1e-6 and abs(axis[1]) < 1e-6 and abs(axis[2] + 1.0) < 1e-6)
            if not is_mosflm_default:
                cmd.extend(["-twotheta_axis", str(axis[0]), str(axis[1]), str(axis[2])])

    # Add pivot mode flag
    from nanobrag_torch.config import DetectorPivot
    
    # Use the configured pivot mode directly
    # Testing shows BEAM pivot gives much better Y-component accuracy with twotheta rotations
    if detector_config.detector_pivot == DetectorPivot.BEAM:
        cmd.extend(["-pivot", "beam"])
    elif detector_config.detector_pivot == DetectorPivot.SAMPLE:
        cmd.extend(["-pivot", "sample"])

    return cmd


def format_command_string(cmd_args: List[str]) -> str:
    """Format command arguments as a readable string.

    Args:
        cmd_args: List of command arguments

    Returns:
        String representation suitable for display or shell execution
    """
    return " ".join(cmd_args)


def validate_executable_exists(executable_path: str) -> bool:
    """Check if the nanoBragg executable exists and is executable.

    Args:
        executable_path: Path to check

    Returns:
        True if executable exists and is executable
    """
    path = Path(executable_path)
    return path.exists() and os.access(path, os.X_OK)


def get_default_executable_path() -> str:
    """Get the default path to the nanoBragg executable.

    Returns:
        Default executable path relative to project root
    """
    return "golden_suite_generator/nanoBragg"


if __name__ == "__main__":
    # Example usage for testing
    from nanobrag_torch.config import DetectorConvention, DetectorPivot

    print("C Reference Utils - Example Usage")
    print("=" * 40)

    # Generate identity matrix
    matrix_file = generate_identity_matrix("scripts/identity.mat")

    # Example configurations
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_convention=DetectorConvention.MOSFLM,
    )

    crystal_config = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
    )

    beam_config = BeamConfig(
        wavelength_A=6.2,
        N_source_points=1,
        source_distance_mm=10000.0,
        source_size_mm=0.0,
    )

    # Build command
    cmd = build_nanobragg_command(
        detector_config, crystal_config, beam_config, matrix_file="scripts/identity.mat"
    )

    print(f"\nGenerated command:")
    print(format_command_string(cmd))

    # Check executable
    executable = get_default_executable_path()
    if validate_executable_exists(executable):
        print(f"\n✅ nanoBragg executable found: {executable}")
    else:
        print(f"\n⚠️  nanoBragg executable not found: {executable}")

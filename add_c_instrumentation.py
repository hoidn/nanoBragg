#!/usr/bin/env python3
"""
Add instrumentation to nanoBragg.c for pixel tracing.

This script directly modifies nanoBragg.c to add the necessary tracing
statements for debugging the detector geometry calculation.
"""

import sys
import shutil
from pathlib import Path


def add_globals_section(lines):
    """Add global variables for tracing after includes."""
    for i, line in enumerate(lines):
        if line.strip().startswith("/* rotate a 3-vector in space"):
            # Insert tracing globals before this line
            insert_lines = [
                "",
                "/* Tracing globals for pixel debugging */",
                "static int trace_target_fpixel = -1;",
                "static int trace_target_spixel = -1;",
                "static int tracing_enabled = 0;",
                "",
            ]
            lines[i:i] = insert_lines
            return True
    return False


def add_trace_pixel_argument(lines):
    """Add -trace_pixel argument parsing."""
    for i, line in enumerate(lines):
        if "strstr(argv[i], \"-oversample\")" in line:
            # Insert trace_pixel argument parsing before oversample
            insert_lines = [
                "",
                "        if(strstr(argv[i], \"-trace_pixel\") && (argc > (i+2)))",
                "        {",
                "            ++i;",
                "            trace_target_spixel = atoi(argv[i]);",
                "            ++i;",
                "            trace_target_fpixel = atoi(argv[i]);",
                "            tracing_enabled = 1;",
                "            printf(\"Enabling pixel tracing for spixel=%d fpixel=%d\\n\", ",
                "                   trace_target_spixel, trace_target_fpixel);",
                "            /* Set locale for consistent number formatting */",
                "            setlocale(LC_NUMERIC, \"C\");",
                "            continue;",
                "        }",
                "",
            ]
            lines[i:i] = insert_lines
            return True
    return False


def add_help_text(lines):
    """Add help text for trace_pixel option."""
    for i, line in enumerate(lines):
        if "printf(\"\\t-printout_pixel  \\tpixel values and x,y at a specific pixel\\n\");" in line:
            # Insert after this line
            insert_lines = [
                "        printf(\"\\t-trace_pixel s f\\tgenerate detailed trace for pixel at (s,f)\\n\");",
            ]
            lines[i+1:i+1] = insert_lines
            return True
    return False


def add_detector_trace(lines):
    """Add detector geometry tracing."""
    for i, line in enumerate(lines):
        if "if(detector_pivot == BEAM){" in line:
            # Look for the printf line after this
            j = i + 1
            while j < len(lines) and "printf(\"pivoting detector around direct beam spot" not in lines[j]:
                j += 1
            if j < len(lines):
                # Insert tracing after the printf
                insert_lines = [
                    "",
                    "        if(tracing_enabled) {",
                    "            printf(\"TRACE_C:detector_convention=MOSFLM\\n\");",
                    "            printf(\"TRACE_C:detector_pivot=BEAM\\n\");",
                    "            trace_scalar(\"distance_mm\", distance * 1000.0);",
                    "            trace_scalar(\"beam_center_s\", Xbeam/pixel_size - 0.5);",
                    "            trace_scalar(\"beam_center_f\", Ybeam/pixel_size - 0.5);", 
                    "            trace_scalar(\"pixel_size_mm\", pixel_size * 1000.0);",
                    "            ",
                    "            trace_scalar(\"detector_rotx_deg\", detector_rotx * RTD);",
                    "            trace_scalar(\"detector_roty_deg\", detector_roty * RTD);",
                    "            trace_scalar(\"detector_rotz_deg\", detector_rotz * RTD);",
                    "            trace_scalar(\"detector_twotheta_deg\", detector_twotheta * RTD);",
                    "            ",
                    "            trace_scalar(\"detector_rotx_rad\", detector_rotx);",
                    "            trace_scalar(\"detector_roty_rad\", detector_roty);",
                    "            trace_scalar(\"detector_rotz_rad\", detector_rotz);",
                    "            trace_scalar(\"detector_twotheta_rad\", detector_twotheta);",
                    "            ",
                    "            /* Log initial basis vectors (MOSFLM convention) */",
                    "            trace_vec(\"initial_fdet\", 0.0, 0.0, 1.0);",
                    "            trace_vec(\"initial_sdet\", 0.0, -1.0, 0.0);",
                    "            trace_vec(\"initial_odet\", 1.0, 0.0, 0.0);",
                    "            ",
                    "            /* Log final rotated vectors */",
                    "            trace_vec(\"fdet_vec\", fdet_vector[1], fdet_vector[2], fdet_vector[3]);",
                    "            trace_vec(\"sdet_vec\", sdet_vector[1], sdet_vector[2], sdet_vector[3]);",
                    "            trace_vec(\"odet_vec\", odet_vector[1], odet_vector[2], odet_vector[3]);",
                    "        }",
                    "",
                ]
                lines[j+1:j+1] = insert_lines
                return True
    return False


def add_sample_pivot_trace(lines):
    """Add SAMPLE pivot tracing."""
    for i, line in enumerate(lines):
        if "printf(\"pivoting detector around sample" in line:
            # Insert tracing after this line
            insert_lines = [
                "",
                "        if(tracing_enabled) {",
                "            printf(\"TRACE_C:detector_convention=MOSFLM\\n\");",
                "            printf(\"TRACE_C:detector_pivot=SAMPLE\\n\");",
                "            trace_scalar(\"distance_mm\", distance * 1000.0);",
                "            trace_scalar(\"beam_center_s\", Xbeam/pixel_size - 0.5);",
                "            trace_scalar(\"beam_center_f\", Ybeam/pixel_size - 0.5);",
                "            trace_scalar(\"pixel_size_mm\", pixel_size * 1000.0);",
                "            ",
                "            trace_scalar(\"detector_rotx_deg\", detector_rotx * RTD);",
                "            trace_scalar(\"detector_roty_deg\", detector_roty * RTD);",
                "            trace_scalar(\"detector_rotz_deg\", detector_rotz * RTD);", 
                "            trace_scalar(\"detector_twotheta_deg\", detector_twotheta * RTD);",
                "            ",
                "            trace_scalar(\"detector_rotx_rad\", detector_rotx);",
                "            trace_scalar(\"detector_roty_rad\", detector_roty);",
                "            trace_scalar(\"detector_rotz_rad\", detector_rotz);",
                "            trace_scalar(\"detector_twotheta_rad\", detector_twotheta);",
                "            ",
                "            /* Log initial basis vectors (MOSFLM convention) */",
                "            trace_vec(\"initial_fdet\", 0.0, 0.0, 1.0);",
                "            trace_vec(\"initial_sdet\", 0.0, -1.0, 0.0);",
                "            trace_vec(\"initial_odet\", 1.0, 0.0, 0.0);",
                "            ",
                "            /* Log final rotated vectors */",
                "            trace_vec(\"fdet_vec\", fdet_vector[1], fdet_vector[2], fdet_vector[3]);",
                "            trace_vec(\"sdet_vec\", sdet_vector[1], sdet_vector[2], sdet_vector[3]);",
                "            trace_vec(\"odet_vec\", odet_vector[1], odet_vector[2], odet_vector[3]);",
                "        }",
                "",
            ]
            lines[i+1:i+1] = insert_lines
            return True
    return False


def add_pix0_trace(lines):
    """Add pix0_vector tracing."""
    for i, line in enumerate(lines):
        if "rotate_axis(odet_vector,odet_vector,twotheta_axis,detector_twotheta);" in line:
            # Insert tracing after this line (after all rotations are done)
            insert_lines = [
                "",
                "    /* Trace final pix0_vector and basis vectors after all rotations */",
                "    if(tracing_enabled) {",
                "        trace_vec(\"pix0_vector\", pix0_vector[1], pix0_vector[2], pix0_vector[3]);",
                "    }",
                "",
            ]
            lines[i+1:i+1] = insert_lines
            return True
    return False


def add_pixel_calculation_trace(lines):
    """Add pixel calculation tracing."""
    for i, line in enumerate(lines):
        if "pixel_pos[1] = Fdet*fdet_vector[1]+Sdet*sdet_vector[1]+Odet*odet_vector[1]+pix0_vector[1];" in line:
            # Insert tracing before this calculation
            insert_lines = [
                "",
                "                        /* Trace specific pixel if requested */",
                "                        if(tracing_enabled && spixel == trace_target_spixel && fpixel == trace_target_fpixel && ",
                "                           subS == 0 && subF == 0) {",
                "                            ",
                "                            printf(\"TRACE_C:PIXEL_CALCULATION_START=spixel:%d fpixel:%d\\n\", spixel, fpixel);",
                "                            ",
                "                            trace_scalar(\"Fdet_mm\", Fdet * 1000.0);",
                "                            trace_scalar(\"Sdet_mm\", Sdet * 1000.0);",
                "                            trace_scalar(\"Odet_mm\", Odet * 1000.0);",
                "                            ",
                "                            /* Log the basis vectors used in calculation */",
                "                            trace_vec(\"fdet_vec\", fdet_vector[1], fdet_vector[2], fdet_vector[3]);",
                "                            trace_vec(\"sdet_vec\", sdet_vector[1], sdet_vector[2], sdet_vector[3]);",
                "                            trace_vec(\"odet_vec\", odet_vector[1], odet_vector[2], odet_vector[3]);",
                "                            trace_vec(\"pix0_vector\", pix0_vector[1], pix0_vector[2], pix0_vector[3]);",
                "                        }",
                "",
            ]
            lines[i:i] = insert_lines
            
            # Now find the next few lines and add more tracing after the calculation
            for j in range(i + len(insert_lines), min(i + len(insert_lines) + 10, len(lines))):
                if "pixel_pos[3] = Fdet*fdet_vector[3]+Sdet*sdet_vector[3]+Odet*odet_vector[3]+pix0_vector[3];" in lines[j]:
                    # Insert tracing after this line
                    post_calc_lines = [
                        "",
                        "                        /* Continue tracing for target pixel */",
                        "                        if(tracing_enabled && spixel == trace_target_spixel && fpixel == trace_target_fpixel && ",
                        "                           subS == 0 && subF == 0) {",
                        "                            ",
                        "                            trace_vec(\"pixel_pos_meters\", pixel_pos[1], pixel_pos[2], pixel_pos[3]);",
                        "                            ",
                        "                            /* Convert to Angstroms for physics calculations */",
                        "                            double pixel_pos_A[3] = {pixel_pos[1]*1e10, pixel_pos[2]*1e10, pixel_pos[3]*1e10};",
                        "                            trace_vec(\"pixel_pos_angstroms\", pixel_pos_A[0], pixel_pos_A[1], pixel_pos_A[2]);",
                        "                            ",
                        "                            /* Log wavelength */",
                        "                            trace_scalar(\"wavelength_A\", lambda0);",
                        "                            ",
                        "                            /* Log incident beam vector */",
                        "                            double k_scale = 2.0 * M_PI / lambda0;",
                        "                            trace_vec(\"k_incident\", k_scale * beam_vector[1], k_scale * beam_vector[2], k_scale * beam_vector[3]);",
                        "                        }",
                        "",
                    ]
                    lines[j+1:j+1] = post_calc_lines
                    return True
    return False


def add_scattering_vector_trace(lines):
    """Add scattering vector calculation tracing."""
    for i, line in enumerate(lines):
        if "airpath = unitize(pixel_pos,diffracted);" in line:
            # Insert tracing after this line
            insert_lines = [
                "",
                "                        /* Continue scattering vector calculation for target pixel */",
                "                        if(tracing_enabled && spixel == trace_target_spixel && fpixel == trace_target_fpixel && ",
                "                           subS == 0 && subF == 0) {",
                "                            ",
                "                            double pixel_distance = sqrt(pixel_pos[1]*pixel_pos[1] + pixel_pos[2]*pixel_pos[2] + pixel_pos[3]*pixel_pos[3]);",
                "                            trace_scalar(\"pixel_distance_m\", pixel_distance);",
                "                            trace_scalar(\"pixel_distance_A\", pixel_distance * 1e10);",
                "                            ",
                "                            /* Scattered beam vector (normalized diffracted vector * k) */",
                "                            double k_scale = 2.0 * M_PI / lambda0;",
                "                            trace_vec(\"k_scattered\", k_scale * diffracted[1], k_scale * diffracted[2], k_scale * diffracted[3]);",
                "                            ",
                "                            /* Scattering vector S = k_scattered - k_incident */",
                "                            double S_vector[3];",
                "                            S_vector[0] = k_scale * diffracted[1] - k_scale * beam_vector[1];",
                "                            S_vector[1] = k_scale * diffracted[2] - k_scale * beam_vector[2];",
                "                            S_vector[2] = k_scale * diffracted[3] - k_scale * beam_vector[3];",
                "                            trace_vec(\"S_vector\", S_vector[0], S_vector[1], S_vector[2]);",
                "                            ",
                "                            /* Miller indices (using the real-space lattice vectors dot product convention) */",
                "                            double h = S_vector[0]*a[1] + S_vector[1]*a[2] + S_vector[2]*a[3];",
                "                            double k_idx = S_vector[0]*b[1] + S_vector[1]*b[2] + S_vector[2]*b[3];",
                "                            double l = S_vector[0]*c[1] + S_vector[1]*c[2] + S_vector[2]*c[3];",
                "                            ",
                "                            trace_scalar(\"h_index\", h);",
                "                            trace_scalar(\"k_index\", k_idx);",
                "                            trace_scalar(\"l_index\", l);",
                "                        }",
                "",
            ]
            lines[i+1:i+1] = insert_lines
            return True
    return False


def main():
    """Main function to add all instrumentation."""
    c_file = Path("golden_suite_generator/nanoBragg.c")
    
    if not c_file.exists():
        print(f"Error: {c_file} not found!")
        return 1
    
    # Create backup
    backup_file = c_file.with_suffix(".c.orig")
    if not backup_file.exists():
        print(f"Creating backup: {backup_file}")
        shutil.copy2(c_file, backup_file)
    
    # Read the file
    print("Reading nanoBragg.c...")
    with open(c_file, 'r') as f:
        lines = f.readlines()
    
    # Remove trailing newlines and add them back consistently
    lines = [line.rstrip('\n') for line in lines]
    
    print("Adding instrumentation...")
    
    # Add each modification
    modifications = [
        ("global variables", add_globals_section),
        ("trace_pixel argument", add_trace_pixel_argument),
        ("help text", add_help_text),
        ("detector tracing", add_detector_trace),
        ("sample pivot tracing", add_sample_pivot_trace),
        ("pix0 tracing", add_pix0_trace),
        ("pixel calculation tracing", add_pixel_calculation_trace),
        ("scattering vector tracing", add_scattering_vector_trace),
    ]
    
    for desc, func in modifications:
        if func(lines):
            print(f"  ✓ Added {desc}")
        else:
            print(f"  ✗ Failed to add {desc}")
    
    # Write the modified file
    print("Writing instrumented nanoBragg.c...")
    with open(c_file, 'w') as f:
        for line in lines:
            f.write(line + '\n')
    
    print("Instrumentation complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
#!/usr/bin/env python3
"""
Simple C Tracing Enhancement for nanoBragg

This script adds targeted trace statements to key calculation points
in nanoBragg.c to help debug the detector geometry mismatch.

Focus on adding single-line trace statements at critical points.
"""

import shutil
from pathlib import Path

def backup_original():
    """Create backup if it doesn't exist"""
    nanoBragg_path = Path("golden_suite_generator/nanoBragg.c")
    backup_path = Path("golden_suite_generator/nanoBragg.c.orig")
    
    if not backup_path.exists():
        print(f"Creating backup: {backup_path}")
        shutil.copy2(nanoBragg_path, backup_path)
        return True
    else:
        print(f"Backup already exists: {backup_path}")
        return False

def restore_from_backup():
    """Restore from backup if it exists"""
    nanoBragg_path = Path("golden_suite_generator/nanoBragg.c")
    backup_path = Path("golden_suite_generator/nanoBragg.c.orig")
    
    if backup_path.exists():
        print(f"Restoring from backup: {backup_path}")
        shutil.copy2(backup_path, nanoBragg_path)
        return True
    else:
        print("No backup found to restore from")
        return False

def add_simple_tracing():
    """Add simple, targeted trace statements"""
    nanoBragg_path = Path("golden_suite_generator/nanoBragg.c")
    
    with open(nanoBragg_path, 'r') as f:
        lines = f.readlines()
    
    # Find and enhance specific lines
    enhanced = False
    
    for i, line in enumerate(lines):
        # Add trace after pix0_vector calculation for BEAM pivot
        if "pix0_vector[3] = -Fbeam*fdet_vector[3]-Sbeam*sdet_vector[3]+distance*beam_vector[3];" in line:
            # Insert trace statement after this line
            lines.insert(i+1, '        printf("TRACE_C:pix0_vector_calculated=%.15g %.15g %.15g\\n", pix0_vector[1], pix0_vector[2], pix0_vector[3]);\n')
            enhanced = True
            break
    
    # Add tracing to scattering vector calculation
    for i, line in enumerate(lines):
        if "scattering[3] = (diffracted[3]-incident[3])/lambda;" in line:
            # Insert trace statement after this line
            lines.insert(i+1, '                            if(fpixel==trace_fpixel && spixel==trace_spixel && source==0) {\n')
            lines.insert(i+2, '                                printf("TRACE_C:scattering_final=%.15g %.15g %.15g\\n", scattering[1], scattering[2], scattering[3]);\n')
            lines.insert(i+3, '                            }\n')
            enhanced = True
            break
    
    # Add tracing to Miller index calculation 
    for i, line in enumerate(lines):
        if "l = dot_product(c,scattering);" in line:
            # Insert trace statements after this line
            lines.insert(i+1, '                                    if(fpixel==trace_fpixel && spixel==trace_spixel && source==0 && mos_tic==0 && phi_tic==0) {\n')
            lines.insert(i+2, '                                        printf("TRACE_C:miller_calc=h:%.15g k:%.15g l:%.15g\\n", h, k, l);\n')
            lines.insert(i+3, '                                        printf("TRACE_C:lattice_vectors=a:[%.15g %.15g %.15g] b:[%.15g %.15g %.15g] c:[%.15g %.15g %.15g]\\n", a[1], a[2], a[3], b[1], b[2], b[3], c[1], c[2], c[3]);\n')
            lines.insert(i+4, '                                    }\n')
            enhanced = True
            break
    
    if enhanced:
        # Write the enhanced content
        with open(nanoBragg_path, 'w') as f:
            f.writelines(lines)
        print("Simple tracing enhancements added")
        return True
    else:
        print("No enhancements were applied - target lines not found")
        return False

def main():
    """Main function"""
    print("=== Simple C Tracing Enhancement ===")
    
    # Create backup
    backup_original()
    
    # Check if we should restore first
    nanoBragg_path = Path("golden_suite_generator/nanoBragg.c")
    
    # Check if file looks like it was already modified
    with open(nanoBragg_path, 'r') as f:
        content = f.read()
    
    if "TRACE_C:pix0_vector_calculated" in content:
        print("File appears to already have simple enhancements. Restoring from backup first...")
        restore_from_backup()
    
    # Apply enhancements
    try:
        if add_simple_tracing():
            print("✓ Successfully added simple tracing to nanoBragg.c")
            print()
            print("The enhanced tracing includes:")
            print("- pix0_vector calculation result")
            print("- Final scattering vector")
            print("- Miller index calculation and lattice vectors")
            print()
            print("Next steps:")
            print("1. Compile with: gcc -O2 -lm -fno-fast-math -ffp-contract=off -DTRACING=1 -o nanoBragg_trace nanoBragg.c")
            print("2. Run with trace parameters")
            return True
        else:
            print("✗ Failed to add simple tracing")
            return False
    except Exception as e:
        print(f"✗ Error adding tracing: {e}")
        print("Restoring from backup...")
        restore_from_backup()
        return False

if __name__ == "__main__":
    main()
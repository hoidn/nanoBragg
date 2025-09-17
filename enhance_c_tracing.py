#!/usr/bin/env python3
"""
Enhanced C Tracing Script for nanoBragg Pixel Debugging

This script enhances the existing tracing infrastructure in nanoBragg.c
by adding more comprehensive trace statements for pixel-specific calculations.
It builds on the existing trace_spixel/trace_fpixel infrastructure.

Strategy:
1. Preserve all existing tracing code 
2. Add missing key trace statements to track detector geometry calculations
3. Focus on pixel coordinate transformations and scattering vector calculations
4. Use existing TRACING macro sections where possible
"""

import re
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

def enhance_tracing():
    """Add enhanced tracing to nanoBragg.c"""
    nanoBragg_path = Path("golden_suite_generator/nanoBragg.c")
    
    with open(nanoBragg_path, 'r') as f:
        content = f.read()
    
    # Enhancement 1: Add basis vector tracing after all detector rotations
    # Find the line that prints DETECTOR_PIX0_VECTOR and add more trace output right after
    detector_pix0_pattern = r'(printf\("DETECTOR_PIX0_VECTOR %.15g %.15g %.15g\\n", pix0_vector\[1\], pix0_vector\[2\], pix0_vector\[3\]\);)'
    
    enhanced_detector_trace = r'''\1
    
    /* Enhanced detector geometry tracing - already printed above in TRACING section */'''
    
    content = re.sub(detector_pix0_pattern, enhanced_detector_trace, content)
    
    # Enhancement 2: Add phi and mosaic rotation tracing to existing pixel trace sections
    # Find the phi rotation trace block and enhance it
    phi_trace_pattern = r'(if\(fpixel==512 && spixel==512 && source==0 && phi_tic==0\) \{\s+printf\("TRACE: Phi rotation.*?\}\s*)'
    
    # Add reciprocal lattice vector tracing after phi rotation
    enhanced_phi_trace = r'''\1
                                        
                                        if(fpixel==trace_fpixel && spixel==trace_spixel && source==0 && phi_tic==0) {
                                            printf("TRACE_C:a_star_before_mosaic=%.15g %.15g %.15g\n", a_star[1], a_star[2], a_star[3]);
                                            printf("TRACE_C:b_star_before_mosaic=%.15g %.15g %.15g\n", b_star[1], b_star[2], b_star[3]);
                                            printf("TRACE_C:c_star_before_mosaic=%.15g %.15g %.15g\n", c_star[1], c_star[2], c_star[3]);
                                        }'''
    
    content = re.sub(phi_trace_pattern, enhanced_phi_trace, content, flags=re.DOTALL)
    
    # Enhancement 3: Add real-space lattice vector tracing after mosaic rotation
    # Find the mosaic rotation trace and add real-space vectors
    mosaic_trace_pattern = r'(if\(fpixel==512 && spixel==512 && source==0 && phi_tic==0 && mos_tic==0\) \{\s+printf\("TRACE:   After mosaic rotation.*?\}\s*)'
    
    enhanced_mosaic_trace = r'''\1
                                        
                                        if(fpixel==trace_fpixel && spixel==trace_spixel && source==0 && phi_tic==0 && mos_tic==0) {
                                            printf("TRACE_C:a_real_final=%.15g %.15g %.15g\n", a[1], a[2], a[3]);
                                            printf("TRACE_C:b_real_final=%.15g %.15g %.15g\n", b[1], b[2], b[3]);
                                            printf("TRACE_C:c_real_final=%.15g %.15g %.15g\n", c[1], c[2], c[3]);
                                        }'''
    
    content = re.sub(mosaic_trace_pattern, enhanced_mosaic_trace, content, flags=re.DOTALL)
    
    # Enhancement 4: Add scattering vector components before Miller index calculation
    # Find the line where we calculate h, k, l and add scattering vector trace
    miller_calc_pattern = r'(h = dot_product\(a,scattering\);\s+k = dot_product\(b,scattering\);\s+l = dot_product\(c,scattering\);)'
    
    enhanced_miller_trace = r'''if(fpixel==trace_fpixel && spixel==trace_spixel && source==0 && mos_tic==0 && phi_tic==0) {
                                        printf("TRACE_C:scattering_vector=%.15g %.15g %.15g\n", scattering[1], scattering[2], scattering[3]);
                                        printf("TRACE_C:incident_vector=%.15g %.15g %.15g\n", incident[1], incident[2], incident[3]);
                                        printf("TRACE_C:diffracted_vector=%.15g %.15g %.15g\n", diffracted[1], diffracted[2], diffracted[3]);
                                    }
                                    
                                    \1
                                    
                                    if(fpixel==trace_fpixel && spixel==trace_spixel && source==0 && mos_tic==0 && phi_tic==0) {
                                        printf("TRACE_C:dot_products=a_dot_S:%.15g b_dot_S:%.15g c_dot_S:%.15g\n", 
                                               dot_product(a,scattering), dot_product(b,scattering), dot_product(c,scattering));
                                    }'''
    
    content = re.sub(miller_calc_pattern, enhanced_miller_trace, content)
    
    # Enhancement 5: Add pixel position calculation tracing
    # Find pixel position calculation and add trace
    pixel_pos_pattern = r'(pixel_pos\[1\] = Fdet\*fdet_vector\[1\]\+Sdet\*sdet_vector\[1\]\+Odet\*odet_vector\[1\]\+pix0_vector\[1\];\s+pixel_pos\[2\] = Fdet\*fdet_vector\[2\]\+Sdet\*sdet_vector\[2\]\+Odet\*odet_vector\[2\]\+pix0_vector\[2\];\s+pixel_pos\[3\] = Fdet\*fdet_vector\[3\]\+Sdet\*sdet_vector\[3\]\+Odet\*odet_vector\[3\]\+pix0_vector\[3\];)'
    
    enhanced_pixel_pos_trace = r'''\1
                        
                        if(fpixel==trace_fpixel && spixel==trace_spixel && source==0) {
                            printf("TRACE_C:pixel_coords=Fdet:%.15g Sdet:%.15g Odet:%.15g\n", Fdet, Sdet, Odet);
                            printf("TRACE_C:fdet_component=%.15g %.15g %.15g\n", 
                                   Fdet*fdet_vector[1], Fdet*fdet_vector[2], Fdet*fdet_vector[3]);
                            printf("TRACE_C:sdet_component=%.15g %.15g %.15g\n", 
                                   Sdet*sdet_vector[1], Sdet*sdet_vector[2], Sdet*sdet_vector[3]);
                            printf("TRACE_C:odet_component=%.15g %.15g %.15g\n", 
                                   Odet*odet_vector[1], Odet*odet_vector[2], Odet*odet_vector[3]);
                            printf("TRACE_C:pix0_component=%.15g %.15g %.15g\n", 
                                   pix0_vector[1], pix0_vector[2], pix0_vector[3]);
                        }'''
    
    content = re.sub(pixel_pos_pattern, enhanced_pixel_pos_trace, content)
    
    # Write the enhanced content
    with open(nanoBragg_path, 'w') as f:
        f.write(content)
    
    print("Enhanced tracing added to nanoBragg.c")
    return True

def main():
    """Main function"""
    print("=== Enhanced C Tracing Script ===")
    print("This script enhances existing tracing infrastructure in nanoBragg.c")
    print()
    
    # Create backup
    backup_original()
    
    # Check if we should restore first
    nanoBragg_path = Path("golden_suite_generator/nanoBragg.c")
    
    # Check if file looks like it was already modified
    with open(nanoBragg_path, 'r') as f:
        content = f.read()
    
    if "Enhanced detector geometry tracing" in content:
        print("File appears to already have enhancements. Restoring from backup first...")
        restore_from_backup()
    
    # Apply enhancements
    try:
        if enhance_tracing():
            print("✓ Successfully enhanced tracing in nanoBragg.c")
            print()
            print("Next steps:")
            print("1. Compile with: gcc -O2 -lm -fno-fast-math -ffp-contract=off -DTRACING=1 -o nanoBragg_trace nanoBragg.c")
            print("2. Run with trace parameters using run_c_trace.sh")
            print("3. Compare with Python trace using compare_c_python_traces.py")
            return True
        else:
            print("✗ Failed to enhance tracing")
            return False
    except Exception as e:
        print(f"✗ Error enhancing tracing: {e}")
        print("Restoring from backup...")
        restore_from_backup()
        return False

if __name__ == "__main__":
    main()
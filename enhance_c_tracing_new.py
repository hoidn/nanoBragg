#!/usr/bin/env python3
"""
Enhanced C tracing tool for Phase 4.1 - adds ultra-detailed pix0_vector tracing to nanoBragg.c

This script adds comprehensive trace statements specifically for the SAMPLE pivot pix0 calculation
to match the ultra-detailed Python tracer for exact comparison.
"""

import re
import shutil
from pathlib import Path


def add_enhanced_pix0_tracing():
    """Add enhanced pix0 tracing to the C code."""
    
    nanobrag_path = Path("golden_suite_generator/nanoBragg.c")
    backup_path = Path("golden_suite_generator/nanoBragg.c.pix0_backup")
    
    if not nanobrag_path.exists():
        print(f"❌ Error: {nanobrag_path} not found")
        return False
    
    # Create backup
    shutil.copy2(nanobrag_path, backup_path)
    print(f"✓ Created backup: {backup_path}")
    
    # Read the file
    with open(nanobrag_path, 'r') as f:
        content = f.read()
    
    # Find the section where pix0 is calculated in SAMPLE pivot mode
    # Look for the rotation matrix application or pix0 calculation
    
    # Add trace headers near the top of the file (after includes)
    header_insert = '''
/* Enhanced pix0 tracing for Phase 4.1 debugging */
#define PIX0_TRACE_ENABLED 1

#define PIX0_TRACE_SCALAR(tag, val) if(PIX0_TRACE_ENABLED) printf("PIX0_C:%s=%.15g\\n", tag, (double)(val))
#define PIX0_TRACE_VEC(tag, x, y, z) if(PIX0_TRACE_ENABLED) printf("PIX0_C:%s=[%.15g %.15g %.15g]\\n", tag, (double)(x), (double)(y), (double)(z))
#define PIX0_TRACE_MAT_ROW(tag, row, m00, m01, m02) if(PIX0_TRACE_ENABLED) printf("PIX0_C:%s_row%d=[%.15g %.15g %.15g]\\n", tag, row, (double)(m00), (double)(m01), (double)(m02))

'''
    
    # Insert after the last #include
    include_pattern = r'(#include\s+[<"][^>"]+[">]\s*\n)(?!.*#include)'
    content = re.sub(include_pattern, r'\1' + header_insert, content, flags=re.DOTALL)
    
    # Find detector rotation section and add detailed tracing
    # Look for where rotx, roty, rotz, twotheta are processed
    
    rotation_trace_code = '''
    /* Enhanced pix0 calculation tracing */
    if(PIX0_TRACE_ENABLED) {
        printf("\\n=== PIX0_VECTOR CALCULATION TRACE ===\\n");
        PIX0_TRACE_SCALAR("distance_mm", distance*1000.0);
        PIX0_TRACE_SCALAR("beam_center_s", Sbeam*1000.0/pixel);  /* Convert back to mm */
        PIX0_TRACE_SCALAR("beam_center_f", Fbeam*1000.0/pixel);  /* Convert back to mm */
        PIX0_TRACE_SCALAR("pixel_size_mm", pixel*1000.0);
        PIX0_TRACE_SCALAR("detector_rotx_deg", detector_rotx*180.0/M_PI);
        PIX0_TRACE_SCALAR("detector_roty_deg", detector_roty*180.0/M_PI);
        PIX0_TRACE_SCALAR("detector_rotz_deg", detector_rotz*180.0/M_PI);
        PIX0_TRACE_SCALAR("detector_twotheta_deg", detector_twotheta*180.0/M_PI);
        
        /* Trace rotation angles in radians */
        PIX0_TRACE_SCALAR("rotx_rad", detector_rotx);
        PIX0_TRACE_SCALAR("roty_rad", detector_roty);
        PIX0_TRACE_SCALAR("rotz_rad", detector_rotz);
        PIX0_TRACE_SCALAR("twotheta_rad", detector_twotheta);
        
        /* Trace initial basis vectors */
        PIX0_TRACE_VEC("fdet_initial", fdet[1], fdet[2], fdet[3]);
        PIX0_TRACE_VEC("sdet_initial", sdet[1], sdet[2], sdet[3]);
        PIX0_TRACE_VEC("odet_initial", odet[1], odet[2], odet[3]);
    }
'''
    
    # Add rotation matrix tracing
    matrix_trace_code = '''
    /* Trace rotation matrices */
    if(PIX0_TRACE_ENABLED) {
        double rx_cos = cos(detector_rotx);
        double rx_sin = sin(detector_rotx);
        PIX0_TRACE_SCALAR("rot_x_angle_rad", detector_rotx);
        PIX0_TRACE_SCALAR("rot_x_cos", rx_cos);
        PIX0_TRACE_SCALAR("rot_x_sin", rx_sin);
        PIX0_TRACE_MAT_ROW("rot_x_matrix", 0, 1.0, 0.0, 0.0);
        PIX0_TRACE_MAT_ROW("rot_x_matrix", 1, 0.0, rx_cos, -rx_sin);
        PIX0_TRACE_MAT_ROW("rot_x_matrix", 2, 0.0, rx_sin, rx_cos);
        
        double ry_cos = cos(detector_roty);
        double ry_sin = sin(detector_roty);
        PIX0_TRACE_SCALAR("rot_y_angle_rad", detector_roty);
        PIX0_TRACE_SCALAR("rot_y_cos", ry_cos);
        PIX0_TRACE_SCALAR("rot_y_sin", ry_sin);
        PIX0_TRACE_MAT_ROW("rot_y_matrix", 0, ry_cos, 0.0, ry_sin);
        PIX0_TRACE_MAT_ROW("rot_y_matrix", 1, 0.0, 1.0, 0.0);
        PIX0_TRACE_MAT_ROW("rot_y_matrix", 2, -ry_sin, 0.0, ry_cos);
        
        double rz_cos = cos(detector_rotz);
        double rz_sin = sin(detector_rotz);
        PIX0_TRACE_SCALAR("rot_z_angle_rad", detector_rotz);
        PIX0_TRACE_SCALAR("rot_z_cos", rz_cos);
        PIX0_TRACE_SCALAR("rot_z_sin", rz_sin);
        PIX0_TRACE_MAT_ROW("rot_z_matrix", 0, rz_cos, -rz_sin, 0.0);
        PIX0_TRACE_MAT_ROW("rot_z_matrix", 1, rz_sin, rz_cos, 0.0);
        PIX0_TRACE_MAT_ROW("rot_z_matrix", 2, 0.0, 0.0, 1.0);
        
        /* Two-theta matrix */
        double tt_cos = cos(detector_twotheta);
        double tt_sin = sin(detector_twotheta);
        PIX0_TRACE_SCALAR("twotheta_angle_rad", detector_twotheta);
        PIX0_TRACE_SCALAR("twotheta_cos", tt_cos);
        PIX0_TRACE_SCALAR("twotheta_sin", tt_sin);
        PIX0_TRACE_VEC("twotheta_axis", 0.0, 1.0, 0.0);  /* Y-axis for MOSFLM */
    }
'''
    
    # Add pix0 calculation tracing for SAMPLE pivot mode
    pix0_calc_trace = '''
    /* Trace pix0 calculation in SAMPLE pivot mode */
    if(PIX0_TRACE_ENABLED && sample_mode) {
        printf("\\nPIX0 CALCULATION (BEFORE ROTATIONS - SAMPLE PIVOT):\\n");
        
        /* MOSFLM beam center calculation */
        double Fclose_calc = (fbeam*pixel + 0.5*pixel) / 1000.0;  /* Convert to meters */
        double Sclose_calc = (sbeam*pixel + 0.5*pixel) / 1000.0;  /* Convert to meters */
        double distance_calc = distance;  /* Already in meters */
        
        PIX0_TRACE_SCALAR("beam_center_f_plus_half", fbeam + 0.5);
        PIX0_TRACE_SCALAR("beam_center_s_plus_half", sbeam + 0.5);
        PIX0_TRACE_SCALAR("Fclose_m", Fclose_calc);
        PIX0_TRACE_SCALAR("Sclose_m", Sclose_calc);
        PIX0_TRACE_SCALAR("distance_m", distance_calc);
        
        /* Calculate each component of unrotated pix0 */
        double fdet_comp[4] = {0, -Fclose_calc * fdet[1], -Fclose_calc * fdet[2], -Fclose_calc * fdet[3]};
        double sdet_comp[4] = {0, -Sclose_calc * sdet[1], -Sclose_calc * sdet[2], -Sclose_calc * sdet[3]};
        double odet_comp[4] = {0, distance_calc * odet[1], distance_calc * odet[2], distance_calc * odet[3]};
        
        PIX0_TRACE_VEC("fdet_component", fdet_comp[1], fdet_comp[2], fdet_comp[3]);
        PIX0_TRACE_VEC("sdet_component", sdet_comp[1], sdet_comp[2], sdet_comp[3]);
        PIX0_TRACE_VEC("odet_component", odet_comp[1], odet_comp[2], odet_comp[3]);
        
        /* Unrotated pix0 */
        double pix0_unrot[4] = {0, 
            fdet_comp[1] + sdet_comp[1] + odet_comp[1],
            fdet_comp[2] + sdet_comp[2] + odet_comp[2], 
            fdet_comp[3] + sdet_comp[3] + odet_comp[3]};
        PIX0_TRACE_VEC("pix0_unrotated", pix0_unrot[1], pix0_unrot[2], pix0_unrot[3]);
    }
'''
    
    # Add final pix0 result tracing
    final_pix0_trace = '''
    /* Trace final rotated pix0 vector */
    if(PIX0_TRACE_ENABLED) {
        PIX0_TRACE_VEC("pix0_rotated_final", pix0[1], pix0[2], pix0[3]);
        PIX0_TRACE_VEC("fdet_rotated", fdet[1], fdet[2], fdet[3]);
        PIX0_TRACE_VEC("sdet_rotated", sdet[1], sdet[2], sdet[3]);
        PIX0_TRACE_VEC("odet_rotated", odet[1], odet[2], odet[3]);
        
        /* Orthonormality check */
        double fdet_norm = sqrt(fdet[1]*fdet[1] + fdet[2]*fdet[2] + fdet[3]*fdet[3]);
        double sdet_norm = sqrt(sdet[1]*sdet[1] + sdet[2]*sdet[2] + sdet[3]*sdet[3]);
        double odet_norm = sqrt(odet[1]*odet[1] + odet[2]*odet[2] + odet[3]*odet[3]);
        
        PIX0_TRACE_SCALAR("fdet_norm", fdet_norm);
        PIX0_TRACE_SCALAR("sdet_norm", sdet_norm);
        PIX0_TRACE_SCALAR("odet_norm", odet_norm);
        
        double fdet_dot_sdet = fdet[1]*sdet[1] + fdet[2]*sdet[2] + fdet[3]*sdet[3];
        double fdet_dot_odet = fdet[1]*odet[1] + fdet[2]*odet[2] + fdet[3]*odet[3];
        double sdet_dot_odet = sdet[1]*odet[1] + sdet[2]*odet[2] + sdet[3]*odet[3];
        
        PIX0_TRACE_SCALAR("fdet_dot_sdet", fdet_dot_sdet);
        PIX0_TRACE_SCALAR("fdet_dot_odet", fdet_dot_odet);
        PIX0_TRACE_SCALAR("sdet_dot_odet", sdet_dot_odet);
        
        printf("=== PIX0_VECTOR TRACE COMPLETE ===\\n\\n");
    }
'''
    
    # Insert tracing code at strategic locations
    
    # 1. Insert rotation trace after detector rotation variables are set
    detector_setup_pattern = r'(detector_rotx\s*=.*?;.*?detector_roty\s*=.*?;.*?detector_rotz\s*=.*?;.*?detector_twotheta\s*=.*?;)'
    if re.search(detector_setup_pattern, content, re.DOTALL):
        content = re.sub(detector_setup_pattern, r'\1' + rotation_trace_code, content, flags=re.DOTALL)
        print("✓ Added rotation parameter tracing")
    else:
        print("⚠️  Could not find detector rotation setup section")
    
    # 2. Insert matrix trace before rotation matrices are applied
    # Look for the section where rotation matrices are computed
    matrix_pattern = r'(cos\(detector_rotx\).*?sin\(detector_rotx\).*?(?=.*rotmatrix))'
    if re.search(matrix_pattern, content, re.DOTALL):
        content = re.sub(matrix_pattern, matrix_trace_code + r'\1', content, flags=re.DOTALL)
        print("✓ Added rotation matrix tracing")
    else:
        print("⚠️  Could not find rotation matrix computation section")
    
    # 3. Insert pix0 calculation trace in SAMPLE pivot mode
    # Look for where pix0 is calculated before rotation
    sample_pivot_pattern = r'(if\s*\(\s*sample_mode\s*\).*?pix0\[[123]\].*?=.*?;)'
    if re.search(sample_pivot_pattern, content, re.DOTALL):
        content = re.sub(sample_pivot_pattern, pix0_calc_trace + r'\1', content, flags=re.DOTALL)
        print("✓ Added pix0 calculation tracing for SAMPLE pivot")
    else:
        print("⚠️  Could not find SAMPLE pivot pix0 calculation section")
    
    # 4. Insert final result trace after rotation is applied
    # Look for where the rotated vectors are finalized
    final_pattern = r'(rotate\(.*?pix0.*?\);.*?rotate\(.*?fdet.*?\);.*?rotate\(.*?sdet.*?\);.*?rotate\(.*?odet.*?\);)'
    if re.search(final_pattern, content, re.DOTALL):
        content = re.sub(final_pattern, r'\1' + final_pix0_trace, content, flags=re.DOTALL)
        print("✓ Added final rotated vector tracing")
    else:
        print("⚠️  Could not find final vector rotation section")
    
    # Write the modified content
    with open(nanobrag_path, 'w') as f:
        f.write(content)
    
    print(f"✓ Enhanced C tracing added to {nanobrag_path}")
    print(f"  Backup saved as: {backup_path}")
    
    return True


def create_c_trace_runner():
    """Create a script to run the enhanced C trace."""
    
    script_content = '''#!/bin/bash
# Enhanced C trace runner for Phase 4.1 pix0 debugging

echo "Building enhanced nanoBragg with pix0 tracing..."
cd golden_suite_generator
make clean
make

if [ $? -ne 0 ]; then
    echo "❌ Build failed!"
    exit 1
fi

echo "✓ Build successful"

echo "Running enhanced C trace..."
./nanoBragg \\
    -lambda 6.2 \\
    -N 5 \\
    -cell 100 100 100 90 90 90 \\
    -default_F 100 \\
    -distance 100 \\
    -detpixels 1024 \\
    -beam 51.2 51.2 \\
    -detector_rotx 5 \\
    -detector_roty 3 \\
    -detector_rotz 2 \\
    -twotheta 20 \\
    -floatfile enhanced_trace.bin \\
    2>&1 | grep "PIX0_C:" > ../c_pix0_trace_enhanced.log

echo "✓ Enhanced C trace saved to c_pix0_trace_enhanced.log"
echo "✓ Output image saved to enhanced_trace.bin"

cd ..
echo "Lines in trace file:"
wc -l c_pix0_trace_enhanced.log
'''
    
    script_path = Path("run_enhanced_c_trace.sh")
    with open(script_path, 'w') as f:
        f.write(script_content)
    
    script_path.chmod(0o755)
    print(f"✓ Created enhanced C trace runner: {script_path}")
    
    return script_path


def main():
    """Main function to enhance C tracing."""
    print("Enhanced C Tracing Setup for Phase 4.1")
    print("======================================")
    
    # Add enhanced tracing to C code
    success = add_enhanced_pix0_tracing()
    
    if success:
        # Create runner script
        script_path = create_c_trace_runner()
        
        print(f"\n✅ Enhanced C tracing setup complete!")
        print(f"   1. Run: ./{script_path}")
        print(f"   2. Run: python scripts/trace_pix0_detailed.py > py_pix0_trace_detailed.log")
        print(f"   3. Compare: python scripts/compare_rotation_matrices.py")
    else:
        print("\n❌ Enhanced C tracing setup failed!")


if __name__ == "__main__":
    main()
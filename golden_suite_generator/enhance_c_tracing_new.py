#!/usr/bin/env python3
"""
Enhanced C code instrumentation to deeply trace beam center calculation.

This script adds detailed printf statements to understand exactly how C calculates 
beam center values, including unit conversions and intermediate calculations.
"""

import os
import shutil

def backup_original():
    """Create backup of original C file."""
    if not os.path.exists("nanoBragg.c.beam_backup"):
        shutil.copy("nanoBragg.c", "nanoBragg.c.beam_backup")
        print("Created backup: nanoBragg.c.beam_backup")

def add_beam_center_tracing():
    """Add comprehensive beam center tracing to nanoBragg.c"""
    
    # Read the current C file
    with open("nanoBragg.c", "r") as f:
        content = f.read()
    
    # Define the tracing code to insert at strategic locations
    
    # 1. Trace command line parsing of Xbeam/Ybeam
    xbeam_parse_trace = '''
            {
                printf("TRACE_BEAM_CENTER:parsing_Xbeam=%.15g (input_mm=%.15g -> meters=%.15g)\\n", 
                       atof(argv[i+1]), atof(argv[i+1]), atof(argv[i+1])/1000.0);
                Xbeam = atof(argv[i+1])/1000.0;
                printf("TRACE_BEAM_CENTER:Xbeam_after_parse=%.15g\\n", Xbeam);
                detector_pivot = BEAM;
            }'''
    
    ybeam_parse_trace = '''
            {
                printf("TRACE_BEAM_CENTER:parsing_Ybeam=%.15g (input_mm=%.15g -> meters=%.15g)\\n", 
                       atof(argv[i+1]), atof(argv[i+1]), atof(argv[i+1])/1000.0);
                Ybeam = atof(argv[i+1])/1000.0;
                printf("TRACE_BEAM_CENTER:Ybeam_after_parse=%.15g\\n", Ybeam);
                detector_pivot = BEAM;
            }'''
    
    # 2. Trace pixel_size parsing
    pixel_parse_trace = '''
            {
                printf("TRACE_BEAM_CENTER:parsing_pixel=%.15g (input_mm=%.15g -> meters=%.15g)\\n", 
                       atof(argv[i+1]), atof(argv[i+1]), atof(argv[i+1])/1000.0);
                pixel_size = atof(argv[i+1])/1000.0;
                printf("TRACE_BEAM_CENTER:pixel_size_after_parse=%.15g\\n", pixel_size);
            }'''
    
    # Replace the original parsing blocks
    content = content.replace(
        '''            if(strstr(argv[i], "-Xbeam") && (argc > (i+1)))
            {
                Xbeam = atof(argv[i+1])/1000.0;
                detector_pivot = BEAM;
            }''',
        f'            if(strstr(argv[i], "-Xbeam") && (argc > (i+1))){xbeam_parse_trace}'
    )
    
    content = content.replace(
        '''            if(strstr(argv[i], "-Ybeam") && (argc > (i+1)))
            {
                Ybeam = atof(argv[i+1])/1000.0;
                detector_pivot = BEAM;
            }''',
        f'            if(strstr(argv[i], "-Ybeam") && (argc > (i+1))){ybeam_parse_trace}'
    )
    
    content = content.replace(
        '''            if(strstr(argv[i], "-pixel") && (argc > (i+1)))
            {
                pixel_size = atof(argv[i+1])/1000.0;
            }''',
        f'            if(strstr(argv[i], "-pixel") && (argc > (i+1))){pixel_parse_trace}'
    )
    
    # 3. Trace Fclose/Sclose initialization (around line 1178-1179)
    fclose_sclose_init_trace = '''    printf("TRACE_BEAM_CENTER:initial_defaults Fclose=%.15g Sclose=%.15g\\n", Fclose, Sclose);
    if(isnan(Fclose)) {
        Fclose = (detsize_f - 0*pixel_size)/2.0;
        printf("TRACE_BEAM_CENTER:Fclose_default_calc=(detsize_f - 0*pixel_size)/2.0 = (%.15g - 0*%.15g)/2.0 = %.15g\\n", detsize_f, pixel_size, Fclose);
    }
    if(isnan(Sclose)) {
        Sclose = (detsize_s + 0*pixel_size)/2.0;
        printf("TRACE_BEAM_CENTER:Sclose_default_calc=(detsize_s + 0*pixel_size)/2.0 = (%.15g + 0*%.15g)/2.0 = %.15g\\n", detsize_s, pixel_size, Sclose);
    }'''
    
    content = content.replace(
        '''    if(isnan(Fclose)) Fclose = (detsize_f - 0*pixel_size)/2.0;
    if(isnan(Sclose)) Sclose = (detsize_s + 0*pixel_size)/2.0;''',
        fclose_sclose_init_trace
    )
    
    # 4. Trace MOSFLM convention Xbeam/Ybeam assignment (around line 1218-1219)
    mosflm_beam_trace = '''        printf("TRACE_BEAM_CENTER:MOSFLM_convention Fbeam_calc=Ybeam + 0.5*pixel_size = %.15g + 0.5*%.15g = %.15g\\n", Ybeam, pixel_size, Ybeam + 0.5*pixel_size);
        printf("TRACE_BEAM_CENTER:MOSFLM_convention Sbeam_calc=Xbeam + 0.5*pixel_size = %.15g + 0.5*%.15g = %.15g\\n", Xbeam, pixel_size, Xbeam + 0.5*pixel_size);
        Fbeam = Ybeam + 0.5*pixel_size;
        Sbeam = Xbeam + 0.5*pixel_size;'''
    
    content = content.replace(
        '''        Fbeam = Ybeam + 0.5*pixel_size;
        Sbeam = Xbeam + 0.5*pixel_size;''',
        mosflm_beam_trace
    )
    
    # 5. Trace CUSTOM convention Fclose/Sclose assignment (around line 1273-1274)
    custom_close_trace = '''        printf("TRACE_BEAM_CENTER:CUSTOM_convention Fclose=Xbeam=%.15g Sclose=Ybeam=%.15g\\n", Xbeam, Ybeam);
        Fclose = Xbeam;
        Sclose = Ybeam;'''
    
    content = content.replace(
        '''        Fclose = Xbeam;
        Sclose = Ybeam;''',
        custom_close_trace
    )
    
    # 6. Trace pix0_vector calculation (around line 1742-1744)
    pix0_vector_trace = '''        printf("TRACE_BEAM_CENTER:pix0_vector_calc components:\\n");
        printf("  -Fclose*fdet_vector[1] = -%.15g*%.15g = %.15g\\n", Fclose, fdet_vector[1], -Fclose*fdet_vector[1]);
        printf("  -Sclose*sdet_vector[1] = -%.15g*%.15g = %.15g\\n", Sclose, sdet_vector[1], -Sclose*sdet_vector[1]);
        printf("  close_distance*odet_vector[1] = %.15g*%.15g = %.15g\\n", close_distance, odet_vector[1], close_distance*odet_vector[1]);
        pix0_vector[1] = -Fclose*fdet_vector[1]-Sclose*sdet_vector[1]+close_distance*odet_vector[1];
        pix0_vector[2] = -Fclose*fdet_vector[2]-Sclose*sdet_vector[2]+close_distance*odet_vector[2];
        pix0_vector[3] = -Fclose*fdet_vector[3]-Sclose*sdet_vector[3]+close_distance*odet_vector[3];
        printf("TRACE_BEAM_CENTER:pix0_vector_after_calc=[%.15g %.15g %.15g]\\n", pix0_vector[1], pix0_vector[2], pix0_vector[3]);'''
    
    content = content.replace(
        '''        pix0_vector[1] = -Fclose*fdet_vector[1]-Sclose*sdet_vector[1]+close_distance*odet_vector[1];
        pix0_vector[2] = -Fclose*fdet_vector[2]-Sclose*sdet_vector[2]+close_distance*odet_vector[2];
        pix0_vector[3] = -Fclose*fdet_vector[3]-Sclose*sdet_vector[3]+close_distance*odet_vector[3];''',
        pix0_vector_trace
    )
    
    # 7. Trace final Fclose/Sclose calculation from dot products (around line 1849-1850)
    final_close_trace = '''    printf("TRACE_BEAM_CENTER:final_close_calc dot_products:\\n");
    printf("  pix0_vector=[%.15g %.15g %.15g]\\n", pix0_vector[1], pix0_vector[2], pix0_vector[3]);
    printf("  fdet_vector=[%.15g %.15g %.15g]\\n", fdet_vector[1], fdet_vector[2], fdet_vector[3]);
    printf("  sdet_vector=[%.15g %.15g %.15g]\\n", sdet_vector[1], sdet_vector[2], sdet_vector[3]);
    printf("  odet_vector=[%.15g %.15g %.15g]\\n", odet_vector[1], odet_vector[2], odet_vector[3]);
    
    double fclose_dot = -dot_product(pix0_vector,fdet_vector);
    double sclose_dot = -dot_product(pix0_vector,sdet_vector);
    double close_dist_dot = dot_product(pix0_vector,odet_vector);
    
    printf("TRACE_BEAM_CENTER:dot_product_results:\\n");
    printf("  Fclose = -dot_product(pix0_vector,fdet_vector) = %.15g\\n", fclose_dot);
    printf("  Sclose = -dot_product(pix0_vector,sdet_vector) = %.15g\\n", sclose_dot);
    printf("  close_distance = dot_product(pix0_vector,odet_vector) = %.15g\\n", close_dist_dot);
    
    Fclose         = fclose_dot;
    Sclose         = sclose_dot;
    close_distance = close_dist_dot;'''
    
    content = content.replace(
        '''    Fclose         = -dot_product(pix0_vector,fdet_vector);
    Sclose         = -dot_product(pix0_vector,sdet_vector);
    close_distance =  dot_product(pix0_vector,odet_vector);''',
        final_close_trace
    )
    
    # 8. Add trace at the end of main calculation showing final values
    beam_summary_trace = '''    printf("TRACE_BEAM_CENTER:FINAL_SUMMARY:\\n");
    printf("  Input: -Xbeam %.1f -Ybeam %.1f -pixel %.4f\\n", Xbeam*1000.0, Ybeam*1000.0, pixel_size*1000.0);
    printf("  Calculated: Fclose=%.15g Sclose=%.15g (in meters)\\n", Fclose, Sclose);
    printf("  For comparison: Fclose*1000=%.15g Sclose*1000=%.15g (in mm)\\n", Fclose*1000.0, Sclose*1000.0);'''
    
    # Insert this before the print of detector settings (around line 2666)
    content = content.replace(
        'printf("  Xbeam=%lg Ybeam=%lg\\n",Xbeam,Ybeam);',
        f'{beam_summary_trace}\n    printf("  Xbeam=%lg Ybeam=%lg\\n",Xbeam,Ybeam);'
    )
    
    # Write the modified content
    with open("nanoBragg.c", "w") as f:
        f.write(content)
    
    print("Enhanced beam center tracing added to nanoBragg.c")

def main():
    """Main function to apply beam center tracing enhancements."""
    backup_original()
    add_beam_center_tracing()
    print("Beam center tracing enhancement complete!")
    print("Run: make -j4 && ./nanoBragg [your_params] 2>&1 | grep 'TRACE_BEAM_CENTER'")

if __name__ == "__main__":
    main()
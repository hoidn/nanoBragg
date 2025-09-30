// Add after line that computes final pixel intensity
if (fpixel == 79 && spixel == 64) {
    printf("TRACE_C: pixel=(%d,%d)\n", spixel, fpixel);
    printf("TRACE_C: pix0_vector=(%.10e, %.10e, %.10e)\n", pix0[1], pix0[2], pix0[3]);
    printf("TRACE_C: fdet=(%.10e, %.10e, %.10e)\n", fdet[1], fdet[2], fdet[3]);
    printf("TRACE_C: sdet=(%.10e, %.10e, %.10e)\n", sdet[1], sdet[2], sdet[3]);
    printf("TRACE_C: odet=(%.10e, %.10e, %.10e)\n", odet[1], odet[2], odet[3]);
    printf("TRACE_C: distance=%.10e\n", distance);
    printf("TRACE_C: close_distance=%.10e\n", close_distance);
    printf("TRACE_C: pixel_size=%.10e\n", pixel_size);
    printf("TRACE_C: pixel_pos=%.10e\n", pixel_pos);
    printf("TRACE_C: airpath=%.10e\n", airpath);
    printf("TRACE_C: omega_pixel=%.10e\n", omega_pixel);
    printf("TRACE_C: omega_sub_reduction=%.10e\n", omega_sub_reduction);
    printf("TRACE_C: polarization=%.10e\n", polarization);
    printf("TRACE_C: I_bg=%.10e\n", I);
    printf("TRACE_C: steps=%d\n", steps);
}

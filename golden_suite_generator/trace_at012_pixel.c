/* Trace patch for AT-PARALLEL-012 triclinic case
 * Insert this code into nanoBragg.c at the pixel loop (around line 4000+)
 * to print detailed trace for pixel (368, 262)
 */

// Add after the pixel coordinate calculation (after "source_path=" declaration):
if (fpixel == 262 && spixel == 368) {
    fprintf(stderr, "TRACE_C: === PIXEL (%d, %d) TRACE START ===\n", fpixel, spixel);
    fprintf(stderr, "TRACE_C: pixel_pos: [%.15e, %.15e, %.15e] m\n",
            pixel_pos[1], pixel_pos[2], pixel_pos[3]);
    fprintf(stderr, "TRACE_C: close_distance: %.15e m\n", close_distance);
    fprintf(stderr, "TRACE_C: distance: %.15e m (from pivot)\n", distance);
    fprintf(stderr, "TRACE_C: airpath: %.15e m\n", airpath);
    fprintf(stderr, "TRACE_C: pixel_size: %.15e m\n", pixel_size);
    fprintf(stderr, "TRACE_C: omega_pixel: %.15e sr\n", omega_pixel);
}

// Add after incident/diffracted calculation (after "diffracted[i] = pixel_pos[i]/distance;"):
if (fpixel == 262 && spixel == 368) {
    fprintf(stderr, "TRACE_C: incident: [%.15e, %.15e, %.15e]\n",
            incident[1], incident[2], incident[3]);
    fprintf(stderr, "TRACE_C: diffracted: [%.15e, %.15e, %.15e]\n",
            diffracted[1], diffracted[2], diffracted[3]);
    fprintf(stderr, "TRACE_C: scattering_vector: [%.15e, %.15e, %.15e] 1/A\n",
            scattering_vector[1], scattering_vector[2], scattering_vector[3]);
}

// Add after Miller indices calculation (after "l = dot_product(c0,scattering_vector);"):
if (fpixel == 262 && spixel == 368) {
    fprintf(stderr, "TRACE_C: h_float: %.15e\n", h);
    fprintf(stderr, "TRACE_C: k_float: %.15e\n", k);
    fprintf(stderr, "TRACE_C: l_float: %.15e\n", l);
    fprintf(stderr, "TRACE_C: h_int: %d\n", h0);
    fprintf(stderr, "TRACE_C: k_int: %d\n", k0);
    fprintf(stderr, "TRACE_C: l_int: %d\n", l0);
}

// Add after F_cell calculation (after "source_I *= F_cell*F_cell;"):
if (fpixel == 262 && spixel == 368) {
    fprintf(stderr, "TRACE_C: F_cell: %.15e\n", F_cell);
    fprintf(stderr, "TRACE_C: F_cell^2: %.15e\n", F_cell*F_cell);
}

// Add after F_latt calculation (after "source_I *= F_latt*F_latt;"):
if (fpixel == 262 && spixel == 368) {
    fprintf(stderr, "TRACE_C: F_latt_a: %.15e\n", F_latt_a);
    fprintf(stderr, "TRACE_C: F_latt_b: %.15e\n", F_latt_b);
    fprintf(stderr, "TRACE_C: F_latt_c: %.15e\n", F_latt_c);
    fprintf(stderr, "TRACE_C: F_latt: %.15e\n", F_latt);
    fprintf(stderr, "TRACE_C: F_latt^2: %.15e\n", F_latt*F_latt);
}

// Add after polarization calculation (after "polar = polarization_factor(polarization,incident,diffracted,polar_vector);"):
if (fpixel == 262 && spixel == 368) {
    fprintf(stderr, "TRACE_C: polarization_factor: %.15e\n", polar);
}

// Add at the end of innermost loop (after "I += source_I;"):
if (fpixel == 262 && spixel == 368) {
    fprintf(stderr, "TRACE_C: source_I_contribution: %.15e\n", source_I);
    fprintf(stderr, "TRACE_C: accumulated_I: %.15e\n", I);
    fprintf(stderr, "TRACE_C: steps: %ld\n", steps);
}

// Add after final intensity calculation (after "pixel_value = r_e_sqr*fluence*I*polar*omega_pixel*omega_sub_reduction/steps;"):
if (fpixel == 262 && spixel == 368) {
    fprintf(stderr, "TRACE_C: r_e_sqr: %.15e\n", r_e_sqr);
    fprintf(stderr, "TRACE_C: fluence: %.15e\n", fluence);
    fprintf(stderr, "TRACE_C: I_before_scaling: %.15e\n", I);
    fprintf(stderr, "TRACE_C: final_pixel_value: %.15e\n", pixel_value);
    fprintf(stderr, "TRACE_C: === PIXEL (%d, %d) TRACE END ===\n", fpixel, spixel);
}
# nanoBragg.c φ Rotation Reference Snippets

## Static setup — misset + reciprocal/real recomputation (lines 2053-2278)

```c
            printf("reading %s\n",matfilename);
            if(! fscanf(infile,"%lg%lg%lg",a_star+1,b_star+1,c_star+1)) {perror("fscanf");};
            if(! fscanf(infile,"%lg%lg%lg",a_star+2,b_star+2,c_star+2)) {perror("fscanf");};
            if(! fscanf(infile,"%lg%lg%lg",a_star+3,b_star+3,c_star+3)) {perror("fscanf");};
            fclose(infile);

            /* mosflm A matrix includes the wavelength, so remove it */
            /* calculate reciprocal cell lengths, store in 0th element */
            printf("TRACE: Raw matrix values from file:\n");
            printf("TRACE:   a_star (raw) = [%g, %g, %g]\n", a_star[1], a_star[2], a_star[3]);
            printf("TRACE:   b_star (raw) = [%g, %g, %g]\n", b_star[1], b_star[2], b_star[3]);
            printf("TRACE:   c_star (raw) = [%g, %g, %g]\n", c_star[1], c_star[2], c_star[3]);
            printf("TRACE:   lambda0 = %g Angstroms\n", lambda0*1e10);
            printf("TRACE:   scaling factor = 1e-10/lambda0 = %g\n", 1e-10/lambda0);
            
            vector_scale(a_star,a_star,1e-10/lambda0);
            vector_scale(b_star,b_star,1e-10/lambda0);
            vector_scale(c_star,c_star,1e-10/lambda0);
            
            printf("TRACE: After wavelength correction:\n");
            printf("TRACE:   a_star = [%g, %g, %g] |a_star| = %g\n", a_star[1], a_star[2], a_star[3], a_star[0]);
            printf("TRACE:   b_star = [%g, %g, %g] |b_star| = %g\n", b_star[1], b_star[2], b_star[3], b_star[0]);
            printf("TRACE:   c_star = [%g, %g, %g] |c_star| = %g\n", c_star[1], c_star[2], c_star[3], c_star[0]);
        }
    }

    /* check for flag to generate random missetting angle */
    if(misset[0] == -1.0)
    {
        /* use spherical cap as sphere to generate random orientation in umat */
        mosaic_rotation_umat(90.0, umat, &misset_seed);
        /* get the missetting angles, in case we want to use them again on -misset option */
        umat2misset(umat,misset);
        printf("random orientation misset angles: %f %f %f deg\n",misset[1]*RTD,misset[2]*RTD,misset[3]*RTD);
        /* apply this orientation shift */
        //rotate_umat(a_star,a_star,umat);
        //rotate_umat(b_star,b_star,umat);
        //rotate_umat(c_star,c_star,umat);
        /* do not apply again */
        misset[0] = 1.0;
    }

    /* apply any missetting angle, if not already done */
    if(misset[0] > 0.0)
    {
        printf("TRACE: Before misset rotation:\n");
        printf("TRACE:   a_star = [%g, %g, %g] |a_star| = %g\n", a_star[1], a_star[2], a_star[3], a_star[0]);
        printf("TRACE:   b_star = [%g, %g, %g] |b_star| = %g\n", b_star[1], b_star[2], b_star[3], b_star[0]);
        printf("TRACE:   c_star = [%g, %g, %g] |c_star| = %g\n", c_star[1], c_star[2], c_star[3], c_star[0]);
        printf("TRACE:   misset angles = [%g, %g, %g] degrees\n", misset[1]*RTD, misset[2]*RTD, misset[3]*RTD);
        
        rotate(a_star,a_star,misset[1],misset[2],misset[3]);
        rotate(b_star,b_star,misset[1],misset[2],misset[3]);
        rotate(c_star,c_star,misset[1],misset[2],misset[3]);
        
        printf("TRACE: After misset rotation:\n");
        printf("TRACE:   a_star = [%g, %g, %g] |a_star| = %g\n", a_star[1], a_star[2], a_star[3], a_star[0]);
        printf("TRACE:   b_star = [%g, %g, %g] |b_star| = %g\n", b_star[1], b_star[2], b_star[3], b_star[0]);
        printf("TRACE:   c_star = [%g, %g, %g] |c_star| = %g\n", c_star[1], c_star[2], c_star[3], c_star[0]);
    }

    /* various cross products */
    printf("TRACE: Computing cross products of reciprocal vectors:\n");
    printf("TRACE:   Input vectors for cross products:\n");
    printf("TRACE:     a_star = [%g, %g, %g]\n", a_star[1], a_star[2], a_star[3]);
    printf("TRACE:     b_star = [%g, %g, %g]\n", b_star[1], b_star[2], b_star[3]);
    printf("TRACE:     c_star = [%g, %g, %g]\n", c_star[1], c_star[2], c_star[3]);
    
    cross_product(a_star,b_star,a_star_cross_b_star);
    cross_product(b_star,c_star,b_star_cross_c_star);
    cross_product(c_star,a_star,c_star_cross_a_star);
    
    printf("TRACE:   Cross product results:\n");
    printf("TRACE:     a_star x b_star = [%g, %g, %g]\n", a_star_cross_b_star[1], a_star_cross_b_star[2], a_star_cross_b_star[3]);
    printf("TRACE:     b_star x c_star = [%g, %g, %g]\n", b_star_cross_c_star[1], b_star_cross_c_star[2], b_star_cross_c_star[3]);
    printf("TRACE:     c_star x a_star = [%g, %g, %g]\n", c_star_cross_a_star[1], c_star_cross_a_star[2], c_star_cross_a_star[3]);

    /* reciprocal lattice vector "a_star" is defined as perpendicular to both b and c, and must also preserve volume
       converse is true for direct-space lattice: a is perpendicular to both b_star and c_star
       a = ( b_star cross c_star ) / V_star    */

    /* reciprocal unit cell volume, but is it lambda-corrected? */
    V_star = dot_product(a_star,b_star_cross_c_star);
    printf("TRACE: Reciprocal cell volume calculation:\n");
    printf("TRACE:   V_star = a_star . (b_star x c_star) = %g\n", V_star);

    /* make sure any user-supplied cell takes */
    if(user_cell)
    {
        /* a,b,c and V_cell were generated above */

        /* force the cross-product vectors to have proper magnitude: b_star X c_star = a*V_star */
        vector_rescale(b_star_cross_c_star,b_star_cross_c_star,a[0]/V_cell);
        vector_rescale(c_star_cross_a_star,c_star_cross_a_star,b[0]/V_cell);
        vector_rescale(a_star_cross_b_star,a_star_cross_b_star,c[0]/V_cell);
        V_star = 1.0/V_cell;
    }

    /* direct-space cell volume */
    V_cell = 1.0/V_star;
    printf("TRACE: Direct-space cell volume: V_cell = 1/V_star = %g\n", V_cell);

    /* generate direct-space cell vectors, also updates magnitudes */
    printf("TRACE: Before computing real-space vectors:\n");
    printf("TRACE:   b_star_cross_c_star = [%g, %g, %g]\n", b_star_cross_c_star[1], b_star_cross_c_star[2], b_star_cross_c_star[3]);
    printf("TRACE:   c_star_cross_a_star = [%g, %g, %g]\n", c_star_cross_a_star[1], c_star_cross_a_star[2], c_star_cross_a_star[3]);
    printf("TRACE:   a_star_cross_b_star = [%g, %g, %g]\n", a_star_cross_b_star[1], a_star_cross_b_star[2], a_star_cross_b_star[3]);
    printf("TRACE:   V_cell = %g, V_star = %g\n", V_cell, V_star);
    
    vector_scale(b_star_cross_c_star,a,V_cell);
    vector_scale(c_star_cross_a_star,b,V_cell);
    vector_scale(a_star_cross_b_star,c,V_cell);
    
    printf("TRACE: After computing real-space vectors:\n");
    printf("TRACE:   a = [%g, %g, %g] |a| = %g\n", a[1], a[2], a[3], a[0]);
    printf("TRACE:   b = [%g, %g, %g] |b| = %g\n", b[1], b[2], b[3], b[0]);
    printf("TRACE:   c = [%g, %g, %g] |c| = %g\n", c[1], c[2], c[3], c[0]);

    /* now that we have direct-space vectors, re-generate the reciprocal ones */
    printf("TRACE: Re-generating reciprocal vectors from real-space vectors:\n");
    printf("TRACE:   Before re-generation: a_star = [%g, %g, %g] |a_star| = %g\n", a_star[1], a_star[2], a_star[3], a_star[0]);
    printf("TRACE:   Before re-generation: b_star = [%g, %g, %g] |b_star| = %g\n", b_star[1], b_star[2], b_star[3], b_star[0]);
    printf("TRACE:   Before re-generation: c_star = [%g, %g, %g] |c_star| = %g\n", c_star[1], c_star[2], c_star[3], c_star[0]);
    
    cross_product(a,b,a_cross_b);
    cross_product(b,c,b_cross_c);
    cross_product(c,a,c_cross_a);
    
    printf("TRACE:   Cross products: b_cross_c = [%g, %g, %g]\n", b_cross_c[1], b_cross_c[2], b_cross_c[3]);
    printf("TRACE:   Cross products: c_cross_a = [%g, %g, %g]\n", c_cross_a[1], c_cross_a[2], c_cross_a[3]);
    printf("TRACE:   Cross products: a_cross_b = [%g, %g, %g]\n", a_cross_b[1], a_cross_b[2], a_cross_b[3]);
    
    vector_scale(b_cross_c,a_star,V_star);
    vector_scale(c_cross_a,b_star,V_star);
    vector_scale(a_cross_b,c_star,V_star);
    
    printf("TRACE:   After re-generation: a_star = [%g, %g, %g] |a_star| = %g\n", a_star[1], a_star[2], a_star[3], a_star[0]);
    printf("TRACE:   After re-generation: b_star = [%g, %g, %g] |b_star| = %g\n", b_star[1], b_star[2], b_star[3], b_star[0]);
    printf("TRACE:   After re-generation: c_star = [%g, %g, %g] |c_star| = %g\n", c_star[1], c_star[2], c_star[3], c_star[0]);

    /* for fun, calculate the cell angles too */
    sin_alpha = a_star[0]*V_cell/b[0]/c[0];
    sin_beta  = b_star[0]*V_cell/a[0]/c[0];
    sin_gamma = c_star[0]*V_cell/a[0]/b[0];
    cos_alpha = dot_product(b,c)/b[0]/c[0];
    cos_beta  = dot_product(a,c)/a[0]/c[0];
    cos_gamma = dot_product(a,b)/a[0]/b[0];
    if(sin_alpha>1.0000001 || sin_alpha<-1.0000001 ||
       sin_beta >1.0000001 || sin_beta <-1.0000001 ||
       sin_gamma>1.0000001 || sin_gamma<-1.0000001 ||
       cos_alpha>1.0000001 || cos_alpha<-1.0000001 ||
       cos_beta >1.0000001 || cos_beta <-1.0000001 ||
       cos_gamma>1.0000001 || cos_gamma<-1.0000001 )
    {
        printf("WARNING: oddball cell angles:\n");
            printf("sin_alpha = %.25g\n",sin_alpha);
            printf("cos_alpha = %.25g\n",cos_alpha);
            printf("sin_beta  = %.25g\n",sin_beta);
            printf("cos_beta  = %.25g\n",cos_beta);
            printf("sin_gamma = %.25g\n",sin_gamma);
            printf("cos_gamma = %.25g\n",cos_gamma);
    }
    if(sin_alpha>1.0) sin_alpha=1.0;
    if(sin_beta >1.0) sin_beta =1.0;
    if(sin_gamma>1.0) sin_gamma=1.0;
    if(sin_alpha<-1.0) sin_alpha=-1.0;
    if(sin_beta <-1.0) sin_beta =-1.0;
    if(sin_gamma<-1.0) sin_gamma=-1.0;
    if(cos_alpha*cos_alpha>1.0) cos_alpha=1.0;
    if(cos_beta *cos_beta >1.0) cos_beta=1.0;
    if(cos_gamma*cos_gamma>1.0) cos_gamma=1.0;
    alpha = atan2(sin_alpha,cos_alpha);
    beta  = atan2(sin_beta ,cos_beta );
    gamma = atan2(sin_gamma,cos_gamma);


    /* reciprocal cell angles */
    sin_alpha_star = a[0]*V_star/b_star[0]/c_star[0];
    sin_beta_star  = b[0]*V_star/a_star[0]/c_star[0];
    sin_gamma_star = c[0]*V_star/a_star[0]/b_star[0];
    cos_alpha_star = dot_product(b_star,c_star)/b_star[0]/c_star[0];
    cos_beta_star  = dot_product(a_star,c_star)/a_star[0]/c_star[0];
    cos_gamma_star = dot_product(a_star,b_star)/a_star[0]/b_star[0];
    if(sin_alpha_star>1.0000001 || sin_alpha_star<-1.0000001 ||
       sin_beta_star >1.0000001 || sin_beta_star <-1.0000001 ||
       sin_gamma_star>1.0000001 || sin_gamma_star<-1.0000001 ||
       cos_alpha_star>1.0000001 || cos_alpha_star<-1.0000001 ||
       cos_beta_star >1.0000001 || cos_beta_star <-1.0000001 ||
       cos_gamma_star>1.0000001 || cos_gamma_star<-1.0000001 )
    {
            printf("WARNING: oddball reciprocal cell angles:\n");
            printf("sin(alpha_star) = %.25g\n",sin_alpha_star);
            printf("cos(alpha_star) = %.25g\n",cos_alpha_star);
            printf("sin(beta_star)  = %.25g\n",sin_beta_star);
            printf("cos(beta_star)  = %.25g\n",cos_beta_star);
            printf("sin(gamma_star) = %.25g\n",sin_gamma_star);
            printf("cos(gamma_star) = %.25g\n",cos_gamma_star);
    }
    if(sin_alpha_star>1.0) sin_alpha_star=1.0;
    if(sin_beta_star >1.0) sin_beta_star =1.0;
    if(sin_gamma_star>1.0) sin_gamma_star=1.0;
    if(sin_alpha_star<-1.0) sin_alpha_star=-1.0;
    if(sin_beta_star <-1.0) sin_beta_star =-1.0;
    if(sin_gamma_star<-1.0) sin_gamma_star=-1.0;
    if(cos_alpha_star*cos_alpha_star>1.0) cos_alpha_star=1.0;
    if(cos_beta_star *cos_beta_star >1.0) cos_beta_star=1.0;
    if(cos_gamma_star*cos_gamma_star>1.0) cos_gamma_star=1.0;
    alpha_star = atan2(sin_alpha_star,cos_alpha_star);
    beta_star  = atan2(sin_beta_star ,cos_beta_star );
    gamma_star = atan2(sin_gamma_star,cos_gamma_star);

    printf("Unit Cell: %g %g %g %g %g %g\n", a[0],b[0],c[0],alpha*RTD,beta*RTD,gamma*RTD);
    printf("Recp Cell: %g %g %g %g %g %g\n", a_star[0],b_star[0],c_star[0],alpha_star*RTD,beta_star*RTD,gamma_star*RTD);
    printf("volume = %g A^3\n",V_cell);

    /* print out the real-space matrix */
    printf("real-space cell vectors (Angstrom):\n");
    printf("     %-10s  %-10s  %-10s\n","a","b","c");
    printf("X: %11.8f %11.8f %11.8f\n",a[1],b[1],c[1]);
    printf("Y: %11.8f %11.8f %11.8f\n",a[2],b[2],c[2]);
    printf("Z: %11.8f %11.8f %11.8f\n",a[3],b[3],c[3]);
    printf("reciprocal-space cell vectors (Angstrom^-1):\n");
    printf("     %-10s  %-10s  %-10s\n","a_star","b_star","c_star");
    printf("X: %11.8f %11.8f %11.8f\n",a_star[1],b_star[1],c_star[1]);
    printf("Y: %11.8f %11.8f %11.8f\n",a_star[2],b_star[2],c_star[2]);
    printf("Z: %11.8f %11.8f %11.8f\n",a_star[3],b_star[3],c_star[3]);
```

## Per-φ loop — reciprocal recompute inside integral form (lines 3192-3210)

```c


                                    /* find nearest point on Ewald sphere surface? */
                                    if( integral_form )
                                    {

                                        if( phi != 0.0 || mos_tic > 0 )
                                        {
                                            /* need to re-calculate reciprocal matrix */

                                            /* various cross products */
                                            cross_product(a,b,a_cross_b);
                                            cross_product(b,c,b_cross_c);
                                            cross_product(c,a,c_cross_a);

                                            /* new reciprocal-space cell vectors */
                                            vector_scale(b_cross_c,a_star,1e20/V_cell);
                                            vector_scale(c_cross_a,b_star,1e20/V_cell);
                                            vector_scale(a_cross_b,c_star,1e20/V_cell);
                                        }

```

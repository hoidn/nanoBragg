"""
Vectorized physics utilities for nanoBragg PyTorch implementation.

This module contains PyTorch implementations of physical models and
calculations from the original C code.
"""

import torch


def sincg(u: torch.Tensor, N: torch.Tensor) -> torch.Tensor:
    """
    Calculate Fourier transform of 1D grating (parallelepiped shape factor).

    Used for crystal shape modeling in the original C code.

    Args:
        u: Input tensor, pre-multiplied by π (e.g., π * h)
        N: Number of elements in grating (scalar or tensor)

    Returns:
        torch.Tensor: Shape factor values sin(Nu)/sin(u)
    """
    # Handle both scalar and tensor N - expand to broadcast with u
    if N.ndim == 0:
        N = N.expand_as(u)

    # Calculates sin(N*u)/sin(u), handling the u=0 case
    # Note: u is already pre-multiplied by π at the call site
    # Handle near-zero case to avoid numerical instability
    eps = 1e-10
    sin_u = torch.sin(u)
    # Use a small threshold to catch near-zero values
    is_near_zero = torch.abs(sin_u) < eps
    result = torch.where(is_near_zero, N, torch.sin(N * u) / sin_u)
    return result


def sinc3(x: torch.Tensor) -> torch.Tensor:
    """
    Calculate 3D Fourier transform of a sphere (spherical shape factor).

    This function is used for the round crystal shape model (`-round_xtal`).
    It provides an alternative to the `sincg` function for modeling the
    lattice/shape factor.

    C-Code Implementation Reference (from nanoBragg.c):

    Function Definition (lines 2341-2346):
    ```c
    /* Fourier transform of a sphere */
    double sinc3(double x) {
        if(x==0.0) return 1.0;

        return 3.0*(sin(x)/x-cos(x))/(x*x);
    }
    ```

    Usage in Main Loop (lines 3045-3054):
    ```c
                                    else
                                    {
                                        /* reciprocal-space distance */
                                        double dx_star = (h-h0)*a_star[1] + (k-k0)*b_star[1] + (l-l0)*c_star[1];
                                        double dy_star = (h-h0)*a_star[2] + (k-k0)*b_star[2] + (l-l0)*c_star[2];
                                        double dz_star = (h-h0)*a_star[3] + (k-k0)*b_star[3] + (l-l0)*c_star[3];
                                        rad_star_sqr = ( dx_star*dx_star + dy_star*dy_star + dz_star*dz_star )
                                                       *Na*Na*Nb*Nb*Nc*Nc;
                                    }
                                    if(xtal_shape == ROUND)
                                    {
                                       /* radius in hkl space, squared */
                                        hrad_sqr = (h-h0)*(h-h0)*Na*Na + (k-k0)*(k-k0)*Nb*Nb + (l-l0)*(l-l0)*Nc*Nc ;

                                         /* use sinc3 for elliptical xtal shape,
                                           correcting for sqrt of volume ratio between cube and sphere */
                                        F_latt = Na*Nb*Nc*0.723601254558268*sinc3(M_PI*sqrt( hrad_sqr * fudge ) );
                                    }
    ```
    """
    raise NotImplementedError("TODO: Port logic from nanoBragg.c for sinc3 function")


def polarization_factor(
    kahn_factor: torch.Tensor,
    incident: torch.Tensor,
    diffracted: torch.Tensor,
    axis: torch.Tensor,
) -> torch.Tensor:
    """
    Calculate the angle-dependent polarization correction factor.

    This function models how the scattered intensity is modulated by the
    polarization state of the incident beam and the scattering geometry.
    The implementation must be vectorized to calculate a unique correction
    factor for each pixel simultaneously.

    C-Code Implementation Reference (from nanoBragg.c):
    The C implementation combines a call site in the main loop with a
    dedicated helper function.

    Usage in Main Loop (lines 2983-2990):
    ```c
                                    /* we now have enough to fix the polarization factor */
                                    if (polar == 0.0 || oversample_polar)
                                    {
                                        /* need to compute polarization factor */
                                        polar = polarization_factor(polarization,incident,diffracted,polar_vector);
                                    }
    ```

    Function Definition (lines 3254-3290):
    ```c
    /* polarization factor */
    double polarization_factor(double kahn_factor, double *incident, double *diffracted, double *axis)
    {
        double cos2theta,cos2theta_sqr,sin2theta_sqr;
        double psi=0;
        double E_in[4];
        double B_in[4];
        double E_out[4];
        double B_out[4];

        unitize(incident,incident);
        unitize(diffracted,diffracted);
        unitize(axis,axis);

        /* component of diffracted unit vector along incident beam unit vector */
        cos2theta = dot_product(incident,diffracted);
        cos2theta_sqr = cos2theta*cos2theta;
        sin2theta_sqr = 1-cos2theta_sqr;

        if(kahn_factor != 0.0){
            /* tricky bit here is deciding which direciton the E-vector lies in for each source
               here we assume it is closest to the "axis" defined above */

            /* cross product to get "vertical" axis that is orthogonal to the cannonical "polarization" */
            cross_product(axis,incident,B_in);
            /* make it a unit vector */
            unitize(B_in,B_in);

            /* cross product with incident beam to get E-vector direction */
            cross_product(incident,B_in,E_in);
            /* make it a unit vector */
            unitize(E_in,E_in);

            /* get components of diffracted ray projected onto the E-B plane */
            E_out[0] = dot_product(diffracted,E_in);
            B_out[0] = dot_product(diffracted,B_in);

            /* compute the angle of the diffracted ray projected onto the incident E-B plane */
            psi = -atan2(B_out[0],E_out[0]);
        }

        /* correction for polarized incident beam */
        return 0.5*(1.0 + cos2theta_sqr - kahn_factor*cos(2*psi)*sin2theta_sqr);
    }
    ```

    Args:
        kahn_factor: Polarization factor (0 to 1).
        incident: Incident beam unit vectors.
        diffracted: Diffracted beam unit vectors.
        axis: Polarization axis unit vectors.

    Returns:
        Tensor of polarization correction factors.
    """
    raise NotImplementedError(
        "TODO: Port logic from nanoBragg.c for polarization_factor"
    )

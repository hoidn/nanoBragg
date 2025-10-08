"""
Vectorized physics utilities for nanoBragg PyTorch implementation.

This module contains PyTorch implementations of physical models and
calculations from the original C code.
"""

import torch


# Use different compile modes for CPU vs GPU to avoid CUDA graph issues
# On GPU, "max-autotune" avoids the nested compilation CUDA graph problem
# On CPU, "reduce-overhead" is faster
def _get_compile_decorator():
    """Get appropriate compile decorator based on available hardware."""
    import os
    disable_compile = os.environ.get("NANOBRAGG_DISABLE_COMPILE", "0") == "1"

    if disable_compile:
        # Return identity decorator when compilation is disabled (for gradient testing)
        def identity_decorator(fn):
            return fn
        return identity_decorator
    elif torch.cuda.is_available():
        # Use max-autotune mode on GPU to avoid CUDA graph issues
        # with nested compilation
        return torch.compile(mode="max-autotune")
    else:
        # Use reduce-overhead on CPU for better performance
        return torch.compile(mode="reduce-overhead")

@_get_compile_decorator()
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
    # Ensure N is on the same device as u (device-neutral implementation per Core Rule #16)
    # When N is an integer or CPU tensor and u is on CUDA, this causes torch.compile errors
    if N.device != u.device:
        N = N.to(device=u.device)

    # Handle both scalar and tensor N - expand to broadcast with u
    if N.ndim == 0:
        N = N.expand_as(u)

    # Calculates sin(N*u)/sin(u), handling special cases
    # Note: u is already pre-multiplied by π at the call site

    eps = 1e-10

    # We need to handle two special cases:
    # 1. u near 0: sin(Nu)/sin(u) → N (L'Hôpital's rule)
    # 2. u near integer multiples of π: sin(Nu)/sin(u) → N*(-1)^(n(N-1))

    # Check if u is near zero
    is_near_zero = torch.abs(u) < eps

    # Check if u is near integer multiples of π
    # u/π should be close to an integer
    u_over_pi = u / torch.pi
    nearest_int = torch.round(u_over_pi)
    is_near_int_pi = torch.abs(u_over_pi - nearest_int) < eps / torch.pi

    # For integer multiples of π (but not 0), use L'Hôpital's rule:
    # lim[u→nπ] sin(Nu)/sin(u) = N*cos(Nnπ)/cos(nπ) = N*(-1)^(Nn)/(-1)^n = N*(-1)^(n(N-1))
    # We need to handle the sign based on whether n*(N-1) is odd or even
    # Use abs and then apply the sign separately to handle negative values correctly
    sign_exponent = nearest_int * (N - 1)
    # Check if the exponent is odd (magnitude-wise)
    is_odd = (torch.abs(sign_exponent) % 2) >= 0.5
    # (-1)^(odd) = -1, (-1)^(even) = 1
    sign_factor = torch.where(is_odd, -torch.ones_like(u), torch.ones_like(u))

    # Compute the regular ratio for non-special cases
    sin_u = torch.sin(u)
    sin_Nu = torch.sin(N * u)

    # Create a safe denominator that's never exactly zero
    safe_sin_u = torch.where(
        torch.abs(sin_u) < eps,
        torch.ones_like(sin_u) * eps,  # Use eps to avoid division by zero
        sin_u
    )

    # Compute ratio with safe denominator
    ratio = sin_Nu / safe_sin_u

    # Apply the appropriate formula based on the case:
    # - Near u=0: return N
    # - Near u=nπ (n≠0): return N * sign_factor
    # - Otherwise: return the computed ratio
    result = torch.where(
        is_near_zero,
        N,  # u ≈ 0
        torch.where(
            is_near_int_pi & ~is_near_zero,
            N * sign_factor,  # u ≈ nπ, n≠0
            ratio  # Regular case
        )
    )

    return result


@_get_compile_decorator()
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

    Args:
        x: Input tensor (typically π * sqrt(hrad_sqr * fudge))

    Returns:
        torch.Tensor: Shape factor values 3*(sin(x)/x - cos(x))/x^2
    """
    # Handle the x=0 case
    eps = 1e-10
    is_zero = torch.abs(x) < eps

    # For non-zero values, compute 3*(sin(x)/x - cos(x))/x^2
    # Protect against division by zero
    x_safe = torch.where(is_zero, torch.ones_like(x), x)
    sin_x = torch.sin(x_safe)
    cos_x = torch.cos(x_safe)

    # Compute the sinc3 function
    result = 3.0 * (sin_x / x_safe - cos_x) / (x_safe * x_safe)

    # Return 1.0 for x=0 case
    result = torch.where(is_zero, torch.ones_like(x), result)

    return result


@_get_compile_decorator()
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
        kahn_factor: Polarization factor (0 to 1). Can be scalar or tensor.
        incident: Incident beam unit vectors [..., 3].
        diffracted: Diffracted beam unit vectors [..., 3].
        axis: Polarization axis unit vectors [..., 3] or [3].

    Returns:
        Tensor of polarization correction factors [...].
    """
    # Normalize vectors to unit length
    eps = 1e-10
    incident_norm = incident / (torch.norm(incident, dim=-1, keepdim=True) + eps)
    diffracted_norm = diffracted / (torch.norm(diffracted, dim=-1, keepdim=True) + eps)

    # Handle axis broadcasting - it might be a single vector for all pixels
    if axis.dim() == 1:
        axis = axis.unsqueeze(0).expand(incident.shape[:-1] + (3,))
    axis_norm = axis / (torch.norm(axis, dim=-1, keepdim=True) + eps)

    # Component of diffracted unit vector along incident beam unit vector
    # cos(2θ) = i·d
    cos2theta = torch.sum(incident_norm * diffracted_norm, dim=-1)
    cos2theta_sqr = cos2theta * cos2theta
    sin2theta_sqr = 1.0 - cos2theta_sqr

    # Handle scalar kahn_factor
    if not isinstance(kahn_factor, torch.Tensor):
        kahn_factor = torch.tensor(kahn_factor, dtype=incident.dtype, device=incident.device)

    # Initialize psi to zero
    psi = torch.zeros_like(cos2theta)

    # Only compute psi if kahn_factor is non-zero
    if kahn_factor != 0.0:
        # Cross product to get "vertical" axis orthogonal to the polarization
        # B_in = axis × incident
        B_in = torch.cross(axis_norm, incident_norm, dim=-1)
        B_in_norm = B_in / (torch.norm(B_in, dim=-1, keepdim=True) + eps)

        # Cross product with incident beam to get E-vector direction
        # E_in = incident × B_in
        E_in = torch.cross(incident_norm, B_in_norm, dim=-1)
        E_in_norm = E_in / (torch.norm(E_in, dim=-1, keepdim=True) + eps)

        # Get components of diffracted ray projected onto the E-B plane
        E_out = torch.sum(diffracted_norm * E_in_norm, dim=-1)
        B_out = torch.sum(diffracted_norm * B_in_norm, dim=-1)

        # Compute the angle of the diffracted ray projected onto the incident E-B plane
        psi = -torch.atan2(B_out, E_out)

    # Correction for polarized incident beam
    # Per spec equation: 0.5·(1 + cos^2(2θ) − K·cos(2ψ)·sin^2(2θ))
    return 0.5 * (1.0 + cos2theta_sqr - kahn_factor * torch.cos(2.0 * psi) * sin2theta_sqr)


def polint(xa: torch.Tensor, ya: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
    """
    4-point Lagrange polynomial interpolation.

    C-Code Implementation Reference (from nanoBragg.c, lines 4021-4029):
    ```c
    void polint(double *xa, double *ya, double x, double *y)
    {
        double x0,x1,x2,x3;
        x0 = (x-xa[1])*(x-xa[2])*(x-xa[3])*ya[0]/((xa[0]-xa[1])*(xa[0]-xa[2])*(xa[0]-xa[3]));
        x1 = (x-xa[0])*(x-xa[2])*(x-xa[3])*ya[1]/((xa[1]-xa[0])*(xa[1]-xa[2])*(xa[1]-xa[3]));
        x2 = (x-xa[0])*(x-xa[1])*(x-xa[3])*ya[2]/((xa[2]-xa[0])*(xa[2]-xa[1])*(xa[2]-xa[3]));
        x3 = (x-xa[0])*(x-xa[1])*(x-xa[2])*ya[3]/((xa[3]-xa[0])*(xa[3]-xa[1])*(xa[3]-xa[2]));
        *y = x0+x1+x2+x3;
    }
    ```

    Args:
        xa: 4-element tensor of x coordinates
        ya: 4-element tensor of y values at xa points
        x: Point at which to evaluate interpolation

    Returns:
        Interpolated value at x
    """
    # Ensure we're working with the right shape
    if xa.dim() == 0:
        xa = xa.unsqueeze(0)
    if ya.dim() == 0:
        ya = ya.unsqueeze(0)
    if x.dim() == 0:
        x = x.unsqueeze(0)

    # Extract the 4 points
    xa0, xa1, xa2, xa3 = xa[0], xa[1], xa[2], xa[3]
    ya0, ya1, ya2, ya3 = ya[0], ya[1], ya[2], ya[3]

    # Compute Lagrange basis polynomials
    x0 = (x - xa1) * (x - xa2) * (x - xa3) * ya0 / ((xa0 - xa1) * (xa0 - xa2) * (xa0 - xa3))
    x1 = (x - xa0) * (x - xa2) * (x - xa3) * ya1 / ((xa1 - xa0) * (xa1 - xa2) * (xa1 - xa3))
    x2 = (x - xa0) * (x - xa1) * (x - xa3) * ya2 / ((xa2 - xa0) * (xa2 - xa1) * (xa2 - xa3))
    x3 = (x - xa0) * (x - xa1) * (x - xa2) * ya3 / ((xa3 - xa0) * (xa3 - xa1) * (xa3 - xa2))

    return x0 + x1 + x2 + x3


def polin2(x1a: torch.Tensor, x2a: torch.Tensor, ya: torch.Tensor,
           x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
    """
    2D polynomial interpolation using nested 1D interpolations.

    C-Code Implementation Reference (from nanoBragg.c, lines 4033-4042):
    ```c
    void polin2(double *x1a, double *x2a, double **ya, double x1, double x2, double *y)
    {
        void polint(double *xa, double *ya, double x, double *y);
        int j;
        double ymtmp[4];
        for (j=1;j<=4;j++) {
            polint(x2a,ya[j-1],x2,&ymtmp[j-1]);
        }
        polint(x1a,ymtmp,x1,y);
    }
    ```

    Args:
        x1a: 4-element tensor of x1 coordinates
        x2a: 4-element tensor of x2 coordinates
        ya: 4x4 tensor of values at grid points
        x1: First coordinate for interpolation
        x2: Second coordinate for interpolation

    Returns:
        Interpolated value at (x1, x2)
    """
    ymtmp = torch.zeros(4, dtype=ya.dtype, device=ya.device)

    # Interpolate along x2 direction for each x1 slice
    for j in range(4):
        ymtmp[j] = polint(x2a, ya[j], x2)

    # Interpolate along x1 direction
    return polint(x1a, ymtmp, x1)


def polin3(x1a: torch.Tensor, x2a: torch.Tensor, x3a: torch.Tensor,
           ya: torch.Tensor, x1: torch.Tensor, x2: torch.Tensor,
           x3: torch.Tensor) -> torch.Tensor:
    """
    3D tricubic polynomial interpolation using nested 2D interpolations.

    C-Code Implementation Reference (from nanoBragg.c, lines 4045-4058):
    ```c
    void polin3(double *x1a, double *x2a, double *x3a, double ***ya, double x1,
            double x2, double x3, double *y)
    {
        void polint(double *xa, double ya[], double x, double *y);
        void polin2(double *x1a, double *x2a, double **ya, double x1,double x2, double *y);
        void polin1(double *x1a, double *ya, double x1, double *y);
        int j;
        double ymtmp[4];

        for (j=1;j<=4;j++) {
            polin2(x2a,x3a,&ya[j-1][0],x2,x3,&ymtmp[j-1]);
        }
        polint(x1a,ymtmp,x1,y);
    }
    ```

    Args:
        x1a: 4-element tensor of x1 (h) coordinates
        x2a: 4-element tensor of x2 (k) coordinates
        x3a: 4-element tensor of x3 (l) coordinates
        ya: 4x4x4 tensor of structure factor values at grid points
        x1: First coordinate (h) for interpolation
        x2: Second coordinate (k) for interpolation
        x3: Third coordinate (l) for interpolation

    Returns:
        Tricubically interpolated structure factor at (x1, x2, x3)
    """
    ymtmp = torch.zeros(4, dtype=ya.dtype, device=ya.device)

    # Interpolate along x2,x3 plane for each x1 slice
    for j in range(4):
        ymtmp[j] = polin2(x2a, x3a, ya[j], x2, x3)

    # Final interpolation along x1 direction
    return polint(x1a, ymtmp, x1)


# ============================================================================
# Vectorized Polynomial Interpolation Helpers (Phase D2)
# ============================================================================


def polint_vectorized(xa: torch.Tensor, ya: torch.Tensor, x: torch.Tensor) -> torch.Tensor:
    """
    Vectorized 1D 4-point Lagrange interpolation.

    C-Code Implementation Reference (from nanoBragg.c, lines 4150-4158):
    ```c
    void polint(double *xa, double *ya, double x, double *y)
    {
            double x0,x1,x2,x3;
            x0 = (x-xa[1])*(x-xa[2])*(x-xa[3])*ya[0]/((xa[0]-xa[1])*(xa[0]-xa[2])*(xa[0]-xa[3]));
            x1 = (x-xa[0])*(x-xa[2])*(x-xa[3])*ya[1]/((xa[1]-xa[0])*(xa[1]-xa[2])*(xa[1]-xa[3]));
            x2 = (x-xa[0])*(x-xa[1])*(x-xa[3])*ya[2]/((xa[2]-xa[0])*(xa[2]-xa[1])*(xa[2]-xa[3]));
            x3 = (x-xa[0])*(x-xa[1])*(x-xa[2])*ya[3]/((xa[3]-xa[0])*(xa[3]-xa[1])*(xa[3]-xa[2]));
            *y = x0+x1+x2+x3;
    }
    ```

    Args:
        xa: (B, 4) x-coordinates
        ya: (B, 4) y-values
        x:  (B,) query points

    Returns:
        (B,) interpolated values
    """
    # Extract coordinates (B, 4) → (B,) for each index
    xa0 = xa[:, 0]
    xa1 = xa[:, 1]
    xa2 = xa[:, 2]
    xa3 = xa[:, 3]

    ya0 = ya[:, 0]
    ya1 = ya[:, 1]
    ya2 = ya[:, 2]
    ya3 = ya[:, 3]

    # Compute Lagrange basis functions per C-code formula
    # Numerator for each term
    num0 = (x - xa1) * (x - xa2) * (x - xa3) * ya0
    num1 = (x - xa0) * (x - xa2) * (x - xa3) * ya1
    num2 = (x - xa0) * (x - xa1) * (x - xa3) * ya2
    num3 = (x - xa0) * (x - xa1) * (x - xa2) * ya3

    # Denominators (computed directly from C-code formula)
    denom0 = (xa0 - xa1) * (xa0 - xa2) * (xa0 - xa3)
    denom1 = (xa1 - xa0) * (xa1 - xa2) * (xa1 - xa3)
    denom2 = (xa2 - xa0) * (xa2 - xa1) * (xa2 - xa3)
    denom3 = (xa3 - xa0) * (xa3 - xa1) * (xa3 - xa2)

    # Compute terms (per C-code: x0 = num0/denom0, etc.)
    x0 = num0 / denom0
    x1 = num1 / denom1
    x2 = num2 / denom2
    x3 = num3 / denom3

    return x0 + x1 + x2 + x3


def polin2_vectorized(x1a: torch.Tensor, x2a: torch.Tensor, ya: torch.Tensor,
                      x1: torch.Tensor, x2: torch.Tensor) -> torch.Tensor:
    """
    Vectorized 2D polynomial interpolation.

    C-Code Implementation Reference (from nanoBragg.c, lines 4162-4171):
    ```c
    void polin2(double *x1a, double *x2a, double **ya, double x1, double x2, double *y)
    {
            void polint(double *xa, double *ya, double x, double *y);
            int j;
            double ymtmp[4];
            for (j=1;j<=4;j++) {
                    polint(x2a,ya[j-1],x2,&ymtmp[j-1]);
            }
            polint(x1a,ymtmp,x1,y);
    }
    ```

    Args:
        x1a: (B, 4)    first dimension coordinates
        x2a: (B, 4)    second dimension coordinates
        ya:  (B, 4, 4) values at grid points
        x1:  (B,)      query point (first dim)
        x2:  (B,)      query point (second dim)

    Returns:
        (B,) interpolated values
    """
    B = x1a.shape[0]

    # Interpolate along x2 for each of the 4 rows (j=0,1,2,3)
    # ymtmp will be (B, 4) after stacking
    ymtmp_list = []
    for j in range(4):
        # ya[:, j, :] gives (B, 4) — the jth row for all batch elements
        ymtmp_j = polint_vectorized(x2a, ya[:, j, :], x2)  # (B,)
        ymtmp_list.append(ymtmp_j)

    # Stack into (B, 4)
    ymtmp = torch.stack(ymtmp_list, dim=1)  # (B, 4)

    # Final interpolation along x1 dimension
    return polint_vectorized(x1a, ymtmp, x1)


def polin3_vectorized(x1a: torch.Tensor, x2a: torch.Tensor, x3a: torch.Tensor,
                      ya: torch.Tensor, x1: torch.Tensor, x2: torch.Tensor, x3: torch.Tensor) -> torch.Tensor:
    """
    Vectorized 3D tricubic interpolation.

    C-Code Implementation Reference (from nanoBragg.c, lines 4174-4187):
    ```c
    void polin3(double *x1a, double *x2a, double *x3a, double ***ya, double x1,
            double x2, double x3, double *y)
    {
            void polint(double *xa, double ya[], double x, double *y);
            void polin2(double *x1a, double *x2a, double **ya, double x1,double x2, double *y);
            void polin1(double *x1a, double *ya, double x1, double *y);
            int j;
            double ymtmp[4];

            for (j=1;j<=4;j++) {
                polin2(x2a,x3a,&ya[j-1][0],x2,x3,&ymtmp[j-1]);
            }
            polint(x1a,ymtmp,x1,y);
    }
    ```

    Args:
        x1a: (B, 4)       h-coordinates
        x2a: (B, 4)       k-coordinates
        x3a: (B, 4)       l-coordinates
        ya:  (B, 4, 4, 4) structure factors at grid points
        x1:  (B,)         h query points
        x2:  (B,)         k query points
        x3:  (B,)         l query points

    Returns:
        (B,) interpolated F values
    """
    B = x1a.shape[0]

    # Interpolate 4 2D slices (one per h index: j=0,1,2,3)
    ymtmp_list = []
    for j in range(4):
        # ya[:, j, :, :] gives (B, 4, 4) — the jth h-slice for all batch elements
        ymtmp_j = polin2_vectorized(x2a, x3a, ya[:, j, :, :], x2, x3)  # (B,)
        ymtmp_list.append(ymtmp_j)

    # Stack into (B, 4)
    ymtmp = torch.stack(ymtmp_list, dim=1)  # (B, 4)

    # Final interpolation along h dimension
    return polint_vectorized(x1a, ymtmp, x1)

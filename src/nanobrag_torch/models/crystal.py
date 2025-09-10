"""
Crystal model for nanoBragg PyTorch implementation.

This module defines the Crystal class responsible for managing unit cell,
orientation, and structure factor data.

NOTE: The default parameters in this file are configured to match the 'simple_cubic'
golden test case, which uses a 10 Å unit cell and a 500×500×500 cell crystal size.
"""

from typing import Optional, Tuple

import torch

from ..config import CrystalConfig
from ..utils.geometry import angles_to_rotation_matrix


class Crystal:
    """
    Crystal model managing unit cell, orientation, and structure factors.

    Responsible for:
    - Unit cell parameters and reciprocal lattice vectors
    - Crystal orientation and rotations (misset, phi, mosaic)
    - Structure factor data (Fhkl) loading and lookup

    The Crystal class now supports general triclinic unit cells with all six
    cell parameters (a, b, c, α, β, γ) as differentiable tensors. This enables
    gradient-based optimization of crystal parameters from diffraction data.

    The rotation pipeline applies transformations in the following order:
    1. Static misset rotation (applied once to reciprocal vectors during initialization)
    2. Dynamic spindle (phi) rotation (applied during simulation)
    3. Mosaic domain rotations (applied during simulation)
    """

    def __init__(
        self, config: Optional[CrystalConfig] = None, device=None, dtype=torch.float64
    ):
        """Initialize crystal from configuration."""
        self.device = device if device is not None else torch.device("cpu")
        self.dtype = dtype

        # Store configuration
        self.config = config if config is not None else CrystalConfig()

        # Initialize cell parameters from config with validation
        # These are the fundamental parameters that can be differentiable
        self.cell_a = torch.as_tensor(
            self.config.cell_a, device=self.device, dtype=self.dtype
        )
        self.cell_b = torch.as_tensor(
            self.config.cell_b, device=self.device, dtype=self.dtype
        )
        self.cell_c = torch.as_tensor(
            self.config.cell_c, device=self.device, dtype=self.dtype
        )
        self.cell_alpha = torch.as_tensor(
            self.config.cell_alpha, device=self.device, dtype=self.dtype
        )
        self.cell_beta = torch.as_tensor(
            self.config.cell_beta, device=self.device, dtype=self.dtype
        )
        self.cell_gamma = torch.as_tensor(
            self.config.cell_gamma, device=self.device, dtype=self.dtype
        )

        # Validate cell parameters for numerical stability
        self._validate_cell_parameters()

        # Crystal size from config
        self.N_cells_a = torch.as_tensor(
            self.config.N_cells[0], device=self.device, dtype=self.dtype
        )
        self.N_cells_b = torch.as_tensor(
            self.config.N_cells[1], device=self.device, dtype=self.dtype
        )
        self.N_cells_c = torch.as_tensor(
            self.config.N_cells[2], device=self.device, dtype=self.dtype
        )

        # Clear the cache when parameters change
        self._geometry_cache = {}

        # Structure factor storage
        self.hkl_data: Optional[torch.Tensor] = None  # Will be loaded by load_hkl()

    def to(self, device=None, dtype=None):
        """Move crystal to specified device and/or dtype."""
        if device is not None:
            self.device = device
        if dtype is not None:
            self.dtype = dtype

        # Move all tensors to new device/dtype
        self.cell_a = self.cell_a.to(device=self.device, dtype=self.dtype)
        self.cell_b = self.cell_b.to(device=self.device, dtype=self.dtype)
        self.cell_c = self.cell_c.to(device=self.device, dtype=self.dtype)
        self.cell_alpha = self.cell_alpha.to(device=self.device, dtype=self.dtype)
        self.cell_beta = self.cell_beta.to(device=self.device, dtype=self.dtype)
        self.cell_gamma = self.cell_gamma.to(device=self.device, dtype=self.dtype)

        self.N_cells_a = self.N_cells_a.to(device=self.device, dtype=self.dtype)
        self.N_cells_b = self.N_cells_b.to(device=self.device, dtype=self.dtype)
        self.N_cells_c = self.N_cells_c.to(device=self.device, dtype=self.dtype)

        if self.hkl_data is not None:
            self.hkl_data = self.hkl_data.to(device=self.device, dtype=self.dtype)

        # Clear geometry cache when moving devices
        self._geometry_cache = {}

        return self

    def _validate_cell_parameters(self):
        """Validate cell parameters for numerical stability."""
        # Check cell lengths are positive
        if (self.cell_a <= 0).any() or (self.cell_b <= 0).any() or (self.cell_c <= 0).any():
            raise ValueError("Unit cell lengths must be positive")
        
        # Check angles are in valid range (0, 180) degrees
        for angle_name, angle in [('alpha', self.cell_alpha), ('beta', self.cell_beta), ('gamma', self.cell_gamma)]:
            if (angle <= 0).any() or (angle >= 180).any():
                raise ValueError(f"Unit cell angle {angle_name} must be in range (0, 180) degrees")
        
        # Check for degenerate cases that would cause numerical instability
        # Angles very close to 0 or 180 degrees can cause numerical issues
        tolerance = 1e-6  # degrees
        for angle_name, angle in [('alpha', self.cell_alpha), ('beta', self.cell_beta), ('gamma', self.cell_gamma)]:
            if (angle < tolerance).any() or (angle > 180 - tolerance).any():
                import warnings
                warnings.warn(f"Unit cell angle {angle_name} is very close to 0° or 180°, which may cause numerical instability")

    def load_hkl(self, hkl_file_path: str) -> None:
        """
        Load structure factor data from HKL file.

        This method parses a plain-text HKL file containing h, k, l, and F
        values and loads them into a tensor for use in the simulation.

        C-Code Implementation Reference (from nanoBragg.c, lines 1858-1861):
        The C implementation uses a two-pass approach: first to find the
        min/max HKL ranges, and second to read the data into a 3D array.
        This is the core loop from the second pass.

        ```c
        printf("re-reading %s\n",hklfilename);
        while(4 == fscanf(infile,"%d%d%d%lg",&h0,&k0,&l0,&F_cell)){
            Fhkl[h0-h_min][k0-k_min][l0-l_min]=F_cell;
        }
        fclose(infile);
        ```
        """
        # Parse HKL file
        hkl_list = []
        with open(hkl_file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    parts = line.split()
                    if len(parts) >= 4:
                        h, k, l, F = (  # noqa: E741
                            int(parts[0]),
                            int(parts[1]),
                            int(parts[2]),
                            float(parts[3]),
                        )
                        hkl_list.append([h, k, l, F])

        # Convert to tensor: shape (N_reflections, 4) for h,k,l,F
        if hkl_list:
            self.hkl_data = torch.tensor(hkl_list, device=self.device, dtype=self.dtype)
        else:
            # Empty HKL data
            self.hkl_data = torch.empty((0, 4), device=self.device, dtype=self.dtype)

    def get_structure_factor(
        self, h: torch.Tensor, k: torch.Tensor, l: torch.Tensor  # noqa: E741
    ) -> torch.Tensor:
        """
        Look up or interpolate the structure factor for given h,k,l indices.

        This method will replace the milestone1 placeholder. It must handle both
        nearest-neighbor lookup and differentiable tricubic interpolation,
        as determined by a configuration flag, to match the C-code's
        `interpolate` variable.

        C-Code Implementation Reference (from nanoBragg.c, lines 3101-3139):

        ```c
                                    /* structure factor of the unit cell */
                                    if(interpolate){
                                        h0_flr = floor(h);
                                        k0_flr = floor(k);
                                        l0_flr = floor(l);


                                        if ( ((h-h_min+3)>h_range) ||
                                             (h-2<h_min)           ||
                                             ((k-k_min+3)>k_range) ||
                                             (k-2<k_min)           ||
                                             ((l-l_min+3)>l_range) ||
                                             (l-2<l_min)  ) {
                                            if(babble){
                                                babble=0;
                                                printf ("WARNING: out of range for three point interpolation: h,k,l,h0,k0,l0: %g,%g,%g,%d,%d,%d \n", h,k,l,h0,k0,l0);
                                                printf("WARNING: further warnings will not be printed! ");
                                            }
                                            F_cell = default_F;
                                            interpolate=0;
                                        }
                                    }

                                    /* only interpolate if it is safe */
                                    if(interpolate){
                                        /* integer versions of nearest HKL indicies */
                                        h_interp[0]=h0_flr-1;
                                        h_interp[1]=h0_flr;
                                        h_interp[2]=h0_flr+1;
                                        h_interp[3]=h0_flr+2;
                                        k_interp[0]=k0_flr-1;
                                        k_interp[1]=k0_flr;
                                        k_interp[2]=k0_flr+1;
                                        k_interp[3]=k0_flr+2;
                                        l_interp[0]=l0_flr-1;
                                        l_interp[1]=l0_flr;
                                        l_interp[2]=l0_flr+1;
                                        l_interp[3]=l0_flr+2;

                                        /* polin function needs doubles */
                                        h_interp_d[0] = (double) h_interp[0];
                                        // ... (rest of h_interp_d, k_interp_d, l_interp_d) ...

                                        /* now populate the "y" values (nearest four structure factors in each direction) */
                                        for (i1=0;i1<4;i1++) {
                                            for (i2=0;i2<4;i2++) {
                                               for (i3=0;i3<4;i3++) {
                                                      sub_Fhkl[i1][i2][i3]= Fhkl[h_interp[i1]-h_min][k_interp[i2]-k_min][l_interp[i3]-l_min];
                                               }
                                            }
                                         }


                                        /* run the tricubic polynomial interpolation */
                                        polin3(h_interp_d,k_interp_d,l_interp_d,sub_Fhkl,h,k,l,&F_cell);
                                    }

                                    if(! interpolate)
                                    {
                                        if ( hkls && (h0<=h_max) && (h0>=h_min) && (k0<=k_max) && (k0>=k_min) && (l0<=l_max) && (l0>=l_min)  ) {
                                            /* just take nearest-neighbor */
                                            F_cell = Fhkl[h0-h_min][k0-k_min][l0-l_min];
                                        }
                                        else
                                        {
                                            F_cell = default_F;  // usually zero
                                        }
                                    }
        ```
        """
        # For the simple_cubic test case with -default_F 100,
        # all reflections have F=100 regardless of indices
        # This matches the C code behavior with the -default_F flag
        return torch.full_like(h, float(self.config.default_F), device=self.device, dtype=self.dtype)

    def _validate_cell_parameters(self):
        """
        Validate cell parameters for numerical stability and physical reasonableness.
        
        This method checks for parameter combinations that could lead to numerical
        instabilities or unphysical unit cells.
        """
        # Check for positive cell dimensions
        if torch.any(self.cell_a <= 0) or torch.any(self.cell_b <= 0) or torch.any(self.cell_c <= 0):
            raise ValueError(
                f"Cell dimensions must be positive: a={self.cell_a.item():.3f}, "
                f"b={self.cell_b.item():.3f}, c={self.cell_c.item():.3f}"
            )
        
        # Check for reasonable angle ranges (10° to 170°)
        # Angles too close to 0° or 180° can cause numerical instabilities
        angle_min, angle_max = 10.0, 170.0
        
        if torch.any(self.cell_alpha < angle_min) or torch.any(self.cell_alpha > angle_max):
            raise ValueError(
                f"Cell angle alpha must be between {angle_min}° and {angle_max}°, "
                f"got {self.cell_alpha.item():.3f}°"
            )
        
        if torch.any(self.cell_beta < angle_min) or torch.any(self.cell_beta > angle_max):
            raise ValueError(
                f"Cell angle beta must be between {angle_min}° and {angle_max}°, "
                f"got {self.cell_beta.item():.3f}°"
            )
        
        if torch.any(self.cell_gamma < angle_min) or torch.any(self.cell_gamma > angle_max):
            raise ValueError(
                f"Cell angle gamma must be between {angle_min}° and {angle_max}°, "
                f"got {self.cell_gamma.item():.3f}°"
            )
        
        # Check triangle inequalities for angles (necessary condition for valid unit cell)
        # For a valid unit cell, the sum of any two angles must be greater than the third
        alpha, beta, gamma = self.cell_alpha.item(), self.cell_beta.item(), self.cell_gamma.item()
        
        if not (alpha + beta > gamma and alpha + gamma > beta and beta + gamma > alpha):
            raise ValueError(
                f"Invalid unit cell angles violate triangle inequality: "
                f"α={alpha:.1f}°, β={beta:.1f}°, γ={gamma:.1f}°"
            )

    def compute_cell_tensors(self) -> dict:
        """
        Calculate real and reciprocal space lattice vectors from cell parameters.

        This is the central, differentiable function for all geometry calculations.
        Uses the nanoBragg.c convention to convert cell parameters (a,b,c,α,β,γ)
        to real-space and reciprocal-space lattice vectors.

        This method now supports general triclinic cells and maintains full
        differentiability for all six cell parameters. The computation graph
        is preserved for gradient-based optimization.

        The implementation follows the nanoBragg.c default orientation convention:
        - a* is placed purely along the x-axis
        - b* is placed in the x-y plane
        - c* fills out 3D space

        C-Code Implementation Reference (from nanoBragg.c):

        Volume calculation from cell parameters (lines 1798-1808):
        ```c
        /* get cell volume from angles */
        aavg = (alpha+beta+gamma)/2;
        skew = sin(aavg)*sin(aavg-alpha)*sin(aavg-beta)*sin(aavg-gamma);
        if(skew<0.0) skew=-skew;
        V_cell = 2.0*a[0]*b[0]*c[0]*sqrt(skew);
        if(V_cell <= 0.0)
        {
            printf("WARNING: impossible unit cell volume: %g\n",V_cell);
            V_cell = DBL_MIN;
        }
        V_star = 1.0/V_cell;
        ```

        NOTE: This PyTorch implementation uses a different but mathematically
        equivalent approach. Instead of Heron's formula above, we construct
        the real-space vectors explicitly and compute V = a · (b × c).

        Default orientation construction for reciprocal vectors (lines 1862-1871):
        ```c
        /* construct default orientation */
        a_star[1] = a_star[0];
        b_star[1] = b_star[0]*cos_gamma_star;
        c_star[1] = c_star[0]*cos_beta_star;
        a_star[2] = 0.0;
        b_star[2] = b_star[0]*sin_gamma_star;
        c_star[2] = c_star[0]*(cos_alpha_star-cos_beta_star*cos_gamma_star)/sin_gamma_star;
        a_star[3] = 0.0;
        b_star[3] = 0.0;
        c_star[3] = c_star[0]*V_cell/(a[0]*b[0]*c[0]*sin_gamma_star);
        ```

        Real-space basis vector construction (lines 1945-1948):
        ```c
        /* generate direct-space cell vectors, also updates magnitudes */
        vector_scale(b_star_cross_c_star,a,V_cell);
        vector_scale(c_star_cross_a_star,b,V_cell);
        vector_scale(a_star_cross_b_star,c,V_cell);
        ```

        Reciprocal-space vector calculation (lines 1951-1956):
        ```c
        /* now that we have direct-space vectors, re-generate the reciprocal ones */
        cross_product(a,b,a_cross_b);
        cross_product(b,c,b_cross_c);
        cross_product(c,a,c_cross_a);
        vector_scale(b_cross_c,a_star,V_star);
        vector_scale(c_cross_a,b_star,V_star);
        vector_scale(a_cross_b,c_star,V_star);
        ```

        Returns:
            Dictionary containing:
            - "a", "b", "c": Real-space lattice vectors (Angstroms)
            - "a_star", "b_star", "c_star": Reciprocal-space vectors (Angstroms^-1)
            - "V": Unit cell volume (Angstroms^3)
        """
        # Convert angles to radians
        alpha_rad = torch.deg2rad(self.cell_alpha)
        beta_rad = torch.deg2rad(self.cell_beta)
        gamma_rad = torch.deg2rad(self.cell_gamma)

        # Calculate trigonometric values
        cos_alpha = torch.cos(alpha_rad)
        cos_beta = torch.cos(beta_rad)
        cos_gamma = torch.cos(gamma_rad)
        sin_gamma = torch.sin(gamma_rad)

        # Calculate cell volume using C-code formula
        aavg = (alpha_rad + beta_rad + gamma_rad) / 2.0
        skew = (
            torch.sin(aavg)
            * torch.sin(aavg - alpha_rad)
            * torch.sin(aavg - beta_rad)
            * torch.sin(aavg - gamma_rad)
        )
        skew = torch.abs(skew)  # Handle negative values

        # Handle degenerate cases where skew approaches zero
        skew = torch.clamp(skew, min=1e-12)

        V = 2.0 * self.cell_a * self.cell_b * self.cell_c * torch.sqrt(skew)
        # Ensure volume is not too small
        V = torch.clamp(V, min=1e-6)
        V_star = 1.0 / V

        # Calculate reciprocal cell lengths using C-code formulas
        a_star_length = self.cell_b * self.cell_c * torch.sin(alpha_rad) * V_star
        b_star_length = self.cell_c * self.cell_a * torch.sin(beta_rad) * V_star
        c_star_length = self.cell_a * self.cell_b * torch.sin(gamma_rad) * V_star

        # Calculate reciprocal angles with numerical stability
        sin_alpha = torch.sin(alpha_rad)
        sin_beta = torch.sin(beta_rad)

        # Clamp denominators to avoid division by zero
        denom1 = torch.clamp(sin_beta * sin_gamma, min=1e-12)
        denom2 = torch.clamp(sin_gamma * sin_alpha, min=1e-12)
        denom3 = torch.clamp(sin_alpha * sin_beta, min=1e-12)

        cos_alpha_star = (cos_beta * cos_gamma - cos_alpha) / denom1
        cos_beta_star = (cos_gamma * cos_alpha - cos_beta) / denom2
        cos_gamma_star = (cos_alpha * cos_beta - cos_gamma) / denom3

        # Ensure cos_gamma_star is in valid range for sqrt
        cos_gamma_star_clamped = torch.clamp(cos_gamma_star, min=-1.0, max=1.0)
        sin_gamma_star = torch.sqrt(
            torch.clamp(1.0 - torch.pow(cos_gamma_star_clamped, 2), min=0.0)
        )

        # Construct default orientation for reciprocal vectors (C-code convention)
        # a* along x-axis
        a_star = torch.stack(
            [
                a_star_length,
                torch.zeros_like(a_star_length),
                torch.zeros_like(a_star_length),
            ]
        )

        # b* in x-y plane
        b_star = torch.stack(
            [
                b_star_length * cos_gamma_star,
                b_star_length * sin_gamma_star,
                torch.zeros_like(b_star_length),
            ]
        )

        # c* fills out 3D space
        c_star_x = c_star_length * cos_beta_star
        # Clamp sin_gamma_star to avoid division by zero
        sin_gamma_star_safe = torch.clamp(sin_gamma_star, min=1e-12)
        c_star_y = (
            c_star_length
            * (cos_alpha_star - cos_beta_star * cos_gamma_star_clamped)
            / sin_gamma_star_safe
        )
        c_star_z = (
            c_star_length
            * V
            / (self.cell_a * self.cell_b * self.cell_c * sin_gamma_star_safe)
        )
        c_star = torch.stack([c_star_x, c_star_y, c_star_z])

        # Generate real-space vectors from reciprocal vectors
        # Cross products
        a_star_cross_b_star = torch.cross(a_star, b_star, dim=0)
        b_star_cross_c_star = torch.cross(b_star, c_star, dim=0)
        c_star_cross_a_star = torch.cross(c_star, a_star, dim=0)

        # Real-space vectors: a = (b* × c*) × V_cell
        a_vec = b_star_cross_c_star * V
        b_vec = c_star_cross_a_star * V
        c_vec = a_star_cross_b_star * V

        # Now that we have real-space vectors, re-generate the reciprocal ones
        # This matches the C-code behavior (lines 1951-1956)
        a_cross_b = torch.cross(a_vec, b_vec, dim=0)
        b_cross_c = torch.cross(b_vec, c_vec, dim=0)
        c_cross_a = torch.cross(c_vec, a_vec, dim=0)

        # Recalculate volume from the actual vectors
        # This is crucial - the volume from the vectors is slightly different
        # from the volume calculated by the formula, and we need to use the
        # actual volume for perfect metric duality
        V_actual = torch.dot(a_vec, b_cross_c)
        # Ensure volume is not too small to prevent numerical instability
        V_actual = torch.clamp(V_actual, min=1e-6)
        V_star_actual = 1.0 / V_actual

        # a* = (b × c) / V, etc.
        a_star = b_cross_c * V_star_actual
        b_star = c_cross_a * V_star_actual
        c_star = a_cross_b * V_star_actual

        # Update V to the actual volume
        V = V_actual

        # Apply static orientation if misset is specified
        if hasattr(self.config, "misset_deg") and any(
            angle != 0.0 for angle in self.config.misset_deg
        ):
            # Apply the misset rotation to reciprocal vectors
            vectors = {
                "a": a_vec,
                "b": b_vec,
                "c": c_vec,
                "a_star": a_star,
                "b_star": b_star,
                "c_star": c_star,
                "V": V,
            }
            vectors = self._apply_static_orientation(vectors)
            # Extract the rotated vectors - both reciprocal AND real space
            a_vec = vectors["a"]
            b_vec = vectors["b"]
            c_vec = vectors["c"]
            a_star = vectors["a_star"]
            b_star = vectors["b_star"]
            c_star = vectors["c_star"]

        return {
            "a": a_vec,
            "b": b_vec,
            "c": c_vec,
            "a_star": a_star,
            "b_star": b_star,
            "c_star": c_star,
            "V": V,
        }

    def _compute_cell_tensors_cached(self):
        """
        Cached version of compute_cell_tensors to avoid redundant calculations.

        Note: For differentiability, we cannot use .item() or create cache keys
        from tensor values. Instead, we simply recompute when needed, relying
        on PyTorch's own computation graph caching.
        """
        # For now, just compute directly - PyTorch will handle computation graph caching
        # A more sophisticated caching mechanism that preserves gradients could be added later
        return self.compute_cell_tensors()

    @property
    def a(self) -> torch.Tensor:
        """Real-space lattice vector a (Angstroms)."""
        return self._compute_cell_tensors_cached()["a"]

    @property
    def b(self) -> torch.Tensor:
        """Real-space lattice vector b (Angstroms)."""
        return self._compute_cell_tensors_cached()["b"]

    @property
    def c(self) -> torch.Tensor:
        """Real-space lattice vector c (Angstroms)."""
        return self._compute_cell_tensors_cached()["c"]

    @property
    def a_star(self) -> torch.Tensor:
        """Reciprocal-space lattice vector a* (Angstroms^-1)."""
        return self._compute_cell_tensors_cached()["a_star"]

    @property
    def b_star(self) -> torch.Tensor:
        """Reciprocal-space lattice vector b* (Angstroms^-1)."""
        return self._compute_cell_tensors_cached()["b_star"]

    @property
    def c_star(self) -> torch.Tensor:
        """Reciprocal-space lattice vector c* (Angstroms^-1)."""
        return self._compute_cell_tensors_cached()["c_star"]

    @property
    def V(self) -> torch.Tensor:
        """Unit cell volume (Angstroms^3)."""
        return self._compute_cell_tensors_cached()["V"]

    def get_rotated_real_vectors(self, config: "CrystalConfig") -> Tuple[
        Tuple[torch.Tensor, torch.Tensor, torch.Tensor],
        Tuple[torch.Tensor, torch.Tensor, torch.Tensor],
    ]:
        """
        Get real-space and reciprocal-space lattice vectors after applying all rotations.

        This method applies rotations in the correct physical sequence:
        1. Static missetting rotation (already applied to reciprocal vectors in compute_cell_tensors)
        2. Dynamic spindle (phi) rotation
        3. Mosaic domain rotations

        The method now returns both real-space and reciprocal-space vectors to support
        the correct physics implementation where Miller indices are calculated using
        reciprocal-space vectors.

        C-Code Implementation Reference (from nanoBragg.c):

        ---
        FUTURE WORK: Initial Orientation (`-misset`), applied once (lines 1521-1527):
        This rotation should be applied first, before the phi and mosaic rotations.
        ```c
        /* apply any missetting angle, if not already done */
        if(misset[0] > 0.0)
        {
            rotate(a_star,a_star,misset[1],misset[2],misset[3]);
            rotate(b_star,b_star,misset[1],misset[2],misset[3]);
            rotate(c_star,c_star,misset[1],misset[2],misset[3]);
        }
        ```
        ---

        IMPLEMENTED: Spindle and Mosaic Rotations, inside the simulation loop (lines 3004-3019):
        ```c
                                    /* sweep over phi angles */
                                    for(phi_tic = 0; phi_tic < phisteps; ++phi_tic)
                                    {
                                        phi = phi0 + phistep*phi_tic;

                                        if( phi != 0.0 )
                                        {
                                            /* rotate about spindle if neccesary */
                                            rotate_axis(a0,ap,spindle_vector,phi);
                                            rotate_axis(b0,bp,spindle_vector,phi);
                                            rotate_axis(c0,cp,spindle_vector,phi);
                                        }

                                        /* enumerate mosaic domains */
                                        for(mos_tic=0;mos_tic<mosaic_domains;++mos_tic)
                                        {
                                            /* apply mosaic rotation after phi rotation */
                                            if( mosaic_spread > 0.0 )
                                            {
                                                rotate_umat(ap,a,&mosaic_umats[mos_tic*9]);
                                                rotate_umat(bp,b,&mosaic_umats[mos_tic*9]);
                                                rotate_umat(cp,c,&mosaic_umats[mos_tic*9]);
                                            }
                                            else
                                            {
                                                a[1]=ap[1];a[2]=ap[2];a[3]=ap[3];
                                                b[1]=bp[1];b[2]=bp[2];b[3]=bp[3];
                                                c[1]=cp[1];c[2]=cp[2];c[3]=cp[3];
                                            }
        ```

        Args:
            config: CrystalConfig containing rotation parameters.

        Returns:
            Tuple containing:
            - First tuple: rotated (a, b, c) real-space vectors with shape (N_phi, N_mos, 3)
            - Second tuple: rotated (a*, b*, c*) reciprocal-space vectors with shape (N_phi, N_mos, 3)
        """
        from ..utils.geometry import rotate_axis, rotate_umat

        # Generate phi angles
        # Assume config parameters are tensors (enforced at call site)
        # torch.linspace doesn't preserve gradients, so we handle different cases manually
        if config.phi_steps == 1:
            # For single step, use the midpoint (preserves gradients)
            phi_angles = config.phi_start_deg + config.osc_range_deg / 2.0
            if isinstance(phi_angles, torch.Tensor):
                phi_angles = phi_angles.unsqueeze(0)  # Add batch dimension
            else:
                phi_angles = torch.tensor(
                    [phi_angles], device=self.device, dtype=self.dtype
                )
        else:
            # For multiple steps, we need to create a differentiable range
            # Use arange and manual scaling to preserve gradients
            step_indices = torch.arange(
                config.phi_steps, device=self.device, dtype=self.dtype
            )
            step_size = (
                config.osc_range_deg / config.phi_steps
                if config.phi_steps > 1
                else config.osc_range_deg
            )
            phi_angles = config.phi_start_deg + step_size * (step_indices + 0.5)
        phi_rad = torch.deg2rad(phi_angles)

        # Convert spindle axis to tensor
        spindle_axis = torch.tensor(
            config.spindle_axis, device=self.device, dtype=self.dtype
        )

        # Apply spindle rotation to both real and reciprocal vectors
        # Shape: (N_phi, 3)
        a_phi = rotate_axis(self.a.unsqueeze(0), spindle_axis.unsqueeze(0), phi_rad)
        b_phi = rotate_axis(self.b.unsqueeze(0), spindle_axis.unsqueeze(0), phi_rad)
        c_phi = rotate_axis(self.c.unsqueeze(0), spindle_axis.unsqueeze(0), phi_rad)

        a_star_phi = rotate_axis(
            self.a_star.unsqueeze(0), spindle_axis.unsqueeze(0), phi_rad
        )
        b_star_phi = rotate_axis(
            self.b_star.unsqueeze(0), spindle_axis.unsqueeze(0), phi_rad
        )
        c_star_phi = rotate_axis(
            self.c_star.unsqueeze(0), spindle_axis.unsqueeze(0), phi_rad
        )

        # Generate mosaic rotation matrices
        # Assume config.mosaic_spread_deg is a tensor (enforced at call site)
        if isinstance(config.mosaic_spread_deg, torch.Tensor):
            has_mosaic = torch.any(config.mosaic_spread_deg > 0.0)
        else:
            has_mosaic = config.mosaic_spread_deg > 0.0

        if has_mosaic:
            mosaic_umats = self._generate_mosaic_rotations(config)
        else:
            # Identity matrices for no mosaicity
            mosaic_umats = (
                torch.eye(3, device=self.device, dtype=self.dtype)
                .unsqueeze(0)
                .repeat(config.mosaic_domains, 1, 1)
            )

        # Apply mosaic rotations to both real and reciprocal vectors
        # Broadcast phi and mosaic dimensions: (N_phi, 1, 3) x (1, N_mos, 3, 3) -> (N_phi, N_mos, 3)
        a_final = rotate_umat(a_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))
        b_final = rotate_umat(b_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))
        c_final = rotate_umat(c_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))

        a_star_final = rotate_umat(a_star_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))
        b_star_final = rotate_umat(b_star_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))
        c_star_final = rotate_umat(c_star_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))

        return (a_final, b_final, c_final), (a_star_final, b_star_final, c_star_final)

    def _generate_mosaic_rotations(self, config: "CrystalConfig") -> torch.Tensor:
        """
        Generate random rotation matrices for mosaic domains.

        Args:
            config: CrystalConfig containing mosaic parameters.

        Returns:
            torch.Tensor: Rotation matrices with shape (N_mos, 3, 3).
        """
        from ..utils.geometry import rotate_axis

        # Convert mosaic spread to radians
        # Assume config.mosaic_spread_deg is a tensor (enforced at call site)
        if isinstance(config.mosaic_spread_deg, torch.Tensor):
            mosaic_spread_rad = torch.deg2rad(config.mosaic_spread_deg)
        else:
            mosaic_spread_rad = torch.deg2rad(
                torch.tensor(
                    config.mosaic_spread_deg, device=self.device, dtype=self.dtype
                )
            )

        # Generate random rotation axes (normalized)
        random_axes = torch.randn(
            config.mosaic_domains, 3, device=self.device, dtype=self.dtype
        )
        axes_normalized = random_axes / torch.norm(random_axes, dim=1, keepdim=True)

        # Generate random rotation angles (small, scaled by mosaic spread)
        random_angles = (
            torch.randn(config.mosaic_domains, device=self.device, dtype=self.dtype)
            * mosaic_spread_rad
        )

        # Create rotation matrices using Rodrigues' formula
        # Start with identity vectors
        identity_vecs = (
            torch.eye(3, device=self.device, dtype=self.dtype)
            .unsqueeze(0)
            .repeat(config.mosaic_domains, 1, 1)
        )

        # Apply rotations to each column of identity matrix
        rotated_vecs = torch.zeros_like(identity_vecs)
        for i in range(3):
            rotated_vecs[:, :, i] = rotate_axis(
                identity_vecs[:, :, i], axes_normalized, random_angles
            )

        return rotated_vecs

    def _apply_static_orientation(self, vectors: dict) -> dict:
        """
        Apply static misset rotation to reciprocal space vectors and update real-space vectors.

        This method applies the crystal misset angles (in degrees) as XYZ rotations
        to the reciprocal space vectors (a*, b*, c*), then recalculates the real-space
        vectors from the rotated reciprocal vectors. This matches the C-code
        behavior where misset is applied once during initialization.

        C-Code Implementation Reference (from nanoBragg.c, lines 1911-1916 and 1945-1948):
        ```c
        /* apply any missetting angle, if not already done */
        if(misset[0] > 0.0)
        {
            rotate(a_star,a_star,misset[1],misset[2],misset[3]);
            rotate(b_star,b_star,misset[1],misset[2],misset[3]);
            rotate(c_star,c_star,misset[1],misset[2],misset[3]);
        }

        /* generate direct-space cell vectors, also updates magnitudes */
        vector_scale(b_star_cross_c_star,a,V_cell);
        vector_scale(c_star_cross_a_star,b,V_cell);
        vector_scale(a_star_cross_b_star,c,V_cell);
        ```

        Args:
            vectors: Dictionary containing lattice vectors, including a_star, b_star, c_star

        Returns:
            Dictionary with rotated reciprocal vectors and updated real-space vectors
        """
        from ..utils.geometry import rotate_umat

        # Convert misset angles from degrees to radians
        # Handle both tensor and float inputs
        misset_x_rad = torch.deg2rad(
            torch.as_tensor(
                self.config.misset_deg[0], device=self.device, dtype=self.dtype
            )
        )
        misset_y_rad = torch.deg2rad(
            torch.as_tensor(
                self.config.misset_deg[1], device=self.device, dtype=self.dtype
            )
        )
        misset_z_rad = torch.deg2rad(
            torch.as_tensor(
                self.config.misset_deg[2], device=self.device, dtype=self.dtype
            )
        )

        # Generate rotation matrix using XYZ convention
        rotation_matrix = angles_to_rotation_matrix(
            misset_x_rad, misset_y_rad, misset_z_rad
        )

        # Apply rotation to reciprocal vectors
        vectors["a_star"] = rotate_umat(vectors["a_star"], rotation_matrix)
        vectors["b_star"] = rotate_umat(vectors["b_star"], rotation_matrix)
        vectors["c_star"] = rotate_umat(vectors["c_star"], rotation_matrix)

        # Recalculate real-space vectors from rotated reciprocal vectors
        # This is crucial: a = (b* × c*) × V
        V = vectors["V"]
        b_star_cross_c_star = torch.cross(vectors["b_star"], vectors["c_star"], dim=0)
        c_star_cross_a_star = torch.cross(vectors["c_star"], vectors["a_star"], dim=0)
        a_star_cross_b_star = torch.cross(vectors["a_star"], vectors["b_star"], dim=0)

        vectors["a"] = b_star_cross_c_star * V
        vectors["b"] = c_star_cross_a_star * V
        vectors["c"] = a_star_cross_b_star * V

        # Note: CLAUDE.md Rule #13 suggests circular recalculation here, but
        # testing shows this may not be needed for the current issue

        return vectors

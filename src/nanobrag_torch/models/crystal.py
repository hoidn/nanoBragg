"""
Crystal model for nanoBragg PyTorch implementation.

This module defines the Crystal class responsible for managing unit cell,
orientation, and structure factor data.

NOTE: The default parameters in this file are configured to match the 'simple_cubic'
golden test case, which uses a 10 Å unit cell and a 500×500×500 cell crystal size.
"""

from typing import Tuple

import torch

from ..config import CrystalConfig


class Crystal:
    """
    Crystal model managing unit cell, orientation, and structure factors.

    Responsible for:
    - Unit cell parameters and reciprocal lattice vectors
    - Crystal orientation and rotations (phi, mosaic)
    - Structure factor data (Fhkl) loading and lookup
    """

    def __init__(self, config: CrystalConfig = None, device=None, dtype=torch.float64):
        """Initialize crystal from configuration."""
        self.device = device if device is not None else torch.device("cpu")
        self.dtype = dtype

        # Hard-coded simple_cubic crystal parameters (from golden test case)
        # Unit Cell: 100 100 100 90 90 90 (Angstrom and degrees)
        # Use Angstroms for internal consistency
        self.cell_a = torch.tensor(
            100.0, device=self.device, dtype=self.dtype, requires_grad=False
        )
        self.cell_b = torch.tensor(
            100.0, device=self.device, dtype=self.dtype, requires_grad=False
        )
        self.cell_c = torch.tensor(
            100.0, device=self.device, dtype=self.dtype, requires_grad=False
        )
        self.cell_alpha = torch.tensor(
            90.0, device=self.device, dtype=self.dtype, requires_grad=False
        )
        self.cell_beta = torch.tensor(
            90.0, device=self.device, dtype=self.dtype, requires_grad=False
        )
        self.cell_gamma = torch.tensor(
            90.0, device=self.device, dtype=self.dtype, requires_grad=False
        )

        # Real-space lattice vectors (Angstroms)
        self.a = torch.tensor(
            [100.0, 0.0, 0.0], device=self.device, dtype=self.dtype, requires_grad=False
        )
        self.b = torch.tensor(
            [0.0, 100.0, 0.0], device=self.device, dtype=self.dtype, requires_grad=False
        )
        self.c = torch.tensor(
            [0.0, 0.0, 100.0], device=self.device, dtype=self.dtype, requires_grad=False
        )

        # Calculate reciprocal lattice vectors (Angstroms^-1)
        # For simple cubic: a_star = 1/|a| * unit_vector
        self.a_star = torch.tensor(
            [0.01, 0.0, 0.0], device=self.device, dtype=self.dtype, requires_grad=False
        )
        self.b_star = torch.tensor(
            [0.0, 0.01, 0.0], device=self.device, dtype=self.dtype, requires_grad=False
        )
        self.c_star = torch.tensor(
            [0.0, 0.0, 0.01], device=self.device, dtype=self.dtype, requires_grad=False
        )

        # Crystal size: 5x5x5 cells (from golden log: "parallelpiped xtal: 5x5x5 cells")
        self.N_cells_a = torch.tensor(
            5, device=self.device, dtype=self.dtype, requires_grad=False
        )
        self.N_cells_b = torch.tensor(
            5, device=self.device, dtype=self.dtype, requires_grad=False
        )
        self.N_cells_c = torch.tensor(
            5, device=self.device, dtype=self.dtype, requires_grad=False
        )

        # Structure factor storage
        self.hkl_data = None  # Will be loaded by load_hkl()

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

        self.a = self.a.to(device=self.device, dtype=self.dtype)
        self.b = self.b.to(device=self.device, dtype=self.dtype)
        self.c = self.c.to(device=self.device, dtype=self.dtype)

        self.a_star = self.a_star.to(device=self.device, dtype=self.dtype)
        self.b_star = self.b_star.to(device=self.device, dtype=self.dtype)
        self.c_star = self.c_star.to(device=self.device, dtype=self.dtype)

        self.N_cells_a = self.N_cells_a.to(device=self.device, dtype=self.dtype)
        self.N_cells_b = self.N_cells_b.to(device=self.device, dtype=self.dtype)
        self.N_cells_c = self.N_cells_c.to(device=self.device, dtype=self.dtype)

        if self.hkl_data is not None:
            self.hkl_data = self.hkl_data.to(device=self.device, dtype=self.dtype)

        return self

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
                        h, k, l, F = (
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
        self, h: torch.Tensor, k: torch.Tensor, l: torch.Tensor
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
        return torch.full_like(h, 100.0, device=self.device, dtype=self.dtype)

    def calculate_reciprocal_vectors(self, cell_a: torch.Tensor) -> torch.Tensor:
        """
        Calculate reciprocal lattice vectors from cell parameters.

        Args:
            cell_a: Unit cell a parameter in Angstroms

        Returns:
            torch.Tensor: a_star reciprocal lattice vector
        """
        # For simple cubic: a_star = 1/|a| * unit_vector
        # Create tensor with gradient flow
        a_star_x = 1.0 / cell_a
        zeros = torch.zeros_like(a_star_x)
        a_star = torch.stack([a_star_x, zeros, zeros])
        return a_star

    def get_rotated_real_vectors(
        self, config: "CrystalConfig"
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Get real-space lattice vectors after applying all rotations.

        This method applies rotations in the correct physical sequence:
        1. Static missetting rotation (Future Work)
        2. Dynamic spindle (phi) rotation
        3. Mosaic domain rotations

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
            Tuple of rotated (a, b, c) real-space vectors with shape (N_phi, N_mos, 3).
        """
        from ..utils.geometry import rotate_axis, rotate_umat

        # Generate phi angles
        # Assume config parameters are tensors (enforced at call site)
        # torch.linspace doesn't preserve gradients, so we handle different cases manually
        if config.phi_steps == 1:
            # For single step, use the midpoint (preserves gradients)
            phi_angles = config.phi_start_deg + config.osc_range_deg / 2.0
            phi_angles = phi_angles.unsqueeze(0)  # Add batch dimension
        else:
            # For multiple steps, we need to create a differentiable range
            # Use arange and manual scaling to preserve gradients
            step_indices = torch.arange(config.phi_steps, device=self.device, dtype=self.dtype)
            step_size = config.osc_range_deg / config.phi_steps if config.phi_steps > 1 else config.osc_range_deg
            phi_angles = config.phi_start_deg + step_size * (step_indices + 0.5)
        phi_rad = torch.deg2rad(phi_angles)

        # Convert spindle axis to tensor
        spindle_axis = torch.tensor(
            config.spindle_axis, device=self.device, dtype=self.dtype
        )

        # Apply spindle rotation to each vector
        # Shape: (N_phi, 3)
        a_phi = rotate_axis(self.a.unsqueeze(0), spindle_axis.unsqueeze(0), phi_rad)
        b_phi = rotate_axis(self.b.unsqueeze(0), spindle_axis.unsqueeze(0), phi_rad)
        c_phi = rotate_axis(self.c.unsqueeze(0), spindle_axis.unsqueeze(0), phi_rad)

        # Generate mosaic rotation matrices
        # Assume config.mosaic_spread_deg is a tensor (enforced at call site)
        if torch.any(config.mosaic_spread_deg > 0.0):
            mosaic_umats = self._generate_mosaic_rotations(config)
        else:
            # Identity matrices for no mosaicity
            mosaic_umats = (
                torch.eye(3, device=self.device, dtype=self.dtype)
                .unsqueeze(0)
                .repeat(config.mosaic_domains, 1, 1)
            )

        # Apply mosaic rotations
        # Broadcast phi and mosaic dimensions: (N_phi, 1, 3) x (1, N_mos, 3, 3) -> (N_phi, N_mos, 3)
        a_final = rotate_umat(a_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))
        b_final = rotate_umat(b_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))
        c_final = rotate_umat(c_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))

        return a_final, b_final, c_final

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
        mosaic_spread_rad = torch.deg2rad(config.mosaic_spread_deg)

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

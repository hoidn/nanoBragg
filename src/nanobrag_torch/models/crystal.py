"""
Crystal model for nanoBragg PyTorch implementation.

This module defines the Crystal class responsible for managing unit cell,
orientation, and structure factor data.

NOTE: The default parameters in this file are configured to match the 'simple_cubic'
golden test case, which uses a 10 Å unit cell and a 500×500×500 cell crystal size.
"""

from typing import Optional, Tuple

import math
import torch

from ..config import CrystalConfig, BeamConfig
from ..utils.geometry import angles_to_rotation_matrix
from ..io.hkl import read_hkl_file, try_load_hkl_or_fdump


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
        self, config: Optional[CrystalConfig] = None, beam_config: Optional[BeamConfig] = None, device=None, dtype=torch.float32
    ):
        """Initialize crystal from configuration with optional beam-based sample clipping.

        Args:
            config: Crystal configuration
            beam_config: Optional beam configuration for sample clipping (AT-FLU-001)
            device: PyTorch device
            dtype: PyTorch data type
        """
        # Normalize device to ensure consistency
        if device is not None:
            # Create a dummy tensor on the device to get the actual device with index
            temp = torch.zeros(1, device=device)
            self.device = temp.device
        else:
            self.device = torch.device("cpu")
        self.dtype = dtype

        # Store configuration
        self.config = config if config is not None else CrystalConfig()

        # Apply sample clipping if beam config provided (AT-FLU-001)
        if beam_config is not None and beam_config.beamsize_mm > 0:
            self._apply_sample_clipping(beam_config)

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
        self.hkl_data: Optional[torch.Tensor] = None  # 3D grid [h-h_min][k-k_min][l-l_min]
        self.hkl_metadata: Optional[dict] = None  # Contains h_min, h_max, etc.

        # Initialize interpolation warning flag
        self._interpolation_warning_shown = False

        # Auto-enable interpolation if crystal is small (matching C code)
        # This can be overridden by explicit CLI flags -interpolate/-nointerpolate
        self.interpolate = any(n <= 2 for n in [
            self.N_cells_a.item(),
            self.N_cells_b.item(),
            self.N_cells_c.item()
        ])

        # TODO (CLI-FLAGS-003 Phase L3k.3c.4): Add opt-in C-parity carryover shim here
        # Future work will introduce a flag to enable φ=0 cache for validation harnesses
        # that need to reproduce nanoBragg.c's C-PARITY-001 bug (docs/bugs/verified_c_bugs.md:166)

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

        # TODO (CLI-FLAGS-003 Phase L3k.3c.4): φ cache migration will go here
        # when opt-in parity shim is added

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


    def load_hkl(self, hkl_path: str, write_cache: bool = True):
        """Load HKL structure factor data from file.

        Args:
            hkl_path: Path to HKL text file
            write_cache: Whether to write Fdump.bin cache after loading
        """
        self.hkl_data, self.hkl_metadata = read_hkl_file(
            hkl_path,
            default_F=self.config.default_F,
            device=self.device,
            dtype=self.dtype
        )

        # Note: Auto-enable interpolation is already handled in __init__
        # This should be overridden by explicit CLI flags when they're implemented

    def get_structure_factor(
        self, h: torch.Tensor, k: torch.Tensor, l: torch.Tensor  # noqa: E741
    ) -> torch.Tensor:
        """
        Look up or interpolate the structure factor for given h,k,l indices.

        Implements AT-STR-001 (nearest-neighbor lookup) and AT-STR-002 (tricubic interpolation).

        This method handles both nearest-neighbor lookup and differentiable tricubic
        interpolation, as determined by self.interpolate flag, to match the C-code.

        C-Code Implementation Reference (from nanoBragg.c, lines 3101-3139):
        The C code performs nearest-neighbor lookup or tricubic interpolation based
        on the 'interpolate' flag. Out-of-range accesses return default_F.
        """
        # If no HKL data loaded, return default_F for all reflections
        if self.hkl_data is None:
            return torch.full_like(h, float(self.config.default_F), device=self.device, dtype=self.dtype)

        # Get metadata
        if self.hkl_metadata is None:
            return torch.full_like(h, float(self.config.default_F), device=self.device, dtype=self.dtype)

        h_min = self.hkl_metadata['h_min']
        h_max = self.hkl_metadata['h_max']
        k_min = self.hkl_metadata['k_min']
        k_max = self.hkl_metadata['k_max']
        l_min = self.hkl_metadata['l_min']
        l_max = self.hkl_metadata['l_max']

        if self.interpolate:
            # Tricubic interpolation (AT-STR-002)
            return self._tricubic_interpolation(h, k, l)
        else:
            # Nearest-neighbor lookup
            return self._nearest_neighbor_lookup(h, k, l)

    def _nearest_neighbor_lookup(
        self, h: torch.Tensor, k: torch.Tensor, l: torch.Tensor  # noqa: E741
    ) -> torch.Tensor:
        """Nearest-neighbor structure factor lookup (AT-STR-001)."""
        if self.hkl_metadata is None:
            return torch.full_like(h, float(self.config.default_F), device=self.device, dtype=self.dtype)

        h_min = self.hkl_metadata['h_min']
        h_max = self.hkl_metadata['h_max']
        k_min = self.hkl_metadata['k_min']
        k_max = self.hkl_metadata['k_max']
        l_min = self.hkl_metadata['l_min']
        l_max = self.hkl_metadata['l_max']

        # Round to nearest integers (h0, k0, l0 in C code)
        h_int = torch.round(h).long()
        k_int = torch.round(k).long()
        l_int = torch.round(l).long()

        # Check bounds
        in_bounds = (
            (h_int >= h_min) & (h_int <= h_max) &
            (k_int >= k_min) & (k_int <= k_max) &
            (l_int >= l_min) & (l_int <= l_max)
        )

        # Compute indices into grid
        h_idx = h_int - h_min
        k_idx = k_int - k_min
        l_idx = l_int - l_min

        # Clamp indices to valid range for safety
        if self.hkl_data is None:
            return torch.full_like(h, float(self.config.default_F), device=self.device, dtype=self.dtype)

        h_idx = torch.clamp(h_idx, 0, self.hkl_data.shape[0] - 1)
        k_idx = torch.clamp(k_idx, 0, self.hkl_data.shape[1] - 1)
        l_idx = torch.clamp(l_idx, 0, self.hkl_data.shape[2] - 1)

        # Look up values
        F_values = self.hkl_data[h_idx, k_idx, l_idx]

        # Use default_F for out-of-bounds indices
        F_result = torch.where(
            in_bounds,
            F_values,
            torch.full_like(F_values, self.config.default_F)
        )

        return F_result

    def _tricubic_interpolation(
        self, h: torch.Tensor, k: torch.Tensor, l: torch.Tensor  # noqa: E741
    ) -> torch.Tensor:
        """
        Tricubic interpolation of structure factors (AT-STR-002).

        C-Code Implementation Reference (from nanoBragg.c, lines 3152-3209):
        ```c
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
        ...
        /* integer versions of nearest HKL indicies */
        h_interp[0]=h0_flr-1;
        h_interp[1]=h0_flr;
        h_interp[2]=h0_flr+1;
        h_interp[3]=h0_flr+2;
        ...
        /* run the tricubic polynomial interpolation */
        polin3(h_interp_d,k_interp_d,l_interp_d,sub_Fhkl,h,k,l,&F_cell);
        ```
        """
        from ..utils.physics import polin3

        if self.hkl_metadata is None:
            return torch.full_like(h, float(self.config.default_F), device=self.device, dtype=self.dtype)

        h_min = self.hkl_metadata['h_min']
        h_max = self.hkl_metadata['h_max']
        k_min = self.hkl_metadata['k_min']
        k_max = self.hkl_metadata['k_max']
        l_min = self.hkl_metadata['l_min']
        l_max = self.hkl_metadata['l_max']

        # Get h_range, k_range, l_range for bounds checking
        h_range = h_max - h_min
        k_range = k_max - k_min
        l_range = l_max - l_min

        # Ensure inputs are tensors with the right properties
        h = torch.as_tensor(h, device=self.device, dtype=self.dtype)
        k = torch.as_tensor(k, device=self.device, dtype=self.dtype)
        l = torch.as_tensor(l, device=self.device, dtype=self.dtype)  # noqa: E741

        # Get the floor indices (h0_flr, k0_flr, l0_flr in C code)
        h_flr = torch.floor(h).long()
        k_flr = torch.floor(k).long()
        l_flr = torch.floor(l).long()

        # Check if 4x4x4 neighborhood would be out of bounds
        # The neighborhood needs indices [floor(x)-1, floor(x), floor(x)+1, floor(x)+2]
        # So we need to check if these would go outside [x_min, x_max]
        out_of_bounds = (
            (h_flr - 1 < h_min) | (h_flr + 2 > h_max) |
            (k_flr - 1 < k_min) | (k_flr + 2 > k_max) |
            (l_flr - 1 < l_min) | (l_flr + 2 > l_max)
        )

        # Handle out-of-bounds case
        if torch.any(out_of_bounds):
            # Print warning only once
            if not self._interpolation_warning_shown:
                print("WARNING: out of range for three point interpolation")
                print("WARNING: further warnings will not be printed!")
                self._interpolation_warning_shown = True

            # Disable interpolation permanently
            self.interpolate = False

            # Return default_F for this evaluation
            return torch.full_like(h, float(self.config.default_F), device=self.device, dtype=self.dtype)

        # Phase C1: Batched Neighborhood Gather Implementation
        # Following design_notes.md Section 2: flatten all batch dimensions, build (B,4,4,4) neighborhoods

        # Store original shape for final reshape
        original_shape = h.shape

        # Flatten all dimensions to (B,) for batched processing
        h_flat = h.reshape(-1)
        k_flat = k.reshape(-1)
        l_flat = l.reshape(-1)
        B = h_flat.shape[0]

        # Recompute floor indices for flattened tensors
        h_flr_flat = torch.floor(h_flat).long()
        k_flr_flat = torch.floor(k_flat).long()
        l_flr_flat = torch.floor(l_flat).long()

        # Build offset array [-1, 0, 1, 2] for neighborhood gathering
        offsets = torch.arange(-1, 3, device=self.device, dtype=torch.long)  # (4,)

        # Build coordinate grids for each query point: (B, 4)
        # h_grid[i] = [h_flr[i]-1, h_flr[i], h_flr[i]+1, h_flr[i]+2]
        h_grid_coords = h_flr_flat.unsqueeze(-1) + offsets  # (B, 4)
        k_grid_coords = k_flr_flat.unsqueeze(-1) + offsets  # (B, 4)
        l_grid_coords = l_flr_flat.unsqueeze(-1) + offsets  # (B, 4)

        # Build the batched 4x4x4 subcubes of structure factors
        if self.hkl_data is None:
            # If no HKL data loaded, use default_F everywhere: shape (B, 4, 4, 4)
            sub_Fhkl = torch.full((B, 4, 4, 4), self.config.default_F, dtype=self.dtype, device=self.device)
            # Coordinate arrays for polin3 (float, for interpolation): (B, 4)
            h_indices = h_grid_coords.to(dtype=self.dtype)
            k_indices = k_grid_coords.to(dtype=self.dtype)
            l_indices = l_grid_coords.to(dtype=self.dtype)
        else:
            # Convert to array indices (relative to hkl_data origin)
            h_array_grid = h_grid_coords - h_min  # (B, 4)
            k_array_grid = k_grid_coords - k_min  # (B, 4)
            l_array_grid = l_grid_coords - l_min  # (B, 4)

            # Advanced indexing to build (B, 4, 4, 4) neighborhoods
            # Following design_notes.md Section 2.6 broadcasting pattern:
            # h_array_grid[:, :, None, None] → (B, 4, 1, 1)
            # k_array_grid[:, None, :, None] → (B, 1, 4, 1)
            # l_array_grid[:, None, None, :] → (B, 1, 1, 4)
            # Result: (B, 4, 4, 4)
            sub_Fhkl = self.hkl_data[
                h_array_grid[:, :, None, None],
                k_array_grid[:, None, :, None],
                l_array_grid[:, None, None, :]
            ]

            # Coordinate arrays for polin3 (float Miller indices): (B, 4)
            h_indices = h_grid_coords.to(dtype=self.dtype)
            k_indices = k_grid_coords.to(dtype=self.dtype)
            l_indices = l_grid_coords.to(dtype=self.dtype)

        # Phase C3: Shape assertions to prevent silent regressions
        # Verify neighborhood tensor has correct shape for polynomial evaluation
        assert sub_Fhkl.shape == (B, 4, 4, 4), \
            f"Neighborhood shape mismatch: expected ({B}, 4, 4, 4), got {sub_Fhkl.shape}"

        # Verify coordinate arrays have correct shape
        assert h_indices.shape == (B, 4), f"h_indices shape mismatch: expected ({B}, 4), got {h_indices.shape}"
        assert k_indices.shape == (B, 4), f"k_indices shape mismatch: expected ({B}, 4), got {k_indices.shape}"
        assert l_indices.shape == (B, 4), f"l_indices shape mismatch: expected ({B}, 4), got {l_indices.shape}"

        # Phase C3: Device/dtype consistency check
        # Ensure all tensors are on the same device as the input query tensors
        assert sub_Fhkl.device == h.device, \
            f"Device mismatch: sub_Fhkl on {sub_Fhkl.device}, input on {h.device}"
        assert h_indices.device == h.device, \
            f"Device mismatch: h_indices on {h_indices.device}, input on {h.device}"

        # Perform tricubic interpolation
        # Phase C1 deliverable: batched gather complete
        # Phase D (polynomial vectorization) will consume these (B,4,4,4) neighborhoods
        # For now, maintain scalar path for single-element case and fall back for batched
        if B == 1:
            # Scalar case: use existing polin3 (squeeze to remove batch dim)
            F_cell = polin3(h_indices.squeeze(0), k_indices.squeeze(0), l_indices.squeeze(0),
                            sub_Fhkl.squeeze(0), h_flat.squeeze(0), k_flat.squeeze(0), l_flat.squeeze(0))

            # Phase C3: Output shape assertion (scalar path)
            # polin3 may return scalar [] or [1], both are acceptable for single-element batch
            assert F_cell.numel() == 1, \
                f"Scalar interpolation output must have 1 element, got {F_cell.numel()} (shape {F_cell.shape})"

            result = F_cell.reshape(original_shape)

            # Phase C3: Verify final output shape matches original input shape
            assert result.shape == original_shape, \
                f"Output shape mismatch: expected {original_shape}, got {result.shape}"

            return result
        else:
            # Batched case: Phase D will vectorize polin3; for now fall back to nearest-neighbor
            # This preserves existing behavior while delivering Phase C1 (batched gather infrastructure)
            if not self._interpolation_warning_shown:
                print("WARNING: tricubic interpolation batched gather implemented")
                print("WARNING: polynomial evaluation not yet vectorized; falling back to nearest-neighbor")
                print("WARNING: this warning will only be shown once")
                self._interpolation_warning_shown = True

            result = self._nearest_neighbor_lookup(h, k, l)

            # Phase C3: Verify fallback output shape matches original input shape
            assert result.shape == original_shape, \
                f"Fallback output shape mismatch: expected {original_shape}, got {result.shape}"

            return result


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
        # PERF-PYTORCH-004 Phase 1: Use clamp_min instead of torch.maximum to avoid allocating tensors inside compiled graph
        skew = skew.clamp_min(1e-12)

        V = 2.0 * self.cell_a * self.cell_b * self.cell_c * torch.sqrt(skew)
        # Ensure volume is not too small
        # PERF-PYTORCH-004 Phase 1: Use clamp_min instead of torch.maximum to avoid allocating tensors inside compiled graph
        V = V.clamp_min(1e-6)
        V_star = 1.0 / V

        # Calculate reciprocal cell lengths using C-code formulas
        a_star_length = self.cell_b * self.cell_c * torch.sin(alpha_rad) * V_star
        b_star_length = self.cell_c * self.cell_a * torch.sin(beta_rad) * V_star
        c_star_length = self.cell_a * self.cell_b * torch.sin(gamma_rad) * V_star

        # Calculate reciprocal angles with numerical stability
        sin_alpha = torch.sin(alpha_rad)
        sin_beta = torch.sin(beta_rad)

        # PERF-PYTORCH-004 Phase 1: Use clamp_min instead of torch.maximum to avoid allocating tensors inside compiled graph
        denom1 = (sin_beta * sin_gamma).clamp_min(1e-12)
        denom2 = (sin_gamma * sin_alpha).clamp_min(1e-12)
        denom3 = (sin_alpha * sin_beta).clamp_min(1e-12)

        cos_alpha_star = (cos_beta * cos_gamma - cos_alpha) / denom1
        cos_beta_star = (cos_gamma * cos_alpha - cos_beta) / denom2
        cos_gamma_star = (cos_alpha * cos_beta - cos_gamma) / denom3

        # Clamp cos_gamma_star to valid range [-1, 1]
        cos_gamma_star_bounded = torch.clamp(cos_gamma_star, -1.0, 1.0)
        # PERF-PYTORCH-004 Phase 1: Use clamp_min instead of torch.maximum to avoid allocating tensors inside compiled graph
        sin_gamma_star = torch.sqrt(
            (1.0 - torch.pow(cos_gamma_star_bounded, 2)).clamp_min(1e-12)
        )

        # Check if MOSFLM orientation matrix is provided (Phase G - CLI-FLAGS-003)
        # If present, use those reciprocal vectors instead of constructing from cell parameters
        if (
            hasattr(self.config, "mosflm_a_star") and self.config.mosflm_a_star is not None
            and hasattr(self.config, "mosflm_b_star") and self.config.mosflm_b_star is not None
            and hasattr(self.config, "mosflm_c_star") and self.config.mosflm_c_star is not None
        ):
            # MOSFLM orientation provided - convert to tensors and use directly
            # These are already in Å⁻¹ from the -mat file parsing
            a_star = torch.as_tensor(
                self.config.mosflm_a_star,
                device=self.device,
                dtype=self.dtype
            )
            b_star = torch.as_tensor(
                self.config.mosflm_b_star,
                device=self.device,
                dtype=self.dtype
            )
            c_star = torch.as_tensor(
                self.config.mosflm_c_star,
                device=self.device,
                dtype=self.dtype
            )
        else:
            # No MOSFLM orientation - construct default orientation from cell parameters (C-code convention)
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
            # PERF-PYTORCH-004 Phase 1: Use clamp_min instead of torch.maximum to avoid allocating tensors inside compiled graph
            sin_gamma_star_safe = sin_gamma_star.clamp_min(1e-12)
            c_star_y = (
                c_star_length
                * (cos_alpha_star - cos_beta_star * cos_gamma_star_bounded)
                / sin_gamma_star_safe
            )
            c_star_z = (
                c_star_length
                * V
                / (self.cell_a * self.cell_b * self.cell_c * sin_gamma_star_safe)
            )
            c_star = torch.stack([c_star_x, c_star_y, c_star_z])

        # Handle random misset generation (AT-PARALLEL-024)
        # This must happen BEFORE applying misset rotation
        if hasattr(self.config, "misset_random") and self.config.misset_random:
            # Generate random misset angles using C-compatible LCG
            from ..utils.c_random import mosaic_rotation_umat, umat2misset

            # Use 90.0 as the cap for random orientation to match C code behavior
            # NOTE: The C code passes 90.0 (degrees) but mosaic_rotation_umat treats it as radians!
            # This is a bug in the C code, but we replicate it for exact parity.
            # C code: mosaic_rotation_umat(90.0, umat, &misset_seed)
            umat = mosaic_rotation_umat(90.0, seed=self.config.misset_seed)

            # Extract Euler angles from the rotation matrix
            rotx, roty, rotz = umat2misset(umat)

            # Convert radians to degrees and update config
            self.config.misset_deg = (
                math.degrees(rotx),
                math.degrees(roty),
                math.degrees(rotz)
            )

            # Log the generated angles (matching C output format)
            if hasattr(self, 'logger') and self.logger:
                self.logger.info(
                    f"random orientation misset angles: "
                    f"{self.config.misset_deg[0]:.6f} "
                    f"{self.config.misset_deg[1]:.6f} "
                    f"{self.config.misset_deg[2]:.6f} deg"
                )

        # CRITICAL ORDER: Apply misset to INITIAL reciprocal vectors BEFORE real-space calculation
        # This matches C-code sequence (nanoBragg.c lines 2025-2034: misset applied to initial vectors)
        if hasattr(self.config, "misset_deg") and any(
            angle != 0.0 for angle in self.config.misset_deg
        ):
            # Apply misset rotation to initial reciprocal vectors only
            # C-code reference (nanoBragg.c lines 2025-2034):
            # rotate(a_star,a_star,misset[1],misset[2],misset[3]);
            # rotate(b_star,b_star,misset[1],misset[2],misset[3]);
            # rotate(c_star,c_star,misset[1],misset[2],misset[3]);
            from ..utils.geometry import angles_to_rotation_matrix, rotate_umat
            # Preserve gradient flow: convert to tensor only if not already a tensor
            misset_rad = []
            for angle in self.config.misset_deg:
                if isinstance(angle, torch.Tensor):
                    # Already a tensor - just convert dtype/device while preserving gradients
                    angle_tensor = angle.to(dtype=self.dtype, device=self.device)
                else:
                    # Scalar - create new tensor
                    angle_tensor = torch.tensor(angle, dtype=self.dtype, device=self.device)
                misset_rad.append(torch.deg2rad(angle_tensor))
            R_misset = angles_to_rotation_matrix(misset_rad[0], misset_rad[1], misset_rad[2])
            a_star = rotate_umat(a_star, R_misset)
            b_star = rotate_umat(b_star, R_misset)
            c_star = rotate_umat(c_star, R_misset)

        # Generate real-space vectors from (possibly rotated) reciprocal vectors
        # Cross products
        a_star_cross_b_star = torch.cross(a_star, b_star, dim=0)
        b_star_cross_c_star = torch.cross(b_star, c_star, dim=0)
        c_star_cross_a_star = torch.cross(c_star, a_star, dim=0)

        # C-code implementation for user-supplied cell (nanoBragg.c lines 2072-2080):
        # When cell parameters are user-supplied, the C code rescales cross products
        # to enforce that real-space vectors have exactly the user-specified magnitudes.
        # This uses formula volume V_cell throughout (not V_actual from vectors).
        #
        # C-code reference (lines 2076-2080):
        #   if (user_cell != 0) {  // Only rescale when cell parameters were explicitly provided
        #     vector_rescale(b_star_cross_c_star, b_star_cross_c_star, a[0]/V_cell);
        #     vector_rescale(c_star_cross_a_star, c_star_cross_a_star, b[0]/V_cell);
        #     vector_rescale(a_star_cross_b_star, a_star_cross_b_star, c[0]/V_cell);
        #     V_star = 1.0/V_cell;
        #   }
        #
        # vector_rescale normalizes and scales: new_vec = (target_mag / |old_vec|) * old_vec
        #
        # CRITICAL (CLI-FLAGS-003 Phase K3a): The C code sets user_cell=0 when MOSFLM matrices
        # are provided via -mat, which SKIPS this rescale path. When MOSFLM reciprocal vectors
        # are supplied, they already encode the exact orientation and should not be altered.

        # Check if MOSFLM orientation was provided - if so, skip rescale
        mosflm_provided = (
            hasattr(self.config, "mosflm_a_star") and self.config.mosflm_a_star is not None
            and hasattr(self.config, "mosflm_b_star") and self.config.mosflm_b_star is not None
            and hasattr(self.config, "mosflm_c_star") and self.config.mosflm_c_star is not None
        )

        if mosflm_provided:
            # MOSFLM matrix provided (CLI-FLAGS-003 Phase K3g1)
            # Recompute cell volume and real vectors from MOSFLM reciprocal vectors
            #
            # C-Code Implementation Reference (from nanoBragg.c, lines 2135-2169):
            # ```c
            # /* reciprocal unit cell volume, but is it lambda-corrected? */
            # V_star = dot_product(a_star,b_star_cross_c_star);
            # printf("TRACE: Reciprocal cell volume calculation:\n");
            # printf("TRACE:   V_star = a_star . (b_star x c_star) = %g\n", V_star);
            #
            # /* make sure any user-supplied cell takes */
            # if(user_cell)
            # {
            #     /* a,b,c and V_cell were generated above */
            #     /* force the cross-product vectors to have proper magnitude: b_star X c_star = a*V_star */
            #     vector_rescale(b_star_cross_c_star,b_star_cross_c_star,a[0]/V_cell);
            #     vector_rescale(c_star_cross_a_star,c_star_cross_a_star,b[0]/V_cell);
            #     vector_rescale(a_star_cross_b_star,a_star_cross_b_star,c[0]/V_cell);
            #     V_star = 1.0/V_cell;
            # }
            #
            # /* direct-space cell volume */
            # V_cell = 1.0/V_star;
            # printf("TRACE: Direct-space cell volume: V_cell = 1/V_star = %g\n", V_cell);
            #
            # /* generate direct-space cell vectors, also updates magnitudes */
            # printf("TRACE: Before computing real-space vectors:\n");
            # printf("TRACE:   b_star_cross_c_star = [%g, %g, %g]\n", b_star_cross_c_star[1], b_star_cross_c_star[2], b_star_cross_c_star[3]);
            # printf("TRACE:   c_star_cross_a_star = [%g, %g, %g]\n", c_star_cross_a_star[1], c_star_cross_a_star[2], c_star_cross_a_star[3]);
            # printf("TRACE:   a_star_cross_b_star = [%g, %g, %g]\n", a_star_cross_b_star[1], a_star_cross_b_star[2], a_star_cross_b_star[3]);
            # printf("TRACE:   V_cell = %g, V_star = %g\n", V_cell, V_star);
            #
            # vector_scale(b_star_cross_c_star,a,V_cell);
            # vector_scale(c_star_cross_a_star,b,V_cell);
            # vector_scale(a_star_cross_b_star,c,V_cell);
            #
            # printf("TRACE: After computing real-space vectors:\n");
            # printf("TRACE:   a = [%g, %g, %g] |a| = %g\n", a[1], a[2], a[3], a[0]);
            # printf("TRACE:   b = [%g, %g, %g] |b| = %g\n", b[1], b[2], b[3], b[0]);
            # printf("TRACE:   c = [%g, %g, %g] |c| = %g\n", c[1], c[2], c[3], c[0]);
            # ```
            #
            # Step 1: Compute reciprocal cell volume V_star = a* · (b* × c*)
            V_star = torch.dot(a_star, b_star_cross_c_star)
            # Clamp to avoid division by zero
            V_star = V_star.clamp_min(1e-18)

            # Step 2: Compute direct-space cell volume V_cell = 1 / V_star (in Å³)
            V_cell = 1.0 / V_star

            # Step 3: Compute real-space vectors: a = (b* × c*) × V_cell, etc. (in Å)
            a_vec = b_star_cross_c_star * V_cell
            b_vec = c_star_cross_a_star * V_cell
            c_vec = a_star_cross_b_star * V_cell

            # Step 4: Update cell parameters (magnitudes in Å)
            self.cell_a = torch.norm(a_vec)
            self.cell_b = torch.norm(b_vec)
            self.cell_c = torch.norm(c_vec)

            # Update V to V_cell in Å³ for metric duality calculation (will be converted to meters later)
            V = V_cell
        else:
            # User-supplied cell parameters (not MOSFLM matrix)
            # Rescale cross products to enforce exact cell lengths
            a_mag = self.config.cell_a
            b_mag = self.config.cell_b
            c_mag = self.config.cell_c

            # Rescale cross products to enforce: |(b* × c*)| = |a| / V_cell
            # This ensures real vectors will have exact user-specified magnitudes
            mag_b_star_cross_c_star = torch.norm(b_star_cross_c_star)
            mag_c_star_cross_a_star = torch.norm(c_star_cross_a_star)
            mag_a_star_cross_b_star = torch.norm(a_star_cross_b_star)

            # Avoid division by zero
            # PERF-PYTORCH-004 Phase 1: Use clamp_min instead of torch.maximum to avoid allocating tensors inside compiled graph
            mag_b_star_cross_c_star = mag_b_star_cross_c_star.clamp_min(1e-12)
            mag_c_star_cross_a_star = mag_c_star_cross_a_star.clamp_min(1e-12)
            mag_a_star_cross_b_star = mag_a_star_cross_b_star.clamp_min(1e-12)

            # Rescale to target magnitudes
            target_mag_b_star_cross_c_star = a_mag / V
            target_mag_c_star_cross_a_star = b_mag / V
            target_mag_a_star_cross_b_star = c_mag / V

            b_star_cross_c_star = b_star_cross_c_star * (target_mag_b_star_cross_c_star / mag_b_star_cross_c_star)
            c_star_cross_a_star = c_star_cross_a_star * (target_mag_c_star_cross_a_star / mag_c_star_cross_a_star)
            a_star_cross_b_star = a_star_cross_b_star * (target_mag_a_star_cross_b_star / mag_a_star_cross_b_star)

            # Real-space vectors: a = (b* × c*) × V_cell
            # After rescaling, these will have exactly the user-specified magnitudes
            a_vec = b_star_cross_c_star * V
            b_vec = c_star_cross_a_star * V
            c_vec = a_star_cross_b_star * V

        # Now that we have real-space vectors, re-generate the reciprocal ones
        # This matches the C-code behavior (lines 2103-2119)
        a_cross_b = torch.cross(a_vec, b_vec, dim=0)
        b_cross_c = torch.cross(b_vec, c_vec, dim=0)
        c_cross_a = torch.cross(c_vec, a_vec, dim=0)

        # Recalculate volume from the actual vectors (Core Rule #13)
        # This is crucial - the volume from the vectors is slightly different
        # from the volume calculated by the formula, and we need to use the
        # actual volume for perfect metric duality (a·a* = 1 within 1e-12)
        V_actual = torch.dot(a_vec, b_cross_c)
        # Ensure volume is not too small
        # PERF-PYTORCH-004 Phase 1: Use clamp_min instead of torch.maximum
        V_actual = V_actual.clamp_min(1e-6)
        V_star_actual = 1.0 / V_actual

        # a* = (b × c) / V_actual, etc.
        a_star = b_cross_c * V_star_actual
        b_star = c_cross_a * V_star_actual
        c_star = a_cross_b * V_star_actual

        # Update V to the actual volume
        V = V_actual

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
    
    @property
    def volume(self) -> torch.Tensor:
        """Unit cell volume (Angstroms^3). Alias for V."""
        return self.V

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
        #
        # CRITICAL: Match C code loop formula: phi = phi0 + phistep*phi_tic
        # where phistep = osc/phisteps and phi_tic ranges from 0 to (phisteps-1)
        #
        # C code reference (nanoBragg.c lines 3004-3009):
        #   for(phi_tic = 0; phi_tic < phisteps; ++phi_tic)
        #   {
        #       phi = phi0 + phistep*phi_tic;
        #       if( phi != 0.0 ) { rotate_axis(...); }
        #   }
        #
        # For phisteps=1, phi_tic=0, so phi = phi0 + phistep*0 = phi0 (no rotation!)
        # PyTorch previously used midpoint formula which was INCORRECT.

        # Use arange and manual scaling to preserve gradients and match C loop formula
        step_indices = torch.arange(
            config.phi_steps, device=self.device, dtype=self.dtype
        )
        step_size = (
            config.osc_range_deg / config.phi_steps
            if config.phi_steps > 0
            else torch.tensor(0.0, device=self.device, dtype=self.dtype)
        )
        # C loop formula: phi = phi_start + step_size * step_index
        # where step_index ranges from 0 to (phi_steps - 1)
        phi_angles = config.phi_start_deg + step_size * step_indices
        phi_rad = torch.deg2rad(phi_angles)

        # Convert spindle axis to tensor
        spindle_axis = torch.tensor(
            config.spindle_axis, device=self.device, dtype=self.dtype
        )

        # Step 1: Apply spindle rotation to ONLY real-space vectors (a, b, c)
        # This follows spec-compliant semantics where each φ step gets a fresh rotation.
        # Spec reference (specs/spec-a-core.md:211-214):
        #   "φ step: φ = φ0 + (step index)*phistep; rotate the reference cell (a0,b0,c0)
        #    about u by φ to get (ap,bp,cp)."
        #
        # NOTE: This is the SPEC-COMPLIANT path. The C code (nanoBragg.c:3044-3058) contains
        # a bug where it skips rotation when phi==0, causing ap/bp/cp to carry over stale
        # values from the previous pixel's last φ step. This is documented as C-PARITY-001
        # in docs/bugs/verified_c_bugs.md:166-204. An opt-in parity shim will be added in
        # Phase L3k.3c.4 for validation harnesses that need to reproduce the C bug.
        #
        # Shape: (N_phi, 3)

        # Apply rotation to base vectors for all φ angles
        # When phi=0, rotate_axis applies identity rotation, yielding base vectors
        a_phi = rotate_axis(
            self.a.unsqueeze(0).expand(config.phi_steps, -1),
            spindle_axis.unsqueeze(0).expand(config.phi_steps, -1),
            phi_rad
        )
        b_phi = rotate_axis(
            self.b.unsqueeze(0).expand(config.phi_steps, -1),
            spindle_axis.unsqueeze(0).expand(config.phi_steps, -1),
            phi_rad
        )
        c_phi = rotate_axis(
            self.c.unsqueeze(0).expand(config.phi_steps, -1),
            spindle_axis.unsqueeze(0).expand(config.phi_steps, -1),
            phi_rad
        )

        # Step 2: Recompute reciprocal vectors from rotated real vectors
        # This ensures metric duality is preserved: a·a* = 1 exactly (CLAUDE Rule #13)
        # Formula: a* = (b × c) / V_actual, where V_actual = a · (b × c)
        # This matches the C-code's implicit reciprocal vector calculation during Miller index lookup.
        b_cross_c = torch.cross(b_phi, c_phi, dim=-1)
        c_cross_a = torch.cross(c_phi, a_phi, dim=-1)
        a_cross_b = torch.cross(a_phi, b_phi, dim=-1)

        # Compute actual volume from rotated real vectors
        # Shape: (N_phi, 1)
        V_actual = torch.sum(a_phi * b_cross_c, dim=-1, keepdim=True)

        # Recompute reciprocal vectors to maintain metric duality
        # Shape: (N_phi, 3)
        a_star_phi = b_cross_c / V_actual
        b_star_phi = c_cross_a / V_actual
        c_star_phi = a_cross_b / V_actual

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
            # PERF-PYTORCH-004 P1.3: Use .new_tensor to avoid fresh allocation
            identity = a_phi.new_zeros(3, 3)
            identity[0, 0] = 1.0
            identity[1, 1] = 1.0
            identity[2, 2] = 1.0
            mosaic_umats = identity.unsqueeze(0).repeat(config.mosaic_domains, 1, 1)

        # Apply mosaic rotations to both real and reciprocal vectors
        # Broadcast phi and mosaic dimensions: (N_phi, 1, 3) x (1, N_mos, 3, 3) -> (N_phi, N_mos, 3)
        a_final = rotate_umat(a_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))
        b_final = rotate_umat(b_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))
        c_final = rotate_umat(c_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))

        a_star_final = rotate_umat(a_star_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))
        b_star_final = rotate_umat(b_star_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))
        c_star_final = rotate_umat(c_star_phi.unsqueeze(1), mosaic_umats.unsqueeze(0))

        # TODO (CLI-FLAGS-003 Phase L3k.3c.4): φ=0 cache population will go here
        # when opt-in parity shim is added

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
        # PERF-PYTORCH-004 P1.3: Use .new_tensor to avoid fresh allocation
        identity = random_axes.new_zeros(3, 3)
        identity[0, 0] = 1.0
        identity[1, 1] = 1.0
        identity[2, 2] = 1.0
        identity_vecs = identity.unsqueeze(0).repeat(config.mosaic_domains, 1, 1)

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

        # NOW regenerate reciprocal vectors from the rotated real-space vectors
        # This matches the C code behavior (lines ~2107-2117 in nanoBragg.c)
        # The C code performs this circular recalculation to ensure perfect metric duality
        a_cross_b = torch.cross(vectors["a"], vectors["b"], dim=0)
        b_cross_c = torch.cross(vectors["b"], vectors["c"], dim=0)
        c_cross_a = torch.cross(vectors["c"], vectors["a"], dim=0)

        # Recalculate volume from the actual rotated vectors
        V_actual = torch.dot(vectors["a"], b_cross_c)
        # PERF-PYTORCH-004 Phase 1: Use clamp_min instead of torch.maximum to avoid allocating tensors inside compiled graph
        V_actual = V_actual.clamp_min(1e-6)
        V_star_actual = 1.0 / V_actual

        # a* = (b × c) / V, etc.
        vectors["a_star"] = b_cross_c * V_star_actual
        vectors["b_star"] = c_cross_a * V_star_actual
        vectors["c_star"] = a_cross_b * V_star_actual

        return vectors

    def _apply_sample_clipping(self, beam_config: BeamConfig) -> None:
        """Apply sample clipping based on beam size (AT-FLU-001).

        Per spec: when beamsize > 0 and smaller than sample_y or sample_z,
        those sample dimensions SHALL be clipped to beamsize and a warning printed.

        Args:
            beam_config: Beam configuration containing beamsize_mm
        """
        beamsize_m = beam_config.beamsize_mm / 1000.0  # Convert mm to meters

        # Check and clip sample_y
        if self.config.sample_y is not None and beamsize_m < self.config.sample_y:
            print(f"Warning: Clipping sample_y from {self.config.sample_y:.6e} m to beamsize {beamsize_m:.6e} m")
            self.config.sample_y = beamsize_m

        # Check and clip sample_z
        if self.config.sample_z is not None and beamsize_m < self.config.sample_z:
            print(f"Warning: Clipping sample_z from {self.config.sample_z:.6e} m to beamsize {beamsize_m:.6e} m")
            self.config.sample_z = beamsize_m

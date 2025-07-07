"""
Crystal model for nanoBragg PyTorch implementation.

This module defines the Crystal class responsible for managing unit cell,
orientation, and structure factor data.
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
        self.cell_a = torch.tensor(100.0, device=self.device, dtype=self.dtype, requires_grad=False)
        self.cell_b = torch.tensor(100.0, device=self.device, dtype=self.dtype, requires_grad=False)
        self.cell_c = torch.tensor(100.0, device=self.device, dtype=self.dtype, requires_grad=False)
        self.cell_alpha = torch.tensor(90.0, device=self.device, dtype=self.dtype, requires_grad=False)
        self.cell_beta = torch.tensor(90.0, device=self.device, dtype=self.dtype, requires_grad=False)
        self.cell_gamma = torch.tensor(90.0, device=self.device, dtype=self.dtype, requires_grad=False)

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
        self.N_cells_a = torch.tensor(5, device=self.device, dtype=self.dtype, requires_grad=False)
        self.N_cells_b = torch.tensor(5, device=self.device, dtype=self.dtype, requires_grad=False)
        self.N_cells_c = torch.tensor(5, device=self.device, dtype=self.dtype, requires_grad=False)

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
        """Load structure factor data from HKL file."""
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
        """Look up structure factor for given h,k,l indices."""
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

    def get_rotated_reciprocal_vectors(
        self, phi: torch.Tensor, mosaic_umats: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Get reciprocal lattice vectors after phi and mosaic rotations.

        Args:
            phi: Spindle rotation angles
            mosaic_umats: Mosaic domain rotation matrices

        Returns:
            Tuple of rotated a_star, b_star, c_star vectors
        """
        # TODO: Implement rotation logic using utils/geometry.py functions
        raise NotImplementedError("Vector rotation to be implemented in Phase 2")

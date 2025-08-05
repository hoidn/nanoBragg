"""
Detector model for nanoBragg PyTorch implementation.

This module defines the Detector class responsible for managing all detector
geometry calculations and pixel coordinate generation.
"""

from typing import Optional, Tuple

import torch

from ..config import DetectorConfig
from ..utils.units import mm_to_angstroms, degrees_to_radians


class Detector:
    """
    Detector model managing geometry and pixel coordinates.

    Responsible for:
    - Detector position and orientation (basis vectors)
    - Pixel coordinate generation and caching
    - Solid angle corrections
    """

    def __init__(self, config: Optional[DetectorConfig] = None, device=None, dtype=torch.float64):
        """Initialize detector from configuration."""
        self.device = device if device is not None else torch.device("cpu")
        self.dtype = dtype
        
        # Use provided config or create default
        if config is None:
            config = DetectorConfig()  # Use defaults
        self.config = config
        
        # Convert units to internal Angstrom system
        self.distance = mm_to_angstroms(config.distance_mm)
        self.pixel_size = mm_to_angstroms(config.pixel_size_mm)
        
        # Copy dimension parameters
        self.spixels = config.spixels
        self.fpixels = config.fpixels
        
        # Convert beam center from mm to pixels
        # Note: beam center is given in mm from detector origin
        if isinstance(config.beam_center_s, torch.Tensor):
            self.beam_center_s = config.beam_center_s / config.pixel_size_mm
        else:
            self.beam_center_s = config.beam_center_s / config.pixel_size_mm
            
        if isinstance(config.beam_center_f, torch.Tensor):
            self.beam_center_f = config.beam_center_f / config.pixel_size_mm
        else:
            self.beam_center_f = config.beam_center_f / config.pixel_size_mm

        # Initialize basis vectors
        if self._is_default_config():
            # Use hard-coded vectors for backward compatibility
            # Detector basis vectors from golden log: DIRECTION_OF_DETECTOR_*_AXIS
            # Fast axis (X): [0, 0, 1]
            # Slow axis (Y): [0, -1, 0]
            # Normal axis (Z): [1, 0, 0]
            self.fdet_vec = torch.tensor(
                [0.0, 0.0, 1.0], device=self.device, dtype=self.dtype
            )
            self.sdet_vec = torch.tensor(
                [0.0, -1.0, 0.0], device=self.device, dtype=self.dtype
            )
            self.odet_vec = torch.tensor(
                [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype
            )
        else:
            # Calculate basis vectors dynamically in Phase 2
            self.fdet_vec, self.sdet_vec, self.odet_vec = self._calculate_basis_vectors()

        self._pixel_coords_cache = None
        self._geometry_version = 0

    def _is_default_config(self) -> bool:
        """Check if using default config (for backward compatibility)."""
        c = self.config
        # Check all basic parameters
        basic_check = (c.distance_mm == 100.0 and c.pixel_size_mm == 0.1 and
                       c.spixels == 1024 and c.fpixels == 1024 and
                       c.beam_center_s == 51.2 and c.beam_center_f == 51.2)
        
        # Check rotation parameters (handle both float and tensor)
        rotx_check = (c.detector_rotx_deg == 0 if isinstance(c.detector_rotx_deg, (int, float))
                      else torch.allclose(c.detector_rotx_deg, torch.tensor(0.0)))
        roty_check = (c.detector_roty_deg == 0 if isinstance(c.detector_roty_deg, (int, float))
                      else torch.allclose(c.detector_roty_deg, torch.tensor(0.0)))
        rotz_check = (c.detector_rotz_deg == 0 if isinstance(c.detector_rotz_deg, (int, float))
                      else torch.allclose(c.detector_rotz_deg, torch.tensor(0.0)))
        twotheta_check = (c.detector_twotheta_deg == 0 if isinstance(c.detector_twotheta_deg, (int, float))
                          else torch.allclose(c.detector_twotheta_deg, torch.tensor(0.0)))
        
        return basic_check and rotx_check and roty_check and rotz_check and twotheta_check

    def to(self, device=None, dtype=None):
        """Move detector to specified device and/or dtype."""
        if device is not None:
            self.device = device
        if dtype is not None:
            self.dtype = dtype

        # Move basis vectors to new device/dtype
        self.fdet_vec = self.fdet_vec.to(device=self.device, dtype=self.dtype)
        self.sdet_vec = self.sdet_vec.to(device=self.device, dtype=self.dtype)
        self.odet_vec = self.odet_vec.to(device=self.device, dtype=self.dtype)

        # Invalidate cache since device/dtype changed
        self.invalidate_cache()
        return self

    def invalidate_cache(self):
        """Invalidate cached pixel coordinates when geometry changes."""
        self._pixel_coords_cache = None
        self._geometry_version += 1

    def get_pixel_coords(self) -> torch.Tensor:
        """
        Get 3D coordinates of all detector pixels.

        Returns:
            torch.Tensor: Pixel coordinates with shape (spixels, fpixels, 3) in Angstroms
        """
        if self._pixel_coords_cache is None:
            # Create pixel coordinate grids
            s_coords = torch.arange(self.spixels, device=self.device, dtype=self.dtype)
            f_coords = torch.arange(self.fpixels, device=self.device, dtype=self.dtype)

            # Convert to Angstroms relative to beam center
            s_angstroms = (s_coords - self.beam_center_s) * self.pixel_size
            f_angstroms = (f_coords - self.beam_center_f) * self.pixel_size

            # Create meshgrid
            s_grid, f_grid = torch.meshgrid(s_angstroms, f_angstroms, indexing="ij")

            # Calculate 3D coordinates for each pixel
            # pixel_coords = detector_origin + s*sdet_vec + f*fdet_vec
            # detector_origin is at distance along normal vector
            # Distance is in Angstroms
            detector_origin = self.distance * self.odet_vec

            # Expand basis vectors for broadcasting
            sdet_expanded = self.sdet_vec.unsqueeze(0).unsqueeze(0)  # (1, 1, 3)
            fdet_expanded = self.fdet_vec.unsqueeze(0).unsqueeze(0)  # (1, 1, 3)
            origin_expanded = detector_origin.unsqueeze(0).unsqueeze(0)  # (1, 1, 3)

            # Calculate pixel coordinates
            pixel_coords = (
                origin_expanded
                + s_grid.unsqueeze(-1) * sdet_expanded
                + f_grid.unsqueeze(-1) * fdet_expanded
            )

            self._pixel_coords_cache = pixel_coords

        return self._pixel_coords_cache

    def _calculate_basis_vectors(
        self,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Calculate detector basis vectors from configuration.

        This method will dynamically compute the detector's fast, slow, and
        normal basis vectors based on user-provided configuration, such as
        detector rotations (`-detector_rot*`) and the two-theta angle.

        C-Code Implementation Reference (from nanoBragg.c, lines 1319-1412):
        The C code performs these calculations in a large block within main()
        after parsing arguments. The key operations to replicate are:

        ```c
            /* initialize detector origin from a beam center and distance */
            /* there are two conventions here: mosflm and XDS */
            // ... logic to handle different conventions ...

            if(detector_pivot == SAMPLE){
                printf("pivoting detector around sample\n");
                /* initialize detector origin before rotating detector */
                pix0_vector[1] = -Fclose*fdet_vector[1]-Sclose*sdet_vector[1]+close_distance*odet_vector[1];
                pix0_vector[2] = -Fclose*fdet_vector[2]-Sclose*sdet_vector[2]+close_distance*odet_vector[2];
                pix0_vector[3] = -Fclose*fdet_vector[3]-Sclose*sdet_vector[3]+close_distance*odet_vector[3];

                /* now swing the detector origin around */
                rotate(pix0_vector,pix0_vector,detector_rotx,detector_roty,detector_rotz);
                rotate_axis(pix0_vector,pix0_vector,twotheta_axis,detector_twotheta);
            }
            /* now orient the detector plane */
            rotate(fdet_vector,fdet_vector,detector_rotx,detector_roty,detector_rotz);
            rotate(sdet_vector,sdet_vector,detector_rotx,detector_roty,detector_rotz);
            rotate(odet_vector,odet_vector,detector_rotx,detector_roty,detector_rotz);

            /* also apply orientation part of twotheta swing */
            rotate_axis(fdet_vector,fdet_vector,twotheta_axis,detector_twotheta);
            rotate_axis(sdet_vector,sdet_vector,twotheta_axis,detector_twotheta);
            rotate_axis(odet_vector,odet_vector,twotheta_axis,detector_twotheta);

            /* make sure beam center is preserved */
            if(detector_pivot == BEAM){
                printf("pivoting detector around direct beam spot\n");
                pix0_vector[1] = -Fbeam*fdet_vector[1]-Sbeam*sdet_vector[1]+distance*beam_vector[1];
                pix0_vector[2] = -Fbeam*fdet_vector[2]-Sbeam*sdet_vector[2]+distance*beam_vector[2];
                pix0_vector[3] = -Fbeam*fdet_vector[3]-Sbeam*sdet_vector[3]+distance*beam_vector[3];
            }
        ```
        """
        raise NotImplementedError(
            "Basis vector calculation to be implemented in Phase 2"
        )

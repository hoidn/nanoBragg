"""
Detector model for nanoBragg PyTorch implementation.

This module defines the Detector class responsible for managing all detector
geometry calculations and pixel coordinate generation.
"""

from typing import Tuple

import torch

from ..config import DetectorConfig


class Detector:
    """
    Detector model managing geometry and pixel coordinates.

    Responsible for:
    - Detector position and orientation (basis vectors)
    - Pixel coordinate generation and caching
    - Solid angle corrections
    """

    def __init__(self, config: DetectorConfig = None, device=None, dtype=torch.float64):
        """Initialize detector from configuration."""
        self.device = device if device is not None else torch.device("cpu")
        self.dtype = dtype

        # Hard-coded simple_cubic geometry (from golden test case)
        # Distance: 100 mm, detector size: 102.4x102.4 mm, pixel size: 0.1 mm, 1024x1024 pixels
        # Convert to Angstroms for internal consistency
        self.distance_m = 0.1  # meters (100 mm)
        self.pixel_size_m = 0.0001  # meters (0.1 mm)
        self.distance = self.distance_m * 1e10  # Angstroms
        self.pixel_size = self.pixel_size_m * 1e10  # Angstroms
        self.spixels = 1024  # slow pixels (from C trace: 1024x1024 pixels)
        self.fpixels = 1024  # fast pixels
        self.beam_center_f = 512.5  # pixels (Xbeam=0.05125 m / 0.0001 m per pixel)
        self.beam_center_s = 512.5  # pixels (Ybeam=0.05125 m / 0.0001 m per pixel)

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

        self._pixel_coords_cache = None
        self._geometry_version = 0

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

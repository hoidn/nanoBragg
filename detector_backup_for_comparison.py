"""
Detector model for nanoBragg PyTorch implementation.

This module defines the Detector class responsible for managing all detector
geometry calculations and pixel coordinate generation.
"""

from typing import Optional, Tuple

import torch

from ..config import DetectorConfig, DetectorConvention
from ..utils.units import mm_to_angstroms, degrees_to_radians


def _nonzero_scalar(x) -> bool:
    """Return a Python bool for 'x != 0' even if x is a 0-dim torch.Tensor."""
    if isinstance(x, torch.Tensor):
        return bool(torch.abs(x).item() > 1e-12)
    return abs(float(x)) > 1e-12


class Detector:
    """
    Detector model managing geometry and pixel coordinates.

    **Authoritative Specification:** For a complete specification of this
    component's coordinate systems, conventions, and unit handling, see the
    full architectural deep dive: `docs/architecture/detector.md`.

    Responsible for:
    - Detector position and orientation (basis vectors)
    - Pixel coordinate generation and caching
    - Solid angle corrections
    """

    def __init__(
        self, config: Optional[DetectorConfig] = None, device=None, dtype=torch.float64
    ):
        """Initialize detector from configuration."""
        self.device = device if device is not None else torch.device("cpu")
        self.dtype = dtype

        # Use provided config or create default
        if config is None:
            config = DetectorConfig()  # Use defaults
        self.config = config

        # NOTE: Detector geometry works in METERS, not Angstroms!
        # This is different from the physics calculations which use Angstroms
        # The C-code detector geometry calculations use meters as evidenced by
        # DETECTOR_PIX0_VECTOR outputting values like 0.1 (for 100mm distance)
        self.distance = config.distance_mm / 1000.0  # Convert mm to meters
        self.pixel_size = config.pixel_size_mm / 1000.0  # Convert mm to meters

        # Copy dimension parameters
        self.spixels = config.spixels
        self.fpixels = config.fpixels

        # Convert beam center from mm to pixels
        # Note: beam center is given in mm from detector origin
        self.beam_center_s: torch.Tensor
        self.beam_center_f: torch.Tensor

        if isinstance(config.beam_center_s, torch.Tensor):
            self.beam_center_s = config.beam_center_s / config.pixel_size_mm
        else:
            self.beam_center_s = torch.tensor(
                config.beam_center_s / config.pixel_size_mm,
                device=self.device,
                dtype=self.dtype,
            )

        if isinstance(config.beam_center_f, torch.Tensor):
            self.beam_center_f = config.beam_center_f / config.pixel_size_mm
        else:
            self.beam_center_f = torch.tensor(
                config.beam_center_f / config.pixel_size_mm,
                device=self.device,
                dtype=self.dtype,
            )

        # Initialize basis vectors
        if self._is_default_config():
            # PHASE 1 FIX: Corrected basis vectors to match C implementation exactly
            # From C code trace: DETECTOR_FAST_AXIS 0 0 1, DETECTOR_SLOW_AXIS 0 -1 0, DETECTOR_NORMAL_AXIS 1 0 0
            # This fixes the 192.67mm coordinate system error
            self.fdet_vec = torch.tensor(
                [0.0, 0.0, 1.0], device=self.device, dtype=self.dtype  # Fast along positive Z
            )
            self.sdet_vec = torch.tensor(
                [0.0, -1.0, 0.0], device=self.device, dtype=self.dtype  # Slow along negative Y
            )
            self.odet_vec = torch.tensor(
                [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype   # Origin along positive X (beam)
            )
        else:
            # Calculate basis vectors dynamically in Phase 2
            self.fdet_vec, self.sdet_vec, self.odet_vec = (
                self._calculate_basis_vectors()
            )

        # Calculate and cache pix0_vector (position of first pixel)
        self._calculate_pix0_vector()

        self._pixel_coords_cache: Optional[torch.Tensor] = None
        self._geometry_version = 0
        self._cached_basis_vectors = (
            self.fdet_vec.clone(),
            self.sdet_vec.clone(),
            self.odet_vec.clone(),
        )
        self._cached_pix0_vector = self.pix0_vector.clone()

    def _is_default_config(self) -> bool:
        """Check if using default config (for backward compatibility)."""
        from ..config import DetectorConvention

        c = self.config
        # Check all basic parameters
        basic_check = (
            c.distance_mm == 100.0
            and c.pixel_size_mm == 0.1
            and c.spixels == 1024
            and c.fpixels == 1024
            and c.beam_center_s == 51.25
            and c.beam_center_f == 51.25
        )

        # Check detector convention is default (MOSFLM)
        convention_check = c.detector_convention == DetectorConvention.MOSFLM

        # Check rotation parameters (handle both float and tensor)
        rotx_check = (
            c.detector_rotx_deg == 0
            if isinstance(c.detector_rotx_deg, (int, float))
            else torch.allclose(
                c.detector_rotx_deg, torch.tensor(0.0, dtype=c.detector_rotx_deg.dtype)
            )
        )
        roty_check = (
            c.detector_roty_deg == 0
            if isinstance(c.detector_roty_deg, (int, float))
            else torch.allclose(
                c.detector_roty_deg, torch.tensor(0.0, dtype=c.detector_roty_deg.dtype)
            )
        )
        rotz_check = (
            c.detector_rotz_deg == 0
            if isinstance(c.detector_rotz_deg, (int, float))
            else torch.allclose(
                c.detector_rotz_deg, torch.tensor(0.0, dtype=c.detector_rotz_deg.dtype)
            )
        )
        twotheta_check = (
            c.detector_twotheta_deg == 0
            if isinstance(c.detector_twotheta_deg, (int, float))
            else torch.allclose(
                c.detector_twotheta_deg,
                torch.tensor(0.0, dtype=c.detector_twotheta_deg.dtype),
            )
        )

        return bool(
            basic_check
            and convention_check
            and rotx_check
            and roty_check
            and rotz_check
            and twotheta_check
        )

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

        # Move beam center tensors
        self.beam_center_s = self.beam_center_s.to(device=self.device, dtype=self.dtype)
        self.beam_center_f = self.beam_center_f.to(device=self.device, dtype=self.dtype)

        # Invalidate cache since device/dtype changed
        self.invalidate_cache()
        return self

    def invalidate_cache(self):
        """Invalidate cached pixel coordinates when geometry changes."""
        self._pixel_coords_cache = None
        self._geometry_version += 1
        # Recalculate pix0_vector when geometry changes
        self._calculate_pix0_vector()

    def _apply_mosflm_beam_convention(self):
        """
        Apply MOSFLM beam center convention with axis swap and pixel offset.
        
        MOSFLM convention requires:
        1. Axis swap: beam_center_s (slow) → F axis, beam_center_f (fast) → S axis
        2. +0.5 pixel offset for both axes
        3. Convert to meters for internal geometry calculations
        
        Returns:
            tuple: (beam_f_m, beam_s_m) in meters for use in pix0_vector calculation
        """
        from ..config import DetectorConvention
        
        if self.config.detector_convention == DetectorConvention.MOSFLM:
            # MOSFLM convention: Apply axis swap AND +0.5 pixel offset
            # beam_center_s → Fbeam (with swap and offset)
            # beam_center_f → Sbeam (with swap and offset)
            beam_s_mm = self.config.beam_center_s if hasattr(self.config, 'beam_center_s') else 51.2
            beam_f_mm = self.config.beam_center_f if hasattr(self.config, 'beam_center_f') else 51.2
            
            # Convert to pixels first, add 0.5 pixel offset, then to meters
            beam_s_pixels = beam_s_mm / self.config.pixel_size_mm  # mm to pixels
            beam_f_pixels = beam_f_mm / self.config.pixel_size_mm  # mm to pixels
            
            # MOSFLM axis mapping with 0.5 pixel offset:
            # Fbeam = beam_center_s (in pixels) + 0.5, then to meters
            # Sbeam = beam_center_f (in pixels) + 0.5, then to meters  
            adjusted_f = (beam_s_pixels + 0.5) * self.pixel_size  # S→F mapping
            adjusted_s = (beam_f_pixels + 0.5) * self.pixel_size  # F→S mapping
        else:
            # Standard convention: no axis swap, no pixel offset
            beam_s_mm = self.config.beam_center_s if hasattr(self.config, 'beam_center_s') else 51.2
            beam_f_mm = self.config.beam_center_f if hasattr(self.config, 'beam_center_f') else 51.2
            
            adjusted_f = beam_f_mm / 1000.0  # mm to meters
            adjusted_s = beam_s_mm / 1000.0  # mm to meters
        
        return adjusted_f, adjusted_s

    def get_effective_distance(self):
        """
        Apply geometric distance correction for tilted detector.
        
        When detector is tilted, effective distance = nominal_distance / cos(tilt_angle)
        where tilt_angle is between beam direction [1,0,0] and detector normal.
        
        Returns:
            torch.Tensor: Effective distance in meters
        """
        # Get the rotated detector normal vector (after all rotations)
        detector_normal = self.odet_vec  # Should already be normalized
        
        # Beam travels along positive X axis in MOSFLM convention
        beam_direction = torch.tensor([1.0, 0.0, 0.0], dtype=self.dtype, device=self.device)
        
        # Calculate cosine of angle between beam and detector normal
        cos_angle = torch.dot(beam_direction, detector_normal)
        
        # Prevent division by zero for perpendicular detector
        cos_angle = torch.clamp(cos_angle, min=0.001)
        
        # Apply the distance correction formula
        if isinstance(self.distance, torch.Tensor):
            effective_distance = self.distance / cos_angle
        else:
            effective_distance = torch.tensor(self.distance, dtype=self.dtype, device=self.device) / cos_angle
        
        return effective_distance

    def _is_custom_convention(self) -> bool:
        """
        Check if C code will use CUSTOM convention instead of MOSFLM.
        
        Based on the C code analysis:
        - MOSFLM convention (no explicit -twotheta_axis): Uses +0.5 pixel offset
        - CUSTOM convention (explicit -twotheta_axis): No +0.5 pixel offset  
        
        For now, we'll return False to always use MOSFLM convention for testing,
        then implement proper detection later.
        
        Returns:
            bool: True if CUSTOM convention should be used
        """
        # TODO: Implement proper user intent detection
        # For now, always use MOSFLM convention to match the baseline behavior
        return False

    def _calculate_pix0_vector(self):
        """
        Calculate the position of the first pixel (0,0) in 3D space.

        This follows the C-code convention where pix0_vector represents the
        3D position of pixel (0,0), taking into account the beam center offset
        and detector positioning.

        The calculation depends on:
        1. detector_pivot mode (BEAM vs SAMPLE)
        2. detector convention (MOSFLM vs CUSTOM)

        CRITICAL: C code switches to CUSTOM convention when twotheta_axis is 
        explicitly specified and differs from MOSFLM default [0,0,-1].
        CUSTOM convention removes the +0.5 pixel offset that MOSFLM adds.

        - BEAM pivot: pix0_vector = -Fbeam*fdet_vec - Sbeam*sdet_vec + distance*beam_vec
        - SAMPLE pivot: Calculate pix0_vector BEFORE rotations, then rotate it

        C-Code Implementation Reference (from nanoBragg.c):
        For SAMPLE pivot (lines 376-385):
        ```c
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
        ```
        For BEAM pivot (lines 398-403):
        ```c
        if(detector_pivot == BEAM){
            printf("pivoting detector around direct beam spot\n");
            pix0_vector[1] = -Fbeam*fdet_vector[1]-Sbeam*sdet_vector[1]+distance*beam_vector[1];
            pix0_vector[2] = -Fbeam*fdet_vector[2]-Sbeam*sdet_vector[2]+distance*beam_vector[2];
            pix0_vector[3] = -Fbeam*fdet_vector[3]-Sbeam*sdet_vector[3]+distance*beam_vector[3];
        }
        ```
        
        MOSFLM vs CUSTOM convention (from nanoBragg.c lines 1218-1219 vs 1236-1239):
        MOSFLM: Fbeam = Ybeam + 0.5*pixel_size, Sbeam = Xbeam + 0.5*pixel_size
        CUSTOM: Fclose = Xbeam, Sclose = Ybeam (no +0.5 offset)

        Note: This uses pixel centers at integer indices.
        """
        from ..config import DetectorPivot, DetectorConvention
        from ..utils.geometry import angles_to_rotation_matrix, rotate_axis
        from ..utils.units import degrees_to_radians

        if self.config.detector_pivot == DetectorPivot.BEAM:
            # BEAM pivot mode: detector rotates around the direct beam spot
            # Use exact C-code formula: pix0_vector = -Fbeam*fdet_vec - Sbeam*sdet_vec + distance*beam_vec
            
            # Calculate Fbeam and Sbeam exactly as C code does
            # MOSFLM convention: Add 0.5 pixel offset
            Fbeam_pixels = self.config.beam_center_f / self.config.pixel_size_mm  # mm to pixels (should be 512)
            Sbeam_pixels = self.config.beam_center_s / self.config.pixel_size_mm  # mm to pixels (should be 512)
            Fbeam = (Fbeam_pixels + 0.5) * self.pixel_size  # Add 0.5 pixel, convert to meters
            Sbeam = (Sbeam_pixels + 0.5) * self.pixel_size  # Add 0.5 pixel, convert to meters
            
            # Set beam vector based on convention
            if self.config.detector_convention == DetectorConvention.MOSFLM:
                beam_vector = torch.tensor(
                    [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype
                )
            else:
                # XDS convention uses [0, 0, 1] as beam vector
                beam_vector = torch.tensor(
                    [0.0, 0.0, 1.0], device=self.device, dtype=self.dtype
                )
            
            # Use exact C-code formula without distance correction for now
            self.pix0_vector = (
                -Fbeam * self.fdet_vec
                - Sbeam * self.sdet_vec
                + self.distance * beam_vector
            )
        else:
            # SAMPLE pivot mode: detector rotates around the sample
            # IMPORTANT: Compute pix0 BEFORE rotating, using the same formula as C:
            # pix0 = -Fclose*fdet - Sclose*sdet + close_distance*odet

            # Unrotated basis (by convention)
            if self.config.detector_convention == DetectorConvention.MOSFLM:
                # PHASE 1 FIX: Corrected initial MOSFLM basis vectors
                fdet_initial = torch.tensor([0.0, -1.0, 0.0], device=self.device, dtype=self.dtype)  # Fast along negative Y
                sdet_initial = torch.tensor([0.0, 0.0, -1.0], device=self.device, dtype=self.dtype)  # Slow along negative Z
                odet_initial = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)   # Origin along positive X
            else:
                # XDS convention
                fdet_initial = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)
                sdet_initial = torch.tensor([0.0, 1.0, 0.0], device=self.device, dtype=self.dtype)
                odet_initial = torch.tensor([0.0, 0.0, 1.0], device=self.device, dtype=self.dtype)

            # Distances from pixel (0,0) center to the beam spot, measured along detector axes
            # Convention handling: MOSFLM adds 0.5 pixel offset, CUSTOM does not
            # CRITICAL: Apply the same axis mapping as BEAM pivot:
            # Fclose comes from beam_center_s (corresponds to Ybeam in C)
            # Sclose comes from beam_center_f (corresponds to Xbeam in C)
            
            is_custom = self._is_custom_convention()
            
            if is_custom:
                # CUSTOM convention: No +0.5 pixel offset
                Fclose = self.beam_center_s * self.pixel_size  # meters, no +0.5
                Sclose = self.beam_center_f * self.pixel_size  # meters, no +0.5
            else:
                # MOSFLM convention: Add 0.5 pixel for leading edge reference
                Fclose = (self.beam_center_s + 0.5) * self.pixel_size  # meters
                Sclose = (self.beam_center_f + 0.5) * self.pixel_size  # meters

            # Compute pix0 BEFORE rotations (close_distance == self.distance)
            pix0_initial = (
                -Fclose * fdet_initial
                - Sclose * sdet_initial
                + self.distance * odet_initial
            )

            # Now rotate pix0 with detector_rotx/roty/rotz and twotheta, same as C
            c = self.config
            detector_rotx = degrees_to_radians(c.detector_rotx_deg)
            detector_roty = degrees_to_radians(c.detector_roty_deg)
            detector_rotz = degrees_to_radians(c.detector_rotz_deg)
            detector_twotheta = degrees_to_radians(c.detector_twotheta_deg)

            if not isinstance(detector_rotx, torch.Tensor):
                detector_rotx = torch.tensor(detector_rotx, device=self.device, dtype=self.dtype)
            if not isinstance(detector_roty, torch.Tensor):
                detector_roty = torch.tensor(detector_roty, device=self.device, dtype=self.dtype)
            if not isinstance(detector_rotz, torch.Tensor):
                detector_rotz = torch.tensor(detector_rotz, device=self.device, dtype=self.dtype)
            if not isinstance(detector_twotheta, torch.Tensor):
                detector_twotheta = torch.tensor(detector_twotheta, device=self.device, dtype=self.dtype)

            rotation_matrix = angles_to_rotation_matrix(detector_rotx, detector_roty, detector_rotz)
            pix0_rotated = torch.matmul(rotation_matrix, pix0_initial)

            if isinstance(c.twotheta_axis, torch.Tensor):
                twotheta_axis = c.twotheta_axis.to(device=self.device, dtype=self.dtype)
            elif c.twotheta_axis is not None:
                twotheta_axis = torch.tensor(c.twotheta_axis, device=self.device, dtype=self.dtype)
            else:
                # Default to MOSFLM twotheta axis when not specified
                twotheta_axis = torch.tensor([0.0, 0.0, -1.0], device=self.device, dtype=self.dtype)

            if _nonzero_scalar(detector_twotheta):
                pix0_rotated = rotate_axis(pix0_rotated, twotheta_axis, detector_twotheta)

            self.pix0_vector = pix0_rotated

    def get_pixel_coords(self) -> torch.Tensor:
        """
        Get 3D coordinates of all detector pixels.

        Returns:
            torch.Tensor: Pixel coordinates with shape (spixels, fpixels, 3) in meters
        """
        # Check if geometry has changed by comparing cached values
        geometry_changed = False
        if hasattr(self, "_cached_basis_vectors") and hasattr(
            self, "_cached_pix0_vector"
        ):
            # Check if basis vectors have changed
            if not (
                torch.allclose(self.fdet_vec, self._cached_basis_vectors[0], atol=1e-15)
                and torch.allclose(
                    self.sdet_vec, self._cached_basis_vectors[1], atol=1e-15
                )
                and torch.allclose(
                    self.odet_vec, self._cached_basis_vectors[2], atol=1e-15
                )
            ):
                geometry_changed = True
            # Check if pix0_vector has changed
            if not torch.allclose(
                self.pix0_vector, self._cached_pix0_vector, atol=1e-15
            ):
                geometry_changed = True

        if self._pixel_coords_cache is None or geometry_changed:
            # Create pixel index grids (integer indices, pixel centers handled in pix0_vector)
            s_indices = torch.arange(self.spixels, device=self.device, dtype=self.dtype)
            f_indices = torch.arange(self.fpixels, device=self.device, dtype=self.dtype)

            # Create meshgrid of indices
            s_grid, f_grid = torch.meshgrid(s_indices, f_indices, indexing="ij")

            # Calculate pixel coordinates using pix0_vector as the reference
            # pixel_coords = pix0_vector + s * pixel_size * sdet_vec + f * pixel_size * fdet_vec

            # Expand vectors for broadcasting
            pix0_expanded = self.pix0_vector.unsqueeze(0).unsqueeze(0)  # (1, 1, 3)
            sdet_expanded = self.sdet_vec.unsqueeze(0).unsqueeze(0)  # (1, 1, 3)
            fdet_expanded = self.fdet_vec.unsqueeze(0).unsqueeze(0)  # (1, 1, 3)

            # Calculate pixel coordinates
            pixel_coords = (
                pix0_expanded
                + s_grid.unsqueeze(-1) * self.pixel_size * sdet_expanded
                + f_grid.unsqueeze(-1) * self.pixel_size * fdet_expanded
            )

            self._pixel_coords_cache = pixel_coords

            # Update cached values for future comparisons
            self._cached_basis_vectors = (
                self.fdet_vec.clone(),
                self.sdet_vec.clone(),
                self.odet_vec.clone(),
            )
            self._cached_pix0_vector = self.pix0_vector.clone()
            self._geometry_version += 1

        return self._pixel_coords_cache

    def _calculate_basis_vectors(
        self,
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        """
        Calculate detector basis vectors from configuration.

        This method dynamically computes the detector's fast, slow, and
        normal basis vectors based on user-provided configuration, such as
        detector rotations (`-detector_rot*`) and the two-theta angle.

        The calculation follows this exact sequence:
        1. Initialize basis vectors according to detector convention (MOSFLM or XDS)
        2. Apply detector rotations in order: X-axis, Y-axis, Z-axis
        3. Apply two-theta rotation around the specified axis (if non-zero)

        All rotations preserve the orthonormality of the basis vectors and
        maintain differentiability when rotation angles are provided as tensors
        with requires_grad=True.

        Note: This method takes no parameters as it uses self.config and
        self.device/dtype. The returned vectors are guaranteed to be on the
        same device and have the same dtype as the detector.

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

        Returns:
            Tuple[torch.Tensor, torch.Tensor, torch.Tensor]: The calculated
            (fdet_vec, sdet_vec, odet_vec) basis vectors, each with shape (3,)
        """
        from ..utils.geometry import angles_to_rotation_matrix, rotate_axis

        # Get configuration parameters
        c = self.config

        # Convert rotation angles to radians (handling both scalar and tensor inputs)
        detector_rotx = degrees_to_radians(c.detector_rotx_deg)
        detector_roty = degrees_to_radians(c.detector_roty_deg)
        detector_rotz = degrees_to_radians(c.detector_rotz_deg)
        detector_twotheta = degrees_to_radians(c.detector_twotheta_deg)

        # Ensure all angles are tensors for consistent handling
        if not isinstance(detector_rotx, torch.Tensor):
            detector_rotx = torch.tensor(
                detector_rotx, device=self.device, dtype=self.dtype
            )
        if not isinstance(detector_roty, torch.Tensor):
            detector_roty = torch.tensor(
                detector_roty, device=self.device, dtype=self.dtype
            )
        if not isinstance(detector_rotz, torch.Tensor):
            detector_rotz = torch.tensor(
                detector_rotz, device=self.device, dtype=self.dtype
            )
        if not isinstance(detector_twotheta, torch.Tensor):
            detector_twotheta = torch.tensor(
                detector_twotheta, device=self.device, dtype=self.dtype
            )

        # Initialize basis vectors based on detector convention
        from ..config import DetectorConvention

        if c.detector_convention == DetectorConvention.MOSFLM:
            # PHASE 1 FIX: Corrected MOSFLM basis vectors to match C implementation
            fdet_vec = torch.tensor(
                [0.0, -1.0, 0.0], device=self.device, dtype=self.dtype  # Fast along negative Y
            )
            sdet_vec = torch.tensor(
                [0.0, 0.0, -1.0], device=self.device, dtype=self.dtype  # Slow along negative Z
            )
            odet_vec = torch.tensor(
                [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype   # Origin along positive X (beam)
            )
        elif c.detector_convention == DetectorConvention.XDS:
            # XDS convention: detector surface normal points away from source
            fdet_vec = torch.tensor(
                [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype
            )
            sdet_vec = torch.tensor(
                [0.0, 1.0, 0.0], device=self.device, dtype=self.dtype
            )
            odet_vec = torch.tensor(
                [0.0, 0.0, 1.0], device=self.device, dtype=self.dtype
            )
        else:
            raise ValueError(f"Unknown detector convention: {c.detector_convention}")

        # Apply detector rotations (rotx, roty, rotz) using the C-code's rotate function logic
        # The C-code applies rotations in order: X, then Y, then Z
        rotation_matrix = angles_to_rotation_matrix(
            detector_rotx, detector_roty, detector_rotz
        )

        # Apply the rotation matrix to all three basis vectors
        fdet_vec = torch.matmul(rotation_matrix, fdet_vec)
        sdet_vec = torch.matmul(rotation_matrix, sdet_vec)
        odet_vec = torch.matmul(rotation_matrix, odet_vec)

        # Apply two-theta rotation around the specified axis
        if isinstance(c.twotheta_axis, torch.Tensor):
            twotheta_axis = c.twotheta_axis.to(device=self.device, dtype=self.dtype)
        elif c.twotheta_axis is not None:
            twotheta_axis = torch.tensor(
                c.twotheta_axis, device=self.device, dtype=self.dtype
            )
        else:
            # Default to MOSFLM twotheta axis when not specified
            twotheta_axis = torch.tensor([0.0, 0.0, -1.0], device=self.device, dtype=self.dtype)

        # Check if twotheta is non-zero (handle both scalar and tensor cases)
        if _nonzero_scalar(detector_twotheta):
            fdet_vec = rotate_axis(fdet_vec, twotheta_axis, detector_twotheta)
            sdet_vec = rotate_axis(sdet_vec, twotheta_axis, detector_twotheta)
            odet_vec = rotate_axis(odet_vec, twotheta_axis, detector_twotheta)

        return fdet_vec, sdet_vec, odet_vec

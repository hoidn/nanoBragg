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
        # Use tensor operations to maintain gradient flow
        return bool((torch.abs(x) > 1e-12).item())
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
        # Normalize device to ensure consistency
        if device is not None:
            # Create a dummy tensor on the device to get the actual device with index
            temp = torch.zeros(1, device=device)
            self.device = temp.device
        else:
            self.device = torch.device("cpu")
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

        # Set close_distance (used for obliquity calculations)
        if config.close_distance_mm is not None:
            self.close_distance = config.close_distance_mm / 1000.0  # Convert mm to meters
        else:
            # Default to distance if not specified
            self.close_distance = self.distance

        # Copy dimension parameters
        self.spixels = config.spixels
        self.fpixels = config.fpixels

        # Convert beam center from mm to pixels
        # Note: beam center is given in mm from detector origin
        # MOSFLM convention adds +0.5 pixel offset per AT-PARALLEL-002
        self.beam_center_s: torch.Tensor
        self.beam_center_f: torch.Tensor

        # Import DetectorConvention for checking
        from ..config import DetectorConvention

        # Calculate pixel coordinates from mm values
        beam_center_s_pixels = config.beam_center_s / config.pixel_size_mm
        beam_center_f_pixels = config.beam_center_f / config.pixel_size_mm

        # Apply MOSFLM +0.5 pixel offset for stored beam centers
        # This matches the C-code convention where beam centers include the offset
        if config.detector_convention == DetectorConvention.MOSFLM:
            beam_center_s_pixels = beam_center_s_pixels + 0.5
            beam_center_f_pixels = beam_center_f_pixels + 0.5

        # Convert to tensors on proper device
        if isinstance(beam_center_s_pixels, torch.Tensor):
            self.beam_center_s = beam_center_s_pixels.to(device=self.device, dtype=self.dtype)
        else:
            self.beam_center_s = torch.tensor(
                beam_center_s_pixels,
                device=self.device,
                dtype=self.dtype,
            )

        if isinstance(beam_center_f_pixels, torch.Tensor):
            self.beam_center_f = beam_center_f_pixels.to(device=self.device, dtype=self.dtype)
        else:
            self.beam_center_f = torch.tensor(
                beam_center_f_pixels,
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

        # Initialize attributes used by pyrefly only if not already set
        # These will be set properly in _calculate_pix0_vector
        if not hasattr(self, 'distance_corrected'):
            self.distance_corrected: Optional[torch.Tensor] = None
        if not hasattr(self, 'r_factor'):
            self.r_factor: Optional[torch.Tensor] = None
        if not hasattr(self, 'pix0_vector'):
            self.pix0_vector: Optional[torch.Tensor] = None

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

        This method delegates to the DetectorConfig.should_use_custom_convention()
        method which replicates the exact C code logic.

        Returns:
            bool: True if CUSTOM convention should be used
        """
        return self.config.should_use_custom_convention()

    def _calculate_pix0_vector(self):
        """
        Calculate the position of the first pixel (0,0) in 3D space.

        This follows the C-code convention where pix0_vector represents the
        3D position of pixel (0,0), taking into account the beam center offset
        and detector positioning.

        The calculation depends on:
        1. detector_pivot mode (BEAM vs SAMPLE)
        2. detector convention (MOSFLM vs CUSTOM)
        3. r-factor distance correction (AT-GEO-003)

        CRITICAL: C code switches to CUSTOM convention when twotheta_axis is
        explicitly specified and differs from MOSFLM default [0,0,-1].
        CUSTOM convention removes the +0.5 pixel offset that MOSFLM adds.

        - BEAM pivot: pix0_vector = -Fbeam*fdet_vec - Sbeam*sdet_vec + distance*beam_vec
        - SAMPLE pivot: Calculate pix0_vector BEFORE rotations, then rotate it

        C-Code Implementation Reference (from nanoBragg.c):
        For r-factor calculation (lines 1727-1732):
        ```c
        /* first off, what is the relationship between the two "beam centers"? */
        rotate(odet_vector,vector,detector_rotx,detector_roty,detector_rotz);
        ratio = dot_product(beam_vector,vector);
        if(ratio == 0.0) { ratio = DBL_MIN; }
        if(isnan(close_distance)) close_distance = fabs(ratio*distance);
        distance = close_distance/ratio;
        ```

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

        Note: Pixel coordinates are generated at pixel corners/edges (pixel 0 at position 0, etc.)
        """
        from ..config import DetectorPivot, DetectorConvention
        from ..utils.geometry import angles_to_rotation_matrix, rotate_axis
        from ..utils.units import degrees_to_radians

        # Calculate r-factor for distance correction (AT-GEO-003)
        c = self.config

        # Get rotation angles as tensors
        detector_rotx = degrees_to_radians(c.detector_rotx_deg)
        detector_roty = degrees_to_radians(c.detector_roty_deg)
        detector_rotz = degrees_to_radians(c.detector_rotz_deg)
        detector_twotheta = degrees_to_radians(c.detector_twotheta_deg)

        if not isinstance(detector_rotx, torch.Tensor):
            detector_rotx = torch.tensor(detector_rotx, device=self.device, dtype=self.dtype)
        elif detector_rotx.device != self.device or detector_rotx.dtype != self.dtype:
            detector_rotx = detector_rotx.to(device=self.device, dtype=self.dtype)

        if not isinstance(detector_roty, torch.Tensor):
            detector_roty = torch.tensor(detector_roty, device=self.device, dtype=self.dtype)
        elif detector_roty.device != self.device or detector_roty.dtype != self.dtype:
            detector_roty = detector_roty.to(device=self.device, dtype=self.dtype)

        if not isinstance(detector_rotz, torch.Tensor):
            detector_rotz = torch.tensor(detector_rotz, device=self.device, dtype=self.dtype)
        elif detector_rotz.device != self.device or detector_rotz.dtype != self.dtype:
            detector_rotz = detector_rotz.to(device=self.device, dtype=self.dtype)

        if not isinstance(detector_twotheta, torch.Tensor):
            detector_twotheta = torch.tensor(detector_twotheta, device=self.device, dtype=self.dtype)
        elif detector_twotheta.device != self.device or detector_twotheta.dtype != self.dtype:
            detector_twotheta = detector_twotheta.to(device=self.device, dtype=self.dtype)

        # Get beam vector based on convention
        if self.config.detector_convention == DetectorConvention.MOSFLM:
            beam_vector = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)
        else:
            beam_vector = torch.tensor([0.0, 0.0, 1.0], device=self.device, dtype=self.dtype)

        # Always calculate r-factor to preserve gradient flow
        # When rotations are zero, the rotation matrix will be identity
        # and r-factor will naturally be 1.0
        if True:  # Always execute to preserve gradients
            # Use the actual rotated detector normal (includes ALL rotations including twotheta)
            # This is critical for correct obliquity calculations with tilted detectors
            odet_rotated = self.odet_vec

            # Calculate ratio (r-factor)
            ratio = torch.dot(beam_vector, odet_rotated)

            # Prevent division by zero while maintaining gradient flow
            # Use torch operations to preserve gradients
            min_ratio = torch.tensor(1e-10, device=self.device, dtype=self.dtype)
            ratio = torch.where(
                torch.abs(ratio) < min_ratio,
                torch.sign(ratio) * min_ratio,
                ratio
            )
            # Handle zero case
            ratio = torch.where(
                ratio == 0,
                min_ratio,
                ratio
            )

            # Update distance based on r-factor
            # If close_distance is specified, use it; otherwise calculate from nominal distance
            if hasattr(self.config, 'close_distance_mm') and self.config.close_distance_mm is not None:
                close_distance = self.config.close_distance_mm / 1000.0  # Convert mm to meters
            else:
                close_distance = abs(ratio * self.distance)  # Default from C code

            # Update the actual distance using r-factor (implements AT-GEO-003)
            self.distance_corrected = close_distance / ratio

            # CRITICAL: Update the stored close_distance for obliquity calculations
            # This is needed when detector is rotated (e.g., with twotheta)
            self.close_distance = close_distance

        # Store r-factor for later verification
        # Ensure it's a tensor with correct dtype
        if isinstance(ratio, torch.Tensor):
            self.r_factor = ratio.to(device=self.device, dtype=self.dtype)
        else:
            self.r_factor = torch.tensor(ratio, device=self.device, dtype=self.dtype)

        if self.config.detector_pivot == DetectorPivot.BEAM:
            # BEAM pivot mode: detector rotates around the direct beam spot
            # Use exact C-code formula: pix0_vector = -Fbeam*fdet_vec - Sbeam*sdet_vec + distance*beam_vec
            
            # Calculate Fbeam and Sbeam from beam centers
            # For MOSFLM: Fbeam = Ybeam + 0.5*pixel, Sbeam = Xbeam + 0.5*pixel
            # c_reference_utils now correctly maps: Xbeam=beam_center_s, Ybeam=beam_center_f
            # Therefore: Fbeam=beam_center_f, Sbeam=beam_center_s (no swap needed)
            # The beam centers already include the MOSFLM +0.5 pixel offset from __init__

            # Direct mapping: no axis swap needed
            Fbeam = self.beam_center_f * self.pixel_size  # F (fast coord) ← beam_f (fast param)
            Sbeam = self.beam_center_s * self.pixel_size  # S (slow coord) ← beam_s (slow param)
            
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
            
            # Use exact C-code formula WITH distance correction (AT-GEO-003)
            self.pix0_vector = (
                -Fbeam * self.fdet_vec
                - Sbeam * self.sdet_vec
                + self.distance_corrected * beam_vector
            )
        else:
            # SAMPLE pivot mode: detector rotates around the sample
            # IMPORTANT: Compute pix0 BEFORE rotating, using the same formula as C:
            # pix0 = -Fclose*fdet - Sclose*sdet + close_distance*odet

            # Unrotated basis (by convention)
            if self.config.detector_convention == DetectorConvention.MOSFLM:
                # PHASE 1 FIX: Corrected initial MOSFLM basis vectors
                fdet_initial = torch.tensor([0.0, 0.0, 1.0], device=self.device, dtype=self.dtype)   # Fast along +Z (CORRECT)
                sdet_initial = torch.tensor([0.0, -1.0, 0.0], device=self.device, dtype=self.dtype)  # Slow along -Y (CORRECT)
                odet_initial = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)   # Normal along +X (CORRECT)
            elif self.config.detector_convention == DetectorConvention.XDS:
                # XDS convention
                fdet_initial = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)
                sdet_initial = torch.tensor([0.0, 1.0, 0.0], device=self.device, dtype=self.dtype)
                odet_initial = torch.tensor([0.0, 0.0, 1.0], device=self.device, dtype=self.dtype)
            elif self.config.detector_convention == DetectorConvention.DIALS:
                # DIALS convention
                fdet_initial = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)
                sdet_initial = torch.tensor([0.0, 1.0, 0.0], device=self.device, dtype=self.dtype)
                odet_initial = torch.tensor([0.0, 0.0, 1.0], device=self.device, dtype=self.dtype)
            else:
                raise ValueError(f"Unknown detector convention: {self.config.detector_convention}")

            # Distances from pixel (0,0) center to the beam spot, measured along detector axes
            # Mapping clarification:
            # - In C code: Fbeam = Ybeam + 0.5*pixel, Sbeam = Xbeam + 0.5*pixel (MOSFLM)
            # - In c_reference_utils.py: Xbeam=beam_center_s, Ybeam=beam_center_f
            # - In PyTorch: beam_center_f is fast, beam_center_s is slow
            # For consistency with BEAM pivot mode:
            # - Fclose (fast coord) ← beam_center_f (fast param)
            # - Sclose (slow coord) ← beam_center_s (slow param)
            # NOTE: The beam centers already have the +0.5 offset from __init__ for MOSFLM!

            # The beam centers already include the MOSFLM +0.5 pixel offset from __init__
            # Use consistent mapping with BEAM pivot mode: no axis swap
            Fclose = self.beam_center_f * self.pixel_size  # F (fast coord) ← beam_f (fast param)
            Sclose = self.beam_center_s * self.pixel_size  # S (slow coord) ← beam_s (slow param)

            # Compute pix0 BEFORE rotations using close_distance if specified
            # When close_distance is provided, use it directly for SAMPLE pivot
            if hasattr(self.config, 'close_distance_mm') and self.config.close_distance_mm is not None:
                initial_distance = self.config.close_distance_mm / 1000.0  # Convert mm to meters
            else:
                initial_distance = self.distance  # Use nominal distance

            pix0_initial = (
                -Fclose * fdet_initial
                - Sclose * sdet_initial
                + initial_distance * odet_initial
            )

            # Now rotate pix0 with detector_rotx/roty/rotz and twotheta, same as C
            # (rotation angles already converted to tensors above)
            rotation_matrix = angles_to_rotation_matrix(detector_rotx, detector_roty, detector_rotz)
            pix0_rotated = torch.matmul(rotation_matrix, pix0_initial)

            if isinstance(c.twotheta_axis, torch.Tensor):
                twotheta_axis = c.twotheta_axis.to(device=self.device, dtype=self.dtype)
            elif c.twotheta_axis is not None:
                twotheta_axis = torch.tensor(c.twotheta_axis, device=self.device, dtype=self.dtype)
            else:
                # Default to convention-specific axis (set in config.__post_init__)
                # MOSFLM uses [0, 0, -1], XDS uses [1, 0, 0], etc.
                # This should already be set in config, but fallback to MOSFLM default
                twotheta_axis = torch.tensor([0.0, 0.0, -1.0], device=self.device, dtype=self.dtype)

            # Always apply twotheta rotation to preserve gradients
            # When detector_twotheta is zero, this will be identity
            pix0_rotated = rotate_axis(pix0_rotated, twotheta_axis, detector_twotheta)

            self.pix0_vector = pix0_rotated

    def get_pixel_coords(self) -> torch.Tensor:
        """
        Get 3D coordinates of all detector pixels.

        Supports both planar and curved (spherical) detector mappings.
        For curved detector: pixels are mapped to a spherical arc by rotating
        from the beam direction by angles Sdet/distance and Fdet/distance.

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
            if self.config.curved_detector:
                # Curved detector mapping (spherical arc)
                pixel_coords = self._compute_curved_pixel_coords()
            else:
                # Standard planar detector mapping
                pixel_coords = self._compute_planar_pixel_coords()

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

    def _compute_planar_pixel_coords(self) -> torch.Tensor:
        """
        Compute pixel coordinates for a standard planar detector.

        Returns:
            torch.Tensor: Pixel coordinates with shape (spixels, fpixels, 3) in meters
        """
        # Create pixel index grids - pixel centers to match C code behavior
        # The C code uses pixel centers (0.5, 1.5, 2.5, ...) not corners
        # Adding 0.5 to indices places coordinates at pixel centers
        s_indices = torch.arange(self.spixels, device=self.device, dtype=self.dtype) + 0.5
        f_indices = torch.arange(self.fpixels, device=self.device, dtype=self.dtype) + 0.5

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

        return pixel_coords

    def _compute_curved_pixel_coords(self) -> torch.Tensor:
        """
        Compute pixel coordinates for a curved (spherical) detector.

        Per spec: "start at distance along b and rotate about s and f by small angles
        Sdet/distance and Fdet/distance respectively."

        Returns:
            torch.Tensor: Pixel coordinates with shape (spixels, fpixels, 3) in meters
        """
        # Create pixel index grids - pixel centers to match C code behavior
        # The C code uses pixel centers (0.5, 1.5, 2.5, ...) not corners
        # Adding 0.5 to indices places coordinates at pixel centers
        s_indices = torch.arange(self.spixels, device=self.device, dtype=self.dtype) + 0.5
        f_indices = torch.arange(self.fpixels, device=self.device, dtype=self.dtype) + 0.5
        s_grid, f_grid = torch.meshgrid(s_indices, f_indices, indexing="ij")

        # Calculate Sdet and Fdet in the detector plane
        # Per spec, these are relative to pix0_vector (the detector origin)
        Sdet = s_grid * self.pixel_size  # meters
        Fdet = f_grid * self.pixel_size  # meters

        # For curved detector, we need to map each (Fdet, Sdet) point to a sphere
        # The idea is that each pixel is at the same distance from the sample,
        # but at different angular positions

        # The beam direction points from sample toward source
        # So -beam_vector points from sample toward detector
        beam_dir = -self.beam_vector

        # Compute the angular offsets for each pixel
        # These are based on the detector plane coordinates
        # We use the small angle approximation: tan(θ) ≈ θ for small θ

        # The detector plane is initially perpendicular to the beam
        # In the detector plane, we have coordinates (Fdet, Sdet)
        # We need to find the angles to rotate from the beam direction

        # For a planar detector, a pixel at (Fdet, Sdet) would be at:
        # P_planar = pix0_vector + Fdet * fdet_vec + Sdet * sdet_vec

        # For a curved detector, we want all pixels at distance R from origin
        # We achieve this by rotating the beam direction by small angles

        # The angle to rotate about the s-axis (affects f-coordinate)
        # tan(angle_s) = Fdet / distance, for small angles: angle_s ≈ Fdet / distance
        angle_about_s = Fdet / self.distance

        # The angle to rotate about the f-axis (affects s-coordinate)
        # tan(angle_f) = Sdet / distance, for small angles: angle_f ≈ Sdet / distance
        angle_about_f = Sdet / self.distance

        # Apply rotations using Rodriguez formula for small angles
        # For small angles, rotate(v, axis, θ) ≈ v + θ * (axis × v)

        # Rotation about s-axis by angle_about_s
        # s × beam_dir gives a vector in the f-o plane
        cross_s_beam = torch.cross(self.sdet_vec, beam_dir, dim=0)

        # Rotation about f-axis by angle_about_f
        # f × beam_dir gives a vector in the s-o plane
        cross_f_beam = torch.cross(self.fdet_vec, beam_dir, dim=0)

        # Expand for broadcasting
        beam_expanded = beam_dir.unsqueeze(0).unsqueeze(0)  # (1, 1, 3)
        cross_s_expanded = cross_s_beam.unsqueeze(0).unsqueeze(0)  # (1, 1, 3)
        cross_f_expanded = cross_f_beam.unsqueeze(0).unsqueeze(0)  # (1, 1, 3)

        # Apply both rotations (small angle approximation)
        # The rotated direction vector
        direction = (
            beam_expanded
            + angle_about_s.unsqueeze(-1) * cross_s_expanded  # Rotation about s
            + angle_about_f.unsqueeze(-1) * cross_f_expanded  # Rotation about f
        )

        # Normalize to get unit direction vector
        direction_norm = torch.norm(direction, dim=-1, keepdim=True)
        direction_normalized = direction / direction_norm

        # Each pixel is at distance from the sample
        # Note: We don't add pix0_vector here because for curved detector,
        # pixels are positioned on a sphere centered at the sample
        pixel_coords = self.distance * direction_normalized

        return pixel_coords

    def get_solid_angle(self, pixel_coords: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Calculate the solid angle factor for each pixel.

        Per spec section "Pixel mapping and solid angle":
        - Default: Ω = (pixel_size^2 / |pos|^2) · (close_distance/|pos|)
        - With point_pixel: Ω = 1/|pos|^2

        Args:
            pixel_coords: Optional pre-computed pixel coordinates. If None, will compute them.
                         Shape should be (spixels, fpixels, 3) in meters.

        Returns:
            torch.Tensor: Solid angle factor for each pixel, shape (spixels, fpixels)
        """
        # Get pixel coordinates if not provided
        if pixel_coords is None:
            pixel_coords = self.get_pixel_coords()

        # Calculate distance from sample to each pixel
        R = torch.norm(pixel_coords, dim=-1)  # Shape: (spixels, fpixels)

        if self.config.point_pixel:
            # Point pixel mode: use 1/R^2 solid angle only (no obliquity)
            omega = 1.0 / (R * R)
        else:
            # Default mode: include pixel size and obliquity factor
            # Ω = (pixel_size^2 / R^2) · (close_distance/R)
            # where close_distance is the minimum distance along detector normal

            # The obliquity factor is close_distance/R
            # For the standard case, close_distance = distance * cos(angle)
            # where angle is between beam and detector normal
            omega = (self.pixel_size * self.pixel_size) / (R * R) * (self.close_distance / R)

        return omega

    @property
    def beam_vector(self) -> torch.Tensor:
        """
        Get the beam vector based on detector convention.

        Returns:
            torch.Tensor: Unit beam vector pointing from sample toward source
        """
        if self.config.detector_convention == DetectorConvention.MOSFLM:
            return torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)
        else:
            # XDS, DIALS, and CUSTOM conventions use beam along +Z
            return torch.tensor([0.0, 0.0, 1.0], device=self.device, dtype=self.dtype)

    def get_r_factor(self) -> torch.Tensor:
        """
        Get the r-factor (ratio) used for distance correction.

        r-factor = dot(beam_vector, rotated_detector_normal)

        Returns:
            torch.Tensor: r-factor value
        """
        if not hasattr(self, 'r_factor'):
            # Calculate on demand if not already computed
            self._calculate_pix0_vector()
        # Ensure r_factor is a tensor with correct dtype
        if not isinstance(self.r_factor, torch.Tensor):
            self.r_factor = torch.tensor(self.r_factor, device=self.device, dtype=self.dtype)
        else:
            # Ensure dtype consistency
            self.r_factor = self.r_factor.to(device=self.device, dtype=self.dtype)
        return self.r_factor

    def get_corrected_distance(self) -> torch.Tensor:
        """
        Get the corrected distance after r-factor calculation.

        distance = close_distance / r-factor

        Returns:
            torch.Tensor: Corrected distance in meters
        """
        if not hasattr(self, 'distance_corrected'):
            # Calculate on demand if not already computed
            self._calculate_pix0_vector()
        # Ensure distance_corrected is a tensor with correct dtype
        if not isinstance(self.distance_corrected, torch.Tensor):
            self.distance_corrected = torch.tensor(self.distance_corrected, device=self.device, dtype=self.dtype)
        else:
            # Ensure dtype consistency
            self.distance_corrected = self.distance_corrected.to(device=self.device, dtype=self.dtype)
        return self.distance_corrected

    def verify_beam_center_preservation(self, tolerance: float = 1e-6) -> Tuple[bool, dict]:
        """
        Verify that the beam center is preserved after detector rotations.

        This implements the acceptance test AT-GEO-003: After all detector transformations,
        the direct beam position should still map to the user-specified beam center.

        For BEAM pivot: R = distance_corrected * beam_vector - pix0_vector
        For SAMPLE pivot: The preservation is verified differently as per spec

        Args:
            tolerance: Tolerance for beam center comparison (in meters)

        Returns:
            tuple: (is_preserved, details_dict) where details_dict contains:
                - 'original_beam_f': Original beam center F component (meters)
                - 'original_beam_s': Original beam center S component (meters)
                - 'computed_beam_f': Computed beam center F after transformations
                - 'computed_beam_s': Computed beam center S after transformations
                - 'error_f': Difference in F component
                - 'error_s': Difference in S component
                - 'max_error': Maximum absolute error
        """
        from ..config import DetectorConvention, DetectorPivot

        # Get beam vector
        if self.config.detector_convention == DetectorConvention.MOSFLM:
            beam_vector = torch.tensor([1.0, 0.0, 0.0], device=self.device, dtype=self.dtype)
        else:
            beam_vector = torch.tensor([0.0, 0.0, 1.0], device=self.device, dtype=self.dtype)

        # Calculate direct beam position after all transformations
        # For both BEAM and SAMPLE pivots, the formula is the same:
        # R = distance_corrected * beam_vector - pix0_vector
        # This works because for SAMPLE pivot, pix0_vector is already rotated
        R = self.distance_corrected * beam_vector - self.pix0_vector

        # Project onto detector basis vectors to get Fbeam and Sbeam
        Fbeam_computed = torch.dot(R, self.fdet_vec)
        Sbeam_computed = torch.dot(R, self.sdet_vec)

        # Get original beam center in meters
        # Account for the +0.5 pixel offset in MOSFLM convention
        # beam_center_f and beam_center_s are already in pixels
        is_custom = self._is_custom_convention()
        # beam_center_f and beam_center_s already have the MOSFLM +0.5 pixel offset applied in __init__
        # so we just need to convert to meters
        Fbeam_original = self.beam_center_f * self.pixel_size
        Sbeam_original = self.beam_center_s * self.pixel_size

        # Calculate errors
        error_f = abs(Fbeam_computed - Fbeam_original)
        error_s = abs(Sbeam_computed - Sbeam_original)
        max_error = max(error_f, error_s)

        # Check if preserved within tolerance
        is_preserved = max_error < tolerance

        details = {
            'original_beam_f': Fbeam_original.item() if isinstance(Fbeam_original, torch.Tensor) else Fbeam_original,
            'original_beam_s': Sbeam_original.item() if isinstance(Sbeam_original, torch.Tensor) else Sbeam_original,
            'computed_beam_f': Fbeam_computed.item(),
            'computed_beam_s': Sbeam_computed.item(),
            'error_f': error_f.item() if isinstance(error_f, torch.Tensor) else error_f,
            'error_s': error_s.item() if isinstance(error_s, torch.Tensor) else error_s,
            'max_error': max_error.item() if isinstance(max_error, torch.Tensor) else max_error,
        }

        return bool(is_preserved), details

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
        elif detector_rotx.device != self.device or detector_rotx.dtype != self.dtype:
            detector_rotx = detector_rotx.to(device=self.device, dtype=self.dtype)

        if not isinstance(detector_roty, torch.Tensor):
            detector_roty = torch.tensor(
                detector_roty, device=self.device, dtype=self.dtype
            )
        elif detector_roty.device != self.device or detector_roty.dtype != self.dtype:
            detector_roty = detector_roty.to(device=self.device, dtype=self.dtype)

        if not isinstance(detector_rotz, torch.Tensor):
            detector_rotz = torch.tensor(
                detector_rotz, device=self.device, dtype=self.dtype
            )
        elif detector_rotz.device != self.device or detector_rotz.dtype != self.dtype:
            detector_rotz = detector_rotz.to(device=self.device, dtype=self.dtype)

        if not isinstance(detector_twotheta, torch.Tensor):
            detector_twotheta = torch.tensor(
                detector_twotheta, device=self.device, dtype=self.dtype
            )
        elif detector_twotheta.device != self.device or detector_twotheta.dtype != self.dtype:
            detector_twotheta = detector_twotheta.to(device=self.device, dtype=self.dtype)

        # Initialize basis vectors based on detector convention
        from ..config import DetectorConvention

        if c.detector_convention == DetectorConvention.MOSFLM:
            # PHASE 1 FIX: Corrected MOSFLM basis vectors to match C implementation
            fdet_vec = torch.tensor(
                [0.0, 0.0, 1.0], device=self.device, dtype=self.dtype  # Fast along +Z (CORRECT)
            )
            sdet_vec = torch.tensor(
                [0.0, -1.0, 0.0], device=self.device, dtype=self.dtype  # Slow along -Y (CORRECT)
            )
            odet_vec = torch.tensor(
                [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype   # Normal along +X (CORRECT)
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
        elif c.detector_convention == DetectorConvention.DIALS:
            # DIALS convention: beam [0,0,1], f=[1,0,0], s=[0,1,0], o=[0,0,1]
            # Similar to XDS but with specific beam and twotheta axis conventions
            fdet_vec = torch.tensor(
                [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype  # Fast along +X
            )
            sdet_vec = torch.tensor(
                [0.0, 1.0, 0.0], device=self.device, dtype=self.dtype  # Slow along +Y
            )
            odet_vec = torch.tensor(
                [0.0, 0.0, 1.0], device=self.device, dtype=self.dtype  # Normal along +Z
            )
        elif c.detector_convention == DetectorConvention.CUSTOM:
            # CUSTOM convention uses user-provided vectors or defaults to MOSFLM
            if c.custom_fdet_vector is not None:
                fdet_vec = torch.tensor(
                    c.custom_fdet_vector, device=self.device, dtype=self.dtype
                )
            else:
                # Default to MOSFLM fast vector
                fdet_vec = torch.tensor(
                    [0.0, 1.0, 0.0], device=self.device, dtype=self.dtype
                )

            if c.custom_sdet_vector is not None:
                sdet_vec = torch.tensor(
                    c.custom_sdet_vector, device=self.device, dtype=self.dtype
                )
            else:
                # Default to MOSFLM slow vector
                sdet_vec = torch.tensor(
                    [0.0, 0.0, 1.0], device=self.device, dtype=self.dtype
                )

            if c.custom_odet_vector is not None:
                odet_vec = torch.tensor(
                    c.custom_odet_vector, device=self.device, dtype=self.dtype
                )
            else:
                # Default to MOSFLM normal vector
                odet_vec = torch.tensor(
                    [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype
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
            # Default to convention-specific axis (set in config.__post_init__)
            # MOSFLM uses [0, 0, -1], XDS uses [1, 0, 0], etc.
            # This should already be set in config, but fallback to MOSFLM default
            twotheta_axis = torch.tensor([0.0, 0.0, -1.0], device=self.device, dtype=self.dtype)

        # Always apply twotheta rotation to preserve gradients
        # When detector_twotheta is zero, this will be identity
        fdet_vec = rotate_axis(fdet_vec, twotheta_axis, detector_twotheta)
        sdet_vec = rotate_axis(sdet_vec, twotheta_axis, detector_twotheta)
        odet_vec = rotate_axis(odet_vec, twotheta_axis, detector_twotheta)

        return fdet_vec, sdet_vec, odet_vec

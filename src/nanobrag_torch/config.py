"""
Configuration dataclasses for nanoBragg PyTorch implementation.

This module defines strongly-typed configuration objects that are intended to
replace the large set of local variables and command-line parsing logic found
in the original C main() function. Each dataclass will correspond to a physical
component of the simulation (Crystal, Detector, Beam).

For a detailed mapping of these dataclass fields to the original nanoBragg.c 
command-line flags, including implicit conventions and common pitfalls, see:
docs/development/c_to_pytorch_config_map.md

C-Code Implementation Reference (from nanoBragg.c):
The configuration is currently handled by a large argument-parsing loop
in main(). The future dataclasses will encapsulate the variables set
in this block.

Representative examples from nanoBragg.c (lines 506-1101):

// Crystal Parameters
if(0==strcmp(argv[i], "-N") && (argc > (i+1)))
{
    Na = Nb = Nc = atoi(argv[i+1]);
    continue;
}
if(strstr(argv[i], "-cell") && (argc > (i+1)))
{
    // ...
    a[0] = atof(argv[i+1]);
    // ...
    alpha = atof(argv[i+4])/RTD;
    // ...
}
if((strstr(argv[i], "-mosaic") && ... ) && (argc > (i+1)))
{
    mosaic_spread = atof(argv[i+1])/RTD;
}

// Beam Parameters
if((strstr(argv[i], "-lambda") || strstr(argv[i], "-wave")) && (argc > (i+1)))
{
    lambda0 = atof(argv[i+1])/1.0e10;
}
if(strstr(argv[i], "-fluence") && (argc > (i+1)))
{
    fluence = atof(argv[i+1]);
}

// Detector Parameters
if(strstr(argv[i], "-distance") && (argc > (i+1)))
{
    distance = atof(argv[i+1])/1000.0;
    detector_pivot = BEAM;
}
if(strstr(argv[i], "-pixel") && (argc > (i+1)))
{
    pixel_size = atof(argv[i+1])/1000.0;
}
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple, Union

import numpy as np
import torch


class DetectorConvention(Enum):
    """Detector coordinate system convention."""

    MOSFLM = "mosflm"
    XDS = "xds"
    DIALS = "dials"
    ADXV = "adxv"
    DENZO = "denzo"
    CUSTOM = "custom"  # For user-specified basis vectors


class DetectorPivot(Enum):
    """Detector rotation pivot mode."""

    BEAM = "beam"
    SAMPLE = "sample"


class CrystalShape(Enum):
    """Crystal shape models for lattice factor calculation."""

    SQUARE = "square"  # Parallelepiped/grating using sincg function
    ROUND = "round"    # Spherical/elliptical using sinc3 function
    GAUSS = "gauss"    # Gaussian in reciprocal space
    TOPHAT = "tophat"  # Binary spots/top-hat function


@dataclass
class CrystalConfig:
    """Configuration for crystal properties and orientation.

    This configuration class now supports general triclinic unit cells with all
    six cell parameters (a, b, c, α, β, γ). All cell parameters can accept
    either scalar values or PyTorch tensors, enabling gradient-based optimization
    of crystal parameters from diffraction data.
    """

    # Unit cell parameters (in Angstroms and degrees)
    # These can be either float values or torch.Tensor for differentiability
    cell_a: float = 100.0
    cell_b: float = 100.0
    cell_c: float = 100.0
    cell_alpha: float = 90.0
    cell_beta: float = 90.0
    cell_gamma: float = 90.0

    # Static misset rotation (applied once at initialization)
    # Static crystal orientation angles (degrees) applied as XYZ rotations to reciprocal space vectors
    misset_deg: Tuple[float, float, float] = (0.0, 0.0, 0.0)

    # Random misset generation (for AT-PARALLEL-024)
    misset_random: bool = False  # If True, generate random misset angles using seed
    misset_seed: Optional[int] = None  # Seed for random misset generation (C-compatible LCG)

    # MOSFLM matrix orientation (Phase G - CLI-FLAGS-003)
    # When -mat file is provided, these store the MOSFLM A* orientation in Å⁻¹
    # If None, Crystal uses canonical orientation from cell parameters
    mosflm_a_star: Optional[np.ndarray] = None  # MOSFLM a* reciprocal vector (Å⁻¹)
    mosflm_b_star: Optional[np.ndarray] = None  # MOSFLM b* reciprocal vector (Å⁻¹)
    mosflm_c_star: Optional[np.ndarray] = None  # MOSFLM c* reciprocal vector (Å⁻¹)

    # Spindle rotation parameters
    phi_start_deg: float = 0.0
    osc_range_deg: float = 0.0
    phi_steps: int = 1
    spindle_axis: Tuple[float, float, float] = (0.0, 0.0, 1.0)

    # Mosaicity parameters
    mosaic_spread_deg: float = 0.0
    mosaic_domains: int = 1
    mosaic_seed: Optional[int] = None

    # Crystal size (number of unit cells in each direction)
    N_cells: Tuple[int, int, int] = (1, 1, 1)  # Matches C default

    # Structure factor parameters
    default_F: float = 0.0  # Default structure factor magnitude (matches C default)

    # Crystal shape parameters
    shape: CrystalShape = CrystalShape.SQUARE  # Crystal shape model for F_latt calculation
    fudge: float = 1.0  # Shape parameter scaling factor

    # Sample size in meters (calculated from N_cells and unit cell dimensions)
    # These are computed in __post_init__ and potentially clipped by beam size
    sample_x: Optional[float] = None  # Sample size along a-axis (meters)
    sample_y: Optional[float] = None  # Sample size along b-axis (meters)
    sample_z: Optional[float] = None  # Sample size along c-axis (meters)

    def __post_init__(self):
        """Calculate sample dimensions from unit cell and N_cells."""
        # Calculate sample dimensions in meters (cell parameters are in Angstroms)
        # For simplicity, assume orthogonal axes for sample size calculation
        # This matches the C code behavior
        self.sample_x = self.N_cells[0] * self.cell_a * 1e-10  # Convert Å to meters
        self.sample_y = self.N_cells[1] * self.cell_b * 1e-10
        self.sample_z = self.N_cells[2] * self.cell_c * 1e-10


@dataclass
class DetectorConfig:
    """Configuration for detector geometry and properties.

    This configuration class defines all parameters needed to specify detector
    geometry, position, and orientation. All distance/size parameters are in
    user-friendly millimeter units and will be converted to meters internally.
    All angle parameters are in degrees and will be converted to radians internally.
    """

    # Basic geometry (user units: mm)
    distance_mm: Union[float, torch.Tensor] = 100.0
    pixel_size_mm: Union[float, torch.Tensor] = 0.1
    close_distance_mm: Optional[Union[float, torch.Tensor]] = None  # For AT-GEO-002

    # Detector dimensions
    spixels: int = 1024  # slow axis pixels
    fpixels: int = 1024  # fast axis pixels

    # Beam center (mm from detector origin)
    beam_center_s: Union[float, torch.Tensor, None] = None  # slow axis (auto-calculated if None)
    beam_center_f: Union[float, torch.Tensor, None] = None  # fast axis (auto-calculated if None)

    # Detector rotations (degrees)
    detector_rotx_deg: Union[float, torch.Tensor] = 0.0
    detector_roty_deg: Union[float, torch.Tensor] = 0.0
    detector_rotz_deg: Union[float, torch.Tensor] = 0.0

    # Two-theta rotation (degrees)
    detector_twotheta_deg: Union[float, torch.Tensor] = 0.0
    twotheta_axis: Optional[torch.Tensor] = None  # Will default based on convention

    # Convention and pivot
    detector_convention: DetectorConvention = DetectorConvention.MOSFLM
    detector_pivot: Optional[DetectorPivot] = None  # Will be auto-selected per AT-GEO-002

    # Sampling
    oversample: int = -1  # -1 means auto-select based on crystal size and detector geometry
    oversample_omega: bool = False  # If True, apply solid angle per subpixel (not last-value)
    oversample_polar: bool = False  # If True, apply polarization per subpixel (not last-value)
    oversample_thick: bool = False  # If True, apply absorption per subpixel (not last-value)

    # Detector geometry mode
    curved_detector: bool = False  # If True, use spherical mapping for pixel positions
    point_pixel: bool = False  # If True, use 1/R^2 solid angle only (no obliquity)

    # Detector origin override (CLI-FLAGS-003)
    pix0_override_m: Optional[Union[Tuple[float, float, float], torch.Tensor]] = None  # Override pix0 vector (meters)

    # Custom basis vectors for CUSTOM convention (unit vectors)
    custom_fdet_vector: Optional[Tuple[float, float, float]] = None  # Fast axis direction
    custom_sdet_vector: Optional[Tuple[float, float, float]] = None  # Slow axis direction
    custom_odet_vector: Optional[Tuple[float, float, float]] = None  # Normal direction
    custom_beam_vector: Optional[Tuple[float, float, float]] = None  # Incident beam direction (unit vector)

    # Detector absorption parameters (AT-ABS-001)
    detector_abs_um: Optional[Union[float, torch.Tensor]] = None  # Attenuation depth in micrometers
    detector_thick_um: Union[float, torch.Tensor] = 0.0  # Detector thickness in micrometers
    detector_thicksteps: int = 1  # Number of thickness layers for absorption calculation

    # ROI (Region of Interest) parameters (AT-ROI-001)
    roi_xmin: Optional[int] = None  # Fast axis minimum pixel (inclusive, 0-based)
    roi_xmax: Optional[int] = None  # Fast axis maximum pixel (inclusive, 0-based)
    roi_ymin: Optional[int] = None  # Slow axis minimum pixel (inclusive, 0-based)
    roi_ymax: Optional[int] = None  # Slow axis maximum pixel (inclusive, 0-based)

    # Mask parameters (AT-ROI-001)
    mask_array: Optional[torch.Tensor] = None  # Binary mask array (0=skip, non-zero=include)

    def __post_init__(self):
        """Validate configuration and set defaults.

        Implements AT-GEO-002 automatic pivot selection logic:
        - If only distance_mm is provided (not close_distance_mm): pivot = BEAM
        - If only close_distance_mm is provided: pivot = SAMPLE
        - If detector_pivot is explicitly set: use that (explicit override wins)
        """
        # AT-GEO-002: Automatic pivot selection based on distance parameters
        if self.detector_pivot is None:
            # Determine if distance_mm was explicitly provided (not just defaulted)
            # Note: In real CLI, we'd know if user provided -distance vs -close_distance
            # For testing, we use the presence/absence of close_distance_mm as indicator

            if self.close_distance_mm is not None:
                # Setup B: -close_distance provided -> pivot SHALL be SAMPLE
                self.detector_pivot = DetectorPivot.SAMPLE
                # Use close_distance as the actual distance if distance wasn't provided
                if self.distance_mm == 100.0:  # Default value, likely not explicitly set
                    self.distance_mm = self.close_distance_mm
            else:
                # Setup A: Only -distance provided -> pivot SHALL be BEAM
                self.detector_pivot = DetectorPivot.BEAM
        # Setup C: Explicit -pivot override is already set, keep it

        # Auto-calculate beam centers if not explicitly provided
        # This ensures beam centers scale correctly with detector size
        if self.beam_center_s is None or self.beam_center_f is None:
            detsize_s = self.spixels * self.pixel_size_mm  # Total detector size in slow axis (mm)
            detsize_f = self.fpixels * self.pixel_size_mm  # Total detector size in fast axis (mm)

            if self.detector_convention == DetectorConvention.MOSFLM:
                # MOSFLM convention adds 0.5 pixel offset (per spec AT-GEO-001)
                # For MOSFLM: beam_center = (detsize + pixel_size) / 2
                if self.beam_center_s is None:
                    self.beam_center_s = (detsize_s + self.pixel_size_mm) / 2.0
                if self.beam_center_f is None:
                    self.beam_center_f = (detsize_f + self.pixel_size_mm) / 2.0
            elif self.detector_convention == DetectorConvention.DENZO:
                # DENZO convention: Same as MOSFLM but NO +0.5 pixel offset
                # For DENZO: beam_center = detsize / 2
                if self.beam_center_s is None:
                    self.beam_center_s = detsize_s / 2.0
                if self.beam_center_f is None:
                    self.beam_center_f = detsize_f / 2.0
            elif self.detector_convention == DetectorConvention.ADXV:
                # ADXV convention: Different beam center mapping
                # Per spec: Default Xbeam = (detsize_f + pixel)/2, Ybeam = (detsize_s - pixel)/2
                if self.beam_center_s is None:
                    self.beam_center_s = (detsize_s - self.pixel_size_mm) / 2.0
                if self.beam_center_f is None:
                    self.beam_center_f = (detsize_f + self.pixel_size_mm) / 2.0
            else:
                # XDS, DIALS, and other conventions: center without offset
                # For XDS: beam_center = detsize / 2
                if self.beam_center_s is None:
                    self.beam_center_s = detsize_s / 2.0
                if self.beam_center_f is None:
                    self.beam_center_f = detsize_f / 2.0

        # Set default twotheta axis if not provided
        if self.twotheta_axis is None:
            # Default depends on detector convention (per spec AT-GEO-004)
            if self.detector_convention == DetectorConvention.MOSFLM:
                # MOSFLM convention: twotheta axis is [0, 0, -1]
                self.twotheta_axis = torch.tensor([0.0, 0.0, -1.0])
            elif self.detector_convention == DetectorConvention.DENZO:
                # DENZO convention: Same as MOSFLM for twotheta axis [0, 0, -1]
                self.twotheta_axis = torch.tensor([0.0, 0.0, -1.0])
            elif self.detector_convention == DetectorConvention.XDS:
                # XDS convention: twotheta axis is [1, 0, 0]
                self.twotheta_axis = torch.tensor([1.0, 0.0, 0.0])
            elif self.detector_convention == DetectorConvention.DIALS:
                # DIALS convention: twotheta axis is [0, 1, 0]
                self.twotheta_axis = torch.tensor([0.0, 1.0, 0.0])
            elif self.detector_convention == DetectorConvention.ADXV:
                # ADXV convention: twotheta axis is [-1, 0, 0]
                self.twotheta_axis = torch.tensor([-1.0, 0.0, 0.0])
            else:
                # Default fallback to DIALS axis [0, 1, 0]
                self.twotheta_axis = torch.tensor([0.0, 1.0, 0.0])

        # Validate pixel counts
        if self.spixels <= 0 or self.fpixels <= 0:
            raise ValueError("Pixel counts must be positive")

        # Validate distance and pixel size
        if isinstance(self.distance_mm, (int, float)):
            if self.distance_mm <= 0:
                raise ValueError("Distance must be positive")

        if isinstance(self.pixel_size_mm, (int, float)):
            if self.pixel_size_mm <= 0:
                raise ValueError("Pixel size must be positive")

        # Validate oversample (-1 means auto-select)
        if self.oversample < -1 or self.oversample == 0:
            raise ValueError("Oversample must be -1 (auto-select) or >= 1")

        # Validate and set ROI defaults (AT-ROI-001)
        # If ROI not specified, default to full detector
        if self.roi_xmin is None:
            self.roi_xmin = 0
        if self.roi_xmax is None:
            self.roi_xmax = self.fpixels - 1  # Inclusive, 0-based
        if self.roi_ymin is None:
            self.roi_ymin = 0
        if self.roi_ymax is None:
            self.roi_ymax = self.spixels - 1  # Inclusive, 0-based

        # Validate ROI bounds
        if self.roi_xmin < 0 or self.roi_xmin >= self.fpixels:
            raise ValueError(f"roi_xmin must be in [0, {self.fpixels-1}]")
        if self.roi_xmax < 0 or self.roi_xmax >= self.fpixels:
            raise ValueError(f"roi_xmax must be in [0, {self.fpixels-1}]")
        if self.roi_ymin < 0 or self.roi_ymin >= self.spixels:
            raise ValueError(f"roi_ymin must be in [0, {self.spixels-1}]")
        if self.roi_ymax < 0 or self.roi_ymax >= self.spixels:
            raise ValueError(f"roi_ymax must be in [0, {self.spixels-1}]")
        if self.roi_xmin > self.roi_xmax:
            raise ValueError("roi_xmin must be <= roi_xmax")
        if self.roi_ymin > self.roi_ymax:
            raise ValueError("roi_ymin must be <= roi_ymax")

        # Validate mask array dimensions if provided
        if self.mask_array is not None:
            if self.mask_array.shape != (self.spixels, self.fpixels):
                raise ValueError(f"Mask array shape {self.mask_array.shape} must match detector dimensions ({self.spixels}, {self.fpixels})")

    @classmethod
    def from_cli_args(
        cls,
        distance_mm: Optional[Union[float, torch.Tensor]] = None,
        close_distance_mm: Optional[Union[float, torch.Tensor]] = None,
        pivot: Optional[str] = None,
        **kwargs
    ) -> "DetectorConfig":
        """Create DetectorConfig from CLI-style arguments with AT-GEO-002 logic.

        This factory method implements the AT-GEO-002 pivot selection requirements:
        - If only -distance is provided: pivot = BEAM
        - If only -close_distance is provided: pivot = SAMPLE
        - If -pivot is explicitly provided: use that (override wins)

        Args:
            distance_mm: Value from -distance flag (None if not provided)
            close_distance_mm: Value from -close_distance flag (None if not provided)
            pivot: Explicit pivot override from -pivot flag ("beam" or "sample")
            **kwargs: Other DetectorConfig parameters

        Returns:
            DetectorConfig with appropriate pivot setting per AT-GEO-002
        """
        # Determine detector_pivot based on AT-GEO-002 rules
        if pivot is not None:
            # Setup C: Explicit pivot override wins
            detector_pivot = DetectorPivot.BEAM if pivot.lower() == "beam" else DetectorPivot.SAMPLE
            # If only close_distance provided, use it as distance
            if close_distance_mm is not None and distance_mm is None:
                distance_mm = close_distance_mm
        elif close_distance_mm is not None and distance_mm is None:
            # Setup B: Only -close_distance provided -> SAMPLE pivot
            detector_pivot = DetectorPivot.SAMPLE
            distance_mm = close_distance_mm  # Use close_distance as actual distance
        elif distance_mm is not None and close_distance_mm is None:
            # Setup A: Only -distance provided -> BEAM pivot
            detector_pivot = DetectorPivot.BEAM
        else:
            # Default case (shouldn't happen in normal CLI usage)
            detector_pivot = None  # Let __post_init__ decide

        # Create config with determined pivot
        return cls(
            distance_mm=distance_mm if distance_mm is not None else 100.0,
            close_distance_mm=close_distance_mm,
            detector_pivot=detector_pivot,
            **kwargs
        )

    def should_use_custom_convention(self) -> bool:
        """
        Determine if CUSTOM convention should be used based on C code logic.

        The C code switches to CUSTOM convention when:
        1. -twotheta_axis is explicitly passed to the command line
        2. AND the twotheta_axis differs from the default for the current convention

        This exactly replicates the logic in build_nanobragg_command() which only
        passes -twotheta_axis when the axis is NOT the convention default.

        Returns:
            bool: True if CUSTOM convention should be used (no 0.5 pixel offset)
        """
        if self.twotheta_axis is None:
            return False

        # Convert twotheta_axis to list for comparison
        if hasattr(self.twotheta_axis, 'tolist'):
            axis = self.twotheta_axis.tolist()
        else:
            axis = list(self.twotheta_axis)

        # Check if axis differs from the convention default
        if self.detector_convention == DetectorConvention.MOSFLM:
            # MOSFLM default is [0, 0, -1]
            is_default = (abs(axis[0]) < 1e-6 and abs(axis[1]) < 1e-6 and abs(axis[2] + 1.0) < 1e-6)
        elif self.detector_convention == DetectorConvention.DENZO:
            # DENZO default is [0, 0, -1] (same as MOSFLM)
            is_default = (abs(axis[0]) < 1e-6 and abs(axis[1]) < 1e-6 and abs(axis[2] + 1.0) < 1e-6)
        elif self.detector_convention == DetectorConvention.XDS:
            # XDS default is [1, 0, 0]
            is_default = (abs(axis[0] - 1.0) < 1e-6 and abs(axis[1]) < 1e-6 and abs(axis[2]) < 1e-6)
        elif self.detector_convention == DetectorConvention.DIALS:
            # DIALS default is [0, 1, 0]
            is_default = (abs(axis[0]) < 1e-6 and abs(axis[1] - 1.0) < 1e-6 and abs(axis[2]) < 1e-6)
        elif self.detector_convention == DetectorConvention.ADXV:
            # ADXV default is [-1, 0, 0]
            is_default = (abs(axis[0] + 1.0) < 1e-6 and abs(axis[1]) < 1e-6 and abs(axis[2]) < 1e-6)
        else:
            # CUSTOM convention or unknown - default to False
            return False

        # CUSTOM convention is used when twotheta_axis is NOT the default
        return not is_default


@dataclass
class BeamConfig:
    """Configuration for X-ray beam properties.

    Supports multiple sources for beam divergence and spectral dispersion (AT-SRC-001).
    """

    # Basic beam properties
    wavelength_A: float = 1.0  # X-ray wavelength in Angstroms (matches C default)

    # Source geometry (simplified)
    N_source_points: int = 1  # Number of source points for beam divergence
    source_distance_mm: float = 10000.0  # Distance from source to sample (mm)
    source_size_mm: float = 0.0  # Source size (0 = point source)

    # Multiple sources support (AT-SRC-001)
    source_directions: Optional[torch.Tensor] = None  # (N, 3) unit direction vectors from sample to sources
    source_weights: Optional[torch.Tensor] = None  # (N,) source weights (ignored per spec, all equal)
    source_wavelengths: Optional[torch.Tensor] = None  # (N,) wavelengths in meters for each source

    # Beam polarization
    polarization_factor: float = 0.0  # Kahn polarization factor K in [0,1] (0.0 = unpolarized, matches C default)
    nopolar: bool = False  # If True, force polarization factor to 1 (disable polarization)
    polarization_axis: tuple[float, float, float] = (0.0, 0.0, 1.0)  # Polarization E-vector direction

    # Flux and fluence parameters (AT-FLU-001)
    flux: float = 0.0  # Photons per second
    exposure: float = 0.0  # Exposure time in seconds
    beamsize_mm: float = 0.0  # Beam size in mm (used for fluence calculation and sample clipping)
    fluence: float = 125932015286227086360700780544.0  # Photons per square meter (default from C code)

    # Resolution cutoff
    dmin: float = 0.0  # Minimum d-spacing in Angstroms (0 = no cutoff)

    # Water background
    water_size_um: float = 0.0  # Water thickness in micrometers for background calculation (0 = no background)

    def __post_init__(self):
        """Calculate fluence from flux/exposure/beamsize if provided (AT-FLU-001).

        Per spec: fluence SHALL be recomputed as flux·exposure/beamsize^2 whenever
        flux != 0 and exposure > 0 and beamsize ≥ 0.
        """
        if self.flux != 0 and self.exposure > 0 and self.beamsize_mm >= 0:
            # Convert beamsize from mm to meters for fluence calculation
            beamsize_m = self.beamsize_mm / 1000.0
            if beamsize_m > 0:
                self.fluence = self.flux * self.exposure / (beamsize_m * beamsize_m)
            # If beamsize is 0 but flux and exposure are set, keep existing fluence

        # Also handle case where exposure > 0 recomputes flux to be consistent
        elif self.exposure > 0 and self.beamsize_mm > 0 and self.fluence > 0:
            beamsize_m = self.beamsize_mm / 1000.0
            self.flux = self.fluence * (beamsize_m * beamsize_m) / self.exposure


@dataclass
class NoiseConfig:
    """Configuration for noise generation (AT-NOISE-001).

    Controls Poisson noise generation and related parameters for
    realistic detector readout simulation.
    """

    # Random seed for noise generation
    seed: Optional[int] = None  # If None, uses negative wall-clock time per spec

    # ADC parameters
    adc_offset: float = 40.0  # ADC offset added to all pixels
    readout_noise: float = 3.0  # Gaussian readout noise sigma

    # Detector saturation
    overload_value: float = 65535.0  # Maximum value before saturation

    # Output control
    generate_noise_image: bool = False  # Whether to generate noisy image
    intfile_scale: float = 1.0  # Scale factor before noise generation

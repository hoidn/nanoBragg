"""
Configuration dataclasses for nanoBragg PyTorch implementation.

This module defines strongly-typed configuration objects that are intended to
replace the large set of local variables and command-line parsing logic found
in the original C main() function. Each dataclass will correspond to a physical
component of the simulation (Crystal, Detector, Beam).

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

import torch


class DetectorConvention(Enum):
    """Detector coordinate system convention."""
    MOSFLM = "mosflm"
    XDS = "xds"


class DetectorPivot(Enum):
    """Detector rotation pivot mode."""
    BEAM = "beam"
    SAMPLE = "sample"


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
    N_cells: Tuple[int, int, int] = (5, 5, 5)


@dataclass
class DetectorConfig:
    """Configuration for detector geometry and properties.
    
    This configuration class defines all parameters needed to specify detector
    geometry, position, and orientation. All distance/size parameters are in
    user-friendly millimeter units and will be converted to Angstroms internally.
    All angle parameters are in degrees and will be converted to radians internally.
    """
    
    # Basic geometry (user units: mm)
    distance_mm: Union[float, torch.Tensor] = 100.0
    pixel_size_mm: Union[float, torch.Tensor] = 0.1
    
    # Detector dimensions
    spixels: int = 1024  # slow axis pixels
    fpixels: int = 1024  # fast axis pixels
    
    # Beam center (mm from detector origin)
    beam_center_s: Union[float, torch.Tensor] = 51.2  # slow axis
    beam_center_f: Union[float, torch.Tensor] = 51.2  # fast axis
    
    # Detector rotations (degrees)
    detector_rotx_deg: Union[float, torch.Tensor] = 0.0
    detector_roty_deg: Union[float, torch.Tensor] = 0.0
    detector_rotz_deg: Union[float, torch.Tensor] = 0.0
    
    # Two-theta rotation (degrees)
    detector_twotheta_deg: Union[float, torch.Tensor] = 0.0
    twotheta_axis: Optional[torch.Tensor] = None  # Will default to [0,1,0]
    
    # Convention and pivot
    detector_convention: DetectorConvention = DetectorConvention.MOSFLM
    detector_pivot: DetectorPivot = DetectorPivot.SAMPLE
    
    # Sampling
    oversample: int = 1
    
    def __post_init__(self):
        """Validate configuration and set defaults."""
        # Set default twotheta axis if not provided
        if self.twotheta_axis is None:
            # Default depends on detector convention
            if self.detector_convention == DetectorConvention.MOSFLM:
                # MOSFLM convention: twotheta axis is [0, 0, -1] (C-code line 1194)
                self.twotheta_axis = torch.tensor([0.0, 0.0, -1.0])
            elif self.detector_convention == DetectorConvention.XDS:
                # XDS convention: twotheta axis is [1, 0, 0] (C-code line 1221)
                self.twotheta_axis = torch.tensor([1.0, 0.0, 0.0])
            else:
                # Default fallback
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
        
        # Validate oversample
        if self.oversample < 1:
            raise ValueError("Oversample must be at least 1")


@dataclass
class BeamConfig:
    """Configuration for X-ray beam properties.
    
    Simplified implementation for detector geometry testing.
    """
    
    # Basic beam properties
    wavelength_A: float = 6.2  # X-ray wavelength in Angstroms
    
    # Source geometry (simplified)
    N_source_points: int = 1  # Number of source points for beam divergence
    source_distance_mm: float = 10000.0  # Distance from source to sample (mm)
    source_size_mm: float = 0.0  # Source size (0 = point source)
    
    # Beam polarization and flux (simplified)
    polarization_factor: float = 1.0  # Polarization correction factor
    flux: float = 1e12  # Photons per second (simplified)

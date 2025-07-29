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
from typing import Optional, Tuple


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
    """Configuration for detector geometry and properties."""

    pass  # TODO: Implement based on C_Parameter_Dictionary.md


@dataclass
class BeamConfig:
    """Configuration for X-ray beam properties."""

    pass  # TODO: Implement based on C_Parameter_Dictionary.md

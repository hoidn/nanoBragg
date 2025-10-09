"""
Main Simulator class for nanoBragg PyTorch implementation.

This module orchestrates the entire diffraction simulation, taking Crystal and
Detector objects as input and producing the final diffraction pattern.
"""

from typing import Optional, Callable

import torch

from .config import BeamConfig, CrystalConfig, CrystalShape
from .models.crystal import Crystal
from .models.detector import Detector
from .utils.geometry import dot_product
from .utils.physics import sincg, sinc3, polarization_factor


def compute_physics_for_position(
    # Geometry inputs
    pixel_coords_angstroms: torch.Tensor,
    rot_a: torch.Tensor,
    rot_b: torch.Tensor,
    rot_c: torch.Tensor,
    rot_a_star: torch.Tensor,
    rot_b_star: torch.Tensor,
    rot_c_star: torch.Tensor,
    # Beam parameters
    incident_beam_direction: torch.Tensor,
    wavelength: torch.Tensor,
    source_weights: Optional[torch.Tensor] = None,
    # Beam configuration (dmin culling)
    dmin: float = 0.0,
    # Crystal structure factor function
    crystal_get_structure_factor: Callable[[torch.Tensor, torch.Tensor, torch.Tensor], torch.Tensor] = None,
    # Crystal parameters for lattice factor
    N_cells_a: int = 0,
    N_cells_b: int = 0,
    N_cells_c: int = 0,
    crystal_shape: CrystalShape = CrystalShape.SQUARE,
    crystal_fudge: float = 1.0,
    # Polarization parameters (PERF-PYTORCH-004 P3.0b)
    apply_polarization: bool = True,
    kahn_factor: float = 1.0,
    polarization_axis: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """Compute physics (Miller indices, structure factors, intensity) for given positions.

    This is a pure function with no instance state dependencies, enabling safe cross-instance
    kernel caching for torch.compile optimization (PERF-PYTORCH-004 Phase 0).

    REFACTORING NOTE (PERF-PYTORCH-004 Phase 0):
    This function was refactored from a bound method (`Simulator._compute_physics_for_position`)
    to a module-level pure function to enable safe cross-instance kernel caching with torch.compile.
    Caching bound methods is unsafe because they capture `self`, which can lead to silent
    correctness bugs when the cached kernel is reused across different simulator instances
    with different state.

    All required state is now passed as explicit parameters, ensuring that:
    1. The function has no hidden dependencies on instance state
    2. torch.compile can safely cache compiled kernels across instances
    3. The function's behavior is fully determined by its inputs
    4. Testing and debugging are simplified (pure function properties)

    This is the core physics calculation that must be done per-subpixel for proper
    anti-aliasing. Each subpixel samples a slightly different position in reciprocal
    space, leading to different Miller indices and structure factors.

    VECTORIZED OVER SOURCES: This function supports batched computation over
    multiple sources (beam divergence/dispersion). When multiple sources are provided,
    the computation is vectorized across the source dimension, eliminating the Python loop.

    Args:
        pixel_coords_angstroms: Pixel/subpixel coordinates in Angstroms (S, F, 3) or (batch, 3)
        rot_a, rot_b, rot_c: Rotated real-space lattice vectors (N_phi, N_mos, 3)
        rot_a_star, rot_b_star, rot_c_star: Rotated reciprocal vectors (N_phi, N_mos, 3)
        incident_beam_direction: Incident beam direction.
            - Single source: shape (3,)
            - Multiple sources: shape (n_sources, 3)
        wavelength: Wavelength in Angstroms.
            - Single source: scalar
            - Multiple sources: shape (n_sources,) or (n_sources, 1, 1)
        source_weights: Optional per-source weights for multi-source accumulation.
            Shape: (n_sources,). If None, equal weighting is assumed.
        dmin: Minimum d-spacing for resolution culling (0 = no culling)
        crystal_get_structure_factor: Function to look up structure factors for (h0, k0, l0)
        N_cells_a/b/c: Number of unit cells in each direction
        crystal_shape: Crystal shape enum for lattice structure factor calculation
        crystal_fudge: Fudge factor for lattice structure factor
        apply_polarization: Whether to apply Kahn polarization correction (default True)
        kahn_factor: Polarization factor for Kahn correction (0=unpolarized, 1=fully polarized)
        polarization_axis: Polarization axis unit vector (3,) or broadcastable shape

    Returns:
        intensity: Computed intensity |F|^2 integrated over phi and mosaic
            - Single source: shape (S, F) or (batch,)
            - Multiple sources: weighted sum across sources, shape (S, F) or (batch,)
    """
    # Detect if we have batched sources
    is_multi_source = incident_beam_direction.dim() == 2
    n_sources = incident_beam_direction.shape[0] if is_multi_source else 1

    # Calculate scattering vectors
    pixel_squared_sum = torch.sum(
        pixel_coords_angstroms * pixel_coords_angstroms, dim=-1, keepdim=True
    )
    # PERF-PYTORCH-004 Phase 1: Use clamp_min instead of torch.maximum to avoid allocating tensors inside compiled graph
    pixel_squared_sum = pixel_squared_sum.clamp_min(1e-12)
    pixel_magnitudes = torch.sqrt(pixel_squared_sum)
    diffracted_beam_unit = pixel_coords_angstroms / pixel_magnitudes

    # Determine spatial dimensionality from original pixel_coords BEFORE multi-source expansion
    # This tells us if we have (S, F, 3) or (batch, 3) input
    original_n_dims = pixel_coords_angstroms.dim()  # 2 for (batch, 3), 3 for (S, F, 3)

    # PERF-PYTORCH-004 Phase 1: No .to() call needed - incident_beam_direction is already on correct device
    # The caller (run() method) ensures source_directions are moved to self.device before calling this function
    # This avoids graph breaks in torch.compile

    if is_multi_source:
        # Multi-source case: broadcast over sources
        # diffracted_beam_unit: (S, F, 3) or (batch, 3)
        # incident_beam_direction: (n_sources, 3)
        # Need to add source dimension to diffracted_beam_unit

        # Add source dimension: (S, F, 3) -> (1, S, F, 3) or (batch, 3) -> (1, batch, 3)
        diffracted_expanded = diffracted_beam_unit.unsqueeze(0)

        # Handle both 2D (batch, 3) and 3D (S, F, 3) cases for incident beam expansion
        if original_n_dims == 2:
            # (batch, 3) case: expand incident to (n_sources, 1, 3)
            incident_expanded = incident_beam_direction.view(n_sources, 1, 3)
        else:
            # (S, F, 3) case: expand incident to (n_sources, 1, 1, 3)
            incident_expanded = incident_beam_direction.view(n_sources, 1, 1, 3)

        # Expand to match diffracted shape
        incident_beam_unit = incident_expanded.expand(n_sources, *diffracted_beam_unit.shape)
        diffracted_beam_unit = diffracted_expanded.expand_as(incident_beam_unit)
    else:
        # Single source case: broadcast as before
        incident_beam_unit = incident_beam_direction.expand_as(diffracted_beam_unit)

    # Prepare wavelength for broadcasting
    if is_multi_source:
        # wavelength: (n_sources,) -> broadcast shape matching diffracted_beam_unit
        if wavelength.dim() == 1:
            if original_n_dims == 2:
                # (batch, 3) case: (n_sources,) -> (n_sources, 1, 1)
                wavelength = wavelength.view(n_sources, 1, 1)
            else:
                # (S, F, 3) case: (n_sources,) -> (n_sources, 1, 1, 1)
                wavelength = wavelength.view(n_sources, 1, 1, 1)

    # Scattering vector using crystallographic convention
    scattering_vector = (diffracted_beam_unit - incident_beam_unit) / wavelength

    # Apply dmin culling if specified
    dmin_mask = None
    if dmin > 0:
        stol = 0.5 * torch.norm(scattering_vector, dim=-1)
        stol_threshold = 0.5 / dmin
        dmin_mask = (stol > 0) & (stol > stol_threshold)

    # Calculate Miller indices
    # scattering_vector shape: (S, F, 3) single source, or
    #                          (n_sources, S, F, 3) or (n_sources, batch, 3) multi-source
    # Need to add phi and mosaic dimensions for broadcasting
    if is_multi_source:
        # Multi-source: (n_sources, S, F, 3) -> (n_sources, S, F, 1, 1, 3)
        #            or (n_sources, batch, 3) -> (n_sources, batch, 1, 1, 3)
        scattering_broadcast = scattering_vector.unsqueeze(-2).unsqueeze(-2)
        # rot vectors: (N_phi, N_mos, 3) -> (1, 1, 1, N_phi, N_mos, 3) for (S, F) case
        #                                or (1, 1, N_phi, N_mos, 3) for batch case
        # Number of leading dims to add depends on ORIGINAL pixel_coords shape
        if original_n_dims == 2:
            # batch case: add 2 leading dims
            rot_a_broadcast = rot_a.unsqueeze(0).unsqueeze(0)
            rot_b_broadcast = rot_b.unsqueeze(0).unsqueeze(0)
            rot_c_broadcast = rot_c.unsqueeze(0).unsqueeze(0)
        else:
            # (S, F) case: add 3 leading dims
            rot_a_broadcast = rot_a.unsqueeze(0).unsqueeze(0).unsqueeze(0)
            rot_b_broadcast = rot_b.unsqueeze(0).unsqueeze(0).unsqueeze(0)
            rot_c_broadcast = rot_c.unsqueeze(0).unsqueeze(0).unsqueeze(0)
    else:
        # Single source: (S, F, 3) -> (S, F, 1, 1, 3) or (batch, 3) -> (batch, 1, 1, 3)
        scattering_broadcast = scattering_vector.unsqueeze(-2).unsqueeze(-2)
        # rot vectors: (N_phi, N_mos, 3) -> (1, 1, N_phi, N_mos, 3)
        rot_a_broadcast = rot_a.unsqueeze(0).unsqueeze(0)
        rot_b_broadcast = rot_b.unsqueeze(0).unsqueeze(0)
        rot_c_broadcast = rot_c.unsqueeze(0).unsqueeze(0)

    h = dot_product(scattering_broadcast, rot_a_broadcast)
    k = dot_product(scattering_broadcast, rot_b_broadcast)
    l = dot_product(scattering_broadcast, rot_c_broadcast)  # noqa: E741

    # Find nearest integer Miller indices
    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)

    # Look up structure factors
    F_cell = crystal_get_structure_factor(h0, k0, l0)

    # Ensure F_cell is on the same device as h (device-neutral implementation per Core Rule #16)
    # The crystal.get_structure_factor may return CPU tensors even when h0/k0/l0 are on CUDA
    if F_cell.device != h.device:
        F_cell = F_cell.to(device=h.device)

    # Calculate lattice structure factor
    #
    # C-Code Implementation Reference (from nanoBragg.c, lines 3062-3081):
    # ```c
    # /* structure factor of the lattice (paralelpiped crystal)
    #     F_latt = sin(M_PI*Na*h)*sin(M_PI*Nb*k)*sin(M_PI*Nc*l)/sin(M_PI*h)/sin(M_PI*k)/sin(M_PI*l);
    # */
    # F_latt = 1.0;
    # if(xtal_shape == SQUARE)
    # {
    #     /* xtal is a paralelpiped */
    #     double F_latt_a = 1.0, F_latt_b = 1.0, F_latt_c = 1.0;
    #     if(Na>1){
    #         F_latt_a = sincg(M_PI*h,Na);
    #         F_latt *= F_latt_a;
    #     }
    #     if(Nb>1){
    #         F_latt_b = sincg(M_PI*k,Nb);
    #         F_latt *= F_latt_b;
    #     }
    #     if(Nc>1){
    #         F_latt_c = sincg(M_PI*l,Nc);
    #         F_latt *= F_latt_c;
    #     }
    # }
    # ```
    #
    # Per specs/spec-a-core.md §4.3:
    # "SQUARE (grating): F_latt = sincg(π·h, Na) · sincg(π·k, Nb) · sincg(π·l, Nc)"
    #
    # CRITICAL: Use fractional h,k,l directly (NOT h-h0), unlike ROUND/GAUSS/TOPHAT shapes.
    Na = N_cells_a
    Nb = N_cells_b
    Nc = N_cells_c
    shape = crystal_shape
    fudge = crystal_fudge

    if shape == CrystalShape.SQUARE:
        # Note: sincg internally handles Na/Nb/Nc > 1 guards per C implementation
        F_latt_a = sincg(torch.pi * h, Na)
        F_latt_b = sincg(torch.pi * k, Nb)
        F_latt_c = sincg(torch.pi * l, Nc)
        F_latt = F_latt_a * F_latt_b * F_latt_c
    elif shape == CrystalShape.ROUND:
        h_frac = h - h0
        k_frac = k - k0
        l_frac = l - l0
        hrad_sqr = (h_frac * h_frac * Na * Na +
                   k_frac * k_frac * Nb * Nb +
                   l_frac * l_frac * Nc * Nc)
        # Use clamp_min to avoid creating fresh tensors in compiled graph (PERF-PYTORCH-004 P1.1)
        hrad_sqr = hrad_sqr.clamp_min(1e-12)
        F_latt = Na * Nb * Nc * 0.723601254558268 * sinc3(
            torch.pi * torch.sqrt(hrad_sqr * fudge)
        )
    elif shape == CrystalShape.GAUSS:
        h_frac = h - h0
        k_frac = k - k0
        l_frac = l - l0
        if is_multi_source:
            # Multi-source: rot_*_star (N_phi, N_mos, 3) -> (1, 1, 1, N_phi, N_mos, 3)
            delta_r_star = (h_frac.unsqueeze(-1) * rot_a_star.unsqueeze(0).unsqueeze(0).unsqueeze(0) +
                          k_frac.unsqueeze(-1) * rot_b_star.unsqueeze(0).unsqueeze(0).unsqueeze(0) +
                          l_frac.unsqueeze(-1) * rot_c_star.unsqueeze(0).unsqueeze(0).unsqueeze(0))
        else:
            # Single source: rot_*_star (N_phi, N_mos, 3) -> (1, 1, N_phi, N_mos, 3)
            delta_r_star = (h_frac.unsqueeze(-1) * rot_a_star.unsqueeze(0).unsqueeze(0) +
                          k_frac.unsqueeze(-1) * rot_b_star.unsqueeze(0).unsqueeze(0) +
                          l_frac.unsqueeze(-1) * rot_c_star.unsqueeze(0).unsqueeze(0))
        rad_star_sqr = torch.sum(delta_r_star * delta_r_star, dim=-1)
        rad_star_sqr = rad_star_sqr * Na * Na * Nb * Nb * Nc * Nc
        F_latt = Na * Nb * Nc * torch.exp(-(rad_star_sqr / 0.63) * fudge)
    elif shape == CrystalShape.TOPHAT:
        h_frac = h - h0
        k_frac = k - k0
        l_frac = l - l0
        if is_multi_source:
            # Multi-source: rot_*_star (N_phi, N_mos, 3) -> (1, 1, 1, N_phi, N_mos, 3)
            delta_r_star = (h_frac.unsqueeze(-1) * rot_a_star.unsqueeze(0).unsqueeze(0).unsqueeze(0) +
                          k_frac.unsqueeze(-1) * rot_b_star.unsqueeze(0).unsqueeze(0).unsqueeze(0) +
                          l_frac.unsqueeze(-1) * rot_c_star.unsqueeze(0).unsqueeze(0).unsqueeze(0))
        else:
            # Single source: rot_*_star (N_phi, N_mos, 3) -> (1, 1, N_phi, N_mos, 3)
            delta_r_star = (h_frac.unsqueeze(-1) * rot_a_star.unsqueeze(0).unsqueeze(0) +
                          k_frac.unsqueeze(-1) * rot_b_star.unsqueeze(0).unsqueeze(0) +
                          l_frac.unsqueeze(-1) * rot_c_star.unsqueeze(0).unsqueeze(0))
        rad_star_sqr = torch.sum(delta_r_star * delta_r_star, dim=-1)
        rad_star_sqr = rad_star_sqr * Na * Na * Nb * Nb * Nc * Nc
        inside_cutoff = (rad_star_sqr * fudge) < 0.3969
        F_latt = torch.where(inside_cutoff,
                            torch.full_like(rad_star_sqr, Na * Nb * Nc),
                            torch.zeros_like(rad_star_sqr))
    else:
        raise ValueError(f"Unsupported crystal shape: {shape}")

    # Calculate intensity
    F_total = F_cell * F_latt
    intensity = F_total * F_total  # |F|^2

    # Apply dmin culling
    if dmin_mask is not None:
        if is_multi_source:
            # Multi-source: add two unsqueeze for phi and mosaic
            keep_mask = ~dmin_mask.unsqueeze(-1).unsqueeze(-1)
        else:
            keep_mask = ~dmin_mask.unsqueeze(-1).unsqueeze(-1)
        intensity = intensity * keep_mask.to(intensity.dtype)

    # Sum over phi and mosaic dimensions
    # intensity shape before sum: (S, F, N_phi, N_mos) or (n_sources, S, F, N_phi, N_mos) or (n_sources, batch, N_phi, N_mos)
    intensity = torch.sum(intensity, dim=(-2, -1))
    # After sum: (S, F) or (n_sources, S, F) or (n_sources, batch)

    # CLI-FLAGS-003 Phase M1: Capture pre-polarization intensity for trace parity
    # This is the I_before_scaling value that C-code logs before multiplying by polar
    intensity_pre_polar = intensity.clone() if apply_polarization else None

    # PERF-PYTORCH-004 P3.0b: Apply polarization PER-SOURCE before weighted sum
    # IMPORTANT: Apply polarization even when kahn_factor==0.0 (unpolarized case)
    # The formula 0.5*(1.0 + cos²(2θ)) is the correct unpolarized correction
    if apply_polarization:
        # Calculate polarization factor for each source
        # Need diffracted beam direction: pixel_coords_angstroms normalized
        pixel_magnitudes = torch.norm(pixel_coords_angstroms, dim=-1, keepdim=True).clamp_min(1e-12)
        diffracted_beam_unit = pixel_coords_angstroms / pixel_magnitudes

        if is_multi_source:
            # Multi-source case: apply per-source polarization
            # diffracted_beam_unit: (S, F, 3) or (batch, 3)
            # incident_beam_direction: (n_sources, 3)
            # NOTE: incident_beam_direction is cloned in _compute_physics_for_position wrapper
            # before entering torch.compile to avoid CUDA graphs aliasing violations

            # Expand diffracted to (n_sources, S, F, 3) or (n_sources, batch, 3)
            if original_n_dims == 2:
                # batch case
                diffracted_expanded = diffracted_beam_unit.unsqueeze(0).expand(n_sources, -1, -1)
                incident_expanded = incident_beam_direction.unsqueeze(1).expand(-1, diffracted_beam_unit.shape[0], -1)
            else:
                # (S, F, 3) case
                diffracted_expanded = diffracted_beam_unit.unsqueeze(0).expand(n_sources, -1, -1, -1)
                incident_expanded = incident_beam_direction.unsqueeze(1).unsqueeze(1).expand(-1, diffracted_beam_unit.shape[0], diffracted_beam_unit.shape[1], -1)

            # Flatten for polarization calculation
            # Use .contiguous() to avoid CUDA graphs tensor reuse errors
            flat_shape = diffracted_expanded.shape
            incident_flat = incident_expanded.reshape(-1, 3).contiguous()
            diffracted_flat = diffracted_expanded.reshape(-1, 3).contiguous()

            # Calculate polarization
            polar_flat = polarization_factor(
                kahn_factor,
                incident_flat,
                diffracted_flat,
                polarization_axis
            )

            # Reshape to match intensity shape: (n_sources, S, F) or (n_sources, batch)
            if original_n_dims == 2:
                polar = polar_flat.reshape(n_sources, -1)
            else:
                polar = polar_flat.reshape(n_sources, diffracted_beam_unit.shape[0], diffracted_beam_unit.shape[1])

            # Apply polarization per source
            intensity = intensity * polar
        else:
            # Single source case
            # Flatten for polarization calculation
            # Use .contiguous() to avoid CUDA graphs tensor reuse errors
            if original_n_dims == 3:
                incident_flat = incident_beam_direction.unsqueeze(0).unsqueeze(0).expand(diffracted_beam_unit.shape[0], diffracted_beam_unit.shape[1], -1).reshape(-1, 3).contiguous()
            else:
                incident_flat = incident_beam_direction.unsqueeze(0).expand(diffracted_beam_unit.shape[0], -1).reshape(-1, 3).contiguous()
            diffracted_flat = diffracted_beam_unit.reshape(-1, 3).contiguous()

            # Calculate polarization
            polar_flat = polarization_factor(
                kahn_factor,
                incident_flat,
                diffracted_flat,
                polarization_axis
            )

            # Reshape to match intensity shape
            if original_n_dims == 2:
                polar = polar_flat.reshape(-1)
            else:
                polar = polar_flat.reshape(diffracted_beam_unit.shape[0], diffracted_beam_unit.shape[1])

            # Apply polarization
            intensity = intensity * polar

    # Handle multi-source weighted accumulation
    if is_multi_source:
        # Apply source weights and sum over sources
        # intensity: (n_sources, S, F) or (n_sources, batch)
        # source_weights: (n_sources,) -> (n_sources, 1, 1) or (n_sources, 1)
        if source_weights is not None:
            # Prepare weights for broadcasting
            weight_shape = [n_sources] + [1] * (intensity.dim() - 1)
            weights_broadcast = source_weights.view(*weight_shape)
            # Apply weights and sum over source dimension
            intensity = torch.sum(intensity * weights_broadcast, dim=0)
            # CLI-FLAGS-003 Phase M1: Apply same accumulation to pre-polar intensity
            if intensity_pre_polar is not None:
                intensity_pre_polar = torch.sum(intensity_pre_polar * weights_broadcast, dim=0)
        else:
            # No weights provided, simple sum
            intensity = torch.sum(intensity, dim=0)
            # CLI-FLAGS-003 Phase M1: Apply same accumulation to pre-polar intensity
            if intensity_pre_polar is not None:
                intensity_pre_polar = torch.sum(intensity_pre_polar, dim=0)

    # CLI-FLAGS-003 Phase M1: Return both post-polar (intensity) and pre-polar for trace
    return intensity, intensity_pre_polar


class Simulator:
    """
    Main diffraction simulator class.

    Implements the vectorized PyTorch equivalent of the nested loops in the
    original nanoBragg.c main simulation loop.
    """

    def __init__(
        self,
        crystal: Crystal,
        detector: Detector,
        crystal_config: Optional[CrystalConfig] = None,
        beam_config: Optional[BeamConfig] = None,
        device=None,
        dtype=torch.float32,
        debug_config: Optional[dict] = None,
    ):
        """
        Initialize simulator with crystal, detector, and configurations.

        Args:
            crystal: Crystal object containing unit cell and structure factors
            detector: Detector object with geometry parameters
            crystal_config: Configuration for crystal rotation parameters (phi, mosaic)
            beam_config: Beam configuration (optional, for future use)
            device: PyTorch device (cpu/cuda)
            dtype: PyTorch data type
            debug_config: Debug configuration with printout, printout_pixel, trace_pixel options
        """
        self.crystal = crystal
        self.detector = detector
        # If crystal_config is provided, update only the rotation-related parameters
        # This preserves essential parameters like cell dimensions and default_F
        if crystal_config is not None:
            # Update only the rotation-related fields that are explicitly set
            # This preserves the crystal's essential parameters while allowing rotation updates
            if hasattr(crystal_config, 'phi_start_deg'):
                self.crystal.config.phi_start_deg = crystal_config.phi_start_deg
            if hasattr(crystal_config, 'osc_range_deg'):
                self.crystal.config.osc_range_deg = crystal_config.osc_range_deg
            if hasattr(crystal_config, 'phi_steps'):
                self.crystal.config.phi_steps = crystal_config.phi_steps
            if hasattr(crystal_config, 'mosaic_spread_deg'):
                self.crystal.config.mosaic_spread_deg = crystal_config.mosaic_spread_deg
            if hasattr(crystal_config, 'mosaic_domains'):
                self.crystal.config.mosaic_domains = crystal_config.mosaic_domains
            if hasattr(crystal_config, 'mosaic_seed'):
                self.crystal.config.mosaic_seed = crystal_config.mosaic_seed
            if hasattr(crystal_config, 'spindle_axis'):
                self.crystal.config.spindle_axis = crystal_config.spindle_axis
        # Use the provided beam_config, or Crystal's beam_config, or default
        if beam_config is not None:
            self.beam_config = beam_config
        elif hasattr(crystal, 'beam_config') and crystal.beam_config is not None:
            self.beam_config = crystal.beam_config
        else:
            self.beam_config = BeamConfig()
        # Normalize device to ensure consistency
        if device is not None:
            # Create a dummy tensor on the device to get the actual device with index
            temp = torch.zeros(1, device=device)
            self.device = temp.device
        else:
            self.device = torch.device("cpu")
        self.dtype = dtype

        # Store debug configuration
        self.debug_config = debug_config if debug_config is not None else {}
        self.printout = self.debug_config.get('printout', False)
        self.printout_pixel = self.debug_config.get('printout_pixel', None)  # [fast, slow]
        self.trace_pixel = self.debug_config.get('trace_pixel', None)  # [slow, fast]

        # Phase CLI-FLAGS-003 M0a: Enable trace instrumentation on Crystal when trace_pixel is active
        # This guards _last_tricubic_neighborhood population to prevent unconditional debug payload retention
        if self.trace_pixel is not None:
            self.crystal._enable_trace = True

        # Set incident beam direction from detector.beam_vector
        # This is critical for convention consistency (AT-PARALLEL-004) and CLI override support (CLI-FLAGS-003 Phase H2)
        # The detector.beam_vector property handles both convention defaults and CUSTOM overrides (e.g., -beam_vector)
        if self.detector is not None:
            # Use detector's beam_vector property which handles:
            # - CUSTOM convention with user-supplied custom_beam_vector
            # - Convention defaults (MOSFLM: [1,0,0], XDS/DIALS: [0,0,1])
            # The detector normalizes and returns the vector with correct device/dtype
            self.incident_beam_direction = self.detector.beam_vector.clone()
        else:
            # If no detector provided, default to MOSFLM beam direction
            self.incident_beam_direction = torch.tensor(
                [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype
            )
        # PERF-PYTORCH-006: Store wavelength as tensor with correct dtype
        self.wavelength = torch.tensor(self.beam_config.wavelength_A, device=self.device, dtype=self.dtype)

        # Physical constants (from nanoBragg.c ~line 240)
        # PERF-PYTORCH-006: Store as tensors with correct dtype to avoid implicit float64 upcasting
        self.r_e_sqr = torch.tensor(
            7.94079248018965e-30, device=self.device, dtype=self.dtype  # classical electron radius squared (meters squared)
        )
        # Use fluence from beam config (AT-FLU-001)
        self.fluence = torch.tensor(self.beam_config.fluence, device=self.device, dtype=self.dtype)
        # Polarization setup from beam config
        # PERF-PYTORCH-006: Store as tensor with correct dtype
        kahn_value = self.beam_config.polarization_factor if not self.beam_config.nopolar else 0.0
        self.kahn_factor = torch.tensor(kahn_value, device=self.device, dtype=self.dtype)
        self.polarization_axis = torch.tensor(
            self.beam_config.polarization_axis, device=self.device, dtype=self.dtype
        )

        # PERF-PYTORCH-004 P1.2 + P3.0: Pre-normalize source tensors to avoid repeated .to() calls in run()
        # Move source direction/wavelength/weight tensors to correct device/dtype once during init
        # P3.0: Seed fallback tensors (equal weights, primary wavelength) when omitted before device cast
        _has_sources = (self.beam_config.source_directions is not None and
                       len(self.beam_config.source_directions) > 0)
        if _has_sources:
            self._source_directions = self.beam_config.source_directions.to(device=self.device, dtype=self.dtype)

            # P3.0: Default source_wavelengths to primary wavelength if not provided (AT-SRC-001)
            if self.beam_config.source_wavelengths is not None:
                self._source_wavelengths = self.beam_config.source_wavelengths.to(device=self.device, dtype=self.dtype)  # meters
            else:
                # Use primary wavelength for all sources
                primary_wavelength_m = self.beam_config.wavelength_A * 1e-10
                n_sources = len(self.beam_config.source_directions)
                self._source_wavelengths = torch.full((n_sources,), primary_wavelength_m, device=self.device, dtype=self.dtype)

            self._source_wavelengths_A = self._source_wavelengths * 1e10  # Convert to Angstroms once

            # P3.0: Default source_weights to equal weights if not provided
            if self.beam_config.source_weights is not None:
                self._source_weights = self.beam_config.source_weights.to(device=self.device, dtype=self.dtype)
            else:
                # Default to equal weights if not provided
                self._source_weights = torch.ones(len(self.beam_config.source_directions), device=self.device, dtype=self.dtype)
        else:
            self._source_directions = None
            self._source_wavelengths_A = None
            self._source_weights = None

        # PERF-PYTORCH-004 P3.4: Cache frequently-accessed tensors to reduce per-run allocations
        # Pre-convert pixel coordinates to correct device/dtype once
        self._cached_pixel_coords_meters = self.detector.get_pixel_coords().to(device=self.device, dtype=self.dtype)

        # Build ROI mask once and cache it (AT-ROI-001)
        # Start with all pixels enabled
        self._cached_roi_mask = torch.ones(
            self.detector.config.spixels,
            self.detector.config.fpixels,
            device=self.device,
            dtype=self.dtype
        )

        # Apply ROI bounds if specified
        # Note: ROI is in pixel indices (xmin/xmax for fast axis, ymin/ymax for slow axis)
        roi_ymin = self.detector.config.roi_ymin
        roi_ymax = self.detector.config.roi_ymax
        roi_xmin = self.detector.config.roi_xmin
        roi_xmax = self.detector.config.roi_xmax

        # BL-2: Guard against None values (should be set by DetectorConfig.__post_init__, but defend)
        if roi_ymin is None or roi_ymax is None or roi_xmin is None or roi_xmax is None:
            raise ValueError(
                "ROI bounds (roi_ymin, roi_ymax, roi_xmin, roi_xmax) must be set. "
                "DetectorConfig.__post_init__ should have set defaults."
            )

        # Set everything outside ROI to zero
        self._cached_roi_mask[:roi_ymin, :] = 0  # Below ymin
        self._cached_roi_mask[roi_ymax+1:, :] = 0  # Above ymax
        self._cached_roi_mask[:, :roi_xmin] = 0  # Left of xmin
        self._cached_roi_mask[:, roi_xmax+1:] = 0  # Right of xmax

        # Apply external mask if provided and cache it
        if self.detector.config.mask_array is not None:
            # Pre-convert mask_array to correct device/dtype and combine with ROI mask
            mask_array = self.detector.config.mask_array.to(device=self.device, dtype=self.dtype)
            self._cached_roi_mask = self._cached_roi_mask * mask_array

        # Compile the physics computation function with appropriate mode
        # Use max-autotune on GPU to avoid CUDA graph issues with nested compilation
        # Use reduce-overhead on CPU for better performance
        # PERF-PYTORCH-005: Create compiled version of the pure function
        # The wrapper method _compute_physics_for_position should NOT be compiled
        # because it needs to clone incident_beam_direction before passing to the
        # compiled pure function (required for CUDA graphs compatibility)
        #
        # Allow disabling compilation via environment variable for gradient testing
        # (torch.inductor has C++ codegen bugs in backward passes that break gradcheck)
        import os
        disable_compile = os.environ.get("NANOBRAGG_DISABLE_COMPILE", "0") == "1"

        if disable_compile:
            self._compiled_compute_physics = compute_physics_for_position
        else:
            try:
                if self.device.type == "cuda":
                    self._compiled_compute_physics = torch.compile(mode="max-autotune")(
                        compute_physics_for_position
                    )
                else:
                    self._compiled_compute_physics = torch.compile(mode="reduce-overhead")(
                        compute_physics_for_position
                    )
            except Exception:
                # Fall back to uncompiled version if torch.compile fails
                # (e.g., missing CUDA, Triton issues, or compilation errors)
                self._compiled_compute_physics = compute_physics_for_position

    def _compute_physics_for_position(self, pixel_coords_angstroms, rot_a, rot_b, rot_c, rot_a_star, rot_b_star, rot_c_star, incident_beam_direction=None, wavelength=None, source_weights=None):
        """Compatibility shim - calls the pure function compute_physics_for_position.

        REFACTORING NOTE (PERF-PYTORCH-004 Phase 0):
        This method has been refactored to a forwarding shim that calls the module-level
        pure function `compute_physics_for_position`. This enables safe cross-instance
        kernel caching with torch.compile.

        See docstring of `compute_physics_for_position` for full documentation.

        Args:
            pixel_coords_angstroms: Pixel/subpixel coordinates in Angstroms (S, F, 3) or (batch, 3)
            rot_a, rot_b, rot_c: Rotated real-space lattice vectors (N_phi, N_mos, 3)
            rot_a_star, rot_b_star, rot_c_star: Rotated reciprocal vectors (N_phi, N_mos, 3)
            incident_beam_direction: Optional incident beam direction (defaults to self.incident_beam_direction)
            wavelength: Optional wavelength (defaults to self.wavelength)
            source_weights: Optional per-source weights for multi-source accumulation

        Returns:
            intensity: Computed intensity |F|^2 integrated over phi and mosaic
        """
        # Use provided values or defaults
        if incident_beam_direction is None:
            incident_beam_direction = self.incident_beam_direction
        if wavelength is None:
            wavelength = self.wavelength

        # PERF-PYTORCH-005: Clone incident_beam_direction to avoid CUDA graphs aliasing violations
        # CUDA graphs requires that tensors which will be expanded/reshaped inside torch.compile
        # are cloned OUTSIDE the compiled region (in this uncompiled wrapper) to prevent
        # "accessing tensor output of CUDAGraphs that has been overwritten by a subsequent run" errors.
        # This wrapper method is intentionally NOT compiled to allow this clone operation.
        incident_beam_direction = incident_beam_direction.clone()

        # Mark CUDA graph step boundary to prevent aliasing errors
        # This tells torch.compile that we're starting a new step and tensors can be safely reused
        if self.device.type == "cuda":
            torch.compiler.cudagraph_mark_step_begin()

        # Forward to compiled pure function with explicit parameters
        return self._compiled_compute_physics(
            pixel_coords_angstroms=pixel_coords_angstroms,
            rot_a=rot_a,
            rot_b=rot_b,
            rot_c=rot_c,
            rot_a_star=rot_a_star,
            rot_b_star=rot_b_star,
            rot_c_star=rot_c_star,
            incident_beam_direction=incident_beam_direction,
            wavelength=wavelength,
            source_weights=source_weights,
            dmin=self.beam_config.dmin,
            crystal_get_structure_factor=self.crystal.get_structure_factor,
            N_cells_a=self.crystal.N_cells_a,
            N_cells_b=self.crystal.N_cells_b,
            N_cells_c=self.crystal.N_cells_c,
            crystal_shape=self.crystal.config.shape,
            crystal_fudge=self.crystal.config.fudge,
            # PERF-PYTORCH-004 P3.0b: Pass polarization parameters
            apply_polarization=not self.beam_config.nopolar,
            kahn_factor=self.kahn_factor,
            polarization_axis=self.polarization_axis,
        )

    def run(
        self,
        pixel_batch_size: Optional[int] = None,
        override_a_star: Optional[torch.Tensor] = None,
        oversample: Optional[int] = None,
        oversample_omega: Optional[bool] = None,
        oversample_polar: Optional[bool] = None,
        oversample_thick: Optional[bool] = None,
    ) -> torch.Tensor:
        """
        Run the diffraction simulation with crystal rotation and mosaicity.

        This method vectorizes the simulation over all detector pixels, phi angles,
        and mosaic domains. It integrates contributions from all crystal orientations
        to produce the final diffraction pattern.

        Important: This implementation uses the full Miller indices (h, k, l) for the
        lattice shape factor calculation, not the fractional part (h-h0). This correctly
        models the crystal shape transform and is consistent with the physics of
        diffraction from a finite crystal.

        C-Code Implementation Reference (from nanoBragg.c, lines 2993-3151):
        The vectorized implementation replaces these nested loops. The outer `source`
        loop is future work for handling beam divergence and dispersion.

        ```c
                        /* loop over sources now */
                        for(source=0;source<sources;++source){

                            /* retrieve stuff from cache */
                            incident[1] = -source_X[source];
                            incident[2] = -source_Y[source];
                            incident[3] = -source_Z[source];
                            lambda = source_lambda[source];

                            /* ... scattering vector calculation ... */

                            /* sweep over phi angles */
                            for(phi_tic = 0; phi_tic < phisteps; ++phi_tic)
                            {
                                /* ... crystal rotation ... */

                                /* enumerate mosaic domains */
                                for(mos_tic=0;mos_tic<mosaic_domains;++mos_tic)
                                {
                                    /* ... mosaic rotation ... */
                                    /* ... h,k,l calculation ... */
                                    /* ... F_cell and F_latt calculation ... */

                                    /* convert amplitudes into intensity (photons per steradian) */
                                    I += F_cell*F_cell*F_latt*F_latt;
                                }
                            }
                        }
        ```

        Args:
            pixel_batch_size: Optional batching for memory management.
            override_a_star: Optional override for the a_star vector for testing.
            oversample: Number of subpixel samples per axis. Defaults to detector config.
            oversample_omega: Apply solid angle per subpixel. Defaults to detector config.
            oversample_polar: Apply polarization per subpixel. Defaults to detector config.
            oversample_thick: Apply absorption per subpixel. Defaults to detector config.

        Returns:
            torch.Tensor: Final diffraction image with shape (spixels, fpixels).
        """
        # Unified vectorization path (spec-compliant fresh rotations)
        # Get oversampling parameters from detector config if not provided
        if oversample is None:
            oversample = self.detector.config.oversample
        if oversample_omega is None:
            oversample_omega = self.detector.config.oversample_omega
        if oversample_polar is None:
            oversample_polar = self.detector.config.oversample_polar
        if oversample_thick is None:
            oversample_thick = self.detector.config.oversample_thick

        # Auto-select oversample if set to -1 (matches C behavior)
        if oversample == -1:
            # Calculate maximum crystal dimension in meters
            xtalsize_max = max(
                abs(self.crystal.config.cell_a * 1e-10 * self.crystal.config.N_cells[0]),  # a*Na in meters
                abs(self.crystal.config.cell_b * 1e-10 * self.crystal.config.N_cells[1]),  # b*Nb in meters
                abs(self.crystal.config.cell_c * 1e-10 * self.crystal.config.N_cells[2])   # c*Nc in meters
            )

            # Calculate reciprocal pixel size in meters
            # reciprocal_pixel_size = λ * distance / pixel_size (all in meters)
            wavelength_m = self.wavelength * 1e-10  # Convert from Angstroms to meters
            distance_m = self.detector.config.distance_mm / 1000.0  # Convert from mm to meters
            pixel_size_m = self.detector.config.pixel_size_mm / 1000.0  # Convert from mm to meters
            reciprocal_pixel_size = wavelength_m * distance_m / pixel_size_m

            # Calculate recommended oversample using C formula
            import math
            recommended_oversample = math.ceil(3.0 * xtalsize_max / reciprocal_pixel_size)

            # Ensure at least 1
            if recommended_oversample <= 0:
                recommended_oversample = 1

            oversample = recommended_oversample
            print(f"auto-selected {oversample}-fold oversampling")

        # For now, we'll implement the base case without oversampling for this test
        # The full subpixel implementation will come later
        # This matches the current implementation which doesn't yet have subpixel sampling

        # PERF-PYTORCH-004 P3.4: Use cached ROI mask instead of rebuilding every run
        roi_mask = self._cached_roi_mask

        # PERF-PYTORCH-004 P3.4: Use cached pixel coordinates instead of fetching/converting every run
        pixel_coords_meters = self._cached_pixel_coords_meters

        # Get rotated lattice vectors for all phi steps and mosaic domains
        # Shape: (N_phi, N_mos, 3)
        # PERF-PYTORCH-006: Convert crystal vectors to correct device/dtype
        if override_a_star is None:
            (rot_a, rot_b, rot_c), (rot_a_star, rot_b_star, rot_c_star) = (
                self.crystal.get_rotated_real_vectors(self.crystal.config)
            )
            # Convert to correct dtype/device
            rot_a = rot_a.to(device=self.device, dtype=self.dtype)
            rot_b = rot_b.to(device=self.device, dtype=self.dtype)
            rot_c = rot_c.to(device=self.device, dtype=self.dtype)
            rot_a_star = rot_a_star.to(device=self.device, dtype=self.dtype)
            rot_b_star = rot_b_star.to(device=self.device, dtype=self.dtype)
            rot_c_star = rot_c_star.to(device=self.device, dtype=self.dtype)
            # Cache rotated reciprocal vectors for GAUSS/TOPHAT shape models
            self._rot_a_star = rot_a_star
            self._rot_b_star = rot_b_star
            self._rot_c_star = rot_c_star
        else:
            # For gradient testing with override, use single orientation
            rot_a = override_a_star.view(1, 1, 3)
            rot_b = self.crystal.b.view(1, 1, 3)
            rot_c = self.crystal.c.view(1, 1, 3)
            rot_a_star = override_a_star.view(1, 1, 3)
            rot_b_star = self.crystal.b_star.view(1, 1, 3)
            rot_c_star = self.crystal.c_star.view(1, 1, 3)
            # Cache for shape models
            self._rot_a_star = rot_a_star
            self._rot_b_star = rot_b_star
            self._rot_c_star = rot_c_star

        # PERF-PYTORCH-004 P1.2: Use pre-normalized source tensors from __init__
        # Tensors were already moved to correct device/dtype during initialization
        if self._source_directions is not None:
            n_sources = len(self._source_directions)
            source_directions = self._source_directions
            source_wavelengths_A = self._source_wavelengths_A
            source_weights = self._source_weights
        else:
            # No explicit sources, use single beam configuration
            n_sources = 1
            source_directions = None
            source_wavelengths_A = None
            source_weights = None

        # Calculate normalization factor (steps)
        # Per spec AT-SAM-001: "Final per-pixel scale SHALL divide by steps"
        # SOURCE-WEIGHT-001 Phase C1: C-parity requires ignoring source weights
        # Per spec-a-core.md line 151: "The weight column is read but ignored (equal weighting results)"
        # C code (nanoBragg.c:3358) divides by steps = sources*mosaic_domains*phisteps*oversample^2
        # where sources is the COUNT of sources, not the sum of weights
        phi_steps = self.crystal.config.phi_steps
        mosaic_domains = self.crystal.config.mosaic_domains

        # Always use n_sources (count) to match C behavior
        # The spec explicitly states source weights are "read but ignored"
        source_norm = n_sources

        steps = source_norm * phi_steps * mosaic_domains * oversample * oversample  # Include sources and oversample^2

        # Apply physical scaling factors (from nanoBragg.c ~line 3050)
        # Solid angle correction, converting all units to meters for calculation

        # Check if we're doing subpixel sampling
        if oversample > 1:
            # VECTORIZED IMPLEMENTATION: Process all subpixels in parallel
            # Generate subpixel offsets (centered on pixel center)
            # Per spec: "Compute detector-plane coordinates (meters): Fdet and Sdet at subpixel centers."
            # Create offsets in fractional pixel units
            subpixel_step = 1.0 / oversample
            offset_start = -0.5 + subpixel_step / 2.0

            # Use manual arithmetic to preserve gradients (avoid torch.linspace)
            subpixel_offsets = offset_start + torch.arange(
                oversample, device=self.device, dtype=self.dtype
            ) * subpixel_step

            # Create grid of subpixel offsets
            sub_s, sub_f = torch.meshgrid(subpixel_offsets, subpixel_offsets, indexing='ij')
            # Flatten the grid for vectorized processing
            # Shape: (oversample*oversample,)
            sub_s_flat = sub_s.flatten()
            sub_f_flat = sub_f.flatten()

            # Get detector basis vectors for proper coordinate transformation
            f_axis = self.detector.fdet_vec  # Shape: [3]
            s_axis = self.detector.sdet_vec  # Shape: [3]
            S, F = pixel_coords_meters.shape[:2]

            # VECTORIZED: Create all subpixel positions at once
            # Shape: (oversample*oversample, 3)
            # Convert detector properties to tensors with correct device/dtype (AT-PERF-DEVICE-001)
            # Use as_tensor to avoid warnings when value might already be a tensor
            pixel_size_m_tensor = torch.as_tensor(self.detector.pixel_size, device=pixel_coords_meters.device, dtype=pixel_coords_meters.dtype)
            delta_s_all = sub_s_flat * pixel_size_m_tensor
            delta_f_all = sub_f_flat * pixel_size_m_tensor

            # Shape: (oversample*oversample, 3)
            offset_vectors = delta_s_all.unsqueeze(-1) * s_axis + delta_f_all.unsqueeze(-1) * f_axis

            # Expand pixel_coords for all subpixels
            # Shape: (S, F, oversample*oversample, 3)
            pixel_coords_expanded = pixel_coords_meters.unsqueeze(2).expand(S, F, oversample*oversample, 3)
            offset_vectors_expanded = offset_vectors.unsqueeze(0).unsqueeze(0).expand(S, F, oversample*oversample, 3)

            # All subpixel coordinates at once
            # Shape: (S, F, oversample*oversample, 3)
            subpixel_coords_all = pixel_coords_expanded + offset_vectors_expanded

            # Convert to Angstroms for physics
            subpixel_coords_ang_all = subpixel_coords_all * 1e10

            # VECTORIZED PHYSICS: Process all subpixels at once
            # Reshape to (S*F*oversample^2, 3) for physics calculation
            # Use .contiguous() to avoid CUDA graphs tensor reuse errors
            batch_shape = subpixel_coords_ang_all.shape[:-1]
            coords_reshaped = subpixel_coords_ang_all.reshape(-1, 3).contiguous()

            # Compute physics for all subpixels and sources (VECTORIZED)
            if n_sources > 1:
                # VECTORIZED Multi-source case: batch all sources together
                # Note: source_directions point FROM sample TO source
                # Incident beam direction should be FROM source TO sample (negated)
                incident_dirs_batched = -source_directions  # Shape: (n_sources, 3)
                wavelengths_batched = source_wavelengths_A  # Shape: (n_sources,)

                # Single batched call for all sources
                # This replaces the Python loop and enables torch.compile optimization
                # CLI-FLAGS-003 Phase M1: Unpack both post-polar and pre-polar intensities
                physics_intensity_flat, physics_intensity_pre_polar_flat = self._compute_physics_for_position(
                    coords_reshaped, rot_a, rot_b, rot_c, rot_a_star, rot_b_star, rot_c_star,
                    incident_beam_direction=incident_dirs_batched,
                    wavelength=wavelengths_batched,
                    source_weights=source_weights
                )

                # Reshape back to (S, F, oversample*oversample)
                # The weighted sum over sources is done inside _compute_physics_for_position
                subpixel_physics_intensity_all = physics_intensity_flat.reshape(batch_shape)
            else:
                # Single source case: use default beam parameters
                # CLI-FLAGS-003 Phase M1: Unpack both post-polar and pre-polar intensities
                physics_intensity_flat, physics_intensity_pre_polar_flat = self._compute_physics_for_position(
                    coords_reshaped, rot_a, rot_b, rot_c, rot_a_star, rot_b_star, rot_c_star
                )

                # Reshape back to (S, F, oversample*oversample)
                subpixel_physics_intensity_all = physics_intensity_flat.reshape(batch_shape)

            # PERF-PYTORCH-004 P3.0b: Polarization is now applied per-source inside compute_physics_for_position
            # Only omega needs to be applied here for subpixel oversampling
            # NOTE: Do NOT divide by steps here - normalization happens once at final scaling (line ~1130)

            # VECTORIZED AIRPATH AND OMEGA: Calculate for all subpixels
            sub_squared_all = torch.sum(subpixel_coords_ang_all * subpixel_coords_ang_all, dim=-1)
            # PERF-PYTORCH-004 Phase 1: Use clamp_min instead of torch.maximum to avoid allocating tensors inside compiled graph
            sub_squared_all = sub_squared_all.clamp_min(1e-20)
            sub_magnitudes_all = torch.sqrt(sub_squared_all)
            airpath_m_all = sub_magnitudes_all * 1e-10

            # Get close_distance from detector (computed during init)
            # Convert detector properties to tensors with correct device/dtype (AT-PERF-DEVICE-001)
            # Use as_tensor to avoid warnings when value might already be a tensor
            close_distance_m = torch.as_tensor(self.detector.close_distance, device=airpath_m_all.device, dtype=airpath_m_all.dtype)
            pixel_size_m = torch.as_tensor(self.detector.pixel_size, device=airpath_m_all.device, dtype=airpath_m_all.dtype)

            # Calculate solid angle (omega) for all subpixels
            # Shape: (S, F, oversample*oversample)
            if self.detector.config.point_pixel:
                omega_all = 1.0 / (airpath_m_all * airpath_m_all)
            else:
                omega_all = (
                    (pixel_size_m * pixel_size_m)
                    / (airpath_m_all * airpath_m_all)
                    * close_distance_m
                    / airpath_m_all
                )

            # Apply omega based on oversample flags
            intensity_all = subpixel_physics_intensity_all.clone()

            if oversample_omega:
                # Apply omega per subpixel
                intensity_all = intensity_all * omega_all

            # Sum over all subpixels to get final intensity
            # Shape: (S, F)
            accumulated_intensity = torch.sum(intensity_all, dim=2)

            # Save pre-normalization intensity for trace (before last-value multiplication)
            I_before_normalization = accumulated_intensity.clone()

            # Apply last-value semantics if omega flag is not set
            if not oversample_omega:
                # Get the last subpixel's omega (last in flattened order)
                last_omega = omega_all[:, :, -1]  # Shape: (S, F)
                accumulated_intensity = accumulated_intensity * last_omega

            # Use accumulated intensity
            normalized_intensity = accumulated_intensity
        else:
            # No subpixel sampling - compute physics once for pixel centers
            # SPEC MODE: Global vectorization per specs/spec-a-core.md:204-240
            pixel_coords_angstroms = pixel_coords_meters * 1e10

            # Compute physics for pixel centers with multiple sources if available
            if n_sources > 1:
                # VECTORIZED Multi-source case: batch all sources together (matching subpixel path)
                # Note: source_directions point FROM sample TO source
                # Incident beam direction should be FROM source TO sample (negated)
                incident_dirs_batched = -source_directions  # Shape: (n_sources, 3)
                wavelengths_batched = source_wavelengths_A  # Shape: (n_sources,)

                # Single batched call for all sources
                # This replaces the Python loop and enables torch.compile optimization
                # CLI-FLAGS-003 Phase M1: Unpack both post-polar and pre-polar intensities
                intensity, I_before_normalization_pre_polar = self._compute_physics_for_position(
                    pixel_coords_angstroms, rot_a, rot_b, rot_c, rot_a_star, rot_b_star, rot_c_star,
                    incident_beam_direction=incident_dirs_batched,
                    wavelength=wavelengths_batched,
                    source_weights=source_weights
                )
                # The weighted sum over sources is done inside _compute_physics_for_position
            else:
                # Single source case: use default beam parameters
                # CLI-FLAGS-003 Phase M1: Unpack both post-polar and pre-polar intensities
                intensity, I_before_normalization_pre_polar = self._compute_physics_for_position(
                    pixel_coords_angstroms, rot_a, rot_b, rot_c, rot_a_star, rot_b_star, rot_c_star
                )

            # CLI-FLAGS-003 Phase M1: Save both post-polar (current intensity) and pre-polar for trace
            # The current intensity already has polarization applied (from compute_physics_for_position)
            I_before_normalization = intensity.clone()

            # PERF-PYTORCH-004 P3.0b: Polarization is now applied per-source inside compute_physics_for_position
            # Only omega needs to be applied here
            # NOTE: Do NOT divide by steps here - normalization happens once at final scaling (line ~1130)
            normalized_intensity = intensity

            # Calculate airpath for pixel centers
            pixel_squared_sum = torch.sum(
                pixel_coords_angstroms * pixel_coords_angstroms, dim=-1, keepdim=True
            )
            # Use clamp_min to avoid creating fresh tensors in compiled graph (PERF-PYTORCH-004 P1.1)
            pixel_squared_sum = pixel_squared_sum.clamp_min(1e-12)
            pixel_magnitudes = torch.sqrt(pixel_squared_sum)
            airpath = pixel_magnitudes.squeeze(-1)  # Remove last dimension for broadcasting
            airpath_m = airpath * 1e-10  # Å to meters
            # Convert detector properties to tensors with correct device/dtype (AT-PERF-DEVICE-001)
            # Use as_tensor to avoid warnings when value might already be a tensor
            close_distance_m = torch.as_tensor(self.detector.close_distance, device=airpath_m.device, dtype=airpath_m.dtype)
            pixel_size_m = torch.as_tensor(self.detector.pixel_size, device=airpath_m.device, dtype=airpath_m.dtype)

            # Calculate solid angle (omega) based on point_pixel mode
            if self.detector.config.point_pixel:
                # Point pixel mode: ω = 1 / R^2
                omega_pixel = 1.0 / (airpath_m * airpath_m)
            else:
                # Standard mode with obliquity correction
                # ω = (pixel_size^2 / R^2) · (close_distance/R)
                omega_pixel = (
                    (pixel_size_m * pixel_size_m)
                    / (airpath_m * airpath_m)
                    * close_distance_m
                    / airpath_m
                )

            # Apply omega directly
            normalized_intensity = normalized_intensity * omega_pixel

        # Apply detector absorption if configured (AT-ABS-001)
        # Cache capture_fraction for trace output if trace_pixel is set
        capture_fraction_for_trace = None
        if (self.detector.config.detector_thick_um is not None and
            self.detector.config.detector_thick_um > 0 and
            self.detector.config.detector_abs_um is not None and
            self.detector.config.detector_abs_um > 0):

            # Apply absorption calculation
            if self.trace_pixel:
                # When tracing, we need to cache the capture fraction
                # Call the absorption method and extract the per-pixel value
                intensity_before_absorption = normalized_intensity.clone()
                normalized_intensity = self._apply_detector_absorption(
                    normalized_intensity,
                    pixel_coords_meters,
                    oversample_thick
                )
                # Compute capture fraction as ratio (avoiding division by zero)
                capture_fraction_tensor = torch.where(
                    intensity_before_absorption > 1e-20,
                    normalized_intensity / intensity_before_absorption,
                    torch.ones_like(normalized_intensity)
                )
                capture_fraction_for_trace = capture_fraction_tensor
            else:
                normalized_intensity = self._apply_detector_absorption(
                    normalized_intensity,
                    pixel_coords_meters,
                    oversample_thick
                )

        # Final intensity with all physical constants in meters
        # Per spec AT-SAM-001 and nanoBragg.c:3358, divide by steps for normalization
        #
        # C-Code Implementation Reference (from nanoBragg.c, lines 3336-3365):
        # ```c
        #             /* end of detector thickness loop */
        #
        #             /* convert pixel intensity into photon units */
        #             test = r_e_sqr*fluence*I/steps;
        #
        #             /* do the corrections now, if they haven't been applied already */
        #             if(! oversample_thick) test *= capture_fraction;
        #             if(! oversample_polar) test *= polar;
        #             if(! oversample_omega) test *= omega_pixel;
        #             floatimage[imgidx] += test;
        # ```
        #
        # Units: [dimensionless] / [dimensionless] × [m²] × [photons/m²] = [photons·m²]
        physical_intensity = (
            normalized_intensity
            / steps
            * self.r_e_sqr
            * self.fluence
        )

        # Add water background if configured (AT-BKG-001)
        if self.beam_config.water_size_um > 0:
            water_background = self._calculate_water_background()
            physical_intensity = physical_intensity + water_background

        # Apply ROI/mask filter (AT-ROI-001)
        # Zero out pixels outside ROI or masked pixels
        # Ensure roi_mask matches the actual intensity shape
        # (some tests may have different detector sizes)
        if physical_intensity.shape != roi_mask.shape:
            # Recreate roi_mask with actual image dimensions
            actual_spixels, actual_fpixels = physical_intensity.shape
            roi_mask = torch.ones_like(physical_intensity)

            # BL-2: Guard against None values before using in min()
            if (self.detector.config.roi_ymin is None or
                self.detector.config.roi_ymax is None or
                self.detector.config.roi_xmin is None or
                self.detector.config.roi_xmax is None):
                raise ValueError(
                    "ROI bounds must be set by DetectorConfig.__post_init__ before use"
                )

            # Clamp ROI bounds to actual image size
            roi_ymin = min(self.detector.config.roi_ymin, actual_spixels - 1)
            roi_ymax = min(self.detector.config.roi_ymax, actual_spixels - 1)
            roi_xmin = min(self.detector.config.roi_xmin, actual_fpixels - 1)
            roi_xmax = min(self.detector.config.roi_xmax, actual_fpixels - 1)

            # Apply ROI bounds
            roi_mask[:roi_ymin, :] = 0
            roi_mask[roi_ymax+1:, :] = 0
            roi_mask[:, :roi_xmin] = 0
            roi_mask[:, roi_xmax+1:] = 0

            # Apply external mask if provided and size matches
            if self.detector.config.mask_array is not None:
                if self.detector.config.mask_array.shape == physical_intensity.shape:
                    # Ensure mask_array is on the same device
                    mask_array = self.detector.config.mask_array.to(device=self.device, dtype=self.dtype)
                    roi_mask = roi_mask * mask_array
                # If mask doesn't match, skip it (for compatibility with tests)

        # Ensure roi_mask is on the same device as physical_intensity
        roi_mask = roi_mask.to(physical_intensity.device)
        physical_intensity = physical_intensity * roi_mask

        # Apply debug output if requested
        if self.printout or self.trace_pixel:
            # For debug output, compute polarization for single pixel case
            # Also cache total steps for accurate trace output
            polarization_value = None
            if not oversample or oversample == 1:
                # Calculate polarization factor for the entire detector when needed for trace
                if self.beam_config.nopolar:
                    polarization_value = torch.ones_like(omega_pixel)
                elif self.trace_pixel:
                    # Recompute polarization for the trace pixel
                    # This matches the calculation in compute_physics_for_position
                    # Get pixel coordinates
                    pixel_coord_ang = pixel_coords_meters * 1e10  # meters to Angstroms

                    # Compute diffracted beam direction (normalized)
                    pixel_squared_sum = torch.sum(pixel_coord_ang * pixel_coord_ang, dim=-1, keepdim=True)
                    pixel_squared_sum = pixel_squared_sum.clamp_min(1e-12)
                    pixel_magnitudes = torch.sqrt(pixel_squared_sum)
                    diffracted_beam_unit = pixel_coord_ang / pixel_magnitudes

                    # Use incident beam direction
                    incident = self.incident_beam_direction

                    # Calculate polarization for all pixels
                    from .utils.physics import polarization_factor
                    polarization_value = polarization_factor(
                        self.kahn_factor,
                        incident.unsqueeze(0).unsqueeze(0).expand(diffracted_beam_unit.shape[0], diffracted_beam_unit.shape[1], -1).reshape(-1, 3),
                        diffracted_beam_unit.reshape(-1, 3),
                        self.polarization_axis
                    ).reshape(diffracted_beam_unit.shape[0], diffracted_beam_unit.shape[1])

            # CLI-FLAGS-003 Phase M1: Pass both post-polar and pre-polar intensities for trace
            self._apply_debug_output(
                physical_intensity,
                normalized_intensity,
                pixel_coords_meters,
                rot_a, rot_b, rot_c,
                rot_a_star, rot_b_star, rot_c_star,
                oversample,
                omega_pixel if not oversample or oversample == 1 else None,
                polarization_value,
                steps,
                capture_fraction_for_trace,
                I_before_normalization,  # Post-polar accumulated intensity
                I_before_normalization_pre_polar  # Pre-polar accumulated intensity
            )

        # PERF-PYTORCH-006: Ensure output matches requested dtype
        # Some intermediate operations may upcast for precision, but final output should match dtype
        return physical_intensity.to(dtype=self.dtype)

    def _apply_debug_output(self,
                           physical_intensity,
                           normalized_intensity,
                           pixel_coords_meters,
                           rot_a, rot_b, rot_c,
                           rot_a_star, rot_b_star, rot_c_star,
                           oversample,
                           omega_pixel=None,
                           polarization=None,
                           steps=None,
                           capture_fraction=None,
                           I_total=None,
                           I_total_pre_polar=None):
        """Apply debug output for -printout and -trace_pixel options.

        Args:
            physical_intensity: Final intensity values
            normalized_intensity: Intensity before final scaling
            pixel_coords_meters: Pixel coordinates in meters
            rot_a, rot_b, rot_c: Rotated real-space lattice vectors (Angstroms)
            rot_a_star, rot_b_star, rot_c_star: Rotated reciprocal vectors (Angstroms^-1)
            oversample: Oversampling factor
            omega_pixel: Solid angle (if computed)
            steps: Total steps calculation (sources × mosaic × φ × oversample²)
            capture_fraction: Detector absorption capture fraction tensor (if computed)
            polarization: Polarization factor (if computed)
        """

        # Check if we should limit output to specific pixel
        if self.printout_pixel:
            # printout_pixel is [fast, slow] from CLI
            target_fast = self.printout_pixel[0]
            target_slow = self.printout_pixel[1]

            # Only output for this specific pixel
            if 0 <= target_slow < physical_intensity.shape[0] and 0 <= target_fast < physical_intensity.shape[1]:
                print(f"\n=== Pixel ({target_fast}, {target_slow}) [fast, slow] ===")
                print(f"  Final intensity: {physical_intensity[target_slow, target_fast].item():.6e}")
                print(f"  Normalized intensity: {normalized_intensity[target_slow, target_fast].item():.6e}")
                if pixel_coords_meters is not None:
                    coords = pixel_coords_meters[target_slow, target_fast]
                    print(f"  Position (meters): ({coords[0].item():.6e}, {coords[1].item():.6e}, {coords[2].item():.6e})")
                    # Convert to Angstroms for physics display
                    coords_ang = coords * 1e10
                    print(f"  Position (Å): ({coords_ang[0].item():.3f}, {coords_ang[1].item():.3f}, {coords_ang[2].item():.3f})")
                if omega_pixel is not None:
                    print(f"  Solid angle: {omega_pixel[target_slow, target_fast].item():.6e}")
                if polarization is not None:
                    print(f"  Polarization: {polarization[target_slow, target_fast].item():.4f}")
        elif self.printout:
            # General verbose output - print statistics for all pixels
            print(f"\n=== Debug Output ===")
            print(f"  Image shape: {physical_intensity.shape[0]} x {physical_intensity.shape[1]} pixels")
            print(f"  Max intensity: {physical_intensity.max().item():.6e}")
            print(f"  Min intensity: {physical_intensity.min().item():.6e}")
            print(f"  Mean intensity: {physical_intensity.mean().item():.6e}")

            # Find and report brightest pixel
            max_val = physical_intensity.max()
            max_pos = (physical_intensity == max_val).nonzero()[0]
            print(f"  Brightest pixel: ({max_pos[1].item()}, {max_pos[0].item()}) [fast, slow] = {max_val.item():.6e}")

        # Handle trace_pixel for detailed single-pixel trace
        if self.trace_pixel:
            # trace_pixel is [slow, fast] from CLI
            target_slow = self.trace_pixel[0]
            target_fast = self.trace_pixel[1]

            if 0 <= target_slow < physical_intensity.shape[0] and 0 <= target_fast < physical_intensity.shape[1]:
                # Output pix0_vector first
                pix0 = self.detector.pix0_vector
                print(f"TRACE_PY: pix0_vector_meters {pix0[0].item():.15g} {pix0[1].item():.15g} {pix0[2].item():.15g}")

                # Output detector basis vectors
                fdet = self.detector.fdet_vec
                sdet = self.detector.sdet_vec
                print(f"TRACE_PY: fdet_vec {fdet[0].item():.15g} {fdet[1].item():.15g} {fdet[2].item():.15g}")
                print(f"TRACE_PY: sdet_vec {sdet[0].item():.15g} {sdet[1].item():.15g} {sdet[2].item():.15g}")

                # Trace coordinate information
                if pixel_coords_meters is not None:
                    coords = pixel_coords_meters[target_slow, target_fast]
                    print(f"TRACE_PY: pixel_pos_meters {coords[0].item():.15g} {coords[1].item():.15g} {coords[2].item():.15g}")

                    # Calculate airpath and omega
                    airpath_m = torch.sqrt(torch.sum(coords * coords)).item()
                    print(f"TRACE_PY: R_distance_meters {airpath_m:.15g}")

                    # Calculate omega (same formula as in main calculation)
                    pixel_size_m = self.detector.pixel_size  # already in meters
                    close_distance_m = self.detector.close_distance  # already in meters
                    if self.detector.config.point_pixel:
                        omega_pixel_val = 1.0 / (airpath_m * airpath_m)
                    else:
                        omega_pixel_val = (pixel_size_m * pixel_size_m) / (airpath_m * airpath_m) * close_distance_m / airpath_m

                    print(f"TRACE_PY: omega_pixel_sr {omega_pixel_val:.15g}")
                    print(f"TRACE_PY: close_distance_meters {close_distance_m:.15g}")
                    print(f"TRACE_PY: obliquity_factor {close_distance_m/airpath_m:.15g}")

                    # Calculate diffracted and incident vectors
                    coords_ang = coords * 1e10  # m to Å
                    pixel_mag = torch.sqrt(torch.sum(coords_ang * coords_ang))
                    diffracted_vec = coords_ang / pixel_mag
                    incident_vec = self.incident_beam_direction

                    print(f"TRACE_PY: diffracted_vec {diffracted_vec[0].item():.15g} {diffracted_vec[1].item():.15g} {diffracted_vec[2].item():.15g}")
                    print(f"TRACE_PY: incident_vec {incident_vec[0].item():.15g} {incident_vec[1].item():.15g} {incident_vec[2].item():.15g}")

                    # Wavelength
                    lambda_m = self.wavelength.item() * 1e-10
                    print(f"TRACE_PY: lambda_meters {lambda_m:.15g}")
                    print(f"TRACE_PY: lambda_angstroms {self.wavelength.item():.15g}")

                    # Scattering vector (in m^-1, not Å^-1!)
                    scattering_vec_ang_inv = (diffracted_vec - incident_vec) / self.wavelength
                    scattering_vec_m_inv = scattering_vec_ang_inv * 1e10  # Å^-1 to m^-1
                    print(f"TRACE_PY: scattering_vec_A_inv {scattering_vec_m_inv[0].item():.15g} {scattering_vec_m_inv[1].item():.15g} {scattering_vec_m_inv[2].item():.15g}")

                # Trace reciprocal space information if available
                if rot_a_star is not None and rot_b_star is not None and rot_c_star is not None:
                    # Output rotated real and reciprocal vectors (first phi/mosaic domain)
                    a_vec = rot_a[0, 0] if len(rot_a.shape) > 1 else rot_a
                    b_vec = rot_b[0, 0] if len(rot_b.shape) > 1 else rot_b
                    c_vec = rot_c[0, 0] if len(rot_c.shape) > 1 else rot_c

                    print(f"TRACE_PY: rot_a_angstroms {a_vec[0].item():.15g} {a_vec[1].item():.15g} {a_vec[2].item():.15g}")
                    print(f"TRACE_PY: rot_b_angstroms {b_vec[0].item():.15g} {b_vec[1].item():.15g} {b_vec[2].item():.15g}")
                    print(f"TRACE_PY: rot_c_angstroms {c_vec[0].item():.15g} {c_vec[1].item():.15g} {c_vec[2].item():.15g}")

                    # Spindle-axis instrumentation (CLI-FLAGS-003 Phase L3g)
                    # Emit raw spindle axis from config and normalized axis used by rotate_axis
                    from nanobrag_torch.utils.geometry import unitize
                    spindle_raw = self.crystal.config.spindle_axis
                    if isinstance(spindle_raw, (list, tuple)):
                        spindle_raw = torch.tensor(spindle_raw, device=self.device, dtype=self.dtype)
                    spindle_norm, spindle_magnitude = unitize(spindle_raw)
                    print(f"TRACE_PY: spindle_axis_raw {spindle_raw[0].item():.15g} {spindle_raw[1].item():.15g} {spindle_raw[2].item():.15g}")
                    print(f"TRACE_PY: spindle_axis_normalized {spindle_norm[0].item():.15g} {spindle_norm[1].item():.15g} {spindle_norm[2].item():.15g}")
                    print(f"TRACE_PY: spindle_magnitude {spindle_magnitude.item():.15g}")

                    a_star_vec = rot_a_star[0, 0] if len(rot_a_star.shape) > 1 else rot_a_star
                    b_star_vec = rot_b_star[0, 0] if len(rot_b_star.shape) > 1 else rot_b_star
                    c_star_vec = rot_c_star[0, 0] if len(rot_c_star.shape) > 1 else rot_c_star

                    print(f"TRACE_PY: rot_a_star_A_inv {a_star_vec[0].item():.15g} {a_star_vec[1].item():.15g} {a_star_vec[2].item():.15g}")
                    print(f"TRACE_PY: rot_b_star_A_inv {b_star_vec[0].item():.15g} {b_star_vec[1].item():.15g} {b_star_vec[2].item():.15g}")
                    print(f"TRACE_PY: rot_c_star_A_inv {c_star_vec[0].item():.15g} {c_star_vec[1].item():.15g} {c_star_vec[2].item():.15g}")

                    # Calculate Miller indices using scattering vector and real-space vectors
                    # Following nanoBragg.c convention: h = dot(a, scattering)
                    coords_ang = pixel_coords_meters[target_slow, target_fast] * 1e10  # m to Å
                    pixel_mag = torch.sqrt(torch.sum(coords_ang * coords_ang))
                    diffracted_unit = coords_ang / pixel_mag
                    incident_unit = self.incident_beam_direction
                    scattering_vec = (diffracted_unit - incident_unit) / self.wavelength

                    from nanobrag_torch.utils.geometry import dot_product
                    h = dot_product(scattering_vec.unsqueeze(0), a_vec.unsqueeze(0)).item()
                    k = dot_product(scattering_vec.unsqueeze(0), b_vec.unsqueeze(0)).item()
                    l = dot_product(scattering_vec.unsqueeze(0), c_vec.unsqueeze(0)).item()

                    h0 = round(h)
                    k0 = round(k)
                    l0 = round(l)

                    print(f"TRACE_PY: hkl_frac {h:.15g} {k:.15g} {l:.15g}")
                    print(f"TRACE_PY: hkl_rounded {h0} {k0} {l0}")

                    # Calculate F_latt components (SQUARE shape assumed)
                    # Per specs/spec-a-core.md §4.3 and nanoBragg.c:3071-3079:
                    # Use fractional h,k,l directly (NOT h-h0) for SQUARE lattice factor
                    Na = self.crystal.N_cells_a
                    Nb = self.crystal.N_cells_b
                    Nc = self.crystal.N_cells_c

                    from nanobrag_torch.utils import sincg
                    F_latt_a = sincg(torch.pi * torch.tensor(h, device=self.device, dtype=self.dtype), Na).item()
                    F_latt_b = sincg(torch.pi * torch.tensor(k, device=self.device, dtype=self.dtype), Nb).item()
                    F_latt_c = sincg(torch.pi * torch.tensor(l, device=self.device, dtype=self.dtype), Nc).item()
                    F_latt = F_latt_a * F_latt_b * F_latt_c

                    print(f"TRACE_PY: F_latt_a {F_latt_a:.15g}")
                    print(f"TRACE_PY: F_latt_b {F_latt_b:.15g}")
                    print(f"TRACE_PY: F_latt_c {F_latt_c:.15g}")
                    print(f"TRACE_PY: F_latt {F_latt:.15g}")

                    # CLI-FLAGS-003 Phase M1: Force interpolation for debug trace
                    # Temporarily enable interpolation to capture 4×4×4 neighborhood for analysis
                    interpolate_saved = self.crystal.interpolate
                    try:
                        # Force interpolation on for this debug query
                        self.crystal.interpolate = True

                        # Call with fractional indices to use tricubic interpolation
                        F_cell_interp = self.crystal.get_structure_factor(
                            torch.tensor([[h]], device=self.device, dtype=self.dtype),
                            torch.tensor([[k]], device=self.device, dtype=self.dtype),
                            torch.tensor([[l]], device=self.device, dtype=self.dtype)
                        ).item()
                        print(f"TRACE_PY: F_cell_interpolated {F_cell_interp:.15g}")

                        # Restore original interpolate flag
                        self.crystal.interpolate = interpolate_saved

                        # Also get nearest-neighbor for comparison
                        F_cell_nearest = self.crystal.get_structure_factor(
                            torch.tensor([[h0]], device=self.device, dtype=self.dtype),
                            torch.tensor([[k0]], device=self.device, dtype=self.dtype),
                            torch.tensor([[l0]], device=self.device, dtype=self.dtype)
                        ).item()
                        print(f"TRACE_PY: F_cell_nearest {F_cell_nearest:.15g}")

                        # Use nearest-neighbor value to match production run behavior
                        F_cell = F_cell_nearest
                    finally:
                        # Ensure flag is restored even if error occurs
                        self.crystal.interpolate = interpolate_saved

                    # CLI-FLAGS-003 Phase M1: Emit 4×4×4 tricubic interpolation neighborhood
                    # This captures the exact weights used for F_latt calculation to diagnose drift
                    if hasattr(self.crystal, '_last_tricubic_neighborhood') and self.crystal._last_tricubic_neighborhood:
                        neighborhood = self.crystal._last_tricubic_neighborhood
                        # Emit compact 4×4×4 grid (64 values) for comparison with C trace
                        # Format: TRACE_PY_TRICUBIC_GRID: [i,j,k]=value for all i,j,k in 0..3
                        sub_Fhkl = neighborhood['sub_Fhkl']
                        if sub_Fhkl.shape[0] == 1:  # Single query point (debug case)
                            grid_3d = sub_Fhkl[0]  # Extract (4,4,4) from (1,4,4,4)
                            # Emit as flattened list with indices for C comparison
                            print("TRACE_PY_TRICUBIC_GRID_START")
                            for i in range(4):
                                for j in range(4):
                                    for k in range(4):
                                        val = grid_3d[i, j, k].item()
                                        print(f"TRACE_PY_TRICUBIC: [{i},{j},{k}]={val:.15g}")
                            print("TRACE_PY_TRICUBIC_GRID_END")
                            # Also emit the coordinate arrays used for interpolation
                            h_coords = neighborhood['h_indices'][0].tolist()  # (4,) array
                            k_coords = neighborhood['k_indices'][0].tolist()
                            l_coords = neighborhood['l_indices'][0].tolist()
                            print(f"TRACE_PY_TRICUBIC_H_COORDS: {h_coords}")
                            print(f"TRACE_PY_TRICUBIC_K_COORDS: {k_coords}")
                            print(f"TRACE_PY_TRICUBIC_L_COORDS: {l_coords}")

                    # CLI-FLAGS-003 Phase M1: Emit both pre-polar and post-polar I_before_scaling
                    # This aligns PyTorch trace with C-code which logs pre-polarization value

                    # Pre-polarization intensity (matches C-code TRACE_C: I_before_scaling)
                    if I_total_pre_polar is not None and isinstance(I_total_pre_polar, torch.Tensor):
                        I_before_scaling_pre_polar = I_total_pre_polar[target_slow, target_fast].item()
                    elif I_total is not None and isinstance(I_total, torch.Tensor):
                        # Fallback: use post-polar if pre-polar not available (backward compat)
                        I_before_scaling_pre_polar = I_total[target_slow, target_fast].item()
                    else:
                        # Fallback: compute from F_cell and F_latt (less accurate)
                        I_before_scaling_pre_polar = (F_cell * F_latt) ** 2
                    print(f"TRACE_PY: I_before_scaling_pre_polar {I_before_scaling_pre_polar:.15g}")

                    # Post-polarization intensity (current I_total)
                    if I_total is not None and isinstance(I_total, torch.Tensor):
                        I_before_scaling_post_polar = I_total[target_slow, target_fast].item()
                    else:
                        # Fallback: compute from F_cell and F_latt (less accurate)
                        I_before_scaling_post_polar = (F_cell * F_latt) ** 2
                    print(f"TRACE_PY: I_before_scaling_post_polar {I_before_scaling_post_polar:.15g}")

                    # Physical constants and scaling factors
                    r_e_m = torch.sqrt(self.r_e_sqr).item()
                    print(f"TRACE_PY: r_e_meters {r_e_m:.15g}")
                    print(f"TRACE_PY: r_e_sqr {self.r_e_sqr.item():.15g}")
                    print(f"TRACE_PY: fluence_photons_per_m2 {self.fluence.item():.15g}")

                    # Use actual steps value passed from run() method
                    # This is the full calculation: sources × mosaic × φ × oversample²
                    if steps is not None:
                        print(f"TRACE_PY: steps {steps}")
                    else:
                        # Fallback to phi_steps only if not provided (backward compatibility)
                        print(f"TRACE_PY: steps {self.crystal.config.phi_steps}")

                    # Oversample flags
                    print(f"TRACE_PY: oversample_thick {1 if self.detector.config.oversample_thick else 0}")
                    print(f"TRACE_PY: oversample_polar {1 if self.detector.config.oversample_polar else 0}")
                    print(f"TRACE_PY: oversample_omega {1 if self.detector.config.oversample_omega else 0}")

                    # Capture fraction from detector absorption (actual value, not placeholder)
                    if capture_fraction is not None and isinstance(capture_fraction, torch.Tensor):
                        capture_frac_val = capture_fraction[target_slow, target_fast].item()
                    else:
                        # If absorption is not configured, capture fraction is 1.0
                        capture_frac_val = 1.0
                    print(f"TRACE_PY: capture_fraction {capture_frac_val:.15g}")

                    # Calculate polarization for this pixel (actual value, not placeholder)
                    # This matches the polarization_factor calculation in the main physics
                    if polarization is not None and isinstance(polarization, torch.Tensor):
                        polar_val = polarization[target_slow, target_fast].item()
                    else:
                        # If polarization was not computed or nopolar is set, default to 1.0
                        polar_val = 1.0

                    print(f"TRACE_PY: polar {polar_val:.15g}")
                    print(f"TRACE_PY: omega_pixel {omega_pixel_val:.15g}")

                    # Calculate cos_2theta
                    # cos(2θ) = incident · diffracted
                    cos_2theta = torch.dot(incident_unit, diffracted_unit).item()
                    print(f"TRACE_PY: cos_2theta {cos_2theta:.15g}")

                    # Final intensity
                    I_pixel_final = physical_intensity[target_slow, target_fast].item()
                    print(f"TRACE_PY: I_pixel_final {I_pixel_final:.15g}")
                    print(f"TRACE_PY: floatimage_accumulated {I_pixel_final:.15g}")

                    # Per-φ lattice trace (Phase L3k.3c.4 per plans/active/cli-phi-parity-shim/plan.md Task C4)
                    # Emit TRACE_PY_PHI for each φ step to enable per-φ parity validation
                    # Enhanced with scattering vector, reciprocal vectors, and volume per input.md 2025-10-08
                    if rot_a.shape[0] > 1:  # Check if we have multiple phi steps
                        # Get phi parameters from crystal config
                        phi_start_deg = self.crystal.config.phi_start_deg
                        osc_range_deg = self.crystal.config.osc_range_deg
                        phi_steps = self.crystal.config.phi_steps

                        # Compute phi angles for each step
                        # Match C formula: phi = phi_start + (osc_range / phi_steps) * phi_tic
                        # where phi_tic ranges from 0 to (phi_steps - 1)
                        phi_step_size = osc_range_deg / phi_steps if phi_steps > 0 else 0.0

                        # Loop over phi steps (first mosaic domain [phi_tic, 0])
                        for phi_tic in range(phi_steps):
                            # Calculate phi angle for this step
                            phi_deg = phi_start_deg + phi_tic * phi_step_size

                            # Get rotated real-space vectors for this phi step
                            a_vec_phi = rot_a[phi_tic, 0]  # First mosaic domain
                            b_vec_phi = rot_b[phi_tic, 0]
                            c_vec_phi = rot_c[phi_tic, 0]

                            # Compute reciprocal vectors from rotated real-space vectors
                            # C-Code Reference (from nanoBragg.c, lines 3044-3058):
                            # ```c
                            # if(phi != 0.0) {
                            #   rotate_axis(a0, spindle, phi, ap);
                            #   rotate_axis(b0, spindle, phi, bp);
                            #   rotate_axis(c0, spindle, phi, cp);
                            # }
                            # /* compute reciprocal-space cell vectors */
                            # cross_product(bp,cp,&ap_mag);
                            # cross_product(cp,ap,&bp_mag);
                            # cross_product(ap,bp,&cp_mag);
                            # /* volume of unit cell */
                            # V_cell = dot_product(ap,&ap_mag);
                            # /* reciprocal cell vectors */
                            # a_star[1] = ap_mag.x/V_cell; a_star[2] = ap_mag.y/V_cell; a_star[3] = ap_mag.z/V_cell;
                            # b_star[1] = bp_mag.x/V_cell; b_star[2] = bp_mag.y/V_cell; b_star[3] = bp_mag.z/V_cell;
                            # c_star[1] = cp_mag.x/V_cell; c_star[2] = cp_mag.y/V_cell; c_star[3] = cp_mag.z/V_cell;
                            # ```
                            from nanobrag_torch.utils.geometry import cross_product as cross_prod_util
                            b_cross_c_phi = cross_prod_util(b_vec_phi.unsqueeze(0), c_vec_phi.unsqueeze(0)).squeeze(0)
                            c_cross_a_phi = cross_prod_util(c_vec_phi.unsqueeze(0), a_vec_phi.unsqueeze(0)).squeeze(0)
                            a_cross_b_phi = cross_prod_util(a_vec_phi.unsqueeze(0), b_vec_phi.unsqueeze(0)).squeeze(0)

                            from nanobrag_torch.utils.geometry import dot_product
                            V_actual_phi = dot_product(a_vec_phi.unsqueeze(0), b_cross_c_phi.unsqueeze(0)).item()

                            a_star_phi = b_cross_c_phi / V_actual_phi
                            b_star_phi = c_cross_a_phi / V_actual_phi
                            c_star_phi = a_cross_b_phi / V_actual_phi

                            # Compute Miller indices for this phi orientation
                            # Reuse scattering vector from above (doesn't change with phi)
                            h_phi = dot_product(scattering_vec.unsqueeze(0), a_vec_phi.unsqueeze(0)).item()
                            k_phi = dot_product(scattering_vec.unsqueeze(0), b_vec_phi.unsqueeze(0)).item()
                            l_phi = dot_product(scattering_vec.unsqueeze(0), c_vec_phi.unsqueeze(0)).item()

                            # Compute F_latt components for this phi (SQUARE shape)
                            from nanobrag_torch.utils import sincg
                            F_latt_a_phi = sincg(torch.pi * torch.tensor(h_phi, device=self.device, dtype=self.dtype), Na).item()
                            F_latt_b_phi = sincg(torch.pi * torch.tensor(k_phi, device=self.device, dtype=self.dtype), Nb).item()
                            F_latt_c_phi = sincg(torch.pi * torch.tensor(l_phi, device=self.device, dtype=self.dtype), Nc).item()
                            F_latt_phi = F_latt_a_phi * F_latt_b_phi * F_latt_c_phi

                            # Emit enhanced TRACE_PY_PHI with scattering vector, reciprocal vectors, and volume
                            # Format matches C trace (TRACE_C_PHI) for direct comparison
                            print(f"TRACE_PY_PHI phi_tic={phi_tic} phi_deg={phi_deg:.15g} "
                                  f"k_frac={k_phi:.15g} F_latt_b={F_latt_b_phi:.15g} F_latt={F_latt_phi:.15g} "
                                  f"S_x={scattering_vec[0].item():.15g} S_y={scattering_vec[1].item():.15g} S_z={scattering_vec[2].item():.15g} "
                                  f"a_star_y={a_star_phi[1].item():.15g} b_star_y={b_star_phi[1].item():.15g} c_star_y={c_star_phi[1].item():.15g} "
                                  f"V_actual={V_actual_phi:.15g}")

                            # Phase M2 (2025-12-06): Emit real-space vectors if requested
                            # This helps diagnose lattice factor drift by comparing ap/bp/cp directly
                            if self.debug_config.get('emit_rot_stars', False):
                                print(f"TRACE_PY_ROTSTAR phi_tic={phi_tic} "
                                      f"ap_y={a_vec_phi[1].item():.15g} bp_y={b_vec_phi[1].item():.15g} cp_y={c_vec_phi[1].item():.15g}")

                # Trace factors (skip in row-wise mode - omega already calculated above at line 1396-1406)
                # In row-wise mode, omega_pixel is scoped within the row loop and not available here
                # Note: We check use_row_batching which is defined at function scope (line 766)
                if 'use_row_batching' in dir() and not use_row_batching:
                    try:
                        if omega_pixel is not None:
                            if isinstance(omega_pixel, torch.Tensor):
                                print(f"TRACE: Omega (solid angle) = {omega_pixel[target_slow, target_fast].item():.12e}")
                            else:
                                print(f"TRACE: Omega (solid angle) = {omega_pixel:.12e}")
                    except (NameError, IndexError):
                        pass  # omega_pixel not available or wrong shape
                    try:
                        if polarization is not None:
                            if isinstance(polarization, torch.Tensor):
                                print(f"TRACE: Polarization = {polarization[target_slow, target_fast].item():.12e}")
                            else:
                                print(f"TRACE: Polarization = {polarization:.12e}")
                    except (NameError, IndexError):
                        pass  # polarization not available or wrong shape

                print(f"TRACE: r_e^2 = {self.r_e_sqr:.12e}")
                print(f"TRACE: Fluence = {self.fluence:.12e}")
                print(f"TRACE: Oversample = {oversample}")

                # Show multiplication chain
                print(f"\nTRACE: Intensity calculation chain:")
                print(f"  normalized * r_e^2 * fluence")
                print(f"  = {normalized_intensity[target_slow, target_fast].item():.12e} * {self.r_e_sqr:.12e} * {self.fluence:.12e}")
                print(f"  = {physical_intensity[target_slow, target_fast].item():.12e}")

    def _calculate_water_background(self) -> torch.Tensor:
        """Calculate water background contribution (AT-BKG-001).

        The water background models forward scattering from amorphous water molecules.
        This is a constant per-pixel contribution that mimics diffuse scattering.

        Formula from spec:
        I_bg = (F_bg^2) · r_e^2 · fluence · (water_size^3) · 1e6 · Avogadro / water_MW

        Where:
        - F_bg = 2.57 (dimensionless, water forward scattering amplitude)
        - r_e^2 = classical electron radius squared
        - fluence = photons per square meter
        - water_size = water thickness in micrometers converted to meters
        - Avogadro = 6.02214179e23 mol^-1
        - water_MW = 18 g/mol

        Note: The 1e6 factor is as specified in the C code; it creates a unit inconsistency
        but we replicate it exactly for compatibility.

        Returns:
            Background intensity per pixel (same shape as detector)
        """
        # Physical constants
        F_bg = 2.57  # Water forward scattering amplitude (dimensionless)
        Avogadro = 6.02214179e23  # mol^-1
        water_MW = 18.0  # g/mol

        # Convert water size from micrometers to meters
        water_size_m = self.beam_config.water_size_um * 1e-6

        # Calculate background intensity per spec formula
        # Note: The 1e6 factor creates unit inconsistency but matches C code
        I_bg = (
            F_bg * F_bg
            * self.r_e_sqr
            * self.fluence
            * (water_size_m ** 3)
            * 1e6
            * Avogadro
            / water_MW
        )

        # Create uniform background for all pixels
        # Shape should match detector dimensions
        fpixels = self.detector.fpixels
        spixels = self.detector.spixels

        background = torch.full(
            (spixels, fpixels),
            I_bg,
            device=self.device,
            dtype=self.dtype
        )

        return background

    def _apply_detector_absorption(
        self,
        intensity: torch.Tensor,
        pixel_coords_meters: torch.Tensor,
        oversample_thick: bool
    ) -> torch.Tensor:
        """Apply detector absorption with layering (AT-ABS-001).

        C-Code Implementation Reference (from nanoBragg.c, lines 2975-2983):
        ```c
        /* now calculate detector thickness effects */
        if(capture_fraction == 0.0 || oversample_thick)
        {
            /* inverse of effective thickness increase */
            parallax = dot_product(diffracted,odet_vector);
            /* fraction of incoming photons absorbed by this detector layer */
            capture_fraction = exp(-thick_tic*detector_thickstep*detector_mu/parallax)
                              -exp(-(thick_tic+1)*detector_thickstep*detector_mu/parallax);
        }
        ```

        Args:
            intensity: Input intensity tensor [S, F]
            pixel_coords_meters: Pixel coordinates in meters [S, F, 3]
            oversample_thick: If True, apply absorption per layer; if False, use last-value semantics

        Returns:
            Intensity with absorption applied

        Implementation follows spec AT-ABS-001:
        - Parallax factor: ρ = d·o where d is detector normal, o is observation direction
        - Capture fraction per layer: exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ)
        - With oversample_thick=False: multiply by last layer's capture fraction
        - With oversample_thick=True: accumulate with per-layer capture fractions

        Vectorization Notes:
        - Oversample_thick=True processes all detector layers in parallel using broadcasting
        - Shape: parallax (S,F), t_indices (thicksteps,) → capture_fractions (thicksteps,S,F)
        - Preserves gradient flow for detector_thick_um, detector_abs_um, and geometry parameters
        """
        # Get detector parameters
        thickness_m = self.detector.config.detector_thick_um * 1e-6  # μm to meters
        thicksteps = self.detector.config.detector_thicksteps

        # Calculate μ (absorption coefficient) from attenuation depth
        # μ = 1 / (attenuation_depth_m)
        attenuation_depth_m = self.detector.config.detector_abs_um * 1e-6  # μm to meters
        mu = 1.0 / attenuation_depth_m  # m^-1

        # Get detector normal vector (odet_vector)
        detector_normal = self.detector.odet_vec  # Shape: [3]

        # Calculate observation directions (normalized pixel coordinates)
        # o = pixel_coords / |pixel_coords|
        pixel_distances = torch.sqrt(torch.sum(pixel_coords_meters**2, dim=-1, keepdim=True))
        # PERF-PYTORCH-004 Phase 1: Use clamp_min instead of torch.maximum to avoid allocating tensors inside compiled graph
        observation_dirs = pixel_coords_meters / pixel_distances.clamp_min(1e-10)

        # Calculate parallax factor: ρ = d·o
        # detector_normal shape: [3], observation_dirs shape: [S, F, 3]
        # Result shape: [S, F]
        # NOTE: C code does NOT take absolute value (nanoBragg.c line 2903)
        # Parallax can be negative for certain detector orientations
        parallax = torch.sum(detector_normal.unsqueeze(0).unsqueeze(0) * observation_dirs, dim=-1)
        # Clamp to avoid division by zero, but preserve sign
        parallax = torch.where(
            torch.abs(parallax) < 1e-10,
            torch.sign(parallax) * 1e-10,
            parallax
        )

        # Calculate layer thickness
        delta_z = thickness_m / thicksteps

        # VECTORIZED THICKNESS IMPLEMENTATION
        if oversample_thick:
            # Create all layer indices at once
            t_indices = torch.arange(thicksteps, device=intensity.device, dtype=intensity.dtype)

            # Calculate capture fractions for all layers at once
            # Shape: (thicksteps, 1, 1) for broadcasting with (S, F)
            t_expanded = t_indices.reshape(-1, 1, 1)

            # Calculate all capture fractions in parallel
            # exp(−t·Δz·μ/ρ) − exp(−(t+1)·Δz·μ/ρ)
            # Expand parallax to (1, S, F) for broadcasting
            parallax_expanded = parallax.unsqueeze(0)

            exp_start_all = torch.exp(-t_expanded * delta_z * mu / parallax_expanded)
            exp_end_all = torch.exp(-(t_expanded + 1) * delta_z * mu / parallax_expanded)
            capture_fractions = exp_start_all - exp_end_all  # Shape: (thicksteps, S, F)

            # Apply capture fractions to intensity
            # Shape: intensity (S, F) -> expand to (1, S, F)
            intensity_expanded = intensity.unsqueeze(0)

            # Multiply and sum over all layers
            # Shape: (thicksteps, S, F) * (1, S, F) -> sum over dim 0 -> (S, F)
            result = torch.sum(intensity_expanded * capture_fractions, dim=0)

        else:
            # Use last-value semantics: multiply by last layer's capture fraction
            t = thicksteps - 1  # Last layer
            exp_start = torch.exp(-t * delta_z * mu / parallax)
            exp_end = torch.exp(-(t + 1) * delta_z * mu / parallax)
            capture_fraction = exp_start - exp_end

            result = intensity * capture_fraction

        return result

    def compute_statistics(self, float_image: torch.Tensor) -> dict:
        """Compute statistics on the float image (AT-STA-001).

        Computes statistics over the unmasked pixels within the ROI.

        Per spec section "Statistics (Normative)":
        - max_I: maximum float image pixel value and its fast/slow subpixel coordinates
        - mean = sum(pixel)/N
        - RMS = sqrt(sum(pixel^2)/(N − 1))
        - RMSD from mean: sqrt(sum((pixel − mean)^2)/(N − 1))
        - N counts only pixels inside the ROI and unmasked

        Args:
            float_image: The rendered float intensity image [S, F]

        Returns:
            Dictionary containing:
            - max_I: Maximum intensity value
            - max_I_fast: Fast pixel index of maximum (0-based)
            - max_I_slow: Slow pixel index of maximum (0-based)
            - max_I_subpixel_fast: Fast subpixel coordinate where max was last set
            - max_I_subpixel_slow: Slow subpixel coordinate where max was last set
            - mean: Mean intensity over ROI/unmasked pixels
            - RMS: Root mean square intensity
            - RMSD: Root mean square deviation from mean
            - N: Number of pixels in statistics (ROI and unmasked)
        """
        # Get ROI bounds from detector config
        roi_xmin = self.detector.config.roi_xmin
        roi_xmax = self.detector.config.roi_xmax
        roi_ymin = self.detector.config.roi_ymin
        roi_ymax = self.detector.config.roi_ymax

        # Create ROI mask
        spixels, fpixels = float_image.shape
        roi_mask = torch.ones_like(float_image, dtype=torch.bool)

        # Apply ROI bounds if set (None means no restriction)
        if roi_xmin is not None:
            roi_mask[:, :roi_xmin] = False
        if roi_xmax is not None:
            roi_mask[:, roi_xmax+1:] = False
        if roi_ymin is not None:
            roi_mask[:roi_ymin, :] = False
        if roi_ymax is not None:
            roi_mask[roi_ymax+1:, :] = False

        # Apply external mask if provided
        if self.detector.config.mask_array is not None:
            if self.detector.config.mask_array.shape == float_image.shape:
                roi_mask = roi_mask & (self.detector.config.mask_array > 0)

        # Get masked pixels
        masked_pixels = float_image[roi_mask]
        N = masked_pixels.numel()

        if N == 0:
            # No pixels in ROI/mask
            return {
                "max_I": 0.0,
                "max_I_fast": 0,
                "max_I_slow": 0,
                "max_I_subpixel_fast": 0,
                "max_I_subpixel_slow": 0,
                "mean": 0.0,
                "RMS": 0.0,
                "RMSD": 0.0,
                "N": 0
            }

        # Find maximum value and its location
        max_I = masked_pixels.max().item()

        # Find the last occurrence of the maximum value in the full image
        # This matches C behavior of "last set" location
        max_mask = (float_image == max_I) & roi_mask
        max_indices = max_mask.nonzero(as_tuple=False)

        if max_indices.numel() > 0:
            # Take the last occurrence
            last_max = max_indices[-1]
            max_I_slow = last_max[0].item()
            max_I_fast = last_max[1].item()
        else:
            max_I_slow = 0
            max_I_fast = 0

        # For subpixel coordinates, we use pixel center for now
        # In future with oversample support, this would be the actual subpixel location
        # Pixel center is at +0.5 from pixel edge
        max_I_subpixel_fast = max_I_fast
        max_I_subpixel_slow = max_I_slow

        # Compute mean
        mean = masked_pixels.mean().item()

        # Compute RMS = sqrt(sum(pixel^2)/(N - 1))
        # Note: Using N-1 for unbiased estimate per spec
        if N > 1:
            sum_sq = (masked_pixels ** 2).sum().item()
            RMS = torch.sqrt(torch.tensor(sum_sq / (N - 1))).item()

            # Compute RMSD = sqrt(sum((pixel - mean)^2)/(N - 1))
            sum_dev_sq = ((masked_pixels - mean) ** 2).sum().item()
            RMSD = torch.sqrt(torch.tensor(sum_dev_sq / (N - 1))).item()
        else:
            # N=1 case: avoid division by zero
            RMS = masked_pixels[0].item()
            RMSD = 0.0

        return {
            "max_I": max_I,
            "max_I_fast": max_I_fast,
            "max_I_slow": max_I_slow,
            "max_I_subpixel_fast": max_I_subpixel_fast,
            "max_I_subpixel_slow": max_I_subpixel_slow,
            "mean": mean,
            "RMS": RMS,
            "RMSD": RMSD,
            "N": N
        }

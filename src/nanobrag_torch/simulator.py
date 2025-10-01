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
    Na = N_cells_a
    Nb = N_cells_b
    Nc = N_cells_c
    shape = crystal_shape
    fudge = crystal_fudge

    if shape == CrystalShape.SQUARE:
        F_latt_a = sincg(torch.pi * (h - h0), Na)
        F_latt_b = sincg(torch.pi * (k - k0), Nb)
        F_latt_c = sincg(torch.pi * (l - l0), Nc)
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
        else:
            # No weights provided, simple sum
            intensity = torch.sum(intensity, dim=0)

    return intensity


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

        # Set incident beam direction based on detector convention
        # This is critical for convention consistency (AT-PARALLEL-004)
        from .config import DetectorConvention

        if self.detector is not None and hasattr(self.detector, 'config'):
            if self.detector.config.detector_convention == DetectorConvention.MOSFLM:
                # MOSFLM convention: beam along +X axis
                self.incident_beam_direction = torch.tensor(
                    [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype
                )
            elif self.detector.config.detector_convention == DetectorConvention.XDS:
                # XDS convention: beam along +Z axis
                self.incident_beam_direction = torch.tensor(
                    [0.0, 0.0, 1.0], device=self.device, dtype=self.dtype
                )
            elif self.detector.config.detector_convention == DetectorConvention.DIALS:
                # DIALS convention: beam along +Z axis (same as XDS)
                self.incident_beam_direction = torch.tensor(
                    [0.0, 0.0, 1.0], device=self.device, dtype=self.dtype
                )
            else:
                # Default to MOSFLM beam direction
                self.incident_beam_direction = torch.tensor(
                    [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype
                )
        else:
            # If no detector provided, default to MOSFLM beam direction
            self.incident_beam_direction = torch.tensor(
                [1.0, 0.0, 0.0], device=self.device, dtype=self.dtype
            )
        # PERF-PYTORCH-006: Store wavelength as tensor with correct dtype
        # Handle tensor-or-scalar inputs to preserve gradients (Core Rule #9)
        if isinstance(self.beam_config.wavelength_A, torch.Tensor):
            self.wavelength = self.beam_config.wavelength_A.to(device=self.device, dtype=self.dtype)
        else:
            self.wavelength = torch.tensor(self.beam_config.wavelength_A, device=self.device, dtype=self.dtype)

        # Physical constants (from nanoBragg.c ~line 240)
        # PERF-PYTORCH-006: Store as tensors with correct dtype to avoid implicit float64 upcasting
        self.r_e_sqr = torch.tensor(
            7.94079248018965e-30, device=self.device, dtype=self.dtype  # classical electron radius squared (meters squared)
        )
        # Use fluence from beam config (AT-FLU-001)
        # Handle tensor-or-scalar inputs to preserve gradients (Core Rule #9)
        if isinstance(self.beam_config.fluence, torch.Tensor):
            self.fluence = self.beam_config.fluence.to(device=self.device, dtype=self.dtype)
        else:
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
        elif self.device.type == "cuda":
            self._compiled_compute_physics = torch.compile(mode="max-autotune")(
                compute_physics_for_position
            )
        else:
            self._compiled_compute_physics = torch.compile(mode="reduce-overhead")(
                compute_physics_for_position
            )

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
        # PERF-PYTORCH-004 P3.0c: Per AT-SRC-001 "steps = sources; intensity contributions SHALL sum with per-source λ and weight, then divide by steps"
        # The divisor SHALL be the COUNT of sources, not the SUM of weights.
        # Weights are applied during accumulation (inside compute_physics_for_position), then we normalize by count.
        phi_steps = self.crystal.config.phi_steps
        mosaic_domains = self.crystal.config.mosaic_domains
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
                physics_intensity_flat = self._compute_physics_for_position(
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
                physics_intensity_flat = self._compute_physics_for_position(
                    coords_reshaped, rot_a, rot_b, rot_c, rot_a_star, rot_b_star, rot_c_star
                )

                # Reshape back to (S, F, oversample*oversample)
                subpixel_physics_intensity_all = physics_intensity_flat.reshape(batch_shape)

            # Normalize by the total number of steps
            subpixel_physics_intensity_all = subpixel_physics_intensity_all / steps

            # PERF-PYTORCH-004 P3.0b: Polarization is now applied per-source inside compute_physics_for_position
            # Only omega needs to be applied here for subpixel oversampling

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

            # Apply last-value semantics if omega flag is not set
            if not oversample_omega:
                # Get the last subpixel's omega (last in flattened order)
                last_omega = omega_all[:, :, -1]  # Shape: (S, F)
                accumulated_intensity = accumulated_intensity * last_omega

            # Use accumulated intensity
            normalized_intensity = accumulated_intensity
        else:
            # No subpixel sampling - compute physics once for pixel centers
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
                intensity = self._compute_physics_for_position(
                    pixel_coords_angstroms, rot_a, rot_b, rot_c, rot_a_star, rot_b_star, rot_c_star,
                    incident_beam_direction=incident_dirs_batched,
                    wavelength=wavelengths_batched,
                    source_weights=source_weights
                )
                # The weighted sum over sources is done inside _compute_physics_for_position
            else:
                # Single source case: use default beam parameters
                intensity = self._compute_physics_for_position(
                    pixel_coords_angstroms, rot_a, rot_b, rot_c, rot_a_star, rot_b_star, rot_c_star
                )

            # Normalize by steps
            normalized_intensity = intensity / steps

            # PERF-PYTORCH-004 P3.0b: Polarization is now applied per-source inside compute_physics_for_position
            # Only omega needs to be applied here

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
        if (self.detector.config.detector_thick_um is not None and
            self.detector.config.detector_thick_um > 0 and
            self.detector.config.detector_abs_um is not None and
            self.detector.config.detector_abs_um > 0):

            # Apply absorption calculation
            normalized_intensity = self._apply_detector_absorption(
                normalized_intensity,
                pixel_coords_meters,
                oversample_thick
            )

        # Final intensity with all physical constants in meters
        # Units: [dimensionless] × [steradians] × [m²] × [photons/m²] × [dimensionless] = [photons·steradians]
        physical_intensity = (
            normalized_intensity
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
            polarization_value = None
            if not oversample or oversample == 1:
                # Calculate polarization factor for the entire detector
                if self.beam_config.nopolar:
                    polarization_value = torch.ones_like(omega_pixel)
                else:
                    # Compute incident and diffracted vectors for debug output
                    # These are already calculated in the main flow but not available here
                    # Since this is only for debug output, we can skip it for now
                    polarization_value = None

            self._apply_debug_output(
                physical_intensity,
                normalized_intensity,
                pixel_coords_meters,
                rot_a, rot_b, rot_c,
                rot_a_star, rot_b_star, rot_c_star,
                oversample,
                omega_pixel if not oversample or oversample == 1 else None,
                polarization_value
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
                           polarization=None):
        """Apply debug output for -printout and -trace_pixel options.

        Args:
            physical_intensity: Final intensity values
            normalized_intensity: Intensity before final scaling
            pixel_coords_meters: Pixel coordinates in meters
            rot_a, rot_b, rot_c: Rotated real-space lattice vectors (Angstroms)
            rot_a_star, rot_b_star, rot_c_star: Rotated reciprocal vectors (Angstroms^-1)
            oversample: Oversampling factor
            omega_pixel: Solid angle (if computed)
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
                print(f"\n=== TRACE: Pixel ({target_slow}, {target_fast}) [slow, fast] ===")
                print(f"TRACE: Final intensity = {physical_intensity[target_slow, target_fast].item():.12e}")
                print(f"TRACE: Normalized intensity = {normalized_intensity[target_slow, target_fast].item():.12e}")

                # Trace coordinate information
                if pixel_coords_meters is not None:
                    coords = pixel_coords_meters[target_slow, target_fast]
                    print(f"TRACE_PY: pixel_pos_meters {coords[0].item():.15g} {coords[1].item():.15g} {coords[2].item():.15g}")
                    coords_ang = coords * 1e10
                    print(f"TRACE: Position (Å) = {coords_ang[0].item():.6f}, {coords_ang[1].item():.6f}, {coords_ang[2].item():.6f}")

                    # Calculate airpath and omega
                    airpath_m = torch.sqrt(torch.sum(coords * coords)).item()
                    print(f"TRACE_PY: R_distance_meters {airpath_m:.15g}")

                    # Calculate omega (same formula as in main calculation)
                    pixel_size_m = self.detector.pixel_size  # already in meters
                    close_distance_m = self.detector.close_distance  # already in meters
                    if self.detector.config.point_pixel:
                        omega_pixel = 1.0 / (airpath_m * airpath_m)
                    else:
                        omega_pixel = (pixel_size_m * pixel_size_m) / (airpath_m * airpath_m) * close_distance_m / airpath_m

                    print(f"TRACE_PY: omega_pixel_sr {omega_pixel:.15g}")
                    print(f"TRACE_PY: close_distance_meters {close_distance_m:.15g}")
                    print(f"TRACE_PY: obliquity_factor {close_distance_m/airpath_m:.15g}")

                # Trace reciprocal space information if available
                if rot_a_star is not None and rot_b_star is not None and rot_c_star is not None:
                    # Show first reciprocal vector as example
                    a_star_0 = rot_a_star[0, 0] if len(rot_a_star.shape) > 1 else rot_a_star
                    print(f"TRACE: a* (first) = ({a_star_0[0].item():.6e}, {a_star_0[1].item():.6e}, {a_star_0[2].item():.6e})")

                    # Detailed trace: recalculate Miller indices and F_latt for this specific pixel
                    # This is duplicated computation but only for one pixel during trace
                    coords_ang = pixel_coords_meters[target_slow, target_fast] * 1e10  # m to Å

                    # Calculate scattering vector (same as in _compute_physics_for_position)
                    pixel_mag = torch.sqrt(torch.sum(coords_ang * coords_ang))
                    diffracted_unit = coords_ang / pixel_mag
                    incident_unit = self.incident_beam_direction
                    scattering_vec = (diffracted_unit - incident_unit) / self.wavelength

                    print(f"TRACE: scattering_vec_A_inv = {scattering_vec[0].item():.12e} {scattering_vec[1].item():.12e} {scattering_vec[2].item():.12e}")

                    # Calculate Miller indices using first phi/mosaic orientation
                    # Use the rotated real-space vectors (NOT reciprocal!)
                    # Following nanoBragg.c convention: h = dot(a, scattering)
                    from nanobrag_torch.utils.geometry import dot_product
                    a_vec = rot_a[0, 0] if len(rot_a.shape) > 1 else rot_a
                    b_vec = rot_b[0, 0] if len(rot_b.shape) > 1 else rot_b
                    c_vec = rot_c[0, 0] if len(rot_c.shape) > 1 else rot_c

                    h = dot_product(scattering_vec.unsqueeze(0), a_vec.unsqueeze(0)).item()
                    k = dot_product(scattering_vec.unsqueeze(0), b_vec.unsqueeze(0)).item()
                    l = dot_product(scattering_vec.unsqueeze(0), c_vec.unsqueeze(0)).item()

                    h0 = round(h)
                    k0 = round(k)
                    l0 = round(l)

                    print(f"TRACE: hkl_frac {h:.12e} {k:.12e} {l:.12e}")
                    print(f"TRACE: hkl_rounded {h0} {k0} {l0}")

                    # Calculate F_latt components (SQUARE shape assumed)
                    Na = self.crystal.N_cells_a
                    Nb = self.crystal.N_cells_b
                    Nc = self.crystal.N_cells_c

                    from nanobrag_torch.utils import sincg
                    F_latt_a = sincg(torch.pi * torch.tensor(h - h0), Na).item()
                    F_latt_b = sincg(torch.pi * torch.tensor(k - k0), Nb).item()
                    F_latt_c = sincg(torch.pi * torch.tensor(l - l0), Nc).item()
                    F_latt = F_latt_a * F_latt_b * F_latt_c

                    print(f"TRACE: F_latt_a {F_latt_a:.12e}")
                    print(f"TRACE: F_latt_b {F_latt_b:.12e}")
                    print(f"TRACE: F_latt_c {F_latt_c:.12e}")
                    print(f"TRACE: F_latt {F_latt:.12e}")

                    # Get structure factor
                    F_cell = self.crystal.get_structure_factor(
                        torch.tensor([[h0]]),
                        torch.tensor([[k0]]),
                        torch.tensor([[l0]])
                    ).item()
                    print(f"TRACE: F_cell {F_cell:.12e}")

                    # Calculate I_before_scaling (this is before r_e^2 * fluence / steps)
                    I_before_scaling = (F_cell * F_latt) ** 2
                    print(f"TRACE: I_before_scaling {I_before_scaling:.12e}")

                # Trace factors
                if omega_pixel is not None:
                    print(f"TRACE: Omega (solid angle) = {omega_pixel[target_slow, target_fast].item():.12e}")
                if polarization is not None:
                    print(f"TRACE: Polarization = {polarization[target_slow, target_fast].item():.12e}")

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

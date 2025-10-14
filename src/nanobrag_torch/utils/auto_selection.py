"""
Auto-selection logic for count/range/step parameters per spec AT-SRC-002.

This module implements the auto-selection rules from specs/spec-a.md for resolving
missing combinations of count/range/step for divergence, dispersion, and thickness sampling.
"""

from typing import Tuple, Optional
from dataclasses import dataclass
import torch
import math


@dataclass
class SamplingParams:
    """Resolved sampling parameters after auto-selection."""
    count: int
    range: float
    step: float


def auto_select_sampling(
    count: Optional[int] = None,
    range_val: Optional[float] = None,
    step: Optional[float] = None,
    default_range: float = 1.0,
    parameter_type: str = "angle"
) -> SamplingParams:
    """
    Apply auto-selection rules for sampling parameters per spec AT-SRC-002.

    Rules from spec section "Auto-selection rules":
    - If step count ≤ 0:
        - If range < 0 and step size ≤ 0: use 1 step, zero range (i.e., no spread)
        - If range < 0 and step size > 0: set range = step size, steps = 2
        - If range ≥ 0 and step size ≤ 0: step size = range, steps = 2
        - If range ≥ 0 and step size > 0: steps = ceil(range / step size)
    - If step count > 0:
        - If range < 0 and step size ≤ 0: set a nominal range and step size = range / max(steps-1, 1)
        - If range < 0 and step size > 0: range = step size, steps = 2
        - If range ≥ 0 and step size ≤ 0: step size = range / max(steps - 1, 1)

    Additional rules from AT-SRC-002:
    - No parameters → count=1, range=0, step=0
    - Only step → range=step, count=2
    - Only range → step=range, count=2
    - Only count → range set to finite default and step derived as range/(count-1)
      with count coerced to ≥2 for nonzero range

    Args:
        count: Number of steps (None or int)
        range_val: Total range to cover (None or float)
        step: Step size (None or float)
        default_range: Default range when only count is provided
                      (1.0 rad for angles, 0.5e-6 m for thickness)
        parameter_type: "angle" or "thickness" for appropriate defaults

    Returns:
        SamplingParams with resolved count, range, and step values
    """
    import math

    # Convert None to appropriate sentinel values
    count = count if count is not None else -1
    range_val = range_val if range_val is not None else -1.0
    step = step if step is not None else -1.0

    # Special case: No parameters provided
    if count <= 0 and range_val < 0 and step <= 0:
        return SamplingParams(count=1, range=0.0, step=0.0)

    # Special case: Only step provided
    if count <= 0 and range_val < 0 and step > 0:
        return SamplingParams(count=2, range=step, step=step)

    # Special case: Only range provided
    if count <= 0 and range_val >= 0 and step <= 0:
        return SamplingParams(count=2, range=range_val, step=range_val)

    # Special case: Only count provided
    if count > 0 and range_val < 0 and step <= 0:
        # Set nominal range based on parameter type
        nominal_range = default_range
        # Coerce count to ≥2 for nonzero range
        if nominal_range > 0:
            count = max(count, 2)
        # Calculate step size
        step_size = nominal_range / max(count - 1, 1)
        return SamplingParams(count=count, range=nominal_range, step=step_size)

    # Apply general rules when step count ≤ 0
    if count <= 0:
        if range_val < 0 and step <= 0:
            # Use 1 step, zero range
            return SamplingParams(count=1, range=0.0, step=0.0)
        elif range_val < 0 and step > 0:
            # Set range = step, steps = 2
            return SamplingParams(count=2, range=step, step=step)
        elif range_val >= 0 and step <= 0:
            # step size = range, steps = 2
            return SamplingParams(count=2, range=range_val, step=range_val)
        elif range_val >= 0 and step > 0:
            # steps = ceil(range / step)
            steps = math.ceil(range_val / step) if step > 0 else 1
            return SamplingParams(count=steps, range=range_val, step=step)

    # Apply rules when step count > 0
    else:
        if range_val < 0 and step <= 0:
            # Set nominal range and calculate step size
            nominal_range = default_range
            step_size = nominal_range / max(count - 1, 1)
            return SamplingParams(count=count, range=nominal_range, step=step_size)
        elif range_val < 0 and step > 0:
            # range = step, steps = 2 (override provided count)
            return SamplingParams(count=2, range=step, step=step)
        elif range_val >= 0 and step <= 0:
            # step size = range / max(steps - 1, 1)
            step_size = range_val / max(count - 1, 1)
            return SamplingParams(count=count, range=range_val, step=step_size)
        else:
            # Both range and step provided with count - use as-is
            return SamplingParams(count=count, range=range_val, step=step)


def auto_select_divergence(
    hdivsteps: Optional[int] = None,
    hdivrange: Optional[float] = None,
    hdivstep: Optional[float] = None,
    vdivsteps: Optional[int] = None,
    vdivrange: Optional[float] = None,
    vdivstep: Optional[float] = None,
) -> Tuple[SamplingParams, SamplingParams]:
    """
    Auto-select horizontal and vertical divergence parameters.

    Args:
        hdivsteps: Horizontal divergence step count
        hdivrange: Horizontal divergence range in radians
        hdivstep: Horizontal divergence step size in radians
        vdivsteps: Vertical divergence step count
        vdivrange: Vertical divergence range in radians
        vdivstep: Vertical divergence step size in radians

    Returns:
        Tuple of (horizontal_params, vertical_params)
    """
    h_params = auto_select_sampling(
        count=hdivsteps,
        range_val=hdivrange,
        step=hdivstep,
        default_range=1.0,  # 1.0 rad for angles
        parameter_type="angle"
    )

    v_params = auto_select_sampling(
        count=vdivsteps,
        range_val=vdivrange,
        step=vdivstep,
        default_range=1.0,  # 1.0 rad for angles
        parameter_type="angle"
    )

    return h_params, v_params


def auto_select_dispersion(
    dispsteps: Optional[int] = None,
    dispersion: Optional[float] = None,
    dispstep: Optional[float] = None,
) -> SamplingParams:
    """
    Auto-select spectral dispersion parameters.

    Note: dispersion is a fraction (0-1), not a range in the same sense as divergence.
    The actual wavelength range is λ0·(1 ± dispersion/2).

    Args:
        dispsteps: Number of wavelength steps
        dispersion: Fractional dispersion (0-1)
        dispstep: Step size in fractional units

    Returns:
        SamplingParams for spectral dispersion
    """
    return auto_select_sampling(
        count=dispsteps,
        range_val=dispersion,
        step=dispstep,
        default_range=0.1,  # Default 10% dispersion when only count provided
        parameter_type="dispersion"
    )


def auto_select_thickness(
    thicksteps: Optional[int] = None,
    detector_thick: Optional[float] = None,
    thickstep: Optional[float] = None,
) -> SamplingParams:
    """
    Auto-select detector thickness sampling parameters.

    Args:
        thicksteps: Number of thickness layers
        detector_thick: Total detector thickness in meters
        thickstep: Thickness step size in meters

    Returns:
        SamplingParams for thickness sampling
    """
    return auto_select_sampling(
        count=thicksteps,
        range_val=detector_thick,
        step=thickstep,
        default_range=0.5e-6,  # 0.5 μm for thickness
        parameter_type="thickness"
    )


def generate_sources_from_divergence_dispersion(
    hdiv_params: SamplingParams,
    vdiv_params: SamplingParams,
    disp_params: SamplingParams,
    central_wavelength_m: float,
    source_distance_m: float = 10.0,
    beam_direction: Optional[torch.Tensor] = None,
    polarization_axis: Optional[torch.Tensor] = None,
    round_div: bool = True,
    dtype=torch.float32,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """
    Generate source arrays from divergence and dispersion parameters.

    Per spec section "Generated sources":
    - Horizontal/vertical divergence grids with optional elliptical trimming
    - Each divergence point starts from vector −source_distance·b
    - Rotated about polarization axis by vertical angle and vertical axis by horizontal angle
    - Wavelength sampled across [λ0·(1 − dispersion/2), λ0·(1 + dispersion/2)]

    Args:
        hdiv_params: Horizontal divergence sampling parameters
        vdiv_params: Vertical divergence sampling parameters
        disp_params: Dispersion sampling parameters (range is fraction 0-1)
        central_wavelength_m: Central wavelength λ0 in meters
        source_distance_m: Distance from source to sample in meters
        beam_direction: Unit beam direction vector (default [0,0,1])
        polarization_axis: Polarization axis for vertical rotation (default [0,1,0])
        round_div: If True, apply elliptical trimming to divergence grid

    Returns:
        Tuple of:
        - directions: (N, 3) tensor of unit direction vectors
        - weights: (N,) tensor of weights (all equal per spec)
        - wavelengths: (N,) tensor of wavelengths in meters
    """
    if beam_direction is None:
        beam_direction = torch.tensor([1.0, 0.0, 0.0], dtype=dtype)  # MOSFLM default
    if polarization_axis is None:
        polarization_axis = torch.tensor([0.0, 0.0, 1.0], dtype=dtype)  # Default vertical

    # Generate divergence angle grids using vectorized operations
    # Horizontal divergence angles
    if hdiv_params.count == 1:
        hdiv_angles = torch.tensor([0.0], dtype=dtype)
    else:
        # Use manual arithmetic to avoid torch.linspace gradient issues
        start = -hdiv_params.range / 2
        hdiv_angles = start + torch.arange(hdiv_params.count, dtype=dtype) * hdiv_params.step

    # Vertical divergence angles
    if vdiv_params.count == 1:
        vdiv_angles = torch.tensor([0.0], dtype=dtype)
    else:
        start = -vdiv_params.range / 2
        vdiv_angles = start + torch.arange(vdiv_params.count, dtype=dtype) * vdiv_params.step

    # Create 2D meshgrid of divergence angles: (H, V)
    h_grid, v_grid = torch.meshgrid(hdiv_angles, vdiv_angles, indexing='ij')
    # Flatten to 1D arrays
    h_flat = h_grid.reshape(-1)
    v_flat = v_grid.reshape(-1)

    # Apply elliptical trimming if requested
    if round_div and (hdiv_params.count > 1 or vdiv_params.count > 1):
        # Normalize to unit square
        h_norm = h_flat / (hdiv_params.range/2) if hdiv_params.range > 0 else torch.zeros_like(h_flat)
        v_norm = v_flat / (vdiv_params.range/2) if vdiv_params.range > 0 else torch.zeros_like(v_flat)
        # Create mask for points inside ellipse
        inside_mask = (h_norm**2 + v_norm**2) <= 1.0
        h_flat = h_flat[inside_mask]
        v_flat = v_flat[inside_mask]

    n_div = h_flat.shape[0]

    # Generate wavelengths using vectorized operations
    if disp_params.count == 1:
        wavelengths = torch.tensor([central_wavelength_m], dtype=dtype)
    else:
        lambda_min = central_wavelength_m * (1 - disp_params.range/2)
        lambda_max = central_wavelength_m * (1 + disp_params.range/2)
        # Use manual arithmetic for gradient preservation
        wavelengths = lambda_min + torch.arange(disp_params.count, dtype=dtype) * (lambda_max - lambda_min) / (disp_params.count - 1)

    n_wave = wavelengths.shape[0]

    # Broadcast divergence and wavelengths: each divergence point gets all wavelengths
    # Shape: (n_div, n_wave)
    h_angles_expanded = h_flat.unsqueeze(1).expand(n_div, n_wave).reshape(-1)  # (n_div * n_wave,)
    v_angles_expanded = v_flat.unsqueeze(1).expand(n_div, n_wave).reshape(-1)  # (n_div * n_wave,)
    wavelengths_expanded = wavelengths.unsqueeze(0).expand(n_div, n_wave).reshape(-1)  # (n_div * n_wave,)

    n_sources = h_angles_expanded.shape[0]

    # Compute vertical axis (perpendicular to beam and polarization) once
    vertical_axis = torch.linalg.cross(beam_direction, polarization_axis)
    vertical_axis = vertical_axis / torch.linalg.norm(vertical_axis)

    # Start with -beam_direction for all sources: (n_sources, 3)
    directions = -beam_direction.unsqueeze(0).expand(n_sources, 3).clone()

    # Batch apply vertical rotation (about polarization axis) using Rodrigues' formula
    # Only apply where |v_angle| > 1e-10
    v_mask = torch.abs(v_angles_expanded) > 1e-10
    if v_mask.any():
        k = polarization_axis.unsqueeze(0)  # (1, 3)
        theta = v_angles_expanded[v_mask].unsqueeze(1)  # (n_active, 1)
        dirs_to_rotate = directions[v_mask]  # (n_active, 3)

        cos_theta = torch.cos(theta)
        sin_theta = torch.sin(theta)
        k_dot_d = (k * dirs_to_rotate).sum(dim=1, keepdim=True)  # (n_active, 1)

        # Rodrigues: v' = v*cos(θ) + (k×v)*sin(θ) + k*(k·v)*(1-cos(θ))
        cross_term = torch.linalg.cross(k.expand_as(dirs_to_rotate), dirs_to_rotate)
        directions[v_mask] = (
            dirs_to_rotate * cos_theta +
            cross_term * sin_theta +
            k.expand_as(dirs_to_rotate) * k_dot_d * (1 - cos_theta)
        )

    # Batch apply horizontal rotation (about vertical axis)
    h_mask = torch.abs(h_angles_expanded) > 1e-10
    if h_mask.any():
        k = vertical_axis.unsqueeze(0)  # (1, 3)
        theta = h_angles_expanded[h_mask].unsqueeze(1)  # (n_active, 1)
        dirs_to_rotate = directions[h_mask]  # (n_active, 3)

        cos_theta = torch.cos(theta)
        sin_theta = torch.sin(theta)
        k_dot_d = (k * dirs_to_rotate).sum(dim=1, keepdim=True)  # (n_active, 1)

        cross_term = torch.linalg.cross(k.expand_as(dirs_to_rotate), dirs_to_rotate)
        directions[h_mask] = (
            dirs_to_rotate * cos_theta +
            cross_term * sin_theta +
            k.expand_as(dirs_to_rotate) * k_dot_d * (1 - cos_theta)
        )

    # Batch normalize all directions
    directions = directions / torch.linalg.norm(directions, dim=1, keepdim=True)

    # Create weights (all equal per spec)
    weights = torch.ones(n_sources, dtype=dtype)

    # Handle edge case of no sources
    if n_sources == 0:
        directions = torch.tensor([[0.0, 0.0, 1.0]], dtype=dtype)
        weights = torch.tensor([1.0], dtype=dtype)
        wavelengths_expanded = torch.tensor([central_wavelength_m], dtype=dtype)

    return directions, weights, wavelengths_expanded
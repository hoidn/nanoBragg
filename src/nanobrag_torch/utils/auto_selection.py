"""
Auto-selection logic for count/range/step parameters per spec AT-SRC-002.

This module implements the auto-selection rules from specs/spec-a.md for resolving
missing combinations of count/range/step for divergence, dispersion, and thickness sampling.
"""

from typing import Tuple, Optional
from dataclasses import dataclass


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
#!/usr/bin/env python3
"""
Improved CLI Interface Design to Prevent Hidden Behavior Issues

This demonstrates how the nanoBragg CLI should be redesigned to make
hidden behaviors explicit and prevent the debugging nightmares that
occur when parameters have undocumented side effects.
"""

import click
import enum
import warnings
from typing import List, Optional, Tuple
from pathlib import Path


class Convention(enum.Enum):
    """Explicit convention enumeration with clear semantics."""
    MOSFLM = "mosflm"    # +0.5 pixel offset, Y-axis twotheta
    XDS = "xds"          # No offset, X-axis twotheta
    CUSTOM = "custom"    # User-specified vectors, no offsets
    
    def __str__(self):
        return self.value


class PivotMode(enum.Enum):
    """Explicit pivot mode to prevent implicit selection issues."""
    BEAM = "beam"        # Pivot around beam position on detector
    SAMPLE = "sample"    # Pivot around sample position
    AUTO = "auto"        # Let system decide (with warnings)
    
    def __str__(self):
        return self.value


def validate_convention_compatibility(ctx, param, value):
    """Validate that convention choices are compatible with other parameters."""
    if not value:
        return value
        
    # Get other parameter values from context
    convention = ctx.params.get('convention', Convention.AUTO)
    
    # Check for potential conflicts
    vector_params = [
        'twotheta_axis', 'fdet_vector', 'sdet_vector', 
        'odet_vector', 'beam_vector', 'polar_vector'
    ]
    
    has_vector_params = any(ctx.params.get(p) for p in vector_params)
    
    if has_vector_params and convention == Convention.AUTO:
        click.echo(
            click.style(
                "WARNING: Vector parameters specified without explicit convention. "
                "This will use CUSTOM convention and may change calculation behavior.",
                fg='yellow', bold=True
            ),
            err=True
        )
        
    return value


def warn_hidden_behavior(param_name: str, convention_change: str):
    """Issue a clear warning about hidden parameter behavior."""
    click.echo(
        click.style(
            f"🚨 WARNING: Parameter '--{param_name}' triggers hidden behavior:\n"
            f"   • Changes convention to {convention_change}\n"
            f"   • This may affect beam center calculations (+0.5 pixel offset)\n"
            f"   • Use '--convention {convention_change}' explicitly to acknowledge\n"
            f"   • See docs/critical_behaviors.md for details",
            fg='red', bold=True
        ),
        err=True
    )


def convention_callback(ctx, param, value):
    """Handle convention selection with explicit validation."""
    if value == 'auto':
        # Check if user has specified any vector parameters
        vector_params = [
            'twotheta_axis', 'fdet_vector', 'sdet_vector',
            'odet_vector', 'beam_vector', 'polar_vector'
        ]
        
        # Note: params might not be fully populated yet during callback
        # This is a limitation of click - in real implementation, 
        # do this validation after all params are parsed
        
        click.echo("Using automatic convention detection (consider explicit --convention)", err=True)
        return Convention.AUTO
    
    return Convention(value)


def pivot_callback(ctx, param, value):
    """Handle pivot mode selection with validation."""
    if value == 'auto':
        twotheta = ctx.params.get('twotheta', 0.0)
        if abs(twotheta) > 1e-6:
            click.echo(
                click.style(
                    "INFO: Non-zero twotheta detected. Consider --pivot sample for better accuracy.",
                    fg='blue'
                ),
                err=True
            )
        return PivotMode.AUTO
    
    return PivotMode(value)


@click.command()
@click.option(
    '--convention', 
    type=click.Choice(['mosflm', 'xds', 'custom', 'auto']), 
    default='auto',
    callback=convention_callback,
    help=(
        "Detector convention to use. "
        "CRITICAL: This affects beam center calculations!\n"
        "• mosflm: +0.5 pixel offset, Y-axis twotheta (most common)\n"
        "• xds: No offset, X-axis twotheta\n"
        "• custom: User-specified vectors, no automatic offsets\n"
        "• auto: Detect based on parameters (NOT recommended - use explicit)"
    )
)
@click.option(
    '--pivot',
    type=click.Choice(['beam', 'sample', 'auto']),
    default='auto', 
    callback=pivot_callback,
    help=(
        "Pivot mode for detector rotations.\n"
        "• beam: Rotate around beam spot on detector (for simple cases)\n" 
        "• sample: Rotate around sample position (for twotheta != 0)\n"
        "• auto: Select based on parameters (issues warnings)"
    )
)
@click.option(
    '--distance', 
    type=float, 
    required=True,
    help="Detector distance in mm"
)
@click.option(
    '--twotheta', 
    type=float, 
    default=0.0,
    help="Detector twotheta angle in degrees"
)
@click.option(
    '--twotheta-axis', 
    type=(float, float, float),
    callback=validate_convention_compatibility,
    help=(
        "🚨 WARNING: Explicit twotheta rotation axis (x y z).\n"
        "SIDE EFFECT: Forces CUSTOM convention unless --convention specified!\n"
        "DEFAULTS: MOSFLM=[0,0,-1], XDS=[1,0,0]\n"
        "Consider omitting this parameter to use convention defaults."
    )
)
@click.option(
    '--beam-center', 
    type=(float, float), 
    help="Beam center position in pixels (fast, slow)"
)
@click.option(
    '--force-hidden-behavior', 
    is_flag=True,
    help="Acknowledge that you understand hidden parameter behaviors (required for some combinations)"
)
@click.option(
    '--validate-config', 
    is_flag=True, 
    default=True,
    help="Validate configuration consistency (disable only for debugging)"
)
@click.option(
    '--verbose-warnings', 
    is_flag=True,
    help="Show detailed warnings about parameter interactions"
)
def improved_nanobragg_cli(
    convention: Convention,
    pivot: PivotMode, 
    distance: float,
    twotheta: float,
    twotheta_axis: Optional[Tuple[float, float, float]],
    beam_center: Optional[Tuple[float, float]],
    force_hidden_behavior: bool,
    validate_config: bool,
    verbose_warnings: bool
):
    """
    Improved nanoBragg CLI that makes hidden behaviors explicit.
    
    This interface prevents the "hidden convention switching" bug by:
    1. Requiring explicit convention selection
    2. Warning about parameter side effects  
    3. Validating parameter combinations
    4. Providing clear defaults and explanations
    """
    
    # Post-processing validation after all parameters are parsed
    if validate_config:
        validate_full_configuration(
            convention, pivot, distance, twotheta, twotheta_axis,
            beam_center, force_hidden_behavior, verbose_warnings
        )
    
    # Build the actual command with explicit convention control
    cmd = build_validated_command(
        convention, pivot, distance, twotheta, twotheta_axis, beam_center
    )
    
    if verbose_warnings:
        click.echo(f"Generated command: {' '.join(cmd)}")
    
    # Execute the command
    import subprocess
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Show convention confirmation
    if "convention selected" in result.stderr:
        convention_line = [line for line in result.stderr.split('\n') 
                          if "convention selected" in line][0]
        click.echo(f"✅ Confirmed: {convention_line}")
    
    return result


def validate_full_configuration(
    convention: Convention,
    pivot: PivotMode,
    distance: float,
    twotheta: float,
    twotheta_axis: Optional[Tuple[float, float, float]],
    beam_center: Optional[Tuple[float, float]], 
    force_hidden_behavior: bool,
    verbose_warnings: bool
):
    """Comprehensive configuration validation to prevent pitfalls."""
    
    issues = []
    warnings_list = []
    
    # Check for convention switching triggers
    if twotheta_axis is not None:
        if convention == Convention.AUTO:
            issues.append(
                "Specified --twotheta-axis without explicit --convention. "
                "This will force CUSTOM convention and remove +0.5 pixel offset!"
            )
        elif convention != Convention.CUSTOM:
            warnings_list.append(
                f"Using --twotheta-axis with --convention {convention}. "
                f"Consider using CUSTOM convention for explicit vector control."
            )
    
    # Check pivot mode for twotheta cases
    if abs(twotheta) > 1e-6:
        if pivot == PivotMode.BEAM:
            warnings_list.append(
                "Using BEAM pivot with non-zero twotheta. "
                "SAMPLE pivot often gives better accuracy for tilted detectors."
            )
        elif pivot == PivotMode.AUTO:
            warnings_list.append(
                "Auto pivot selection with twotheta. "
                "Consider explicit --pivot sample for tilted detectors."
            )
    
    # Check for common parameter mistakes
    if beam_center is not None:
        if abs(beam_center[0]) > 2048 or abs(beam_center[1]) > 2048:
            warnings_list.append(
                f"Large beam center values: {beam_center}. "
                f"Verify these are in pixels, not mm."
            )
    
    # Show warnings
    if warnings_list and verbose_warnings:
        click.echo(click.style("Configuration warnings:", fg='yellow', bold=True))
        for warning in warnings_list:
            click.echo(f"  ⚠️  {warning}")
    
    # Handle critical issues
    if issues:
        click.echo(click.style("Configuration errors:", fg='red', bold=True))
        for issue in issues:
            click.echo(f"  🚨 {issue}")
        
        if not force_hidden_behavior:
            click.echo(
                "\nTo proceed with hidden behavior changes, use --force-hidden-behavior"
            )
            raise click.Abort()
        else:
            click.echo("Proceeding with --force-hidden-behavior acknowledgment...")


def build_validated_command(
    convention: Convention,
    pivot: PivotMode,
    distance: float, 
    twotheta: float,
    twotheta_axis: Optional[Tuple[float, float, float]],
    beam_center: Optional[Tuple[float, float]]
) -> List[str]:
    """Build command with explicit convention and parameter control."""
    
    cmd = ['./nanoBragg']
    
    # Always specify convention explicitly (never rely on defaults)
    if convention == Convention.AUTO:
        # Determine convention based on parameters
        if twotheta_axis is not None:
            actual_convention = Convention.CUSTOM
            warn_hidden_behavior('twotheta-axis', 'CUSTOM')
        else:
            actual_convention = Convention.MOSFLM  # Safe default
    else:
        actual_convention = convention
    
    # Add explicit convention flag to prevent surprises
    cmd.extend(['-convention', str(actual_convention)])
    
    # Add basic parameters
    cmd.extend(['-distance', str(distance)])
    
    if abs(twotheta) > 1e-6:
        cmd.extend(['-twotheta', str(twotheta)])
    
    # Handle pivot mode
    if pivot == PivotMode.AUTO:
        if abs(twotheta) > 1e-6:
            actual_pivot = PivotMode.SAMPLE
        else:
            actual_pivot = PivotMode.BEAM
    else:
        actual_pivot = pivot
        
    cmd.extend(['-pivot', str(actual_pivot)])
    
    # Add vector parameters only if explicitly requested
    if twotheta_axis is not None:
        cmd.extend(['-twotheta_axis'] + [str(x) for x in twotheta_axis])
    
    if beam_center is not None:
        cmd.extend(['-Xbeam', str(beam_center[0]), '-Ybeam', str(beam_center[1])])
    
    return cmd


# Additional validation utilities

class ConfigurationValidator:
    """Utility class for validating complex parameter interactions."""
    
    @staticmethod
    def check_unit_consistency(params: dict) -> List[str]:
        """Check for common unit system mistakes."""
        issues = []
        
        distance = params.get('distance', 0)
        if distance > 10000:  # Suspiciously large for mm
            issues.append(f"Distance {distance} seems large for mm. Check units.")
        elif distance < 10:   # Suspiciously small for mm
            issues.append(f"Distance {distance} seems small for mm. Check units.")
            
        return issues
    
    @staticmethod  
    def check_convention_parameter_consistency(
        convention: Convention, 
        twotheta_axis: Optional[Tuple[float, float, float]]
    ) -> List[str]:
        """Check that convention and parameters are consistent."""
        issues = []
        
        if convention == Convention.MOSFLM and twotheta_axis is not None:
            # Check if it's the MOSFLM default
            if abs(twotheta_axis[0]) > 1e-6 or abs(twotheta_axis[1]) > 1e-6:
                issues.append(
                    "MOSFLM convention with non-default twotheta axis. "
                    "Consider CUSTOM convention."
                )
            elif abs(twotheta_axis[2] + 1.0) > 1e-6:  # Should be -1
                issues.append(
                    f"MOSFLM default twotheta axis is [0,0,-1], got {twotheta_axis}"
                )
        
        return issues


if __name__ == "__main__":
    improved_nanobragg_cli()


# Example usage patterns:

"""
# ✅ SAFE: Explicit convention, explicit pivot
python improved_cli.py --convention mosflm --pivot beam --distance 100

# ✅ SAFE: Explicit acknowledgment of hidden behavior  
python improved_cli.py --twotheta-axis 0 0 -1 --convention custom --distance 100 --force-hidden-behavior

# ❌ DANGEROUS: Would trigger warnings and require --force-hidden-behavior
python improved_cli.py --twotheta-axis 0 0 -1 --distance 100

# ✅ SAFE: Uses defaults appropriately
python improved_cli.py --convention mosflm --distance 100 --twotheta 20 --pivot sample

# ✅ EDUCATIONAL: Shows all warnings and validation
python improved_cli.py --distance 100 --twotheta 20 --verbose-warnings --validate-config
"""
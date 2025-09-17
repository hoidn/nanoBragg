#!/usr/bin/env python3
"""
Improved C Reference Utils Design

This demonstrates how c_reference_utils.py should be redesigned to prevent
the hidden behavior issues that caused months of debugging. The key improvements:

1. Explicit convention control and validation
2. Command logging and verification
3. Hidden behavior detection and warnings
4. Parameter consistency checking
"""

import os
import warnings
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import subprocess
import tempfile
import logging

from nanobrag_torch.config import BeamConfig, CrystalConfig, DetectorConfig, DetectorConvention, DetectorPivot


class HiddenBehaviorDetector:
    """Detects and warns about hidden behavior triggers in C command construction."""
    
    @staticmethod
    def check_for_hidden_triggers(cmd: List[str]) -> List[str]:
        """Check command for parameters that trigger hidden behaviors."""
        warnings_list = []
        
        # Hidden trigger 1: Vector parameters force CUSTOM convention
        vector_triggers = [
            '-twotheta_axis', '-fdet_vector', '-sdet_vector', '-odet_vector',
            '-beam_vector', '-polar_vector', '-spindle_axis', '-pix0_vector'
        ]
        
        has_explicit_convention = '-convention' in cmd
        has_vector_param = any(trigger in cmd for trigger in vector_triggers)
        
        if has_vector_param and not has_explicit_convention:
            triggered_params = [t for t in vector_triggers if t in cmd]
            warnings_list.append(
                f"🚨 HIDDEN BEHAVIOR: Parameters {triggered_params} will force CUSTOM convention! "
                f"This removes +0.5 pixel offset and may cause ~5mm beam center errors. "
                f"Add explicit -convention flag to control this."
            )
        
        # Hidden trigger 2: Parameter order sensitivity
        if '-pivot' in cmd and '-twotheta' in cmd:
            pivot_idx = cmd.index('-pivot')
            twotheta_idx = cmd.index('-twotheta')  
            if pivot_idx > twotheta_idx:
                warnings_list.append(
                    "⚠️ PARAMETER ORDER: -pivot after -twotheta may not work as expected. "
                    "Consider placing -pivot before -twotheta."
                )
        
        return warnings_list
    
    @staticmethod
    def validate_convention_consistency(
        cmd: List[str], 
        expected_convention: DetectorConvention
    ) -> List[str]:
        """Validate that command will produce expected convention."""
        issues = []
        
        has_explicit_convention = '-convention' in cmd
        if not has_explicit_convention:
            issues.append(
                "No explicit -convention specified. C code will make automatic selection "
                "which may not match PyTorch expectations."
            )
        
        # Check for MOSFLM default axis specification (triggers CUSTOM mode)
        if '-twotheta_axis' in cmd and expected_convention == DetectorConvention.MOSFLM:
            axis_idx = cmd.index('-twotheta_axis')
            if axis_idx + 3 < len(cmd):
                axis = [float(cmd[axis_idx + i]) for i in range(1, 4)]
                is_mosflm_default = (
                    abs(axis[0]) < 1e-6 and 
                    abs(axis[1]) < 1e-6 and 
                    abs(axis[2] + 1.0) < 1e-6
                )
                if is_mosflm_default:
                    issues.append(
                        "Specifying MOSFLM default twotheta_axis [0,0,-1] will trigger "
                        "CUSTOM convention instead of MOSFLM. Remove -twotheta_axis to "
                        "use true MOSFLM convention."
                    )
        
        return issues


class CommandBuilder:
    """Improved command builder with explicit behavior control."""
    
    def __init__(self, enable_warnings: bool = True, strict_validation: bool = True):
        self.enable_warnings = enable_warnings
        self.strict_validation = strict_validation
        self.logger = logging.getLogger(__name__)
        
    def build_command(
        self,
        detector_config: DetectorConfig,
        crystal_config: CrystalConfig, 
        beam_config: BeamConfig,
        matrix_file: str = "identity.mat",
        default_F: float = 100.0,
        executable_path: str = "golden_suite_generator/nanoBragg",
        force_explicit_convention: bool = True,
    ) -> Tuple[List[str], Dict[str, Any]]:
        """
        Build command with explicit behavior control and validation.
        
        Returns:
            Tuple of (command_args, metadata_dict)
        """
        
        metadata = {
            'detector_convention': detector_config.detector_convention,
            'detector_pivot': detector_config.detector_pivot,
            'warnings': [],
            'validation_issues': [],
            'hidden_behaviors_detected': []
        }
        
        # Start building command
        cmd = [executable_path]
        
        # CRITICAL: Always specify convention explicitly unless specifically disabled
        if force_explicit_convention:
            convention_name = self._get_c_convention_name(detector_config.detector_convention)
            cmd.extend(['-convention', convention_name])
            metadata['explicit_convention'] = convention_name
        
        # Core parameters
        cmd.extend(['-default_F', str(default_F)])
        cmd.extend(['-lambda', str(beam_config.wavelength_A)])
        cmd.extend(['-distance', str(detector_config.distance_mm)])
        cmd.extend(['-pixel', str(detector_config.pixel_size_mm)])
        cmd.extend(['-detpixels', str(detector_config.spixels)])
        
        # Beam center with explicit format
        cmd.extend(['-Xbeam', str(detector_config.beam_center_f)])
        cmd.extend(['-Ybeam', str(detector_config.beam_center_s)])
        
        # Crystal parameters  
        cmd.extend([
            '-cell',
            str(crystal_config.cell_a), str(crystal_config.cell_b), str(crystal_config.cell_c),
            str(crystal_config.cell_alpha), str(crystal_config.cell_beta), str(crystal_config.cell_gamma)
        ])
        cmd.extend(['-N', str(crystal_config.N_cells[0])])
        cmd.extend(['-matrix', matrix_file])
        
        # Detector rotations (only if non-zero)
        self._add_nonzero_rotation(cmd, '-detector_rotx', detector_config.detector_rotx_deg)
        self._add_nonzero_rotation(cmd, '-detector_roty', detector_config.detector_roty_deg) 
        self._add_nonzero_rotation(cmd, '-detector_rotz', detector_config.detector_rotz_deg)
        
        # Two-theta handling with explicit convention control
        has_twotheta = abs(detector_config.detector_twotheta_deg) > 1e-6
        if has_twotheta:
            cmd.extend(['-twotheta', str(detector_config.detector_twotheta_deg)])
            
            # CRITICAL DECISION: Only add twotheta_axis if truly needed
            # Adding it triggers CUSTOM convention!
            if self._should_specify_twotheta_axis(detector_config):
                axis = detector_config.twotheta_axis
                if hasattr(axis, 'tolist'):
                    axis = axis.tolist()
                cmd.extend(['-twotheta_axis'] + [str(x) for x in axis])
                metadata['twotheta_axis_specified'] = True
            else:
                metadata['twotheta_axis_specified'] = False
                metadata['twotheta_axis_reason'] = 'Using convention default to avoid CUSTOM mode'
        
        # Pivot mode (explicit to avoid implicit selection issues)
        pivot_name = self._get_c_pivot_name(detector_config.detector_pivot)
        cmd.extend(['-pivot', pivot_name])
        metadata['explicit_pivot'] = pivot_name
        
        # Validation and warnings
        if self.enable_warnings or self.strict_validation:
            self._validate_and_warn(cmd, detector_config, metadata)
        
        return cmd, metadata
    
    def _should_specify_twotheta_axis(self, detector_config: DetectorConfig) -> bool:
        """Determine if twotheta_axis should be explicitly specified."""
        
        # If no axis specified, use convention default
        if detector_config.twotheta_axis is None:
            return False
        
        axis = detector_config.twotheta_axis
        if hasattr(axis, 'tolist'):
            axis = axis.tolist()
        
        # Check if it matches convention defaults
        convention = detector_config.detector_convention
        
        if convention == DetectorConvention.MOSFLM:
            # MOSFLM default: [0, 0, -1]
            is_default = (abs(axis[0]) < 1e-6 and abs(axis[1]) < 1e-6 and abs(axis[2] + 1.0) < 1e-6)
        elif convention == DetectorConvention.XDS:
            # XDS default: [1, 0, 0]  
            is_default = (abs(axis[0] - 1.0) < 1e-6 and abs(axis[1]) < 1e-6 and abs(axis[2]) < 1e-6)
        else:
            # For CUSTOM, always specify
            is_default = False
        
        # Only specify if it's NOT the default (avoids triggering CUSTOM mode)
        return not is_default
    
    def _add_nonzero_rotation(self, cmd: List[str], param: str, value: float):
        """Add rotation parameter only if non-zero."""
        if abs(value) > 1e-6:
            cmd.extend([param, str(value)])
    
    def _get_c_convention_name(self, convention: DetectorConvention) -> str:
        """Map PyTorch convention to C convention name."""
        mapping = {
            DetectorConvention.MOSFLM: 'mosflm',
            DetectorConvention.XDS: 'xds', 
            DetectorConvention.CUSTOM: 'custom'
        }
        return mapping[convention]
    
    def _get_c_pivot_name(self, pivot: DetectorPivot) -> str:
        """Map PyTorch pivot to C pivot name."""
        mapping = {
            DetectorPivot.BEAM: 'beam',
            DetectorPivot.SAMPLE: 'sample'
        }
        return mapping[pivot]
    
    def _validate_and_warn(self, cmd: List[str], detector_config: DetectorConfig, metadata: Dict[str, Any]):
        """Perform validation and collect warnings."""
        
        # Check for hidden behavior triggers
        hidden_warnings = HiddenBehaviorDetector.check_for_hidden_triggers(cmd)
        metadata['warnings'].extend(hidden_warnings)
        
        # Check convention consistency
        consistency_issues = HiddenBehaviorDetector.validate_convention_consistency(
            cmd, detector_config.detector_convention
        )
        metadata['validation_issues'].extend(consistency_issues)
        
        # Log warnings if enabled
        if self.enable_warnings:
            for warning in metadata['warnings']:
                self.logger.warning(warning)
            for issue in metadata['validation_issues']:
                self.logger.error(issue)
    
    def format_command_for_logging(self, cmd: List[str]) -> str:
        """Format command for clear logging and debugging."""
        
        # Group related parameters for readability
        formatted_lines = []
        formatted_lines.append(f"{cmd[0]} \\")  # executable
        
        i = 1
        while i < len(cmd):
            param = cmd[i]
            
            if param.startswith('-'):
                # Parameter with potential values
                param_line = f"  {param}"
                
                # Add values until next parameter or end
                i += 1
                while i < len(cmd) and not cmd[i].startswith('-'):
                    param_line += f" {cmd[i]}"
                    i += 1
                
                param_line += " \\"
                formatted_lines.append(param_line)
            else:
                i += 1
        
        # Remove trailing backslash
        if formatted_lines:
            formatted_lines[-1] = formatted_lines[-1].rstrip(" \\")
        
        return "\n".join(formatted_lines)


class CommandExecutor:
    """Enhanced command executor with verification and logging."""
    
    def __init__(self, verify_executable: bool = True, log_output: bool = True):
        self.verify_executable = verify_executable
        self.log_output = log_output
        self.logger = logging.getLogger(__name__)
    
    def execute_c_reference(
        self, 
        cmd: List[str], 
        metadata: Dict[str, Any],
        timeout: int = 300,
        verify_outputs: bool = True
    ) -> subprocess.CompletedProcess:
        """Execute C reference with comprehensive logging and verification."""
        
        # Pre-execution validation
        if self.verify_executable and not self._validate_executable(cmd[0]):
            raise FileNotFoundError(f"C executable not found or not executable: {cmd[0]}")
        
        # Log the command being executed
        self.logger.info("Executing C reference command:")
        formatted_cmd = CommandBuilder().format_command_for_logging(cmd)
        self.logger.info(f"\n{formatted_cmd}")
        
        # Log metadata for debugging
        self.logger.info(f"Command metadata: {metadata}")
        
        # Execute
        try:
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=Path(cmd[0]).parent if '/' in cmd[0] else None
            )
        except subprocess.TimeoutExpired:
            self.logger.error(f"Command timed out after {timeout} seconds")
            raise
        
        # Post-execution verification
        if verify_outputs:
            self._verify_execution_results(result, metadata)
        
        # Log outputs if enabled
        if self.log_output:
            self.logger.info(f"Return code: {result.returncode}")
            if result.stdout:
                self.logger.info(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                self.logger.info(f"STDERR:\n{result.stderr}")
        
        return result
    
    def _validate_executable(self, executable_path: str) -> bool:
        """Validate that executable exists and is executable."""
        path = Path(executable_path)
        return path.exists() and os.access(path, os.X_OK)
    
    def _verify_execution_results(self, result: subprocess.CompletedProcess, metadata: Dict[str, Any]):
        """Verify that execution results match expectations."""
        
        # Check return code
        if result.returncode != 0:
            self.logger.error(f"C executable failed with return code {result.returncode}")
            if result.stderr:
                self.logger.error(f"Error output: {result.stderr}")
            raise subprocess.CalledProcessError(result.returncode, result.args, result.stdout, result.stderr)
        
        # Verify convention selection
        if 'explicit_convention' in metadata:
            expected_convention = metadata['explicit_convention']
            convention_msg = f"{expected_convention} convention selected"
            if convention_msg not in result.stderr:
                self.logger.warning(
                    f"Expected '{convention_msg}' not found in stderr. "
                    f"Actual stderr: {result.stderr[:200]}..."
                )
        
        # Check for unexpected convention switches
        stderr_lower = result.stderr.lower()
        if 'custom convention selected' in stderr_lower and metadata.get('explicit_convention') != 'custom':
            self.logger.error(
                "🚨 UNEXPECTED CUSTOM CONVENTION SELECTED! "
                "This indicates hidden behavior triggered by parameter combination. "
                "Check for vector parameters without explicit -convention flag."
            )


# Enhanced utility functions

def build_validated_c_command(
    detector_config: DetectorConfig,
    crystal_config: CrystalConfig,
    beam_config: BeamConfig,
    matrix_file: str = "identity.mat",
    executable_path: str = "golden_suite_generator/nanoBragg",
    strict_mode: bool = True
) -> Tuple[List[str], Dict[str, Any]]:
    """
    Build C command with full validation and hidden behavior prevention.
    
    This is the main entry point that replaces the original build_nanobragg_command.
    """
    
    builder = CommandBuilder(
        enable_warnings=True, 
        strict_validation=strict_mode
    )
    
    cmd, metadata = builder.build_command(
        detector_config, crystal_config, beam_config, 
        matrix_file, executable_path=executable_path
    )
    
    # Additional validation for strict mode
    if strict_mode:
        if metadata['warnings']:
            warnings.warn(
                f"Hidden behavior warnings detected: {metadata['warnings']}. "
                f"Consider using explicit convention control."
            )
        
        if metadata['validation_issues']:
            raise ValueError(
                f"Configuration validation failed: {metadata['validation_issues']}"
            )
    
    return cmd, metadata


def execute_c_reference_with_logging(
    cmd: List[str], 
    metadata: Dict[str, Any],
    log_file: Optional[str] = None
) -> subprocess.CompletedProcess:
    """Execute C reference with comprehensive logging."""
    
    # Set up logging
    if log_file:
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger = logging.getLogger(__name__)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    executor = CommandExecutor(verify_executable=True, log_output=True)
    return executor.execute_c_reference(cmd, metadata)


# Regression test utilities

def test_hidden_behavior_detection():
    """Test that hidden behaviors are properly detected."""
    
    # Test case 1: Vector parameter without explicit convention
    cmd_with_hidden_trigger = [
        'nanoBragg', '-distance', '100', '-twotheta_axis', '0', '0', '-1'
    ]
    
    warnings_list = HiddenBehaviorDetector.check_for_hidden_triggers(cmd_with_hidden_trigger)
    assert len(warnings_list) > 0, "Should detect hidden behavior trigger"
    assert 'CUSTOM convention' in warnings_list[0], "Should warn about CUSTOM convention"
    
    # Test case 2: Explicit convention specified
    cmd_with_explicit_convention = [
        'nanoBragg', '-convention', 'custom', '-distance', '100', '-twotheta_axis', '0', '0', '-1'
    ]
    
    warnings_list = HiddenBehaviorDetector.check_for_hidden_triggers(cmd_with_explicit_convention)
    assert len(warnings_list) == 0, "Should not warn when convention is explicit"


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    from nanobrag_torch.config import DetectorConvention, DetectorPivot
    
    # Create test configuration
    detector_config = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=1024,
        fpixels=1024,
        beam_center_s=51.2,
        beam_center_f=51.2,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
        detector_twotheta_deg=20.0,
    )
    
    crystal_config = CrystalConfig(
        cell_a=100.0, cell_b=100.0, cell_c=100.0,
        cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
        N_cells=(5, 5, 5)
    )
    
    beam_config = BeamConfig(wavelength_A=6.2)
    
    # Build command with validation
    cmd, metadata = build_validated_c_command(
        detector_config, crystal_config, beam_config
    )
    
    print("Generated command:")
    print(CommandBuilder().format_command_for_logging(cmd))
    print(f"\nMetadata: {metadata}")
    
    # Run regression test
    test_hidden_behavior_detection()
    print("✅ Hidden behavior detection tests passed")
#!/usr/bin/env python3
"""
nanoBragg Pre-Flight Check System
=================================

Comprehensive validation system for nanoBragg simulations to prevent convention
switching bugs and other common configuration issues.

This script provides automated checking of:
• Convention consistency and conflict detection
• Parameter validation against known good configurations  
• File system readiness (paths, permissions, disk space)
• Environment setup verification
• Correlation validation against golden references

Usage:
    python preflight_check.py --config my_simulation.conf
    python preflight_check.py --script my_simulation.sh
    python preflight_check.py --interactive
    python preflight_check.py --validate-environment
"""

import sys
import os
import argparse
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import tempfile
import time

# Import our warning system
try:
    from startup_warnings import NanoBraggParameterParser, Warning, print_warning
except ImportError:
    print("❌ Error: Cannot import startup_warnings.py")
    print("   Make sure startup_warnings.py is in the same directory")
    sys.exit(1)

# ASCII Art for the pre-flight system
PREFLIGHT_BANNER = """
✈️ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✈️
✈️                                                                          ✈️
✈️                    nanoBragg PRE-FLIGHT CHECK SYSTEM                     ✈️
✈️                                                                          ✈️
✈️            Comprehensive validation before simulation launch             ✈️
✈️                                                                          ✈️
✈️ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ✈️
"""

CHECKLIST_COMPLETE = """
🎉 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 🎉
🎉                                                                         🎉
🎉                       🚀 CLEARED FOR TAKEOFF! 🚀                        🎉
🎉                                                                         🎉
🎉  All pre-flight checks completed successfully.                          🎉
🎉  Your nanoBragg simulation is ready to launch!                          🎉
🎉                                                                         🎉
🎉 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 🎉
"""

CHECKLIST_FAILED = """
🛑 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 🛑
🛑                                                                         🛑
🛑                        ❌ PRE-FLIGHT FAILED ❌                           🛑
🛑                                                                         🛑
🛑  Critical issues found. DO NOT proceed with simulation.                 🛑
🛑  Fix the above issues and run pre-flight check again.                   🛑
🛑                                                                         🛑
🛑 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 🛑
"""

@dataclass
class CheckResult:
    """Result of a single validation check."""
    name: str
    status: str  # 'PASS', 'WARN', 'FAIL'
    message: str
    details: Optional[str] = None
    fix_suggestion: Optional[str] = None

@dataclass
class PreFlightConfig:
    """Configuration for pre-flight checks."""
    nanoBragg_path: str = "./nanoBragg"
    output_dir: str = "preflight_output"
    temp_dir: Optional[str] = None
    check_correlation: bool = True
    check_disk_space: bool = True
    min_disk_space_mb: int = 1000
    correlation_threshold: float = 0.999
    validation_timeout: int = 300  # 5 minutes

class PreFlightChecker:
    """Main pre-flight validation system."""
    
    def __init__(self, config: PreFlightConfig):
        self.config = config
        self.results: List[CheckResult] = []
        self.parameters: Dict[str, Any] = {}
        
    def log_result(self, result: CheckResult) -> None:
        """Log a check result."""
        self.results.append(result)
        
        # Print result with appropriate formatting
        status_symbols = {
            'PASS': '✅',
            'WARN': '⚠️ ',
            'FAIL': '❌'
        }
        
        symbol = status_symbols.get(result.status, '❓')
        print(f"{symbol} {result.name}: {result.message}")
        
        if result.details:
            print(f"   Details: {result.details}")
            
        if result.fix_suggestion:
            print(f"   Fix: {result.fix_suggestion}")
        
        print()
    
    def check_environment(self) -> None:
        """Check that the runtime environment is properly set up."""
        print("🔧 Checking runtime environment...")
        
        # Check nanoBragg executable
        if Path(self.config.nanoBragg_path).exists():
            if os.access(self.config.nanoBragg_path, os.X_OK):
                self.log_result(CheckResult(
                    name="nanoBragg Executable",
                    status="PASS", 
                    message=f"Found and executable: {self.config.nanoBragg_path}"
                ))
            else:
                self.log_result(CheckResult(
                    name="nanoBragg Executable",
                    status="FAIL",
                    message=f"Found but not executable: {self.config.nanoBragg_path}",
                    fix_suggestion="Run: chmod +x " + self.config.nanoBragg_path
                ))
        else:
            self.log_result(CheckResult(
                name="nanoBragg Executable",
                status="FAIL",
                message=f"nanoBragg not found: {self.config.nanoBragg_path}",
                fix_suggestion="Compile nanoBragg: gcc -O3 -o nanoBragg nanoBragg.c -lm -fopenmp"
            ))
        
        # Check Python environment
        try:
            import numpy
            self.log_result(CheckResult(
                name="Python NumPy",
                status="PASS",
                message=f"NumPy {numpy.__version__} available"
            ))
        except ImportError:
            self.log_result(CheckResult(
                name="Python NumPy", 
                status="FAIL",
                message="NumPy not available",
                fix_suggestion="Install: pip install numpy"
            ))
        
        # Check torch (if needed)
        try:
            import torch
            self.log_result(CheckResult(
                name="PyTorch",
                status="PASS", 
                message=f"PyTorch {torch.__version__} available"
            ))
            
            # Check KMP environment variable
            if os.environ.get('KMP_DUPLICATE_LIB_OK') == 'TRUE':
                self.log_result(CheckResult(
                    name="KMP Environment",
                    status="PASS",
                    message="KMP_DUPLICATE_LIB_OK=TRUE set"
                ))
            else:
                self.log_result(CheckResult(
                    name="KMP Environment",
                    status="WARN",
                    message="KMP_DUPLICATE_LIB_OK not set",
                    fix_suggestion="Set environment: export KMP_DUPLICATE_LIB_OK=TRUE"
                ))
        except ImportError:
            self.log_result(CheckResult(
                name="PyTorch",
                status="WARN",
                message="PyTorch not available (only needed for validation scripts)"
            ))
    
    def check_filesystem(self) -> None:
        """Check filesystem readiness."""
        print("📁 Checking filesystem...")
        
        # Check output directory
        output_path = Path(self.config.output_dir)
        if output_path.exists():
            if output_path.is_dir():
                if os.access(output_path, os.W_OK):
                    self.log_result(CheckResult(
                        name="Output Directory",
                        status="PASS",
                        message=f"Output directory writable: {output_path}"
                    ))
                else:
                    self.log_result(CheckResult(
                        name="Output Directory",
                        status="FAIL",
                        message=f"Output directory not writable: {output_path}",
                        fix_suggestion=f"Fix permissions: chmod 755 {output_path}"
                    ))
            else:
                self.log_result(CheckResult(
                    name="Output Directory",
                    status="FAIL",
                    message=f"Output path exists but is not a directory: {output_path}",
                    fix_suggestion=f"Remove file: rm {output_path}"
                ))
        else:
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                self.log_result(CheckResult(
                    name="Output Directory", 
                    status="PASS",
                    message=f"Created output directory: {output_path}"
                ))
            except PermissionError:
                self.log_result(CheckResult(
                    name="Output Directory",
                    status="FAIL", 
                    message=f"Cannot create output directory: {output_path}",
                    fix_suggestion="Check parent directory permissions"
                ))
        
        # Check disk space
        if self.config.check_disk_space:
            try:
                disk_usage = shutil.disk_usage(output_path.parent)
                free_space_mb = disk_usage.free // (1024 * 1024)
                
                if free_space_mb >= self.config.min_disk_space_mb:
                    self.log_result(CheckResult(
                        name="Disk Space",
                        status="PASS",
                        message=f"Free space: {free_space_mb:,} MB (required: {self.config.min_disk_space_mb} MB)"
                    ))
                else:
                    self.log_result(CheckResult(
                        name="Disk Space",
                        status="FAIL",
                        message=f"Insufficient disk space: {free_space_mb:,} MB (required: {self.config.min_disk_space_mb} MB)",
                        fix_suggestion="Free up disk space or choose different output directory"
                    ))
            except Exception as e:
                self.log_result(CheckResult(
                    name="Disk Space",
                    status="WARN",
                    message=f"Could not check disk space: {e}"
                ))
    
    def check_parameters(self, parameters: Dict[str, str]) -> None:
        """Check parameter configuration using startup warnings system."""
        print("⚙️  Checking parameter configuration...")
        
        self.parameters = parameters
        
        # Convert parameters to command line format for startup_warnings
        args = []
        for key, value in parameters.items():
            args.append(key)
            if value is not None:
                args.append(str(value))
        
        # Use startup warnings system  
        parser = NanoBraggParameterParser()
        parser.parse_command_line(args)
        warnings = parser.analyze()
        
        if not warnings:
            self.log_result(CheckResult(
                name="Parameter Configuration",
                status="PASS",
                message="No parameter issues detected"
            ))
        else:
            has_critical = False
            has_warnings = False
            
            for warning in warnings:
                if warning.level == 'CRITICAL':
                    has_critical = True
                    self.log_result(CheckResult(
                        name=f"CRITICAL: {warning.title}",
                        status="FAIL",
                        message=warning.message.strip(),
                        details=f"Affected parameters: {', '.join(warning.parameters)}",
                        fix_suggestion=warning.solution.strip()
                    ))
                elif warning.level == 'WARNING':
                    has_warnings = True
                    self.log_result(CheckResult(
                        name=f"WARNING: {warning.title}",
                        status="WARN",
                        message=warning.message.strip(),
                        details=f"Affected parameters: {', '.join(warning.parameters)}",
                        fix_suggestion=warning.solution.strip()
                    ))
                else:
                    self.log_result(CheckResult(
                        name=f"INFO: {warning.title}",
                        status="PASS",
                        message=warning.message.strip(),
                        details=f"Parameters: {', '.join(warning.parameters)}"
                    ))
            
            if has_critical:
                self.log_result(CheckResult(
                    name="Overall Parameter Status",
                    status="FAIL", 
                    message="Critical parameter issues found - simulation will fail",
                    fix_suggestion="Fix all CRITICAL issues above before proceeding"
                ))
            elif has_warnings:
                self.log_result(CheckResult(
                    name="Overall Parameter Status",
                    status="WARN",
                    message="Parameter warnings found - proceed with caution",
                    fix_suggestion="Review WARNING issues above"
                ))
    
    def check_input_files(self, parameters: Dict[str, str]) -> None:
        """Check that input files exist and are readable."""
        print("📄 Checking input files...")
        
        # Files to check based on parameters
        file_params = {
            '-hkl': 'HKL Structure Factors',
            '-matrix': 'Orientation Matrix', 
            '-mat': 'Matrix File',
            '-stolfile': 'STOL File',
            '-Amatrixfile': 'A Matrix File'
        }
        
        for param, description in file_params.items():
            if param in parameters:
                filepath = parameters[param]
                path = Path(filepath)
                
                if path.exists():
                    if path.is_file():
                        if os.access(path, os.R_OK):
                            # Check file size
                            size = path.stat().st_size
                            if size > 0:
                                self.log_result(CheckResult(
                                    name=f"{description} File",
                                    status="PASS",
                                    message=f"File exists and readable: {filepath} ({size} bytes)"
                                ))
                            else:
                                self.log_result(CheckResult(
                                    name=f"{description} File",
                                    status="FAIL",
                                    message=f"File is empty: {filepath}",
                                    fix_suggestion="Verify file content"
                                ))
                        else:
                            self.log_result(CheckResult(
                                name=f"{description} File",
                                status="FAIL",
                                message=f"File not readable: {filepath}",
                                fix_suggestion=f"Fix permissions: chmod 644 {filepath}"
                            ))
                    else:
                        self.log_result(CheckResult(
                            name=f"{description} File", 
                            status="FAIL",
                            message=f"Path is not a file: {filepath}",
                            fix_suggestion="Check path specification"
                        ))
                else:
                    self.log_result(CheckResult(
                        name=f"{description} File",
                        status="FAIL",
                        message=f"File not found: {filepath}",
                        fix_suggestion="Check file path and ensure file exists"
                    ))
    
    def check_golden_reference(self) -> None:
        """Run a quick golden reference test to verify system works."""
        if not self.config.check_correlation:
            return
            
        print("🏆 Running golden reference validation...")
        
        # Simple cubic test parameters
        golden_params = {
            '-lambda': '6.2',
            '-N': '5', 
            '-cell': '100 100 100 90 90 90',
            '-default_F': '100',
            '-distance': '100',
            '-detpixels': '1024',
        }
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.bin', delete=False) as tmp_file:
            tmp_output = tmp_file.name
        
        try:
            # Build nanoBragg command
            cmd = [self.config.nanoBragg_path]
            for key, value in golden_params.items():
                cmd.extend([key, value])
            cmd.extend(['-floatfile', tmp_output])
            
            # Run nanoBragg with timeout
            start_time = time.time()
            try:
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True,
                    timeout=self.config.validation_timeout
                )
                
                runtime = time.time() - start_time
                
                if result.returncode == 0:
                    # Check output file
                    if Path(tmp_output).exists():
                        file_size = Path(tmp_output).stat().st_size
                        expected_size = 1024 * 1024 * 4  # 1024x1024 pixels, 4 bytes each
                        
                        if file_size == expected_size:
                            self.log_result(CheckResult(
                                name="Golden Reference Test",
                                status="PASS",
                                message=f"Simple cubic test completed successfully ({runtime:.1f}s)",
                                details=f"Output file: {file_size:,} bytes"
                            ))
                        else:
                            self.log_result(CheckResult(
                                name="Golden Reference Test",
                                status="WARN", 
                                message=f"Test completed but output size unexpected",
                                details=f"Got {file_size:,} bytes, expected {expected_size:,} bytes"
                            ))
                    else:
                        self.log_result(CheckResult(
                            name="Golden Reference Test",
                            status="FAIL",
                            message="Test completed but no output file created",
                            fix_suggestion="Check nanoBragg output permissions"
                        ))
                else:
                    self.log_result(CheckResult(
                        name="Golden Reference Test",
                        status="FAIL",
                        message=f"nanoBragg failed with return code {result.returncode}",
                        details=f"stderr: {result.stderr}",
                        fix_suggestion="Check nanoBragg compilation and dependencies"
                    ))
                    
            except subprocess.TimeoutExpired:
                self.log_result(CheckResult(
                    name="Golden Reference Test",
                    status="FAIL",
                    message=f"Test timed out after {self.config.validation_timeout}s",
                    fix_suggestion="Check system performance or increase timeout"
                ))
            
        except Exception as e:
            self.log_result(CheckResult(
                name="Golden Reference Test",
                status="FAIL",
                message=f"Test failed with exception: {e}",
                fix_suggestion="Check nanoBragg path and system setup"
            ))
        
        finally:
            # Clean up temporary file
            try:
                Path(tmp_output).unlink()
            except:
                pass
    
    def run_all_checks(self, parameters: Optional[Dict[str, str]] = None) -> bool:
        """Run all pre-flight checks and return True if safe to proceed."""
        print(PREFLIGHT_BANNER)
        print("Starting comprehensive pre-flight validation...\n")
        
        # Run all checks
        self.check_environment()
        self.check_filesystem()
        
        if parameters:
            self.check_parameters(parameters)
            self.check_input_files(parameters)
        
        self.check_golden_reference()
        
        # Analyze results
        failures = [r for r in self.results if r.status == 'FAIL']
        warnings = [r for r in self.results if r.status == 'WARN']
        passes = [r for r in self.results if r.status == 'PASS']
        
        # Summary
        print("="*80)
        print(f"Pre-flight check summary:")
        print(f"  ✅ PASSED: {len(passes)}")
        print(f"  ⚠️  WARNED: {len(warnings)}")
        print(f"  ❌ FAILED: {len(failures)}")
        print()
        
        if failures:
            print(CHECKLIST_FAILED)
            return False
        elif warnings:
            print("⚠️  Warnings found - please review before proceeding")
            response = input("Continue with simulation anyway? [y/N]: ")
            return response.lower() in ['y', 'yes']
        else:
            print(CHECKLIST_COMPLETE)
            return True

def parse_config_file(config_path: str) -> Dict[str, str]:
    """Parse a configuration file into parameter dictionary."""
    parameters = {}
    
    if config_path.endswith('.json'):
        with open(config_path, 'r') as f:
            data = json.load(f)
            parameters = data.get('parameters', data)
    else:
        # Parse simple key=value format
        with open(config_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        parameters[key.strip()] = value.strip()
                    else:
                        print(f"Warning: Invalid config line {line_num}: {line}")
    
    return parameters

def parse_script_file(script_path: str) -> Dict[str, str]:
    """Parse a shell script file to extract nanoBragg parameters."""
    parameters = {}
    
    with open(script_path, 'r') as f:
        content = f.read()
    
    # Find nanoBragg command lines (simplified parsing)
    lines = content.split('\n')
    for line in lines:
        line = line.strip()
        if 'nanoBragg' in line and not line.startswith('#'):
            # Extract parameters (simplified - could be enhanced)
            parts = line.split()
            i = 0
            while i < len(parts):
                if parts[i].startswith('-'):
                    param = parts[i]
                    if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                        value = parts[i + 1] 
                        i += 2
                    else:
                        value = None
                        i += 1
                    parameters[param] = value
                else:
                    i += 1
            break  # Use first nanoBragg command found
    
    return parameters

def interactive_setup() -> Dict[str, str]:
    """Interactive parameter setup."""
    print("🎯 Interactive nanoBragg Configuration Setup")
    print("=" * 50)
    
    parameters = {}
    
    # Essential parameters
    essential = [
        ('-lambda', 'X-ray wavelength (Angstroms)', '6.2'),
        ('-N', 'Crystal size (unit cells per dimension)', '5'), 
        ('-cell', 'Unit cell (a b c alpha beta gamma)', '100 100 100 90 90 90'),
        ('-default_F', 'Default structure factor magnitude', '100'),
        ('-distance', 'Detector distance (mm)', '100'),
        ('-detpixels', 'Detector size (pixels)', '1024')
    ]
    
    print("\n📋 Essential Parameters:")
    for param, description, default in essential:
        value = input(f"{param} - {description} [{default}]: ").strip()
        parameters[param] = value if value else default
    
    # Optional parameters
    print("\n📋 Optional Parameters (press Enter to skip):")
    optional = [
        ('-Xbeam', 'X beam center (pixels)'),
        ('-Ybeam', 'Y beam center (pixels)'),
        ('-detector_rotx', 'Detector rotation X (degrees)'),
        ('-detector_roty', 'Detector rotation Y (degrees)'),
        ('-detector_rotz', 'Detector rotation Z (degrees)'),
        ('-twotheta', 'Two-theta angle (degrees)'),
        ('-convention', 'Convention (MOSFLM/XDS/CUSTOM)')
    ]
    
    for param, description in optional:
        value = input(f"{param} - {description}: ").strip()
        if value:
            parameters[param] = value
    
    return parameters

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="nanoBragg pre-flight check system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Check configuration file
    python preflight_check.py --config my_sim.conf
    
    # Check shell script  
    python preflight_check.py --script my_sim.sh
    
    # Interactive setup
    python preflight_check.py --interactive
    
    # Environment check only
    python preflight_check.py --validate-environment
        """
    )
    
    parser.add_argument('--config', help='Configuration file to validate')
    parser.add_argument('--script', help='Shell script file to validate')
    parser.add_argument('--interactive', action='store_true', help='Interactive setup')
    parser.add_argument('--validate-environment', action='store_true', help='Check environment only')
    parser.add_argument('--nanoBragg-path', default='./nanoBragg', help='Path to nanoBragg executable')
    parser.add_argument('--output-dir', default='preflight_output', help='Output directory')
    parser.add_argument('--no-correlation', action='store_true', help='Skip correlation validation')
    parser.add_argument('--timeout', type=int, default=300, help='Validation timeout (seconds)')
    
    args = parser.parse_args()
    
    # Create configuration
    config = PreFlightConfig(
        nanoBragg_path=args.nanoBragg_path,
        output_dir=args.output_dir,
        check_correlation=not args.no_correlation,
        validation_timeout=args.timeout
    )
    
    checker = PreFlightChecker(config)
    
    # Determine what to check
    parameters = None
    
    if args.config:
        try:
            parameters = parse_config_file(args.config)
            print(f"📝 Loaded configuration from: {args.config}")
        except Exception as e:
            print(f"❌ Error loading config file: {e}")
            sys.exit(1)
            
    elif args.script:
        try:
            parameters = parse_script_file(args.script)
            print(f"📜 Parsed script file: {args.script}")
        except Exception as e:
            print(f"❌ Error parsing script file: {e}")
            sys.exit(1)
            
    elif args.interactive:
        parameters = interactive_setup()
        
    elif args.validate_environment:
        # Environment check only
        checker.check_environment()
        checker.check_filesystem()
        sys.exit(0)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Run validation
    success = checker.run_all_checks(parameters)
    
    if success:
        print("🚀 Ready for nanoBragg simulation launch!")
        if parameters:
            # Optionally save validated configuration
            output_config = Path(config.output_dir) / "validated_config.json"
            with open(output_config, 'w') as f:
                json.dump({
                    'parameters': parameters,
                    'validation_time': time.time(),
                    'preflight_results': [asdict(r) for r in checker.results]
                }, f, indent=2)
            print(f"💾 Validated configuration saved to: {output_config}")
    else:
        print("🛑 Pre-flight check failed - do not proceed")
        sys.exit(1)

if __name__ == '__main__':
    main()
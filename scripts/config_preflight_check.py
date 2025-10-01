#!/usr/bin/env python3
"""
Pre-flight configuration consistency check between C and PyTorch implementations.

This module provides functions to detect configuration mismatches before running
simulations, preventing the class of bugs that caused 3-6 months of debugging.
"""

import os
import re
import sys
from typing import Dict, Optional, Tuple
from enum import Enum


class CheckSeverity(Enum):
    """Severity levels for configuration checks."""
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ConfigCheckResult:
    """Result of a configuration check."""
    
    def __init__(self, severity: CheckSeverity, message: str, 
                 c_config: Optional[Dict] = None, 
                 py_config: Optional[Dict] = None,
                 recommendation: Optional[str] = None):
        self.severity = severity
        self.message = message
        self.c_config = c_config
        self.py_config = py_config
        self.recommendation = recommendation
    
    def display(self, verbose: bool = False):
        """Display the check result."""
        if self.severity == CheckSeverity.SUCCESS:
            if verbose:
                print("✓ Configuration check passed")
        elif self.severity == CheckSeverity.WARNING:
            print("\n" + "="*60)
            print("⚠️  Configuration Warning")
            print("="*60)
            print(f"   {self.message}")
            if self.recommendation:
                print(f"\n   Recommendation: {self.recommendation}")
            if verbose and self.c_config and self.py_config:
                print(f"\n   C config: {self.c_config}")
                print(f"   PyTorch config: {self.py_config}")
            print("="*60 + "\n")
        else:  # CRITICAL
            print("\n" + "="*60)
            print("⚠️  CONFIGURATION MISMATCH DETECTED!")
            print("="*60)
            if self.c_config and self.py_config:
                print(f"   C implementation is in {self.c_config.get('mode', 'UNKNOWN')} mode")
                print(f"   PyTorch implementation is in {self.py_config.get('mode', 'UNKNOWN')} mode")
            print(f"\n   {self.message}")
            print("\n   This WILL cause correlation failures!")
            
            if self.recommendation:
                print(f"\n   {self.recommendation}")
            
            print("\n   Common causes:")
            print("     1. Test script passing -twotheta_axis")
            print("     2. Different default parameters")
            print("\n   Quick fix:")
            print("     Remove -twotheta_axis from C command")
            print("\n   See: docs/configuration_mismatch.md")
            print("="*60 + "\n")
    
    def should_fail_strict(self) -> bool:
        """Whether this result should cause failure in strict mode."""
        return self.severity == CheckSeverity.CRITICAL


def extract_config_from_output(output: str) -> Dict[str, str]:
    """Extract configuration information from C or PyTorch output."""
    config = {}
    
    # Extract CONFIG_MODE
    mode_match = re.search(r'CONFIG_MODE:\s*(\w+)', output)
    if mode_match:
        config['mode'] = mode_match.group(1)
    
    # Extract CONFIG_TRIGGER
    trigger_match = re.search(r'CONFIG_TRIGGER:\s*(.+)', output)
    if trigger_match:
        config['trigger'] = trigger_match.group(1).strip()
    
    # Extract CONFIG_HASH
    hash_match = re.search(r'CONFIG_HASH:\s*(\w+)', output)
    if hash_match:
        config['hash'] = hash_match.group(1)
    
    return config


def preflight_check(c_output: str, py_output: str) -> ConfigCheckResult:
    """
    Perform pre-flight configuration consistency check.
    
    Args:
        c_output: Output from C implementation containing CONFIG_* lines
        py_output: Output from PyTorch implementation containing CONFIG_* lines
    
    Returns:
        ConfigCheckResult with severity and recommendations
    """
    # Step 1: Extract configuration from both outputs
    c_config = extract_config_from_output(c_output)
    py_config = extract_config_from_output(py_output)
    
    # Check if we have configuration info
    if not c_config or not py_config:
        return ConfigCheckResult(
            CheckSeverity.WARNING,
            "Configuration information not found in one or both outputs",
            c_config, py_config,
            "Ensure both implementations are compiled with CONFIG_MODE output"
        )
    
    # Step 2: Check for mode mismatch
    c_mode = c_config.get('mode', 'UNKNOWN')
    py_mode = py_config.get('mode', 'UNKNOWN')
    
    if c_mode != py_mode:
        # Determine specific recommendation based on the mismatch
        if c_mode == 'CUSTOM' and py_mode == 'MOSFLM':
            recommendation = (
                "Quick fix:\n"
                "     Option 1: Remove -twotheta_axis from C command\n"
                "     Option 2: Set convention='CUSTOM' in PyTorch config"
            )
        elif c_mode == 'MOSFLM' and py_mode == 'CUSTOM':
            recommendation = (
                "Quick fix:\n"
                "     Option 1: Add -mosflm to C command\n"
                "     Option 2: Set convention='MOSFLM' in PyTorch config"
            )
        else:
            recommendation = f"Align conventions: both should use {c_mode} or {py_mode}"
        
        return ConfigCheckResult(
            CheckSeverity.CRITICAL,
            f"Mode mismatch: C={c_mode}, PyTorch={py_mode}",
            c_config, py_config,
            recommendation
        )
    
    # Step 3: Check for hash mismatch (warning only)
    c_hash = c_config.get('hash', '')
    py_hash = py_config.get('hash', '')
    
    if c_hash and py_hash and c_hash != py_hash:
        return ConfigCheckResult(
            CheckSeverity.WARNING,
            f"Configuration hashes differ ({c_hash} vs {py_hash})",
            c_config, py_config,
            "Parameters may differ slightly between implementations"
        )
    
    # Step 4: Check trigger consistency
    c_trigger = c_config.get('trigger', '')
    py_trigger = py_config.get('trigger', '')
    
    if c_trigger != py_trigger:
        # This is informational, not necessarily a problem
        if 'default' in c_trigger and 'default' in py_trigger:
            # Both are defaults, just slightly different wording
            pass
        else:
            return ConfigCheckResult(
                CheckSeverity.WARNING,
                f"Different configuration triggers",
                c_config, py_config,
                f"C: {c_trigger}, PyTorch: {py_trigger}"
            )
    
    return ConfigCheckResult(
        CheckSeverity.SUCCESS,
        "Configuration check passed",
        c_config, py_config
    )


def check_from_files(c_output_file: str, py_output_file: str,
                      strict: bool = False, verbose: bool = False) -> bool:
    """
    Check configuration consistency from output files.
    
    Args:
        c_output_file: Path to C output file
        py_output_file: Path to PyTorch output file
        strict: If True, fail on any mismatch
        verbose: If True, show detailed output
    
    Returns:
        True if check passed (or only warnings in non-strict mode)
    """
    # Read output files
    with open(c_output_file, 'r') as f:
        c_output = f.read()
    
    with open(py_output_file, 'r') as f:
        py_output = f.read()
    
    # Perform check
    result = preflight_check(c_output, py_output)
    
    # Display result
    result.display(verbose=verbose)
    
    # Determine pass/fail
    if strict and result.should_fail_strict():
        return False
    
    return result.severity != CheckSeverity.CRITICAL


def main():
    """Command-line interface for pre-flight check."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Check configuration consistency between C and PyTorch implementations"
    )
    parser.add_argument(
        "c_output", 
        help="C implementation output file (or '-' for stdin)"
    )
    parser.add_argument(
        "py_output",
        help="PyTorch implementation output file"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on any configuration mismatch"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show detailed configuration information"
    )
    parser.add_argument(
        "--suppress",
        action="store_true",
        help="Suppress all output (debugging only)"
    )
    
    args = parser.parse_args()
    
    # Handle stdin input
    if args.c_output == '-':
        c_output = sys.stdin.read()
        with open(args.py_output, 'r') as f:
            py_output = f.read()
        result = preflight_check(c_output, py_output)
    else:
        # Read from files
        with open(args.c_output, 'r') as f:
            c_output = f.read()
        with open(args.py_output, 'r') as f:
            py_output = f.read()
        result = preflight_check(c_output, py_output)
    
    # Display result unless suppressed
    if not args.suppress:
        result.display(verbose=args.verbose)
    
    # Exit with appropriate code
    if args.strict and result.should_fail_strict():
        sys.exit(1)
    elif result.severity == CheckSeverity.CRITICAL:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    # Check for environment variables
    strict_mode = os.environ.get('STRICT_MODE', '0') == '1'
    suppress_mode = os.environ.get('SUPPRESS_PREFLIGHT', '0') == '1'
    verbose_mode = os.environ.get('PREFLIGHT_VERBOSE', '0') == '1'
    
    if suppress_mode:
        sys.exit(0)  # Skip check entirely
    
    # If called with arguments, use command-line interface
    if len(sys.argv) > 1:
        main()
    else:
        # Interactive demo
        print("Pre-Flight Configuration Check Demo")
        print("="*40)
        
        # Simulate outputs
        c_output_good = """
mosflm convention selected.
CONFIG_MODE: MOSFLM
CONFIG_TRIGGER: default
CONFIG_HASH: 12345678
"""
        
        py_output_good = """
CONFIG_MODE: MOSFLM
CONFIG_TRIGGER: default
CONFIG_HASH: 12345678
"""
        
        c_output_bad = """
custom convention selected.
CONFIG_MODE: CUSTOM
CONFIG_TRIGGER: twotheta_axis parameter
CONFIG_HASH: 87654321
"""
        
        print("\nTest 1: Matching configurations")
        result = preflight_check(c_output_good, py_output_good)
        result.display(verbose=True)
        
        print("\nTest 2: Configuration mismatch (the bug!)")
        result = preflight_check(c_output_bad, py_output_good)
        result.display(verbose=verbose_mode)
        
        if strict_mode and result.should_fail_strict():
            print("\nSTRICT_MODE=1: Exiting with error")
            sys.exit(1)
"""
Test suite for AT-CLI-001: CLI presence and help

From spec-a.md:
- AT-CLI-001 CLI presence and help
  - Setup: Invoke nanoBragg with -h (or --help).
  - Expectation: Prints usage including at least: -hkl, -mat, -cell, -pixel, -detpixels,
    -distance, -lambda|-energy, -floatfile, -intfile, -noisefile, -pgmfile, -scale,
    -adc, -mosflm/-xds/-adxv/-denzo/-dials, -roi. Exit code indicates success.
"""

import os
import sys
import subprocess
import pytest


class TestAT_CLI_001:
    """Test CLI help and presence."""

    def test_cli_help_short_flag(self):
        """Test that -h flag shows help."""
        # Run nanoBragg with -h
        result = subprocess.run(
            [sys.executable, '-m', 'nanobrag_torch', '-h'],
            capture_output=True,
            text=True,
            env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
        )

        # Check exit code is 0 (success)
        assert result.returncode == 0, f"Exit code was {result.returncode}, expected 0"

        # Check that usage is printed
        assert 'usage:' in result.stdout.lower() or 'Usage:' in result.stdout

        # Check for required flags per spec
        required_flags = [
            '-hkl', '-mat', '-cell', '-pixel', '-detpixels',
            '-distance', '-lambda', '-energy', '-floatfile', '-intfile',
            '-noisefile', '-pgmfile', '-scale', '-adc',
            '-mosflm', '-xds', '-adxv', '-denzo', '-dials', '-roi'
        ]

        for flag in required_flags:
            assert flag in result.stdout, f"Required flag {flag} not found in help output"

    def test_cli_help_long_flag(self):
        """Test that --help flag shows help."""
        # Run nanoBragg with --help
        result = subprocess.run(
            [sys.executable, '-m', 'nanobrag_torch', '--help'],
            capture_output=True,
            text=True,
            env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
        )

        # Check exit code is 0 (success)
        assert result.returncode == 0, f"Exit code was {result.returncode}, expected 0"

        # Check that usage is printed
        assert 'usage:' in result.stdout.lower() or 'Usage:' in result.stdout

        # Check for program name
        assert 'nanoBragg' in result.stdout

    def test_cli_invocable(self):
        """Test that the CLI module is invocable."""
        # Try to import the main module
        try:
            from nanobrag_torch.__main__ import main
            assert callable(main), "main function should be callable"
        except ImportError as e:
            pytest.fail(f"Could not import CLI module: {e}")

    def test_cli_help_includes_examples(self):
        """Test that help includes usage examples."""
        result = subprocess.run(
            [sys.executable, '-m', 'nanobrag_torch', '-h'],
            capture_output=True,
            text=True,
            env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
        )

        # Check for examples section
        assert 'example' in result.stdout.lower(), "Help should include examples"

    def test_cli_help_includes_wavelength_synonyms(self):
        """Test that both -lambda and -wave are documented."""
        result = subprocess.run(
            [sys.executable, '-m', 'nanobrag_torch', '-h'],
            capture_output=True,
            text=True,
            env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
        )

        # Check for wavelength synonyms
        assert '-lambda' in result.stdout or '-wave' in result.stdout
        assert 'wavelength' in result.stdout.lower()

    def test_cli_help_includes_output_synonyms(self):
        """Test that output file synonyms are documented."""
        result = subprocess.run(
            [sys.executable, '-m', 'nanobrag_torch', '-h'],
            capture_output=True,
            text=True,
            env={**os.environ, 'KMP_DUPLICATE_LIB_OK': 'TRUE'}
        )

        # Check for output file options with synonyms
        assert ('-floatfile' in result.stdout or '-floatimage' in result.stdout)
        assert ('-intfile' in result.stdout or '-intimage' in result.stdout)
        assert ('-noisefile' in result.stdout or '-noiseimage' in result.stdout)
        assert ('-pgmfile' in result.stdout or '-pgmimage' in result.stdout)
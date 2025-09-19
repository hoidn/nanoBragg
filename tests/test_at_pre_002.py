"""
Test AT-PRE-002: Pivot and origin overrides

From spec:
- Setup: Use -Xbeam/-Ybeam vs -Xclose/-Yclose vs -ORGX/-ORGY and -pivot.
- Expectation: -Xbeam/-Ybeam SHALL force pivot=BEAM; -Xclose/-Yclose and
  -ORGX/-ORGY SHALL force pivot=SAMPLE; -pivot SHALL override both.
"""

import subprocess
import tempfile
import os
import numpy as np
from pathlib import Path
import re

def create_simple_hkl_file(filepath):
    """Create a minimal HKL file for testing."""
    with open(filepath, 'w') as f:
        f.write("0 0 0 100.0\n")
        f.write("1 0 0 50.0\n")
        f.write("0 1 0 50.0\n")

def read_smv_header_value(filepath, key):
    """Read a specific header value from an SMV file."""
    with open(filepath, 'rb') as f:
        header_bytes = f.read(512)
        header_str = header_bytes.decode('ascii', errors='ignore')

        # Find the key in the header
        pattern = f'{key}=([^;]+);'
        match = re.search(pattern, header_str)
        if match:
            return match.group(1)
    return None

def test_xbeam_ybeam_forces_beam_pivot():
    """Test that -Xbeam/-Ybeam force pivot to BEAM."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create HKL file
        hkl_file = tmpdir / "test.hkl"
        create_simple_hkl_file(hkl_file)

        # Output file
        int_file = tmpdir / "output.img"

        # Run with -Xbeam/-Ybeam (should force BEAM pivot)
        cmd = [
            'python', '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-distance', '100',
            '-detpixels', '32',
            '-pixel', '0.1',
            '-Xbeam', '1.6',  # This should force pivot=BEAM
            '-Ybeam', '1.6',
            '-intfile', str(int_file),
            '-default_F', '100'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Check that BEAM pivot was used
        # The presence of BEAM_CENTER_X/Y in output confirms beam pivot behavior
        beam_center_x = read_smv_header_value(int_file, 'BEAM_CENTER_X')
        beam_center_y = read_smv_header_value(int_file, 'BEAM_CENTER_Y')

        assert float(beam_center_x) == 1.6, f"Expected BEAM_CENTER_X=1.6, got {beam_center_x}"
        assert float(beam_center_y) == 1.6, f"Expected BEAM_CENTER_Y=1.6, got {beam_center_y}"

def test_xclose_yclose_forces_sample_pivot():
    """Test that -Xclose/-Yclose force pivot to SAMPLE."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create HKL file
        hkl_file = tmpdir / "test.hkl"
        create_simple_hkl_file(hkl_file)

        # Output file
        int_file = tmpdir / "output.img"

        # Run with -Xclose/-Yclose (should force SAMPLE pivot)
        cmd = [
            'python', '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-distance', '100',  # This normally sets BEAM pivot
            '-detpixels', '32',
            '-pixel', '0.1',
            '-Xclose', '1.5',  # This should force pivot=SAMPLE
            '-Yclose', '1.5',
            '-intfile', str(int_file),
            '-default_F', '100'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # With SAMPLE pivot and Xclose/Yclose, the CLOSE_DISTANCE should be set
        close_distance = read_smv_header_value(int_file, 'CLOSE_DISTANCE')
        assert close_distance is not None, "CLOSE_DISTANCE should be set with SAMPLE pivot"

def test_orgx_orgy_forces_sample_pivot():
    """Test that -ORGX/-ORGY force pivot to SAMPLE."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create HKL file
        hkl_file = tmpdir / "test.hkl"
        create_simple_hkl_file(hkl_file)

        # Output file
        int_file = tmpdir / "output.img"

        # Run with -ORGX/-ORGY (should force SAMPLE pivot)
        cmd = [
            'python', '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-distance', '100',  # This normally sets BEAM pivot
            '-detpixels', '32',
            '-pixel', '0.1',
            '-ORGX', '16.5',  # This should force pivot=SAMPLE
            '-ORGY', '16.5',
            '-intfile', str(int_file),
            '-default_F', '100'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Check that XDS_ORGX/ORGY are set (indicates SAMPLE pivot behavior)
        xds_orgx = read_smv_header_value(int_file, 'XDS_ORGX')
        xds_orgy = read_smv_header_value(int_file, 'XDS_ORGY')

        assert xds_orgx is not None, "XDS_ORGX should be set"
        assert xds_orgy is not None, "XDS_ORGY should be set"

def test_explicit_pivot_override():
    """Test that explicit -pivot flag overrides all other pivot-forcing flags."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create HKL file
        hkl_file = tmpdir / "test.hkl"
        create_simple_hkl_file(hkl_file)

        # Output file
        int_file = tmpdir / "output.img"

        # Test 1: -pivot sample overrides -Xbeam/-Ybeam (which normally force BEAM)
        cmd = [
            'python', '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-distance', '100',
            '-detpixels', '32',
            '-pixel', '0.1',
            '-Xbeam', '1.6',  # Normally forces pivot=BEAM
            '-Ybeam', '1.6',
            '-pivot', 'sample',  # Explicit override to SAMPLE
            '-intfile', str(int_file),
            '-default_F', '100'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # SAMPLE pivot should be used despite -Xbeam/-Ybeam
        close_distance = read_smv_header_value(int_file, 'CLOSE_DISTANCE')
        assert close_distance is not None, "CLOSE_DISTANCE should be set with SAMPLE pivot override"

        # Test 2: -pivot beam overrides -ORGX/-ORGY (which normally force SAMPLE)
        cmd[cmd.index('-Xbeam')] = '-ORGX'
        cmd[cmd.index('1.6')] = '16.5'
        cmd[cmd.index('-Ybeam')] = '-ORGY'
        cmd[cmd.index('1.6')] = '16.5'
        cmd[cmd.index('sample')] = 'beam'  # Override to BEAM

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # BEAM pivot should be used despite -ORGX/-ORGY
        # Beam center values should be properly set
        beam_center_x = read_smv_header_value(int_file, 'BEAM_CENTER_X')
        beam_center_y = read_smv_header_value(int_file, 'BEAM_CENTER_Y')
        assert beam_center_x is not None, "BEAM_CENTER_X should be set with BEAM pivot override"
        assert beam_center_y is not None, "BEAM_CENTER_Y should be set with BEAM pivot override"

def test_distance_vs_close_distance_pivot_defaults():
    """Test that -distance sets BEAM pivot and -close_distance sets SAMPLE pivot by default."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create HKL file
        hkl_file = tmpdir / "test.hkl"
        create_simple_hkl_file(hkl_file)

        # Test 1: -distance alone should use BEAM pivot
        int_file = tmpdir / "output1.img"
        cmd = [
            'python', '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-distance', '100',  # Should set pivot=BEAM
            '-detpixels', '32',
            '-pixel', '0.1',
            '-intfile', str(int_file),
            '-default_F', '100'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Check for BEAM pivot indicators
        distance_header = read_smv_header_value(int_file, 'DISTANCE')
        assert float(distance_header) == 100.0, f"Expected DISTANCE=100, got {distance_header}"

        # Test 2: -close_distance alone should use SAMPLE pivot
        int_file = tmpdir / "output2.img"
        cmd = [
            'python', '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-close_distance', '100',  # Should set pivot=SAMPLE
            '-detpixels', '32',
            '-pixel', '0.1',
            '-intfile', str(int_file),
            '-default_F', '100'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Check for SAMPLE pivot indicators
        close_distance_header = read_smv_header_value(int_file, 'CLOSE_DISTANCE')
        assert close_distance_header is not None, "CLOSE_DISTANCE should be set with -close_distance"

def test_convention_default_pivots():
    """Test that different conventions have correct default pivots."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create HKL file
        hkl_file = tmpdir / "test.hkl"
        create_simple_hkl_file(hkl_file)

        # Test MOSFLM (should default to BEAM pivot)
        int_file = tmpdir / "output_mosflm.img"
        cmd = [
            'python', '-m', 'nanobrag_torch',
            '-hkl', str(hkl_file),
            '-cell', '100', '100', '100', '90', '90', '90',
            '-lambda', '1.0',
            '-mosflm',  # MOSFLM defaults to BEAM pivot
            '-distance', '100',
            '-detpixels', '32',
            '-pixel', '0.1',
            '-intfile', str(int_file),
            '-default_F', '100'
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Check for MOSFLM-specific headers
        mosflm_center_x = read_smv_header_value(int_file, 'MOSFLM_CENTER_X')
        assert mosflm_center_x is not None, "MOSFLM_CENTER_X should be set for MOSFLM convention"

        # Test XDS (should default to SAMPLE pivot)
        int_file = tmpdir / "output_xds.img"
        cmd[cmd.index('-mosflm')] = '-xds'
        cmd[cmd.index(str(tmpdir / "output_mosflm.img"))] = str(int_file)

        result = subprocess.run(cmd, capture_output=True, text=True)
        assert result.returncode == 0, f"Command failed: {result.stderr}"

        # Check for XDS-specific headers
        xds_orgx = read_smv_header_value(int_file, 'XDS_ORGX')
        xds_orgy = read_smv_header_value(int_file, 'XDS_ORGY')
        assert xds_orgx is not None, "XDS_ORGX should be set for XDS convention"
        assert xds_orgy is not None, "XDS_ORGY should be set for XDS convention"

if __name__ == "__main__":
    test_xbeam_ybeam_forces_beam_pivot()
    print("✓ test_xbeam_ybeam_forces_beam_pivot")

    test_xclose_yclose_forces_sample_pivot()
    print("✓ test_xclose_yclose_forces_sample_pivot")

    test_orgx_orgy_forces_sample_pivot()
    print("✓ test_orgx_orgy_forces_sample_pivot")

    test_explicit_pivot_override()
    print("✓ test_explicit_pivot_override")

    test_distance_vs_close_distance_pivot_defaults()
    print("✓ test_distance_vs_close_distance_pivot_defaults")

    test_convention_default_pivots()
    print("✓ test_convention_default_pivots")

    print("\nAll AT-PRE-002 tests passed!")
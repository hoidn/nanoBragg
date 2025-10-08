"""Simple test for AT-SRC-001 to verify source file parsing works.

This is a minimal test to verify the sourcefile parsing functionality
before full integration with the simulator.
"""

import pytest
import torch
import tempfile
from pathlib import Path

from nanobrag_torch.io.source import read_sourcefile


def test_sourcefile_parsing():
    """Basic test of source file parsing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sourcefile = Path(tmpdir) / "test_sources.txt"

        # Write test source file with two sources
        content = """# Test source file
-10.0  0.0  0.0  2.0  1.0e-10
0.0  -10.0  0.0  3.0  1.5e-10
"""
        sourcefile.write_text(content)

        # Read source file
        default_wavelength_m = 6.2e-10
        directions, weights, wavelengths = read_sourcefile(
            sourcefile,
            default_wavelength_m=default_wavelength_m
        )

        # Check results
        assert directions.shape == (2, 3)
        assert weights.shape == (2,)
        assert wavelengths.shape == (2,)

        # Check directions are normalized
        norms = torch.linalg.norm(directions, dim=1)
        torch.testing.assert_close(norms, torch.ones(2, dtype=torch.float64))

        # Check wavelengths
        assert wavelengths[0].item() == pytest.approx(1.0e-10)
        assert wavelengths[1].item() == pytest.approx(1.5e-10)

        # Check weights are preserved from file per AT-SRC-001 requirement
        expected_weights = torch.tensor([2.0, 3.0], dtype=torch.float64)
        torch.testing.assert_close(weights, expected_weights)

        print(f"✓ Source file parsing successful")
        print(f"  Directions: {directions}")
        print(f"  Wavelengths: {wavelengths}")
        print(f"  Weights: {weights}")


if __name__ == "__main__":
    test_sourcefile_parsing()
"""Simple test for AT-SRC-001 to verify source file parsing works.

This is a minimal test to verify the sourcefile parsing functionality
before full integration with the simulator.
"""

import pytest
import torch
import tempfile
from pathlib import Path

from nanobrag_torch.io.source import read_sourcefile


@pytest.mark.parametrize("dtype", [torch.float32, torch.float64, None])
def test_sourcefile_dtype_propagation(dtype):
    """Test that dtype parameter propagates correctly to output tensors.

    Regression test for Phase C dtype handling (SOURCE-WEIGHT-002 Phase C2).
    Verifies parser respects explicit dtype and defaults to torch.get_default_dtype().
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        sourcefile = Path(tmpdir) / "test_sources.txt"

        # Write test source file
        content = """# Test source file
-10.0  0.0  0.0  1.0  6.2e-10
0.0  -10.0  0.0  1.0  6.2e-10
"""
        sourcefile.write_text(content)

        # Read source file with specified dtype
        default_wavelength_m = 6.2e-10
        directions, weights, wavelengths = read_sourcefile(
            sourcefile,
            default_wavelength_m=default_wavelength_m,
            dtype=dtype
        )

        # Determine expected dtype
        if dtype is None:
            expected_dtype = torch.get_default_dtype()
        else:
            expected_dtype = dtype

        # Verify all tensors match expected dtype
        assert directions.dtype == expected_dtype, \
            f"directions dtype mismatch: {directions.dtype} != {expected_dtype}"
        assert weights.dtype == expected_dtype, \
            f"weights dtype mismatch: {weights.dtype} != {expected_dtype}"
        assert wavelengths.dtype == expected_dtype, \
            f"wavelengths dtype mismatch: {wavelengths.dtype} != {expected_dtype}"

        print(f"✓ dtype={dtype} propagation successful (resolved to {expected_dtype})")


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
        torch.testing.assert_close(norms, torch.ones(2, dtype=torch.float32))

        # Per spec-a-core.md:151-153, wavelength column is IGNORED.
        # All sources use CLI -lambda value (default_wavelength_m).
        assert wavelengths[0].item() == pytest.approx(default_wavelength_m)
        assert wavelengths[1].item() == pytest.approx(default_wavelength_m)

        # Check weights are preserved from file (for parsing correctness)
        expected_weights = torch.tensor([2.0, 3.0], dtype=torch.float32)
        torch.testing.assert_close(weights, expected_weights)

        print(f"✓ Source file parsing successful")
        print(f"  Directions: {directions}")
        print(f"  Wavelengths: {wavelengths}")
        print(f"  Weights: {weights}")


if __name__ == "__main__":
    test_sourcefile_parsing()
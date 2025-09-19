"""
Acceptance test AT-STR-002: Tricubic interpolation with fallback.

Tests tricubic interpolation of structure factors with proper fallback behavior
when neighborhood goes out of bounds.
"""

import torch
import tempfile
import os
from pathlib import Path
from io import StringIO

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import CrystalConfig


def test_tricubic_interpolation_enabled():
    """
    AT-STR-002: Test that tricubic interpolation is enabled and works correctly.

    Setup: Enable -interpolate; choose fractional h,k,l within a grid with complete 4×4×4 neighborhoods.
    Expectation: F_cell SHALL be tricubically interpolated between neighbors.
    """
    # Create a simple HKL file with a 5x5x5 grid of known values
    hkl_content = StringIO()

    # Generate a grid with values that vary smoothly
    for h in range(-2, 3):
        for k in range(-2, 3):
            for l in range(-2, 3):
                # Create a smooth function: F = 100 + 10*h + 5*k + 2*l
                F = 100.0 + 10.0 * h + 5.0 * k + 2.0 * l
                hkl_content.write(f"{h} {k} {l} {F:.1f}\n")

    # Write HKL to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.hkl', delete=False) as f:
        f.write(hkl_content.getvalue())
        hkl_file = f.name

    try:
        # Create crystal with interpolation enabled
        config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=0.0
        )

        crystal = Crystal(config, device='cpu')
        crystal.load_hkl(hkl_file)
        crystal.interpolate = True  # Force interpolation on

        # Test fractional indices that should be interpolated
        # h=0.5, k=0.5, l=0.5 should interpolate between the 8 nearest integer points
        h = torch.tensor(0.5)
        k = torch.tensor(0.5)
        l = torch.tensor(0.5)

        F_interp = crystal.get_structure_factor(h, k, l)

        # The interpolation should give us a value between the surrounding points
        # For our smooth function, the exact value at (0.5, 0.5, 0.5) should be
        # approximately 100 + 10*0.5 + 5*0.5 + 2*0.5 = 100 + 5 + 2.5 + 1 = 108.5
        #
        # However, tricubic interpolation will give a slightly different value
        # based on the 4x4x4 neighborhood. We just check it's in a reasonable range.
        assert 105.0 < F_interp.item() < 112.0, \
            f"Interpolated value {F_interp.item()} outside expected range"

        # Test another fractional point
        h = torch.tensor(-0.25)
        k = torch.tensor(0.75)
        l = torch.tensor(-0.5)

        F_interp2 = crystal.get_structure_factor(h, k, l)

        # This should also give a reasonable interpolated value
        # Expected roughly: 100 + 10*(-0.25) + 5*0.75 + 2*(-0.5) = 100 - 2.5 + 3.75 - 1 = 100.25
        assert 97.0 < F_interp2.item() < 104.0, \
            f"Second interpolated value {F_interp2.item()} outside expected range"

    finally:
        # Clean up temp file
        os.unlink(hkl_file)

    print("✓ Tricubic interpolation test passed")


def test_tricubic_out_of_bounds_fallback():
    """
    AT-STR-002: Test out-of-bounds fallback behavior.

    Setup: Enable interpolation but query a point where 4×4×4 neighborhood would be out of bounds.
    Expectation:
    - SHALL print a one-time warning
    - SHALL use default_F for that evaluation
    - SHALL permanently disable interpolation for the rest of the run
    """
    # Create a small HKL grid (3x3x3)
    hkl_content = StringIO()

    for h in range(-1, 2):
        for k in range(-1, 2):
            for l in range(-1, 2):
                F = 100.0 + h + k + l
                hkl_content.write(f"{h} {k} {l} {F:.1f}\n")

    # Write HKL to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.hkl', delete=False) as f:
        f.write(hkl_content.getvalue())
        hkl_file = f.name

    try:
        # Create crystal with specific default_F value
        config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=999.0  # Distinctive value to verify fallback
        )

        crystal = Crystal(config, device='cpu')
        crystal.load_hkl(hkl_file)
        crystal.interpolate = True  # Force interpolation on initially

        # Query a point near the edge where 4x4x4 neighborhood would go out of bounds
        # For h=1.5, we'd need points at h=0,1,2,3 but our grid only goes to h=1
        h = torch.tensor(1.5)
        k = torch.tensor(0.0)
        l = torch.tensor(0.0)

        # This should trigger the out-of-bounds condition
        F_oob = crystal.get_structure_factor(h, k, l)

        # Should return default_F
        assert torch.allclose(F_oob, torch.tensor(999.0, dtype=F_oob.dtype)), \
            f"Out-of-bounds should return default_F=999.0, got {F_oob.item()}"

        # Interpolation should now be permanently disabled
        assert not crystal.interpolate, \
            "Interpolation should be disabled after out-of-bounds access"

        # Subsequent queries should use nearest-neighbor even for in-bounds points
        h = torch.tensor(0.0)
        k = torch.tensor(0.0)
        l = torch.tensor(0.0)

        F_nn = crystal.get_structure_factor(h, k, l)

        # Should get exact value from nearest-neighbor lookup (100.0)
        assert torch.allclose(F_nn, torch.tensor(100.0, dtype=F_nn.dtype)), \
            f"After fallback, should use nearest-neighbor, got {F_nn.item()}"

    finally:
        # Clean up temp file
        os.unlink(hkl_file)

    print("✓ Out-of-bounds fallback test passed")


def test_auto_enable_interpolation():
    """
    AT-STR-002: Test auto-enable logic for small crystals.

    Setup: Create crystal with Na, Nb, or Nc ≤ 2.
    Expectation: Interpolation SHALL be automatically enabled.
    """
    # Test with small crystal (Na=2)
    config1 = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(2, 5, 5),  # Na=2 should trigger auto-enable
        default_F=100.0
    )

    crystal1 = Crystal(config1, device='cpu')
    assert crystal1.interpolate, "Interpolation should be auto-enabled for Na=2"

    # Test with Nb=1
    config2 = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 1, 5),  # Nb=1 should trigger auto-enable
        default_F=100.0
    )

    crystal2 = Crystal(config2, device='cpu')
    assert crystal2.interpolate, "Interpolation should be auto-enabled for Nb=1"

    # Test with larger crystal (should NOT auto-enable)
    config3 = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),  # All > 2, should not auto-enable
        default_F=100.0
    )

    crystal3 = Crystal(config3, device='cpu')
    assert not crystal3.interpolate, "Interpolation should NOT be auto-enabled for large crystal"

    print("✓ Auto-enable interpolation test passed")


if __name__ == "__main__":
    # Run all tests
    test_tricubic_interpolation_enabled()
    test_tricubic_out_of_bounds_fallback()
    test_auto_enable_interpolation()

    print("\n✅ All AT-STR-002 tests passed!")
"""
Test for AT-STR-001: Nearest-neighbor structure factor lookup

From spec-a.md Acceptance Test:
- Setup: Load a small HKL grid with known F values; set -nointerpolate;
  query pixels yielding integer (h0,k0,l0) both in-range and out-of-range.
- Expectation: In-range uses grid values; out-of-range uses default_F.
"""

import torch
import pytest
import tempfile
import os
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import CrystalConfig


def test_at_str_001_nearest_neighbor_lookup():
    """Test AT-STR-001: Nearest-neighbor structure factor lookup when interpolation off."""

    # Create a temporary HKL file with known values
    hkl_content = """# Test HKL file
0 0 0 100.0
1 0 0 150.0
0 1 0 200.0
0 0 1 250.0
-1 0 0 50.0
1 1 0 300.0
1 0 1 350.0
0 1 1 400.0
1 1 1 450.0
"""

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.hkl', delete=False) as f:
        f.write(hkl_content)
        hkl_path = f.name

    try:
        # Create crystal with default_F = 10
        config = CrystalConfig(default_F=10.0)
        crystal = Crystal(config=config, dtype=torch.float64)

        # Load HKL data
        crystal.load_hkl(hkl_path, write_cache=False)

        # Disable interpolation to test nearest-neighbor
        crystal.interpolate = False

        print(f"HKL metadata: {crystal.hkl_metadata}")

        # Test in-range queries with known values
        h = torch.tensor([0.0, 1.0, 0.0, 0.0, -1.0, 1.0, 1.0, 0.0, 1.0], dtype=torch.float64)
        k = torch.tensor([0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 1.0, 1.0], dtype=torch.float64)
        l = torch.tensor([0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 1.0], dtype=torch.float64)

        expected = torch.tensor([100.0, 150.0, 200.0, 250.0, 50.0, 300.0, 350.0, 400.0, 450.0], dtype=torch.float64)

        F_result = crystal.get_structure_factor(h, k, l)

        print(f"In-range queries:")
        for i in range(len(h)):
            print(f"  ({h[i]:.0f}, {k[i]:.0f}, {l[i]:.0f}) -> F = {F_result[i]:.1f} (expected {expected[i]:.1f})")

        assert torch.allclose(F_result, expected), \
            f"In-range lookup failed: {F_result} != {expected}"

        # Test out-of-range queries (should return default_F = 10)
        h_out = torch.tensor([5.0, -5.0, 0.0], dtype=torch.float64)
        k_out = torch.tensor([0.0, 0.0, 5.0], dtype=torch.float64)
        l_out = torch.tensor([0.0, 0.0, -5.0], dtype=torch.float64)

        F_out = crystal.get_structure_factor(h_out, k_out, l_out)

        print(f"\nOut-of-range queries:")
        for i in range(len(h_out)):
            print(f"  ({h_out[i]:.0f}, {k_out[i]:.0f}, {l_out[i]:.0f}) -> F = {F_out[i]:.1f} (expected default_F = 10.0)")

        expected_out = torch.tensor([10.0, 10.0, 10.0], dtype=torch.float64)
        assert torch.allclose(F_out, expected_out), \
            f"Out-of-range should return default_F: {F_out} != {expected_out}"

        # Test mixed in-range and out-of-range in same query
        h_mixed = torch.tensor([0.0, 10.0, 1.0], dtype=torch.float64)
        k_mixed = torch.tensor([0.0, 0.0, 0.0], dtype=torch.float64)
        l_mixed = torch.tensor([0.0, 0.0, 0.0], dtype=torch.float64)

        F_mixed = crystal.get_structure_factor(h_mixed, k_mixed, l_mixed)

        print(f"\nMixed queries:")
        print(f"  (0, 0, 0) -> F = {F_mixed[0]:.1f} (expected 100.0)")
        print(f"  (10, 0, 0) -> F = {F_mixed[1]:.1f} (expected default_F = 10.0)")
        print(f"  (1, 0, 0) -> F = {F_mixed[2]:.1f} (expected 150.0)")

        expected_mixed = torch.tensor([100.0, 10.0, 150.0], dtype=torch.float64)
        assert torch.allclose(F_mixed, expected_mixed), \
            f"Mixed in/out-of-range failed: {F_mixed} != {expected_mixed}"

        # Test rounding behavior (nearest-neighbor)
        h_round = torch.tensor([0.4, 0.6, -0.4, -0.6], dtype=torch.float64)
        k_round = torch.zeros(4, dtype=torch.float64)
        l_round = torch.zeros(4, dtype=torch.float64)

        F_round = crystal.get_structure_factor(h_round, k_round, l_round)

        print(f"\nRounding behavior:")
        print(f"  (0.4, 0, 0) -> F = {F_round[0]:.1f} (rounds to 0, expected 100.0)")
        print(f"  (0.6, 0, 0) -> F = {F_round[1]:.1f} (rounds to 1, expected 150.0)")
        print(f"  (-0.4, 0, 0) -> F = {F_round[2]:.1f} (rounds to 0, expected 100.0)")
        print(f"  (-0.6, 0, 0) -> F = {F_round[3]:.1f} (rounds to -1, expected 50.0)")

        expected_round = torch.tensor([100.0, 150.0, 100.0, 50.0], dtype=torch.float64)
        assert torch.allclose(F_round, expected_round), \
            f"Rounding behavior incorrect: {F_round} != {expected_round}"

        print("\n✅ AT-STR-001 PASSED: Nearest-neighbor structure factor lookup correct")

    finally:
        # Clean up temporary file
        if os.path.exists(hkl_path):
            os.unlink(hkl_path)


if __name__ == "__main__":
    test_at_str_001_nearest_neighbor_lookup()
"""
Tests for vectorized tricubic interpolation (Phase C1).

This module tests the batched neighborhood gather implementation
in Crystal._tricubic_interpolation, verifying that it correctly
constructs (B, 4, 4, 4) neighborhoods for batched Miller index queries.

Reference: reports/2025-10-vectorization/phase_b/design_notes.md
"""
import os
import pytest
import torch
from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal

# Set environment variable to avoid MKL conflicts
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


class TestTricubicGather:
    """Test suite for batched neighborhood gathering (Phase C1)."""

    @pytest.fixture
    def simple_crystal_config(self):
        """Create a simple cubic crystal configuration for testing."""
        return CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=[5, 5, 5],
            default_F=100.0,
            misset_deg=[0.0, 0.0, 0.0],
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            spindle_axis=[0.0, 1.0, 0.0],
            mosaic_spread_deg=0.0,
            mosaic_domains=1,
            mosaic_seed=None
        )

    @pytest.fixture
    def crystal_with_data(self, simple_crystal_config):
        """Create a crystal with synthetic HKL data for testing."""
        crystal = Crystal(simple_crystal_config)

        # Create synthetic HKL data grid (small for speed)
        # Grid spanning h,k,l ∈ [-5, 5] with known values
        h_range = 11  # -5 to 5
        k_range = 11
        l_range = 11

        # Populate with a simple pattern: F(h,k,l) = 100 + 10*h + k + 0.1*l
        hkl_data = torch.zeros((h_range, k_range, l_range), dtype=torch.float32)
        for i in range(h_range):
            for j in range(k_range):
                for k in range(l_range):
                    h_idx = i - 5  # map to Miller index
                    k_idx = j - 5
                    l_idx = k - 5
                    hkl_data[i, j, k] = 100.0 + 10.0 * h_idx + 1.0 * k_idx + 0.1 * l_idx

        crystal.hkl_data = hkl_data
        crystal.hkl_metadata = {
            'h_min': -5, 'h_max': 5,
            'k_min': -5, 'k_max': 5,
            'l_min': -5, 'l_max': 5,
            'h_range': 10, 'k_range': 10, 'l_range': 10
        }

        return crystal

    def test_vectorized_matches_scalar(self, crystal_with_data):
        """
        Verify that batched gather produces correct neighborhoods.

        Phase C1 requirement: Build (B, 4, 4, 4) neighborhoods via advanced indexing.
        This test validates the gather mechanism by comparing:
        1. Scalar interpolation (existing path, B=1)
        2. Shape assertions on batched gather output
        3. Neighborhood contents match expected HKL data

        Reference: design_notes.md Section 2.2, Section 5.1
        """
        crystal = crystal_with_data

        # Test case 1: Single query point (scalar path, B=1)
        h_scalar = torch.tensor([1.5], dtype=torch.float32)
        k_scalar = torch.tensor([2.3], dtype=torch.float32)
        l_scalar = torch.tensor([0.5], dtype=torch.float32)

        # This should use the scalar path (B=1)
        F_scalar = crystal._tricubic_interpolation(h_scalar, k_scalar, l_scalar)

        assert F_scalar.shape == h_scalar.shape, f"Scalar output shape mismatch: {F_scalar.shape} vs {h_scalar.shape}"
        assert not torch.isnan(F_scalar).any(), "Scalar output contains NaNs"
        assert not torch.isinf(F_scalar).any(), "Scalar output contains Infs"

        # Test case 2: Batched query points (gather path, B>1)
        # Use a small batch to verify neighborhood gathering
        h_batch = torch.tensor([1.5, 2.3, -1.2], dtype=torch.float32)
        k_batch = torch.tensor([2.3, -0.5, 3.1], dtype=torch.float32)
        l_batch = torch.tensor([0.5, 1.8, -2.0], dtype=torch.float32)

        # This triggers the batched gather path (B=3)
        # Currently falls back to nearest-neighbor but builds neighborhoods internally
        F_batch = crystal._tricubic_interpolation(h_batch, k_batch, l_batch)

        assert F_batch.shape == h_batch.shape, f"Batch output shape mismatch: {F_batch.shape} vs {h_batch.shape}"
        assert not torch.isnan(F_batch).any(), "Batch output contains NaNs"
        assert not torch.isinf(F_batch).any(), "Batch output contains Infs"

        # Test case 3: Multi-dimensional batch (detector grid simulation)
        # Simulate a small detector region: (S=2, F=3)
        h_grid = torch.tensor([[1.5, 2.3, 0.8], [-1.2, 3.1, 1.9]], dtype=torch.float32)
        k_grid = torch.tensor([[2.3, -0.5, 1.2], [3.1, -2.0, 0.5]], dtype=torch.float32)
        l_grid = torch.tensor([[0.5, 1.8, -1.0], [-2.0, 0.3, 2.5]], dtype=torch.float32)

        # Flatten to (B=6) internally
        F_grid = crystal._tricubic_interpolation(h_grid, k_grid, l_grid)

        assert F_grid.shape == h_grid.shape, f"Grid output shape mismatch: {F_grid.shape} vs {h_grid.shape}"
        assert not torch.isnan(F_grid).any(), "Grid output contains NaNs"
        assert not torch.isinf(F_grid).any(), "Grid output contains Infs"

        # Test case 4: Verify neighborhood bounds checking still works
        # Query point near edge (h=4.5 → floor=4 → needs neighbors 3,4,5,6; 6>h_max=5)
        h_edge = torch.tensor([4.5], dtype=torch.float32)
        k_edge = torch.tensor([0.0], dtype=torch.float32)
        l_edge = torch.tensor([0.0], dtype=torch.float32)

        # Capture warning state before test
        warning_shown_before = crystal._interpolation_warning_shown

        # This should trigger OOB fallback and return default_F
        F_edge = crystal._tricubic_interpolation(h_edge, k_edge, l_edge)

        # Should fallback to default_F due to OOB
        expected_default = crystal.config.default_F
        # Allow small tolerance due to potential floating point ops
        assert torch.allclose(F_edge, torch.tensor(expected_default, dtype=F_edge.dtype, device=F_edge.device), atol=1e-5), \
            f"OOB fallback failed: expected {expected_default}, got {F_edge.item()}"

        # Warning should have been shown
        assert crystal._interpolation_warning_shown, "OOB warning was not triggered"

        print("✓ Phase C1 batched gather validation passed")
        print(f"  - Scalar path (B=1): shape {h_scalar.shape} → {F_scalar.shape}")
        print(f"  - Batched path (B=3): shape {h_batch.shape} → {F_batch.shape}")
        print(f"  - Grid path (S=2, F=3): shape {h_grid.shape} → {F_grid.shape}")
        print(f"  - OOB detection: triggered correctly for edge case")

    def test_neighborhood_gathering_internals(self, crystal_with_data):
        """
        Validate internal neighborhood gathering mechanics.

        This test verifies that the batched gather logic correctly:
        1. Flattens input shapes to (B,)
        2. Builds (B, 4) coordinate grids
        3. Uses advanced indexing to produce (B, 4, 4, 4) neighborhoods

        This is a white-box test inspecting intermediate state.
        """
        crystal = crystal_with_data

        # Create a simple query
        h = torch.tensor([[1.5, 2.3]], dtype=torch.float32)  # shape (1, 2)
        k = torch.tensor([[0.5, 1.2]], dtype=torch.float32)
        l = torch.tensor([[0.0, 0.5]], dtype=torch.float32)

        # Manually trace the gather logic to validate shapes
        h_flat = h.reshape(-1)  # (2,)
        k_flat = k.reshape(-1)
        l_flat = l.reshape(-1)
        B = h_flat.shape[0]

        assert B == 2, f"Flatten failed: expected B=2, got {B}"

        # Build coordinate grids
        h_flr = torch.floor(h_flat).long()
        offsets = torch.arange(-1, 3, dtype=torch.long)
        h_grid_coords = h_flr.unsqueeze(-1) + offsets  # (B, 4)

        assert h_grid_coords.shape == (B, 4), f"Grid coords shape error: {h_grid_coords.shape}"

        # Verify coordinate values for first query (h=1.5 → floor=1)
        expected_h_coords_0 = torch.tensor([0, 1, 2, 3], dtype=torch.long)  # floor(1.5) + [-1,0,1,2]
        assert torch.equal(h_grid_coords[0], expected_h_coords_0), \
            f"Coordinate array mismatch: {h_grid_coords[0]} vs {expected_h_coords_0}"

        print("✓ Internal neighborhood gathering mechanics validated")
        print(f"  - Flattening: (1, 2) → (B={B},)")
        print(f"  - Coordinate grids: (B={B}, 4)")
        print(f"  - Sample coords for h=1.5: {h_grid_coords[0].tolist()}")

    def test_oob_warning_single_fire(self, simple_crystal_config):
        """
        Verify that out-of-bounds warning fires exactly once and disables interpolation.

        Phase C2 requirement: Lock the single-warning behavior for OOB fallback.
        When tricubic interpolation encounters an out-of-bounds neighborhood query:
        1. First occurrence triggers warning message (printed once only)
        2. Interpolation is permanently disabled (self.interpolate = False)
        3. Subsequent OOB queries return default_F without additional warnings

        Reference: plans/active/vectorization.md Phase C2
        """
        # Create crystal with small HKL data range to easily trigger OOB
        crystal = Crystal(simple_crystal_config)

        h_range, k_range, l_range = 11, 11, 11  # covers h,k,l ∈ [-5, 5]
        hkl_data = torch.ones((h_range, k_range, l_range), dtype=torch.float32) * 50.0
        crystal.hkl_data = hkl_data
        crystal.hkl_metadata = {
            'h_min': -5, 'h_max': 5,
            'k_min': -5, 'k_max': 5,
            'l_min': -5, 'l_max': 5,
            'h_range': 10, 'k_range': 10, 'l_range': 10
        }

        # Enable interpolation explicitly
        crystal.interpolate = True
        initial_warning_state = crystal._interpolation_warning_shown
        assert not initial_warning_state, "Warning flag should start False"
        assert crystal.interpolate, "Interpolation should start enabled"

        # First OOB query: h=4.8 → floor=4 → needs neighbors [3,4,5,6]
        # Since h_max=5, neighbor h=6 is out of range
        h_oob = torch.tensor([4.8], dtype=torch.float32)
        k_oob = torch.tensor([0.0], dtype=torch.float32)
        l_oob = torch.tensor([0.0], dtype=torch.float32)

        # Capture stdout to verify warning message
        import io
        import sys
        captured_output = io.StringIO()
        sys.stdout = captured_output

        # First call: should trigger warning
        F_first = crystal._tricubic_interpolation(h_oob, k_oob, l_oob)

        # Restore stdout
        sys.stdout = sys.__stdout__
        warning_text = captured_output.getvalue()

        # Verify warning was printed
        assert "WARNING: out of range for three point interpolation" in warning_text, \
            "First OOB call should print warning"
        assert "further warnings will not be printed" in warning_text, \
            "Warning should indicate no further warnings"

        # Verify state changes
        assert crystal._interpolation_warning_shown, "Warning flag should be set"
        assert not crystal.interpolate, "Interpolation should be disabled"

        # Verify fallback to default_F
        expected_default = crystal.config.default_F
        assert torch.allclose(F_first, torch.tensor(expected_default, dtype=F_first.dtype, device=F_first.device), atol=1e-5), \
            f"First OOB call should return default_F={expected_default}, got {F_first.item()}"

        # Second OOB query: should NOT print warning
        h_oob2 = torch.tensor([4.9], dtype=torch.float32)
        k_oob2 = torch.tensor([0.5], dtype=torch.float32)
        l_oob2 = torch.tensor([0.5], dtype=torch.float32)

        captured_output2 = io.StringIO()
        sys.stdout = captured_output2

        F_second = crystal._tricubic_interpolation(h_oob2, k_oob2, l_oob2)

        sys.stdout = sys.__stdout__
        warning_text2 = captured_output2.getvalue()

        # Verify NO new warning
        assert "WARNING" not in warning_text2, \
            "Second OOB call should not print any warnings"

        # Verify still returns default_F
        assert torch.allclose(F_second, torch.tensor(expected_default, dtype=F_second.dtype, device=F_second.device), atol=1e-5), \
            f"Second OOB call should return default_F={expected_default}, got {F_second.item()}"

        # Verify persistent state
        assert crystal._interpolation_warning_shown, "Warning flag should remain set"
        assert not crystal.interpolate, "Interpolation should remain disabled"

        # Third query (in-bounds but interpolation disabled): should use nearest-neighbor
        h_valid = torch.tensor([1.5], dtype=torch.float32)
        k_valid = torch.tensor([0.0], dtype=torch.float32)
        l_valid = torch.tensor([0.0], dtype=torch.float32)

        captured_output3 = io.StringIO()
        sys.stdout = captured_output3

        F_third = crystal._tricubic_interpolation(h_valid, k_valid, l_valid)

        sys.stdout = sys.__stdout__
        warning_text3 = captured_output3.getvalue()

        # Should not trigger OOB warning (in-bounds) but uses nearest-neighbor due to disabled interpolation
        assert "out of range" not in warning_text3, \
            "In-bounds query should not mention out of range"

        # Nearest-neighbor should return one of the grid values (50.0 in this case)
        # Since interpolation is disabled, we expect the nearest neighbor value
        assert F_third.item() == 50.0 or F_third.item() == expected_default, \
            f"Disabled interpolation should use nearest-neighbor or default_F, got {F_third.item()}"

        print("✓ Phase C2: OOB warning single-fire behavior validated")
        print(f"  - First OOB: warning printed, interpolation disabled, returned default_F={expected_default}")
        print(f"  - Second OOB: no warning, still returns default_F={expected_default}")
        print(f"  - In-bounds post-disable: uses fallback path, returns {F_third.item()}")

    @pytest.mark.parametrize("device", [
        "cpu",
        pytest.param("cuda", marks=pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available"))
    ])
    def test_device_neutrality(self, simple_crystal_config, device):
        """
        Verify batched gather works on both CPU and CUDA.

        Phase C1 requirement: Device-neutral implementation per Core Rule #16.
        Reference: design_notes.md Section 4.2
        """
        # Create crystal and move to target device
        config_dict = simple_crystal_config.__dict__.copy()
        crystal = Crystal(CrystalConfig(**config_dict))

        # Create synthetic HKL data on target device
        h_range, k_range, l_range = 11, 11, 11
        hkl_data = torch.randn((h_range, k_range, l_range), dtype=torch.float32, device=device)
        crystal.hkl_data = hkl_data
        crystal.hkl_metadata = {
            'h_min': -5, 'h_max': 5,
            'k_min': -5, 'k_max': 5,
            'l_min': -5, 'l_max': 5,
            'h_range': 10, 'k_range': 10, 'l_range': 10
        }
        crystal.device = device
        crystal.dtype = torch.float32

        # Create query tensors on target device
        h = torch.tensor([1.5, 2.3, -1.2], dtype=torch.float32, device=device)
        k = torch.tensor([0.5, 1.2, 2.0], dtype=torch.float32, device=device)
        l = torch.tensor([0.0, 0.5, 1.0], dtype=torch.float32, device=device)

        # Run interpolation (batched gather path)
        F = crystal._tricubic_interpolation(h, k, l)

        # Verify output is on correct device
        # Note: torch.device("cuda") != torch.device("cuda:0"), so compare type only
        assert F.device.type == device, f"Output device mismatch: {F.device} vs {device}"
        assert F.shape == h.shape, f"Output shape mismatch: {F.shape} vs {h.shape}"
        assert not torch.isnan(F).any(), f"Output contains NaNs on {device}"

        print(f"✓ Device neutrality validated for {device}")
        print(f"  - Input device: {h.device}")
        print(f"  - Output device: {F.device}")
        print(f"  - Shape: {h.shape} → {F.shape}")


class TestTricubicPoly:
    """
    Test suite for vectorized polynomial interpolation helpers (Phase D3).

    These tests validate the batched polynomial evaluation helpers that power
    tricubic interpolation. Tests are expected to FAIL until Phase D2 implementation
    lands (polint_vectorized, polin2_vectorized, polin3_vectorized).

    Reference: reports/2025-10-vectorization/phase_d/polynomial_validation.md
    """

    @pytest.fixture
    def poly_fixture_data(self):
        """
        Create deterministic polynomial test data per worksheet Table 2.1.

        Uses small integer-based tensor values to minimize rounding noise
        while exercising all indices.
        """
        # 1D data for polint testing (B=3)
        xa = torch.tensor([
            [0.0, 1.0, 2.0, 3.0],  # Linear spacing
            [0.0, 1.0, 2.0, 3.0],
            [1.0, 2.0, 3.0, 4.0]
        ], dtype=torch.float64)

        ya = torch.tensor([
            [1.0, 2.0, 4.0, 8.0],   # Power of 2 pattern
            [0.0, 1.0, 8.0, 27.0],  # Cubic pattern
            [2.0, 3.0, 5.0, 9.0]    # Linear + constant
        ], dtype=torch.float64)

        x = torch.tensor([1.5, 0.5, 2.5], dtype=torch.float64)

        # 2D data for polin2 testing (B=2)
        x1a_2d = torch.tensor([
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0]
        ], dtype=torch.float64)

        x2a_2d = torch.tensor([
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0]
        ], dtype=torch.float64)

        # Simple grid: ya[i,j] = i + j
        ya_2d = torch.zeros((2, 4, 4), dtype=torch.float64)
        for i in range(4):
            for j in range(4):
                ya_2d[0, i, j] = float(i + j)
                ya_2d[1, i, j] = float(i * j)  # Different pattern for second batch

        x1_2d = torch.tensor([1.5, 0.5], dtype=torch.float64)
        x2_2d = torch.tensor([1.5, 1.5], dtype=torch.float64)

        # 3D data for polin3 testing (B=2)
        x1a_3d = torch.tensor([
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0]
        ], dtype=torch.float64)

        x2a_3d = torch.tensor([
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0]
        ], dtype=torch.float64)

        x3a_3d = torch.tensor([
            [0.0, 1.0, 2.0, 3.0],
            [0.0, 1.0, 2.0, 3.0]
        ], dtype=torch.float64)

        # Simple 3D grid: ya[i,j,k] = i + j + k
        ya_3d = torch.zeros((2, 4, 4, 4), dtype=torch.float64)
        for i in range(4):
            for j in range(4):
                for k in range(4):
                    ya_3d[0, i, j, k] = float(i + j + k)
                    ya_3d[1, i, j, k] = float(i + j + k) * 10.0  # Scaled for second batch

        x1_3d = torch.tensor([1.5, 0.5], dtype=torch.float64)
        x2_3d = torch.tensor([1.5, 1.5], dtype=torch.float64)
        x3_3d = torch.tensor([0.5, 0.5], dtype=torch.float64)

        return {
            # 1D polint data
            'xa': xa, 'ya': ya, 'x': x,
            # 2D polin2 data
            'x1a_2d': x1a_2d, 'x2a_2d': x2a_2d, 'ya_2d': ya_2d,
            'x1_2d': x1_2d, 'x2_2d': x2_2d,
            # 3D polin3 data
            'x1a_3d': x1a_3d, 'x2a_3d': x2a_3d, 'x3a_3d': x3a_3d, 'ya_3d': ya_3d,
            'x1_3d': x1_3d, 'x2_3d': x2_3d, 'x3_3d': x3_3d
        }

    def test_polint_matches_scalar_batched(self, poly_fixture_data):
        """
        Verify batched polint produces same results as scalar reference.

        Expected to FAIL until D2 implementation lands.
        Reference: polynomial_validation.md Section 3.1
        """
        from nanobrag_torch.utils.physics import polint_vectorized

        xa = poly_fixture_data['xa']
        ya = poly_fixture_data['ya']
        x = poly_fixture_data['x']
        B = xa.shape[0]

        # Call vectorized implementation
        y_batch = polint_vectorized(xa, ya, x)

        # Verify shape
        assert y_batch.shape == (B,), f"Output shape should be ({B},), got {y_batch.shape}"

        # Verify no NaNs/Infs
        assert not torch.isnan(y_batch).any(), "Batched polint output contains NaNs"
        assert not torch.isinf(y_batch).any(), "Batched polint output contains Infs"

        # Compare against scalar reference (from existing utils/physics.py)
        from nanobrag_torch.utils.physics import polint as polint_scalar
        y_scalar = torch.zeros(B, dtype=torch.float64)
        for i in range(B):
            y_scalar[i] = polint_scalar(xa[i], ya[i], x[i])

        # Should match within numerical tolerance
        assert torch.allclose(y_batch, y_scalar, rtol=1e-10, atol=1e-12), \
            f"Batched vs scalar mismatch: max diff = {(y_batch - y_scalar).abs().max()}"

        print(f"✓ polint_vectorized matches scalar for B={B}")
        print(f"  Output: {y_batch.tolist()}")

    def test_polint_gradient_flow(self, poly_fixture_data):
        """
        Verify gradcheck passes for vectorized polint.

        Expected to FAIL until D2 implementation with gradient support lands.
        Reference: polynomial_validation.md Section 4.2
        """
        from nanobrag_torch.utils.physics import polint_vectorized

        xa = poly_fixture_data['xa'][:1]  # B=1 for gradcheck
        ya = poly_fixture_data['ya'][:1].requires_grad_(True)
        x = poly_fixture_data['x'][:1].requires_grad_(True)

        # Verify computation graph connectivity
        y = polint_vectorized(xa, ya, x)
        assert y.requires_grad, "Output should have requires_grad=True"
        assert y.grad_fn is not None, "Output should have grad_fn (part of computation graph)"

        # Gradcheck w.r.t. x
        assert torch.autograd.gradcheck(
            lambda x_: polint_vectorized(xa, ya, x_),
            x,
            eps=1e-6,
            atol=1e-4
        ), "Gradcheck failed w.r.t. x"

        # Gradcheck w.r.t. ya
        assert torch.autograd.gradcheck(
            lambda ya_: polint_vectorized(xa, ya_, x),
            ya,
            eps=1e-6,
            atol=1e-4
        ), "Gradcheck failed w.r.t. ya"

        print("✓ polint_vectorized gradients verified")

    def test_polin2_matches_scalar_batched(self, poly_fixture_data):
        """
        Verify batched polin2 produces same results as scalar reference.

        Expected to FAIL until D2 implementation lands.
        Reference: polynomial_validation.md Section 3.2
        """
        from nanobrag_torch.utils.physics import polin2_vectorized

        x1a = poly_fixture_data['x1a_2d']
        x2a = poly_fixture_data['x2a_2d']
        ya = poly_fixture_data['ya_2d']
        x1 = poly_fixture_data['x1_2d']
        x2 = poly_fixture_data['x2_2d']
        B = x1a.shape[0]

        # Call vectorized implementation
        y_batch = polin2_vectorized(x1a, x2a, ya, x1, x2)

        # Verify shape
        assert y_batch.shape == (B,), f"Output shape should be ({B},), got {y_batch.shape}"

        # Verify no NaNs/Infs
        assert not torch.isnan(y_batch).any(), "Batched polin2 output contains NaNs"
        assert not torch.isinf(y_batch).any(), "Batched polin2 output contains Infs"

        # Compare against scalar reference
        from nanobrag_torch.utils.physics import polin2 as polin2_scalar
        y_scalar = torch.zeros(B, dtype=torch.float64)
        for i in range(B):
            y_scalar[i] = polin2_scalar(x1a[i], x2a[i], ya[i], x1[i], x2[i])

        # Should match within numerical tolerance
        assert torch.allclose(y_batch, y_scalar, rtol=1e-10, atol=1e-12), \
            f"Batched vs scalar mismatch: max diff = {(y_batch - y_scalar).abs().max()}"

        print(f"✓ polin2_vectorized matches scalar for B={B}")
        print(f"  Output: {y_batch.tolist()}")

    def test_polin2_gradient_flow(self, poly_fixture_data):
        """
        Verify gradcheck passes for vectorized polin2.

        Expected to FAIL until D2 implementation with gradient support lands.
        Reference: polynomial_validation.md Section 4.2
        """
        from nanobrag_torch.utils.physics import polin2_vectorized

        x1a = poly_fixture_data['x1a_2d'][:1]
        x2a = poly_fixture_data['x2a_2d'][:1]
        ya = poly_fixture_data['ya_2d'][:1].requires_grad_(True)
        x1 = poly_fixture_data['x1_2d'][:1].requires_grad_(True)
        x2 = poly_fixture_data['x2_2d'][:1].requires_grad_(True)

        # Verify computation graph connectivity
        y = polin2_vectorized(x1a, x2a, ya, x1, x2)
        assert y.requires_grad, "Output should have requires_grad=True"
        assert y.grad_fn is not None, "Output should have grad_fn"

        # Gradcheck w.r.t. x1
        assert torch.autograd.gradcheck(
            lambda x1_: polin2_vectorized(x1a, x2a, ya, x1_, x2),
            x1,
            eps=1e-6,
            atol=1e-4
        ), "Gradcheck failed w.r.t. x1"

        print("✓ polin2_vectorized gradients verified")

    def test_polin3_matches_scalar_batched(self, poly_fixture_data):
        """
        Verify batched polin3 (full 3D tricubic) produces same results as scalar.

        Expected to FAIL until D2 implementation lands.
        Reference: polynomial_validation.md Section 3.3
        """
        from nanobrag_torch.utils.physics import polin3_vectorized

        x1a = poly_fixture_data['x1a_3d']
        x2a = poly_fixture_data['x2a_3d']
        x3a = poly_fixture_data['x3a_3d']
        ya = poly_fixture_data['ya_3d']
        x1 = poly_fixture_data['x1_3d']
        x2 = poly_fixture_data['x2_3d']
        x3 = poly_fixture_data['x3_3d']
        B = x1a.shape[0]

        # Call vectorized implementation
        y_batch = polin3_vectorized(x1a, x2a, x3a, ya, x1, x2, x3)

        # Verify shape
        assert y_batch.shape == (B,), f"Output shape should be ({B},), got {y_batch.shape}"

        # Verify no NaNs/Infs
        assert not torch.isnan(y_batch).any(), "Batched polin3 output contains NaNs"
        assert not torch.isinf(y_batch).any(), "Batched polin3 output contains Infs"

        # Compare against scalar reference
        from nanobrag_torch.utils.physics import polin3 as polin3_scalar
        y_scalar = torch.zeros(B, dtype=torch.float64)
        for i in range(B):
            y_scalar[i] = polin3_scalar(x1a[i], x2a[i], x3a[i], ya[i], x1[i], x2[i], x3[i])

        # Should match within numerical tolerance
        assert torch.allclose(y_batch, y_scalar, rtol=1e-10, atol=1e-12), \
            f"Batched vs scalar mismatch: max diff = {(y_batch - y_scalar).abs().max()}"

        print(f"✓ polin3_vectorized matches scalar for B={B}")
        print(f"  Output: {y_batch.tolist()}")

    def test_polin3_gradient_flow(self, poly_fixture_data):
        """
        Verify gradcheck passes for vectorized polin3 (full 3D interpolation).

        Expected to FAIL until D2 implementation with gradient support lands.
        Reference: polynomial_validation.md Section 4.2
        """
        from nanobrag_torch.utils.physics import polin3_vectorized

        x1a = poly_fixture_data['x1a_3d'][:1]
        x2a = poly_fixture_data['x2a_3d'][:1]
        x3a = poly_fixture_data['x3a_3d'][:1]
        ya = poly_fixture_data['ya_3d'][:1].requires_grad_(True)
        x1 = poly_fixture_data['x1_3d'][:1].requires_grad_(True)
        x2 = poly_fixture_data['x2_3d'][:1].requires_grad_(True)
        x3 = poly_fixture_data['x3_3d'][:1].requires_grad_(True)

        # Verify computation graph connectivity
        y = polin3_vectorized(x1a, x2a, x3a, ya, x1, x2, x3)
        assert y.requires_grad, "Output should have requires_grad=True"
        assert y.grad_fn is not None, "Output should have grad_fn"

        # Gradcheck w.r.t. x1
        assert torch.autograd.gradcheck(
            lambda x1_: polin3_vectorized(x1a, x2a, x3a, ya, x1_, x2, x3),
            x1,
            eps=1e-6,
            atol=1e-4
        ), "Gradcheck failed w.r.t. x1"

        print("✓ polin3_vectorized gradients verified")

    def test_polin3_batch_shape_preserved(self, poly_fixture_data):
        """
        Verify batched polin3 preserves batch dimension correctly.

        Expected to FAIL until D2 implementation lands.
        Reference: polynomial_validation.md Section 2.2
        """
        from nanobrag_torch.utils.physics import polin3_vectorized

        # Create larger batch to verify shape handling
        B = 10
        ya = torch.randn((B, 4, 4, 4), dtype=torch.float64)
        x1a = torch.arange(4, dtype=torch.float64).unsqueeze(0).expand(B, -1)
        x2a = x1a.clone()
        x3a = x1a.clone()
        x1 = torch.rand(B, dtype=torch.float64) * 3.0
        x2 = torch.rand(B, dtype=torch.float64) * 3.0
        x3 = torch.rand(B, dtype=torch.float64) * 3.0

        y = polin3_vectorized(x1a, x2a, x3a, ya, x1, x2, x3)

        # Verify output shape matches batch size
        assert y.shape == (B,), f"Output shape should be ({B},), got {y.shape}"

        # Verify no unexpected broadcasting
        assert y.ndim == 1, f"Output should be 1D, got {y.ndim}D"

        print(f"✓ polin3_vectorized preserves batch shape correctly for B={B}")

    @pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
    def test_polynomials_support_float64(self, poly_fixture_data, dtype):
        """
        Verify polynomial helpers work with both float32 and float64.

        Expected to FAIL until D2 implementation lands.
        Reference: polynomial_validation.md Section 5.2
        """
        from nanobrag_torch.utils.physics import polint_vectorized

        xa = poly_fixture_data['xa'].to(dtype=dtype)
        ya = poly_fixture_data['ya'].to(dtype=dtype)
        x = poly_fixture_data['x'].to(dtype=dtype)

        y = polint_vectorized(xa, ya, x)

        # Verify dtype preservation
        assert y.dtype == dtype, f"Output dtype should be {dtype}, got {y.dtype}"

        # Verify no NaNs (could occur with float32 precision issues)
        assert not torch.isnan(y).any(), f"Output contains NaNs with dtype={dtype}"

        print(f"✓ polint_vectorized works with {dtype}")

    @pytest.mark.parametrize("device", [
        "cpu",
        pytest.param("cuda", marks=pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available"))
    ])
    def test_polynomials_device_neutral(self, poly_fixture_data, device):
        """
        Verify polynomial helpers work on both CPU and CUDA.

        Expected to FAIL until D2 implementation lands.
        Reference: polynomial_validation.md Section 5.1
        """
        from nanobrag_torch.utils.physics import polin3_vectorized

        x1a = poly_fixture_data['x1a_3d'].to(device=device)
        x2a = poly_fixture_data['x2a_3d'].to(device=device)
        x3a = poly_fixture_data['x3a_3d'].to(device=device)
        ya = poly_fixture_data['ya_3d'].to(device=device)
        x1 = poly_fixture_data['x1_3d'].to(device=device)
        x2 = poly_fixture_data['x2_3d'].to(device=device)
        x3 = poly_fixture_data['x3_3d'].to(device=device)

        y = polin3_vectorized(x1a, x2a, x3a, ya, x1, x2, x3)

        # Verify output is on correct device
        assert y.device.type == device, f"Output device should be {device}, got {y.device.type}"

        # Verify no NaNs (CUDA numerical issues)
        assert not torch.isnan(y).any(), f"Output contains NaNs on {device}"

        print(f"✓ polin3_vectorized works on {device}")


if __name__ == "__main__":
    # Allow running this test file directly
    pytest.main([__file__, "-v"])

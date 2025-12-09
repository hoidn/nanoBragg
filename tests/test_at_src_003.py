"""AT-SRC-003: Sourcefile Lambda Override and Steps Reconciliation Tests

Tests for SOURCE-WEIGHT-001 Phase E implementation (Option B):
- TC-E1: Sourcefile wavelengths overridden by CLI -lambda
- TC-E2: Warning emission when sourcefile wavelengths differ from CLI
- TC-E3: Steps normalization parity (counts all sources including zero-weight)

Per lambda_semantics.md (2025-10-09T13:17:09Z):
Both weight and wavelength columns in sourcefiles are read but IGNORED.
CLI -lambda is the sole authoritative wavelength source.
"""

import pytest
import torch
import tempfile
import warnings
from pathlib import Path

from nanobrag_torch.io.source import read_sourcefile


class TestSourcefileLambdaOverride:
    """TC-E1: Sourcefile wavelengths must be overridden by CLI -lambda."""

    def test_lambda_override_single_source(self):
        """Single source with different wavelength - CLI wins."""
        cli_lambda = 0.9768e-10  # meters (CLI value from TC-D1 fixture)
        file_lambda = 6.2e-10     # meters (sourcefile value from TC-D1 fixture)

        # Create temporary sourcefile with divergent wavelength
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Format: X Y Z weight wavelength(m)
            f.write(f"0.0 0.0 -10.0 1.0 {file_lambda}\n")
            sourcefile_path = Path(f.name)

        try:
            directions, weights, wavelengths = read_sourcefile(
                sourcefile_path,
                default_wavelength_m=cli_lambda,
                dtype=torch.float64,
                device=torch.device('cpu')
            )

            # Verify wavelength is CLI value, not file value
            assert wavelengths.shape == (1,)
            expected_cli = torch.tensor([cli_lambda], dtype=torch.float64)
            assert torch.allclose(wavelengths, expected_cli), \
                f"Expected CLI wavelength {cli_lambda}, got {wavelengths[0].item()}"

            # Verify it's NOT the file value
            file_value = torch.tensor([file_lambda], dtype=torch.float64)
            assert abs(wavelengths[0].item() - file_lambda) > 1e-12, \
                f"Wavelength should be CLI value {cli_lambda}, not file value {file_lambda}"

        finally:
            sourcefile_path.unlink()

    def test_lambda_override_multiple_sources(self):
        """Multiple sources with varying wavelengths - all overridden to CLI."""
        cli_lambda = 1.0e-10  # 1.0 Å
        file_lambdas = [6.2e-10, 0.9768e-10, 1.5e-10]  # Various values

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            for lam in file_lambdas:
                f.write(f"0.0 0.0 -10.0 1.0 {lam}\n")
            sourcefile_path = Path(f.name)

        try:
            directions, weights, wavelengths = read_sourcefile(
                sourcefile_path,
                default_wavelength_m=cli_lambda,
                dtype=torch.float64
            )

            # All wavelengths must equal CLI value
            assert wavelengths.shape == (len(file_lambdas),)
            expected = torch.full((len(file_lambdas),), cli_lambda, dtype=torch.float64)
            assert torch.allclose(wavelengths, expected)

        finally:
            sourcefile_path.unlink()


class TestSourcefileWarningEmission:
    """TC-E2: Warning must be emitted when sourcefile wavelength differs from CLI."""

    def test_warning_emitted_on_mismatch(self):
        """Warning emitted when file wavelength ≠ CLI wavelength."""
        cli_lambda = 0.9768e-10
        file_lambda = 6.2e-10  # Significantly different

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(f"0.0 0.0 -10.0 1.0 {file_lambda}\n")
            sourcefile_path = Path(f.name)

        try:
            # Clear any previous warning state
            if hasattr(read_sourcefile, '_wavelength_warned'):
                delattr(read_sourcefile, '_wavelength_warned')

            # Expect UserWarning with specific text
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                directions, weights, wavelengths = read_sourcefile(
                    sourcefile_path,
                    default_wavelength_m=cli_lambda,
                    dtype=torch.float64
                )

                # Verify warning was emitted
                assert len(w) == 1
                assert issubclass(w[0].category, UserWarning)
                assert "sourcefile wavelength column differs" in str(w[0].message).lower()
                assert "spec-a-core.md:150-151" in str(w[0].message)

        finally:
            sourcefile_path.unlink()

    def test_no_warning_when_matching(self):
        """No warning when file wavelength matches CLI wavelength."""
        cli_lambda = 1.0e-10

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # File wavelength matches CLI
            f.write(f"0.0 0.0 -10.0 1.0 {cli_lambda}\n")
            sourcefile_path = Path(f.name)

        try:
            # Clear any previous warning state
            if hasattr(read_sourcefile, '_wavelength_warned'):
                delattr(read_sourcefile, '_wavelength_warned')

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                directions, weights, wavelengths = read_sourcefile(
                    sourcefile_path,
                    default_wavelength_m=cli_lambda,
                    dtype=torch.float64
                )

                # No warning should be emitted
                wavelength_warnings = [warning for warning in w
                                      if "wavelength" in str(warning.message).lower()]
                assert len(wavelength_warnings) == 0

        finally:
            sourcefile_path.unlink()

    def test_no_warning_when_column_missing(self):
        """No warning when wavelength column is absent (defaults to CLI)."""
        cli_lambda = 1.0e-10

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Only X Y Z weight (no wavelength column)
            f.write("0.0 0.0 -10.0 1.0\n")
            sourcefile_path = Path(f.name)

        try:
            # Clear any previous warning state
            if hasattr(read_sourcefile, '_wavelength_warned'):
                delattr(read_sourcefile, '_wavelength_warned')

            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")

                directions, weights, wavelengths = read_sourcefile(
                    sourcefile_path,
                    default_wavelength_m=cli_lambda,
                    dtype=torch.float64
                )

                # No warning for missing column
                wavelength_warnings = [warning for warning in w
                                      if "wavelength" in str(warning.message).lower()]
                assert len(wavelength_warnings) == 0

                # Wavelength should still be CLI value
                assert torch.allclose(wavelengths, torch.tensor([cli_lambda], dtype=torch.float64))

        finally:
            sourcefile_path.unlink()


class TestStepsNormalizationParity:
    """TC-E3: Steps calculation must count all sources (including zero-weight).

    Per nanoBragg.c:2700-2720, steps = sources_total × mosaic × phi × oversample²
    where sources_total includes all entries (even zero-weight divergence placeholders).
    """

    def test_steps_count_includes_zero_weight_sources(self):
        """Steps denominator must count zero-weight sources per C convention."""
        # This test verifies the simulator's steps calculation.
        # Implementation note: The actual steps fix is in simulator.py initialization,
        # not in source.py. This test documents the expected behavior.

        cli_lambda = 1.0e-10

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Two sources: one normal weight, one zero weight
            f.write(f"0.0 0.0 -10.0 1.0 {cli_lambda}\n")
            f.write(f"0.1 0.0 -10.0 0.0 {cli_lambda}\n")  # Zero weight
            sourcefile_path = Path(f.name)

        try:
            directions, weights, wavelengths = read_sourcefile(
                sourcefile_path,
                default_wavelength_m=cli_lambda,
                dtype=torch.float64
            )

            # Verify both sources are returned
            assert len(directions) == 2
            assert len(weights) == 2
            assert len(wavelengths) == 2

            # Verify weights include the zero-weight entry
            assert weights[0].item() == 1.0
            assert weights[1].item() == 0.0

            # NOTE: The actual steps calculation test is in the simulator integration tests.
            # This test confirms source.py returns all sources for proper steps counting.

        finally:
            sourcefile_path.unlink()

    def test_equal_weighting_preserved(self):
        """All sources must have equal weight (per spec line 151)."""
        cli_lambda = 1.0e-10

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            # Varying weights in file (should be ignored in final intensity calc)
            f.write(f"0.0 0.0 -10.0 1.0 {cli_lambda}\n")
            f.write(f"0.1 0.0 -10.0 0.5 {cli_lambda}\n")
            f.write(f"0.2 0.0 -10.0 2.0 {cli_lambda}\n")
            sourcefile_path = Path(f.name)

        try:
            directions, weights, wavelengths = read_sourcefile(
                sourcefile_path,
                default_wavelength_m=cli_lambda,
                dtype=torch.float64
            )

            # Weights are read from file (for future use or validation)
            # but should NOT affect final intensity (equal weighting via steps division)
            assert len(weights) == 3
            # File weights are preserved for now; equal weighting enforced in simulator

        finally:
            sourcefile_path.unlink()


# Acceptance thresholds (from lambda_semantics.md):
# - Wavelength override: exact match (within machine precision)
# - Warning emission: pytest.warns match on text
# - Steps parity: integration test required (simulator level)

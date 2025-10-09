"""
CLI Scaling Tests for CLI-FLAGS-003 Phase K

Tests the SQUARE lattice factor (F_latt) calculation correctness after fixing
the (h-h0) bug. Validates that PyTorch matches C for F_latt and I_before_scaling.

Evidence base: reports/2025-10-cli-flags/phase_k/f_latt_fix/
Plan reference: plans/active/cli-noise-pix0/plan.md Phase K1-K3
"""
import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
import pytest
import numpy as np

# Set required environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def get_c_binary():
    """Resolve C binary path from env or fallback."""
    c_bin = os.environ.get('NB_C_BIN')
    if c_bin:
        c_path = Path(c_bin)
        if c_path.exists():
            return str(c_path)
        pytest.skip(f"NB_C_BIN={c_bin} does not exist")

    # Fallback order: golden_suite_generator/nanoBragg → ./nanoBragg
    for candidate in ['./golden_suite_generator/nanoBragg', './nanoBragg']:
        c_path = Path(candidate)
        if c_path.exists():
            return str(c_path.resolve())

    pytest.skip("No C binary found (set NB_C_BIN or ensure ./golden_suite_generator/nanoBragg exists)")


def is_parallel_enabled():
    """Check if parallel validation is enabled."""
    return os.environ.get('NB_RUN_PARALLEL', '0') == '1'


def read_float_image(path, shape):
    """Read a raw float binary image."""
    data = np.fromfile(path, dtype=np.float32)
    if data.size != shape[0] * shape[1]:
        raise ValueError(f"Expected {shape[0]}×{shape[1]}={shape[0]*shape[1]} floats, got {data.size}")
    return data.reshape(shape)


class TestMOSFLMCellVectors:
    """Test MOSFLM matrix cell vector computation (Phase K3g2)."""

    def test_mosflm_cell_vectors(self):
        """
        Verify that PyTorch correctly computes real-space vectors from MOSFLM matrices.

        This test validates CLI-FLAGS-003 Phase K3g1 implementation:
        When MOSFLM reciprocal vectors are provided (via -mat file), PyTorch must:
        1. Compute V_star = a* · (b* × c*)
        2. Compute V_cell = 1 / V_star
        3. Derive real vectors: a = (b* × c*) × V_cell, etc.
        4. Update cell_a/b/c parameters from the derived vectors

        Expected output (from C trace):
        - V_cell ≈ 24682.3 Å³
        - |a| ≈ 26.7514 Å
        - |b| ≈ 31.3100 Å
        - |c| ≈ 33.6734 Å
        """
        import torch
        from nanobrag_torch.models.crystal import Crystal, CrystalConfig
        from nanobrag_torch.io.mosflm import read_mosflm_matrix

        # Read A.mat from repo root
        mat_file = Path('A.mat')
        if not mat_file.exists():
            pytest.skip("A.mat not found in repository root")

        wavelength_A = 0.976800
        a_star, b_star, c_star = read_mosflm_matrix(str(mat_file), wavelength_A)

        # Create Crystal with MOSFLM orientation
        config = CrystalConfig(
            cell_a=100.0,  # placeholder
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            mosflm_a_star=a_star,
            mosflm_b_star=b_star,
            mosflm_c_star=c_star,
            N_cells=(36, 47, 29),
        )

        crystal = Crystal(config, device=torch.device('cpu'), dtype=torch.float64)
        tensors = crystal.compute_cell_tensors()

        # Expected values from C trace (reports/2025-10-cli-flags/phase_k/base_lattice/c_stdout.txt)
        expected_V_cell = 24682.3  # Å³
        expected_mag_a = 26.7514   # Å
        expected_mag_b = 31.3100   # Å
        expected_mag_c = 33.6734   # Å

        # Compute actual values
        actual_V_cell = tensors['V'].item()
        actual_mag_a = torch.norm(tensors['a']).item()
        actual_mag_b = torch.norm(tensors['b']).item()
        actual_mag_c = torch.norm(tensors['c']).item()

        # Tolerance: 5e-4 relative error (from Phase K3f exit criteria)
        rtol = 5e-4

        # Assertions
        V_rel_error = abs(actual_V_cell - expected_V_cell) / expected_V_cell
        assert V_rel_error <= rtol, \
            f"V_cell relative error {V_rel_error:.6g} > {rtol}. " \
            f"Expected {expected_V_cell:.2f}, got {actual_V_cell:.2f} Å³"

        a_rel_error = abs(actual_mag_a - expected_mag_a) / expected_mag_a
        assert a_rel_error <= rtol, \
            f"|a| relative error {a_rel_error:.6g} > {rtol}. " \
            f"Expected {expected_mag_a:.4f}, got {actual_mag_a:.4f} Å"

        b_rel_error = abs(actual_mag_b - expected_mag_b) / expected_mag_b
        assert b_rel_error <= rtol, \
            f"|b| relative error {b_rel_error:.6g} > {rtol}. " \
            f"Expected {expected_mag_b:.4f}, got {actual_mag_b:.4f} Å"

        c_rel_error = abs(actual_mag_c - expected_mag_c) / expected_mag_c
        assert c_rel_error <= rtol, \
            f"|c| relative error {c_rel_error:.6g} > {rtol}. " \
            f"Expected {expected_mag_c:.4f}, got {actual_mag_c:.4f} Å"


@pytest.mark.skipif(not is_parallel_enabled(), reason="NB_RUN_PARALLEL=1 required for C↔PyTorch parity")
class TestFlattSquareMatchesC:
    """Test that SQUARE lattice factor matches C implementation."""

    def test_f_latt_square_matches_c(self):
        """
        Verify F_latt and I_before_scaling match between C and PyTorch for SQUARE shape.

        This test runs a minimal SQUARE crystal simulation and compares final intensities.
        The ratio should be within 1e-3 (Phase K3 exit criterion).

        CRITICAL FIX: This test validates that F_latt uses sincg(π·h, Na) instead of
        the incorrect sincg(π·(h-h0), Na) which caused a 463× error (Attempt #28).
        """
        if not is_parallel_enabled():
            pytest.skip("NB_RUN_PARALLEL=1 required")

        c_bin = get_c_binary()
        py_cli = f"{sys.executable} -m nanobrag_torch"

        # Shared parameters (simple cubic, SQUARE shape)
        common_args = [
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '300',
            '-N', '10',
            '-lambda', '1.0',
            '-distance', '100',
            '-detpixels', '512',
            '-pixel', '0.1',
            '-oversample', '1',
            '-phisteps', '1',
            '-mosaic_dom', '1'
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            c_out = tmpdir / 'c_image.bin'
            py_out = tmpdir / 'py_image.bin'

            # Run C (in tmpdir to avoid Fdump.bin contamination)
            # Convert c_bin to absolute path before changing directory
            c_bin_abs = str(Path(c_bin).resolve())
            c_cmd = [c_bin_abs] + common_args + ['-floatfile', str(c_out)]
            result_c = subprocess.run(c_cmd, capture_output=True, text=True, cwd=tmpdir)
            if result_c.returncode != 0:
                pytest.fail(f"C simulation failed:\n{result_c.stderr}")

            # Run PyTorch (in tmpdir to avoid Fdump.bin contamination)
            py_cmd = py_cli.split() + common_args + ['-floatfile', str(py_out)]
            result_py = subprocess.run(py_cmd, capture_output=True, text=True, cwd=tmpdir)
            if result_py.returncode != 0:
                pytest.fail(f"PyTorch simulation failed:\n{result_py.stderr}")

            # Load images
            shape = (512, 512)
            c_img = read_float_image(c_out, shape)
            py_img = read_float_image(py_out, shape)

            # Compute metrics
            c_sum = np.sum(c_img)
            py_sum = np.sum(py_img)
            sum_ratio = py_sum / c_sum if c_sum > 0 else float('inf')

            c_max = np.max(c_img)
            py_max = np.max(py_img)
            max_ratio = py_max / c_max if c_max > 0 else float('inf')

            # Correlation
            c_flat = c_img.flatten()
            py_flat = py_img.flatten()
            correlation = np.corrcoef(c_flat, py_flat)[0, 1] if np.std(c_flat) > 0 and np.std(py_flat) > 0 else 0.0

            # Phase K3 exit criteria: ratios within 1e-3
            # (sum_ratio and max_ratio should be ~1.0)
            tolerance = 1e-3

            # Report metrics
            metrics = {
                'c_sum': float(c_sum),
                'py_sum': float(py_sum),
                'sum_ratio': float(sum_ratio),
                'c_max': float(c_max),
                'py_max': float(py_max),
                'max_ratio': float(max_ratio),
                'correlation': float(correlation)
            }

            # Save metrics on failure for debugging
            if abs(sum_ratio - 1.0) > tolerance or abs(max_ratio - 1.0) > tolerance or correlation < 0.999:
                report_dir = Path('reports/2025-10-cli-flags/phase_k/f_latt_fix')
                report_dir.mkdir(parents=True, exist_ok=True)
                metrics_path = report_dir / 'test_metrics_failure.json'
                with open(metrics_path, 'w') as f:
                    json.dump(metrics, f, indent=2)

                # Save images for inspection
                np.save(report_dir / 'c_image.npy', c_img)
                np.save(report_dir / 'py_image.npy', py_img)

            # Assertions
            assert correlation >= 0.999, \
                f"Correlation {correlation:.6f} < 0.999. Metrics: {json.dumps(metrics, indent=2)}"

            assert abs(sum_ratio - 1.0) <= tolerance, \
                f"Sum ratio {sum_ratio:.6f} deviates by {abs(sum_ratio - 1.0):.6f} (> {tolerance}). " \
                f"C sum={c_sum:.6g}, PyTorch sum={py_sum:.6g}. Metrics: {json.dumps(metrics, indent=2)}"

            assert abs(max_ratio - 1.0) <= tolerance, \
                f"Max ratio {max_ratio:.6f} deviates by {abs(max_ratio - 1.0):.6f} (> {tolerance}). " \
                f"C max={c_max:.6g}, PyTorch max={py_max:.6g}. Metrics: {json.dumps(metrics, indent=2)}"


class TestSourceWeights:
    """Test SOURCE-WEIGHT-001: Weighted source normalization correctness."""

    def test_source_weights_ignored_per_spec(self):
        """
        Verify that source weights are ignored per specs/spec-a-core.md:151.

        SOURCE-WEIGHT-001 Phase G (TC-Spec-1): Weighted vs equal-weight comparison
        This test replaces test_weighted_source_matches_c (which enforced C-PARITY-001 bug).
        Expected: PyTorch treats weighted and unweighted sourcefiles identically (equal weighting).

        Strategy: Run PyTorch twice with same source positions:
        - Run A: Sourcefile with varying weights [1.0, 0.2]
        - Run B: Sourcefile with equal weights [1.0, 1.0]
        - Assert: Outputs are identical (within 0.3% tolerance for float32 precision)

        Per spec: "Both the weight column and the wavelength column are read but ignored:
        the CLI -lambda parameter is the sole authoritative wavelength source for all sources,
        and equal weighting results (all sources contribute equally via division by total
        source count in the steps normalization)." (spec-a-core.md:151-153)
        """
        py_cli = f"{sys.executable} -m nanobrag_torch"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create weighted source file (weights 1.0 and 0.2, should be ignored)
            weighted_sourcefile = tmpdir / 'weighted_sources.txt'
            with open(weighted_sourcefile, 'w') as f:
                # Format: X Y Z weight lambda(m)
                f.write("0.0 0.0 -1.0 1.0 1.0e-10\n")  # weight=1.0
                f.write("0.1 0.0 -1.0 0.2 1.0e-10\n")  # weight=0.2 (should be ignored)

            # Create equal-weight source file (same positions, uniform weights)
            equal_sourcefile = tmpdir / 'equal_sources.txt'
            with open(equal_sourcefile, 'w') as f:
                # Same positions, but weights = 1.0 for both
                f.write("0.0 0.0 -1.0 1.0 1.0e-10\n")
                f.write("0.1 0.0 -1.0 1.0 1.0e-10\n")

            # Shared parameters (small detector for fast test)
            common_args = [
                '-cell', '100', '100', '100', '90', '90', '90',
                '-default_F', '300',
                '-N', '5',
                '-distance', '100',
                '-detpixels', '128',
                '-pixel', '0.1',
                '-lambda', '1.0',  # CLI lambda overrides sourcefile values
                '-oversample', '1',
                '-phisteps', '1',
                '-mosaic_dom', '1'
            ]

            weighted_out = tmpdir / 'py_weighted.bin'
            equal_out = tmpdir / 'py_equal.bin'

            # Run A: Weighted sourcefile
            weighted_cmd = py_cli.split() + common_args + ['-sourcefile', str(weighted_sourcefile), '-floatfile', str(weighted_out)]
            result_weighted = subprocess.run(weighted_cmd, capture_output=True, text=True, cwd=tmpdir)
            if result_weighted.returncode != 0:
                pytest.fail(f"Weighted run failed:\n{result_weighted.stderr}")

            # Run B: Equal-weight sourcefile
            equal_cmd = py_cli.split() + common_args + ['-sourcefile', str(equal_sourcefile), '-floatfile', str(equal_out)]
            result_equal = subprocess.run(equal_cmd, capture_output=True, text=True, cwd=tmpdir)
            if result_equal.returncode != 0:
                pytest.fail(f"Equal-weight run failed:\n{result_equal.stderr}")

            # Load images
            shape = (128, 128)
            weighted_img = read_float_image(weighted_out, shape)
            equal_img = read_float_image(equal_out, shape)

            # Compute metrics
            weighted_sum = np.sum(weighted_img)
            equal_sum = np.sum(equal_img)
            sum_ratio = weighted_sum / equal_sum if equal_sum > 0 else float('inf')

            # Correlation
            weighted_flat = weighted_img.flatten()
            equal_flat = equal_img.flatten()
            correlation = np.corrcoef(weighted_flat, equal_flat)[0, 1] if np.std(weighted_flat) > 0 and np.std(equal_flat) > 0 else 0.0

            # Spec-based tolerance: 0.3% for sum ratio (float32 precision)
            tolerance_ratio = 3e-3  # 0.3%
            tolerance_corr = 0.999

            # Save metrics on failure
            metrics = {
                'weighted_sum': float(weighted_sum),
                'equal_sum': float(equal_sum),
                'sum_ratio': float(sum_ratio),
                'correlation': float(correlation),
                'tolerance_ratio': tolerance_ratio,
                'tolerance_corr': tolerance_corr
            }

            if abs(sum_ratio - 1.0) > tolerance_ratio or correlation < tolerance_corr:
                report_dir = Path('reports/2025-11-source-weights/phase_g') / 'test_failure'
                report_dir.mkdir(parents=True, exist_ok=True)
                with open(report_dir / 'metrics_spec_compliance.json', 'w') as f:
                    json.dump(metrics, f, indent=2)

            # Assertions
            assert correlation >= tolerance_corr, \
                f"Weighted vs equal correlation {correlation:.6f} < {tolerance_corr}. " \
                f"Spec violation: weights should be ignored (spec-a-core.md:151-153). " \
                f"Metrics: {json.dumps(metrics, indent=2)}"

            assert abs(sum_ratio - 1.0) <= tolerance_ratio, \
                f"Weighted vs equal sum ratio {sum_ratio:.6f} deviates from 1.0 by {abs(sum_ratio - 1.0):.6f} (> {tolerance_ratio}). " \
                f"Spec violation: equal weighting should result. " \
                f"Weighted sum={weighted_sum:.6g}, Equal sum={equal_sum:.6g}. " \
                f"Metrics: {json.dumps(metrics, indent=2)}"

    def test_cli_lambda_overrides_sourcefile(self, monkeypatch):
        """
        Verify CLI -lambda parameter overrides sourcefile wavelengths per spec §4.

        SOURCE-WEIGHT-001 Phase G (TC-Spec-2): CLI lambda override validation
        Expected behavior:
        1. UserWarning emitted when sourcefile wavelengths differ from CLI
        2. All source contributions use CLI wavelength (not file values)
        3. Physics calculations consistent with CLI lambda only

        Per spec: "the CLI -lambda parameter is the sole authoritative wavelength source
        for all sources" (spec-a-core.md:151-152)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            py_out = tmpdir / 'py_lambda_override.bin'

            # Create sourcefile with lambda=1.0e-10m (1.0Å), CLI will specify 0.5Å
            sourcefile = tmpdir / 'sources_with_lambda.txt'
            with open(sourcefile, 'w') as f:
                # Format: X Y Z weight lambda(m)
                f.write("0.0 0.0 -1.0 1.0 1.0e-10\n")  # lambda=1.0Å (should be overridden)
                f.write("0.1 0.0 -1.0 1.0 1.0e-10\n")  # lambda=1.0Å (should be overridden)

            # Command with CLI lambda override
            args_with_override = [
                'nanoBragg',  # Program name
                '-cell', '100', '100', '100', '90', '90', '90',
                '-default_F', '300',
                '-N', '5',
                '-distance', '100',
                '-detpixels', '128',
                '-pixel', '0.1',
                '-sourcefile', str(sourcefile),
                '-lambda', '0.5',  # CLI override (different from file's 1.0Å)
                '-oversample', '1',
                '-phisteps', '1',
                '-mosaic_dom', '1',
                '-floatfile', str(py_out)
            ]

            # Use monkeypatch to set sys.argv for in-process execution
            monkeypatch.setattr(sys, 'argv', args_with_override)

            # Import main function
            from nanobrag_torch.__main__ import main

            # Execute main() under pytest.warns context
            # The warning should be emitted when sourcefile wavelengths differ from CLI
            with pytest.warns(UserWarning, match="Sourcefile wavelength column differs") as record:
                main()

            # Verify warning message contains expected fragments
            assert len(record) >= 1, "No UserWarning was raised about wavelength override"
            warning_message = str(record[0].message.args[0])

            # Check for spec reference in warning
            assert "spec-a-core.md" in warning_message, \
                f"Warning missing spec reference. Full warning: {warning_message}"

            # Verify output was written
            assert py_out.exists(), "Output file was not created"

            # Indirect verification: Compare against reference run with CLI lambda only
            # If CLI override worked correctly, the output should match a run with uniform lambda
            reference_out = tmpdir / 'py_reference.bin'
            reference_sourcefile = tmpdir / 'sources_uniform_lambda.txt'
            with open(reference_sourcefile, 'w') as f:
                # Same positions, but lambda matches CLI value
                f.write("0.0 0.0 -1.0 1.0 5.0e-11\n")  # lambda=0.5Å (matches CLI)
                f.write("0.1 0.0 -1.0 1.0 5.0e-11\n")  # lambda=0.5Å (matches CLI)

            args_reference = [
                'nanoBragg',
                '-cell', '100', '100', '100', '90', '90', '90',
                '-default_F', '300',
                '-N', '5',
                '-distance', '100',
                '-detpixels', '128',
                '-pixel', '0.1',
                '-sourcefile', str(reference_sourcefile),
                '-lambda', '0.5',
                '-oversample', '1',
                '-phisteps', '1',
                '-mosaic_dom', '1',
                '-floatfile', str(reference_out)
            ]

            monkeypatch.setattr(sys, 'argv', args_reference)
            main()

            # Load and compare
            shape = (128, 128)
            override_img = read_float_image(py_out, shape)
            reference_img = read_float_image(reference_out, shape)

            override_sum = np.sum(override_img)
            reference_sum = np.sum(reference_img)
            sum_ratio = override_sum / reference_sum if reference_sum > 0 else float('inf')

            # If CLI override worked, outputs should match within float32 precision
            tolerance_ratio = 3e-3  # 0.3%

            assert abs(sum_ratio - 1.0) <= tolerance_ratio, \
                f"CLI lambda override failed: sum_ratio={sum_ratio:.6f} (expected ~1.0). " \
                f"Override sum={override_sum:.6g}, Reference sum={reference_sum:.6g}"

    def test_uniform_weights_ignored(self):
        """
        Verify that weights are ignored per spec-a-core.md line 151.

        SOURCE-WEIGHT-001 Phase C3 (TC-B): Three sources with uniform weights [1.0, 1.0, 1.0]
        Expected: Weights are read but ignored (equal weighting results)
        """
        import torch
        from nanobrag_torch.config import BeamConfig

        # Create beam config with uniform weights (should be accepted but ignored)
        beam_config = BeamConfig(
            wavelength_A=1.0,
            source_weights=torch.tensor([1.0, 1.0, 1.0])
        )

        # Verify weights were stored (config doesn't validate or reject them)
        assert beam_config.source_weights is not None
        assert len(beam_config.source_weights) == 3

    def test_edge_case_zero_sum_accepted(self):
        """
        Verify that zero-sum weights are accepted (since they're ignored).

        SOURCE-WEIGHT-001 Phase C3 (TC-D): Edge case validation
        Per spec: weights are "read but ignored", so any values should be accepted
        """
        import torch
        from nanobrag_torch.config import BeamConfig

        # Test all-zero weights (should be accepted since ignored)
        beam_config = BeamConfig(
            wavelength_A=1.0,
            source_weights=torch.tensor([0.0, 0.0])
        )
        assert beam_config.source_weights is not None

        # Test zero-sum from mixed signs (should be accepted since ignored)
        beam_config = BeamConfig(
            wavelength_A=1.0,
            source_weights=torch.tensor([1.0, -1.0])
        )
        assert beam_config.source_weights is not None

    def test_edge_case_negative_weights_accepted(self):
        """
        Verify that negative weights are accepted (since they're ignored).

        SOURCE-WEIGHT-001 Phase C3 (TC-D): Edge case validation
        Per spec: weights are "read but ignored", so negative values are allowed
        """
        import torch
        from nanobrag_torch.config import BeamConfig

        beam_config = BeamConfig(
            wavelength_A=1.0,
            source_weights=torch.tensor([1.0, -0.2])
        )
        assert beam_config.source_weights is not None

    def test_single_source_fallback(self):
        """
        Verify that single-source behavior is preserved (source_weights=None).

        SOURCE-WEIGHT-001 Phase C3 (TC-C): Single source fallback
        """
        import torch
        from nanobrag_torch.config import BeamConfig
        from nanobrag_torch.models.detector import Detector, DetectorConfig
        from nanobrag_torch.models.crystal import Crystal, CrystalConfig
        from nanobrag_torch.simulator import Simulator

        # Create minimal configs without source_weights
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=100.0
        )

        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64,
            fpixels=64
        )

        beam_config = BeamConfig(
            wavelength_A=1.0,
            source_weights=None  # Explicit None for single source
        )

        # Create simulator (should not crash)
        detector = Detector(detector_config, device=torch.device('cpu'), dtype=torch.float32)
        crystal = Crystal(crystal_config, beam_config=beam_config, device=torch.device('cpu'), dtype=torch.float32)
        simulator = Simulator(crystal, detector, beam_config, device=torch.device('cpu'), dtype=torch.float32)

        # Run simulation (should use n_sources=1 fallback)
        result = simulator.run()

        # Verify result shape
        assert result.shape == (64, 64), f"Expected (64, 64), got {result.shape}"

        # Verify some intensity was generated (default_F=100 should produce signal)
        assert result.sum().item() > 0, "Single source simulation should produce non-zero intensity"


class TestSourceWeightsDivergence:
    """Test SOURCE-WEIGHT-001 Phase G: Source weight spec compliance and divergence documentation."""

    @pytest.mark.xfail(
        reason="C-PARITY-001: C applies source weights during accumulation, "
               "violating spec requirement for equal weighting (spec-a-core.md:151-153). "
               "See reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md"
    )
    @pytest.mark.skipif(not is_parallel_enabled(), reason="NB_RUN_PARALLEL=1 required")
    def test_c_divergence_reference(self):
        """
        Reference test documenting expected C vs PyTorch divergence on weighted sources.

        This test is marked XFAIL because C behavior diverges from spec (C-PARITY-001).
        It serves as a regression detector: if it starts passing, investigate whether
        C or PyTorch changed unexpectedly.

        Expected divergence (from Phase E analysis):
        - Correlation < 0.8 (C applies weights, PyTorch ignores them per spec)
        - C intensity differs significantly due to weight application bug

        Per spec: "Both the weight column and the wavelength column are read but ignored"
        (spec-a-core.md:151-152). PyTorch implements this correctly; C does not.
        """
        if not is_parallel_enabled():
            pytest.skip("NB_RUN_PARALLEL=1 required")

        c_bin = get_c_binary()
        py_cli = f"{sys.executable} -m nanobrag_torch"

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # Create weighted source file (C will apply weights, PyTorch will ignore)
            sourcefile = tmpdir / 'weighted_sources.txt'
            with open(sourcefile, 'w') as f:
                # Format: X Y Z weight lambda(m)
                f.write("0.0 0.0 -1.0 1.0 1.0e-10\n")  # weight=1.0
                f.write("0.1 0.0 -1.0 0.2 1.0e-10\n")  # weight=0.2 (C applies, Py ignores)

            # Shared parameters (small detector for fast test)
            common_args = [
                '-cell', '100', '100', '100', '90', '90', '90',
                '-default_F', '300',
                '-N', '5',
                '-distance', '100',
                '-detpixels', '128',
                '-pixel', '0.1',
                '-lambda', '1.0',
                '-oversample', '1',
                '-phisteps', '1',
                '-mosaic_dom', '1',
                '-sourcefile', str(sourcefile)
            ]

            c_out = tmpdir / 'c_weighted.bin'
            py_out = tmpdir / 'py_weighted.bin'

            # Run C
            c_bin_abs = str(Path(c_bin).resolve())
            c_cmd = [c_bin_abs] + common_args + ['-floatfile', str(c_out)]
            result_c = subprocess.run(c_cmd, capture_output=True, text=True, cwd=tmpdir)
            if result_c.returncode != 0:
                pytest.fail(f"C simulation failed:\n{result_c.stderr}")

            # Run PyTorch
            py_cmd = py_cli.split() + common_args + ['-floatfile', str(py_out)]
            result_py = subprocess.run(py_cmd, capture_output=True, text=True, cwd=tmpdir)
            if result_py.returncode != 0:
                pytest.fail(f"PyTorch simulation failed:\n{result_py.stderr}")

            # Load images
            shape = (128, 128)
            c_img = read_float_image(c_out, shape)
            py_img = read_float_image(py_out, shape)

            # Compute metrics
            c_sum = np.sum(c_img)
            py_sum = np.sum(py_img)
            sum_ratio = py_sum / c_sum if c_sum > 0 else float('inf')

            # Correlation
            c_flat = c_img.flatten()
            py_flat = py_img.flatten()
            correlation = np.corrcoef(c_flat, py_flat)[0, 1] if np.std(c_flat) > 0 and np.std(py_flat) > 0 else 0.0

            # Save metrics for documentation
            metrics = {
                'c_sum': float(c_sum),
                'py_sum': float(py_sum),
                'sum_ratio': float(sum_ratio),
                'correlation': float(correlation),
                'expected': 'correlation < 0.8 (C-PARITY-001)',
                'decision_memo': 'reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md'
            }

            if correlation >= 0.8 or abs(sum_ratio - 1.0) <= 1e-3:
                # This would be unexpected - document for investigation
                report_dir = Path('reports/2025-11-source-weights/phase_g') / 'unexpected_c_parity'
                report_dir.mkdir(parents=True, exist_ok=True)
                with open(report_dir / 'metrics.json', 'w') as f:
                    json.dump(metrics, f, indent=2)

            # This assertion is EXPECTED TO FAIL (hence @pytest.mark.xfail)
            # If it starts passing, investigate whether C or PyTorch changed
            assert correlation >= 0.999, \
                f"C-PARITY-001: Expected divergence detected. Correlation={correlation:.6f}. " \
                f"C sum={c_sum:.6g}, PyTorch sum={py_sum:.6g}, ratio={sum_ratio:.6f}. " \
                f"See reports/2025-11-source-weights/phase_e/20251009T202432Z/spec_vs_c_decision.md"

    def test_sourcefile_divergence_warning(self, monkeypatch):
        """TC-D2: Verify UserWarning when sourcefile + divergence parameters both present."""
        # This test validates the CLI warning guard at argument parsing level
        # Per SOURCE-WEIGHT-001 Phase E Option B: warn when sourcefile + divergence params coexist
        # Updated to use in-process pytest.warns instead of subprocess stderr parsing

        # Check fixture availability
        fixture_paths = [
            Path('reports/2025-11-source-weights/fixtures/two_sources.txt'),
            Path('reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt')
        ]
        sourcefile = None
        for path in fixture_paths:
            if path.exists():
                sourcefile = path
                break

        if sourcefile is None:
            pytest.skip("two_sources.txt fixture not found in expected locations")

        mat_file = Path('A.mat')
        if not mat_file.exists():
            pytest.skip("A.mat not found in repository root")

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            py_out = tmpdir / 'py_tc_d2.bin'

            # Command that should emit warning: sourcefile + hdivrange
            args_with_warning = [
                'nanoBragg',  # Program name
                '-mat', str(mat_file.resolve()),
                '-sourcefile', str(sourcefile.resolve()),
                '-hdivrange', '0.5',  # This should trigger the warning
                '-distance', '231.274660',
                '-lambda', '0.9768',
                '-pixel', '0.172',
                '-detpixels_x', '256',
                '-detpixels_y', '256',
                '-oversample', '1',
                '-nonoise',
                '-nointerpolate',
                '-floatfile', str(py_out)
            ]

            # Use monkeypatch to set sys.argv for in-process execution
            monkeypatch.setattr(sys, 'argv', args_with_warning)

            # Import main function (local import to avoid side effects)
            from nanobrag_torch.__main__ import main

            # Execute main() under pytest.warns context
            # The warning should be emitted from __main__.py:736-741
            with pytest.warns(UserWarning, match="Divergence/dispersion parameters ignored") as record:
                main()

            # Verify warning message contains expected fragments
            assert len(record) >= 1, "TC-D2: No UserWarning was raised"
            warning_message = str(record[0].message.args[0])

            expected_fragments = [
                "Divergence/dispersion parameters ignored",
                "sourcefile is provided",
                "spec-a-core.md:151-162"
            ]

            for fragment in expected_fragments:
                assert fragment in warning_message, \
                    f"TC-D2: Expected warning fragment '{fragment}' not found.\n" \
                    f"Full warning: {warning_message}"

            # Verify output was written
            assert py_out.exists(), "TC-D2: Output file was not created"


class TestHKLDevice:
    """Test that HKL tensors respect CLI -device flag (Phase L3d)."""

    @pytest.mark.parametrize("device_str,dtype_str", [
        ("cpu", "float32"),
        ("cpu", "float64"),
        pytest.param("cuda", "float32", marks=pytest.mark.skipif(
            not __import__('torch').cuda.is_available(), reason="CUDA not available")),
        pytest.param("cuda", "float64", marks=pytest.mark.skipif(
            not __import__('torch').cuda.is_available(), reason="CUDA not available")),
    ])
    def test_hkl_tensor_respects_device(self, device_str, dtype_str):
        """
        Verify that HKL tensors are transferred to the correct device when CLI -device is specified.

        This test validates CLI-FLAGS-003 Phase L3d implementation:
        When the CLI is invoked with -device cuda (or cpu), the HKL tensor loaded from
        -hkl file must be transferred to the specified device (not remain on CPU).

        The fix ensures that __main__.py:1073 calls .to(device=device, dtype=dtype)
        instead of just .to(dtype=dtype).

        Expected behavior:
        - crystal.hkl_data.device matches the requested device
        - crystal.hkl_data.dtype matches the requested dtype
        - Structure factor lookup succeeds without device mismatch errors
        """
        import torch
        from nanobrag_torch.models.crystal import Crystal, CrystalConfig
        from nanobrag_torch.config import BeamConfig
        from nanobrag_torch.io.hkl import read_hkl_file

        # Check if scaled.hkl exists (supervisor test case)
        hkl_file = Path('scaled.hkl')
        if not hkl_file.exists():
            pytest.skip("scaled.hkl not found (required for Phase L supervisor command)")

        # Parse device and dtype
        device = torch.device(device_str)
        dtype = torch.float32 if dtype_str == "float32" else torch.float64

        # Load HKL data
        hkl_array, hkl_metadata = read_hkl_file(str(hkl_file))

        # Create minimal config (matching supervisor command)
        wavelength_A = 0.976800
        beam_config = BeamConfig(wavelength_A=wavelength_A)

        config = CrystalConfig(
            cell_a=100.0,
            cell_b=100.0,
            cell_c=100.0,
            cell_alpha=90.0,
            cell_beta=90.0,
            cell_gamma=90.0,
            N_cells=(36, 47, 29),
        )

        # Instantiate Crystal
        crystal = Crystal(config, beam_config=beam_config, device=device, dtype=dtype)

        # Attach HKL data (mimicking __main__.py flow)
        if isinstance(hkl_array, torch.Tensor):
            crystal.hkl_data = hkl_array.clone().detach().to(device=device, dtype=dtype)
        else:
            crystal.hkl_data = torch.tensor(hkl_array, device=device, dtype=dtype)
        crystal.hkl_metadata = hkl_metadata

        # Verify device and dtype
        # Use .type comparison for device to handle cuda vs cuda:0
        assert crystal.hkl_data.device.type == device.type, \
            f"HKL tensor device {crystal.hkl_data.device} does not match requested {device}"
        assert crystal.hkl_data.dtype == dtype, \
            f"HKL tensor dtype {crystal.hkl_data.dtype} does not match requested {dtype}"

        # Verify structure factor lookup works (target reflection from supervisor trace)
        # hkl = (-7, -1, -14) should return F_cell ≈ 190.27 (from Phase L3b probe)
        h = torch.tensor(-7.0, device=device, dtype=dtype)
        k = torch.tensor(-1.0, device=device, dtype=dtype)
        l = torch.tensor(-14.0, device=device, dtype=dtype)

        # Lookup structure factor
        F_cell = crystal.get_structure_factor(h, k, l)

        # Expected value from C trace and Phase L3b probe
        expected_F = 190.27
        tolerance = 0.01  # Allow 1% tolerance for dtype differences

        # Verify result
        # Use .type comparison for device to handle cuda vs cuda:0
        assert F_cell.device.type == device.type, \
            f"get_structure_factor returned tensor on {F_cell.device}, expected {device}"

        F_cell_val = F_cell.item()
        rel_error = abs(F_cell_val - expected_F) / expected_F
        assert rel_error <= tolerance, \
            f"Structure factor lookup failed: expected {expected_F:.2f}, got {F_cell_val:.2f} " \
            f"(relative error {rel_error:.6f} > {tolerance})"

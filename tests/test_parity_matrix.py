"""
Parity Matrix Test Runner

This module implements the canonical C↔PyTorch parity harness referenced in:
- specs/spec-a-parallel.md (Parallel Validation Matrix)
- docs/development/testing_strategy.md (Section 2.5)

It consumes cases from tests/parity_cases.yaml and executes both the C reference
(NB_C_BIN) and PyTorch CLI (sys.executable -m nanobrag_torch), computing:
- Correlation (Pearson r)
- MSE, RMSE
- Max absolute difference
- Sum ratio (C_sum / Py_sum)
- Optional SSIM

On failure, it writes metrics.json and diff artifacts to reports/<date>-AT-<ID>/.

Required environment variables:
- NB_RUN_PARALLEL=1 (enables live parity tests)
- NB_C_BIN (path to C binary; defaults to ./golden_suite_generator/nanoBragg or ./nanoBragg)

Usage:
    KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py
    KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 NB_C_BIN=./golden_suite_generator/nanoBragg pytest -v tests/test_parity_matrix.py -k "AT-PARALLEL-002"
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime
import pytest
import yaml
import numpy as np
from scipy.stats import pearsonr


# --- Environment & Binary Resolution ---


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


def get_pytorch_cli():
    """Resolve PyTorch CLI command."""
    py_bin = os.environ.get('NB_PY_BIN')
    if py_bin:
        return py_bin

    # Use current Python interpreter with module runner
    return f"{sys.executable} -m nanobrag_torch"


def is_parallel_enabled():
    """Check if parallel validation is enabled."""
    return os.environ.get('NB_RUN_PARALLEL', '0') == '1'


# --- Case Loading ---


def load_parity_cases():
    """Load parity cases from YAML file."""
    yaml_path = Path(__file__).parent / 'parity_cases.yaml'
    if not yaml_path.exists():
        pytest.skip(f"Parity cases file not found: {yaml_path}")

    with open(yaml_path, 'r') as f:
        data = yaml.safe_load(f)

    return data.get('cases', [])


# --- Image I/O ---


def read_float_image(path, shape_hint=None):
    """
    Read a raw float binary image.

    Args:
        path: Path to .bin file
        shape_hint: Optional (H, W) tuple for reshaping

    Returns:
        2D numpy array
    """
    data = np.fromfile(path, dtype=np.float32)

    if shape_hint:
        return data.reshape(shape_hint)

    # Try to infer square shape
    size = len(data)
    side = int(np.sqrt(size))
    if side * side == size:
        return data.reshape(side, side)

    raise ValueError(f"Cannot infer shape for {len(data)} pixels (provide shape_hint)")


# --- Metrics ---


def compute_metrics(c_img, py_img, compute_ssim=False):
    """
    Compute comparison metrics between C and PyTorch images.

    Args:
        c_img: C reference image (2D array)
        py_img: PyTorch image (2D array)
        compute_ssim: Whether to compute SSIM (optional)

    Returns:
        dict with keys: correlation, mse, rmse, max_abs_diff, c_sum, py_sum, sum_ratio, [ssim]
    """
    # Flatten for correlation
    c_flat = c_img.flatten()
    py_flat = py_img.flatten()

    # Pearson correlation
    if np.std(c_flat) > 0 and np.std(py_flat) > 0:
        corr, _ = pearsonr(c_flat, py_flat)
    else:
        corr = 0.0

    # MSE and RMSE
    mse = np.mean((c_img - py_img) ** 2)
    rmse = np.sqrt(mse)

    # Max absolute difference
    max_abs_diff = np.max(np.abs(c_img - py_img))

    # Total sums
    c_sum = float(np.sum(c_img))
    py_sum = float(np.sum(py_img))
    sum_ratio = py_sum / c_sum if c_sum != 0 else 0.0

    metrics = {
        'correlation': float(corr),
        'mse': float(mse),
        'rmse': float(rmse),
        'max_abs_diff': float(max_abs_diff),
        'c_sum': c_sum,
        'py_sum': py_sum,
        'sum_ratio': sum_ratio,
    }

    if compute_ssim:
        try:
            from skimage.metrics import structural_similarity as ssim
            ssim_val = ssim(c_img, py_img, data_range=c_img.max() - c_img.min())
            metrics['ssim'] = float(ssim_val)
        except ImportError:
            pass

    return metrics


# --- Artifact Management ---


def create_artifact_dir(case_id):
    """Create dated artifact directory for a case."""
    date_str = datetime.now().strftime('%Y-%m-%d')
    base_dir = Path('reports') / f"{date_str}-{case_id}"
    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir


def save_diff_heatmap(c_img, py_img, output_path):
    """Save a diff heatmap visualization."""
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        diff = np.abs(c_img - py_img)
        log_diff = np.log1p(diff)

        fig, axes = plt.subplots(1, 3, figsize=(15, 5))

        axes[0].imshow(c_img, origin='lower', cmap='viridis')
        axes[0].set_title('C Reference')
        axes[0].axis('off')

        axes[1].imshow(py_img, origin='lower', cmap='viridis')
        axes[1].set_title('PyTorch')
        axes[1].axis('off')

        im = axes[2].imshow(log_diff, origin='lower', cmap='hot')
        axes[2].set_title('log₁₊|Δ|')
        axes[2].axis('off')
        plt.colorbar(im, ax=axes[2])

        plt.tight_layout()
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
    except ImportError:
        pass  # Matplotlib not available


# --- Test Runner ---


def run_binary(binary_cmd, args_list, output_path):
    """
    Run a binary with arguments and capture output.

    Args:
        binary_cmd: Command string (may include spaces)
        args_list: List of argument strings
        output_path: Path for -floatfile output

    Returns:
        (exit_code, stdout, stderr)
    """
    # Split binary_cmd into parts (handles "python -m nanobrag_torch")
    cmd_parts = binary_cmd.split()

    # Build full command
    full_cmd = cmd_parts + args_list + ['-floatfile', str(output_path)]

    # Run
    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, '', 'TIMEOUT'
    except Exception as e:
        return -1, '', str(e)


# --- Pytest Fixtures & Parametrization ---


@pytest.fixture(scope="session")
def c_binary():
    """Session-scoped C binary path."""
    if not is_parallel_enabled():
        pytest.skip("NB_RUN_PARALLEL not set to 1")
    return get_c_binary()


@pytest.fixture(scope="session")
def pytorch_cli():
    """Session-scoped PyTorch CLI command."""
    if not is_parallel_enabled():
        pytest.skip("NB_RUN_PARALLEL not set to 1")
    return get_pytorch_cli()


def pytest_generate_tests(metafunc):
    """Generate test cases from YAML."""
    if 'parity_case' in metafunc.fixturenames:
        cases = load_parity_cases()

        # Flatten cases into (case, run) pairs
        test_params = []
        test_ids = []

        for case in cases:
            case_id = case['id']
            for run in case['runs']:
                test_params.append((case, run))
                test_ids.append(f"{case_id}-{run['name']}")

        metafunc.parametrize('parity_case', test_params, ids=test_ids)


# --- Main Test Function ---


def test_parity_case(parity_case, c_binary, pytorch_cli, request):
    """
    Execute a single parity case run.

    This test:
    1. Runs C binary with combined base_args + extra_args
    2. Runs PyTorch CLI with identical arguments
    3. Loads both float images
    4. Computes metrics (correlation, MSE, RMSE, max_abs_diff, sum_ratio)
    5. Asserts thresholds from YAML
    6. On failure, saves metrics.json and diff artifacts
    """
    case, run = parity_case
    case_id = case['id']
    run_name = run['name']

    # Combine arguments
    base_args = case['base_args'].strip().split()
    extra_args = run['extra_args'].strip().split()
    all_args = base_args + extra_args

    # Get thresholds (case-level or run-level)
    thresholds = run.get('thresholds', case.get('thresholds', {}))

    # Create temp files for outputs
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        c_output = tmpdir / 'c_float.bin'
        py_output = tmpdir / 'py_float.bin'

        # Run C binary
        c_exit, c_stdout, c_stderr = run_binary(c_binary, all_args, c_output)
        assert c_exit == 0, f"C binary failed:\nSTDOUT:\n{c_stdout}\nSTDERR:\n{c_stderr}"
        assert c_output.exists(), f"C binary did not produce {c_output}"

        # Run PyTorch CLI
        py_exit, py_stdout, py_stderr = run_binary(pytorch_cli, all_args, py_output)
        assert py_exit == 0, f"PyTorch CLI failed:\nSTDOUT:\n{py_stdout}\nSTDERR:\n{py_stderr}"
        assert py_output.exists(), f"PyTorch CLI did not produce {py_output}"

        # Infer detector size from args
        detector_size = None
        for i, arg in enumerate(all_args):
            if arg == '-detpixels' and i + 1 < len(all_args):
                try:
                    size = int(all_args[i + 1])
                    detector_size = (size, size)
                except ValueError:
                    pass
                break

        # Load images
        c_img = read_float_image(c_output, detector_size)
        py_img = read_float_image(py_output, detector_size)

        # Check shapes match
        assert c_img.shape == py_img.shape, f"Shape mismatch: C={c_img.shape} vs Py={py_img.shape}"

        # Compute metrics
        metrics = compute_metrics(c_img, py_img, compute_ssim=False)

        # Add metadata
        metrics['case_id'] = case_id
        metrics['run_name'] = run_name
        metrics['args'] = ' '.join(all_args)
        metrics['c_binary'] = c_binary
        metrics['pytorch_cli'] = pytorch_cli
        metrics['timestamp'] = datetime.now().isoformat()

        # Check thresholds
        failures = []

        if 'corr_min' in thresholds:
            if metrics['correlation'] < thresholds['corr_min']:
                failures.append(f"correlation {metrics['correlation']:.6f} < {thresholds['corr_min']}")

        if 'max_abs_max' in thresholds:
            if metrics['max_abs_diff'] > thresholds['max_abs_max']:
                failures.append(f"max_abs_diff {metrics['max_abs_diff']:.2f} > {thresholds['max_abs_max']}")

        if 'sum_ratio_min' in thresholds and 'sum_ratio_max' in thresholds:
            if not (thresholds['sum_ratio_min'] <= metrics['sum_ratio'] <= thresholds['sum_ratio_max']):
                failures.append(f"sum_ratio {metrics['sum_ratio']:.4f} not in [{thresholds['sum_ratio_min']}, {thresholds['sum_ratio_max']}]")

        # If failures, save artifacts
        if failures:
            artifact_dir = create_artifact_dir(case_id)

            # Save metrics
            metrics_path = artifact_dir / f"{run_name}_metrics.json"
            with open(metrics_path, 'w') as f:
                json.dump(metrics, f, indent=2)

            # Save diff heatmap
            heatmap_path = artifact_dir / f"{run_name}_diff.png"
            save_diff_heatmap(c_img, py_img, heatmap_path)

            # Save images
            np.save(artifact_dir / f"{run_name}_c.npy", c_img)
            np.save(artifact_dir / f"{run_name}_py.npy", py_img)

            # Construct failure message
            msg = f"\nParity test failed for {case_id} / {run_name}:\n"
            msg += "\n".join(f"  - {f}" for f in failures)
            msg += f"\n\nMetrics: corr={metrics['correlation']:.6f}, RMSE={metrics['rmse']:.2f}, max|Δ|={metrics['max_abs_diff']:.2f}, sum_ratio={metrics['sum_ratio']:.4f}"
            msg += f"\n\nArtifacts saved to: {artifact_dir}"
            msg += f"\n  - {metrics_path.name}"
            msg += f"\n  - {heatmap_path.name}"

            pytest.fail(msg)

        # Success: print summary
        print(f"\n{case_id}/{run_name}: PASS (corr={metrics['correlation']:.6f}, RMSE={metrics['rmse']:.2f}, max|Δ|={metrics['max_abs_diff']:.2f}, sum_ratio={metrics['sum_ratio']:.4f})")
"""Tests for benchmark_probabilistic CLI functionality.

Validates scenario resolution, flag precedence, and dry-run mode.
"""

import pytest
import sys
import json
from pathlib import Path
from argparse import Namespace

# Add scripts to path for import
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "scripts"))


def test_scenario_override_defaults():
    """resolve_scenario with --scenario hi_res_a produces expected values."""
    from benchmark_probabilistic import resolve_scenario
    args = Namespace(
        scenario="hi_res_a",
        cell_edge=None,
        wavelength=None,
        distance=None,
        pixel_size=None,
        fpixels=None,
        spixels=None,
    )
    s = resolve_scenario(args)
    assert s.cell_edge_A == 40.0
    assert s.wavelength_A == 0.65
    assert s.fpixels == 96


def test_cli_flag_precedence():
    """Explicit --distance overrides --scenario."""
    from benchmark_probabilistic import resolve_scenario
    args = Namespace(
        scenario="hi_res_a",
        cell_edge=None,
        wavelength=None,
        distance=200.0,
        pixel_size=None,
        fpixels=None,
        spixels=None,
    )
    s = resolve_scenario(args)
    assert s.distance_mm == 200.0
    assert s.cell_edge_A == 40.0  # from scenario


def test_default_scenario_when_none():
    """No --scenario uses default preset."""
    from benchmark_probabilistic import resolve_scenario
    args = Namespace(
        scenario=None,
        cell_edge=None,
        wavelength=None,
        distance=None,
        pixel_size=None,
        fpixels=None,
        spixels=None,
    )
    s = resolve_scenario(args)
    assert s.cell_edge_A == 100.0
    assert s.fpixels == 64


def test_dry_run(tmp_path):
    """--dry-run prints scenario JSON and exits."""
    import subprocess

    result = subprocess.run(
        [
            sys.executable,
            str(
                Path(__file__).resolve().parent.parent.parent
                / "scripts"
                / "benchmark_probabilistic.py"
            ),
            "--dry-run",
            "--scenario",
            "hi_res_b",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    # Should contain scenario info
    assert "hi_res_b" in result.stdout or "128" in result.stdout

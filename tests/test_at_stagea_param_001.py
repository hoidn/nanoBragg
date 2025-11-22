"""
AT-STAGEA-PARAM-001: Nucleus test for Stage-A parameterized experiment.

This test validates that introducing Stage-A parameter ownership in "frozen"
mode (parameters initialized to match the config values) does not change the
Simulator output for a small ROI, and that gradients flow through at least one
Stage-A degree of freedom.
"""

import torch

from src.nanobrag_torch.config import (
    BeamConfig,
    CrystalConfig,
    DetectorConfig,
    DetectorConvention,
    DetectorPivot,
)
from src.nanobrag_torch.models.crystal import Crystal
from src.nanobrag_torch.models.detector import Detector
from src.nanobrag_torch.models.experiment import ExperimentModel
from src.nanobrag_torch.simulator import Simulator


def _make_simple_configs():
    """Helper: simple cubic-style configs with a small ROI."""
    crystal_cfg = CrystalConfig(
        cell_a=100.0,
        cell_b=100.0,
        cell_c=100.0,
        cell_alpha=90.0,
        cell_beta=90.0,
        cell_gamma=90.0,
        N_cells=(5, 5, 5),
        default_F=100.0,
    )
    detector_cfg = DetectorConfig(
        distance_mm=100.0,
        pixel_size_mm=0.1,
        spixels=64,
        fpixels=64,
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.BEAM,
        roi_xmin=16,
        roi_xmax=47,
        roi_ymin=16,
        roi_ymax=47,
    )
    beam_cfg = BeamConfig(
        wavelength_A=6.2,
        fluence=1.0e12,
        beamsize_mm=1.0,
    )
    return crystal_cfg, detector_cfg, beam_cfg


def test_stagea_frozen_matches_config_path():
    """Frozen Stage-A wrapper must reproduce the legacy config-driven path."""
    device = torch.device("cpu")
    dtype = torch.float32

    crystal_cfg, detector_cfg, beam_cfg = _make_simple_configs()

    # Legacy config-driven path.
    crystal = Crystal(crystal_cfg, device=device, dtype=dtype)
    detector = Detector(detector_cfg, device=device, dtype=dtype)
    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        beam_config=beam_cfg,
        device=device,
        dtype=dtype,
    )
    baseline = simulator.run()

    # Stage-A wrapper in "frozen" mode (no learnable parameters).
    experiment = ExperimentModel(
        crystal_config=crystal_cfg,
        detector_config=detector_cfg,
        beam_config=beam_cfg,
        device=device,
        dtype=dtype,
        param_init="frozen",
    )
    assert sum(1 for _ in experiment.parameters()) == 0

    wrapped = experiment()

    assert baseline.shape == wrapped.shape
    assert torch.allclose(baseline, wrapped, rtol=1e-6, atol=1e-6)


def test_stagea_stage_a_grad_flow():
    """Gradients must flow through at least one Stage-A parameter."""
    device = torch.device("cpu")
    dtype = torch.float64  # more stable gradients

    crystal_cfg, detector_cfg, beam_cfg = _make_simple_configs()

    experiment = ExperimentModel(
        crystal_config=crystal_cfg,
        detector_config=detector_cfg,
        beam_config=beam_cfg,
        device=device,
        dtype=dtype,
        param_init="stage_a",
    )

    # Simple scalar loss: mean intensity over the ROI.
    image = experiment()
    loss = image.mean()
    loss.backward()

    # Check that at least one crystal Stage-A parameter received gradients.
    grads = [
        experiment.crystal_params.delta_log_a.grad,
        experiment.crystal_params.delta_log_b.grad,
        experiment.crystal_params.delta_log_c.grad,
    ]
    assert any(g is not None for g in grads), "Expected gradients on Stage-A crystal parameters"


def test_stagea_external_hkl_grid_hook():
    """ExperimentModel should accept an external HKL grid via the public hook."""
    device = torch.device("cpu")
    dtype = torch.float32

    crystal_cfg, detector_cfg, beam_cfg = _make_simple_configs()

    # Build a tiny synthetic HKL grid with metadata.
    # h,k,l in [-1, 0, 1] → shape (3,3,3)
    F_grid = torch.ones((3, 3, 3), dtype=dtype)
    metadata = {
        "h_min": -1,
        "h_max": 1,
        "k_min": -1,
        "k_max": 1,
        "l_min": -1,
        "l_max": 1,
    }

    experiment = ExperimentModel(
        crystal_config=crystal_cfg,
        detector_config=detector_cfg,
        beam_config=beam_cfg,
        device=device,
        dtype=dtype,
        param_init="frozen",
    )

    # Use the public hook to supply the grid.
    experiment.set_structure_factors(F_grid, metadata)

    # Internal helper should wire the grid into the Crystal instance on the
    # correct device/dtype.
    simulator, crystal, detector, beam_cfg_out = experiment._build_simulator()

    assert crystal.hkl_data is not None
    assert crystal.hkl_data.shape == F_grid.shape
    assert crystal.hkl_data.device == device
    assert crystal.hkl_data.dtype == dtype
    assert crystal.hkl_metadata == metadata

    # A forward run should succeed using the external grid.
    image = simulator.run()
    assert image.ndim == 2

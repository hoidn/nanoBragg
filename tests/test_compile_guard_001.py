#!/usr/bin/env python3
"""Tests for Simulator compile guard behavior (COMPILE-GUARD-001).

These tests verify that the Simulator honours the compile-disable environment
variables and wires _compiled_compute_physics correctly.
"""

import os

import pytest
import torch

from nanobrag_torch.config import BeamConfig, CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.simulator import Simulator, compute_physics_for_position


def _make_minimal_simulator():
    """Construct a minimal Simulator instance on CPU for wiring tests."""
    device = torch.device("cpu")
    dtype = torch.float32

    crystal_config = CrystalConfig()
    beam_config = BeamConfig()

    crystal = Crystal(config=crystal_config, device=device, dtype=dtype)
    detector = Detector(device=device, dtype=dtype)

    simulator = Simulator(
        crystal=crystal,
        detector=detector,
        crystal_config=crystal_config,
        beam_config=beam_config,
        device=device,
        dtype=dtype,
    )
    return simulator


def test_simulator_uses_eager_path_when_compile_disabled(monkeypatch):
    """Simulator should not call torch.compile when compile is disabled via env."""
    # Ensure both spellings are treated as disabled; use the DBEX spelling here.
    monkeypatch.setenv("NANOBRAG_DISABLE_COMPILE", "1")
    monkeypatch.delenv("NANOBRAGG_DISABLE_COMPILE", raising=False)

    # If torch.compile were called, raise to catch regressions in the guard.
    from nanobrag_torch import simulator as simulator_module

    def _fail_compile(*args, **kwargs):  # pragma: no cover - should never be hit
        raise AssertionError("torch.compile was called despite disable flag")

    monkeypatch.setattr(simulator_module.torch, "compile", _fail_compile, raising=True)

    simulator = _make_minimal_simulator()

    # With compile disabled, the Simulator should use the raw function
    assert simulator._compiled_compute_physics is compute_physics_for_position


def test_simulator_attempts_compile_when_not_disabled(monkeypatch):
    """Simulator should route through torch.compile when no disable flag is set."""
    # Clear any disable flags
    monkeypatch.delenv("NANOBRAG_DISABLE_COMPILE", raising=False)
    monkeypatch.delenv("NANOBRAGG_DISABLE_COMPILE", raising=False)

    # Patch torch.compile in the simulator module's namespace
    from nanobrag_torch import simulator as simulator_module

    compile_calls = {"called": False}

    def _fake_compile(*args, **kwargs):
        """Mock torch.compile that returns a decorator."""
        compile_calls["called"] = True

        def _decorator(fn):
            """The decorator returned by torch.compile."""
            def _wrapped(*fn_args, **fn_kwargs):
                return fn(*fn_args, **fn_kwargs)
            return _wrapped

        return _decorator

    monkeypatch.setattr(simulator_module.torch, "compile", _fake_compile, raising=True)

    simulator = _make_minimal_simulator()

    # Simulator.__init__ should have invoked torch.compile once
    assert compile_calls["called"] is True
    # And the compiled function should not be the raw function object
    assert simulator._compiled_compute_physics is not compute_physics_for_position


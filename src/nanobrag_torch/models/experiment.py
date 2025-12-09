"""
Stage-A parameterized experiment model.

This module implements thin nn.Module wrappers around the existing config-driven
Crystal, Detector, and Beam models.  It exposes optimizer-friendly raw
parameters while delegating all physics and geometry to the core components.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Optional

import torch
from torch import nn

from ..config import BeamConfig, CrystalConfig, DetectorConfig
from ..models.crystal import Crystal
from ..models.detector import Detector


class CrystalStageAParams(nn.Module):
    """Stage-A learnable parameterization for crystal geometry."""

    def __init__(
        self,
        base_config: CrystalConfig,
        device: Optional[torch.device] = None,
        dtype: torch.dtype = torch.float32,
        param_init: str = "frozen",
        max_angle_delta_deg: float = 10.0,
        max_misset_delta_deg: float = 10.0,
    ) -> None:
        super().__init__()
        if device is None:
            device = torch.device("cpu")
        self.device = device
        self.dtype = dtype
        self.max_angle_delta_deg = float(max_angle_delta_deg)
        self.max_misset_delta_deg = float(max_misset_delta_deg)

        # Store an immutable copy of the base config for defaults/non-learnable fields.
        # Use dataclasses.replace to avoid sharing accidental mutable state.
        self._base_config = replace(base_config)

        # Base cell parameters as buffers (Å, degrees).
        self.register_buffer(
            "base_cell_a",
            torch.as_tensor(base_config.cell_a, device=self.device, dtype=self.dtype),
        )
        self.register_buffer(
            "base_cell_b",
            torch.as_tensor(base_config.cell_b, device=self.device, dtype=self.dtype),
        )
        self.register_buffer(
            "base_cell_c",
            torch.as_tensor(base_config.cell_c, device=self.device, dtype=self.dtype),
        )
        self.register_buffer(
            "base_cell_alpha",
            torch.as_tensor(
                base_config.cell_alpha, device=self.device, dtype=self.dtype
            ),
        )
        self.register_buffer(
            "base_cell_beta",
            torch.as_tensor(
                base_config.cell_beta, device=self.device, dtype=self.dtype
            ),
        )
        self.register_buffer(
            "base_cell_gamma",
            torch.as_tensor(
                base_config.cell_gamma, device=self.device, dtype=self.dtype
            ),
        )

        # Base misset angles (degrees).
        m0x, m0y, m0z = base_config.misset_deg
        self.register_buffer(
            "base_misset_x",
            torch.as_tensor(m0x, device=self.device, dtype=self.dtype),
        )
        self.register_buffer(
            "base_misset_y",
            torch.as_tensor(m0y, device=self.device, dtype=self.dtype),
        )
        self.register_buffer(
            "base_misset_z",
            torch.as_tensor(m0z, device=self.device, dtype=self.dtype),
        )

        learnable = param_init == "stage_a"
        param_cls = nn.Parameter if learnable else lambda x: x

        # Log-length deltas (unconstrained, start at zero).
        self.delta_log_a = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )
        self.delta_log_b = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )
        self.delta_log_c = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )

        # Bounded angle deltas (raw).
        self.delta_alpha_raw = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )
        self.delta_beta_raw = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )
        self.delta_gamma_raw = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )

        # Bounded misset deltas (raw 3-vector).
        self.delta_misset_raw = param_cls(
            torch.zeros((3,), device=self.device, dtype=self.dtype)
        )

    def build_config(self) -> CrystalConfig:
        """Return a CrystalConfig with physical values derived from raw parameters."""
        # Exponentiate log-length deltas to maintain positivity.
        cell_a = self.base_cell_a * torch.exp(self.delta_log_a)
        cell_b = self.base_cell_b * torch.exp(self.delta_log_b)
        cell_c = self.base_cell_c * torch.exp(self.delta_log_c)

        # Bounded angle deltas using tanh window.
        max_angle = self.max_angle_delta_deg
        cell_alpha = self.base_cell_alpha + max_angle * torch.tanh(self.delta_alpha_raw)
        cell_beta = self.base_cell_beta + max_angle * torch.tanh(self.delta_beta_raw)
        cell_gamma = self.base_cell_gamma + max_angle * torch.tanh(self.delta_gamma_raw)

        # Bounded misset deltas.
        max_misset = self.max_misset_delta_deg
        delta_misset = max_misset * torch.tanh(self.delta_misset_raw)
        misset_x = self.base_misset_x + delta_misset[0]
        misset_y = self.base_misset_y + delta_misset[1]
        misset_z = self.base_misset_z + delta_misset[2]

        # Create a fresh config clone and overwrite the learnable fields.
        cfg = replace(self._base_config)
        cfg.cell_a = cell_a
        cfg.cell_b = cell_b
        cfg.cell_c = cell_c
        cfg.cell_alpha = cell_alpha
        cfg.cell_beta = cell_beta
        cfg.cell_gamma = cell_gamma
        cfg.misset_deg = (misset_x, misset_y, misset_z)
        return cfg


class DetectorStageAParams(nn.Module):
    """Stage-A learnable parameterization for detector geometry."""

    def __init__(
        self,
        base_config: DetectorConfig,
        device: Optional[torch.device] = None,
        dtype: torch.dtype = torch.float32,
        param_init: str = "frozen",
        max_tilt_delta_deg: float = 5.0,
        beam_shift_pixels: float = 5.0,
    ) -> None:
        super().__init__()
        if device is None:
            device = torch.device("cpu")
        self.device = device
        self.dtype = dtype
        self.max_tilt_delta_deg = float(max_tilt_delta_deg)
        self.beam_shift_pixels = float(beam_shift_pixels)

        self._base_config = replace(base_config)

        # Base distance and angles.
        self.register_buffer(
            "base_distance_mm",
            torch.as_tensor(base_config.distance_mm, device=self.device, dtype=self.dtype),
        )
        self.register_buffer(
            "base_rotx_deg",
            torch.as_tensor(base_config.detector_rotx_deg, device=self.device, dtype=self.dtype),
        )
        self.register_buffer(
            "base_roty_deg",
            torch.as_tensor(base_config.detector_roty_deg, device=self.device, dtype=self.dtype),
        )
        self.register_buffer(
            "base_rotz_deg",
            torch.as_tensor(base_config.detector_rotz_deg, device=self.device, dtype=self.dtype),
        )
        self.register_buffer(
            "base_twotheta_deg",
            torch.as_tensor(base_config.detector_twotheta_deg, device=self.device, dtype=self.dtype),
        )

        # Base beam-center in mm (after DetectorConfig defaults).
        beam_s = base_config.beam_center_s
        beam_f = base_config.beam_center_f
        self.register_buffer(
            "base_beam_center_s_mm",
            torch.as_tensor(beam_s, device=self.device, dtype=self.dtype),
        )
        self.register_buffer(
            "base_beam_center_f_mm",
            torch.as_tensor(beam_f, device=self.device, dtype=self.dtype),
        )
        self.register_buffer(
            "pixel_size_mm",
            torch.as_tensor(base_config.pixel_size_mm, device=self.device, dtype=self.dtype),
        )

        learnable = param_init == "stage_a"
        param_cls = nn.Parameter if learnable else lambda x: x

        # Log-distance delta.
        self.delta_log_distance_mm = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )

        # Bounded tilt and twotheta deltas.
        self.delta_rotx_raw = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )
        self.delta_roty_raw = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )
        self.delta_rotz_raw = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )
        self.delta_twotheta_raw = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )

        # Beam-center deltas in pixel units (coarse centering).
        self.delta_beam_s_raw = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )
        self.delta_beam_f_raw = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )

    def build_config(self) -> DetectorConfig:
        """Return a DetectorConfig with physical values derived from raw parameters."""
        # Distance (mm, positive).
        distance_mm = self.base_distance_mm * torch.exp(self.delta_log_distance_mm)

        # Bounded small-angle tilts.
        max_tilt = self.max_tilt_delta_deg
        rotx = self.base_rotx_deg + max_tilt * torch.tanh(self.delta_rotx_raw)
        roty = self.base_roty_deg + max_tilt * torch.tanh(self.delta_roty_raw)
        rotz = self.base_rotz_deg + max_tilt * torch.tanh(self.delta_rotz_raw)
        twotheta = self.base_twotheta_deg + max_tilt * torch.tanh(self.delta_twotheta_raw)

        # Beam-center deltas in mm via pixel-size scaling.
        max_shift_mm = self.beam_shift_pixels * self.pixel_size_mm
        beam_delta_s_mm = max_shift_mm * torch.tanh(self.delta_beam_s_raw)
        beam_delta_f_mm = max_shift_mm * torch.tanh(self.delta_beam_f_raw)

        beam_center_s = self.base_beam_center_s_mm + beam_delta_s_mm
        beam_center_f = self.base_beam_center_f_mm + beam_delta_f_mm

        cfg = replace(self._base_config)
        cfg.distance_mm = distance_mm
        cfg.detector_rotx_deg = rotx
        cfg.detector_roty_deg = roty
        cfg.detector_rotz_deg = rotz
        cfg.detector_twotheta_deg = twotheta
        cfg.beam_center_s = beam_center_s
        cfg.beam_center_f = beam_center_f
        return cfg


class BeamStageAParams(nn.Module):
    """Stage-A learnable parameterization for beam fluence."""

    def __init__(
        self,
        base_config: BeamConfig,
        device: Optional[torch.device] = None,
        dtype: torch.dtype = torch.float32,
        param_init: str = "frozen",
    ) -> None:
        super().__init__()
        if device is None:
            device = torch.device("cpu")
        self.device = device
        self.dtype = dtype
        self._base_config = replace(base_config)

        self.register_buffer(
            "base_fluence",
            torch.as_tensor(base_config.fluence, device=self.device, dtype=self.dtype),
        )

        learnable = param_init == "stage_a"
        param_cls = nn.Parameter if learnable else lambda x: x

        self.delta_log_fluence = param_cls(
            torch.zeros((), device=self.device, dtype=self.dtype)
        )

    def build_config(self) -> BeamConfig:
        """Return a BeamConfig with physical values derived from raw parameters."""
        fluence = self.base_fluence * torch.exp(self.delta_log_fluence)

        cfg = replace(self._base_config)
        cfg.fluence = fluence
        return cfg


class ExperimentModel(nn.Module):
    """
    High-level experiment composition model for Stage-A optimization.

    Owns parameter wrappers for crystal, detector, and beam, and delegates
    physics to the existing Simulator.
    """

    def __init__(
        self,
        crystal_config: CrystalConfig,
        detector_config: DetectorConfig,
        beam_config: BeamConfig,
        device: Optional[torch.device] = None,
        dtype: torch.dtype = torch.float32,
        param_init: str = "frozen",
        hkl_data: Optional[torch.Tensor] = None,
        hkl_metadata: Optional[dict] = None,
    ) -> None:
        super().__init__()
        if device is None:
            device = torch.device("cpu")
        self.device = device
        self.dtype = dtype

        # Stage-A parameter blocks.
        self.crystal_params = CrystalStageAParams(
            base_config=crystal_config,
            device=self.device,
            dtype=self.dtype,
            param_init=param_init,
        )
        self.detector_params = DetectorStageAParams(
            base_config=detector_config,
            device=self.device,
            dtype=self.dtype,
            param_init=param_init,
        )
        self.beam_params = BeamStageAParams(
            base_config=beam_config,
            device=self.device,
            dtype=self.dtype,
            param_init=param_init,
        )

        # Optional externally-provided structure factors (dense HKL grid).
        # Downstream projects (e.g. dbex) can populate these either via the
        # constructor or via set_structure_factors() below.
        self._external_hkl_data: Optional[torch.Tensor] = hkl_data
        self._external_hkl_metadata: Optional[dict] = hkl_metadata

    def set_structure_factors(
        self, hkl_data: torch.Tensor, hkl_metadata: dict
    ) -> None:
        """
        Override structure factors with an external dense HKL grid.

        Args:
            hkl_data:
                Dense HKL grid as a tensor (e.g. shape [H, K, L]) on any
                device/dtype. The ExperimentModel will move it to its own
                device/dtype before use.
            hkl_metadata:
                Dictionary containing at least the integer bounds:
                'h_min', 'h_max', 'k_min', 'k_max', 'l_min', 'l_max'.

        This is the supported hook for downstream projects that build their
        own P1 grids and want ExperimentModel to reuse them, rather than
        loading HKL files internally via Crystal.load_hkl().
        """
        self._external_hkl_data = hkl_data
        self._external_hkl_metadata = hkl_metadata

    def _build_simulator(self):
        """
        Internal helper to build Crystal/Detector/Simulator for the current parameters.

        Returns:
            (simulator, crystal, detector, beam_config)

        Note: This is primarily intended for tests and tooling; callers should
        prefer ExperimentModel.forward() for normal use.
        """
        # Build configs from raw parameters.
        crystal_cfg = self.crystal_params.build_config()
        detector_cfg = self.detector_params.build_config()
        beam_cfg = self.beam_params.build_config()

        # Instantiate core models on the requested device/dtype.
        crystal = Crystal(
            config=crystal_cfg,
            beam_config=beam_cfg,
            device=self.device,
            dtype=self.dtype,
        )

        # Apply external HKL grid if provided.
        if self._external_hkl_data is not None:
            if isinstance(self._external_hkl_data, torch.Tensor):
                hkl_tensor = self._external_hkl_data
            else:
                hkl_tensor = torch.as_tensor(self._external_hkl_data)
            crystal.hkl_data = hkl_tensor.to(
                device=self.device,
                dtype=self.dtype,
            )
            crystal.hkl_metadata = (
                dict(self._external_hkl_metadata)
                if self._external_hkl_metadata is not None
                else None
            )

        detector = Detector(
            config=detector_cfg,
            device=self.device,
            dtype=self.dtype,
        )

        # Import Simulator lazily here to avoid circular imports at module load
        # time (Simulator imports models.crystal / models.detector).
        from ..simulator import Simulator

        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            beam_config=beam_cfg,
            device=self.device,
            dtype=self.dtype,
        )

        return simulator, crystal, detector, beam_cfg

    def forward(
        self,
        pixel_batch_size: Optional[int] = None,
        oversample: Optional[int] = None,
        oversample_omega: Optional[bool] = None,
        oversample_polar: Optional[bool] = None,
        oversample_thick: Optional[bool] = None,
    ) -> torch.Tensor:
        """
        Run the diffraction simulation for the current parameter values.

        Returns:
            Float image tensor with shape (spixels, fpixels).
        """
        simulator, _, _, _ = self._build_simulator()

        return simulator.run(
            pixel_batch_size=pixel_batch_size,
            oversample=oversample,
            oversample_omega=oversample_omega,
            oversample_polar=oversample_polar,
            oversample_thick=oversample_thick,
        )

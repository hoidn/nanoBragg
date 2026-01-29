"""
Probabilistic Simulator — analytic mosaic broadening kernel.

Replaces Monte Carlo mosaic-domain sampling with a closed-form Gaussian
envelope in reciprocal space, yielding O(1) cost independent of mosaic spread
and smooth, noise-free gradients.

Design reference: docs/plans/2026-01-29-probabilistic-simulator-design.md
Strategy reference: docs/strategy/mainstrategy.md §§2–4
"""

from typing import Optional, Union, Tuple

import torch

from ..config import BeamConfig, CrystalConfig, CrystalShape
from ..models.crystal import Crystal
from ..models.detector import Detector
from ..simulator import Simulator, compute_physics_for_position
from ..utils.geometry import dot_product
from ..utils.physics import sincg, sinc3, polarization_factor


def compute_probabilistic_physics(
    # Geometry inputs
    pixel_coords_angstroms: torch.Tensor,
    rot_a: torch.Tensor,
    rot_b: torch.Tensor,
    rot_c: torch.Tensor,
    rot_a_star: torch.Tensor,
    rot_b_star: torch.Tensor,
    rot_c_star: torch.Tensor,
    # Beam parameters
    incident_beam_direction: torch.Tensor,
    wavelength: torch.Tensor,
    source_weights: Optional[torch.Tensor] = None,
    # Beam configuration (dmin culling)
    dmin: float = 0.0,
    # Crystal structure factor function
    crystal_get_structure_factor=None,
    # Crystal parameters for lattice factor
    N_cells_a: int = 0,
    N_cells_b: int = 0,
    N_cells_c: int = 0,
    crystal_shape: CrystalShape = CrystalShape.SQUARE,
    crystal_fudge: float = 1.0,
    # Polarization parameters
    apply_polarization: bool = True,
    kahn_factor: float = 1.0,
    polarization_axis: Optional[torch.Tensor] = None,
    # Probabilistic-specific
    mosaic_spread_rad: Optional[torch.Tensor] = None,
    eps: float = 1e-12,
) -> torch.Tensor:
    """Analytic probabilistic physics kernel.

    Mirrors the baseline ``compute_physics_for_position`` but replaces the
    discrete mosaic-domain summation with a Gaussian envelope whose width
    scales with |q| × tan(mosaic_spread).

    The mosaic envelope is applied multiplicatively to the lattice-factor
    intensity so that the existing structure-factor and polarization logic
    is reused verbatim.

    Design reference: docs/plans/2026-01-29-probabilistic-simulator-design.md §Probabilistic Physics Kernel
    Strategy anchor: docs/strategy/mainstrategy.md §3B (Angular Broadening)
    """
    # --- Detect multi-source ---
    is_multi_source = incident_beam_direction.dim() == 2
    n_sources = incident_beam_direction.shape[0] if is_multi_source else 1
    original_n_dims = pixel_coords_angstroms.dim()

    # --- Scattering vector (same as baseline) ---
    pixel_squared_sum = torch.sum(
        pixel_coords_angstroms * pixel_coords_angstroms, dim=-1, keepdim=True
    ).clamp_min(1e-12)
    pixel_magnitudes = torch.sqrt(pixel_squared_sum)
    diffracted_beam_unit = pixel_coords_angstroms / pixel_magnitudes

    if is_multi_source:
        diffracted_expanded = diffracted_beam_unit.unsqueeze(0)
        if original_n_dims == 2:
            incident_expanded = incident_beam_direction.view(n_sources, 1, 3)
        else:
            incident_expanded = incident_beam_direction.view(n_sources, 1, 1, 3)
        incident_beam_unit = incident_expanded.expand(n_sources, *diffracted_beam_unit.shape)
        diffracted_beam_unit = diffracted_expanded.expand_as(incident_beam_unit)
    else:
        incident_beam_unit = incident_beam_direction.expand_as(diffracted_beam_unit)

    # Wavelength broadcasting
    if is_multi_source:
        if wavelength.dim() == 1:
            if original_n_dims == 2:
                wavelength = wavelength.view(n_sources, 1, 1)
            else:
                wavelength = wavelength.view(n_sources, 1, 1, 1)

    wavelength_meters = wavelength * 1e-10
    scattering_vector = (diffracted_beam_unit - incident_beam_unit) / wavelength_meters

    # dmin culling
    dmin_mask = None
    if dmin is not None and dmin > 0:
        stol = 0.5 * torch.norm(scattering_vector, dim=-1)
        stol_threshold = 0.5 / dmin
        dmin_mask = (stol > 0) & (stol > stol_threshold)

    # --- Miller indices ---
    if is_multi_source:
        scattering_broadcast = scattering_vector.unsqueeze(-2).unsqueeze(-2)
        if original_n_dims == 2:
            rot_a_broadcast = rot_a.unsqueeze(0).unsqueeze(0)
            rot_b_broadcast = rot_b.unsqueeze(0).unsqueeze(0)
            rot_c_broadcast = rot_c.unsqueeze(0).unsqueeze(0)
        else:
            rot_a_broadcast = rot_a.unsqueeze(0).unsqueeze(0).unsqueeze(0)
            rot_b_broadcast = rot_b.unsqueeze(0).unsqueeze(0).unsqueeze(0)
            rot_c_broadcast = rot_c.unsqueeze(0).unsqueeze(0).unsqueeze(0)
    else:
        scattering_broadcast = scattering_vector.unsqueeze(-2).unsqueeze(-2)
        rot_a_broadcast = rot_a.unsqueeze(0).unsqueeze(0)
        rot_b_broadcast = rot_b.unsqueeze(0).unsqueeze(0)
        rot_c_broadcast = rot_c.unsqueeze(0).unsqueeze(0)

    h = dot_product(scattering_broadcast, rot_a_broadcast)
    k = dot_product(scattering_broadcast, rot_b_broadcast)
    l = dot_product(scattering_broadcast, rot_c_broadcast)  # noqa: E741

    h0 = torch.round(h)
    k0 = torch.round(k)
    l0 = torch.round(l)

    F_cell = crystal_get_structure_factor(h0, k0, l0)
    if F_cell.device != h.device:
        F_cell = F_cell.to(device=h.device)

    # --- Lattice factor (same as baseline) ---
    Na, Nb, Nc = N_cells_a, N_cells_b, N_cells_c
    shape = crystal_shape
    fudge = crystal_fudge

    if shape == CrystalShape.SQUARE:
        F_latt = sincg(torch.pi * h, Na) * sincg(torch.pi * k, Nb) * sincg(torch.pi * l, Nc)
    elif shape == CrystalShape.ROUND:
        h_frac = h - h0
        k_frac = k - k0
        l_frac = l - l0
        hrad_sqr = (h_frac * h_frac * Na * Na +
                    k_frac * k_frac * Nb * Nb +
                    l_frac * l_frac * Nc * Nc).clamp_min(1e-12)
        F_latt = Na * Nb * Nc * 0.723601254558268 * sinc3(
            torch.pi * torch.sqrt(hrad_sqr * fudge)
        )
    elif shape == CrystalShape.GAUSS:
        h_frac = h - h0
        k_frac = k - k0
        l_frac = l - l0
        if is_multi_source:
            delta_r_star = (h_frac.unsqueeze(-1) * rot_a_star.unsqueeze(0).unsqueeze(0).unsqueeze(0) +
                            k_frac.unsqueeze(-1) * rot_b_star.unsqueeze(0).unsqueeze(0).unsqueeze(0) +
                            l_frac.unsqueeze(-1) * rot_c_star.unsqueeze(0).unsqueeze(0).unsqueeze(0))
        else:
            delta_r_star = (h_frac.unsqueeze(-1) * rot_a_star.unsqueeze(0).unsqueeze(0) +
                            k_frac.unsqueeze(-1) * rot_b_star.unsqueeze(0).unsqueeze(0) +
                            l_frac.unsqueeze(-1) * rot_c_star.unsqueeze(0).unsqueeze(0))
        rad_star_sqr = torch.sum(delta_r_star * delta_r_star, dim=-1)
        rad_star_sqr = rad_star_sqr * Na * Na * Nb * Nb * Nc * Nc
        F_latt = Na * Nb * Nc * torch.exp(-(rad_star_sqr / 0.63) * fudge)
    elif shape == CrystalShape.TOPHAT:
        h_frac = h - h0
        k_frac = k - k0
        l_frac = l - l0
        if is_multi_source:
            delta_r_star = (h_frac.unsqueeze(-1) * rot_a_star.unsqueeze(0).unsqueeze(0).unsqueeze(0) +
                            k_frac.unsqueeze(-1) * rot_b_star.unsqueeze(0).unsqueeze(0).unsqueeze(0) +
                            l_frac.unsqueeze(-1) * rot_c_star.unsqueeze(0).unsqueeze(0).unsqueeze(0))
        else:
            delta_r_star = (h_frac.unsqueeze(-1) * rot_a_star.unsqueeze(0).unsqueeze(0) +
                            k_frac.unsqueeze(-1) * rot_b_star.unsqueeze(0).unsqueeze(0) +
                            l_frac.unsqueeze(-1) * rot_c_star.unsqueeze(0).unsqueeze(0))
        rad_star_sqr = torch.sum(delta_r_star * delta_r_star, dim=-1)
        rad_star_sqr = rad_star_sqr * Na * Na * Nb * Nb * Nc * Nc
        inside_cutoff = (rad_star_sqr * fudge) < 0.3969
        F_latt = torch.where(inside_cutoff,
                             torch.full_like(rad_star_sqr, Na * Nb * Nc),
                             torch.zeros_like(rad_star_sqr))
    else:
        raise ValueError(f"Unsupported crystal shape: {shape}")

    # --- Analytic mosaic envelope (THE NEW PART) ---
    # Per design doc: sigma = |q| * tan(mosaic_spread_rad) + eps
    # dQ = dh*a* + dk*b* + dl*c*  (full metric geometry)
    # G = exp(-|dQ|^2 / (2*sigma^2))
    h_frac = h - h0
    k_frac = k - k0
    l_frac = l - l0

    # Build dQ in reciprocal space using rotated reciprocal vectors
    # rot_*_star shape: (N_phi, N_mos, 3)
    if is_multi_source:
        a_star_bcast = rot_a_star.unsqueeze(0).unsqueeze(0).unsqueeze(0)
        b_star_bcast = rot_b_star.unsqueeze(0).unsqueeze(0).unsqueeze(0)
        c_star_bcast = rot_c_star.unsqueeze(0).unsqueeze(0).unsqueeze(0)
    else:
        a_star_bcast = rot_a_star.unsqueeze(0).unsqueeze(0)
        b_star_bcast = rot_b_star.unsqueeze(0).unsqueeze(0)
        c_star_bcast = rot_c_star.unsqueeze(0).unsqueeze(0)

    # dQ: (..., N_phi, N_mos, 3)
    dQ = (h_frac.unsqueeze(-1) * a_star_bcast +
          k_frac.unsqueeze(-1) * b_star_bcast +
          l_frac.unsqueeze(-1) * c_star_bcast)
    dr2 = torch.sum(dQ * dQ, dim=-1)  # (..., N_phi, N_mos)

    # q_norm from scattering vector (in m^-1) — collapse to pixel dims
    q_norm = torch.norm(scattering_vector, dim=-1)  # (..., spatial)
    # Expand q_norm to match phi/mos dims
    q_norm_expanded = q_norm.unsqueeze(-1).unsqueeze(-1)  # (..., 1, 1)

    spread = mosaic_spread_rad.clamp_min(1e-8) if mosaic_spread_rad is not None else torch.tensor(1e-8, device=h.device, dtype=h.dtype)
    sigma = q_norm_expanded * torch.tan(spread) + eps

    gaussian_envelope = torch.exp(-dr2 / (2.0 * sigma * sigma))

    # --- Intensity ---
    F_total = F_cell * F_latt
    intensity = F_total * F_total * gaussian_envelope

    # dmin culling
    if dmin_mask is not None:
        keep_mask = (~dmin_mask.unsqueeze(-1).unsqueeze(-1)).to(intensity.dtype)
        intensity = intensity * keep_mask

    # Sum over phi and mosaic
    intensity = torch.sum(intensity, dim=(-2, -1))

    intensity_pre_polar = intensity.clone() if apply_polarization else None

    # --- Polarization (same as baseline) ---
    if apply_polarization:
        pixel_magnitudes_pol = torch.norm(pixel_coords_angstroms, dim=-1, keepdim=True).clamp_min(1e-12)
        diffracted_unit_pol = pixel_coords_angstroms / pixel_magnitudes_pol

        if is_multi_source:
            if original_n_dims == 2:
                diffracted_expanded = diffracted_unit_pol.unsqueeze(0).expand(n_sources, -1, -1)
                incident_expanded = incident_beam_direction.unsqueeze(1).expand(-1, diffracted_unit_pol.shape[0], -1)
            else:
                diffracted_expanded = diffracted_unit_pol.unsqueeze(0).expand(n_sources, -1, -1, -1)
                incident_expanded = incident_beam_direction.unsqueeze(1).unsqueeze(1).expand(-1, diffracted_unit_pol.shape[0], diffracted_unit_pol.shape[1], -1)
            incident_flat = incident_expanded.reshape(-1, 3).contiguous()
            diffracted_flat = diffracted_expanded.reshape(-1, 3).contiguous()
            polar_flat = polarization_factor(kahn_factor, incident_flat, diffracted_flat, polarization_axis)
            if original_n_dims == 2:
                polar = polar_flat.reshape(n_sources, -1)
            else:
                polar = polar_flat.reshape(n_sources, diffracted_unit_pol.shape[0], diffracted_unit_pol.shape[1])
            intensity = intensity * polar
        else:
            if original_n_dims == 3:
                incident_flat = incident_beam_direction.unsqueeze(0).unsqueeze(0).expand(
                    diffracted_unit_pol.shape[0], diffracted_unit_pol.shape[1], -1
                ).reshape(-1, 3).contiguous()
            else:
                incident_flat = incident_beam_direction.unsqueeze(0).expand(
                    diffracted_unit_pol.shape[0], -1
                ).reshape(-1, 3).contiguous()
            diffracted_flat = diffracted_unit_pol.reshape(-1, 3).contiguous()
            polar_flat = polarization_factor(kahn_factor, incident_flat, diffracted_flat, polarization_axis)
            if original_n_dims == 2:
                polar = polar_flat.reshape(-1)
            else:
                polar = polar_flat.reshape(diffracted_unit_pol.shape[0], diffracted_unit_pol.shape[1])
            intensity = intensity * polar

    # Multi-source accumulation
    if is_multi_source:
        intensity = torch.sum(intensity, dim=0)
        if intensity_pre_polar is not None:
            intensity_pre_polar = torch.sum(intensity_pre_polar, dim=0)

    return intensity, intensity_pre_polar


class ProbabilisticSimulator(Simulator):
    """Drop-in simulator that replaces Monte Carlo mosaic sampling with an
    analytic Gaussian envelope in reciprocal space.

    Accepts the same configuration objects as :class:`Simulator`.  The
    ``mosaic_domains`` parameter is ignored (treated as 1); ``mosaic_spread_deg``
    drives the analytic width σ.

    Design reference: docs/plans/2026-01-29-probabilistic-simulator-design.md
    Strategy anchor: docs/strategy/mainstrategy.md §3A (Drop-in API Contract)
    """

    def __init__(
        self,
        crystal: Crystal,
        detector: Detector,
        crystal_config: Optional[CrystalConfig] = None,
        beam_config: Optional[BeamConfig] = None,
        device=None,
        dtype=torch.float32,
        debug_config: Optional[dict] = None,
    ):
        super().__init__(
            crystal=crystal,
            detector=detector,
            crystal_config=crystal_config,
            beam_config=beam_config,
            device=device,
            dtype=dtype,
            debug_config=debug_config,
        )
        # Will be populated lazily in run() from the stashed config
        self._analytic_mosaic_spread_rad: Optional[torch.Tensor] = None

    # ------------------------------------------------------------------
    # Stash-and-patch helpers
    # ------------------------------------------------------------------
    def _stash_mosaic_state(self):
        """Save true mosaic config and patch to single-domain / zero-spread."""
        cfg = self.crystal.config
        self._orig_spread_deg = cfg.mosaic_spread_deg
        self._orig_domains = cfg.mosaic_domains
        self._orig_seed = cfg.mosaic_seed

        # Convert to radians and store as tensor on device
        spread_deg = cfg.mosaic_spread_deg
        if isinstance(spread_deg, torch.Tensor):
            self._analytic_mosaic_spread_rad = (spread_deg * torch.pi / 180.0).to(
                device=self.device, dtype=self.dtype
            )
        else:
            self._analytic_mosaic_spread_rad = torch.tensor(
                spread_deg * 3.141592653589793 / 180.0,
                device=self.device,
                dtype=self.dtype,
            )

        # Patch config so base run() uses a single orientation (no MC domains)
        cfg.mosaic_spread_deg = 0.0
        cfg.mosaic_domains = 1
        cfg.mosaic_seed = None

    def _restore_mosaic_state(self):
        """Restore original mosaic config after run()."""
        cfg = self.crystal.config
        cfg.mosaic_spread_deg = self._orig_spread_deg
        cfg.mosaic_domains = self._orig_domains
        cfg.mosaic_seed = self._orig_seed

    # ------------------------------------------------------------------
    # Physics override
    # ------------------------------------------------------------------
    def _compute_physics_for_position(
        self, pixel_coords_angstroms, rot_a, rot_b, rot_c,
        rot_a_star, rot_b_star, rot_c_star,
        incident_beam_direction=None, wavelength=None, source_weights=None,
    ):
        """Override to call the probabilistic kernel with analytic spread."""
        if incident_beam_direction is None:
            incident_beam_direction = self.incident_beam_direction
        if wavelength is None:
            wavelength = self.wavelength

        incident_beam_direction = incident_beam_direction.clone()

        if self.device.type == "cuda":
            torch.compiler.cudagraph_mark_step_begin()

        if self._analytic_mosaic_spread_rad is None:
            raise RuntimeError(
                "ProbabilisticSimulator._compute_physics_for_position called "
                "outside of run() — mosaic spread not stashed."
            )

        return compute_probabilistic_physics(
            pixel_coords_angstroms=pixel_coords_angstroms,
            rot_a=rot_a,
            rot_b=rot_b,
            rot_c=rot_c,
            rot_a_star=rot_a_star,
            rot_b_star=rot_b_star,
            rot_c_star=rot_c_star,
            incident_beam_direction=incident_beam_direction,
            wavelength=wavelength,
            source_weights=source_weights,
            dmin=self.beam_config.dmin,
            crystal_get_structure_factor=self.crystal.get_structure_factor,
            N_cells_a=self.crystal.N_cells_a,
            N_cells_b=self.crystal.N_cells_b,
            N_cells_c=self.crystal.N_cells_c,
            crystal_shape=self.crystal.config.shape,
            crystal_fudge=self.crystal.config.fudge,
            apply_polarization=not self.beam_config.nopolar,
            kahn_factor=self.kahn_factor,
            polarization_axis=self.polarization_axis,
            mosaic_spread_rad=self._analytic_mosaic_spread_rad,
        )

    # ------------------------------------------------------------------
    # run() override — stash-and-patch
    # ------------------------------------------------------------------
    def run(
        self,
        pixel_batch_size: Optional[int] = None,
        stochastic_pixel_count: Optional[int] = None,
        override_a_star: Optional[torch.Tensor] = None,
        oversample: Optional[int] = None,
        oversample_omega: Optional[bool] = None,
        oversample_polar: Optional[bool] = None,
        oversample_thick: Optional[bool] = None,
    ):
        """Run the probabilistic simulation with stash-and-patch isolation.

        Temporarily sets ``mosaic_spread_deg=0`` and ``mosaic_domains=1`` so that
        the base ``Simulator.run()`` builds a single orientation (no MC domains).
        The true spread is forwarded to the analytic kernel via
        ``self._analytic_mosaic_spread_rad``.
        """
        self._stash_mosaic_state()
        try:
            return super().run(
                pixel_batch_size=pixel_batch_size,
                stochastic_pixel_count=stochastic_pixel_count,
                override_a_star=override_a_star,
                oversample=oversample,
                oversample_omega=oversample_omega,
                oversample_polar=oversample_polar,
                oversample_thick=oversample_thick,
            )
        finally:
            self._restore_mosaic_state()
            # Clear cached spread so accidental calls outside run() fail loudly
            self._analytic_mosaic_spread_rad = None

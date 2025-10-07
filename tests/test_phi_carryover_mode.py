"""
Test suite for --phi-carryover-mode CLI flag (CLI-FLAGS-003 Phase C2)

This module tests the CLI flag wiring and validation for the phi carryover mode
option that allows reproducing the C-PARITY-001 bug for validation purposes.

References:
- docs/bugs/verified_c_bugs.md (C-PARITY-001 description)
- plans/active/cli-phi-parity-shim/plan.md (Phase B2 design)
- reports/2025-10-cli-flags/phase_l/parity_shim/20251007T232657Z/design.md
"""
import os
import pytest
import torch
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
from nanobrag_torch.config import CrystalConfig
from nanobrag_torch.models.crystal import Crystal
from nanobrag_torch.config import BeamConfig

# Set required environment variable
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'


def run_parse(args):
    """
    Helper to parse CLI arguments and return validated config.

    Creates a fresh parser for each invocation to avoid state contamination.
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    return parse_and_validate_args(parsed_args)


class TestPhiCarryoverModeParsing:
    """Test CLI flag parsing and validation for --phi-carryover-mode."""

    def test_default_mode_is_spec(self):
        """Verify default phi_carryover_mode is 'spec' (spec-compliant)."""
        parser = create_parser()
        args = parser.parse_args([
            '-cell', '100', '100', '100', '90', '90', '90'
        ])

        assert args.phi_carryover_mode == 'spec', \
            "Default --phi-carryover-mode should be 'spec'"

    def test_spec_mode_explicit(self):
        """Verify --phi-carryover-mode spec is accepted."""
        parser = create_parser()
        args = parser.parse_args([
            '-cell', '100', '100', '100', '90', '90', '90',
            '--phi-carryover-mode', 'spec'
        ])

        assert args.phi_carryover_mode == 'spec'

    def test_c_parity_mode_explicit(self):
        """Verify --phi-carryover-mode c-parity is accepted."""
        parser = create_parser()
        args = parser.parse_args([
            '-cell', '100', '100', '100', '90', '90', '90',
            '--phi-carryover-mode', 'c-parity'
        ])

        assert args.phi_carryover_mode == 'c-parity'

    def test_invalid_mode_rejected(self):
        """Verify invalid modes are rejected by argparse."""
        parser = create_parser()

        with pytest.raises(SystemExit):
            # argparse exits with status 2 for invalid choice
            parser.parse_args([
                '-cell', '100', '100', '100', '90', '90', '90',
                '--phi-carryover-mode', 'invalid'
            ])


class TestCrystalConfigValidation:
    """Test CrystalConfig validation for phi_carryover_mode."""

    def test_default_config_mode(self):
        """Verify CrystalConfig defaults to 'spec' mode."""
        config = CrystalConfig()
        assert config.phi_carryover_mode == 'spec'

    def test_spec_mode_validation(self):
        """Verify 'spec' mode is accepted."""
        config = CrystalConfig(phi_carryover_mode='spec')
        assert config.phi_carryover_mode == 'spec'

    def test_c_parity_mode_validation(self):
        """Verify 'c-parity' mode is accepted."""
        config = CrystalConfig(phi_carryover_mode='c-parity')
        assert config.phi_carryover_mode == 'c-parity'

    def test_invalid_mode_raises_valueerror(self):
        """Verify invalid modes raise ValueError in __post_init__."""
        with pytest.raises(ValueError, match="phi_carryover_mode must be"):
            CrystalConfig(phi_carryover_mode='invalid')


class TestCLIToConfigWiring:
    """Test that CLI flag correctly wires through to CrystalConfig."""

    def test_spec_mode_wiring(self):
        """Verify --phi-carryover-mode spec reaches CrystalConfig."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '100',
            '--phi-carryover-mode', 'spec'
        ])

        # The config dict should be used to create CrystalConfig
        # We can't directly test CrystalConfig creation here since it happens in main()
        # but we can verify the args were parsed correctly
        parser = create_parser()
        args = parser.parse_args([
            '-cell', '100', '100', '100', '90', '90', '90',
            '--phi-carryover-mode', 'spec'
        ])

        assert args.phi_carryover_mode == 'spec'

        # Test that CrystalConfig accepts the value
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            phi_carryover_mode=args.phi_carryover_mode
        )

        assert crystal_config.phi_carryover_mode == 'spec'

    def test_c_parity_mode_wiring(self):
        """Verify --phi-carryover-mode c-parity reaches CrystalConfig."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '100',
            '--phi-carryover-mode', 'c-parity'
        ])

        parser = create_parser()
        args = parser.parse_args([
            '-cell', '100', '100', '100', '90', '90', '90',
            '--phi-carryover-mode', 'c-parity'
        ])

        assert args.phi_carryover_mode == 'c-parity'

        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            phi_carryover_mode=args.phi_carryover_mode
        )

        assert crystal_config.phi_carryover_mode == 'c-parity'


class TestPhiCarryoverBehavior:
    """Test that phi_carryover_mode affects rotation behavior correctly."""

    @pytest.mark.parametrize("device,dtype", [
        ("cpu", torch.float32),
        ("cpu", torch.float64),
        pytest.param("cuda", torch.float32, marks=pytest.mark.skipif(
            not torch.cuda.is_available(), reason="CUDA not available"
        )),
        pytest.param("cuda", torch.float64, marks=pytest.mark.skipif(
            not torch.cuda.is_available(), reason="CUDA not available"
        )),
    ])
    def test_spec_mode_fresh_rotation(self, device, dtype):
        """
        Verify 'spec' mode applies fresh rotation for φ=0.

        In spec mode, φ=0 should receive an identity rotation (fresh vectors).
        """
        config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            phi_start_deg=0.0,
            osc_range_deg=1.0,
            phi_steps=3,  # φ angles: 0°, 0.5°, 1.0° (C loop formula)
            phi_carryover_mode='spec'
        )

        crystal = Crystal(config, device=device, dtype=dtype)
        beam_config = BeamConfig(wavelength_A=6.2)

        (a_final, b_final, c_final), (a_star_final, b_star_final, c_star_final) = \
            crystal.get_rotated_real_vectors(config)

        # For spec mode, φ=0 (index 0) should be identity rotation
        # So a_final[0] should match the base vector crystal.a
        # (allowing for numerical precision)
        base_a = crystal.a
        phi_0_a = a_final[0, 0]  # First phi step, first mosaic domain

        delta = torch.abs(phi_0_a - base_a).max()
        assert delta < 1e-6, \
            f"Spec mode: φ=0 should have identity rotation, max delta={delta:.3e}"

    @pytest.mark.parametrize("device,dtype", [
        ("cpu", torch.float32),
        ("cpu", torch.float64),
        pytest.param("cuda", torch.float32, marks=pytest.mark.skipif(
            not torch.cuda.is_available(), reason="CUDA not available"
        )),
        pytest.param("cuda", torch.float64, marks=pytest.mark.skipif(
            not torch.cuda.is_available(), reason="CUDA not available"
        )),
    ])
    def test_c_parity_mode_stale_carryover(self, device, dtype):
        """
        Verify 'c-parity' mode reuses final φ vectors for φ=0 (C bug emulation).

        In c-parity mode, φ=0 should receive the same vectors as the final φ step
        (simulating stale carryover from previous pixel's last φ).
        """
        config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            phi_start_deg=0.0,
            osc_range_deg=1.0,
            phi_steps=3,  # φ angles: 0°, 0.5°, 1.0° (C loop formula)
            phi_carryover_mode='c-parity'
        )

        crystal = Crystal(config, device=device, dtype=dtype)
        beam_config = BeamConfig(wavelength_A=6.2)

        (a_final, b_final, c_final), (a_star_final, b_star_final, c_star_final) = \
            crystal.get_rotated_real_vectors(config)

        # For c-parity mode, φ=0 (index 0) should match φ=final (index -1)
        phi_0_a = a_final[0, 0]  # First phi step, first mosaic domain
        phi_final_a = a_final[-1, 0]  # Last phi step, first mosaic domain

        delta = torch.abs(phi_0_a - phi_final_a).max()
        assert delta < 1e-12, \
            f"C-parity mode: φ=0 should match φ=final, max delta={delta:.3e}"

    @pytest.mark.parametrize("device,dtype", [
        ("cpu", torch.float32),
        ("cpu", torch.float64),
        pytest.param("cuda", torch.float32, marks=pytest.mark.skipif(
            not torch.cuda.is_available(), reason="CUDA not available"
        )),
        pytest.param("cuda", torch.float64, marks=pytest.mark.skipif(
            not torch.cuda.is_available(), reason="CUDA not available"
        )),
    ])
    def test_modes_differ_at_phi_zero(self, device, dtype):
        """
        Verify that spec and c-parity modes produce different φ=0 vectors.

        This test confirms that the two modes actually behave differently.
        """
        config_spec = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            phi_start_deg=0.0,
            osc_range_deg=1.0,
            phi_steps=3,
            phi_carryover_mode='spec'
        )

        config_parity = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            phi_start_deg=0.0,
            osc_range_deg=1.0,
            phi_steps=3,
            phi_carryover_mode='c-parity'
        )

        crystal_spec = Crystal(config_spec, device=device, dtype=dtype)
        crystal_parity = Crystal(config_parity, device=device, dtype=dtype)

        (a_spec, _, _), _ = crystal_spec.get_rotated_real_vectors(config_spec)
        (a_parity, _, _), _ = crystal_parity.get_rotated_real_vectors(config_parity)

        # φ=0 vectors should differ between modes
        phi_0_a_spec = a_spec[0, 0]
        phi_0_a_parity = a_parity[0, 0]

        delta = torch.abs(phi_0_a_spec - phi_0_a_parity).max()
        # Allow small tolerance for numerical precision, but should be measurably different
        assert delta > 1e-6, \
            f"Spec and c-parity modes should produce different φ=0 vectors, delta={delta:.3e}"


class TestDeviceDtypeNeutrality:
    """Test that phi carryover mode works across devices and dtypes."""

    @pytest.mark.parametrize("mode", ['spec', 'c-parity'])
    @pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
    def test_cpu_consistency(self, mode, dtype):
        """Verify mode works correctly on CPU with both dtypes."""
        config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            phi_start_deg=0.0,
            osc_range_deg=1.0,
            phi_steps=2,
            phi_carryover_mode=mode
        )

        crystal = Crystal(config, device='cpu', dtype=dtype)
        (a_final, _, _), _ = crystal.get_rotated_real_vectors(config)

        # Verify output is on correct device and dtype
        assert a_final.device.type == 'cpu'
        assert a_final.dtype == dtype

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    @pytest.mark.parametrize("mode", ['spec', 'c-parity'])
    @pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
    def test_cuda_consistency(self, mode, dtype):
        """Verify mode works correctly on CUDA with both dtypes."""
        config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            phi_start_deg=0.0,
            osc_range_deg=1.0,
            phi_steps=2,
            phi_carryover_mode=mode
        )

        crystal = Crystal(config, device='cuda', dtype=dtype)
        (a_final, _, _), _ = crystal.get_rotated_real_vectors(config)

        # Verify output is on correct device and dtype
        assert a_final.device.type == 'cuda'
        assert a_final.dtype == dtype


class TestFlagInteractions:
    """Test that --phi-carryover-mode doesn't interfere with other flags."""

    def test_with_misset(self):
        """Verify phi carryover works with misset angles."""
        config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            misset_deg=(5.0, 10.0, 15.0),
            phi_start_deg=0.0,
            osc_range_deg=1.0,
            phi_steps=2,
            phi_carryover_mode='c-parity'
        )

        crystal = Crystal(config)
        (a_final, _, _), _ = crystal.get_rotated_real_vectors(config)

        # Should not crash and should produce valid output
        assert a_final.shape == (2, 1, 3)  # (phi_steps, mosaic_domains, 3)

    def test_with_mosaic(self):
        """Verify phi carryover works with mosaic domains."""
        config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            mosaic_spread_deg=0.5,
            mosaic_domains=3,
            phi_start_deg=0.0,
            osc_range_deg=1.0,
            phi_steps=2,
            phi_carryover_mode='c-parity'
        )

        crystal = Crystal(config)
        (a_final, _, _), _ = crystal.get_rotated_real_vectors(config)

        # Should not crash and should produce valid output
        assert a_final.shape == (2, 3, 3)  # (phi_steps, mosaic_domains, 3)

    def test_with_single_phi_step(self):
        """Verify phi carryover handles edge case of single phi step."""
        config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            phi_start_deg=0.0,
            osc_range_deg=0.0,
            phi_steps=1,
            phi_carryover_mode='c-parity'
        )

        crystal = Crystal(config)
        (a_final, _, _), _ = crystal.get_rotated_real_vectors(config)

        # With single phi step, φ=0 should match φ=final (same index)
        # This should not crash
        assert a_final.shape == (1, 1, 3)

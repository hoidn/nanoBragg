"""
CLI Flag Regression Tests for CLI-FLAGS-003 Phase C1

Tests the -nonoise and -pix0_vector_mm flags added in Phase B.
Validates argument parsing, unit conversions, and detector override behavior.

Evidence base: reports/2025-10-cli-flags/phase_a/README.md
"""
import os
import pytest
import torch
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
from nanobrag_torch.config import DetectorConfig
from nanobrag_torch.models.detector import Detector

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


class TestPix0VectorAlias:
    """Test pix0_vector (meters) and pix0_vector_mm (millimeters) equivalence."""

    def test_pix0_meters_alias(self):
        """Verify -pix0_vector accepts meters and stores correctly."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-pix0_vector', '0.1', '-0.2', '0.3'
        ])

        # Should store as meter tuple
        assert config['pix0_override_m'] == pytest.approx((0.1, -0.2, 0.3), rel=0, abs=1e-12)
        # CUSTOM override should propagate
        assert config['custom_pix0_vector'] == config['pix0_override_m']

    def test_pix0_millimeter_alias(self):
        """Verify -pix0_vector_mm accepts millimeters and converts to meters."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-pix0_vector_mm', '100', '-200', '300'
        ])

        # Should convert mm -> m (100mm = 0.1m, etc.)
        assert config['pix0_override_m'] == pytest.approx((0.1, -0.2, 0.3), rel=0, abs=1e-12)
        assert config['custom_pix0_vector'] == config['pix0_override_m']

    def test_pix0_meters_and_mm_equivalence(self):
        """Meters and millimeters flags should produce identical config."""
        config_m = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-pix0_vector', '0.1', '-0.2', '0.3'
        ])

        config_mm = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-pix0_vector_mm', '100', '-200', '300'
        ])

        assert config_m['pix0_override_m'] == pytest.approx(config_mm['pix0_override_m'], rel=0, abs=1e-12)

    def test_dual_pix0_flag_rejection(self):
        """Using both -pix0_vector and -pix0_vector_mm should raise ValueError."""
        with pytest.raises(ValueError, match="Cannot specify both -pix0_vector and -pix0_vector_mm"):
            run_parse([
                '-cell', '100', '100', '100', '90', '90', '90',
                '-pixel', '0.1',
                '-pix0_vector', '0', '0', '0',
                '-pix0_vector_mm', '0', '0', '0'
            ])

    @pytest.mark.parametrize("pix0_m,pix0_mm", [
        ((0.1, -0.2, 0.3), (100, -200, 300)),
        ((-0.1, 0.0, 0.0), (-100, 0, 0)),
        ((0.001, 0.002, 0.003), (1, 2, 3)),
    ])
    def test_pix0_signed_combinations(self, pix0_m, pix0_mm):
        """Test various signed pix0 combinations to catch sign bugs."""
        config_m = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-pix0_vector', str(pix0_m[0]), str(pix0_m[1]), str(pix0_m[2])
        ])

        config_mm = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-pix0_vector_mm', str(pix0_mm[0]), str(pix0_mm[1]), str(pix0_mm[2])
        ])

        assert config_m['pix0_override_m'] == pytest.approx(pix0_m, rel=0, abs=1e-12)
        assert config_mm['pix0_override_m'] == pytest.approx(pix0_m, rel=0, abs=1e-12)


class TestDetectorOverridePersistence:
    """Test detector override behavior on CPU and CUDA."""

    def test_detector_override_persistence_cpu(self):
        """Verify pix0 override persists through cache invalidation on CPU."""
        cfg = DetectorConfig(
            distance_mm=100,
            pixel_size_mm=0.1,
            spixels=4,
            fpixels=4,
            pix0_override_m=torch.tensor([0.01, -0.02, 0.03], dtype=torch.float64)
        )

        det = Detector(cfg, device='cpu', dtype=torch.float64)

        # Check override applied
        assert torch.allclose(
            det.pix0_vector,
            torch.tensor([0.01, -0.02, 0.03], dtype=torch.float64)
        )

        # Invalidate cache and verify override persists
        det.invalidate_cache()
        assert torch.allclose(
            det.pix0_vector,
            torch.tensor([0.01, -0.02, 0.03], dtype=torch.float64)
        )

        # When override is used, r_factor should be 1.0 and close_distance == distance (in meters)
        assert det.r_factor == pytest.approx(1.0, rel=1e-9)
        assert det.close_distance == pytest.approx(cfg.distance_mm * 1e-3, rel=1e-9)  # mm to m

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_detector_override_persistence_cuda(self):
        """Verify pix0 override persists through cache invalidation on CUDA."""
        cfg = DetectorConfig(
            distance_mm=100,
            pixel_size_mm=0.1,
            spixels=4,
            fpixels=4,
            pix0_override_m=torch.tensor([0.01, -0.02, 0.03], dtype=torch.float64)
        )

        det = Detector(cfg, device='cuda', dtype=torch.float64)

        # Check override applied and on correct device
        assert torch.allclose(
            det.pix0_vector.cpu(),
            torch.tensor([0.01, -0.02, 0.03], dtype=torch.float64)
        )
        assert det.pix0_vector.device.type == 'cuda'

        # Invalidate cache and verify override persists
        det.invalidate_cache()
        assert torch.allclose(
            det.pix0_vector.cpu(),
            torch.tensor([0.01, -0.02, 0.03], dtype=torch.float64)
        )
        assert det.pix0_vector.device.type == 'cuda'

        # When override is used, r_factor should be 1.0 and close_distance == distance (in meters)
        # Move tensor to CPU for comparison; close_distance is a float
        assert det.r_factor.cpu().item() == pytest.approx(1.0, rel=1e-9)
        assert det.close_distance == pytest.approx(cfg.distance_mm * 1e-3, rel=1e-9)  # mm to m

    def test_detector_override_dtype_preservation(self):
        """Verify pix0 override preserves dtype across operations."""
        for dtype in [torch.float32, torch.float64]:
            cfg = DetectorConfig(
                distance_mm=100,
                pixel_size_mm=0.1,
                spixels=4,
                fpixels=4,
                pix0_override_m=torch.tensor([0.01, -0.02, 0.03], dtype=dtype)
            )

            det = Detector(cfg, device='cpu', dtype=dtype)
            assert det.pix0_vector.dtype == dtype

            det.invalidate_cache()
            assert det.pix0_vector.dtype == dtype


class TestNoiseSuppressionFlag:
    """Test -nonoise flag suppresses noise image generation."""

    def test_nonoise_suppresses_noise_output(self):
        """Verify -nonoise sets suppress_noise flag."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-floatfile', 'out.bin',
            '-noisefile', 'noise.img',
            '-nonoise'
        ])

        assert config['noisefile'] == 'noise.img'
        assert config['suppress_noise'] is True
        # Ensure other fields remain unaffected
        assert config['adc'] == pytest.approx(40.0)

    def test_noisefile_without_nonoise(self):
        """Verify -noisefile without -nonoise enables noise generation."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-floatfile', 'out.bin',
            '-noisefile', 'noise.img'
        ])

        assert config['noisefile'] == 'noise.img'
        assert config['suppress_noise'] is False

    def test_nonoise_preserves_seed(self):
        """Verify -nonoise doesn't mutate seed handling."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-floatfile', 'out.bin',
            '-noisefile', 'noise.img',
            '-seed', '1234',
            '-nonoise'
        ])

        assert config['seed'] == 1234
        assert config['suppress_noise'] is True

    def test_nonoise_without_noisefile(self):
        """Verify -nonoise can be used without -noisefile (no-op but valid)."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-floatfile', 'out.bin',
            '-nonoise'
        ])

        assert config.get('noisefile') is None
        assert config['suppress_noise'] is True


class TestCLIIntegrationSanity:
    """Integration tests to ensure new flags don't break existing behavior."""

    def test_pix0_does_not_alter_beam_vector(self):
        """Verify -pix0_vector doesn't mutate beam_vector."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-pix0_vector', '0.1', '0.2', '0.3'
        ])

        # custom_beam_vector should remain unset
        assert config.get('custom_beam_vector') is None

    def test_pix0_triggers_custom_convention(self):
        """Verify pix0 vectors trigger CUSTOM convention."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-pix0_vector_mm', '100', '200', '300'
        ])

        # Should switch to CUSTOM when custom vectors are provided
        assert config['convention'] == 'CUSTOM'

    def test_roi_unaffected_by_new_flags(self):
        """Verify ROI defaults remain unchanged."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-pix0_vector', '0', '0', '0',
            '-nonoise'
        ])

        assert config.get('roi') is None

    def test_convention_preserved_without_pix0(self):
        """Verify MOSFLM convention remains when pix0 not specified."""
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-pixel', '0.1',
            '-mosflm'  # Use the flag form, not -convention
        ])

        assert config.get('convention') == 'MOSFLM'
        assert config.get('pix0_override_m') is None

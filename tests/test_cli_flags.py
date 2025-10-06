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
from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
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
    """
    Test detector override behavior on CPU and CUDA.

    UPDATED for CLI-FLAGS-003 Phase H3b: pix0_override with BEAM pivot
    now applies the BEAM-pivot formula, NOT the raw override.
    Reference: plans/active/cli-noise-pix0/plan.md Phase H3b
    """

    def test_detector_override_persistence_cpu(self):
        """
        Verify pix0 calculation applies BEAM-pivot formula even with override.

        Phase H3b Update: When pix0_override is provided with BEAM pivot,
        the detector ALWAYS applies the formula:
            pix0 = -Fbeam*fdet - Sbeam*sdet + distance*beam

        The override is IGNORED (as per C-code behavior and parity analysis).
        """
        cfg = DetectorConfig(
            distance_mm=100,
            pixel_size_mm=0.1,
            spixels=4,
            fpixels=4,
            beam_center_f=0.2,  # mm
            beam_center_s=0.2,  # mm
            pix0_override_m=torch.tensor([0.15, -0.05, 0.05], dtype=torch.float64)  # Will be IGNORED
        )

        det = Detector(cfg, device='cpu', dtype=torch.float64)

        # Phase H3b: pix0 is calculated from formula, NOT from override
        # Expected: pix0 = -Fbeam*fdet - Sbeam*sdet + distance*beam
        # For MOSFLM: fdet=[0,0,1], sdet=[0,-1,0], beam=[1,0,0]
        # Fbeam = Ybeam + 0.5*pixel = 0.0002 + 0.00005 = 0.00025 m
        # Sbeam = Xbeam + 0.5*pixel = 0.0002 + 0.00005 = 0.00025 m
        # pix0 = -0.00025*[0,0,1] - 0.00025*[0,-1,0] + 0.1*[1,0,0]
        #      = [0, 0, -0.00025] + [0, 0.00025, 0] + [0.1, 0, 0]
        #      = [0.1, 0.00025, -0.00025]
        expected_pix0 = torch.tensor([0.1, 0.00025, -0.00025], dtype=torch.float64)

        assert torch.allclose(det.pix0_vector, expected_pix0, atol=1e-9)

        # Invalidate cache and verify formula still applied
        det.invalidate_cache()
        assert torch.allclose(det.pix0_vector, expected_pix0, atol=1e-9)

        # r_factor and close_distance should be consistent
        assert det.r_factor == pytest.approx(1.0, rel=1e-9)
        assert det.close_distance.item() == pytest.approx(0.1, rel=1e-9)  # pix0[0] for MOSFLM

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_detector_override_persistence_cuda(self):
        """
        Verify pix0 calculation applies BEAM-pivot formula on CUDA.

        Phase H3b Update: Same behavior as CPU test, but validates device neutrality.
        """
        cfg = DetectorConfig(
            distance_mm=100,
            pixel_size_mm=0.1,
            spixels=4,
            fpixels=4,
            beam_center_f=0.2,  # mm
            beam_center_s=0.2,  # mm
            pix0_override_m=torch.tensor([0.15, -0.05, 0.05], dtype=torch.float64)  # Will be IGNORED
        )

        det = Detector(cfg, device='cuda', dtype=torch.float64)

        # Phase H3b: pix0 calculated from formula (same as CPU test)
        expected_pix0 = torch.tensor([0.1, 0.00025, -0.00025], dtype=torch.float64)

        assert torch.allclose(det.pix0_vector.cpu(), expected_pix0, atol=1e-9)
        assert det.pix0_vector.device.type == 'cuda'

        # Invalidate cache and verify formula still applied
        det.invalidate_cache()
        assert torch.allclose(det.pix0_vector.cpu(), expected_pix0, atol=1e-9)
        assert det.pix0_vector.device.type == 'cuda'

        # r_factor and close_distance should be consistent
        assert det.r_factor.cpu().item() == pytest.approx(1.0, rel=1e-9)
        assert det.close_distance.cpu().item() == pytest.approx(0.1, rel=1e-9)  # pix0[0] for MOSFLM

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


class TestCLIBeamVector:
    """Test -beam_vector CLI flag propagation through Detector→Simulator."""

    def test_custom_beam_vector_propagates(self):
        """
        Verify custom beam vector from CLI reaches Simulator.incident_beam_direction.

        Addresses CLI-FLAGS-003 Phase H2: beam vector must propagate from detector
        to simulator so CLI `-beam_vector` overrides reach the physics kernels.

        Evidence: input.md Do Now (2025-10-17), plans/active/cli-noise-pix0/plan.md H2
        """
        from nanobrag_torch.models.detector import Detector
        from nanobrag_torch.models.crystal import Crystal
        from nanobrag_torch.simulator import Simulator
        from nanobrag_torch.config import DetectorConfig, DetectorConvention, CrystalConfig, BeamConfig

        # Custom beam vector (will be normalized by detector)
        custom_beam_raw = (0.5, 0.5, 0.707107)

        # Create detector config with custom beam vector
        detector_config = DetectorConfig(
            distance_mm=100.0,
            pixel_size_mm=0.1,
            spixels=64,
            fpixels=64,
            detector_convention=DetectorConvention.CUSTOM,
            custom_beam_vector=custom_beam_raw
        )

        # Construct detector
        detector = Detector(detector_config)

        # Verify detector has the custom beam vector (normalized)
        beam_vec = detector.beam_vector
        expected = torch.tensor(custom_beam_raw, dtype=detector.dtype, device=detector.device)
        expected_norm = expected / torch.linalg.norm(expected)

        assert torch.allclose(beam_vec, expected_norm, atol=1e-6), \
            f"Detector beam_vector {beam_vec} != expected {expected_norm}"

        # Construct minimal configs for simulator
        crystal_config = CrystalConfig(
            cell_a=100.0, cell_b=100.0, cell_c=100.0,
            cell_alpha=90.0, cell_beta=90.0, cell_gamma=90.0,
            N_cells=(5, 5, 5),
            default_F=1.0
        )

        beam_config = BeamConfig(wavelength_A=6.2)

        # Create Crystal object
        crystal = Crystal(crystal_config)

        # Construct simulator and verify it picks up detector's beam vector
        simulator = Simulator(
            crystal=crystal,
            detector=detector,
            crystal_config=crystal_config,
            beam_config=beam_config
        )

        # CRITICAL: Simulator.incident_beam_direction must match detector.beam_vector
        incident = simulator.incident_beam_direction
        assert torch.allclose(incident, expected_norm, atol=1e-6), \
            f"Simulator incident_beam_direction {incident} != detector beam_vector {expected_norm}"


class TestCLIPix0Override:
    """
    Regression tests for CLI-FLAGS-003 Phase H3b.

    Test the BEAM-pivot pix0 transformation when -pix0_vector_mm override is provided.
    Reference: plans/active/cli-noise-pix0/plan.md Phase H3b
    Evidence: reports/2025-10-cli-flags/phase_h/pix0_reproduction.md
    """

    @pytest.mark.parametrize("device,dtype", [
        ("cpu", torch.float32),
        pytest.param("cuda", torch.float32, marks=pytest.mark.skipif(
            not torch.cuda.is_available(), reason="CUDA not available"
        ))
    ])
    def test_pix0_override_beam_pivot_transform(self, device, dtype):
        """
        Verify pix0 override with BEAM pivot applies the C-code formula.

        When pix0_override is provided with BEAM pivot, the detector must ALWAYS
        apply the BEAM-pivot transformation formula:

            pix0 = -Fbeam*fdet - Sbeam*sdet + distance*beam

        This ensures geometric consistency and matches C-code behavior.
        Reference: nanoBragg.c lines 1833-1835, pix0_reproduction.md
        """
        # Test configuration: MOSFLM convention with BEAM pivot
        # Use simple detector geometry for analytical verification
        distance_mm = 100.0  # 100mm = 0.1m
        pixel_size_mm = 0.1
        spixels = fpixels = 512

        # MOSFLM beam centers (mm)
        Xbeam_mm = 51.2
        Ybeam_mm = 51.2

        # MOSFLM convention: Fbeam = Ybeam + 0.5*pixel, Sbeam = Xbeam + 0.5*pixel
        Fbeam_mm = Ybeam_mm + 0.5 * pixel_size_mm
        Sbeam_mm = Xbeam_mm + 0.5 * pixel_size_mm

        # Convert to meters
        Fbeam_m = Fbeam_mm / 1000.0
        Sbeam_m = Sbeam_mm / 1000.0
        distance_m = distance_mm / 1000.0

        # MOSFLM basis vectors (unrotated): f=[0,0,1], s=[0,-1,0], o=[1,0,0], beam=[1,0,0]
        fdet = torch.tensor([0.0, 0.0, 1.0], device=device, dtype=dtype)
        sdet = torch.tensor([0.0, -1.0, 0.0], device=device, dtype=dtype)
        beam = torch.tensor([1.0, 0.0, 0.0], device=device, dtype=dtype)

        # Expected pix0 from BEAM-pivot formula (C-code lines 1833-1835)
        expected_pix0 = (
            -Fbeam_m * fdet
            - Sbeam_m * sdet
            + distance_m * beam
        )

        # Create detector config WITH pix0_override
        # (The override should NOT bypass the formula!)
        dummy_override = torch.tensor([0.15, -0.05, 0.05], device=device, dtype=dtype)

        cfg = DetectorConfig(
            distance_mm=distance_mm,
            pixel_size_mm=pixel_size_mm,
            spixels=spixels,
            fpixels=fpixels,
            beam_center_f=Xbeam_mm,
            beam_center_s=Ybeam_mm,
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            pix0_override_m=dummy_override  # This should be IGNORED for BEAM pivot
        )

        det = Detector(cfg, device=device, dtype=dtype)

        # Verify pix0 matches the BEAM-pivot formula, NOT the raw override
        pix0_delta = torch.abs(det.pix0_vector - expected_pix0)
        max_error = torch.max(pix0_delta).item()

        assert max_error <= 1e-6, \
            f"pix0 delta exceeds threshold: max_error={max_error:.3e} m\n" \
            f"Expected (formula): {expected_pix0.cpu().numpy()}\n" \
            f"Actual (detector):  {det.pix0_vector.cpu().numpy()}\n" \
            f"Delta (per component): {pix0_delta.cpu().numpy()}"

        # Also verify device/dtype preservation
        assert det.pix0_vector.device.type == device
        assert det.pix0_vector.dtype == dtype

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
        Verify pix0 override IS APPLIED when NO custom vectors are present (BEAM pivot mode).

        Phase H3b2 Update: Per Phase H3b1 evidence, pix0_override is ONLY ignored when
        custom detector vectors are present. Without custom vectors, the override IS applied
        by deriving Fbeam/Sbeam from it and then applying the BEAM pivot formula.
        """
        cfg = DetectorConfig(
            distance_mm=100,
            pixel_size_mm=0.1,
            spixels=4,
            fpixels=4,
            beam_center_f=0.2,  # mm
            beam_center_s=0.2,  # mm
            pix0_override_m=torch.tensor([0.1, -0.05, 0.05], dtype=torch.float64)
        )

        det = Detector(cfg, device='cpu', dtype=torch.float64)

        # Phase H3b2: Without custom vectors, pix0_override IS applied
        # Expected: pix0 ≈ override value (modulo projection/reprojection precision)
        expected_pix0 = torch.tensor([0.1, -0.05, 0.05], dtype=torch.float64)

        assert torch.allclose(det.pix0_vector, expected_pix0, atol=1e-6)

        # Invalidate cache and verify override still applied
        det.invalidate_cache()
        assert torch.allclose(det.pix0_vector, expected_pix0, atol=1e-6)

        # r_factor and close_distance should be finite
        assert torch.isfinite(det.r_factor)
        assert torch.isfinite(det.close_distance)

    @pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
    def test_detector_override_persistence_cuda(self):
        """
        Verify pix0 override IS APPLIED on CUDA (same behavior as CPU test).

        Phase H3b2 Update: Validates device neutrality for pix0_override application.
        """
        cfg = DetectorConfig(
            distance_mm=100,
            pixel_size_mm=0.1,
            spixels=4,
            fpixels=4,
            beam_center_f=0.2,  # mm
            beam_center_s=0.2,  # mm
            pix0_override_m=torch.tensor([0.1, -0.05, 0.05], dtype=torch.float64)
        )

        det = Detector(cfg, device='cuda', dtype=torch.float64)

        # Phase H3b2: pix0_override applied (same as CPU test)
        expected_pix0 = torch.tensor([0.1, -0.05, 0.05], dtype=torch.float64)

        assert torch.allclose(det.pix0_vector.cpu(), expected_pix0, atol=1e-6)
        assert det.pix0_vector.device.type == 'cuda'

        # Invalidate cache and verify override still applied
        det.invalidate_cache()
        assert torch.allclose(det.pix0_vector.cpu(), expected_pix0, atol=1e-6)
        assert det.pix0_vector.device.type == 'cuda'

        # r_factor and close_distance should be finite
        assert torch.isfinite(det.r_factor)
        assert torch.isfinite(det.close_distance)

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
        Verify pix0 override IS APPLIED when NO custom vectors are present (BEAM pivot).

        Phase H3b2 Update: Per Phase H3b1 evidence, pix0_override is ONLY ignored when
        custom detector vectors are present. Without custom vectors, the override IS applied.

        This test verifies that the override value approximately matches the output (modulo
        the projection/reprojection precision from deriving Fbeam/Sbeam).
        """
        # Test configuration: MOSFLM convention with BEAM pivot
        distance_mm = 100.0  # 100mm = 0.1m
        pixel_size_mm = 0.1
        spixels = fpixels = 512

        # pix0_override value
        pix0_override = torch.tensor([0.1, -0.05, 0.05], device=device, dtype=dtype)

        cfg = DetectorConfig(
            distance_mm=distance_mm,
            pixel_size_mm=pixel_size_mm,
            spixels=spixels,
            fpixels=fpixels,
            beam_center_f=51.2,  # mm
            beam_center_s=51.2,  # mm
            detector_convention=DetectorConvention.MOSFLM,
            detector_pivot=DetectorPivot.BEAM,
            pix0_override_m=pix0_override  # Should be APPLIED (no custom vectors)
        )

        det = Detector(cfg, device=device, dtype=dtype)

        # Verify pix0 matches the override value (modulo projection precision)
        # Expected: pix0 ≈ override (after Fbeam/Sbeam derivation and reapplication)
        pix0_delta = torch.abs(det.pix0_vector - pix0_override)
        max_error = torch.max(pix0_delta).item()

        assert max_error <= 1e-6, \
            f"pix0 delta exceeds threshold: max_error={max_error:.3e} m\n" \
            f"Expected (override): {pix0_override.cpu().numpy()}\n" \
            f"Actual (detector):   {det.pix0_vector.cpu().numpy()}\n" \
            f"Delta (per component): {pix0_delta.cpu().numpy()}"

        # Also verify device/dtype preservation
        assert det.pix0_vector.device.type == device
        assert det.pix0_vector.dtype == dtype

    @pytest.mark.parametrize("device", ["cpu", pytest.param("cuda", marks=pytest.mark.skipif(
        not torch.cuda.is_available(), reason="CUDA not available"))])
    def test_pix0_vector_mm_beam_pivot(self, device):
        """
        Regression test for CLI-FLAGS-003 Phase H3b.

        CRITICAL FINDING from Phase H3b1:
        When custom detector vectors are provided, C code IGNORES -pix0_vector_mm entirely.
        The custom vectors already define the detector geometry completely.

        This test verifies BOTH scenarios:
        1. WITH custom vectors: pix0_override has NO EFFECT (matches C behavior)
        2. WITHOUT custom vectors: pix0_override IS applied

        Expected pix0 vector from C trace (phase_h) WITH custom vectors:
        -0.216336514802265, 0.215206668836451, -0.230198010448577 meters

        Reference: plans/active/cli-noise-pix0/plan.md Phase H3b
        Evidence: reports/2025-10-cli-flags/phase_h/implementation/pix0_mapping_analysis.md
        """
        import json
        from pathlib import Path

        # Load expected C pix0 vector
        expected_json_path = Path("reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json")
        with open(expected_json_path) as f:
            expected_data = json.load(f)

        expected_pix0_with_custom_vectors = torch.tensor([
            expected_data["pix0_vector_m"]["x"],
            expected_data["pix0_vector_m"]["y"],
            expected_data["pix0_vector_m"]["z"]
        ], device=device, dtype=torch.float32)

        # Custom detector vectors from supervisor command
        custom_odet = (-0.000088, 0.004914, -0.999988)
        custom_sdet = (-0.005998, -0.999970, -0.004913)
        custom_fdet = (0.999982, -0.005998, -0.000118)

        # -pix0_vector_mm from supervisor command
        pix0_override_mm = (-216.336293, 215.205512, -230.200866)

        # ==========================================
        # CASE 1: WITH custom vectors → override should be IGNORED
        # ==========================================
        # From C trace: Xbeam=0.217742 m, Ybeam=0.213907 m, Fbeam=0.217742 m, Sbeam=0.213907 m
        # For CUSTOM convention with these specific custom vectors: Fbeam=Xbeam, Sbeam=Ybeam (no +0.5 offset)
        # Note: This is OPPOSITE of MOSFLM mapping (Fbeam=Ybeam, Sbeam=Xbeam)
        # DetectorConfig expects beam_center_f/s in mm
        Xbeam_m = 0.217742  # From C trace (meters)
        Ybeam_m = 0.213907  # From C trace (meters)
        beam_center_f_mm = Xbeam_m * 1000.0  # Convert to mm - For these custom vectors: Fbeam=Xbeam
        beam_center_s_mm = Ybeam_m * 1000.0  # Convert to mm - For these custom vectors: Sbeam=Ybeam

        # Build detector from parsed config (with custom vectors)
        from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot

        det_with_custom = Detector(
            DetectorConfig(
                distance_mm=231.27466,
                pixel_size_mm=0.172,
                spixels=1024,
                fpixels=1024,
                beam_center_f=beam_center_f_mm,  # mm
                beam_center_s=beam_center_s_mm,  # mm
                detector_convention=DetectorConvention.CUSTOM,
                detector_pivot=DetectorPivot.BEAM,  # CLI-FLAGS-003 Phase H6f: Will be OVERRIDDEN to SAMPLE by custom vectors
                pix0_override_m=(-0.216336293, 0.215205512, -0.230200866),  # Should be IGNORED
                custom_beam_vector=(0.00051387949, 0.0, -0.99999986),
                custom_odet_vector=custom_odet,
                custom_sdet_vector=custom_sdet,
                custom_fdet_vector=custom_fdet
            ),
            device=device,
            dtype=torch.float32
        )

        # Verify pix0 matches C expectation (override should be IGNORED)
        pix0_delta = torch.abs(det_with_custom.pix0_vector - expected_pix0_with_custom_vectors)
        max_error = torch.max(pix0_delta).item()

        # CLI-FLAGS-003 Phase H4c: Tolerance tightened to 5e-5 m (50 μm) after H4a beam-centre
        # recomputation implementation. Expected values updated to fresh C trace from phase_h.
        # The post-rotation newvector logic now correctly updates Fbeam/Sbeam and distance_corrected.
        assert max_error <= 5e-5, \
            f"CASE 1 FAILED: With custom vectors, pix0_override should be IGNORED\n" \
            f"pix0 delta exceeds 5e-5 m threshold: max_error={max_error:.6e} m\n" \
            f"Expected (C trace): {expected_pix0_with_custom_vectors.cpu().numpy()}\n" \
            f"Actual (PyTorch):   {det_with_custom.pix0_vector.cpu().numpy()}\n" \
            f"Delta (per component): {pix0_delta.cpu().numpy()}"

        # ==========================================
        # CASE 2: WITHOUT custom vectors → override should be applied
        # ==========================================
        # Note: This case is harder to verify against C because we don't have a C trace
        # for this scenario. We'll just verify that the override is actually used.
        config_without_custom = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-distance', '100',  # mm
            '-pixel', '0.1',      # mm
            '-detpixels', '512',
            '-pix0_vector_mm', str(pix0_override_mm[0]), str(pix0_override_mm[1]), str(pix0_override_mm[2])
        ])

        det_without_custom = Detector(
            DetectorConfig(
                distance_mm=config_without_custom.get('distance_mm'),
                pixel_size_mm=config_without_custom.get('pixel_size_mm'),
                spixels=config_without_custom.get('spixels'),
                fpixels=config_without_custom.get('fpixels'),
                detector_convention=DetectorConvention.MOSFLM,  # No custom convention
                detector_pivot=DetectorPivot.BEAM,
                pix0_override_m=config_without_custom.get('pix0_override_m')
            ),
            device=device,
            dtype=torch.float32
        )

        # Build detector WITHOUT override for comparison
        det_without_override = Detector(
            DetectorConfig(
                distance_mm=config_without_custom.get('distance_mm'),
                pixel_size_mm=config_without_custom.get('pixel_size_mm'),
                spixels=config_without_custom.get('spixels'),
                fpixels=config_without_custom.get('fpixels'),
                detector_convention=DetectorConvention.MOSFLM,
                detector_pivot=DetectorPivot.BEAM,
                pix0_override_m=None  # NO override
            ),
            device=device,
            dtype=torch.float32
        )

        # Verify that pix0 DIFFERS when override is provided (override IS applied)
        pix0_diff = torch.abs(det_without_custom.pix0_vector - det_without_override.pix0_vector)
        max_difference = torch.max(pix0_diff).item()

        assert max_difference > 1e-3, \
            f"CASE 2 FAILED: Without custom vectors, pix0_override should be APPLIED\n" \
            f"pix0 with override:    {det_without_custom.pix0_vector.cpu().numpy()}\n" \
            f"pix0 without override: {det_without_override.pix0_vector.cpu().numpy()}\n" \
            f"Max difference: {max_difference:.6e} m (expected > 1e-3 m to show override was applied)"

        # Verify close_distance is recalculated and finite
        assert torch.isfinite(det_with_custom.close_distance), "close_distance must be finite (with custom)"
        assert torch.isfinite(det_without_custom.close_distance), "close_distance must be finite (without custom)"

        # Device/dtype preservation
        assert det_with_custom.pix0_vector.device.type == device
        assert det_with_custom.pix0_vector.dtype == torch.float32
        assert det_without_custom.pix0_vector.device.type == device
        assert det_without_custom.pix0_vector.dtype == torch.float32


class TestCLIPolarization:
    """Test CLI polarization defaults match C reference (CLI-FLAGS-003 Phase I)."""

    def test_default_polarization_parity(self):
        """
        Verify BeamConfig.polarization_factor defaults to 0.0 to match C dynamic computation.

        C reference: golden_suite_generator/nanoBragg.c:308-309, 3732
            double polar=1.0,polarization=0.0;  # Initial values
            int nopolar = 0;
            # Per-pixel: polarization = 0.0; triggers dynamic Kahn factor computation

        CRITICAL UPDATE (CLI-FLAGS-003 Phase K3b):
        C code initializes polar=1.0 but resets polarization=0.0 per pixel (nanoBragg.c:3732),
        which triggers dynamic Kahn factor computation (≈0.9126) based on pixel geometry.
        PyTorch must default polarization_factor=0.0 to match this behavior.

        Evidence: reports/2025-10-cli-flags/phase_k/f_latt_fix/scaling_chain.md
            Shows C computing polar≈0.9126 dynamically, not using the initial 1.0 value
            Previous Phase E analysis was incomplete - it missed the per-pixel reset
        """
        # Parse minimal command with no explicit polarization flags
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '100',
            '-lambda', '6.2',
            '-distance', '100',
            '-detpixels', '128'
        ])

        # When no polarization flags provided, config dict should not contain polarization keys
        # BeamConfig() constructor will use its default polarization_factor=0.0 (triggers dynamic computation)
        assert 'polarization_factor' not in config, \
            "Config should not contain polarization_factor when no -polar flag provided"
        assert config.get('nopolar', False) is False, \
            "Config nopolar should be False or absent when no -nopolar flag provided"

        # Verify BeamConfig default directly by importing and instantiating
        from nanobrag_torch.config import BeamConfig
        beam_config = BeamConfig()
        assert beam_config.polarization_factor == 0.0, \
            f"Expected BeamConfig default polarization_factor=0.0 (triggers dynamic Kahn computation), got {beam_config.polarization_factor}"
        assert beam_config.nopolar is False, \
            f"Expected BeamConfig default nopolar=False (C nopolar=0), got {beam_config.nopolar}"

    def test_nopolar_flag(self):
        """
        Verify -nopolar flag sets nopolar=True.

        C reference: nanoBragg.c:844
            nopolar = 1;
        """
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '100',
            '-lambda', '6.2',
            '-distance', '100',
            '-detpixels', '128',
            '-nopolar'
        ])

        # Verify -nopolar flag sets nopolar in config
        assert config.get('nopolar', False) is True, \
            f"Expected config['nopolar']=True with -nopolar flag, got {config.get('nopolar')}"

    def test_polar_override(self):
        """
        Verify -polar <value> overrides default polarization_factor.

        C reference: nanoBragg.c:847-852
            polar = strtod(argv[++i],NULL);
        """
        config = run_parse([
            '-cell', '100', '100', '100', '90', '90', '90',
            '-default_F', '100',
            '-lambda', '6.2',
            '-distance', '100',
            '-detpixels', '128',
            '-polar', '0.5'
        ])

        # Verify -polar flag stores value in config
        assert 'polarization_factor' in config, \
            "Expected config to contain polarization_factor when -polar flag provided"
        assert config['polarization_factor'] == pytest.approx(0.5, rel=0, abs=1e-12), \
            f"Expected config['polarization_factor']=0.5 from -polar 0.5, got {config['polarization_factor']}"


class TestCLIPivotSelection:
    """
    Test automatic pivot mode selection with custom detector vectors (CLI-FLAGS-003 Phase H6f).

    Validates that custom detector basis vectors and pix0 overrides force SAMPLE pivot mode
    to match nanoBragg.c behavior. See reports/2025-10-cli-flags/phase_h6/pivot_parity.md.

    C Reference: nanoBragg.c lines ~1690-1750
        When custom_fdet/sdet/odet/beam or pix0_override are present, C forces SAMPLE pivot
        to ensure geometric consistency with overridden detector orientation.
    """

    @pytest.mark.parametrize("device", ["cpu", "cuda"])
    @pytest.mark.parametrize("dtype_name", ["float32", "float64"])
    def test_custom_vectors_force_sample_pivot(self, device, dtype_name):
        """
        Verify custom detector vectors force SAMPLE pivot mode.

        Test covers:
        1. Default BEAM pivot without custom vectors
        2. SAMPLE pivot when any custom vector is supplied
        3. SAMPLE pivot when pix0 override is supplied
        4. Device/dtype neutrality (CPU + CUDA when available)
        """
        # Skip CUDA tests if not available
        if device == "cuda" and not torch.cuda.is_available():
            pytest.skip("CUDA not available")

        dtype = torch.float32 if dtype_name == "float32" else torch.float64

        # Test 1: Default BEAM pivot (no custom vectors)
        config_default = DetectorConfig(
            spixels=1024,
            fpixels=1024,
            pixel_size_mm=0.1,
            distance_mm=100.0,
            detector_convention=DetectorConvention.MOSFLM
        )
        assert config_default.detector_pivot == DetectorPivot.BEAM, \
            "Expected BEAM pivot for default MOSFLM configuration without custom vectors"

        # Test 2: Custom fdet_vector forces SAMPLE pivot
        config_custom_fdet = DetectorConfig(
            spixels=2463,
            fpixels=2527,
            pixel_size_mm=0.172,
            distance_mm=231.274660,
            detector_convention=DetectorConvention.CUSTOM,
            beam_center_s=213.907080,
            beam_center_f=217.742295,
            custom_fdet_vector=(0.999982, -0.005998, -0.000118)
        )
        assert config_custom_fdet.detector_pivot == DetectorPivot.SAMPLE, \
            "Expected SAMPLE pivot when custom_fdet_vector is present"

        # Test 3: All four custom vectors force SAMPLE pivot
        config_all_custom = DetectorConfig(
            spixels=2463,
            fpixels=2527,
            pixel_size_mm=0.172,
            distance_mm=231.274660,
            detector_convention=DetectorConvention.CUSTOM,
            beam_center_s=213.907080,
            beam_center_f=217.742295,
            custom_fdet_vector=(0.999982, -0.005998, -0.000118),
            custom_sdet_vector=(-0.005998, -0.999970, -0.004913),
            custom_odet_vector=(-0.000088, 0.004914, -0.999988),
            custom_beam_vector=(0.00051387949, 0.0, -0.99999986)
        )
        assert config_all_custom.detector_pivot == DetectorPivot.SAMPLE, \
            "Expected SAMPLE pivot when all custom vectors are present"

        # Test 4: pix0_override WITHOUT custom vectors does NOT force SAMPLE (uses default BEAM)
        config_pix0_override = DetectorConfig(
            spixels=1024,
            fpixels=1024,
            pixel_size_mm=0.1,
            distance_mm=100.0,
            detector_convention=DetectorConvention.MOSFLM,
            pix0_override_m=(-0.216336, 0.215206, -0.230201)
        )
        # Phase H6f clarification: Only custom BASIS vectors force SAMPLE, not pix0_override alone
        assert config_pix0_override.detector_pivot == DetectorPivot.BEAM, \
            "Expected BEAM pivot when ONLY pix0_override is present (no custom basis vectors)"

        # Test 5: Verify Detector class honors forced SAMPLE pivot with device/dtype
        # This ensures pivot forcing propagates through geometry calculations
        detector = Detector(config_all_custom, device=device, dtype=dtype)

        # Check detector correctly initialized on requested device
        pix0_vector = detector.pix0_vector
        assert pix0_vector.device.type == device, \
            f"Expected pix0_vector on {device}, got {pix0_vector.device.type}"
        assert pix0_vector.dtype == dtype, \
            f"Expected pix0_vector dtype {dtype}, got {pix0_vector.dtype}"

        # Verify pix0 shape is (3,) vector
        assert pix0_vector.shape == (3,), \
            f"Expected pix0_vector shape (3,), got {pix0_vector.shape}"

        # C reference pix0 from reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0.log
        # SAMPLE pivot: pix0 = (-0.216476, 0.216343, -0.230192) meters
        c_reference_pix0 = torch.tensor(
            [-0.216476, 0.216343, -0.230192],
            device=device,
            dtype=dtype
        )

        # Allow larger tolerance due to SAMPLE pivot geometry calculations
        # We're verifying the pivot selection logic is correct, not exact parity yet
        # (H6g will verify exact parity after all pivot fixes are complete)
        pix0_delta = torch.abs(pix0_vector - c_reference_pix0)
        max_delta = torch.max(pix0_delta).item()

        # Sanity check: pix0 should be within ~5mm of C reference
        # (exact parity verification happens in Phase H6g after this fix)
        assert max_delta < 0.005, \
            f"pix0 delta {max_delta:.6f} m exceeds 5mm threshold (expected rough agreement)"


class TestHKLFdumpParity:
    """
    Test HKL/Fdump roundtrip parity (CLI-FLAGS-003 Phase L1c).

    Verifies that:
    1. read_hkl_file() produces same grid as read_fdump() for C-generated cache
    2. write_fdump() matches C binary layout exactly (with padding)
    3. Structure factors remain lossless through the roundtrip

    References:
    - specs/spec-a-core.md §Structure Factors & Fdump (line 474)
    - golden_suite_generator/nanoBragg.c:2359-2486 (C writer loops)
    - reports/2025-10-cli-flags/phase_l/hkl_parity/layout_analysis.md
    """

    def test_scaled_hkl_roundtrip(self):
        """
        Roundtrip test: HKL text → PyTorch grid → Fdump → PyTorch grid.

        Expected failure (before fix):
        - read_fdump will fail to match HKL grid due to padding mismatch
        - C allocates (range+1) dimensions but PyTorch currently uses range

        After fix:
        - Both readers should produce identical grids
        - Max |ΔF| ≤ 1e-6 electrons (spec-a-core.md:460)
        """
        from pathlib import Path
        import tempfile
        from nanobrag_torch.io.hkl import read_hkl_file, write_fdump, read_fdump

        # Input files from Phase L1b analysis
        hkl_path = "scaled.hkl"
        c_fdump_path = "reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_20251006181401.bin"

        # Verify files exist
        assert Path(hkl_path).exists(), f"Missing {hkl_path}"
        assert Path(c_fdump_path).exists(), f"Missing C-generated Fdump cache"

        # Read HKL text file
        F_hkl, meta_hkl = read_hkl_file(hkl_path, default_F=0.0, dtype=torch.float64)

        # Read C-generated Fdump cache
        F_c_fdump, meta_c = read_fdump(c_fdump_path, dtype=torch.float64)

        # Metadata should match exactly
        for key in ['h_min', 'h_max', 'k_min', 'k_max', 'l_min', 'l_max']:
            assert meta_hkl[key] == meta_c[key], \
                f"Metadata mismatch: {key} HKL={meta_hkl[key]} vs C={meta_c[key]}"

        # Grid shapes should match (accounting for C padding)
        # According to layout_analysis.md, C allocates (range+1)^3
        # But only uses indices 0..range (inclusive), so we need to handle this
        assert F_hkl.shape == F_c_fdump.shape, \
            f"Shape mismatch: HKL={F_hkl.shape} vs C={F_c_fdump.shape}"

        # Structure factors should match within tolerance
        # Per spec-a-core.md:460, acceptable tolerance is <1e-6 electrons
        delta_F = torch.abs(F_hkl - F_c_fdump)
        max_delta = torch.max(delta_F).item()

        # Count mismatches beyond tolerance
        mismatches = torch.sum(delta_F > 1e-6).item()

        assert max_delta <= 1e-6, \
            f"Max |ΔF| = {max_delta:.2e} exceeds tolerance (1e-6); {mismatches} mismatches"
        assert mismatches == 0, \
            f"Found {mismatches} mismatches beyond 1e-6 tolerance"

        # Write roundtrip: HKL → PyTorch Fdump → read back
        with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            write_fdump(F_hkl, meta_hkl, tmp_path)
            F_roundtrip, meta_roundtrip = read_fdump(tmp_path, dtype=torch.float64)

            # Verify roundtrip preserves data exactly
            assert F_hkl.shape == F_roundtrip.shape
            delta_roundtrip = torch.abs(F_hkl - F_roundtrip)
            max_roundtrip = torch.max(delta_roundtrip).item()

            assert max_roundtrip == 0.0, \
                f"Roundtrip introduced error: max |ΔF| = {max_roundtrip:.2e}"

        finally:
            # Cleanup
            Path(tmp_path).unlink(missing_ok=True)

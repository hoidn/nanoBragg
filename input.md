Summary: Port CUSTOM pix0 transform so PyTorch CLI parity matches C pix0 trace.
Phase: Implementation
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py -k pix0 -v
Artifacts: reports/2025-10-cli-flags/phase_f/pix0_transform_validation/

timestamp: 2025-10-06T02:54:20Z
commit: 1918c2b
author: galph
active focus: CLI-FLAGS-003 Phase F2 — port CUSTOM pix0 transform

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py -k pix0 -v
If Blocked: Capture current pix0/beam vectors via the Phase E Python snippet and log Attempt #12 in docs/fix_plan.md before proceeding.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:76 — Phase F2 demands replacing the early-return pix0 override with the CUSTOM transform copied from nanoBragg.c.
- docs/fix_plan.md:645 — Next actions already escalate F2 as the blocker before orientation (Phase G) work can begin.
- src/nanobrag_torch/models/detector.py:401 — Early return after setting pix0_override_m bypasses the rotation/pivot math; must be removed.
- docs/architecture/detector.md:35 — BEAM-pivot pix0 formula defines the reference math we need to reuse for CUSTOM overrides.
- specs/spec-a-cli.md:60 — CLI contract states `-pix0_vector` supplies meters, `_mm` supplies millimetres but still triggers CUSTOM convention.

How-To Map:
- `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py -k pix0 -v | tee reports/2025-10-cli-flags/phase_f/pix0_transform_validation/pytest.log`
- `NB_C_BIN=./golden_suite_generator/nanoBragg nanoBragg  -mat A.mat -floatfile img.bin -hkl scaled.hkl  -nonoise  -nointerpolate -oversample 1  -exposure 1  -flux 1e18 -beamsize 1.0  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080  -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866  -beam_vector 0.00051387949 0.0 -0.99999986  -Na 36  -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0` (store outputs under `reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/c_reference/`).
- `env KMP_DUPLICATE_LIB_OK=TRUE nanoBragg  -mat A.mat -floatfile torch_img.bin -hkl scaled.hkl  -nonoise  -nointerpolate -oversample 1  -exposure 1  -flux 1e18 -beamsize 1.0  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080  -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866  -beam_vector 0.00051387949 0.0 -0.99999986  -Na 36  -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0` (store outputs under `reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/pytorch/`).
- `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY'
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
parser = create_parser()
args = parser.parse_args("-mat A.mat -floatfile torch_img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0".split())
config = parse_and_validate_args(args)
detector = config['detector']
print("pix0_vector_meters", detector.pix0_vector)
print("beam_vector", detector.beam_vector)
PY
> reports/2025-10-cli-flags/phase_f/pix0_transform_validation/pix0_vector_after_f2.txt`

Pitfalls To Avoid:
- Keep `_calculate_pix0_vector` differentiable — no `.detach()`, `.cpu()`, or `.item()` on tensors that feed gradients.
- Preserve device/dtype neutrality; reuse existing tensors and `type_as` instead of hard-coding CPU allocations.
- Do not bypass the CUSTOM transform by reintroducing the early return; all overrides must flow through the BEAM/SAMPLE pivots.
- Respect Protected Assets (docs/index.md); do not delete or rename any indexed files while working in reports/.
- Avoid adding temporary scripts outside `scripts/`; use the plan’s report directories for artifacts.
- Maintain vectorization — no per-pixel Python loops when porting the C logic.
- Leave polarization work untouched until Phase G/H; focus on pix0 parity first.

Pointers:
- plans/active/cli-noise-pix0/plan.md:76 — Phase F2 guidance and exit criteria.
- docs/fix_plan.md:645 — Current next actions and outstanding checkpoints for `[CLI-FLAGS-003]`.
- src/nanobrag_torch/models/detector.py:401 — Early-return override path needing CUSTOM transform port.
- docs/architecture/detector.md:35 — Reference formulas for BEAM-pivot pix0 calculation.
- specs/spec-a-cli.md:60 — CLI contract for `-pix0_vector` / `_mm` semantics and CUSTOM convention trigger.

Next Up:
- [CLI-FLAGS-003] Phase F3 — rerun parity harness after pix0 transform (store under `phase_f/parity_after_detector_fix/`).
- [VECTOR-TRICUBIC-001] Phase A — capture tricubic/absorption baselines once CLI geometry is back in sync.

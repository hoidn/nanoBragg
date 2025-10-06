Summary: Capture beam-vector evidence for CLI-FLAGS-003 Phase E before touching implementation.
Phase: Evidence
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only this loop
Artifacts: reports/2025-10-cli-flags/phase_e/beam_vector_check.txt

Header:
- Timestamp: 2025-10-06T01:21:20Z
- Commit: 2e11820
- Author: galph
- Active Focus: CLI-FLAGS-003 Phase E — beam vector + pix0 parity diagnostics

Do Now: [CLI-FLAGS-003] Phase E0 beam-vector evidence — see How-To Map for inline python command.

If Blocked: If the CLI snippet dies on import/argparse, fall back to dumping `create_parser().parse_args([...])` into `reports/2025-10-cli-flags/phase_e/parser_dump.txt` and document the failure in docs/fix_plan.md Attempts.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md Phase E table now includes E0 for beam-vector parity; we need that artifact before rerunning traces.
- docs/fix_plan.md (CLI-FLAGS-003) calls out custom beam vector omission as a fresh divergence; evidence will unblock implementation guidance.
- docs/development/c_to_pytorch_config_map.md §Detector Parameters reminds us CUSTOM convention should inherit user beam vectors.
- docs/debugging/debugging.md §Parallel Trace Comparison forbids implementation changes before evidence and trace alignment.

How-To Map:
1. `mkdir -p reports/2025-10-cli-flags/phase_e`
2. `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python - <<'PY' > reports/2025-10-cli-flags/phase_e/beam_vector_check.txt
import torch
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
from nanobrag_torch.config import DetectorConfig, DetectorPivot, DetectorConvention
from nanobrag_torch.models.detector import Detector

args = create_parser().parse_args([
    '-mat','A.mat','-hkl','scaled.hkl','-lambda','0.9768','-oversample','1',
    '-pix0_vector_mm','-216.336293','215.205512','-230.200866',
    '-nonoise','-floatfile','/tmp/discard.bin',
    '-spindle_axis','-1','0','0','-Xbeam','217.742295','-Ybeam','213.907080',
    '-distance','231.274660','-pixel','0.172','-detpixels_x','2463','-detpixels_y','2527',
    '-odet_vector','-0.000088','0.004914','-0.999988',
    '-sdet_vector','-0.005998','-0.999970','-0.004913',
    '-fdet_vector','0.999982','-0.005998','-0.000118',
    '-beam_vector','0.00051387949','0.0','-0.99999986',
    '-Na','36','-Nb','47','-Nc','29','-osc','0.1','-phi','0','-phisteps','10',
    '-detector_rotx','0','-detector_roty','0','-detector_rotz','0','-twotheta','0'
])
config_dict = parse_and_validate_args(args)
config = DetectorConfig(
    distance_mm=config_dict['distance_mm'],
    pixel_size_mm=config_dict['pixel_size_mm'],
    spixels=config_dict['spixels'],
    fpixels=config_dict['fpixels'],
    beam_center_s=config_dict.get('beam_center_y_mm'),
    beam_center_f=config_dict.get('beam_center_x_mm'),
    detector_rotx_deg=config_dict['detector_rotx_deg'],
    detector_roty_deg=config_dict['detector_roty_deg'],
    detector_rotz_deg=config_dict['detector_rotz_deg'],
    detector_twotheta_deg=config_dict['twotheta_deg'],
    detector_pivot=DetectorPivot[config_dict['pivot']],
    detector_convention=DetectorConvention[config_dict['convention']],
    pix0_override_m=config_dict['pix0_override_m'],
    custom_fdet_vector=config_dict['custom_fdet_vector'],
    custom_sdet_vector=config_dict['custom_sdet_vector'],
    custom_odet_vector=config_dict['custom_odet_vector']
)
beam = Detector(config=config, dtype=torch.float64).beam_vector
print('beam_vector:', beam)
PY`
3. Annotate docs/fix_plan.md `[CLI-FLAGS-003]` Attempts with the artifact path and observed values (expected `[0., 0., 1.]` vs C log `0.00051387949 0 -0.99999986`).

Pitfalls To Avoid:
- No code edits until beam-vector evidence and Phase E traces exist.
- Keep snippet inline; do not add ad-hoc scripts outside `reports/` archives.
- Maintain `KMP_DUPLICATE_LIB_OK=TRUE` or the snippet will crash on MKL.
- Do not convert values to numpy or call `.item()` on tensors needed for later gradient work.
- Avoid rerunning parity command yet; we need first-divergence artifacts first.
- Do not touch docs/index.md or other protected assets.
- Leave `input.md` untouched after reading.
- Use existing plan/attempt IDs when updating docs/fix_plan.md.
- Preserve device/dtype neutrality in any subsequent prototypes.
- Honor two-message loop policy—capture evidence before implementations.

Pointers:
- plans/active/cli-noise-pix0/plan.md (Phase E table, task E0)
- docs/fix_plan.md (CLI-FLAGS-003 section)
- reports/2025-10-cli-flags/phase_d/intensity_gap.md (context for geometry mismatch)
- docs/development/c_to_pytorch_config_map.md §Detector parameters
- docs/debugging/debugging.md §Parallel Trace Comparison rule

Next Up: Once beam-vector evidence is captured, proceed to plan tasks E1–E3 to gather the full C/PyTorch trace set for the supervisor command.

timestamp: 2025-10-06T03:34:14Z
commit: f581141
author: galph
active focus: CLI-FLAGS-003 Phase F3 parity rerun

Summary: Capture C vs PyTorch parity evidence after detector fixes (Phase F3).
Phase: Evidence
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only
If Blocked: Re-run the pix0/beam vector Python snippet and log Attempt #12 with the resulting artifact under reports/2025-10-cli-flags/phase_f/ before escalating.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:78 keeps F3 open; parity evidence is required before advancing to Phase G.
- docs/fix_plan.md:458 calls for F3 artifacts and an Attempt #12 log prior to any orientation refactor.
- specs/spec-a-core.md:487 enforces the BEAM pivot pix0 formula that we must prove via C/PyTorch agreement.
- specs/spec-a-cli.md:14 mandates -mat parity with MOSFLM A*, so the recorded run must mirror the C configuration.
- docs/development/testing_strategy.md:162 requires parity artifacts before moving implementation forward.

How-To Map:
- `mkdir -p reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/c_reference && NB_C_BIN=./golden_suite_generator/nanoBragg \
  nanoBragg  -mat A.mat -floatfile reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/c_reference/img.bin \
  -hkl scaled.hkl  -nonoise  -nointerpolate -oversample 1  -exposure 1  -flux 1e18 -beamsize 1.0 \
  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080  -distance 231.274660 -lambda 0.976800 \
  -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986  -Na 36  -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 \
  -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 > \
  reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/c_reference/command.log 2>&1`
- `mkdir -p reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/pytorch && \
  env KMP_DUPLICATE_LIB_OK=TRUE nanoBragg  -mat A.mat -floatfile \
  reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/pytorch/torch_img.bin \
  -hkl scaled.hkl  -nonoise  -nointerpolate -oversample 1  -exposure 1  -flux 1e18 -beamsize 1.0 \
  -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080  -distance 231.274660 -lambda 0.976800 \
  -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 \
  -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 \
  -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 \
  -beam_vector 0.00051387949 0.0 -0.99999986  -Na 36  -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 \
  -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 > \
  reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/pytorch/command.log 2>&1`
- `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python - <<'PY'
from pathlib import Path
from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
parser = create_parser()
argv = "-mat A.mat -floatfile torch_img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0".split()
args = parser.parse_args(argv)
config = parse_and_validate_args(args)
detector = config['detector']
beam_vec = detector.beam_vector.detach().cpu().tolist()
pix0_vec = detector.pix0_vector.detach().cpu().tolist()
Path('reports/2025-10-cli-flags/phase_f/parity_after_detector_fix').mkdir(parents=True, exist_ok=True)
with open('reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/pytorch_pix0_beam.txt','w') as f:
    f.write(f"beam_vector {beam_vec}\n")
    f.write(f"pix0_vector {pix0_vec}\n")
PY`
- `env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only | tee reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/pytest_collect.log`

Pitfalls To Avoid:
- Do not edit source files; this loop is evidence-only.
- Keep all commands within the repo; honor Protected Assets and leave docs/index.md untouched.
- Always set KMP_DUPLICATE_LIB_OK=TRUE before importing torch or running pytest.
- Use the plan’s report directories; avoid scattering artifacts elsewhere or overwriting existing evidence.
- Ensure NB_C_BIN points at golden_suite_generator/nanoBragg to match the traced C binary.
- Maintain device/dtype neutrality if running Python snippets (no `.cpu()` on differentiable tensors except for logging copies).
- Capture stdout/stderr to the specified logs so fix_plan attempts can cite them.
- Do not delete `scaled.hkl.1` until parity evidence and documentation updates land together.
- Skip running heavy pytest suites beyond `--collect-only`; this loop gathers evidence, not regression results.
- Verify both commands complete without divergence before proceeding to Phase G.

Pointers:
- plans/active/cli-noise-pix0/plan.md:5 highlights the outstanding F3 parity gap and orientation follow-up.
- plans/active/cli-noise-pix0/plan.md:78 details the F3 task and artifact expectations.
- docs/fix_plan.md:458 enumerates the required Attempt #12 actions tied to this evidence run.
- specs/spec-a-cli.md:14 documents the -mat contract that must be honored in both runs.
- specs/spec-a-core.md:487 defines the BEAM pivot pix0 formula we are validating.
- docs/development/testing_strategy.md:162 reminds us to store parity artifacts alongside authoritative commands.
- src/nanobrag_torch/models/detector.py:520 shows the current pix0_override handling we are validating against the C trace.
- src/nanobrag_torch/__main__.py:425 converts A.mat into cell parameters but drops orientation, explaining the Phase G follow-up.

Next Up:
- [CLI-FLAGS-003] Phase G — retain MOSFLM A* orientation and refresh traces.
- [VECTOR-TRICUBIC-001] Phase A — capture tricubic/absorption baseline artifacts once parity evidence is banked.

2025-10-06T02:16:37Z | e3cd54c | galph | Active Focus: Restore CUSTOM detector parity for CLI parallel command
Summary: Implement Phase F2 pix0 override parity so PyTorch matches C for `-pix0_vector_mm`
Phase: Implementation
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none (manual parity harness per How-To Map)
Artifacts: reports/2025-10-cli-flags/phase_f/
Do Now: [CLI-FLAGS-003] Phase F2 — port CUSTOM pix0 transform; verify with parity harness (env KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch ...)
If Blocked: Capture updated detector trace reproducing the mismatch (store under reports/2025-10-cli-flags/phase_e/blocked/<timestamp>) and document the failure in docs/fix_plan.md Attempts History before pausing.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md — Phase F1 done; F2/F3 gate all downstream work, so finish CUSTOM pix0 transform next.
- docs/fix_plan.md:664 — Next Actions explicitly call for F2 implementation and rerunning validation snippet (current artifact empty).
- docs/development/c_to_pytorch_config_map.md §Detector Parameters — Confirms pix0/pivot semantics that must be mirrored from C.
- docs/debugging/detector_geometry_checklist.md — Required guardrails when touching detector origin math; re-read before editing.
- docs/development/testing_strategy.md §2 — Parallel trace + parity requirement after geometry edits; informs verification plan.
- reports/2025-10-cli-flags/phase_c/parity/SUMMARY.md — Baseline metrics (scale mismatch) to improve once pix0 parity lands.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md (keep for all shells this loop).
- mkdir -p reports/2025-10-cli-flags/phase_f/pix0_transform && cd /Users/ollie/Documents/nanoBragg3.
- After code edits, run:
  `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python - <<'PY'`
  ```python
  from pathlib import Path
  from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
  from nanobrag_torch.models.detector import Detector
  from nanobrag_torch.config import DetectorConfig
  import torch

  args = [
      "-mat", "A.mat",
      "-floatfile", "py_pix0_test.bin",
      "-hkl", "scaled.hkl",
      "-nonoise",
      "-nointerpolate",
      "-oversample", "1",
      "-exposure", "1",
      "-flux", "1e18",
      "-beamsize", "1.0",
      "-spindle_axis", "-1", "0", "0",
      "-Xbeam", "217.742295",
      "-Ybeam", "213.907080",
      "-distance", "231.274660",
      "-lambda", "0.976800",
      "-pixel", "0.172",
      "-detpixels_x", "2463",
      "-detpixels_y", "2527",
      "-odet_vector", "-0.000088", "0.004914", "-0.999988",
      "-sdet_vector", "-0.005998", "-0.999970", "-0.004913",
      "-fdet_vector", "0.999982", "-0.005998", "-0.000118",
      "-pix0_vector_mm", "-216.336293", "215.205512", "-230.200866",
      "-beam_vector", "0.00051387949", "0.0", "-0.99999986",
      "-Na", "36", "-Nb", "47", "-Nc", "29",
      "-osc", "0.1",
      "-phi", "0",
      "-phisteps", "10",
      "-detector_rotx", "0",
      "-detector_roty", "0",
      "-detector_rotz", "0",
      "-twotheta", "0"
  ]

  parser = create_parser()
  parsed = parse_and_validate_args(parser.parse_args(args))
  det_cfg = DetectorConfig(
      pixel_size_mm=parsed['pixel_size_mm'],
      distance_mm=parsed['distance_mm'],
      spixels=parsed['spixels'],
      fpixels=parsed['fpixels'],
      detector_convention=parsed['convention'],
      detector_pivot=parsed['pivot'],
      beam_center_s=parsed['beam_center_y_mm'],
      beam_center_f=parsed['beam_center_x_mm'],
      detector_rotx_deg=parsed['detector_rotx_deg'],
      detector_roty_deg=parsed['detector_roty_deg'],
      detector_rotz_deg=parsed['detector_rotz_deg'],
      detector_twotheta_deg=parsed['twotheta_deg'],
      custom_fdet_vector=parsed.get('custom_fdet_vector'),
      custom_sdet_vector=parsed.get('custom_sdet_vector'),
      custom_odet_vector=parsed.get('custom_odet_vector'),
      custom_beam_vector=parsed.get('custom_beam_vector'),
      pix0_override_m=parsed.get('pix0_override_m')
  )
  det = Detector(det_cfg, device=torch.device("cpu"), dtype=torch.float64)
  print("pix0_vector", det.pix0_vector)
  print("beam_vector", det.beam_vector)
  Path("reports/2025-10-cli-flags/phase_f/pix0_transform/pytorch_pix0.txt").write_text(str(det.pix0_vector.tolist()))
  PY
- Compare against C reference (`reports/2025-10-cli-flags/phase_e/c_trace_pix0.txt`); note tolerances (≤1e-12 diff expected).
- Populate `reports/2025-10-cli-flags/phase_f/beam_vector_after_fix.txt` with the tensor dump using the same snippet before proceeding.
- Run full parity after edits:
  * `NB_C_BIN=./golden_suite_generator/nanoBragg ./golden_suite_generator/nanoBragg -mat A.mat -floatfile reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/c_img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0`
  * `KMP_DUPLICATE_LIB_OK=TRUE nanoBragg -mat A.mat -floatfile reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/torch_img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0`
- Summarize findings in `reports/2025-10-cli-flags/phase_f/parity_after_detector_fix/SUMMARY.md` (include max intensity, correlation, pix0 vector diff) and log Attempt #11 in docs/fix_plan.md.
Pitfalls To Avoid:
- Do not bypass CUSTOM pix0 math (no early return once override present); replicate C’s pivot + rotation order exactly.
- Keep everything differentiable/device-neutral (no `.item()`, `.cpu()`, or dtype-specific tensors inside detector math).
- Maintain vectorization; do not reintroduce per-pixel Python loops for pix0 transforms.
- Respect Protected Assets (docs/index.md) — do not rename/delete listed files (e.g., loop.sh, input.md).
- Preserve existing detector cache invalidation logic; ensure new tensors reuse device/dtype helpers.
- No ad-hoc scripts outside documented directories; place diagnostics under `reports/2025-10-cli-flags/` only.
- Follow two-message loop policy: land evidence + update fix_plan before further code changes.
- Keep C vs PyTorch configs identical; consult docs/development/c_to_pytorch_config_map.md before adjusting parameters.
- Do not edit `scaled.hkl` contents except via documented reproduction (duplicate `scaled.hkl.1` will be removed once parity passes).
- Ensure `beam_vector_after_fix.txt` shows values (no empty artifact) before closing the loop.
Pointers:
- docs/architecture/detector.md §5 (pix0 derivation, pivot ordering)
- docs/debugging/detector_geometry_checklist.md (mandatory preflight)
- reports/2025-10-cli-flags/phase_e/trace_summary.md (latest divergence notes)
- plans/active/cli-noise-pix0/plan.md (Phase F to-do table)
- docs/development/testing_strategy.md §2.4 (golden command reference)
Next Up: If F2/F3 land early, move to Phase G1 (retain MOSFLM A* vectors) per plan before touching polarization.

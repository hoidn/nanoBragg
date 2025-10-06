2025-10-06T02:36:00Z | a50acc2 | galph | Active Focus: Finish CUSTOM beam vector wiring ahead of pix0 transform
Summary: Make `_calculate_pix0_vector()` honor user-supplied beam vectors so CUSTOM overrides drive parity evidence
Phase: Implementation
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — manual parity harness
Artifacts: reports/2025-10-cli-flags/phase_f/

Do Now: [CLI-FLAGS-003] Phase F1 — refactor detector pix0 override to call `Detector.beam_vector`; verify via validation snippet (env KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python ...)
If Blocked: Capture fresh detector trace showing the lingering default beam vector, store under reports/2025-10-cli-flags/phase_f/blocked/<timestamp>, and log the stall in docs/fix_plan.md Attempts before pausing.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md — Phase F1 reverted to [P]; helper still hardcodes convention defaults so CUSTOM beam input never lands.
- docs/fix_plan.md:664 — Next Actions explicitly call for the `_calculate_pix0_vector()` refactor and regenerated beam-vector artifact prior to Phase F2.
- docs/development/c_to_pytorch_config_map.md §Detector Parameters — Confirms CUSTOM overrides must traverse the same r-factor/pix0 math as meter-path inputs.
- docs/architecture/detector.md §5 — Details CUSTOM convention rotation/pivot ordering that the helper must reuse verbatim.
- docs/debugging/detector_geometry_checklist.md — Mandatory preflight; reinforces unit system and +0.5 pixel offset rules before edits.
- reports/2025-10-cli-flags/phase_e/trace_summary.md — Shows current parity harness only succeeds by injecting beam overrides manually.

How-To Map:
- export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md so subsequent shells inherit the authoritative command reference.
- Re-read docs/debugging/detector_geometry_checklist.md and docs/architecture/detector.md §5 before editing; note CUSTOM pivot sequence and meter⇄millimeter conversions.
- Update `_calculate_pix0_vector()` BEAM-pivot branch to reuse `self.beam_vector` (tensor on caller device/dtype) instead of instantiating convention defaults; ensure pix0 override retains differentiability and cache invalidation.
- Run the validation snippet below after edits to repopulate beam/pix0 artifacts and confirm CUSTOM vector usage:
  ```python
  import torch
  from pathlib import Path
  from nanobrag_torch.__main__ import create_parser, parse_and_validate_args
  from nanobrag_torch.config import DetectorConfig
  from nanobrag_torch.models.detector import Detector

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
      "-Na", "36",
      "-Nb", "47",
      "-Nc", "29",
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
      distance_mm=parsed['distance_mm'],
      close_distance_mm=parsed.get('close_distance_mm'),
      pixel_size_mm=parsed['pixel_size_mm'],
      spixels=parsed['spixels'],
      fpixels=parsed['fpixels'],
      detector_rotx_deg=parsed['detector_rotx_deg'],
      detector_roty_deg=parsed['detector_roty_deg'],
      detector_rotz_deg=parsed['detector_rotz_deg'],
      detector_twotheta_deg=parsed['twotheta_deg'],
      detector_convention=parsed['convention'],
      detector_pivot=parsed['pivot'],
      beam_center_s=parsed['beam_center_y_mm'],
      beam_center_f=parsed['beam_center_x_mm'],
      custom_fdet_vector=parsed.get('custom_fdet_vector'),
      custom_sdet_vector=parsed.get('custom_sdet_vector'),
      custom_odet_vector=parsed.get('custom_odet_vector'),
      custom_beam_vector=parsed.get('custom_beam_vector'),
      pix0_override_m=parsed.get('pix0_override_m')
  )
  det = Detector(det_cfg, device=torch.device("cpu"), dtype=torch.float64)
  Path("reports/2025-10-cli-flags/phase_f/beam_vector_after_fix.txt").write_text(f"{det.beam_vector.tolist()}\n")
  Path("reports/2025-10-cli-flags/phase_f/pix0_vector_after_fix.txt").write_text(f"{det.pix0_vector.tolist()}\n")
  print("beam_vector", det.beam_vector)
  print("pix0_vector", det.pix0_vector)
  ```
- Diff the new pix0 vector against `reports/2025-10-cli-flags/phase_e/c_trace_beam.log` (expect ≤1e-12 delta); log results in a short summary under `reports/2025-10-cli-flags/phase_f/beam_vector_check.md`.
- After verification, add Attempt #11 to docs/fix_plan.md capturing commands, artifacts, and observed deltas before moving to Phase F2.

Pitfalls To Avoid:
- Do not keep the early-return path that bypasses CUSTOM math when `pix0_override_m` is present.
- Preserve differentiability and device/dtype neutrality (avoid `.item()`, `.cpu()`, or mismatched tensor factories).
- Keep detector geometry vectorized; no per-pixel or per-axis Python loops.
- Obey Protected Assets (docs/index.md) — no renaming/removing indexed files.
- Ensure detector caches invalidate once pix0 or beam vectors change; regen `_cached_*` tensors as needed.
- Store probes under reports/2025-10-cli-flags/ (no ad-hoc temp scripts elsewhere).
- Document evidence before edits escalate; parallel trace discipline still applies.
- Confirm artifact files are non-empty and readable before committing or logging.

Pointers:
- plans/active/cli-noise-pix0/plan.md#phase-f-—-detector-implementation-beam--pix0-parity
- docs/fix_plan.md:664
- docs/development/c_to_pytorch_config_map.md
- docs/architecture/detector.md#5-detector-origin-and-pivots
- docs/debugging/detector_geometry_checklist.md
- reports/2025-10-cli-flags/phase_e/trace_summary.md

Next Up: If F1 lands quickly, proceed to Phase F2 (CUSTOM pix0 transform) under the same plan before attempting parity reruns.

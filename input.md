Header:
- Timestamp: 2025-10-06T01:44:49Z
- Commit: c1588b7
- Author: galph
- Active Focus: [CLI-FLAGS-003] Phase F — detector parity (beam vector + CUSTOM pix0)

Do Now: [CLI-FLAGS-003] Phase F1 — thread custom beam vector; verify with `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python - <<'PY' ...` (see How-To Map).

If Blocked: Capture failure details to `reports/2025-10-cli-flags/phase_f/beam_vector_after_fix.txt`, log Attempt in docs/fix_plan.md, then pivot to documenting the blocker in `reports/2025-10-cli-flags/phase_f/blockers.md`.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md Phase F table demands wiring `custom_beam_vector` before pix0 or matrix fixes proceed.
- docs/fix_plan.md:664-836 records traced divergences; closing Phase F1 unlocks subsequent parity actions.
- docs/development/c_to_pytorch_config_map.md:40-140 documents detector convention defaults you must honor while adding overrides.
- docs/debugging/debugging.md:1-120 mandates parity-first workflow; we’ll rerun the harness immediately after the wiring change.

How-To Map:
1. Implement Phase F1: propagate `custom_beam_vector` from CLI config into `DetectorConfig` and `Detector` so CUSTOM convention uses it everywhere beam direction is consumed.
2. Rebuild editable install if imports complain: `pip install -e .`.
3. Validate wiring with a focused harness run:
   ```bash
   KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python - <<'PY'
   import torch
   from nanobrag_torch.config import DetectorConfig, DetectorConvention, DetectorPivot
   from nanobrag_torch.models.detector import Detector
   cfg = DetectorConfig(
       distance_mm=231.274660,
       pixel_size_mm=0.172,
       spixels=2463,
       fpixels=2527,
       beam_center_s=213.907080,
       beam_center_f=217.742295,
       detector_convention=DetectorConvention.CUSTOM,
       detector_pivot=DetectorPivot.BEAM,
       custom_fdet_vector=(0.999982, -0.005998, -0.000118),
       custom_sdet_vector=(-0.005998, -0.999970, -0.004913),
       custom_odet_vector=(-0.000088, 0.004914, -0.999988),
       custom_beam_vector=(0.00051387949, 0.0, -0.99999986),
       pix0_override_m=(-0.216336293, 0.215205512, -0.230200866),
       oversample=1
   )
   det = Detector(cfg, device='cpu', dtype=torch.float64)
   print('beam_vector:', det.beam_vector)
   PY
   ```
4. Save stdout to `reports/2025-10-cli-flags/phase_f/beam_vector_after_fix.txt` (expect `[5.1387949e-04, 0.0000000e+00, -9.9999986e-01]`).
5. Update docs/fix_plan.md Attempt history and mark plan task F1 complete once the snippet reports the custom vector.

Pitfalls To Avoid:
- Leave pix0 override logic untouched until Phase F2; avoid mixing fixes.
- Preserve differentiability: no `.detach()`, `.cpu()`, or `.item()` inside new code paths.
- Maintain device/dtype neutrality—coerce via `.to()` relative to existing tensors.
- Keep Protected Assets intact (loop.sh, input.md, docs/index.md references).
- Defer deleting `scaled.hkl.1` until implementation pass concludes.
- Re-run only the targeted harness; no broad pytest sweep yet.
- Retain trace harness override notes so parity reruns capture native behavior post-fix.
- Log every attempt (success or failure) in docs/fix_plan.md with artifact paths.

Pointers:
- plans/active/cli-noise-pix0/plan.md (Phase F)
- docs/fix_plan.md:664-836 (`[CLI-FLAGS-003]` status & attempts)
- docs/architecture/detector.md:1-250 (CUSTOM basis & pivot formulas)
- docs/development/testing_strategy.md:2.1 (parallel validation expectations)
- reports/2025-10-cli-flags/phase_e/trace_summary.md (current divergence evidence)

Next Up:
- Phase F2 — port CUSTOM pix0 transform once beam vector parity is proven.

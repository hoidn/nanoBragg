Summary: Capture concrete evidence that PyTorch still selects BEAM pivot while C runs the supervisor case in SAMPLE.
Phase: Evidence
Focus: CLI-FLAGS-003 Phase H6e — pivot parity proof
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_h6/pivot_parity.md
Do Now: CLI-FLAGS-003 H6e — Confirm pivot parity; run `PYTHONPATH=src python - <<'PY'\nfrom nanobrag_torch.config import DetectorConfig, DetectorConvention\nconfig = DetectorConfig(spixels=2463, fpixels=2527, pixel_size_mm=0.172, distance_mm=231.274660, detector_convention=DetectorConvention.CUSTOM, beam_center_s=213.907080, beam_center_f=217.742295, pix0_override_m=(-216.336293/1000, 215.205512/1000, -230.200866/1000), custom_fdet_vector=(0.999982, -0.005998, -0.000118), custom_sdet_vector=(-0.005998, -0.999970, -0.004913), custom_odet_vector=(-0.000088, 0.004914, -0.999988), custom_beam_vector=(0.00051387949, 0.0, -0.99999986))\nprint(config.detector_pivot)\nPY` and summarise alongside the C trace message in the artifact.
If Blocked: Record pivot evidence attempt (command + stderr) in reports/2025-10-cli-flags/phase_h6/attempts.log and flag in Attempts History before proceeding.
Priorities & Rationale:
- specs/spec-a-cli.md:136 — custom vectors force CUSTOM convention; document how C treats pivot.
- docs/architecture/detector.md:109 — pivot determination checklist to cite in parity memo.
- plans/active/cli-noise-pix0/plan.md:130 — Phase H6e freshly added; this memo executes that row.
- docs/fix_plan.md:448 — Next Actions now require pivot proof before implementation.
How-To Map:
- Extract C evidence: `grep -n "pivoting" reports/2025-10-cli-flags/phase_h6/c_trace/trace_c_pix0.log >> reports/2025-10-cli-flags/phase_h6/pivot_parity.md`.
- Run the inline Python snippet above (use PYTHONPATH=src) and append output with context to the same markdown.
- In the artifact, note that SAMPLE pivot message appears in C while the Python snippet reports DetectorPivot.BEAM.
Pitfalls To Avoid:
- Do not modify source files yet; this loop is evidence-only.
- Keep PYTHONPATH pointing at src so the editable build is used.
- Avoid running pytest or nb-compare in Evidence phase.
- Preserve existing trace logs; add new files instead of overwriting.
- Document units (mm vs m) explicitly in the memo.
- Capture command invocations verbatim for reproducibility.
- Respect Protected Assets (docs/index.md, loop.sh, input.md).
Pointers:
- specs/spec-a-cli.md:136
- docs/architecture/detector.md:109
- plans/active/cli-noise-pix0/plan.md:130
- docs/fix_plan.md:448
Next Up: Phase H6f — adjust DetectorConfig pivot logic and add regression test once pivot parity evidence lands.

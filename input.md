Summary: Capture fresh C & PyTorch evidence that pix0 override applies with custom vectors before touching normalization.
Phase: Evidence
Focus: [CLI-FLAGS-003] Phase H5 — Custom Vector Pix0 Override
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-21/, reports/2025-10-cli-flags/phase_h5/py_traces/, reports/2025-10-cli-flags/phase_h5/parity_summary.md
Do Now: [CLI-FLAGS-003] H5a/H5c — capture fresh C & PyTorch parity traces (run NB_C_BIN and harness commands in How-To Map).

If Blocked: Document the obstruction in reports/2025-10-cli-flags/phase_h5/ATTEMPTS.md with command output snippets; note the block in docs/fix_plan.md Attempts History.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:115 — Phase H5 now marks H5b complete; H5a/H5c evidence gate Phase K normalization.
- docs/fix_plan.md:452 — Next Actions call for refreshed C traces + PyTorch parity before closing Attempt #29.
- specs/spec-a-cli.md:55 — Confirms `-pix0_vector_mm` semantics we must validate against C.
- docs/debugging/detector_geometry_checklist.md:1 — Required before any detector-geometry parity work.
- docs/development/testing_strategy.md:95 — Evidence phase rules: collect traces before touching implementation/tests.

How-To Map:
- Export NB_C_BIN=./golden_suite_generator/nanoBragg; mkdir -p reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-21/.
- Run C WITHOUT override:
  NB_C_BIN=./golden_suite_generator/nanoBragg \
  $NB_C_BIN -mat A.mat -floatfile /tmp/c_no_override.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 \
  2>&1 | tee reports/2025-10-cli-flags/phase_h5/c_traces/2025-10-21/without_override.log
- Run C WITH override (same command plus `-pix0_vector_mm -216.336293 215.205512 -230.200866`) and capture to `with_override.log`.
- Update reports/2025-10-cli-flags/phase_h5/c_precedence.md with the new values (pix0, Fbeam/Sbeam, h/k/l) noting the 2025-10-06 conclusion is obsolete.
- Copy reports/2025-10-cli-flags/phase_h/trace_harness.py to phase_h5/trace_harness.py, extend logging to print pix0/Fbeam/Sbeam, fractional h/k/l, and F_latt components after override fix.
- Run PyTorch harness: PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h5/trace_harness.py > reports/2025-10-cli-flags/phase_h5/py_traces/with_override.log.
- Append numeric deltas vs C traces to reports/2025-10-cli-flags/phase_h5/parity_summary.md (note tolerances: 5e-5 m for pix0/Fbeam/Sbeam, 1e-3 relative for F_latt components).

Pitfalls To Avoid:
- Do not edit CLI or detector code until H5 evidence is archived.
- Preserve device/dtype neutrality in any harness tweaks (use detector.dtype/device bindings).
- Keep NB_C_BIN pointing at golden_suite_generator/nanoBragg; no rebuilds on frozen binary.
- Avoid running pytest during evidence phase; only capture traces.
- When copying harness scripts, maintain ASCII and include Phase H5 header comments.
- Ensure directories under reports/ are created before redirecting output to avoid silent failures.
- Record the exact commands in the artifacts for reproducibility.
- Do not overwrite previous logs; use the 2025-10-21 subdirectory for new C evidence.
- Keep KMP_DUPLICATE_LIB_OK=TRUE set for all Python invocations involving torch.
- Update docs/fix_plan.md only after artifacts exist.

Pointers:
- plans/active/cli-noise-pix0/plan.md:115
- docs/fix_plan.md:452
- specs/spec-a-cli.md:55
- docs/debugging/detector_geometry_checklist.md:1
- reports/2025-10-cli-flags/phase_h5/parity_summary.md

Next Up: Once H5 evidence is in place, proceed to Phase K1 normalization fix per plans/active/cli-noise-pix0/plan.md.

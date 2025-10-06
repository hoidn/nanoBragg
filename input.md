Summary: Capture C/PyTorch base-lattice traces to isolate the Δk≈6 gap.
Phase: Evidence
Focus: CLI-FLAGS-003 / Phase K3f — Base lattice & scattering parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_k/base_lattice/
Do Now: CLI-FLAGS-003 Phase K3f1 – run `timeout 30 ./golden_suite_generator/nanoBragg -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 2>&1 | tee reports/2025-10-cli-flags/phase_k/base_lattice/c_trace.log`
If Blocked: Capture a fresh per-φ summary via `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python scripts/trace_per_phi.py --out reports/2025-10-cli-flags/phase_k/base_lattice/per_phi_probe.json` and log the failure in Attempts History.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md (Phase K3f table) mandates C+Py baseline traces before any normalization fixes.
- docs/fix_plan.md (CLI-FLAGS-003 Next Actions) now points to K3f1–K3f4 as the gating work toward long-term goal #1.
- specs/spec-a-core.md (lattice factor) is needed to interpret h/k/l tolerances while reviewing trace output.
- docs/architecture/detector.md (SAMPLE pivot & beam definitions) anchors expected pixel geometry for Δk diagnosis.
How-To Map:
- Add `TRACE_C_BASE` printf blocks near MOSFLM load, real-vector recomputation, and scattering-vector setup inside `golden_suite_generator/nanoBragg.c`; rebuild with `timeout 30 make -C golden_suite_generator`.
- Run the Do Now command; confirm the log includes MOSFLM a*/b*/c*, real a/b/c, and φ=0 scattering vector components; stash under base_lattice/c_trace.log.
- Mirror the fields in PyTorch by extending `reports/2025-10-cli-flags/phase_k/trace_harness.py` to emit `TRACE_PY_BASE` lines, then execute `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_k/trace_harness.py --out reports/2025-10-cli-flags/phase_k/base_lattice/trace_py.log`.
- Note any instrumentation edits in Attempts History; keep CLAUDE Rule #8 (reuse production helpers) intact.
Pitfalls To Avoid:
- Do not modify simulator normalization paths yet; this loop is evidence-only.
- Keep instrumentation in `golden_suite_generator/` and reports scripts—no hacks inside src/ modules.
- Preserve SAMPLE pivot behavior; avoid toggling detector pivots while logging data.
- Ensure logs print double precision (%.15g) to match existing trace tooling.
- Avoid `pytest` entirely this loop; Evidence phase forbids it.
- Verify `NB_C_BIN` points to the instrumented binary before running.
- Don’t rely on cached pixel coordinates—reinitialize detector if basis vectors change.
- Retain the `TRACE_*` prefixes exactly; comparison tooling expects them.
Pointers:
- plans/active/cli-noise-pix0/plan.md (Phase K3f tasks)
- docs/fix_plan.md (CLI-FLAGS-003 entry)
- docs/architecture/detector.md (§5 pix0 & pivots)
- docs/architecture/pytorch_design.md (§2 lattice pipeline)
- specs/spec-a-core.md (§4 lattice factor equations)
Next Up: Phase K3f3 diff/summary once both traces land.

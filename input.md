Summary: Instrument the C binary for per-φ traces and regenerate comparison artifacts without reporting false parity.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<timestamp>/, reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<timestamp>/c_trace_phi_<timestamp>.log, reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<timestamp>/diagnosis.md
Do Now: CLI-FLAGS-003 · Phase L3k.3b — add TRACE_C_PHI instrumentation to golden_suite_generator/nanoBragg.c, rebuild, then run NB_C_BIN=./golden_suite_generator/nanoBragg -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 2>&1 | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<timestamp>/c_trace_phi_<timestamp>.log
If Blocked: Capture the failing stdout/patch under reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<timestamp>/blocked.md, stash any partial changes, run pytest --collect-only -q, and log the selector + failure text in blocked.md.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:33 — L3k.3b now mandates C instrumentation plus truthful BLOCKED reporting before VG gates.
- docs/fix_plan.md:458 — Next Actions call out the missing TRACE_C_PHI data and the false ✅ summary that must be corrected.
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/comparison_summary.md — currently misreports parity because C trace was empty.
- specs/spec-a-cli.md:129 — Confirms φ sampling (osc=0.1 with phisteps=10) that the harness and C run must match.
- docs/debugging/debugging.md:41 — Parallel trace SOP requires C and PyTorch traces before diagnosing physics discrepancies.

How-To Map:
- export TAG=$(date +%Y%m%d%H%M)
- mkdir -p reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TAG
- Edit golden_suite_generator/nanoBragg.c inside the φ loop (see nanoBragg.c:3044-3068) to emit TRACE_C_PHI lines for h,k,l, rot_b, k_frac, F_latt.
- timeout 120 make -C golden_suite_generator
- NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE ./golden_suite_generator/nanoBragg -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 2>&1 | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TAG/c_trace_phi_$TAG.log
- PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --out trace_py_rot_vector_$TAG.log --device cpu --dtype float64
- mv trace_py_rot_vector_$TAG.log reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TAG/
- mv reports/2025-10-cli-flags/phase_l/per_phi/trace_py_rot_vector_$TAG_per_phi.* reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TAG/
- python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TAG/trace_py_rot_vector_$TAG_per_phi.json reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TAG/c_trace_phi_$TAG.log > reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TAG/comparison_stdout.txt
- Edit comparison_summary.md so it reports BLOCKED when C entries are missing, then write diagnosis.md capturing k_frac deltas, TRACE_C availability, and next hypotheses. Copy updates into fix_checklist.md VG-1.4. Finish with pytest --collect-only -q | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TAG/pytest_collect.log

Pitfalls To Avoid:
- Do not leave TRACE_C instrumentation in repo without noting it; keep changes under golden_suite_generator/ only.
- No ✅ wording in comparison outputs when C data is absent—explicitly mark BLOCKED.
- Ensure NB_C_BIN points at the rebuilt binary; don’t accidentally invoke the frozen root ./nanoBragg.
- Maintain CPU + float64 parity; avoid CUDA for these traces.
- Preserve prior artifacts; use the new $TAG subdir rather than overwriting 20251122.
- Keep vectorization (no manual loops) when touching trace harness; follow docs/architecture/pytorch_design.md.
- Remember Protected Assets from docs/index.md (input.md, loop.sh, etc.) when editing.
- If make fails, do not partially commit; document the failure and revert instrumentation.
- Don’t run nb-compare yet; ROI work lives in L3k.3d.
- Avoid editing production PyTorch code in this loop.

Pointers:
- plans/active/cli-noise-pix0/plan.md:33
- docs/fix_plan.md:455
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/comparison_summary.md
- docs/debugging/debugging.md:41
- specs/spec-a-cli.md:90

Next Up:
1. L3k.3d — repair nb-compare ROI metrics after per-φ parity is unblocked.
2. L3k.3e — finalize documentation and prepare the L3k.4 attempt log.

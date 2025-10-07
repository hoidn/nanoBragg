Summary: Regenerate C HKL cache and confirm PyTorch HKL parity so Phase L can advance to scaling diagnostics.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase L1d structure-factor parity refresh
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip
Artifacts: reports/2025-10-cli-flags/phase_l/hkl_parity/summary_20251109.md; reports/2025-10-cli-flags/phase_l/hkl_parity/metrics_20251109.json; reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_c_20251109.bin
Do Now: CLI-FLAGS-003 L1d — KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python scripts/validation/compare_structure_factors.py --hkl scaled.hkl --fdump reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_c_20251109.bin --out reports/2025-10-cli-flags/phase_l/hkl_parity/summary_20251109.md --metrics reports/2025-10-cli-flags/phase_l/hkl_parity/metrics_20251109.json
If Blocked: Capture the blocking command output under reports/2025-10-cli-flags/phase_l/hkl_parity/attempt_blocked.log and note the failure in docs/fix_plan.md Attempts before escalating.
Priorities & Rationale:
- specs/spec-a-cli.md:1 — CLI spec mandates C↔Py structure-factor parity before flag acceptance is complete.
- docs/architecture/detector.md:5 — Ensures pix0/pivot context used when interpreting parity deltas.
- docs/development/testing_strategy.md:120 — Parallel validation matrix requires targeted parity checks before full nb-compare reruns.
- plans/active/cli-noise-pix0/plan.md:218 — L1d exit criteria define the evidence bundle we must collect this loop.
How-To Map:
- export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md
- Regenerate the cache first: NB_C_BIN=./golden_suite_generator/nanoBragg nanoBragg -mat A.mat -floatfile /tmp/discard.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 -floatfile /dev/null -intfile /dev/null -noiseimage /dev/null -Fdump reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_c_20251109.bin
- Then run the Do Now command to produce summary and metrics; keep outputs under reports/2025-10-cli-flags/phase_l/hkl_parity/.
- Validate mapped pytest node with `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_flags.py::TestHKLFdumpParity::test_scaled_hkl_roundtrip` (collection only under supervisor evidence gate).
Pitfalls To Avoid:
- Do not skip setting KMP_DUPLICATE_LIB_OK before any torch import or CLI call.
- No edits outside planning/docs; production code stays untouched this loop.
- Preserve device/dtype neutrality when running scripts (use cpu by default, no implicit `.cpu()` copies).
- Avoid overwriting prior parity artefacts; use new timestamped filenames.
- Remember Protected Assets rule — never move or delete files referenced in docs/index.md.
- Do not run full pytest suite; stick to targeted collection/tests per instructions.
- Keep nb-compare unused until HKL parity metrics clear the 1e-6 threshold.
- Ensure reports/ paths exist before writing artefacts to avoid accidental repo clutter.
- No torch.compile caches cleared during evidence-only loops.
- Record any deviations in docs/fix_plan.md Attempts immediately.
Pointers:
- plans/active/cli-noise-pix0/plan.md:218
- docs/fix_plan.md:448
- scripts/validation/compare_structure_factors.py:1
- specs/spec-a-cli.md:1
- docs/development/testing_strategy.md:120
Next Up: Phase L2 scaling-chain rerun once HKL parity hits ≤1e-6 with zero mismatches.

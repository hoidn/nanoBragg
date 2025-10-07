Summary: Finish CLI-FLAGS-003 Phase L3k.3 by capturing φ-rotation parity evidence before logging the attempt.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/
Artifacts: reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/comparison_summary.txt
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/pytest_vg2_refresh.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/trace_py_rot_vector_postfix_per_phi.json
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/trace_py_rot_vector_postfix_per_phi.log
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/sha256.txt
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/env_snapshot.txt
Artifacts: docs/fix_plan.md
Do Now: CLI-FLAGS-003 Phase L3k.3 (VG-1/VG-3/VG-4) — env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c -v (confirm parity after evidence capture).
If Blocked: Park raw per-φ logs + notes under reports/2025-10-cli-flags/phase_l/rot_vector/blockers/ and flag the delta that stopped nb-compare so we can revisit with fresh guidance.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:285 names VG-1⇢VG-5 as the last hurdles before the supervisor command rerun.
- docs/fix_plan.md:457 now points Next Actions at L3k.3, so today’s loop must deliver the outstanding verification gates.
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:1 tracks gate status; VG-2 is ✅ and VG-1/VG-3/VG-4/VG-5 remain ⏸️.
- specs/spec-a-cli.md:30 anchors φ/oscillation semantics, giving us the correctness targets for the trace evidence.
- docs/architecture/detector.md:112 covers pivot math we must hold invariant while collecting per-φ traces.
- reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md:274 lists VG thresholds (b_Y, k_frac, I_ratio) we must annotate in the comparison doc.
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md:302 captures prior hypotheses; use it to cross-check that new evidence closes H5 without reopening earlier ones.
How-To Map:
- Ensure PYTHONPATH includes src (export PYTHONPATH=src) before running harness commands.
- cd reports/2025-10-cli-flags/phase_l/rot_vector && mkdir -p per_phi_postfix && KMP_DUPLICATE_LIB_OK=TRUE python trace_harness.py --pixel 685 1039 --out per_phi_postfix/trace_py_rot_vector_postfix.log --config supervisor --device cpu --dtype float32
- Confirm the harness wrote per-φ logs to reports/2025-10-cli-flags/phase_l/per_phi/trace_py_rot_vector_postfix_per_phi.{log,json}; copy them into per_phi_postfix/ for this attempt.
- python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/trace_py_rot_vector_postfix_per_phi.json reports/2025-10-cli-flags/phase_l/per_phi/trace_c_per_phi.log > reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/comparison_summary.txt
- grep "TRACE_PY_PHI" per_phi_postfix/trace_py_rot_vector_postfix.log | wc -l (expect 10 φ steps) and note the count in fix_checklist VG-1 entries.
- sha256sum per_phi_postfix/* > reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/sha256.txt for reproducibility metadata.
- ls -lh reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/ >> reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/listing.txt to capture artefact sizes for audit trail.
- python - <<'PY'
import json
data = json.load(open('reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/trace_py_rot_vector_postfix_per_phi.json'))
vals = [entry['k_frac'] for entry in data['traces']]
print('φ entries:', len(vals))
print('k_frac span:', max(vals) - min(vals))
PY >> reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/comparison_summary.txt
- Inspect comparison_summary.txt for Δk, ΔF_latt_b, and note whether all rows flip to ✅; capture highlights in rot_vector_comparison.md.
- nb-compare --roi 100 156 100 156 --resample --outdir reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/ -- -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0
- Record correlation, sum_ratio, and mean_peak_distance from nb_compare output in rot_vector_comparison.md and fix_checklist.md VG-3 rows; stash JSON + PNG artefacts in nb_compare_phi_fix/.
- python - <<'PY'
import json
from pathlib import Path
summary = json.load(open('reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/summary.json'))
print('Correlation:', summary['correlation'])
print('Sum ratio:', summary['sum_ratio'])
print('Mean peak distance:', summary['mean_peak_distance'])
PY
- tee reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/env_snapshot.txt <<<'NB_C_BIN='"${NB_C_BIN:-./golden_suite_generator/nanoBragg}"' PYTHONPATH='"${PYTHONPATH}"' TORCH_VERSION='$(python - <<'PY'
import torch
print(torch.__version__)
PY
)' ensures env data is captured beside the traces.
- env KMP_DUPLICATE_LIB_OK=TRUE NB_RUN_PARALLEL=1 pytest tests/test_cli_scaling.py::TestFlattSquareMatchesC::test_f_latt_square_matches_c -v | tee reports/2025-10-cli-flags/phase_l/rot_vector/pytest_vg2_refresh.log (rerun after evidence to ensure no regressions).
- Update reports/2025-10-cli-flags/phase_l/rot_vector/rot_vector_comparison.md with new b_Y, k_frac, F_latt, I_before_scaling deltas referencing the copied per-φ logs and nb-compare metrics.
- Mark VG-1/VG-3/VG-4/VG-5 rows in fix_checklist.md to ✅ with artifact links; include comparison_summary, nb-compare summary.json, and pytest log.
- Append a new Attempt in docs/fix_plan.md (CLI-FLAGS-003) capturing the metrics, artefact paths, and noting readiness for Phase L4.
- Verify plans/active/cli-noise-pix0/plan.md reflects the updated checklist status before closing the loop.
Pitfalls To Avoid:
- Don’t overwrite existing per_phi/ logs; copy them aside before rerunning the harness.
- Keep KMP_DUPLICATE_LIB_OK=TRUE on every Python/pytest invocation to prevent MKL errors.
- Stay in evidence-only mode—no simulator or model edits under this memo.
- Use the supervisor command paths verbatim; altered floatfile/hkl inputs invalidate VG-3 results.
- Capture SHA256 checksums for new logs placed outside git to aid reproducibility.
- Append to existing markdown analyses rather than deleting historical context.
- Maintain CUSTOM convention inputs; do not toggle to MOSFLM/XDS during trace capture.
- Leave tensors on float32 CPU; no `.cuda()`, `.to()` overrides, or dtype switches mid-harness.
- Update fix_plan and checklist only after verifying artefacts exist on disk.
- Keep Attempt numbering sequential and note NB_C_BIN used when logging results.
- Capture command transcripts with `script` if you hit discrepancies, then attach the log under rot_vector/postfix/ for review.
- Double-check that per_phi_postfix/sha256.txt includes both .log and .json entries before accepting VG-1.
- Keep nb_compare output directories timestamped if you need multiple runs (nb_compare_phi_fix/2025MMDD-HHMMSS/).
- Make sure comparison_summary.txt and rot_vector_comparison.md reference each other so future readers see provenance.
- Review harness stdout for WARN/ERROR strings; unresolved warnings invalidate VG-1 until investigated.
- Keep PYTHONPATH consistent; mixing editable-install imports with absolute paths can yield stale modules.
- Do not delete prior per_phi archives; archive superseded logs under per_phi_postfix/archive/ instead.
- Avoid parallel nb-compare invocations; race conditions in output directory will clobber metrics.
- Update evoked README files (e.g., nb_compare_phi_fix/README.md) if thresholds or commands differ from historical notes.
Pointers:
- plans/active/cli-noise-pix0/plan.md:285
- docs/fix_plan.md:457
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:1
- reports/2025-10-cli-flags/phase_l/rot_vector/mosflm_matrix_correction.md:187
- specs/spec-a-cli.md:30
- reports/2025-10-cli-flags/phase_l/rot_vector/analysis.md:302
- reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/README.md:1
Next Up: Phase L3k.4 attempt logging and the Phase L4 supervisor-command rerun once VG gates are satisfied.

Summary: Run nb-compare on the supervisor ROI (Phase N2) to capture correlation metrics, PNG previews, and a written analysis so we can close the CLI-FLAGS parity loop.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase N2 nb-compare
Branch: feature/spec-based-2
Mapped tests:
- KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py
- KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py
- KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py --device cuda --maxfail=1  (run only if GPU available)
Artifacts:
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/summary.json
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/comparison.png
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/diff.png
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/analysis.md
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/nb_compare_stdout.txt
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/tests/pytest_cpu.log (append)
- docs/fix_plan.md (new Attempt for Phase N2 metrics)
- plans/active/cli-noise-pix0/plan.md (mark N2 once metrics captured)
Do Now: CLI-FLAGS-003 Phase N2 — run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py`; then execute `PYTHONPATH=src python scripts/nb_compare.py --roi 100 156 100 156 --resample --threshold 0.98 --outdir reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/ -- -mat A.mat -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0`.
If Blocked: If pytest or nb-compare fails, capture the stdout/stderr into `reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/nb_compare_error.log`, append the failure signature plus environment details to docs/fix_plan.md Attempt, leave plan row N2 as [ ], and stop for supervisor review after running `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py`.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:73–83 defines Phase N2 as the current gate and lists the exact nb-compare invocation to satisfy VG‑3/VG‑4.
- docs/fix_plan.md:452–471 marks Phase N2 as the next action after N1 completion and requires correlation/sum_ratio metrics to unblock closure.
- docs/bugs/verified_c_bugs.md:166–184 documents the φ=0 carryover as a C-only bug; cite it in the Attempt so the -14.6% I_before_scaling delta stays contextualised.
- docs/development/testing_strategy.md:58–109 mandates targeted pytest prior to bespoke tooling and device/dtype discipline for parity work.
- scripts/nb_compare.py uses temporary floatfiles per run; the generated artifacts must live under `reports/.../results/` per docs/index.md guidance on report layout.
How-To Map:
- export NB_C_BIN=./golden_suite_generator/nanoBragg
- KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py | tee reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/tests/pytest_cpu.log
- Optional CUDA smoke: KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py --device cuda --maxfail=1 | tee reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/tests/pytest_cuda.log
- PYTHONPATH=src python scripts/nb_compare.py --roi 100 156 100 156 --resample --threshold 0.98 --outdir reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/ -- -mat A.mat -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 -detector_rotx 0 -detector_roty 0 -detector_rotz 0 -twotheta 0 | tee reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/results/nb_compare_stdout.txt
- Verify `summary.json` meets thresholds (correlation ≥0.9995, sum_ratio 0.99–1.01); note peak alignment in `analysis.md` together with Option 1 reminder.
- Update reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/notes/todo_nb_compare.md (check N2 boxes) and create results/analysis.md summarising metrics, timings, and any resample notes.
- Append Attempt details to docs/fix_plan.md (metrics, command, artifacts) and flip plan row N2 to [D] once outputs look good.
Pitfalls To Avoid:
- Do not rerun the full pytest suite; stay with the targeted selector plus optional CUDA smoke.
- Do not move or overwrite the existing `inputs/` float files; nb-compare uses temporary paths.
- Avoid editing production code—this loop is evidence-only.
- Keep `reports/.../results/` free of ad-hoc filenames; use the script’s outputs and add `analysis.md` only.
- Ensure `NB_C_BIN` points to the instrumented binary to preserve trace parity (no system nanoBragg).
- Capture stdout/stderr even on success; missing logs make the Attempt incomplete.
- Respect Protected Assets: only touch input.md and report/doc files listed above.
- Confirm device availability before attempting the CUDA smoke test; skip gracefully if unavailable.
- Keep `nb_compare_stdout.txt` under 1 MB by piping through `tee` (no verbose reruns).
- Do not delete the TODO checklist; mark completed items with `[x]` instead.
Pointers:
- plans/active/cli-noise-pix0/plan.md:74–83 — Phase N tasks and thresholds.
- docs/fix_plan.md:452–471 — Current ledger notes for CLI-FLAGS-003.
- docs/bugs/verified_c_bugs.md:166–188 — C-only φ carryover description.
- docs/development/testing_strategy.md:65–105 — Targeted testing cadence rules.
- scripts/nb_compare.py:316–330 — CLI parameters (roi/resample/outdir handling).
- reports/2025-10-cli-flags/phase_l/nb_compare/20251009T020401Z/notes/todo_nb_compare.md — Existing N2 checklist to update.
Next Up:
1. Phase N3 — Write analysis.md summary, update docs/fix_plan Attempt, and archive the nb-compare metrics once correlation thresholds are confirmed.
2. Phase O1 prep — plan the final supervisor command rerun if Phase N metrics come back green.

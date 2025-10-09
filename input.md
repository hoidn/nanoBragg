Summary: Run a lambda sweep on the weighted-source fixture to verify the wavelength-column mismatch that is inflating PyTorch intensities.
Mode: Parity
Focus: SOURCE-WEIGHT-001 / Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2025-11-source-weights/phase_e/<STAMP>/lambda_sweep/{lambda62,lambda09768}/{commands.txt,py_stdout.log,simulator_diagnostics.txt,metrics.json,env.json}
Do Now: SOURCE-WEIGHT-001 — Correct weighted source normalization; run the lambda sweep experiment by executing the two CLI variants (original 6.2 Å sourcefile and duplicated sourcefile with 0.9768 Å wavelengths) and capture correlation/sum-ratio metrics against the existing C floatfile.
If Blocked: If either CLI run fails, record stdout/stderr under attempts/<STAMP>/failure.log and fall back to collecting simulator diagnostics only (no parity metrics).
Priorities & Rationale:
- docs/fix_plan.md — Next Actions now start with the lambda sweep to confirm the wavelength hypothesis before further parity runs.
- plans/active/source-weight-normalization.md — Phase E status and E2 guidance updated today to require twin PyTorch runs with 6.2 Å vs 0.9768 Å sourcefile columns.
- specs/spec-a-core.md:151 — Explicitly states the weight column is read but ignored; resolving the wavelength interpretation keeps behaviour aligned with spec.
- src/nanobrag_torch/simulator.py:552 & 849 — Source wavelengths are converted to Angstroms and fed into `_compute_physics_for_position`; evidence shows they track the file verbatim.
How-To Map:
- export KMP_DUPLICATE_LIB_OK=TRUE; export NB_RUN_PARALLEL=1; export NB_C_BIN=./golden_suite_generator/nanoBragg.
- Run `pytest --collect-only -q | tee collect.log` and stash the log under the final lambda_sweep folder.
- Define `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and create directories `reports/2025-11-source-weights/phase_e/$STAMP/lambda_sweep/{lambda62,lambda09768}`.
- Copy the baseline fixture `cp reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt /tmp/two_sources_lambda62.txt` and duplicate it with updated wavelength `sed 's/6.2e-10/9.768e-11/' /tmp/two_sources_lambda62.txt > /tmp/two_sources_lambda09768.txt`.
- Baseline PyTorch run: `KMP_DUPLICATE_LIB_OK=TRUE nanoBragg -mat A.mat -sourcefile /tmp/two_sources_lambda62.txt -distance 231.274660 -lambda 0.9768 -pixel 0.172 -detpixels_x 256 -detpixels_y 256 -oversample 1 -nonoise -nointerpolate -floatfile /tmp/py_lambda62.bin | tee reports/2025-11-source-weights/phase_e/$STAMP/lambda_sweep/lambda62/py_stdout.log`.
- Control PyTorch run: same command pointing to `/tmp/two_sources_lambda09768.txt` and `/tmp/py_lambda09768.bin`, logging to the lambda09768 directory.
- Optional (reuse existing data if present): run the canonical C command once to refresh `/tmp/c_tc_d1.bin` and capture stdout to `lambda62/c_stdout.log`.
- Capture simulator diagnostics for both fixtures using the short Python snippet from commands.txt (print `n_sources`, `steps`, `fluence`, `_source_wavelengths_A`) and save outputs to `simulator_diagnostics.txt` inside each directory.
- Compute metrics via `python scripts/analysis/compute_lambda_sweep.py` equivalent: a quick inline script that loads `/tmp/c_tc_d1.bin`, `/tmp/py_lambda62.bin`, `/tmp/py_lambda09768.bin`, prints correlation & sum ratios, and writes JSON to each folder.
- Record every command in `commands.txt` (chronological) and dump `python - <<'PY'` snippet that captures env metadata (git SHA, torch.collect_env) into `env.json` within lambda62.
Pitfalls To Avoid:
- Do not modify source code or tests during this evidence loop.
- Keep generated `.bin` files in /tmp; do not add them to git.
- Ensure both fixtures stay ASCII; avoid editing the original sourcefile in-place.
- Reuse the same NB_C_BIN for both runs to keep parity fair.
- Remember to set NB_RUN_PARALLEL=1 for PyTorch parity runs to match harness expectations.
- Do not delete or rename any file referenced in docs/index.md (protected assets rule).
- Verify directories exist before tee/cat to avoid silent failures.
- Capture command outputs immediately; reruns without logs will block plan closure.
- Skip full pytest; only the mapped collect-only run is allowed this loop.
Pointers:
- docs/fix_plan.md:4040 — SOURCE-WEIGHT-001 entry with new Attempt #13 and lambda sweep Next Action.
- plans/active/source-weight-normalization.md:11 — Phase E status snapshot spelling out the wavelength mismatch.
- specs/spec-a-core.md:151 — Authoritative statement that weights are ignored (context for this triage).
- src/nanobrag_torch/simulator.py:552 — Source wavelength conversion to Angstroms before physics.
- reports/2025-11-source-weights/phase_a/20251009T071821Z/c/c_stdout.log:117 — C reference showing 4 sources and lambda 0.9768 Å.
Next Up: Once lambda sweep confirms the hypothesis, regenerate TC-D1/TC-D3 parity metrics with the corrected fixture (Phase E3).

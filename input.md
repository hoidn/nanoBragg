Summary: Capture spec φ=0 baselines (rot_b_y, k_frac) and tighten VG-1 checks before parity shim work
Mode: Parity
Focus: CLI-FLAGS-003 / L3k.3c.3 lock spec φ=0 baselines
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c -v
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/trace_py_rot_vector.log; reports/2025-10-cli-flags/phase_l/per_phi/trace_py_rot_vector_per_phi.json; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/comparison_summary.md; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/delta_metrics.json; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/pytest_phi0.log
Do Now: CLI-FLAGS-003 L3k.3c.3 — env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity -v
If Blocked: Run env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/collect_only.log, log current k_frac/rot_b outputs from the harness in diagnosis.md, and pause for supervisor guidance

Priorities & Rationale:
- specs/spec-a-core.md:211-214 — φ sampling must rotate the reference cell freshly each step; spec values (rot_b_y, k_frac) are normative
- docs/bugs/verified_c_bugs.md:166-204 — C-PARITY-001 stays quarantined behind the future shim; default tests must no longer rely on the buggy plateau
- plans/active/cli-noise-pix0/plan.md:288-313 — L3k.3/L3k.3c.3 now require capturing spec baselines and proving ≤1e-6 deltas before nb-compare
- docs/fix_plan.md:450-464 — Next Actions call for recording rot_b_y=0.7173197865 Å, k_frac=1.6756687164 and updating pytest expectations accordingly
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251007154213/comparison_summary.md — Source of the current spec numbers; use it to confirm new captures match prior evidence
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:116-353 — Memo spells out VG-1 tolerances and trace workflow; keep it synchronized with new artifacts
- tests/test_cli_scaling_phi0.py:25-273 — Active assertions need to shift from “differs from C” to spec constants with tight tolerances
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:15-56 — VG checklist records pass/fail state; update rows with new timestamps once ≤1e-6 is demonstrated
- docs/development/testing_strategy.md:1.4 — Reinforces CPU+CUDA smoke expectations; apply when running targeted pytest after edits
- CLAUDE.md Core Implementation Rules (Rule 11 & 13) — Keep C-code references intact and ensure reciprocal/real recalculation stays metrically consistent while editing
- reports/2025-10-cli-flags/phase_l/per_phi/trace_py_rot_vector_per_phi.json — Current source for per-φ data; confirm it aligns with the newly captured copy under the timestamped directory
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_metrics.json — Previous baseline; use it as an A/B comparison when confirming ≤1e-6 deltas
- galph_memory.md (latest entries) — Ensure follow-on notes stay consistent with the decisions captured there when logging new attempts
- docs/architecture/pytorch_design.md §2.2-§2.4 — Reiterate vectorization requirements while touching the rotation utilities
- docs/development/pytorch_runtime_checklist.md — Checklist to cite when documenting CPU+CUDA coverage in the attempt log
- reports/2025-10-cli-flags/phase_l/nb_compare_phi_fix/summary.json — Will need consistency once VG-1 unlocks nb-compare work; keep future metrics aligned
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251207/comparison_summary.md — Most recent exploratory capture; compare patterns to ensure naming stays consistent
- tests/test_cli_scaling_phi0.py::TestPhiZeroParity (class overview) — Document test intent after updating expectations so future audits understand dual-mode plan

-How-To Map:
- Pick a new ISO-style timestamp (e.g., `20251201T1530Z`) and export `TS=reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$TS` so every command writes into the same folder
- Ensure editable import path is active: `export PYTHONPATH=src` and keep `KMP_DUPLICATE_LIB_OK=TRUE` in the environment before importing torch
- Generate CPU traces: `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --out ${TS}/trace_py_rot_vector.log --device cpu --dtype float32`
- Capture the harness stdout to `${TS}/trace_harness_cpu.log` (redirect with `| tee`) so deltas and metadata are preserved for the summary
- Snapshot the HKL/metadata payload by copying `reports/2025-10-cli-flags/phase_l/rot_vector/config_snapshot.json` into `${TS}/config_snapshot.json` to document the run configuration
- If CUDA is available, repeat with `--device cuda` and write to `${TS}/trace_py_rot_vector_cuda.log`; note the device in the filename to keep artifacts unambiguous
- Optionally run a float64 CPU trace (`--dtype float64`) to confirm the spec constants remain stable; archive as `${TS}/trace_py_rot_vector_float64.log`
- Run `python -m json.tool reports/2025-10-cli-flags/phase_l/per_phi/trace_py_rot_vector_per_phi.json > ${TS}/trace_py_rot_vector_per_phi.json` to capture a pretty-printed copy in the timestamped folder before comparisons
- Compare against the 20251123 C trace: `KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py ${TS}/trace_py_rot_vector_per_phi.json reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log | tee ${TS}/comparison_stdout.txt`
- Inspect the comparison output and record the max Δk/Δb_y in `${TS}/comparison_summary.md`; add a table with both CPU and CUDA results if both were run
- Generate a quick diff vs the 20251007 baseline: `diff -u reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251007154213/delta_metrics.json ${TS}/delta_metrics.json > ${TS}/delta_metrics.diff`
- Update `tests/test_cli_scaling_phi0.py` so `test_rot_b_matches_c` asserts `pytest.approx(0.7173197865, abs=1e-6)` and `test_k_frac_phi0_matches_c` asserts `pytest.approx(1.6756687164, abs=1e-6)`; remove the `> 0.1` divergence guard and add comments referencing the spec citation
- Drop `pytest.approx` into local variables (e.g., `expected_rot_b = pytest.approx(...)`) to keep assertions readable and to log the numeric constants in docstrings
- Refresh the docstrings in that test module to reference the new evidence path (timestamp folder + comparison summary) so future readers know where the numbers came from
- Run `git diff tests/test_cli_scaling_phi0.py` before executing pytest to confirm only the expected assertions/docstrings changed
- Run targeted pytest with `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c -v | tee ${TS}/pytest_phi0.log`; repeat on CUDA via `--maxfail=1 -k TestPhiZeroParity` guard if GPU-only code is touched
- If pytest fails, capture the stderr to `${TS}/pytest_phi0_fail.log`, revert any code edits, and document the failure in `diagnosis.md` before attempting fixes
- Run `env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee ${TS}/collect_only.log` after test edits to demonstrate selector stability per testing_strategy.md §1.5
- Append the targeted pytest command and outcome to `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/attempt_log.md` (create if missing) to keep historical breadcrumbs
- Rebuild `delta_metrics.json` (either by editing manually or reusing the script output) so it records `max_delta_k` and `max_delta_rot_b` ≤1e-6; cross-link the numeric evidence in `fix_checklist.md`
- Once tests and metrics pass, update `comparison_summary.md` with a “Spec baseline locked” section, cite the exact commands run, and tick VG-1.4 inside `reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md`
- Add a short summary to `docs/fix_plan.md` Attempt history (Attempt #116) referencing the new timestamp, metrics, and targeted tests so the ledger stays current
- Update `plans/active/cli-noise-pix0/plan.md` checklist row L3k.3c.3 with the new timestamp and mark `[D]` only after both CPU and CUDA (if available) traces agree within tolerance
- Update `galph_memory.md` with any surprises (e.g., new tolerances, missing CUDA) so the next supervisor loop has context
- Ping the parity shim tasks (L3k.3c.4/L3k.3c.5) by adding “ready to start” notes once VG-1 turns green

Pitfalls To Avoid:
- Do not rely on “differs from C” assertions; lock the actual spec values in tests
- Keep vectorization intact (no manual φ loops) and avoid device-conditional branches
- Ensure CPU and CUDA traces live under the same timestamped directory with device noted in filenames
- Maintain device/dtype neutrality; no `.cpu()`, `.numpy()`, or `.item()` on tensors that require grad
- Leave C carryover emulation for L3k.3c.4; default path must remain spec-true
- Run collect-only before edits if pytest selectors change; archive logs under the new timestamp
- Respect Protected Assets; never move/delete paths referenced in docs/index.md while reorganising artifacts
- Confirm `compare_per_phi_traces.py` input paths exist; script does not create directories for typos
- Keep HKL cache untouched; reruns must reuse `scaled.hkl` without regeneration
- Note the current C trace timestamp (20251123); update instructions if a newer trace is captured
- Don’t forget to propagate new constants into docstrings/comments so future readers know the provenance of 0.7173197865 Å / 1.6756687164
- Avoid overwriting previous timestamp directories; create a new folder even when re-running on the same day
- When running CUDA harness, guard with `torch.cuda.is_available()` to avoid noisy stack traces in reports
- Ensure pytest output includes the device/dtype markers (param IDs) so we can prove CPU+CUDA coverage in the attempt log
- Update `galph_memory.md` if unexpected artifacts appear or if plan assumptions change mid-loop
- Keep commit boundaries clean; do not bundle spec baseline work with shim design changes
- Avoid editing `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251007154213/` except for read-only comparisons; all new evidence goes under the fresh timestamp
- Keep a copy of the raw harness stdout; missing it makes later debugging harder
- Verify the `TS` variable each time before running commands to avoid polluting prior runs
- Do not forget to restore `PYTHONPATH`/env vars after the loop if they were temporarily changed in shell profile
- Avoid committing `collect_only.log` paths outside the timestamped folder; reruns should overwrite within the same directory

Pointers:
- specs/spec-a-core.md:211-214
- docs/bugs/verified_c_bugs.md:166-204
- plans/active/cli-noise-pix0/plan.md:288-312
- docs/fix_plan.md:450-468
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251007154213/comparison_summary.md
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:15-56
- tests/test_cli_scaling_phi0.py:25-273
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:116-353
- prompts/supervisor.md (for the canonical CLI command parameters referenced by the harness)
- reports/2025-10-cli-flags/phase_l/per_phi/README.md
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/attempt_log.md (create/update during this loop)
- arch.md §2a-§3
- docs/index.md (Protected Assets reminder)
- docs/development/pytorch_runtime_checklist.md
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/comparison_summary.md (to be produced this loop)
- docs/fix_plan.md Attempt #115 entry (current status reference)

Next Up:
1. L3k.3c.4 — design the opt-in C carryover shim and add parity-only tests once VG-1 is green
2. L3k.3d — revisit nb-compare ROI metrics with the updated per-φ baselines

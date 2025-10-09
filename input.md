Summary: Record the Phase M6 skip decision and prepare Phase N parity work with new ROI artifacts.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase M6 decision & Phase N1 ROI preparation
Branch: feature/spec-based-2
Mapped tests:
- tests/test_cli_scaling_phi0.py
- tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_rot_b_matches_c
- tests/test_cli_scaling_phi0.py::TestCLIScalingPhi0::test_k_frac_phi0_matches_c
- pytest --collect-only -q tests/test_cli_scaling_phi0.py (fallback log if run fails)
Artifacts:
- reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/inputs/
- reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/results/
- reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/tests/pytest_cpu.log
- reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/inputs/commands.txt
- reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/inputs/env.txt
- reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/inputs/git_sha.txt
- reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/inputs/version.txt
- reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/inputs/sha256.txt
- reports/2025-10-cli-flags/phase_l/nb_compare/<timestamp>/analysis.md
- docs/fix_plan.md (new Attempt entry referencing the timestamp)
- plans/active/cli-noise-pix0/plan.md (Phase M6 paragraph updated)
Do Now: CLI-FLAGS-003 / Phase N1 — run `pytest -v tests/test_cli_scaling_phi0.py` on CPU, regenerate the supervisor ROI float images for both C and PyTorch under nb_compare/<timestamp>/inputs/, and log the Phase M6 (skip) decision plus artifact paths in docs/fix_plan.md Attempts before concluding the loop.
If Blocked: If nb-compare prerequisites (C binary, PyTorch CLI, ROI args) fail, capture the failing command output with timestamps, rerun `pytest --collect-only -q tests/test_cli_scaling_phi0.py`, document the blocker and partial artifacts in docs/fix_plan.md Attempts, and pause for supervisor review.
Context Recap:
- Option 1 accepted: PyTorch intentionally diverges from buggy C at I_before_scaling; carryover shim permanently removed.
- Phase M5d–M5g completed 2025-12-20; docs/fix_plan.md and plan rows already updated this loop.
- Phase M4d closure artifacts now live under option1_spec_compliance/20251009T013046Z/ with refreshed compare_scaling outputs.
- Normalization fix landed in Attempt #189; only φ rotation divergence remains and is documented.
- Tests/test_cli_scaling_phi0.py provides the spec-mode regression coverage verifying Option 1 behaviour.
- Plan Phase N remains untouched; we are seeding prerequisites this loop.
- Phase M6 was optional; decision today is to skip further shim work and proceed with spec-only parity.
- Long-term Goal 1 (shim removal) is complete; this work advances Long-term Goal 2 documentation alignment and parity closure.
- reports/2025-10-cli-flags/phase_l/scaling_validation/ inventories hold previous trace bundles for reference; keep naming consistent.
- Protected Assets reminder: docs/index.md lists loop.sh, supervisor.sh, input.md — ensure they remain intact while editing.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:73–120 requires Phase M6 disposition before Phase N; recording the skip is the final gate.
- plans/active/cli-noise-pix0/plan.md:97 makes ROI regeneration the first deliverable for Phase N1; without inputs nb-compare cannot run.
- docs/fix_plan.md:452–540 must reflect the decision so the ledger matches the plan rows updated this loop.
- reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/20251009T013046Z/metrics.json sets expectations for the persistent -14.6% I_before_scaling delta.
- reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/20251009T013046Z/summary.md captures the Option 1 rationale; cite this when explaining the skip.
- scripts/validation/compare_scaling_traces.py lines 1-40 document Option 1 context and reference compare_scaling expectations.
- docs/bugs/verified_c_bugs.md:166-204 formally records C-PARITY-001; include this citation in Attempt and analysis write-ups.
- specs/spec-a-cli.md detector and pix0 sections ensure CLI argument ordering remains spec compliant for both implementations.
- docs/development/testing_strategy.md §§1.4–1.5 enforce targeted pytest cadence and logging discipline prior to bespoke tooling.
- arch.md §§2–2a outline runtime layout and detector vector handling that informs command verification.
- prompts/supervisor.md authoritative command block prevents flag drift when copying CLI arguments.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T223805Z/summary.md records the normalization fix and serves as historical context while writing the skip rationale.
How-To Map:
- Export environment: `export NB_C_BIN=./golden_suite_generator/nanoBragg` and `export KMP_DUPLICATE_LIB_OK=TRUE`; note both in env.txt.
- Snapshot git/Python versions: `git rev-parse HEAD > git_sha.txt`; `python -m nanobrag_torch --version > version.txt`.
- Determine timestamp: `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`.
- Create bundle directories: `mkdir -p reports/2025-10-cli-flags/phase_l/nb_compare/$STAMP/{inputs,results,tests}`.
- Baseline test: `pytest -v tests/test_cli_scaling_phi0.py | tee reports/.../tests/pytest_cpu.log`; record pass/fail in analysis.md.
- If pytest fails, still write collect-only log and mention failure state in Attempt.
- Supervisor command (C): run `${NB_C_BIN}` with the documented CLI flags, redirect stdout/stderr to `inputs/c_command.log`, write float output to `inputs/c_float.bin`.
- Supervisor command (PyTorch): `KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch <args>` mirrored from the plan, log to `inputs/py_command.log`, ensure float output at `inputs/py_float.bin`.
- Capture timing and exit codes: append to commands.txt after each run with start/end timestamps and `$?` values.
- Store environment details: list OS/Python/PyTorch versions and CUDA availability in env.txt; mention CPU-only if GPU absent.
- Hash outputs: `(cd inputs && sha256sum * > sha256.txt)` and verify with `sha256sum -c sha256.txt`.
- Draft analysis.md summarising tests run, Option 1 citation, ROI command steps, differences observed (if any), and placeholder for future nb-compare metrics.
- Update docs/fix_plan.md Attempt entry with test results, command references, new artifact path, and explicit note “Phase M6 deferred (Option 1 accepted).”
- Update plans/active/cli-noise-pix0/plan.md Phase M6 narrative indicating skip plus timestamp (e.g., `[N/A — skipped {STAMP}]`).
- Stage results directory but leave nb-compare execution for Phase N2; include command outline in analysis.md so future loop can resume quickly.
- Provide TODO in analysis.md for GPU rerun if/when hardware becomes available.
Evidence Expectations:
- Commands.txt should include UTC timestamps for traceability.
- env.txt (or env.json) should list OS, Python, PyTorch, CUDA status, and relevant environment variables.
- analysis.md must quote Option 1 bundle path, docs/bugs entry, and plan rows touched this loop.
- Attempt entry in docs/fix_plan.md should include new timestamp path, targeted pytest outcome, and explicit mention of ROI bundle contents.
- Plan update should mark Phase M6 as skipped and reaffirm that Phase N1 inputs now exist.
- Tests/pytest_cpu.log should be committed under the timestamp directory for reproducibility.
- C and PyTorch command logs should capture warnings verbatim; note any differences in analysis.md.
- sha256.txt verification result should be documented (pass/fail) in analysis.md.
- analysis.md should include bullet list of files produced (c_float.bin, py_float.bin, commands.txt, etc.).
- Document absence of CUDA run (if applicable) so reviewers do not assume it was attempted silently.
Pitfalls To Avoid:
- Do not resurrect the removed `--phi-carryover-mode`; spec compliance mandates fresh rotations.
- Avoid `.cpu()`/`.item()` conversions in scripts; keep tensors device/dtype neutral even if CLI defaults to CPU.
- Preserve Protected Assets (loop.sh, supervisor.sh, input.md, docs/index.md references).
- Do not overwrite the Option 1 bundles; always use a new timestamp under nb_compare/.
- Ensure ROI indices remain `100 156 100 156`; typos derail parity comparisons.
- Record env metadata before running commands; missing env files forces reruns.
- Capture stderr/stdout for both C and PyTorch to aid future debugging.
- If GPU unavailable, explicitly note it; silent omissions are treated as regressions.
- Reference docs/bugs/verified_c_bugs.md whenever explaining the remaining divergence.
- Keep commands.txt, analysis.md, and Attempt entries consistent; mismatches create audit churn.
- Do not run nb-compare until inputs exist; mention planned command instead.
- Avoid scattershot directories; every artifact for this loop lives under the timestamp bundle.
Pointers:
- plans/active/cli-noise-pix0/plan.md:60-120 for Phase M6 and Phase N details.
- docs/fix_plan.md:452-540 for Attempt templates and Next Actions context.
- reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/20251009T013046Z/ for Option 1 evidence.
- scripts/validation/README.md for nb-compare usage and artifact expectations.
- scripts/validation/compare_scaling_traces.py docstring for shared narrative.
- docs/development/testing_strategy.md §§1.4-1.5 for test cadence and logging requirements.
- specs/spec-a-cli.md §§Detector vectors & CLI semantics for command validation.
- arch.md §§2-3 describing runtime layout and detector vector handling.
- docs/bugs/verified_c_bugs.md:166-204 outlining the C bug we now treat as historical.
- plans/archive/cli-phi-parity-shim/plan.md for background on the retired shim.
- galph_memory.md latest entry to keep supervisor ↔ engineer context aligned.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_20251008T231211Z/trace_py_scaling.log if trace naming guidance is needed.
- prompts/supervisor.md authoritative command block for cross-checking flag order.
Next Up:
1. CLI-FLAGS-003 / Phase N2 — execute nb-compare with the new ROI float files, archive metrics/PNGs, and verify correlation thresholds.
2. CLI-FLAGS-003 / Phase O1 — rerun the full supervisor command once nb-compare is green, logging parity metrics for final closure.

Summary: Lock the spec φ=0 baselines (rot_b_y, k_frac) with fresh traces, document ≤1e-6 deltas, and keep parity shim work gated
Mode: Parity
Focus: CLI-FLAGS-003 / L3k.3c.3 lock spec φ=0 baselines
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c -v
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/trace_py_rot_vector.log, reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/trace_harness_cpu.log, reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/trace_py_rot_vector_per_phi.json, reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/comparison_summary.md, reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/delta_metrics.json, reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/pytest_phi0.log, reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/collect_only.log, reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/config_snapshot.json, reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/<ts>/sha256.txt
Do Now: CLI-FLAGS-003 L3k.3c.3 — env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity -v
If Blocked: env KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py | tee ${TS}/collect_only.log, dump current φ=0 deltas into reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md, stash harness stdout, and pause for supervisor review before modifying implementation

Priorities & Rationale:
- specs/spec-a-core.md:211-214 mandate φ=0 identity rotation, so rot_b_y and k_frac must be recorded against the 0.7173197865 Å and 1.6756687164 targets
- docs/bugs/verified_c_bugs.md:166-204 isolates the nanoBragg C carryover defect; keeping PyTorch default spec-compliant is non-negotiable until the shim exists
- plans/active/cli-noise-pix0/plan.md:288-320 leaves L3k.3c.3 open until CPU (and CUDA) traces show ≤1e-6 deltas plus refreshed pytest evidence
- docs/fix_plan.md:450-520 calls for updated comparison_summary.md, delta_metrics.json, and checklist rows before advancing to parity shim tasks
- tests/test_cli_scaling_phi0.py:25-273 already assert the spec baselines; passing them confirms the simulator still honors the spec after recent merges
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:116-353 enumerates VG gates and artifact expectations you must satisfy this loop
- docs/development/testing_strategy.md:1.4 enforces CPU+CUDA smoke coverage for tensor math edits; cite it when logging the Attempt metadata
- CLAUDE.md Rule 13 (metric duality) and Rule 11 (C reference docstrings) remain in force; do not regress the cross-product recalculation while gathering evidence
- galph_memory.md latest entry reiterates that the shim work is deferrable; respect the standing decision to finish L3k.3c.3 before new implementation
- reports/2025-10-cli-flags/phase_l/fix_checklist.md VG-1 rows (lines 18-46) still marked pending; your artifacts should let you tick them
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251007154213/comparison_summary.md contains the historic deltas; supersede it with the new timestamped capture
- CLAUDE.md Protected Assets Rule forces us to keep docs/index.md consistent; storing outputs under reports/ preserves compliance during evidence capture
- Project long-term goal #1 (parallel supervisor command) depends on this gate; clearing it unlocks downstream normalization and parity reruns
- Long-term goal #2 (ensuring spec rejects the C bug) requires this loop to confirm that the default behavior remains spec-aligned post-fixes

How-To Map:
- export TS="reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/$(date -u +%Y%m%dT%H%M%SZ)" && mkdir -p "$TS" && printf "timestamp=%s\n" "$TS" >> ${TS}/metadata.txt
- cp reports/2025-10-cli-flags/phase_l/rot_vector/config_snapshot.json ${TS}/config_snapshot.json to capture the supervisor command parameters used for this run
- echo NB_C_BIN=${NB_C_BIN:-./golden_suite_generator/nanoBragg} >> ${TS}/metadata.txt to document the C binary provenance
- Ensure editable import path and MKL guard: export PYTHONPATH=src; export KMP_DUPLICATE_LIB_OK=TRUE; verify `which nanoBragg` points to the editable install before running harnesses
- KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --out ${TS}/trace_py_rot_vector.log --device cpu --dtype float32 | tee ${TS}/trace_harness_cpu.log
- Verify trace_harness exit code and file sizes; if trace_py_rot_vector_per_phi.json is missing, rerun with --emit-per-phi to regenerate the JSON payload expected by compare_per_phi_traces.py
- shasum -a 256 ${TS}/trace_py_rot_vector.log ${TS}/trace_harness_cpu.log > ${TS}/sha256.txt for reproducibility
- KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py ${TS}/trace_py_rot_vector_per_phi.json reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/202510070839/c_trace_phi_202510070839.log > ${TS}/comparison_stdout.txt
- jq '.per_phi_entries' ${TS}/trace_py_rot_vector_per_phi.json > ${TS}/per_phi_entries.json to document the raw values before summarising deltas
- python scripts/summarise_phi_deltas.py ${TS}/trace_py_rot_vector_per_phi.json --out ${TS}/delta_metrics.json --threshold 1e-6 >> ${TS}/comparison_stdout.txt
- env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c -v | tee ${TS}/pytest_rot_b.log
- env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c -v | tee ${TS}/pytest_k_frac.log
- cat ${TS}/pytest_rot_b.log ${TS}/pytest_k_frac.log > ${TS}/pytest_phi0.log to simplify fix_plan references; record CPU runtime in metadata.txt
- If CUDA is available, rerun the harness with --device cuda --dtype float32, store outputs as ${TS}/trace_py_rot_vector_cuda.log and delta_metrics_cuda.json, and capture pytest logs with `env KMP_DUPLICATE_LIB_OK=TRUE pytest -k TestPhiZeroParity --device cuda -v | tee ${TS}/pytest_phi0_cuda.log`
- Append device availability, torch version, and git SHA via `python -c "import torch, subprocess; print(f'device={torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu"}')" >> ${TS}/metadata.txt`
- Update reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md with a new section summarising metrics, referencing ${TS}/delta_metrics*.json, pytest logs, and comparison_stdout.txt
- Mark VG-1 entries in reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md as complete with timestamp, device, and delta figures; include both CPU and CUDA rows when applicable
- Append Attempt details to docs/fix_plan.md under CLI-FLAGS-003 with metrics (rot_b delta, k_frac delta, pytest runtimes), artifact paths (TS folder), references to spec lines, and confirmation that Next Actions move to L3k.3c.4
- Run `git status --short reports/2025-10-cli-flags/phase_l/rot_vector` to confirm no stray temp files remain before committing artifacts

Pitfalls To Avoid:
- Do not reintroduce `_phi_last_cache` or any cached φ state in production code while collecting evidence
- Avoid hard-coding CPU tensors when running CUDA validation; use `.to(device)` based on harness arguments
- Never touch docs/index.md assets when creating timestamp folders; keep all outputs under reports/...
- Skip nb-compare or normalization reruns; focus strictly on per-φ baselines this loop
- Do not loosen pytest tolerances; maintain abs=1e-6 assertions in tests/test_cli_scaling_phi0.py
- Keep harness RNG seeds stable; do not modify mosaic seed inputs while capturing traces
- Confirm NB_C_BIN still points to golden_suite_generator/nanoBragg before invoking compare_per_phi_traces.py so the C trace reference remains valid
- Capture SHA256 hashes with `shasum -a 256 ${TS}/trace_py_rot_vector.log` to make future audits replicable
- Log CUDA availability in metadata.txt to clarify skipped GPU runs if hardware is absent
- Ensure KMP_DUPLICATE_LIB_OK=TRUE is exported before importing torch inside ad-hoc shells or scripts
- Do not delete historical timestamp folders; new evidence should be additive for auditability
- Avoid editing plan status markers prematurely; update plans/active and fix_plan only after the evidence is stored
- Keep vectorized rotate_axis calls intact; no Python loops around phi or mosaic dimensions
- Resist the temptation to regenerate the C trace; rely on the checked-in 202510070839 log unless the supervisor instructs otherwise
- Document skipped steps explicitly in metadata if CUDA or other resources are unavailable, to prevent re-opened attempts later

Pointers:
- specs/spec-a-core.md:211
- docs/bugs/verified_c_bugs.md:166
- plans/active/cli-noise-pix0/plan.md:309
- docs/fix_plan.md:461
- tests/test_cli_scaling_phi0.py:257
- reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md:116
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:18
- scripts/compare_per_phi_traces.py:1
- scripts/summarise_phi_deltas.py:1
- galph_memory.md:1753
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251007154213/comparison_summary.md:12
- docs/development/testing_strategy.md:37
- CLAUDE.md:210
- docs/development/pytorch_runtime_checklist.md:10
- docs/architecture/pytorch_design.md:120
- reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/delta_metrics.json:1

Next Up:
- Phase L3k.3c.4 — design and document the opt-in C parity shim once VG-1 evidence is archived
- Phase L3k.3d — rerun nb-compare ROI parity with the refreshed φ baselines to unblock Phase L4 supervisor command rerun
Attempts Log Expectations:
- Record Attempt number, plan row (L3k.3c.3), and precise timestamp from ${TS}
- Include CPU and CUDA (if run) device names, torch version, and git SHA in the Attempt entry
- Cite comparison_stdout.txt, delta_metrics.json, pytest_phi0.log, and fix_checklist rows explicitly in the attempt narrative
- Note whether scripts/summarise_phi_deltas.py threshold checks passed (≤1e-6) and attach the CLI output snippet
- Mention any skipped CUDA steps with rationale (hardware unavailable, driver mismatch, etc.)
- Reference docs/development/testing_strategy.md:1.4 in the Attempt to satisfy device coverage policy
- Confirm that no code changes were made during evidence capture (documentation-only loop)
- State that parity shim tasks remain TODO (L3k.3c.4 onward) to prevent premature closure
- Cross-link galph_memory.md entry from this supervisor loop for future context
- Update docs/fix_plan.md Next Actions so L3k.3c.3 is marked done and L3k.3c.4 becomes the active focus after evidence is stored
Notes:
- Keep ${TS} consistent across all commands to avoid mixing artifacts from separate runs
- Double-check that reports/2025-10-cli-flags/phase_l/rot_vector/per_phi_postfix/ remains untouched; new data should live only in the timestamped directory
- Retain prior artifacts for comparison; do not delete or overwrite older delta_metrics.json files from historical runs
- If you discover discrepancies beyond tolerance, stop after capturing evidence and escalate rather than proceeding to shim work
- Share any unexpected tool output (stderr warnings, runtime anomalies) in the attempt narrative for traceability
- Sync with git after archiving artifacts to keep the repository clean for the next supervisor invocation

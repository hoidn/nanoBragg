Summary: Capture float32 vs float64 φ-trace evidence so we can decide whether to relax the Δk tolerance or chase a precision fix.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm — Phase L3k.3c.4 dtype sensitivity probe
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_phi0.py tests/test_phi_carryover_mode.py
Artifacts: reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/, reports/2025-10-cli-flags/phase_l/per_phi/trace_py_c_parity_float32_per_phi.json, reports/2025-10-cli-flags/phase_l/per_phi/trace_py_c_parity_float64_per_phi.json, reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/c_trace_phi.log
Do Now: CLI-FLAGS-003 (Phase L3k.3c.4) — KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --phi-mode c-parity --dtype float32 --out reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/trace_py_c_parity_float32.log
If Blocked: If the harness errors because `scaled.hkl` or `A.mat` is missing, recreate them via the supervisor setup (see reports/2025-10-cli-flags/phase_i/supervisor_command/README.md) and rerun; record the failure + command in Attempts History before retrying.
Priorities & Rationale:
- plans/active/cli-phi-parity-shim/plan.md — C4b/C4d now demand explicit dtype sweep before tolerances move.
- docs/fix_plan.md:450 — Updated Next Actions call for float32/float64 evidence prior to VG-1 decision.
- specs/spec-a-core.md:211 — Spec insists on fresh φ rotations; parity shim must stay opt-in and validated.
- docs/bugs/verified_c_bugs.md:166 — C-PARITY-001 context ensures we keep the bug quarantined while measuring.
How-To Map:
- mkdir -p reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe && export BASE=reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe
- KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --phi-mode c-parity --dtype float32 --out ${BASE}/trace_py_c_parity_float32.log
- KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --phi-mode c-parity --dtype float64 --out ${BASE}/trace_py_c_parity_float64.log
- (Optional sanity) repeat the harness for `--phi-mode spec` with float32 to ensure baseline stays aligned; keep outputs in ${BASE} with clear filenames.
- After each run copy metadata: cp reports/2025-10-cli-flags/phase_l/rot_vector/trace_py_env.json ${BASE}/env_$(date +%H%M%S)_<dtype>_<mode>.json and cp reports/2025-10-cli-flags/phase_l/rot_vector/config_snapshot.json ${BASE}/config_<dtype>_<mode>.json before the next invocation overwrites them.
- For each new JSON under reports/2025-10-cli-flags/phase_l/per_phi/, run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/compare_per_phi_traces.py <json> reports/2025-10-cli-flags/phase_l/parity_shim/20251008T021659Z/c_trace_phi.log > ${BASE}/compare_$(basename <json> .json).txt` and gather the generated comparison_summary.md/delta files into ${BASE}.
- Append a short subsection to reports/2025-10-cli-flags/phase_l/rot_vector/diagnosis.md (C4b) summarising float32 vs float64 Δk / ΔF_latt_b, and drop a commands.txt + sha256.txt in ${BASE} capturing every invocation and key artifacts.
Pitfalls To Avoid:
- Do not edit production code to change dtype defaults; use harness CLI / temporary wrappers only.
- Keep KMP_DUPLICATE_LIB_OK=TRUE on every run to avoid MKL crashes.
- Do not overwrite prior parity evidence—stage new outputs under the ${BASE} timestamp before copying metadata.
- Avoid moving or renaming assets listed in docs/index.md (Protected Assets rule).
- No full pytest runs; stick to the collect-only command above.
- Record precise commands in ${BASE}/commands.txt as you go to keep repeatability.
- Copy env/config snapshots before launching the next run, or the harness will clobber them.
- Maintain device neutrality: if you switch to CUDA, note it and capture a separate env file.
- Do not stage/commit temporary dtype patches; revert to clean state before finishing.
Pointers:
- plans/active/cli-phi-parity-shim/plan.md (Phase C4b/C4c guidance)
- docs/fix_plan.md:450 (current Next Actions for CLI-FLAGS-003)
- docs/bugs/verified_c_bugs.md:166 (φ=0 carryover bug description)
- specs/spec-a-core.md:211 (normative φ rotation contract)
Next Up: After dtype evidence lands, update diagnosis.md + docs/fix_plan.md with the tolerance decision (Phase L3k.3c.4/C4c).

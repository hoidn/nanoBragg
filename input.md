Summary: Land the pixel-indexed φ=0 carryover cache (Option 1) and prove parity so VG-2 can turn green.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c; tests/test_cli_scaling_parity.py::TestScalingParity::test_phi_carryover_gradcheck
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/carryover_cache_validation/; reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/carryover_probe/
Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q
If Blocked: Capture the failing command + traceback in carryover_cache_validation/<ts>/commands.txt, run pytest --collect-only -q on the same selector for discovery proof, log the blocker (with artifact path) in docs/fix_plan.md Attempts, and halt.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:94 calls for M2g–M2i to unblock VG-2; executions must follow the new sub-checklists (M2g.1–M2i.3).
- docs/fix_plan.md:461 lists the refreshed Next Actions; Option 1 cache is now the top item ahead of downstream nb-compare work.
- specs/spec-a-core.md:210 keeps the spec path (fresh rotations each φ step) authoritative—ensure spec mode remains untouched while adding c-parity plumbing.
- docs/bugs/verified_c_bugs.md:166 documents C-PARITY-001 as a quarantined C-only bug; parity shim must emulate it without polluting spec behavior.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T100653Z/analysis.md anchors the Option 1 design; update it once the cache is implemented.

How-To Map:
- Allocate and wire the cache per M2g.1–M2g.4: edit src/nanobrag_torch/models/crystal.py to add pixel-indexed buffers, hook them through `_compute_physics_for_position`, and mirror the helper in reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py.
- After coding, regenerate failing evidence then rerun the targeted test: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c -q > $RUN_DIR/pytest_cpu.log 2>&1`.
- Add a gradcheck harness (e.g., new test `TestScalingParity::test_phi_carryover_gradcheck`) and run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_phi_carryover_gradcheck -q`.
- Probe CUDA if available: `python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --config supervisor --phi-mode c-parity --device cuda --dtype float64 --out trace_py_scaling_cuda.log`.
- Re-run the ROI trace comparison once the cache lands: `python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --roi 684 686 1039 1040 --phi-mode c-parity --dtype float64 --device cpu --out trace_py_scaling.log`.
- Archive logs plus env metadata under carryover_cache_validation/<ts>/ (pytest_cpu.log, gradcheck.log, trace_py_scaling_cuda.log, commands.txt, env.json, sha256.txt) and carryover_probe/<ts>/ (trace_py_scaling.log, metrics.json, trace_diff.md).
- Update reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md with an “Implementation” subsection (M2g.5) and sync lattice_hypotheses.md + scaling_validation_summary.md.
- Record the Attempt in docs/fix_plan.md with ΔF_latt/ΔI_before_scaling and mark M2g–M2i rows [D] in plans/active/cli-noise-pix0/plan.md.

Pitfalls To Avoid:
- Do not leave `.detach()`, `.clone()`, or in-place writes inside the cache plumbing—this must stay autograd-safe.
- Keep spec mode untouched; gate the new path strictly behind `phi_carryover_mode == "c-parity"`.
- Respect device/dtype neutrality when allocating caches (no implicit `.cpu()`/`.double()` conversions).
- Avoid shrinking existing reports; add new timestamped directories instead of overwriting.
- Make sure trace_harness.py and the simulator share identical helper logic so evidence stays aligned.
- Remember Protected Assets (docs/index.md); don’t rename or delete any listed file.
- Ensure every torch import obeys KMP_DUPLICATE_LIB_OK=TRUE.
- Don’t skip gradcheck—Option 1 must keep gradients intact for downstream optimization work.
- Capture exit codes in commands.txt for every command (tests, traces, gradcheck).
- Keep all markdown edits ASCII and update sha256.txt entries for new artifacts.

Pointers:
- plans/active/cli-noise-pix0/plan.md:94 — M2 implementation checklist and new M2g/M2h/M2i subtables.
- docs/fix_plan.md:461 — Current Next Actions driving this work.
- specs/spec-a-core.md:210 — Normative φ rotation pipeline that spec mode must preserve.
- docs/bugs/verified_c_bugs.md:166 — C-PARITY-001 bug classification and parity-shim constraints.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md — Option 1 design record to extend post-implementation.

Next Up: Once VG-2 turns green, move to Phase M4 documentation refresh and prep the nb-compare rerun (Phase N).

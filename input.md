Summary: Regenerate φ-trace artifacts to isolate the residual rotation drift before rerunning VG gates.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q (collection only, defer execution)
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/
Do Now: CLI-FLAGS-003 · Phase L3k.3b — regenerate per-φ traces; run PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --out trace_py_rot_vector_20251122.log --device cpu --dtype float64
If Blocked: Capture the failure mode in base_vector_debug/20251122/blockers.md with command + stderr, then run pytest --collect-only -q and stash the log beside it.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:279 — L3k.3 checklist now demands a fresh diagnosis before VG reruns.
- docs/fix_plan.md:458 — Next Actions call for L3k.3b evidence (per-φ harness diff) ahead of nb-compare fixes.
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:20 — VG-1.4 remains ⚠️, so we must quantify the drift.
- specs/spec-a-cli.md §Sampling — confirms φ grid (osc=0.1, phisteps=10) to match in harness.
- docs/development/testing_strategy.md §2 — keep parity evidence organized under reports/ with reproducible commands.

How-To Map:
- mkdir -p reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122
- PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --config supervisor --pixel 685 1039 --out trace_py_rot_vector_20251122.log --device cpu --dtype float64
- mv trace_py_rot_vector_20251122.log reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/
- mv reports/2025-10-cli-flags/phase_l/per_phi/trace_py_rot_vector_20251122_per_phi.* reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/
- python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/trace_py_rot_vector_20251122_per_phi.json reports/2025-10-cli-flags/phase_l/rot_vector/c_trace_mosflm.log > reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/comparison_stdout.txt
- pytest --collect-only -q | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/pytest_collect.log
- Summarize deltas + hypotheses in reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251122/diagnosis.md and update fix_checklist.md VG-1.4 notes.

Pitfalls To Avoid:
- Do not modify production code; this loop is evidence-only.
- Keep PYTHONPATH=src and KMP_DUPLICATE_LIB_OK=TRUE set before importing torch.
- Avoid overwriting prior per_phi artifacts; create the 20251122 subdir first.
- Use CPU + float64 as scripted; CUDA may diverge from archived C traces.
- Don’t forget to move the auto-emitted per_phi files out of reports/.../per_phi/ to keep tree tidy.
- Leave tests red; no attempts to "fix" failing assertions yet.
- Preserve Protected Assets (docs/index.md references) if editing docs.
- Record command invocations in diagnosis.md for reproducibility.
- Limit nb-compare/new runs until this diagnosis is done; ROI work is later.
- No git commits until artifacts + notes are captured.

Pointers:
- plans/active/cli-noise-pix0/plan.md:276
- docs/fix_plan.md:454
- reports/2025-10-cli-flags/phase_l/rot_vector/fix_checklist.md:18
- docs/architecture/detector.md:48
- specs/spec-a-cli.md:73

Next Up:
1. Phase L3k.3d — repair nb-compare ROI metrics once φ drift is characterized.
2. Phase L3k.3e — document resolutions and prep L3k.4 attempt log after VG gates flip green.

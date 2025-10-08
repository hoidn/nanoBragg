Summary: Deliver the CLI-FLAGS-003 Phase M4 normalization correction so PyTorch matches the nanoBragg.c scaling chain again.
Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests:
- tests/test_cli_scaling_phi0.py::TestScalingParity::test_rot_b_matches_c
- tests/test_cli_scaling_phi0.py::TestScalingParity::test_k_frac_phi0_matches_c
- tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
- tests/test_suite.py::TestTier1TranslationCorrectness::test_cli_scaling_trace_cpu
- tests/test_suite.py::TestTier1TranslationCorrectness::test_cli_scaling_trace_cuda
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/summary.md — recap of normalization change, parity metrics, follow-on steps.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/trace_py_fix.log — TRACE_PY lines matching TRACE_C ordering.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/trace_py_phi.log — per-φ instrumentation from M3a schema.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/trace_c_baseline.log — either fresh capture or pointer to reused baseline.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/compare_scaling_traces.json — factor-by-factor deltas with first_divergence None.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/compare_scaling_traces.txt — human-readable diff summary.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/pytest.log — full CPU run including targeted selectors.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/pytest_collect.log — proof of discovery for mapped tests.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/commands.txt — chronological reproduction commands.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/env.json — python/torch/device/dtype snapshot.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/sha256.txt — checksum table for bundle validation.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/git_sha.txt — commit hash after landing fix.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/lattice_hypotheses.md — Hypothesis H4 closure note with before/after intensities.
- docs/fix_plan.md Attempt #??? update — describe Phase M4 completion, metrics, artifact paths, next steps.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/run_metadata.json — CLI harness metadata (device, dtype, oversample, steps).
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/diff_trace.md — first-divergence narrative confirming parity.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/metrics.json — machine-readable factor table for regression tracking.
Do Now: CLI-FLAGS-003 Phase M4b normalization fix — KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py
If Blocked: Capture a partial bundle under reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/summary.md describing the blocker, run pytest --collect-only -q tests/test_cli_scaling_phi0.py, attach both paths to docs/fix_plan.md Attempt history, then pause.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:60-71 keeps M4b–M4d ahead of CUDA and nb-compare, so finishing them is mandatory before any other CLI work.
- docs/fix_plan.md:451-480 records M4a closure and explicitly calls for eliminating the double `/ steps` regression.
- specs/spec-a-core.md:247-254 mandates a single `S = r_e^2 · fluence · I / steps` scaling stage with last-value semantics for capture_fraction/polar/omega.
- golden_suite_generator/nanoBragg.c:3336-3364 is the authoritative reference sequence for the normalization we need to mirror exactly.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/analysis_20251008T212459Z.md quantifies the current −14.6% I_before_scaling deficit that this fix must eliminate.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T223046Z/design_memo.md documents the double-division root cause and provides citations for implementation.
- docs/development/c_to_pytorch_config_map.md:34-56 reiterates the scaling parity expectations between C and PyTorch simulators.
How-To Map:
- Re-read the spec + C snippet: sed -n '240,270p' specs/spec-a-core.md && nl -ba golden_suite_generator/nanoBragg.c | sed -n '3332,3368p'.
- Inspect the current PyTorch normalization pipeline: nl -ba src/nanobrag_torch/simulator.py | sed -n '940,1140p'.
- Adjust the physics path so normalization divides by `steps` exactly once alongside `self.r_e_sqr * self.fluence`, updating TRACE_PY emission to log the pre-division accumulator.
- Use /tmp/m3a_instrumentation_design.md for TRACE_PY_PHI format while refreshing per-φ logging after the fix.
- Run KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py on CPU float64; if CUDA available, repeat with --device cuda.
- Regenerate PyTorch trace: KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/.
- Reuse or refresh the C trace with NB_C_BIN=./golden_suite_generator/nanoBragg bash -lc "python reports/2025-10-cli-flags/phase_l/scaling_audit/run_c_trace.py --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/trace_c_baseline.log".
- Compare scaling factors: python scripts/validation/compare_scaling_traces.py --bundle reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/ --c-bundle reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/.
- Summarise results in summary.md, update lattice_hypotheses.md (close Hypothesis H4), and log docs/fix_plan.md Attempt #??? with metrics + artifact list.
- Prepare CUDA smoke + gradcheck re-run plan (Phase M5) once CPU parity confirmed; note prerequisites in summary.md.
- Capture new sha256.txt after all artifacts are in place: find reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp> -type f | sort | xargs shasum -a 256 > sha256.txt.
- Store git status snapshot: git status -sb > reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/git_status.txt prior to commit.
- Document test runtime + device in summary.md so future regressions can spot performance anomalies.
- Queue CUDA rerun command template (Phase M5) inside summary.md for future reference.
- Record trace harness command with explicit RNG seed (if applicable) inside commands.txt for reproducibility.
- Run python scripts/validation/compare_scaling_traces.py --bundle ... --emit-table to produce additional CSV if needed for Phase M6 ledger.
- Validate that lattice_hypotheses.md includes cross-reference to fix_<timestamp> bundle with new delta values.
Pitfalls To Avoid:
- Do not reintroduce `.item()` on tensors that must remain differentiable except inside trace-only guards that mirror C logging.
- Avoid `.cpu()` or fresh CPU tensor allocations inside hot loops; maintain device neutrality for GPU execution.
- Preserve vectorization—no per-pixel Python loops when modifying normalization or logging.
- Keep TRACE_PY ordering identical to TRACE_C so diff tooling works without manual alignment.
- Respect Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md) when editing files.
- Do not overwrite prior evidence bundles—create a fresh fix_<timestamp> directory.
- Ensure compare_scaling_traces.py is run after the fix so first_divergence resolves to None before closing Phase M4.
- Update sha256.txt after all artifacts are in place; stale checksums block future audits.
- Record git SHA and environment details so repro metadata stays verifiable.
- Leave `normalize_intensity` helper untouched unless absolutely necessary; scope change to simulator main path only.
- Do not adjust capture_fraction or polarization semantics—they already match spec and C trace.
- Keep logging strings ASCII-only to preserve diff stability.
- Avoid editing archived bundles referenced by docs/fix_plan.md to maintain audit trails.
- Refrain from altering trace harness defaults beyond normalization; upstream tools expect current formatting.
- Skip nb-compare until Phase M5/M6 mark green to avoid mixing evidence stages.
Pointers:
- specs/spec-a-core.md:247
- golden_suite_generator/nanoBragg.c:3358
- src/nanobrag_torch/simulator.py:954
- plans/active/cli-noise-pix0/plan.md:68
- docs/fix_plan.md:466
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T223046Z/design_memo.md:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/analysis_20251008T212459Z.md:1
- docs/development/c_to_pytorch_config_map.md:1
- scripts/validation/compare_scaling_traces.py:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T043438Z/trace_py_scaling_cpu.log:1
- /tmp/m3a_instrumentation_design.md:1
- tests/test_cli_scaling_phi0.py:1
- tests/test_cli_scaling_parity.py:1
- docs/bugs/verified_c_bugs.md:182
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T070513Z/summary.md:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T070513Z/commands.txt:1
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T070513Z/sha256.txt:1
Next Up:
- Phase M4c/M4d parity evidence capture with full artifact bundle.
- Phase M5 CUDA + gradcheck smoke once CPU normalization fix lands cleanly.
- Phase M6 ledger/doc sync followed by Phase N nb-compare and Phase O supervisor rerun.
- Prep STATIC-PYREFLY-001 Phase A once normalization is green to unblock the static analysis backlog.
- Refresh docs/development/pytorch_runtime_checklist.md with normalization notes after Phase M6.
- Coordinate with VECTOR-TRICUBIC-001 to ensure detector absorption timelines stay aligned once scaling parity is restored.
- Schedule supervisor follow-up to review fix bundle and update galph_memory.md with closure details.
- Revisit perf plan (PERF-PYTORCH-004) once normalization impact is measured to verify no regressions in runtime traces.

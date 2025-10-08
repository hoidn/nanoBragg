Summary: Implement the Phase M4 normalization fix and prove the supervisor pixel now matches nanoBragg.c within VG-2 tolerances.
Mode: Parity
Focus: CLI-FLAGS-003 / Phase M4 normalization fix (plans/active/cli-noise-pix0/plan.md)
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py
Artifacts:
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/design_memo.md (spec + nanoBragg.c contract recap)
  - Summarise spec citations (specs/spec-a-core.md:446,576,633), C loop references (nanoBragg.c:3336-3365), and the planned tensor ops for normalization + logging.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/trace_py_fix.log and trace_c_baseline.log (per-φ parity)
  - Ensure TRACE_PY ordering matches TRACE_C, include per-step accumulators pre/post division, and note any residual <1e-9 drift.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/trace_py_phi.log (extended per-φ instrumentation output per M3a schema)
  - Capture both raw sums and normalized outputs so future probes can validate intermediate tensors.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/summary.md, metrics.json, compare_scaling_traces.txt, compare_scaling_traces.json
  - `summary.md` should list each factor, signed delta, and conclude with `first_divergence=None` when parity holds.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/pytest.log, pytest_collect.log, commands.txt, env.json, sha256.txt, git_sha.txt
  - Separate CPU vs CUDA logs (if both run) and record RNG seeds; env.json should capture python, torch, cuda, device, dtype.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/lattice_hypotheses.md addendum documenting Hypothesis H4 closure
  - Include the before/after intensity values, cite fix_<timestamp>, and mark Hypothesis H4 as closed or downgraded.
- reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/diff_trace.md (first-divergence narrative confirming parity)
  - Highlight the exact normalization line showing PyTorch now divides by `steps`; embed representative numeric comparison.
- docs/fix_plan.md Attempt #??? entry summarising Phase M4 completion with artifact links
  - Provide timestamp, git SHA, metrics (ΔI_before_scaling), list of artifacts, and note follow-on actions (Phase M5).
Do Now: CLI-FLAGS-003 Phase M4 (run M4a–M4d) — verify with KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py once the patch is ready
If Blocked: Capture partial progress in fix_<timestamp>/summary.md (note which M4 subtask hit issues), run pytest --collect-only -q tests/test_cli_scaling_phi0.py to document state, update docs/fix_plan.md Attempt entry with the blocker + artifact path, then stop.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:60-71 promotes the new M4a–M4d checklist as the gate before CUDA/nb-compare work.
- docs/fix_plan.md:461-468 now expects the checklist sequence and fix_<timestamp> bundle before moving to Phase M5.
- specs/spec-a-core.md:446 and specs/spec-a-core.md:576/633 articulate the mandatory `intensity /= steps` normalization we must restore.
- docs/development/c_to_pytorch_config_map.md:34-56 reinforces scaling parity expectations between C and PyTorch simulators.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/analysis_20251008T212459Z.md pins the 14.6% I_before_scaling deficit and Hypothesis H4.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T215700Z/phase_m3_probes/rotation_audit.md confirms rotation math is correct, letting us focus on normalization.
-How-To Map:
- Re-read spec & C contract: `sed -n '430,640p' specs/spec-a-core.md` and `rg -n "intensity" golden_suite_generator/nanoBragg.c | head` (confirm `steps` division placement).
- Design memo: document citations + planned tensor updates in `reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/design_memo.md` before editing code.
- Code edit target: `src/nanobrag_torch/simulator.py` (normalization after per-source sum); update per-φ logging hooks per `/tmp/m3a_instrumentation_design.md`.
- Pre-flight formatting check: run `python -m compileall src/nanobrag_torch/simulator.py` to confirm syntax before executing tests.
- Regenerate traces: `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --config supervisor --pixel 685 1039 --device cpu --dtype float64 --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/`.
- Capture C trace if baseline drifted: `NB_C_BIN=./golden_suite_generator/nanoBragg bash -lc "python reports/2025-10-cli-flags/phase_l/scaling_audit/run_c_trace.py --pixel 685 1039 --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/trace_c_baseline.log"` (or reuse archived log if git SHA unchanged).
- Compare scaling: `python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/c_trace_scaling.log --py reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/trace_py_fix.log --out reports/2025-10-cli-flags/phase_l/scaling_validation/fix_<timestamp>/summary.md` and store JSON output alongside.
- Tests: `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_scaling_phi0.py` (repeat with CUDA device if available; capture both logs).
- Additional guard: run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_cli_nonoise.py::TestCLINoise::test_noise_disabled_when_flag_set` to ensure no regressions from normalization changes.
- Update hypotheses: append closure note to `reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md` referencing fix_<timestamp> metrics and note Hypothesis H4 resolution.
- Update docs/fix_plan.md Attempt with metrics + artifact paths after artifacts exist; include SHA and summarized findings.
- Record commands/env: populate commands.txt, env.json, sha256.txt within fix_<timestamp> directory before ending loop.
- Verify gradient behaviour (if instrumentation touched differentiable tensors): run `KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_autograd_phi.py::TestPhiGradients::test_phi_requires_grad` (skip gracefully if selector missing but document in summary).
- Re-run `pytest --collect-only -q tests/test_cli_scaling_phi0.py` post-edit to confirm selectors still resolve.
- Update docs/fix_plan.md Attempt with metrics + artifact paths only after artifacts exist; include `git rev-parse HEAD` value.
- Append commands chronologically to commands.txt (CPU run, CUDA run, compare script, pytest) with numbering for reproducibility.
- Dump env metadata via `python -c "import json, os, sys, torch; print(json.dumps({'python': sys.version, 'torch': torch.__version__, 'cuda': torch.version.cuda, 'device': 'cpu', 'dtype': 'float64'}, indent=2))" > env.json` (and add CUDA variant if executed).

Attempts History Logging:
- docs/fix_plan.md Attempt: include UTC timestamp, git SHA, summary of normalization change + instrumentation, parity metrics, and artifact bullet list.
- plans/active/cli-noise-pix0/plan.md: flip M4 row to [D] with one-line status referencing fix_<timestamp> once parity is proven; mark M4a–M4d checklist states accordingly.
- galph_memory.md: add recap of Phase M4 completion, metrics, and next-focus (Phase M5) before finishing the loop.
- Partial loops: mark incomplete checklist rows as `[P]` with blocker description inside the plan tables before handing back.

Validation Checklist:
- [ ] Design memo written before touching code; includes spec + C references and tensor plan.
- [ ] Simulator patch keeps operations batched (no shape regressions verified via asserts or shape dumps).
- [ ] TRACE_PY vs TRACE_C diff returns zero first divergence (confirm via compare_scaling_traces and manual spot-check).
- [ ] `pytest -v tests/test_cli_scaling_phi0.py` passes on CPU (and CUDA if available) with logs saved.
- [ ] Optional guard test `tests/test_cli_nonoise.py::TestCLINoise::test_noise_disabled_when_flag_set` passes post-change.
- [ ] `lattice_hypotheses.md` updated with Hypothesis H4 disposition + metrics.
- [ ] docs/fix_plan.md updated with Attempt entry referencing artifact bundle.
- [ ] Plan checklist M4a–M4d states flipped to [D] with notes.
- [ ] galph_memory.md entry appended with summary and follow-up tasks.
Pitfalls To Avoid:
- Do not introduce `.item()`, `.cpu()`, or scalar loops; keep normalization batched over ROI/phi/mosaic/sources.
  - Verify via tensor `.shape` logging during development if unsure; remove prints before commit.
- Preserve device/dtype neutrality (derive tensors via `.type_as(...)` or existing buffers, no implicit CPU fallbacks).
  - Constants should be instantiated with `.new_tensor` or `.type_as` helpers to stay on caller device.
- Maintain per-φ logging schema compatible with existing Phase M artifacts (TRACE_PY_PHI ordering, 1-based step index).
  - Changing token names or order will break diff tooling; double-check against Phase M3 design document.
- Include the exact `nanoBragg.c` snippet in the updated docstring before writing implementation (CLAUDE Rule #11).
  - Snippet must be verbatim (no ellipses) and reference line numbers used in design memo.
- Ensure `fix_<timestamp>` bundle includes commands, env, sha256 — no empty files or missing metadata.
  - Run `find reports/.../fix_<timestamp> -maxdepth 1 -type f` to confirm required files exist before finishing.
- Run trace harness with float64 to match existing baseline; mixing dtypes will invalidate comparisons.
  - If CUDA run uses float32, document the dtype difference explicitly in summary.md.
- Keep Protected Assets intact (docs/index.md references input.md, loop.sh, supervisor.sh).
  - Never rename or delete these assets during cleanup; mention if touched for read-only access.
- Update docs/fix_plan.md Attempt entry after artifacts exist; don't pre-commit placeholder text.
  - Attempt entries without artifacts create audit gaps; delay update until bundle is immutable.
- Confirm C trace reused from baseline is still valid; re-run nanoBragg if git SHA drifted.
  - Note in commands.txt whether the baseline trace was regenerated or reused (include SHA check result).
- Avoid deleting historical evidence directories; create a new timestamped folder for this fix.
  - Use ISO8601 timestamp (UTC) to keep ordering consistent with earlier bundles.
Pointers:
- plans/active/cli-noise-pix0/plan.md:60-71 (Phase M4 instructions + checklist)
- docs/fix_plan.md:461-468 (Next Actions expectations)
- specs/spec-a-core.md:446 (intensity accumulator) and specs/spec-a-core.md:576 (steps division requirement)
- golden_suite_generator/nanoBragg.c:3336-3365 (reference normalization loop)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T212459Z/spec_baseline/commands.txt (baseline harness invocation)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T075949Z/lattice_hypotheses.md (Hypothesis ledger to update)
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T215755Z/phase_m3_probes/sincg_sweep.md (context for k_frac sensitivity)
- /tmp/m3a_instrumentation_design.md (logging schema to follow for per-φ traces)
- docs/architecture/pytorch_design.md:70-122 (vectorization + device/dtype guidance relevant to simulator edits)
- docs/development/testing_strategy.md:34-118 (authoritative commands + parity evidence requirements)
- reports/2025-10-cli-flags/phase_phi_removal/phase_d/20251008T203504Z/trace_py_spec.log (legacy trace format for comparison)
- docs/development/pytorch_runtime_checklist.md:1-80 (runtime guardrails to verify before/after edits)
Next Up:
- Phase M5 GPU + gradcheck validation once fix_<timestamp> bundle is green.

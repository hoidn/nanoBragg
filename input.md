Summary: Land SOURCE-WEIGHT Phase E parity so vectorization profiling can resume.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests:
- pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v
- pytest --collect-only -q
Artifacts:
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/commands.txt
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/summary.md
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/metrics.json
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/pytest.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/pytest_collect.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/c_stdout.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/py_stdout.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/warning.log
- reports/2025-11-source-weights/phase_e/<UTCSTAMP>/env.json
Do Now: [SOURCE-WEIGHT-001] Phase E — implement Option B divergence parity, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v`
If Blocked:
- Capture TC-D1 and TC-D3 CLI outputs with current simulator behaviour.
- Store binaries + stdout/stderr under reports/2025-11-source-weights/phase_e/<UTCSTAMP>/attempts/.
- Record blocker context and metrics in docs/fix_plan.md Attempts History before pausing.
Priorities & Rationale:
- spec/spec-a-core.md:150-190 requires that source weights are read but ignored, so parity hinges on enforcing equal weighting even when divergence grids are requested.
- docs/architecture/pytorch_design.md §§1.1,2.3 describe the intended batched source flow; these sections must reflect the Option B guard after implementation.
- plans/active/source-weight-normalization.md Phase E lists exit criteria (correlation ≥0.999, |sum_ratio−1| ≤1e-3) that unblock VECTOR-GAPS-002 profiling and PERF-PYTORCH-004.
- reports/2025-11-source-weights/phase_d/20251009T104310Z/commands.txt is the authoritative harness; reusing it preserves parity with prior evidence.
- docs/development/testing_strategy.md §1.4 mandates CPU+CUDA device discipline; at minimum provide CPU evidence and log CUDA status.
- docs/fix_plan.md `[SOURCE-WEIGHT-001]` needs a fresh Attempt entry summarising Phase E artefacts once complete.
How-To Map:
- Environment setup:
  - `export KMP_DUPLICATE_LIB_OK=TRUE`
  - `export NB_C_BIN=./golden_suite_generator/nanoBragg`
  - If the instrumented binary is unavailable, fall back to `./nanoBragg` and note it in env.json.
- Pre-flight checks:
  - Run `pytest --collect-only -q` and capture the log to phase_e/<stamp>/pytest_collect.log.
  - Verify that the new `TestSourceWeightsDivergence` suite is discovered.
- Implementation tasks:
  - Update simulator source accumulation so weights are ignored regardless of divergence flags; keep vectorized tensor operations (no Python loops).
  - Add a validation guard that emits `UserWarning` when a sourcefile is combined with divergence/dispersion parameters, consistent with Phase D2 design.
  - Store guard logic at the configuration boundary (BeamConfig or Simulator initialisation) to avoid runtime branching per pixel.
  - Maintain device/dtype neutrality; use `.type_as` or `.to` on existing tensors rather than `.cpu()`/`.cuda()`.
  - Ensure no `.item()` calls appear on tensors that carry gradients.
- Test authoring:
  - Create `TestSourceWeightsDivergence` in `tests/test_cli_scaling.py` with methods for TC-D1 parity, TC-D2 warning capture, and TC-D3 divergence-only control.
  - Parameterise tests over `device` with CPU required and CUDA conditional (`pytest.importorskip` or custom marker) to satisfy runtime checklist guidance.
  - For TC-D2, assert that the warning message matches the text recorded in `reports/2025-11-source-weights/phase_d/20251009T104310Z/warning_capture.log`.
- Targeted testing:
  - Run `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeightsDivergence -v` and save stdout to phase_e/<stamp>/pytest.log.
  - Note skipped CUDA cases explicitly in the log if GPU unavailable.
- CLI parity runs (reuse Phase D3 commands):
  - TC-D1 C reference and PyTorch runs using `reports/2025-11-source-weights/fixtures/A.mat`, the weighted sourcefile fixture, `-oversample 1`, `-nonoise`, `-nointerpolate`.
  - TC-D2 PyTorch-only run that should emit the warning; pipe stderr to `warning.log`.
  - TC-D3 C and PyTorch runs with divergence-only configuration to confirm grid parity.
  - Optionally include TC-D4 metrics capture by repeating TC-D1 and computing correlation/sum_ratio.
  - Copy the exact command set from the harness into phase_e/<stamp>/commands.txt with timestamps.
- Metrics capture:
  - Use the provided Python snippet (or equivalent) to compute correlation and sum_ratio for TC-D1; store numeric results in metrics.json.
  - Document findings, thresholds, device info, and warning text in summary.md.
  - Include counts of generated sources/steps from both C and PyTorch logs for traceability.
- Documentation updates:
  - Amend `docs/architecture/pytorch_design.md` Sources subsection to note that weights are ignored and describe the new warning behaviour.
  - If the spec requires clarification, add draft language to `specs/spec-a-core.md` referencing Option B; coordinate with supervisor if further review needed.
- Ledger updates:
  - Append a new Attempt entry under `[SOURCE-WEIGHT-001]` in docs/fix_plan.md with artifact paths, metrics, warning text, CPU/GPU status, and follow-up actions.
  - Update the Status Snapshot in plans/active/source-weight-normalization.md marking Phase E tasks complete as you finish them.
Pitfalls To Avoid:
- Do not alter divergence grid auto-selection semantics beyond the agreed warning; the goal is documentation + guard, not changing source counts.
- Avoid duplicating weight-ignore logic in multiple places; centralise behaviour to maintain traceability.
- Keep Protected Assets listed in docs/index.md untouched (loop.sh, supervisor.sh, input.md, etc.).
- Ensure reports directories use ASCII names and UTC timestamps (e.g., 20251009T104310Z).
- Do not drop existing regression tests or fixtures while adding new coverage.
- Refrain from adding ad-hoc scripts outside `scripts/` — place helpers under `scripts/validation/` if needed.
- Capture warning text via stderr redirection; do not rely solely on pytest output for documentation.
- When rerunning CLI commands, clean `/tmp` outputs between runs to avoid mixing artifacts.
- For CUDA runs, guard with `torch.cuda.is_available()` and document skip reasons.
- Maintain differentiability by avoiding in-place ops that would share storage across gradient paths.
Pointers:
- plans/active/source-weight-normalization.md#phase-e-implementation--verification — phase checklist and acceptance criteria.
- reports/2025-11-source-weights/phase_d/20251009T103212Z/design_notes.md — Option B decision matrix and warning copy.
- reports/2025-11-source-weights/phase_d/20251009T104310Z/summary.md — metrics scaffold and command references for Phase E.
- reports/2025-11-source-weights/phase_a/20251009T071821Z/summary.md — baseline bias metrics useful for before/after comparison.
- docs/development/c_to_pytorch_config_map.md (Beam table) — ensure CLI parameters map one-to-one across implementations.
- docs/debugging/debugging.md (Parallel Trace SOP) — follow if CLI parity metrics fall below thresholds.
- docs/development/testing_strategy.md §1.4 — reiterates device/dtype neutrality requirements for PyTorch edits.
- CLAUDE.md (Protected Assets rule) — reminder not to rename or delete artifacts referenced there.
- galph_memory.md entry 2025-12-24 (Source-weight Phase D3) — prior supervisor guidance and expectations for Phase E.
Next Up:
- VECTOR-GAPS-002 Phase B1 profiler rerun once Phase E metrics meet thresholds and dependencies are notified.
- PERF-PYTORCH-004 Phase B6/B7 warm benchmark once source-weight parity unblock is confirmed.

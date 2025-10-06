Header:
- Timestamp: 2025-10-06T08:04:56Z
- Commit: 17d8097
- Author: galph
- Active Focus: CLI-FLAGS-003 Phase H3b2 pix0 precedence fix
- Active Phase: Implementation loop against supervisor command parity
- AUTHORITATIVE_CMDS_DOC: docs/development/testing_strategy.md
- Supervisor Command Context: prompts/supervisor.md lists the parity command requiring pix0 precedence.
- Reports Target Directory: reports/2025-10-cli-flags/phase_h/implementation/.
- Evidence Status: Phase H3b1 completed (Attempt #23) — precedence proof on file.
- Reports Archive Trigger: Move artifacts to reports/archive/ once CLI-FLAGS-003 closes.
- Attempt Counter: Prepare Attempt #24 entry in docs/fix_plan.md upon completion.
- Attempt Window: Evidence refreshed; implementation and regression updates required this loop.
Summary: Align pix0 override precedence with C when custom detector vectors are supplied so the supervisor command geometry matches.
Phase: Implementation
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm (Phase H3b2/H3b3)
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -v
Artifacts: reports/2025-10-cli-flags/phase_h/implementation/ (pix0_override_validation.md, pytest_TestCLIPix0Override_cpu.log[,cuda.log], refreshed pix0_expected.json if needed)

Do Now: CLI-FLAGS-003 Phase H3b2 — env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -v

If Blocked:
- Re-run reports/2025-10-cli-flags/phase_h/trace_harness.py with and without `-pix0_vector_mm` to reconfirm precedence.
- Capture detector traces plus comparison notes in pix0_mapping_analysis.md to confirm evidence, then reassess blocking issue.
- Escalate only after documenting the obstacle in docs/fix_plan.md Attempt log, implementation_notes.md, and attempts_history/attempt_log.txt.
- If CLI parser prevents reproductions, verify NB_C_BIN path and record raw command + stderr under reports/2025-10-cli-flags/phase_h/debug/.
- Double-check pytest node discovery with `pytest --collect-only` if the mapped test fails to collect, then log the output.
- Validate environment variables (KMP_DUPLICATE_LIB_OK, PYTHONPATH) before retrying runs to avoid false negatives.

Priorities & Rationale:
- docs/fix_plan.md:448 — Next actions call for precedence enforcement before further CLI parity checks.
- plans/active/cli-noise-pix0/plan.md:90 — Phase H3b2/H3b3 tasks list concrete prerequisites, validations, and exit criteria.
- reports/2025-10-cli-flags/phase_h/implementation/pix0_mapping_analysis.md — Demonstrates C ignoring the override when custom vectors exist; implementation must reflect this precedence.
- src/nanobrag_torch/models/detector.py:450 — Present override projection causes ~1.14 mm Y error and cascades into scattering vector drift.
- tests/test_cli_flags.py:470 — Regression still expects override to modify pix0; update to assert no-effect for CUSTOM with override.
- docs/development/c_to_pytorch_config_map.md — Confirms CUSTOM convention side-effects (beam pivot, 0.5 pixel offsets) that interplay with pix0 logic.
- docs/architecture/detector.md:5 — Clarifies pix0 derivation order and rotation sequencing we must preserve.
- docs/debugging/detector_geometry_checklist.md — Reminder of parity SOP, including verifying units before concluding fixes.
- reports/2025-10-cli-flags/phase_h/implementation/implementation_notes.md — Needs new entry summarising precedence fix rationale once complete.
- galph_memory.md latest entry — Highlights expectation to close Phase H3b2 before moving to parity.
- docs/development/pytorch_runtime_checklist.md — Reinforces device/dtype neutrality rules to observe during Detector edits.
- docs/architecture/pytorch_design.md:2.1 — Notes caching invariants we must respect when updating Detector state.

How-To Map:
- Review pix0_mapping_analysis.md evidence to refresh the precedence findings before coding.
- Modify src/nanobrag_torch/models/detector.py so CUSTOM convention ignores pix0_override_m whenever any custom vectors are configured.
- Ensure the override path still assigns pix0 directly when no custom vectors exist (MOSFLM/XDS defaults) and retains r_factor updates.
- Preserve device/dtype neutrality by allocating tensors via `.to(device=self.device, dtype=self.dtype)` and avoiding `.cpu()`/`.cuda()` inline.
- Refresh beam_center tensors, r_factor, close_distance, and cached pix0/basis vectors after precedence logic executes to keep caching coherent.
- Update tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot with two assertions: (a) CUSTOM+override leaves pix0 identical to custom-only case; (b) baseline (no custom vectors) still honors override inputs.
- Add fixture-level helper if necessary to avoid repeated CLI parsing boilerplate while keeping test deterministic.
- Run env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -v on CPU, then rerun with CUDA_VISIBLE_DEVICES=0 when GPU is available to confirm device neutrality.
- Capture validation outputs under reports/2025-10-cli-flags/phase_h/implementation/ (e.g., pix0_override_validation.md with before/after table, pytest logs named with timestamp, refreshed pix0_expected.json if values change).
- Record Attempt #24 for CLI-FLAGS-003 in docs/fix_plan.md including metrics (max pix0 delta vs C, beam-centre deltas, test status) and link to artifacts.
- Update implementation_notes.md and attempts_history/attempt_log.txt with narrative summary before handing back to supervisor loop.
- If parity remains off after fix, queue data for Phase H4 without reverting the precedence change.
- Verify noise generation path still respects suppress_noise flag by spot-checking config['suppress_noise'] after CLI parse.
- Confirm pix0_override_m remains stored on DetectorConfig for downstream debugging even when ignored.
- Re-run minimal CLI parse smoke (`PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch --help`) if argparse options were touched.

Pitfalls To Avoid:
- No `.item()`, `.detach()`, or `.numpy()` on tensors that must remain differentiable in Detector or Simulator paths.
- Maintain device/dtype neutrality—allocate new tensors with `.to(device=self.device, dtype=self.dtype)` and avoid silent CPU allocations.
- Avoid reintroducing per-pixel Python loops; keep geometry computations vectorized to respect PyTorch runtime guardrails.
- Honor Protected Assets by checking docs/index.md before touching referenced files (loop.sh, supervisor.sh, input.md, etc.).
- Keep CLI parser behavior intact including mutual exclusion of pix0 flags and preservation of existing help text.
- Do not regress CUSTOM orientation math or beam vector propagation implemented in Phase F (see src/nanobrag_torch/models/detector.py:840).
- Resist running the full pytest suite; confine execution to mapped nodes unless a targeted failure requires adjacent tests.
- Always set KMP_DUPLICATE_LIB_OK=TRUE prior to importing torch or executing pytest nodes to prevent MKL conflicts.
- Update attempt logs (docs/fix_plan.md, implementation_notes.md, attempts_history/attempt_log.txt) before concluding; missing notes block supervisor sign-off.
- Maintain deterministic artifact naming under reports/2025-10-cli-flags/phase_h/implementation/ for reproducibility across loops.
- Do not delete or rename pix0_expected.json without updating docs/index.md references per Protected Assets rule.
- Avoid editing golden_suite_generator traces directly; regenerate via NB_C_BIN when new evidence is needed.
- Ensure pix0_override tensors stay float32/float64 consistently; avoid implicit dtype promotion that could break gradchecks.
- Verify NB_C_BIN references remain untouched; they will be needed for later parity checks.
- Keep ROI logic untouched; precedence change should not mutate intensity masks used by noise handling.

Pointers:
- docs/development/c_to_pytorch_config_map.md — Detector precedence, pivot implications, and CUSTOM side effects.
- docs/architecture/detector.md:5 — Pix0 computation order, rotation application, and unit conventions.
- docs/debugging/detector_geometry_checklist.md:1 — Step-by-step expectations before declaring detector parity solved.
- plans/active/cli-noise-pix0/plan.md:90 — Phase H3b2/H3b3 checklist, artifact requirements, and next-phase gating.
- reports/2025-10-cli-flags/phase_h/implementation/pix0_mapping_analysis.md — Evidence driving precedence decision.
- reports/2025-10-cli-flags/phase_h/implementation/implementation_notes.md — Where to append loop findings.
- src/nanobrag_torch/models/detector.py:500 — Override logic to adjust.
- tests/test_cli_flags.py:440 — CLI regression coverage to rewrite for precedence behavior.
- docs/development/testing_strategy.md:1.5 — Authoritative command discipline ensuring reproducible validations.
- prompts/supervisor.md — Source of the supervisor command we must satisfy post-fix.
- galph_memory.md latest section — Captures expectations for CLI-FLAGS-003 progression.
- implementation_notes.md — Running log that must record precedence change outcomes.
- tests/test_cli_flags.py:120 — Helper utilities reused across CLI flag tests; adjust if new fixtures are introduced.
- src/nanobrag_torch/config.py:200 — DetectorConfig fields storing pix0_override_m and custom vectors.

Next Up:
- H4 parity rerun for the supervisor command once pix0 precedence fix lands and regression test passes; store metrics under reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/.
- Phase G orientation preservation (retain A.mat reciprocal vectors) if mismatch persists after pix0 fix; prep design notes referencing docs/architecture/pytorch_design.md §2.2.
- Revisit polarization plan (Phase I) only after lattice parity passes, ensuring Kahn factor logic references latest traces.
- Prep vectorization Phase A baselines once CLI parity stabilises so Ralph can pivot to VECTOR-TRICUBIC-001 without context loss.
- Schedule documentation refresh (docs/architecture/detector.md, docs/development/testing_strategy.md) after precedence fix to record new behavior.

Summary: Implement BEAM-pivot pix0 override transform + regression harness
Phase: Implementation
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm (Phase H3b)
Branch: feature/spec-based-2
Mapped tests: env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -v
Artifacts: reports/2025-10-cli-flags/phase_h/implementation/

timestamp: 2025-10-06 07:15:24Z
commit: 2113548
author: galph
Active Focus: CLI-FLAGS-003 Phase H3b — enforce BEAM-pivot pix0 override parity

Do Now: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm (Phase H3b) — run `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -v`

If Blocked: Capture fresh C & PyTorch traces via `reports/2025-10-cli-flags/phase_h/trace_harness.py`, stash outputs plus first-divergence notes in `reports/2025-10-cli-flags/phase_h/implementation/blocked.md`, and record an Attempt in docs/fix_plan.md so the next supervisor loop has evidence.

Priorities & Rationale:
- docs/fix_plan.md:448 — Next Actions enumerate the projection math, regression node, and artifact drop points required to unblock Phase H4.
- plans/active/cli-noise-pix0/plan.md:91 — Phase H3b guidance specifies the beam-term subtraction and beam-centre recomputation we must follow verbatim.
- docs/architecture/detector.md:35 — Canonical BEAM pivot equation; the override path must flow through this exact formula to stay spec compliant.
- docs/development/c_to_pytorch_config_map.md:53 — Mapping between CLI beam flags and DetectorConfig ensures header parity once we rewrite beam centres from override-derived offsets.
- docs/development/testing_strategy.md:18 — Device/dtype discipline and targeted test requirements govern validation once code changes land.
- reports/2025-10-cli-flags/phase_a/README.md — Contains the authoritative C pix0 vector for the supervisor command; we must encode it into `pix0_expected.json`.
- golden_suite_generator/nanoBragg.c:1833 — Source-of-truth C snippet showing the BEAM pivot transform we are replicating.
- scripts/debug_pixel_trace.py — Parallel trace harness to confirm pix0 alignment before moving to lattice parity.

How-To Map:
1. Export loop env: `export AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md` and `export KMP_DUPLICATE_LIB_OK=TRUE` before any command; keep both for the entire session.
2. Prepare workspace directories:
   - `mkdir -p reports/2025-10-cli-flags/phase_h/implementation`
   - `cp reports/2025-10-cli-flags/phase_a/pix0_trace/trace.log reports/2025-10-cli-flags/phase_h/implementation/pix0_trace_reference.log`
3. Derive the C expectation:
   - `grep DETECTOR_PIX0_VECTOR reports/2025-10-cli-flags/phase_a/pix0_trace/trace.log > reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.txt`
   - Convert the meters-valued triple into JSON with 1e-12 precision; save as `pix0_expected.json` alongside the text file.
4. Update `src/nanobrag_torch/models/detector.py` (BEAM pivot branch):
   - Ensure all tensors (`beam_vector`, `fdet_vec`, `sdet_vec`, `odet_vec`) are on the detector device/dtype.
   - Compute `beam_term = self.distance_corrected * beam_vector` using tensor ops only.
   - Set `pix0_delta = pix0_override_tensor - beam_term` and project onto detector axes to get `Fbeam_override`/`Sbeam_override` (use `torch.dot`).
   - Recalculate `self.beam_center_f` and `self.beam_center_s` in pixel units via division by `self.pixel_size`; keep gradients and device alignment intact.
   - Reuse the standard formula `self.pix0_vector = -Fbeam * self.fdet_vec - Sbeam * self.sdet_vec + self.distance_corrected * beam_vector`.
   - Refresh `self.close_distance = torch.dot(self.pix0_vector, self.odet_vec)` so obliquity math stays consistent.
   - Leave SAMPLE pivot path untouched; add guards so override logic triggers only for BEAM pivot.
5. Verify caches: confirm `_cached_pix0_vector` and `_cached_basis_vectors` refresh naturally after `_calculate_pix0_vector()`; adjust if the override path previously returned early.
6. Add regression to `tests/test_cli_flags.py`:
   - Introduce `class TestCLIPix0Override` with helper fixtures for CLI invocation.
   - Parameterize over `device in ['cpu', 'cuda']` (guard CUDA availability) so both pathways are checked when possible.
   - CLI invocation must include `-pix0_vector_mm` with supervisor command values, `-nonoise`, and the existing plan-controlled ROI to keep runtime modest.
   - Load `pix0_expected.json` and compare to the detector-side pix0 tensor with `torch.allclose(..., atol=5e-5, rtol=0)`.
   - Assert that CLI-reported beam centres (fast/slow mm) map back to the override-derived offsets; rely on header parsing helpers if available.
7. Extend regression coverage: check that `Detector.r_factor` remains finite and that `distance_corrected` equals the C trace value (store both numbers in notes for trace comparison).
8. Document math and evidence in `reports/2025-10-cli-flags/phase_h/implementation/implementation_notes.md`:
   - Outline the projection derivation step-by-step.
   - Log numeric values for `Fbeam_override`, `Sbeam_override`, `close_distance`, and beam centres in both meters and mm.
   - Record any device/dtype considerations or guards added.
9. Run targeted pytest on CPU:
   - `env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -v | tee reports/2025-10-cli-flags/phase_h/implementation/pytest_TestCLIPix0Override_cpu.log`
   - Confirm the log shows the new test passing and no regressions in neighbouring CLI tests.
10. If CUDA is available, rerun with GPU:
    - `CUDA_VISIBLE_DEVICES=0 env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -v --device cuda | tee reports/2025-10-cli-flags/phase_h/implementation/pytest_TestCLIPix0Override_cuda.log`
    - Add a note if CUDA is unavailable, citing the command output.
11. Refresh trace comparison:
    - `PYTHONPATH=src KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_h/trace_harness.py > reports/2025-10-cli-flags/phase_h/implementation/trace_py_after_H3b.log`
    - Diff against the existing C trace (`diff -u ... trace_py_after_H3b.log reports/2025-10-cli-flags/phase_e/c_trace_beam.log > .../trace_diff_after_H3b.txt`).
12. Update docs/fix_plan.md Attempt history with Attempt #22 summarising implementation results, pytest status, trace diff outcome, and stored artifacts.
13. Leave a brief TODO in `implementation_notes.md` for Phase H4 (e.g., polarization still pending) so follow-up work is explicit.

Artifact Checklist:
- reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.txt — raw DETECTOR_PIX0_VECTOR line from C trace.
- reports/2025-10-cli-flags/phase_h/implementation/pix0_expected.json — JSON copy used by the regression.
- reports/2025-10-cli-flags/phase_h/implementation/implementation_notes.md — math, tensor values, next actions.
- reports/2025-10-cli-flags/phase_h/implementation/pytest_TestCLIPix0Override_cpu.log — CPU pytest output.
- reports/2025-10-cli-flags/phase_h/implementation/pytest_TestCLIPix0Override_cuda.log — CUDA pytest output (or note absence).
- reports/2025-10-cli-flags/phase_h/implementation/trace_py_after_H3b.log — post-fix PyTorch trace.
- reports/2025-10-cli-flags/phase_h/implementation/trace_diff_after_H3b.txt — diff vs C reference trace.
- reports/2025-10-cli-flags/phase_h/implementation/blocked.md — only if progress stalls; include commands + stdout.

Verification Checklist:
- [ ] New regression passes on CPU and, when possible, CUDA.
- [ ] `self.pix0_vector` matches C within 5e-5 m on all components.
- [ ] `beam_center_f`/`beam_center_s` tensors update and remain differentiable (check `.requires_grad`).
- [ ] `self.close_distance` equals the dot product of pix0 and odet (log both values in notes).
- [ ] Trace diff shows no divergence in pix0, Fbeam, Sbeam, or incident beam lines.
- [ ] docs/fix_plan.md Attempt #22 added with artifact references.
- [ ] No unintended modifications to `detector.py.backup` or other protected files.
- [ ] Working tree clean except for intentional changes and new artifacts before finishing.

Pitfalls To Avoid:
- Directly assigning `pix0_override` to `self.pix0_vector` skips the BEAM formula and breaks parity.
- `.item()` or `.detach()` on tensors severs gradient flow; keep operations tensor-bound.
- Forgetting to update beam-centre tensors leaves SMV headers inconsistent with pix0.
- Implicit CPU tensor creation (e.g., `torch.tensor([...])` without device) will crash CUDA runs.
- Editing archive or backup files (e.g., `detector.py.backup`) instead of the live module.
- Skipping cache refresh leads to stale pixel coordinate caches and bogus traces.
- Running the full pytest suite violates the testing cadence for this loop; stick to targeted nodes.
- Ignoring CUSTOM convention side-effects (beam/polar/spindle vectors) risks regressions in other CLI scenarios.
- Failing to capture artifacts before git commit leaves plan items unverifiable.
- Omitting Attempt updates in docs/fix_plan.md obscures progress and blocks future loops.

Trace Validation Steps:
- Confirm `TRACE_PY: pix0_vector` lines match the C trace numerically.
- Check `TRACE_PY: Fbeam_m` and `TRACE_PY: Sbeam_m` after the fix to ensure offsets updated.
- Verify `TRACE_PY: distance_m` equals C `distance` (post r-factor correction).
- Ensure `TRACE_PY: incident_beam` still reflects the CLI custom vector.
- Document any remaining divergence in `trace_diff_after_H3b.txt` with hypotheses.

Pointers:
- docs/fix_plan.md:448
- plans/active/cli-noise-pix0/plan.md:91
- docs/architecture/detector.md:35
- docs/development/c_to_pytorch_config_map.md:53
- docs/development/testing_strategy.md:18
- reports/2025-10-cli-flags/phase_a/pix0_trace/trace.log
- reports/2025-10-cli-flags/phase_h/trace_harness.py
- scripts/debug_pixel_trace.py
- golden_suite_generator/nanoBragg.c:1833
- src/nanobrag_torch/models/detector.py:326
- docs/debugging/debugging.md:20
- docs/index.md:20

Next Up:
- Phase H4 lattice parity smoke once pix0 override math lands, followed by Phase I polarization alignment and eventual parity rerun against the supervisor command.

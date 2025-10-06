timestamp: 2025-10-06 08:31:05Z
commit: 85d5e45
author: galph
focus: CLI-FLAGS-003 Phase H4 pix0 parity
Do Now: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm — env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot -v
If Blocked: Capture current pix0 delta via KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_h/trace_harness.py --mode pix0-only --outdir reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/blocked && append metrics + stacktrace to reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/blocked.md
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:95 anchors this loop in Phase H4 with explicit success metrics (≤5e-5 m pix0 delta, <0.5% F_latt drift, <10× intensity ratio).
  The plan also lists mandatory artifacts under reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/ that we must produce before closing the phase.
- plans/active/cli-noise-pix0/plan.md:99-113 now marks H3b2/H3b3 as ✅, highlighting the remaining 3.9 mm Y-offset and pointing to the C recomputation we have to port.
  This keeps the precedence work locked in while flagging the geometry gap we are tackling today.
- docs/fix_plan.md:448-465 reconfirms CLI-FLAGS-003 is in progress and elevates the post-rotation beam-centre recomputation as the highest-priority next action.
  Updating this entry after we finish ensures the broader ledger sees H4 progress.
- reports/2025-10-cli-flags/phase_h/implementation/pix0_mapping_analysis.md:116-123 records the precedence evidence and leaves H4 unchecked.
  Treat it as the evidence source we must close out with the new parity logs.
- golden_suite_generator/nanoBragg.c:1822-1860 contains the canonical `newvector` projection and dot products that recalculate Fbeam/Sbeam.
  Porting this sequence exactly (tensorised) is the key to eliminating the 3.9 mm delta.
- tests/test_cli_flags.py:439-520 encodes both precedence scenarios and currently tolerates 5 mm error.
  Tightening that tolerance after the fix is part of the Do Now pytest run.
- reports/2025-10-cli-flags/phase_h/trace_comparison.md documents the current divergence cascade (pix0 → Miller indices → F_latt), giving us a baseline for validation.
  Refresh this report once the new trace pair is captured so downstream phases inherit accurate context.
How-To Map:
1. Review the C implementation:
   Read golden_suite_generator/nanoBragg.c lines 1180-1860, focusing on how `Fbeam`, `Sbeam`, `pix0_vector`, and `newvector` interact for CUSTOM detectors with BEAM pivot.
   Pay attention to the order of `rotate`, `dot_product`, and `unitize` calls to avoid subtle sign errors.
2. Mirror the logic in Detector:
   In src/nanobrag_torch/models/detector.py inside `_calculate_pix0_vector`, extend the CUSTOM + BEAM branch to recompute Fbeam/Sbeam/beam centres after pix0 is formed.
   Reuse tensor operations (torch.dot, torch.matmul) and ensure values stay on `self.device` with dtype `self.dtype`.
3. Maintain precedence safeguards:
   Keep the existing `has_custom_vectors` gating, but insert the recomputation immediately after pix0 assignment so overrides remain skipped in CUSTOM mode.
   Confirm that all new tensors respect differentiability (no .item / .cpu).
4. Refresh dependent state:
   Update `self.beam_center_f/s`, `self.r_factor`, `self.distance_corrected`, and `self.close_distance` using tensor math.
   Refresh `_cached_pix0_vector` and `_geometry_version` so cached grids stay accurate.
5. Regenerate PyTorch trace:
   Run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_h/trace_harness.py --mode pix0 --no-polar --outdir reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/`.
   This writes `py_trace.log`, JSON metrics, and summary scaffolding in the parity_after_lattice_fix folder.
6. Gather C reference:
   Execute `timeout 180 env NB_C_BIN=./golden_suite_generator/nanoBragg KMP_DUPLICATE_LIB_OK=TRUE python scripts/c_reference_runner.py --config prompts/supervisor_command.yaml --out reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/c_trace.log`.
   Reusing the same command ensures 1:1 trace structure for diffing.
7. Diff the traces:
   Use `python scripts/validation/diff_traces.py --c reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/c_trace.log --py reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/py_trace.log --out reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/trace_diff.txt`.
   Validate that pix0, Fbeam, Sbeam, F_latt, and intensity rows align within plan tolerances (<5e-5 m, <0.5%, <10×).
8. Run targeted pytest:
   Execute the Do Now command on CPU first.
   If CUDA is available, rerun with `CUDA_VISIBLE_DEVICES=0 PYTORCH_TEST_DEVICE=cuda` to ensure device neutrality.
   After the fix, tighten the tolerance inside the test to ≤5e-5 m and commit the change as part of this loop.
9. Summarise evidence:
   Update `reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/summary.md` with component-wise pix0 deltas, relative F_latt errors, and intensity ratios.
   Include command transcripts or references to the logs stored in the same directory.
10. Log attempts:
    Append Attempt #25 to docs/fix_plan.md under CLI-FLAGS-003, referencing the new summary, traces, and pytest log.
    Note both CPU and CUDA (if run) results and any remaining discrepancies.
Pitfalls To Avoid:
- Do not loosen tolerances—only tighten them once geometry aligns.
  Regressions here mask real discrepancies and contradict the plan’s exit criteria.
- Avoid `.item()`, `.cpu()`, `.detach()`, or numpy conversions in the recomputation path.
  These sever gradients and violate differentiability requirements in docs/architecture/pytorch_design.md.
- Keep tensors on the detector’s device/dtype when recomputing beam centres and distances.
  Implicit CPU allocations will break CUDA runs.
- Do not touch `_pixel_coords_cache` invalidation beyond refreshing it after pix0 changes.
  Extra invalidations can cause unnecessary recomputations and perf regressions.
- Preserve Protected Assets (docs/index.md). Never rename/delete loop.sh, supervisor.sh, input.md, or other listed files during cleanup.
- Resist running the entire pytest suite; rely on the targeted node plus the trace harness to keep the loop focused.
- Always set `KMP_DUPLICATE_LIB_OK=TRUE` before importing torch to avoid libomp crashes (see CLAUDE.md Rule 6).
- When editing trace scripts, keep filenames and formats consistent so diff tooling continues to work.
- Document each command in reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/summary.md or attempt_log.txt to preserve reproducibility.
- If a discrepancy remains, stop after evidence capture and flag it; do not forge ahead with half-fixed geometry.
Pointers:
- plans/active/cli-noise-pix0/plan.md:95-117 — authoritative Phase H guidance and checklist.
  Use it to verify prerequisites and exit criteria before concluding the loop.
- docs/development/c_to_pytorch_config_map.md: detector section — confirms CUSTOM pivot precedence and unit expectations.
  Helpful when validating beam centre conversions.
- docs/architecture/detector.md:310-410 — explains pix0 derivation, CUSTOM vectors, and BEAM pivot specifics.
  Align your implementation details with this contract.
- reports/2025-10-cli-flags/phase_h/trace_comparison.md — current PyTorch vs C delta summary.
  Refresh after generating new traces to keep historical context accurate.
- specs/spec-a-cli.md:120-185 — normative description of `-pix0_vector_mm`, `-Xbeam`, `-Ybeam`, and detector conventions.
  Use it to double-check CLI parsing assumptions if new edge cases appear.
- prompts/supervisor.md — stores the parallel comparison command to reproduce end-to-end scenarios.
  Always rerun this command when verifying parity changes.
Next Up:
- After pix0 parity and tightened tolerances land, proceed to Phase H parity rerun per plan.
  Archive the parity artifacts under reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/ and update docs/fix_plan.md accordingly.
- Once Phase H exit criteria are satisfied, queue Phase I (polarization alignment) as described in plans/active/cli-noise-pix0/plan.md:121-132.
  Gather preliminary evidence (Kahn factor traces) but defer implementation until H4 is officially closed.
- Before handing off to Phase I, ensure `reports/2025-10-cli-flags/phase_h/parity_after_lattice_fix/summary.md` captures device/dtype coverage and notes any residual quirks (e.g., tolerance adjustments).
- Prepare a CUDA smoke command (`env KMP_DUPLICATE_LIB_OK=TRUE PYTORCH_TEST_DEVICE=cuda python -m nanobrag_torch ...`) for the eventual parity rerun so we can reuse it in the final validation pass.
- Start outlining the polarization audit by bookmarking nanoBragg.c lines 2080-2155 and documenting expected Kahn factors in reports/2025-10-cli-flags/phase_i/notes.md (create directory on demand, no code yet).
- Catalogue any follow-on cleanups (e.g., removing pix0 fallback comments) in plans/active/cli-noise-pix0/plan.md so we can close the plan cleanly once Phase I finishes.
- Flag any surprises (trace mismatches, command failures) immediately in docs/fix_plan.md Attempts so supervisor can adjust the plan before the next loop starts.
- Leave a short note in reports/2025-10-cli-flags/phase_h/attempt_log.txt summarising commands, hashes, and outcomes to keep the evidence trail unbroken.
- If time remains, stage a draft of polarization trace harness inputs (device, dtype) but do not modify code; just note expected files so the next loop can start quickly.
- Double-check reports/2025-10-cli-flags/phase_h directories for stray `.DS_Store` or duplicate HKL files and clean them up if created during this loop (respect Protected Assets rule).
- Capture the final pix0/F_latt numbers in both JSON and Markdown form so they are machine- and human-readable for regression tracking.
- Ensure commit message references the parity work (e.g., "CLI pix0 recomputation") so history stays searchable for future regressions.
- Maintain the habit of running `git status` after each major step to catch accidental file churn (e.g., generated binary blobs) before staging.
- Keep `prompts/main.md` untouched unless explicitly instructed; routing automation depends on it staying stable.
- Verify that `scaled.hkl` remains the only HKL artifact in the repo root; delete `scaled.hkl.1` clones if tests regenerate them (document the removal in Attempt log).
- Before exiting, re-open plans/active/cli-noise-pix0/plan.md to ensure the checklist still mirrors the updated state (no regressions in the markdown tables).

diff --git a/docs/bugs/verified_c_bugs.md b/docs/bugs/verified_c_bugs.md
index 33d3bff..0a573fd 100644
--- a/docs/bugs/verified_c_bugs.md
+++ b/docs/bugs/verified_c_bugs.md
@@ -176,14 +176,14 @@ The follow-up log contains `reading Fs from Fdump.bin`, demonstrating the implic
 ```
 The trace (`docs/bugs/artifacts/c-parity-001.txt`) includes a single `TRACE_C: hkl_frac …` entry, regardless of φ step, confirming that the φ=0 pass reused the rotated vectors. Comparing successive pixels reveals identical `k_frac` values at φ=0 and the terminal φ step.
 
-**PyTorch Parity Shim:**
-- The PyTorch implementation provides an **opt-in** emulation of this bug via `--phi-carryover-mode c-parity`
-- **Default behavior** (`--phi-carryover-mode spec`) uses spec-compliant fresh rotations (no carryover)
-- **c-parity mode tolerance**: |Δk_frac| ≤ 5e-5, |Δb_y| ≤ 1e-4 (relaxed to document C bug behavior)
-- **spec mode tolerance**: |Δk_frac| ≤ 1e-6, |Δb_y| ≤ 1e-6 (strict, normative)
-- Dtype sensitivity analysis (2025-12-01) confirmed the ~2.8e-05 plateau is intrinsic to the carryover logic, not precision-limited
+**PyTorch Parity Shim (Historical):**
+- The PyTorch implementation **previously** provided an opt-in emulation of this C bug via `--phi-carryover-mode c-parity` (removed in commit 340683f, October 2025)
+- **Current behavior**: PyTorch uses spec-compliant fresh rotations exclusively (no carryover mode available)
+- **Historical c-parity mode tolerance**: |Δk_frac| ≤ 5e-5, |Δb_y| ≤ 1e-4 (relaxed to document C bug behavior)
+- **Current spec mode tolerance**: |Δk_frac| ≤ 1e-6, |Δb_y| ≤ 1e-6 (strict, normative)
+- Dtype sensitivity analysis (2025-12-01) confirmed the ~2.8e-05 plateau was intrinsic to the carryover logic, not precision-limited
 - Evidence: `reports/2025-10-cli-flags/phase_l/parity_shim/20251201_dtype_probe/analysis_summary.md`
-- **Documentation Status (2025-10-07)**: Phase L sync complete; dual thresholds documented in diagnosis.md and plan files. Implementation complete per `plans/active/cli-phi-parity-shim/plan.md` Phase C; documentation handoff (Phase D) in progress. Artifacts: `reports/2025-10-cli-flags/phase_l/rot_vector/20251007T212159Z/`
+- **Removal Status (2025-10-08)**: CLI flag removed (commit 340683f); config/model plumbing removal in progress per `plans/active/phi-carryover-removal/plan.md`. Documentation sync: `reports/2025-10-cli-flags/phase_phi_removal/phase_b/`
 
 **Relevant code:**
 - `golden_suite_generator/nanoBragg.c:3042-3059` — rotation only applied when `phi != 0.0`; no reset path exists.
diff --git a/prompts/supervisor.md b/prompts/supervisor.md
index b5d2c57..54aa1fb 100644
--- a/prompts/supervisor.md
+++ b/prompts/supervisor.md
@@ -4,7 +4,7 @@ planning, review and analysis. do not make implementation code changes.
 <current long-term goals>
 in order of decreasing priority:
 <1>
-Undo the architectural complexity and performance issues that were introduced by past reproduction of the phi carryover bug in the pytorch implementation (see <past long-term goals>). Corrsepondingly, deprecate the parallel test / acceptance test that was introduced by <past long term goals> <1> and target the correct, non-buggy spec behavior instead. (relaxing the parity test expectations is acceptable as well, but either way you MUST remove the phi-carryover codepath and any associated debt)
+Complete removal of phi-carryover technical debt from the PyTorch implementation. The CLI flag (`--phi-carryover-mode`) has been removed (commit 340683f). Remaining work: delete config/model plumbing, retire shim-specific tests, and realign documentation to reflect that PyTorch uses spec-compliant fresh rotations exclusively. See `plans/active/phi-carryover-removal/plan.md` for removal phases.
 </1>
 <2>
 review docs/bugs/verified_c_bugs.md and specs/. Make sure that the phi 0 carryover C implementation bug wasnt propagated to the specs. Update the specs (if needed) and pytorch implementation to fix this bug, if it was propagated.

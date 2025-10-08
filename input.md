Summary: Capture consecutive-pixel carryover evidence and extend the Option 1 cache design before touching production code.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/carryover_probe/, reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/commands.txt, reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md
Do Now: CLI-FLAGS-003 M2d — export RUN_DIR="reports/2025-10-cli-flags/phase_l/scaling_validation/$(date -u +%Y%m%dT%H%M%SZ)/carryover_probe" && mkdir -p "$RUN_DIR" && KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --roi 684 686 1039 1040 --phi-mode c-parity --dtype float64 --out "$RUN_DIR/trace_py_scaling.log"
If Blocked: Save stdout/stderr + exit code to "$RUN_DIR/commands.txt", run pytest --collect-only -q tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c for discovery proof, then log the obstacle (with paths) in docs/fix_plan.md Attempts.

Context:
- We must close Phase M2 prerequisites before any implementation retry. Commit 3269f6d created a cache that never fires and breaks gradients.
- Attempt #151 documented Option 1 (pixel-indexed cache) but lacks tensor-shape detail and paired-pixel evidence.
- Spec mode remains normative; parity mode alone should inherit C’s bug for validation.

Current Evidence State:
- Latest PyTorch trace (`reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T081932Z/trace_py_scaling.log`) shows TRACE_PY_ROTSTAR values changing only once per run.
- Metrics: F_latt (Py) = -2.380134142, F_latt (C) = -2.383196653 → Δ ≈ 3.06e-03; I_before_scaling Δ = -1968.57 (≈ -0.209%).
- No cross-pixel run yet demonstrating cache miss on the second pixel; we need that proof.

Design TODO after Do Now (same loop, time permitting):
- Update phi_carryover_diagnosis.md with Option 1 tensor shapes `(S,F,N_mos,3)`, cache initialisation/clear rules, and call sequence (Crystal → Simulator → trace harness).
- Note memory budget assumptions (full detector ≈ 4–8 GB @ float32) and how ROIs affect allocation.
- Clarify how gradients will remain intact (no `.detach()`, use gather/scatter or advanced indexing).

Priorities & Rationale:
- docs/fix_plan.md:451-465 — Next Actions require the cross-pixel probe and Option 1 design expansion before implementation.
- plans/active/cli-noise-pix0/plan.md:65-95 — M2 checklist tracks probe (M2d), design (M2f), implementation (M2g), validation (M2h), trace rerun (M2i).
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md:1 — Diagnosis document must become the authoritative Option 1 spec.
- docs/bugs/verified_c_bugs.md:166-204 — C bug definition that parity mode imitates; keep spec documentation unchanged.
- specs/spec-a-core.md:205-233 — Confirms normative φ rotations recompute each step (baseline for spec mode tests).

How-To Map:
- After running the ROI harness, copy stdout to "$RUN_DIR/commands.txt" with both the PyTorch command and the matching C command (`NB_C_BIN=./golden_suite_generator/nanoBragg ... --trace-pixel 685 1039`). Include SHA256 checksums via `sha256sum * > "$RUN_DIR/sha256.txt"`.
- Append ΔF_latt and ΔI_before_scaling for both pixels to reports/.../lattice_hypotheses.md (note cache-miss observations), then add an Attempt entry in docs/fix_plan.md referencing the new timestamp.
- Expand phi_carryover_diagnosis.md with Option 1 details (tensor shapes, API sketch, reset timing). Cite nanoBragg.c:2797,3044-3095 per CLAUDE Rule #11.
- Run the mapped pytest selector with --collect-only and store the output in "$RUN_DIR/pytest_collect.log" to validate discovery.
- Capture environment metadata (`python -V`, `torch.__version__`, `git rev-parse HEAD`) into "$RUN_DIR/env.json" for reproducibility.

Pitfalls To Avoid:
- Do not modify production carryover code this loop; evidence and documentation only.
- Avoid `.detach()` / `.clone()` on tensors that will later require gradients.
- Do not introduce per-pixel Python loops in exploratory scripts; keep traces vectorised.
- Skip full pytest runs; collect-only proof satisfies supervisor guardrails for evidence loops.
- Do not overwrite prior reports; always work inside a fresh timestamp directory.
- Keep spec-mode traces untouched—only c-parity runs are needed here.
- Ensure RUN_DIR uses UTC timestamp to avoid collisions across loops.
- Remember Protected Assets: do not move files listed in docs/index.md.
- Confirm `KMP_DUPLICATE_LIB_OK=TRUE` is set for every torch invocation.
- Document all commands in commands.txt (no undocumented manual steps).

Verification Targets for Future Loop (for awareness):
- Expect TRACE_PY cache-hit markers for the second pixel once Option 1 is implemented.
- metrics.json first_divergence should become `null` with ≤1e-6 relative deltas across factors.
- tests/test_cli_scaling_parity.py must pass on CPU float64 and (if available) CUDA float32 after implementation.

Reporting Checklist (this loop):
- Ensure RUN_DIR contains trace_py_scaling.log, commands.txt, env.json, sha256.txt, pytest_collect.log.
- Update docs/fix_plan.md Attempt with timestamp, command lines, ΔF_latt/ΔI_before_scaling, cache observations.
- Note plan progress in plans/active/cli-noise-pix0/plan.md when M2d or M2f completes.

Reference Metrics (do not overwrite):
- C trace baseline stored at reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log.
- Last PyTorch failing run `20251008T081932Z` should remain intact for comparison.

Documentation Hooks:
- After extending phi_carryover_diagnosis.md, include a short "Next steps" subheading referencing M2g implementation expectations.
- Keep textual additions ASCII-only (per editing constraints).

Communication Notes:
- If the ROI harness fails, capture the full traceback and note whether failure occurred before or after trace writing.
- If any new hypotheses arise (e.g., ordering of ROI indices), jot them in reports/.../lattice_hypotheses.md and flag in docs/fix_plan.md.

Sanity Checks Before Finishing:
- Confirm RUN_DIR contains artifacts and sha256.txt lists them all.
- Verify docs/fix_plan.md reflects the new Attempt number and plan progress.
- Ensure no untracked files remain outside the reports directory (run git status).

Pointers:
- docs/fix_plan.md:451-465
- plans/active/cli-noise-pix0/plan.md:65-95
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py
- docs/bugs/verified_c_bugs.md:166-204
- specs/spec-a-core.md:205-233

Next Up: Begin M2f/M2g preparation—finalise Option 1 tensor layout and plan code touchpoints—once the new carryover evidence and diagnosis addendum are checked in.

Gradient Considerations:
- Future implementation must keep gradients flowing from pixel intensities back to φ-dependent vectors; document any gradcheck failures verbatim.
- Plan for a minimal 2×2 ROI gradcheck harness so Option 1 changes can be validated quickly before large detector runs.

Open Questions to Track:
- Does the ROI ordering (slow-fast vs fast-slow) affect cache indexing? Note observations in lattice_hypotheses.md.
- Are there memory concerns on CUDA for full-detector caches? Record estimated tensor sizes after profiling.

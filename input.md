Summary: Capture a fresh failing run of the scaling-parity test so M2e has reproducible evidence before the Option 1 cache implementation starts.
Mode: Parity
Focus: [CLI-FLAGS-003] Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/parity_test_failure/{commands.txt,pytest.log,env.json,sha256.txt}
Do Now: CLI-FLAGS-003 M2e — export RUN_DIR="reports/2025-10-cli-flags/phase_l/scaling_validation/$(date -u +%Y%m%dT%H%M%SZ)/parity_test_failure" && mkdir -p "$RUN_DIR" && KMP_DUPLICATE_LIB_OK=TRUE pytest -vv tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c --maxfail=1 | tee "$RUN_DIR/pytest.log"
If Blocked: Capture stdout/stderr + exit code in "$RUN_DIR/commands.txt", run pytest --collect-only -q tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c for discovery proof, log the blocker (with artifact path) in docs/fix_plan.md Attempts, and stop.

Context:
- M2d and M2f are now complete; cross-pixel evidence lives under reports/20251008T100653Z and Option 1 design details are in phi_carryover_diagnosis.md.
- VG‑2 is still red because `_phi_carryover_cache` never fires per-pixel; F_latt and I_before_scaling disagree by ≈0.209%.
- Plan now expects a reproducible failing test log (M2e) before any code changes so we can diff pre/post traces.
- Parity shim mimics the C φ=0 carryover bug; spec mode remains the normative reference and must stay untouched.
- Feature branch `feature/spec-based-2` already carries the trace harness utilities needed for subsequent reruns.

Evidence Snapshot:
- Last PyTorch trace (reports/20251008T081932Z/trace_py_scaling.log) shows F_latt = -2.380134142 vs C = -2.383196653.
- ΔI_before_scaling ≈ -1968.57 (≈ -0.209% relative) propagated to the regression test.
- Current pytest selector fails with AssertionError on F_latt tolerance (≤1e-6 target) because the cache delivers the wrong lattice factor.
- C trace baseline remains in reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log; do not overwrite.

Execution Steps (after Do Now if time permits):
1. Append command, exit status, and a short failure summary (e.g., "F_latt rel error 3.06e-03") to "$RUN_DIR/commands.txt".
2. Record environment metadata into "$RUN_DIR/env.json" (python -V, torch.__version__, git rev-parse HEAD, CUDA availability).
3. Generate checksums via `sha256sum "$RUN_DIR"/* > "$RUN_DIR/sha256.txt"`.
4. Summarise the failure deltas in reports/2025-10-cli-flags/phase_l/scaling_validation/lattice_hypotheses.md (new subsection dated with the timestamp).
5. Update docs/fix_plan.md Attempts with the timestamp, command, observed ΔF_latt/ΔI_before_scaling, and RUN_DIR pointer.
6. Flip M2e to [D] in plans/active/cli-noise-pix0/plan.md once the artifacts exist (note the timestamp alongside).

Implementation Guardrails:
- Evidence loop only — no simulator/crystal code edits until Option 1 implementation loop (M2g).
- Keep RUN_DIR unique per execution (UTC timestamp) and nested under phase_l/scaling_validation/.
- Preserve Protected Assets (docs/index.md references). Do not rename or delete any listed file.
- Ensure every torch invocation sets KMP_DUPLICATE_LIB_OK=TRUE.
- Maintain ASCII-only edits when updating markdown docs.
- If pytest exits early (collection failure), capture the trace and mark the attempt as blocked per fix plan protocol.
- Leave existing reports untouched; add new directories rather than replacing older timestamps.

Reporting Checklist:
- RUN_DIR contains: pytest.log, commands.txt (with command, exit code, failure summary), env.json, sha256.txt.
- commands.txt lists both test command(s) and any supplementary diagnostics (e.g., collect-only run).
- env.json includes python/torch versions, git SHA, device availability, and whether CUDA was used (parity evidence can remain CPU-only).
- lattice_hypotheses.md gains a "2025-12-07 parity test failure" entry referencing RUN_DIR.
- docs/fix_plan.md attempt includes Next Action status, artifact path, Δ metrics, and note that Option 1 design is ready.
- plans/active/cli-noise-pix0/plan.md M2e row updated to [D] with timestamp + RUN_DIR.

Follow-on Targets (for awareness):
- Option 1 cache (M2g) must respect tensor shape (S,F,N_mos,3) and avoid `.detach()`; future gradcheck expected on a 2×2 ROI.
- Post-fix reruns (M2i/M3) should deliver `metrics.json` first_divergence=None and a green regression test.
- Phase N nb-compare requires correlation ≥0.9995 and sum ratio 0.99–1.01; keep this in mind when storing new reports.

Pitfalls To Avoid:
- Do not discard pytest.log even if the run aborts quickly; we need the stack trace.
- Avoid manual edits to trace_harness.py or test files in this loop.
- Do not shortcut documentation updates; every artifact must be referenced in fix_plan and plan tables.
- Refrain from running the full pytest suite; stick to the mapped selector (collect-only allowed when blocked).
- Mind CPU/GPU device neutrality when documenting observations; note explicitly if CUDA unavailable.
- Keep environment capture immediate post-run to match the failure log version.
- Confirm git status before finishing; only reports and doc updates should appear.
- If you must re-run the test, create a new timestamped directory instead of reusing RUN_DIR.
- Record all commands verbatim; avoid paraphrasing in commands.txt.
- Use `tee` (already in Do Now) to ensure pytest output is preserved.

Reference Material:
- plans/active/cli-noise-pix0/plan.md:60-110 — Phase M checklist and status.
- docs/fix_plan.md:451-520 — CLI-FLAGS-003 attempts and fresh Next Actions.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md — Option 1 design spec.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py — canonical harness used in later phases.
- docs/bugs/verified_c_bugs.md:166 — Definition of the φ carryover bug being emulated.
- specs/spec-a-core.md:211 — Spec-mode φ rotation contract (baseline for tests).

Next Up (after M2e succeeds):
1. Implement the pixel-indexed cache (M2g) per Option 1 design, then validate with targeted pytest + gradcheck (M2h).
2. Rerun `trace_harness.py --roi 684 686 1039 1040 --phi-mode c-parity` to refresh metrics.json and close M2i/M3.

Diagnostic Reminders:
- Before running pytest, ensure A.mat and scaled.hkl exist at repo root; skip gracefully if missing.
- Confirm NB_C_BIN points to golden_suite_generator/nanoBragg for later comparison runs (document in commands.txt even if unused this loop).
- Note current values of Na/Nb/Nc, oversample, and phi settings in the failure summary for quick parity checks.
- Record whether torch reports any compile or dynamo warnings during the failing run; include snippets in commands.txt if present.
- If pytest output truncates due to pager, rerun with `PYTHONUNBUFFERED=1` and capture full log.

Command Snippets for Future Reference:
- C trace command (document for parity context): `NB_C_BIN=./golden_suite_generator/nanoBragg -mat A.mat -floatfile img.bin -hkl scaled.hkl -nonoise -nointerpolate -oversample 1 -exposure 1 -flux 1e18 -beamsize 1.0 -spindle_axis -1 0 0 -Xbeam 217.742295 -Ybeam 213.907080 -distance 231.274660 -lambda 0.976800 -pixel 0.172 -detpixels_x 2463 -detpixels_y 2527 -odet_vector -0.000088 0.004914 -0.999988 -sdet_vector -0.005998 -0.999970 -0.004913 -fdet_vector 0.999982 -0.005998 -0.000118 -pix0_vector_mm -216.336293 215.205512 -230.200866 -beam_vector 0.00051387949 0.0 -0.99999986 -Na 36 -Nb 47 -Nc 29 -osc 0.1 -phi 0 -phisteps 10 --trace-pixel 685 1039`.
- PyTorch trace harness (not run this loop, but keep handy): `KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --phi-mode c-parity --dtype float64`.
- Gradcheck harness placeholder for later loops: `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c --device cuda --dtype float32` (guard with torch.cuda.is_available()).

Log Formatting Expectations:
- Begin commands.txt with ISO timestamp and command line, e.g., `[2025-12-07T18:42:05Z] pytest ...`.
- Capture failure excerpt lines (AssertionError message, expected vs actual) below the command in commands.txt for quick scanning.
- env.json should be valid JSON with keys {"python", "torch", "cuda_available", "git_sha", "platform"}.
- For lattice_hypotheses.md entry, include bullet list: command, F_latt_py, F_latt_c, relative error, I_before delta, notes.
- When updating docs/fix_plan.md, prefix the attempt with `Attempt #[next] (ralph loop ...) — Result: evidence captured (M2e)` to maintain chronology.

Cross-checks & Sign-off:
- After documentation updates, re-run `pytest --collect-only -q tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c` and attach output to RUN_DIR/collect.log if not already captured.
- Verify git status shows only reports/..., docs/fix_plan.md, plans/active/cli-noise-pix0/plan.md modified when you exit (no stray files).
- Confirm sha256.txt lists exactly the files in RUN_DIR; regenerate if new files added.
- Ping supervisor in docs/fix_plan.md attempt if failure mode differs from expected (e.g., missing data file rather than tolerance mismatch).
- Leave a brief "Next steps" note inside lattice_hypotheses.md pointing to Option 1 implementation tasks (M2g–M2h).

Support Files to Revisit Before Option 1:
- src/nanobrag_torch/models/crystal.py:1084 (current carryover cache) — read but do not modify this loop; note lines for future work.
- src/nanobrag_torch/simulator.py:780-860 — understand where φ vectors are consumed; add notes to commands.txt if any surprising behavior observed during failure run.
- tests/test_cli_scaling_parity.py — verify expected constants remain aligned with c_trace_scaling.log; update docs if drift observed.
- reports/2025-10-cli-flags/phase_l/scaling_validation/phi_carryover_diagnosis.md — append a "Pre-fix failure log" section referencing RUN_DIR.

Final Checks Before Handoff:
- Ensure input.md remains untouched (do not edit this file during the engineer loop).
- Confirm the RUN_DIR path is mirrored in both docs/fix_plan.md and plan.md so future loops can trace the evidence quickly.
- Add a short bullet in commands.txt noting whether the failure occurs on CPU float64 (expected) and if any other device was attempted.
- Cleanly exit virtualenvs/sessions so environment metadata reflects the test execution context.

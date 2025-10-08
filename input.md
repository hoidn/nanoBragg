Summary: Diagnose and rebuild the φ=0 carryover pathway so PyTorch reproduces C’s F_latt and I_before_scaling on the supervisor command.
Mode: Parity
Focus: [CLI-FLAGS-003] Phase M2 — Fix φ=0 carryover parity
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/carryover_probe/, reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/metrics.json, reports/2025-10-cli-flags/phase_l/scaling_validation/<ts>/implementation_notes.md
Do Now: CLI-FLAGS-003 Phase M2 — export RUN_DIR="reports/2025-10-cli-flags/phase_l/scaling_validation/$(date -u +%Y%m%dT%H%M%SZ)/carryover_probe" && mkdir -p "$RUN_DIR" && KMP_DUPLICATE_LIB_OK=TRUE python reports/2025-10-cli-flags/phase_l/scaling_audit/trace_harness.py --pixel 685 1039 --out "$RUN_DIR/trace_py_scaling.log" --config supervisor --dtype float64 --phi-mode c-parity --emit-rot-stars
If Blocked: Capture the failing shell command plus stderr into $RUN_DIR/commands.txt, run pytest --collect-only -q tests/test_cli_scaling_parity.py to document discovery status, then log the blockage + paths in docs/fix_plan.md Attempts and wait for further direction.

Context Notes:
Line-by-line parity still breaks at φ=0 despite the new cache introduced in commit 3269f6d. TRACE_PY_ROTSTAR proves the cache never fires; we must demonstrate this empirically, redesign the storage scheme, and rerun the scaling audit before Phase M3 can start. Keep spec mode untouched and preserve the documented tolerances (spec ≤1e-6, c-parity ≤5e-5).

Baseline Metrics:
F_latt (Py) = -2.38013414214076, F_latt (C) = -2.38319665302824.
I_before_scaling (Py) = 941686.235979802, I_before_scaling (C) = 943654.80923755.
ΔI_before_scaling = -1968.573257748, relative error ≈ -0.209%. These values come from reports/.../20251008T081932Z and must move to ≤1e-6 after the fix.

Carryover Expectations:
C’s OpenMP loop keeps ap/bp/cp in firstprivate memory, so φ=0 inherits the previous pixel’s φ-final vectors. The PyTorch implementation processes whole pixel slabs at once, so we need a vectorized analogue that does not rely on sequential loops yet still reproduces the stale-state behavior when c-parity mode is active.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:59-86 — Phase M2 checklist is reopened; cache redesign + evidence are prerequisites for VG-2.
- docs/fix_plan.md:451-520 — Next Actions emphasise consecutive-pixel probes, implementation fix, metric reruns, and parity shim documentation.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T081932Z/trace_py_scaling.log — Latest failing trace (124 lines) shows TRACE_PY_ROTSTAR with fresh vectors.
- tests/test_cli_scaling_parity.py:1-184 — Regression test capturing the C reference; keep it failing until parity is restored.
- docs/bugs/verified_c_bugs.md:166-204 — Defines the C carryover defect; spec documents must remain unaffected.

Failure Snapshot:
Trace harness currently runs a single pixel per invocation, so cached tensors are written but never reused. Even if reuse occurred, the `.detach().clone()` calls would sever gradients, violating architecture rules and making the test unsuitable for future optimisation work.

How-To Map:
- Baseline reproduction: run the Do Now harness command, archive logs, and copy the failing metrics into implementation_notes.md.
- Consecutive-pixel proof: modify trace_harness.py (temporary branch) or spin up a short script that sets debug_config for both pixels within one Simulator.run() call; store results under reports/.../<ts>/carryover_probe_pair/ with SHA256 manifests.
- Cache redesign: refactor Crystal.get_rotated_real_vectors to buffer φ-final tensors keyed by pixel index (or equivalent ordering) without `.detach()` or in-place slice writes; ensure device/dtype neutrality.
- Verification: rerun trace_harness.py (float64 CPU, optional CUDA) and scripts/validation/compare_scaling_traces.py so metrics.json reports first_divergence=None; attach SHA logs.
- Regression test: execute KMP_DUPLICATE_LIB_OK=TRUE pytest -q tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c — expect failure pre-fix, success post-fix; archive stdout under reports/.../<ts>/pytest_cli_scaling_parity.log.

Implementation Guardrails:
Keep spec mode intact while editing c-parity logic. Retain vectorization across φ, mosaic, and oversample axes. Maintain the existing debug toggles (_enable_trace, emit-rot-stars) and document any temporary instrumentation in implementation_notes.md so they can be removed cleanly.

Pitfalls To Avoid:
- Detaching tensors or writing to slices in place when replaying cached vectors (breaks gradients and violates architectural contracts).
- Introducing per-pixel Python loops; the design must stay fully batched.
- Hard-coding device conversions; keep cache tensors on the caller’s device/dtype.
- Forgetting to clear cache state between runs (Simulator.run() currently does this — keep or improve it).
- Overwriting canonical artifacts; create a new timestamp folder for every probe and record SHA256 checksums.
- Leaving temporary TRACE_PY prints in production paths; gate them behind debug_config and remove after use.

Trace & Metrics Workflow:
1. mkdir -p "$RUN_DIR" (already in Do Now) and run trace_harness.py with --emit-rot-stars.
2. python scripts/validation/compare_scaling_traces.py --c reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log --py "$RUN_DIR/trace_py_scaling.log" --out "$RUN_DIR/../scaling_validation_summary.md".
3. Inspect metrics.json and confirm first_divergence is None; if not, iterate until it is.
4. Copy the metrics snapshot and run metadata into docs/fix_plan.md Attempts.

Testing Cadence:
Before the fix: allow tests/test_cli_scaling_parity.py to fail (document the failure). After the fix: rerun the same selector until it passes, then, if code changed broadly, schedule an end-of-loop targeted subset (no full suite unless necessary). Keep all runs CPU float64 first; add CUDA coverage once results are green.

Pointers:
- src/nanobrag_torch/models/crystal.py:123-145 — Cache initialisation/clear.
- src/nanobrag_torch/models/crystal.py:1243-1305 — φ=0 substitution logic that needs redesign.
- src/nanobrag_torch/simulator.py:758-764 — Cache reset at run start.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T081932Z/summary.md — Evidence write-up for failing attempt.
- scripts/validation/compare_scaling_traces.py:1-210 — Tool used to regenerate metrics.json + summary.

Documentation Expectations:
Update docs/fix_plan.md with Attempt details (command lines, metrics, SHA paths) after each probe. Mirror plan changes in plans/active/cli-noise-pix0/plan.md (M2 rows) when tasks close. Ensure summary.md files include command history, git SHA, pixel coordinates, and whether TRACE_PY_ROTSTAR indicates cache hits.

Next Up: Phase M3 — rerun scaling comparison, regenerate metrics.json, and begin nb-compare ROI parity once ΔI_before_scaling ≤ 1e-6 and the new regression test passes.

Temporary Instrumentation Plan:
If you need extra logging, add TRACE_PY_CACHE_HIT / TRACE_PY_CACHE_MISS lines guarded by debug_config flags. Capture the diff output in implementation_notes.md and remove the instrumentation before pushing. Note any transient flags in docs/fix_plan.md so reviewers see why they existed.

Validation Deliverables:
Produce three artefacts per iteration: (1) trace_py_scaling.log with ROTSTAR (and eventual cache-hit markers), (2) scaling_validation_summary.md + metrics.json showing first_divergence, (3) pytest log for the scaling parity test. Each artefact must have a companion SHA256 manifest.

Reporting Checklist:
After each run, append to docs/fix_plan.md Attempt log: commands, git SHA, ΔF_latt, ΔI_before_scaling, cache-hit observations, and pointer to new timestamp directory. Reflect any status changes in plans/active/cli-noise-pix0/plan.md (flip M2 rows to [D] once complete, otherwise annotate partial progress).

Fallback Steps:
If cache redesign appears blocked, document hypotheses (e.g., vectorization order, per-pixel ordering) in implementation_notes.md and ping supervisor with concrete deltas. Do not downgrade tolerances; the target remains ≤1e-6 for VG-2.

Final Verification Path:
Once parity holds, rerun nb-compare with the supervisor ROI per plan Phase N, record correlation ≥0.9995, intensity ratio 0.99–1.01, and archive PNGs + JSON. Only then advance to the supervisor command rerun (Phase O) and close CLI-FLAGS-003.

Timeline Reminder:
Phase M2 evidence and implementation must complete before vectorization/plans goals resume. Expect to spend the loop on cache redesign; do not switch focus until metrics.json is green.

Success Criteria:
- TRACE_PY logs show cache hits at φ=0 for the second pixel when c-parity mode is active.
- compare_scaling_traces.py reports first_divergence=None with ≤1e-6 relative deltas across all factors.
- tests/test_cli_scaling_parity.py passes on CPU float64 and (optionally) CUDA float32 without altering tolerances.

Communication Notes:
Document any new hypotheses or blockers in implementation_notes.md and reference them in docs/fix_plan.md. If gradients fail after redesign, capture the gradcheck failure message verbatim and include tensor shapes to speed up triage.

Review Hooks:
Once ready for review, highlight the new cache strategy in a short summary (where state stored, how gradients preserved) and point reviewers to amended specs/tests. Mention whether additional unit tests are needed for cache hits (e.g., synthetic two-pixel scenario) before merging.

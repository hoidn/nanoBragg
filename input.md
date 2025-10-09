Summary: Capture new profiler evidence for VECTOR-GAPS-002 Phase B1 so we can rank residual Python loops with up-to-date correlation metrics.
Mode: Perf
Focus: [VECTOR-GAPS-002] Vectorization gap audit
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/, reports/2026-01-vectorization-gap/phase_b/<STAMP>/summary.md, reports/2026-01-vectorization-gap/phase_b/<STAMP>/commands.txt, reports/2026-01-vectorization-gap/phase_b/<STAMP>/env.json, reports/2026-01-vectorization-gap/phase_b/<STAMP>/benchmark_results.json, reports/2026-01-vectorization-gap/phase_b/<STAMP>/pytest_collect.log, reports/2026-01-vectorization-gap/phase_b/<STAMP>/correlation.txt
Do Now: [VECTOR-GAPS-002] Vectorization gap audit (Phase B1) — run `pytest --collect-only -q` then `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --keep-artifacts --iterations 1 --outdir reports/2026-01-vectorization-gap/phase_b/$(date -u +%Y%m%dT%H%M%SZ)/profile/`

Context Notes:
The vectorization backlog is now fully unblocked after SOURCE-WEIGHT-001 Phase D and VECTOR-TRICUBIC-001 Phase H closed parity gaps; this profiler run replaces the stale 20251009 capture with correlation 0.721. Use a fresh UTC timestamp for the new evidence bundle so the reports ledger remains chronological.
Plan to populate the summary with inclusive time percentages for each major autograd kernel, the measured correlation between PyTorch and C outputs (≥0.99 expected), and the warm/cold runtime values so Phase B2 can reason about prioritisation thresholds.
Record all commands (including directory creation) in commands.txt and mirror the environment snapshot workflow used during Phase A to keep artifacts consistent.

Execution Outline:
Step 1 — Prepare directories: create the UTC-stamped folder under `reports/2026-01-vectorization-gap/phase_b/` and add subfolders `profile/` and `notes/` before running anything.
Step 2 — Capture git context: record `git rev-parse HEAD`, `git status --short`, and `uname -a` into commands.txt before invoking tests.
Step 3 — Run `pytest --collect-only -q` with output redirected to the new `pytest_collect.log`; confirm exit code 0 and note the collected test count in summary.md.
Step 4 — Execute the profiler command with `KMP_DUPLICATE_LIB_OK=TRUE`; retain the stdout/stderr stream (tee into `profile/run.log`) for future investigation.
Step 5 — After the run, copy `trace.json`, `benchmark_results.json`, and any auxiliary output into `profile/`; compute correlation metrics (see How-To) and store them in correlation.txt plus summary.md.
Step 6 — Populate env.json via `python - <<'PY'` snippet (see How-To) so device availability, torch version, and CUDA status are captured; store `torch_env.txt` if you run `python -m torch.utils.collect_env`.
Step 7 — Update docs/fix_plan.md attempts once artifacts exist; include timestamp, command line, correlation result, and outstanding hypotheses.

If Blocked: Capture stderr/stdout from the failing command, keep any partial `profile/` artifacts, write blocking.md summarising the failure mode (device mismatch, missing CUDA, low correlation, etc.), and append an Attempt note in docs/fix_plan.md with the same detail before halting work.

Priorities & Rationale:
- plans/active/vectorization-gap-audit.md Phase B1 row documents that the profiler capture is the next gate; completing it enables B2 correlation analysis and backlog creation.
- docs/fix_plan.md:3763-3810 keeps VECTOR-GAPS-002 at High priority with Phase B tasks outstanding; logging Attempt #3 maintains the ledger expectations.
- reports/2025-10-vectorization/phase_h/20251009T092228Z/summary.md shows CUDA parity; the CPU profiler evidence will let us compare GPU/CPU hotspots when Phase B2 begins.
- docs/development/testing_strategy.md#14 emphasises device/dtype neutrality; running the profiler with explicit env settings prevents hidden CPU<->CUDA transfers.
- plans/active/perf-pytorch-compile-refactor/plan.md (Phase P3) depends on these metrics to target kernel fusion; delivering them keeps PERF-PYTORCH-004 on track.
- specs/spec-a-parallel.md §2.3 expects correlation ≥0.999 for validation traces; we need to confirm the profiler command respects current parity levels.

How-To Map:
- Always prefix simulator runs with `KMP_DUPLICATE_LIB_OK=TRUE`; use `env KMP_DUPLICATE_LIB_OK=TRUE` notation when scripting to avoid environment drift.
- Create the directory skeleton via `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `mkdir -p reports/2026-01-vectorization-gap/phase_b/$STAMP/{profile,notes}`; record `$STAMP` in commands.txt for traceability.
- Push pytest output into `reports/2026-01-vectorization-gap/phase_b/$STAMP/pytest_collect.log` using `pytest --collect-only -q | tee ...` so we retain both console output and log file.
- Execute the profiler command exactly as in Do Now; redirect stdout with `tee reports/.../profile/run.log` to maintain a durable log of iteration timings and correlation printouts.
- After the profiler finishes, compute correlation using the existing helper: `python scripts/validation/compare_scaling_traces.py --from-benchmark reports/.../profile/benchmark_results.json --out reports/.../correlation.txt` (adjust if helper requires extra flags); if helper is unavailable, write a short Python snippet to extract metrics from benchmark_results.json and document the approach in summary.md.
- Generate env.json with `python - <<'PY'
import json, torch, platform, os
info = {
    "python": platform.python_version(),
    "pytorch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "device_count": torch.cuda.device_count(),
    "git_sha": os.popen('git rev-parse HEAD').read().strip(),
}
print(json.dumps(info, indent=2))
PY > reports/2026-01-vectorization-gap/phase_b/$STAMP/env.json`.
- Store `torch_env.txt` via `python -m torch.utils.collect_env > reports/.../torch_env.txt` if the module is available; this helps Phase B2 reason about driver/toolkit versions.
- Summarise findings in summary.md with sections: command list, timings (cold/warm), correlation, top-5 kernels by inclusive time, follow-up hypotheses, link to relevant spec sections.

Pitfalls To Avoid:
- Do not reuse or append to the 20251009 profiler bundle; we need a pristine capture reflecting post-fix behaviour.
- Avoid adding new Python loops or instrumentation to production code while profiling; this loop is evidence-only by mandate.
- Ensure profiler output remains on CPU; forcing CUDA mid-run will distort inclusive time measurements and break comparability.
- Keep `--iterations 1`; raising iterations increases run time and skews warm/cold metrics captured in the baseline.
- Do not omit `--keep-artifacts`; losing trace.json prevents the callgraph analysis required in Phase B2.
- Protect disk space: delete accidental large dumps (>500MB) from scratch directories, but never touch protected assets listed in docs/index.md.
- Skip full pytest runs unless the profiler command fails due to import errors; the collect-only pass is sufficient for this evidence loop.
- When writing summary.md, avoid deferring conclusions—document whether correlation met ≥0.99 and flag any unexpected hotspots immediately.
- Double-check that the recorded timestamp folder name matches commands.txt and docs/fix_plan.md to avoid audit confusion.
- Do not leave env.json empty; Phase C design packets rely on consistent metadata.

Pointers:
- plans/active/vectorization-gap-audit.md (Phase B guidance and prerequisites)
- docs/fix_plan.md:3763-3810 ([VECTOR-GAPS-002] ledger context, expected artifacts)
- docs/development/testing_strategy.md#14 (device/dtype discipline requirements)
- reports/2025-10-vectorization/phase_h/20251009T092228Z/summary.md (latest CUDA parity metrics for comparison)
- reports/2026-01-vectorization-gap/phase_a/20251009T065238Z/summary.md (loop classification baseline to cross-reference during write-up)

Next Up: 1) Phase B2 — map profiler hotspots to the Phase A inventory and draft `hot_loops.csv` with %time and call counts. 2) Phase B3 — produce backlog.md summarising top priority loops with recommended owners and expected vectorization benefits.

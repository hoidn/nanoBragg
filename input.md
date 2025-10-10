Summary: Capture fresh 4096² profiler evidence to restart Phase C of the vectorization relaunch.
Mode: Docs
Focus: VECTOR-TRICUBIC-002 Vectorization relaunch backlog
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-gap/phase_b/<STAMP>/
Do Now: VECTOR-TRICUBIC-002 — Run the Phase C1 warm profiler capture via `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/`
If Blocked: Capture stdout/stderr to `reports/2026-01-vectorization-gap/phase_b/<STAMP>/attempts/failed_profile.log`, log the exit code, and note the failure in docs/fix_plan.md before stopping.
Priorities & Rationale:
- plans/active/vectorization.md:39 – Phase C1 is the next gate to unblock backlog work.
- docs/fix_plan.md:110 – Updated Next Actions require this profiler capture before further delegation.
- docs/development/testing_strategy.md:80 – Confirms profiling runs supplement Tier 1 parity before new vectorization edits.
- docs/architecture/pytorch_design.md:34 – Maintains vectorization guardrails while analysing hotspots.
How-To Map:
- Ensure editable install is active (`pip install -e .` already satisfied if unchanged) and export `KMP_DUPLICATE_LIB_OK=TRUE` inline with the command.
- Replace `<STAMP>` with an ISO8601 timestamp (e.g., `20260105T153000Z`) when creating the reports directory; keep all artifacts under that folder.
- Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --iterations 1 --keep-artifacts --outdir reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/` from repo root.
- After the run, record correlation metrics, torch.compile status, and profiler summary in `reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/summary.md`, then queue an Attempt update for docs/fix_plan.md.
Pitfalls To Avoid:
- Do not commit the generated `reports/` artifacts; reference them only.
- Respect vectorization guardrails—no temporary edits to simulator code to ease profiling.
- Keep device/dtype neutrality; run on CPU as requested and note CUDA status without forcing GPU transfers.
- Avoid modifying Protected Assets listed in docs/index.md during this loop.
- Do not spawn subagents without full prompts per CLAUDE.md; single-agent loop only.
- Skip full pytest runs; only the profiling command is expected here.
- Preserve existing plan states; log progress via attempts rather than changing task checkboxes.
- Maintain the Do Now focus; do not chase other fix_plan items mid-loop.
Pointers:
- docs/fix_plan.md:110
- plans/active/vectorization.md:39
- docs/development/testing_strategy.md:80
- docs/architecture/pytorch_design.md:34
Next Up: Finish Phase C2 hotspot mapping once profiler artifacts are ready.

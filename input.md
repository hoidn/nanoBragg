Summary: Capture a warm-run profiler trace so we can rank the remaining scalar loops before delegating vectorization work.
Mode: Perf
Focus: [VECTOR-GAPS-002] Vectorization gap audit
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-gap/phase_b/<STAMP>/profile/
Artifacts: reports/2026-01-vectorization-gap/phase_b/<STAMP>/commands.txt
Artifacts: reports/2026-01-vectorization-gap/phase_b/<STAMP>/summary.md
Artifacts: reports/2026-01-vectorization-gap/phase_b/<STAMP>/env.json
Artifacts: reports/2026-01-vectorization-gap/phase_b/<STAMP>/pytest_collect.log

Do Now: [VECTOR-GAPS-002] Vectorization gap audit — Phase B1 profiler capture. Run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/benchmarks/benchmark_detailed.py --sizes 4096 --device cpu --dtype float32 --profile --keep-artifacts --iterations 1 --outdir reports/2026-01-vectorization-gap/phase_b/$STAMP/profile/`.
If Blocked: If the profiler run fails or OOMs, capture the failing command/output in `commands.txt`, fall back to `--sizes 2048`, tag the attempt as blocked in docs/fix_plan.md, and pause for guidance.

Priorities & Rationale:
- `plans/active/vectorization-gap-audit.md:34` — Phase B1 requires the warm-run profiler trace before any backlog work can start.
- `docs/fix_plan.md:3740` — Next Actions now depend on capturing Phase B1 evidence and storing artifacts under the new stamp.
- `reports/2026-01-vectorization-gap/phase_a/20251009T065238Z/analysis.md:9` — Classification identified the todo/uncertain loops this profiler run must measure.
- `docs/development/testing_strategy.md:78` — Performance runs must log commands/env for reproducibility and future regression checks.
- `docs/development/pytorch_runtime_checklist.md:1` — Reaffirm device/dtype neutrality while profiling; capture any warnings for follow-up.

How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and create `reports/2026-01-vectorization-gap/phase_b/$STAMP` before running commands.
- Execute the profiler command with `KMP_DUPLICATE_LIB_OK=TRUE` and `--keep-artifacts`; expect trace files under the `profile/` subfolder.
- After the run, record the exact command, start/end timestamps, exit code, and `git rev-parse HEAD` in `commands.txt`.
- Dump environment info by running `python - <<'PY'` blocks that emit JSON (`{"python": ..., "torch": ..., "cuda_available": ...}`) and redirect to `env.json`.
- Create `summary.md` outlining top inclusive-time ops, preliminary mapping to the Phase A inventory, and any surprises.
- Run `pytest --collect-only -q | tee reports/2026-01-vectorization-gap/phase_b/$STAMP/pytest_collect.log` once artifacts are staged.
- Update `docs/fix_plan.md` Attempt history with profiler metrics (e.g., top loop timings) and link to the new stamp; mark Phase B1 `[P]` in `plans/active/vectorization-gap-audit.md`.

Pitfalls To Avoid:
- Do not downscale detector size unless the 4096² run truly fails; we need an apples-to-apples warm benchmark.
- Avoid editing production code; this loop is evidence-only.
- Keep tensor device placement warnings; note them instead of suppressing.
- Do not move or rename prior Phase A artifacts; reference them in summary when comparing hotspots.
- Capture all commands in `commands.txt`; missing entries will block sign-off.
- Ensure profiler output remains under the timestamped directory; no stray files in repo root.
- Skip GPU profiling until the device-placement blocker is cleared; stay on CPU for this attempt.
- Verify the profiler exited 0 before proceeding; rerun or document failure otherwise.
- Maintain ASCII-only content in summary and command logs.
- Remember to refresh fix_plan and the Phase B status after recording metrics.

Pointers:
- `plans/active/vectorization-gap-audit.md:27` — Full Phase B goals and deliverables.
- `docs/fix_plan.md:3735` — Updated ledger expectations after Phase A completion.
- `reports/2025-10-vectorization/gaps/20251009T061928Z/analysis.md:1` — Example performance analysis narrative format to follow.
- `scripts/benchmarks/benchmark_detailed.py` — Harness the profiler command wraps; review if options change.
- `docs/development/testing_strategy.md:95` — Guidance on logging benchmarks and storing artifacts.

Next Up (optional): Phase B2 loop↔trace correlation once profiler metrics are captured.

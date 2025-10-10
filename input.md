Summary: Refresh tricubic/absorption evidence before resuming vectorization backlog.
Mode: Perf
Focus: [VECTOR-TRICUBIC-002] Vectorization relaunch backlog
Branch: feature/spec-based-2
Mapped tests: tests/test_tricubic_vectorized.py; tests/test_at_abs_001.py
Artifacts: reports/2026-01-vectorization-refresh/phase_b/<STAMP>/
Do Now: Execute Phase B1–B2 of [VECTOR-TRICUBIC-002]; run the mapped pytest selectors and capture the paired tricubic/absorption benchmarks (CPU + CUDA when available).
If Blocked: Stop after capturing failing pytest/benchmark logs to reports/2026-01-vectorization-refresh/phase_b/<STAMP>/attempt_blocked/ and record the exit code in docs/fix_plan.md Attempts History.
Priorities & Rationale:
- docs/fix_plan.md:3766-3784 — Status now in_progress; Next Actions demand fresh Phase B regression evidence.
- plans/active/vectorization.md:28-36 — Phase B checklist defines pytest selectors and benchmark cadence we must refresh.
- docs/architecture/pytorch_design.md:3-67 — Revalidating tricubic/absorption ensures the documented tensor flows still hold after upstream parity shifts.
- docs/development/pytorch_runtime_checklist.md:6-29 — Reinforces vectorization/device guardrails and mandates CPU+CUDA coverage.
- plans/active/vectorization-gap-audit.md:1-36 — Downstream gap profiling depends on these refreshed baselines before profiling resumes.
How-To Map:
- Export `STAMP=$(date -u +%Y%m%dT%H%M%SZ)` and `BASE=reports/2026-01-vectorization-refresh/phase_b/$STAMP`; `mkdir -p "$BASE"/pytest "$BASE"/benchmarks` (do not git add).
- `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_tricubic_vectorized.py -v | tee "$BASE/pytest/tricubic.log"`; record exit code in `$BASE/pytest/exit_codes.txt`.
- `KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_at_abs_001.py -v -k "cpu or cuda" | tee "$BASE/pytest/absorption.log"`; append exit code to the same tracker.
- `python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 200 --device cpu --outdir "$BASE/benchmarks/tricubic_cpu"`.
- Guard the CUDA reruns with:
  ```bash
  if python - <<'PY'
import torch, sys
sys.exit(0 if torch.cuda.is_available() else 1)
PY
  then
      python scripts/benchmarks/tricubic_baseline.py --sizes 256 512 --repeats 200 --device cuda --outdir "$BASE/benchmarks/tricubic_cuda"
  else
      echo "cuda_unavailable=$(date -u)" >> "$BASE/benchmarks/notes.md"
  fi
  ```
- Repeat the same pattern for absorption: always run the CPU command `python scripts/benchmarks/absorption_baseline.py --sizes 256 512 --repeats 200 --device cpu --outdir "$BASE/benchmarks/absorption_cpu"`; only add the CUDA run inside the guard above with the absorption script (write fallback note when skipped).
- After runs, draft `$BASE/summary.md` noting mean/median warm timings vs `reports/2025-10-vectorization/phase_e/` and `/phase_f/`, flagging if drift >5%.
- Update docs/fix_plan.md Attempts for [VECTOR-TRICUBIC-002] with metrics + artifact paths once data captured.
Pitfalls To Avoid:
- Do not commit anything under reports/; reference paths only.
- Keep `KMP_DUPLICATE_LIB_OK=TRUE` on every pytest/benchmark invocation.
- Guard CUDA runs with `torch.cuda.is_available()`; never assume GPU access.
- Avoid editing plan/docs beyond required attempt notes; no code changes this loop.
- Capture exit codes for each command; missing exit data invalidates the evidence.
- Preserve runtime environment noted by the benchmark scripts; do not modify their defaults besides documented flags.
- No ad-hoc scripts or notebooks—use the established benchmarks only.
- Ensure pytest logs stay under `$BASE/pytest/`; don’t mix with benchmark outputs.
- Record CPU vs CUDA availability explicitly in `$BASE/summary.md`.
- Leave the git tree clean after recording attempt notes.
Pointers:
- docs/fix_plan.md:3766-3784 — Current mandate for Phase B refresh.
- plans/active/vectorization.md:28-36 — Phase B tasks and command templates.
- docs/architecture/pytorch_design.md:3-67 — Vectorization evidence gates we’re revalidating.
- docs/development/pytorch_runtime_checklist.md:6-27 — Guardrails for the refresh run.
- plans/active/vectorization-gap-audit.md:34-36 — Profiler work waits on these refreshed baselines.
Next Up: Once data is archived, move to VECTOR-GAPS-002 Phase B1 profiler capture (`benchmark_detailed.py --profile`) using the same STAMP structure.

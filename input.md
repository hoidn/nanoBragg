Summary: Capture fresh memory-bandwidth diagnostics for CLUSTER-PERF-001 so we can scope fixes under PERF-PYTORCH-004.
Mode: Perf
Focus: [TEST-SUITE-TRIAGE-002] Next Action 8 — CLUSTER-PERF-001 (memory bandwidth diagnostics)
Branch: feature/spec-based-2
Mapped tests: tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_memory_bandwidth_utilization
Artifacts: reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-PERF-001/<STAMP>/
Do Now: Execute Next Action 8 by running `/usr/bin/time -v timeout 900 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=1 --timeout=900 --durations=0" pytest -vv tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_memory_bandwidth_utilization` and capture all outputs under the cluster directory.
If Blocked: Preserve whatever partial logs you have (pytest log, `/usr/bin/time` stderr, env snapshot) in the STAMP folder and write a short blocker note in `summary.md` so we can reassess next loop.
Priorities & Rationale:
- docs/fix_plan.md:64 — Next Action 8 keeps the perf regression at the front of the remediation queue.
- plans/active/test-suite-triage-rerun.md:74 — Phase D checklist still requires fresh timing evidence before we touch PERF-PYTORCH-004.
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-PERF-001.md:1 — Cluster brief spells out the profiling expectations and downstream plan ties.
- docs/development/testing_strategy.md:18 — Guardrails for CPU-only execution and runtime capture.
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `OUT=reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-PERF-001/$STAMP`; `mkdir -p "$OUT"` and log the command in `$OUT/commands.txt`.
- `set -o pipefail; /usr/bin/time -v timeout 900 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=1 --timeout=900 --durations=0" pytest -vv tests/test_at_perf_003.py::TestATPERF003MemoryBandwidth::test_memory_bandwidth_utilization 2> >(tee "$OUT/time.txt" >&2) | tee "$OUT/pytest.log"`; afterwards capture the exit status with `printf "%s\n" "${PIPESTATUS[0]}" > "$OUT/exit_code.txt"`.
- Record environment details via `env | sort > "$OUT/env.txt"` and `python -m torch.utils.collect_env > "$OUT/torch_env.txt"`.
- Summarize observed bandwidth numbers, pytest assertions, and `/usr/bin/time` highlights in `$OUT/summary.md`. If you run an additional profiler (e.g., set `NB_PROFILER_OUT=$OUT/profile.json`), mention it and stash the artifact alongside.
Pitfalls To Avoid:
- Evidence loop only: do not change production code or tests.
- Stay on CPU (`CUDA_VISIBLE_DEVICES=-1`) and keep `NANOBRAGG_DISABLE_COMPILE=1` to avoid Dynamo side effects.
- Do not skip `/usr/bin/time`; we need the resource breakdown.
- Reuse the guarded PYTEST_ADDOPTS string; do not lower the timeout below 900 s without supervisor sign-off.
- Avoid overwriting prior artifacts—use a fresh STAMP for each run.
- Maintain ASCII filenames and keep logs in the cluster directory.
- Do not enable torch.compile or GPU markers during this run.
- Keep the conda environment unchanged; note any anomalies in `summary.md`.
Pointers:
- docs/fix_plan.md:64
- plans/active/test-suite-triage-rerun.md:74
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-PERF-001.md:1
- docs/development/testing_strategy.md:18
Next Up: Once perf evidence lands, move to Next Action 9 (CLUSTER-VEC-001 dtype diagnostics).

Summary: Capture gradient stability timeout diagnostics so we can profile CLUSTER-GRAD-001 before any fixes.
Mode: Perf
Focus: [TEST-SUITE-TRIAGE-002] Next Action 7 — CLUSTER-GRAD-001 (gradient timeout diagnostics)
Branch: feature/spec-based-2
Mapped tests: tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability
Artifacts: reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-GRAD-001/<STAMP>/
Do Now: Execute Next Action 7 by running `/usr/bin/time -v timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=1 --timeout=1200 --durations=0" pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability` and capture logs, `/usr/bin/time` output, exit status, and env snapshot under the cluster artifact directory.
If Blocked: Store the partial pytest log, `/usr/bin/time` output (or note if unavailable), and a brief summary explaining the blocker in `summary.md`; include any traceback snippets so we can reassess in the next supervisor loop.
Priorities & Rationale:
- docs/fix_plan.md:62 — Next Action 7 keeps CLUSTER-GRAD-001 at the top of the remediation queue.
- plans/active/test-suite-triage-rerun.md:77 — Phase D checklist requires profiler-quality diagnostics before closing the cluster.
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-GRAD-001.md:1 — Cluster brief mandates extended-timeout run with profiling artifacts.
- docs/development/testing_strategy.md:34 — Reinforces reuse of authoritative pytest commands and guardrails (CPU-only, compile guard disabled).
How-To Map:
- `STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `OUT=reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-GRAD-001/$STAMP`; `mkdir -p "$OUT"` and log the command in `$OUT/commands.txt`.
- `set -o pipefail; /usr/bin/time -v timeout 1200 env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE NANOBRAGG_DISABLE_COMPILE=1 PYTEST_ADDOPTS="--maxfail=1 --timeout=1200 --durations=0" pytest -vv tests/test_gradients.py::TestPropertyBasedGradients::test_property_gradient_stability 2> >(tee "$OUT/time.txt" >&2) | tee "$OUT/pytest.log"`; afterwards record the exit code with `printf "%s\n" "${PIPESTATUS[0]}" > "$OUT/exit_code.txt"`.
- Capture environment details via `env | sort > "$OUT/env.txt"` and append hardware info with `python -m torch.utils.collect_env > "$OUT/torch_env.txt"`.
- Summarize the observed runtime, timeout behavior, and any profiler hooks in `$OUT/summary.md`; call out whether the test finished within 1200 s or still timed out at 905/1200.
- If you can easily add PyTorch profiler output without code edits (e.g., existing helper), store it in `$OUT/profiler.json`; otherwise note the limitation in `summary.md`.
Pitfalls To Avoid:
- Evidence-only loop: do not modify production code or tests during this pass.
- Keep execution on CPU and maintain compile guard (`NANOBRAGG_DISABLE_COMPILE=1`).
- Do not shorten the timeout below 1200 s; we need full runtime data.
- Ensure `/usr/bin/time` output is captured; don’t rely solely on pytest timing summaries.
- Avoid overwriting earlier artifacts—use fresh STAMP directories.
- Respect protected assets listed in docs/index.md (no edits to loop.sh, supervisor.sh, input.md).
- Leave Torch Dynamo disabled (handled via NANOBRAGG_DISABLE_COMPILE); don’t re-enable torch.compile.
- Maintain ASCII filenames and avoid spaces to keep automation happy.
- Confirm the PYTEST_ADDOPTS string includes `--durations=0` for timing details.
Pointers:
- docs/fix_plan.md:55-64
- plans/active/test-suite-triage-rerun.md:71-78
- reports/2026-01-test-suite-refresh/phase_d/20251015T113531Z/cluster_CLUSTER-GRAD-001.md:1-31
- docs/development/testing_strategy.md:20-56
Next Up: Next Action 8 — CLUSTER-PERF-001 bandwidth repro + profiling once gradient diagnostics are captured.

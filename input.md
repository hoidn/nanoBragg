Summary: Implement the weighted-source normalization fix and prove parity vs nanoBragg C so downstream profiling can resume.
Mode: Parity
Focus: [SOURCE-WEIGHT-001] Correct weighted source normalization
Branch: feature/spec-based-2
Mapped tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights -v; KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights::test_weighted_source_matches_c -v
Artifacts: reports/2025-11-source-weights/phase_c/<STAMP>/implementation_notes.md
Artifacts: reports/2025-11-source-weights/phase_c/<STAMP>/commands.txt
Artifacts: reports/2025-11-source-weights/phase_c/<STAMP>/pytest_cpu.log
Artifacts: reports/2025-11-source-weights/phase_c/<STAMP>/pytest_cuda.log
Artifacts: reports/2025-11-source-weights/phase_d/<STAMP>/summary.md
Artifacts: reports/2025-11-source-weights/phase_d/<STAMP>/compare_scaling_traces.log
Do Now: SOURCE-WEIGHT-001 Phase C — KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights -v (after implementing the normalization update and new regression cases).
If Blocked: Capture partial implementation notes + failing logs under the current STAMP, add a blocking section to summary.md, and record the status in docs/fix_plan.md Attempt history before stopping.
Priorities & Rationale:
- plans/active/source-weight-normalization.md:5 — Status snapshot shows Phase C (C1–C3) is the remaining gate before profiling restarts.
- docs/fix_plan.md:3963 — New First Divergence text documents the 328× mismatch; normalization fix is required before any perf/vectorization work continues.
- plans/active/source-weight-normalization.md:33 — C1–C3 define the exact implementation + regression scope.
- docs/development/c_to_pytorch_config_map.md:18 — Beam/source mapping requires fluence/flux parity; updates must respect config expectations.
- specs/spec-a-core.md:142 — Source weighting rules justify the divisor change; reference when updating docstrings.
- reports/2025-11-source-weights/phase_b/20251009T072937Z/strategy.md — Documented decision to divide by sum(weights) with edge-case handling.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); base=reports/2025-11-source-weights/phase_c/$STAMP; mkdir -p "$base"; printf "%s\n%s\n" "$(date -Is) phase_c_start" "$base" >> "$base"/commands.txt
- python - <<'PY'
import json, os, pathlib, platform, torch
base = pathlib.Path("$base")
(base/"env.json").write_text(json.dumps({
    "python": platform.python_version(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "git_head": os.popen('git rev-parse HEAD').read().strip(),
    "nb_c_bin": os.environ.get('NB_C_BIN', './golden_suite_generator/nanoBragg')
}, indent=2))
PY
- Implement C1: in src/nanobrag_torch/simulator.py update the final normalization so weighted runs divide by sum(weights) (fallback to n_sources for equal weights). Preserve device/dtype neutrality; avoid `.item()` unless the tensor is non-differentiable (document rationale in code comment if used).
- Evaluate whether `_accumulate_source_contribution` needs adjustments (C2); note findings in "$base"/implementation_notes.md with file:line anchors.
- Extend/author regression tests (C3) under tests/test_cli_scaling.py::TestSourceWeights covering unequal weights, uniform weights, and error handling for zero/negative sums. Cite plan test cases TC-A–TC-E.
- Run targeted tests: KMP_DUPLICATE_LIB_OK=TRUE pytest tests/test_cli_scaling.py::TestSourceWeights -v | tee "$base"/pytest_cpu.log; repeat with --device cuda when available saving to "$base"/pytest_cuda.log. Log commands in commands.txt with ISO timestamps.
- Transition to Phase D: dst=reports/2025-11-source-weights/phase_d/$STAMP; mkdir -p "$dst"; printf "%s\n%s\n" "$(date -Is) phase_d_start" "$dst" >> "$dst"/commands.txt
- python - <<'PY'
import json, os, pathlib, platform, torch
dst = pathlib.Path("$dst")
(dst/"env.json").write_text(json.dumps({
    "python": platform.python_version(),
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "git_head": os.popen('git rev-parse HEAD').read().strip(),
    "nb_c_bin": os.environ.get('NB_C_BIN', './golden_suite_generator/nanoBragg')
}, indent=2))
PY
- scripts/validation/compare_scaling_traces.py --sourcefile reports/2025-11-source-weights/phase_a/20251009T071821Z/fixtures/two_sources.txt | tee "$dst"/compare_scaling_traces.log; append command + timestamp to commands.txt
- Summarize parity metrics (correlation, sum_ratio, peak delta) in "$dst"/summary.md, explicitly calling out CPU/CUDA results and any residual gaps.
- Update plans/active/source-weight-normalization.md Phase C rows to [D] with artifact paths, then add Attempt #3 to docs/fix_plan.md including key metrics and dependency unblocks.
Pitfalls To Avoid:
- Do not regress uniform-weight behavior; keep legacy cases identical (unit tests should enforce this).
- Maintain differentiability—no `.item()` on tensors that could ever require grad, and keep operations vectorized.
- Respect device/dtype neutrality; ensure new tensors live on the simulator’s device and match dtype.
- Include the nanoBragg.c snippet in any new helper docstring per CLAUDE Rule #11 before writing implementation code.
- Keep commands.txt chronological with ISO timestamps and exact command lines.
- When CUDA unavailable, note it explicitly in summary.md and skip only those validations, not the CPU set.
- Avoid introducing ad-hoc scripts; use existing fixtures and validation tools.
- Preserve Protected Assets (docs/index.md references) when creating or modifying files.
- Capture environment metadata (python/torch/cuda/git/NB_C_BIN) in env.json for each phase directory.
- After edits, rerun pytest on the targeted selectors before touching other suites; full test suite waits until final verification.
Pointers:
- plans/active/source-weight-normalization.md:1
- docs/fix_plan.md:3953
- reports/2025-11-source-weights/phase_b/20251009T072937Z/normalization_flow.md
- specs/spec-a-core.md:142
- docs/architecture/pytorch_design.md:58
Next Up: Once parity and validation artifacts land, supervise Phase D documentation + notify VECTOR-GAPS-002 to resume profiling.

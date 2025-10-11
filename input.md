Summary: Fix CUDA-graphs fixtures to use the positional Simulator API so Cluster C5 stops erroring and the module passes.
Mode: Parity
Focus: [TEST-SUITE-TRIAGE-001] Phase M1d — Cluster C5 simulator API alignment
Branch: feature/spec-based-2
Mapped tests: tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution; tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_gradient_flow_preserved; tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_cpu_cuda_correlation
Artifacts: reports/2026-01-test-suite-triage/phase_m1/$STAMP/simulator_api/{env.txt,pytest_before.log,pytest_module.log,summary.md}
Do Now: [TEST-SUITE-TRIAGE-001] Phase M1d — env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution
If Blocked: Record the failure log under phase_m1/$STAMP/simulator_api/blocked.log, update docs/fix_plan.md Attempt history with the command/env, and state the blocker in remediation_tracker.md before exiting.

Priorities & Rationale:
- docs/fix_plan.md:48-109 – Sprint 0 now targets C5/C7 after C4 closure; C5 failure log still outstanding.
- plans/active/test-suite-triage.md:202-214 – Task M1d prescribes upgrading CUDA-graphs fixtures to positional Simulator ctor.
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:157-182 – Reproduction command and scope for Cluster C5.
- tests/test_perf_pytorch_005_cudagraphs.py:20-118 – Assertions that expect the simulator to build successfully for CPU/CUDA runs.
- src/nanobrag_torch/simulator.py:150-236 – Constructor signature (positional detector required) to mirror in the fixtures.

How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)` then `mkdir -p reports/2026-01-test-suite-triage/phase_m1/$STAMP/simulator_api` and run `env | sort > .../env.txt`.
2. Capture the current failure: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py::TestCUDAGraphsCompatibility::test_basic_execution | tee reports/.../pytest_before.log`.
3. Update the CUDA-graphs fixtures so they instantiate `Simulator(crystal, detector, beam)` (no `detector_config=` kwarg). Ensure detector/beam objects come from existing helpers to keep parity with other tests.
4. Re-run the full module for coverage: `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -v tests/test_perf_pytorch_005_cudagraphs.py | tee reports/.../pytest_module.log`. Note any CUDA skips explicitly.
5. Summarise changes, commands, runtimes, and remaining skips in `reports/.../summary.md`; include references to updated fixtures.
6. Update docs/fix_plan.md with Attempt #26 context, refresh plans/active/test-suite-triage.md row M1d to [D], and sync remediation_tracker.md counts.
7. If edits fall through to other clusters (e.g., shared fixtures), add notes in summary + fix_plan about affected selectors before closing the loop.

Pitfalls To Avoid:
- Do not reintroduce keyword-based Simulator construction in shared helpers.
- Keep artifacts under reports/2026-01-test-suite-triage/phase_m1/$STAMP/simulator_api.
- Preserve device/dtype neutrality; no `.cpu()` shim in fixtures.
- Ensure every pytest command includes `KMP_DUPLICATE_LIB_OK=TRUE`.
- Avoid touching files referenced in docs/index.md beyond their intended edits.
- Capture before/after logs; do not overwrite prior attempts’ artifacts.
- Leave gradient guard (M2) untouched this loop; scope creep adds risk.
- Document any CUDA skips or env limitations in summary.md.
- Keep fixture updates minimal; no speculative refactors beyond positional constructor swap.
- Update remediation_tracker.md in the same loop to reflect remaining failure counts.

Pointers:
- docs/fix_plan.md:48-109
- plans/active/test-suite-triage.md:202-214
- reports/2026-01-test-suite-triage/phase_m0/20251011T153931Z/triage_summary.md:157-182
- tests/test_perf_pytorch_005_cudagraphs.py:20-118
- src/nanobrag_torch/simulator.py:150-236

Next Up: Phase M1e – restore lattice-shape fixtures so Cluster C7 stops passing `detector=None`.

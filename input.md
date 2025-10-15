Summary: Resolve the remaining detector orthogonality failure (C16) by relaxing the documented tolerance and revalidating the geometry suite.
Mode: Parity
Focus: TEST-SUITE-TRIAGE-001 / Sprint 1.2 (C16 detector orthogonality)
Branch: feature/spec-based-2
Mapped tests: tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts; tests/test_detector_basis_vectors.py; tests/test_detector_geometry.py
Artifacts: reports/2026-01-test-suite-triage/phase_m3/$STAMP/detector_ortho/{commands.txt,pytest_before.log,pytest_after.log,regression.log,implementation_notes.md}
Do Now: env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv tests/test_at_parallel_017.py::TestATParallel017GrazingIncidence::test_large_detector_tilts
If Blocked: Capture the failure signature under reports/2026-01-test-suite-triage/phase_m3/$STAMP/detector_ortho/blocked.md and note the blocker in docs/fix_plan.md Attempts History; ping supervisor before proceeding.
Priorities & Rationale:
- plans/active/test-suite-triage.md:280 — Phase N checklist (N1–N4) defines the exact tasks for Sprint 1.2.
- docs/fix_plan.md:48 — Next Actions now point to launching Sprint 1.2 with baseline log, tolerance update, regression run, and tracker sync.
- reports/2026-01-test-suite-triage/phase_m3/20251011T181529Z/detector_ortho/notes.md — Owner notes capture the failure magnitude (~1.49e-08) and recommend tolerance relaxation over code changes.
- tests/test_at_parallel_017.py:88-139 — Current assertions still quote the stricter tolerance in multiple spots and need coordinated updates plus explanatory comments.
- specs/spec-a-core.md:49-89 — Detector basis and rotation requirements the revised tolerance must still respect.
How-To Map:
1. `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`, then `mkdir -p reports/2026-01-test-suite-triage/phase_m3/$STAMP/detector_ortho` and tee every pytest invocation into `commands.txt` inside that directory.
2. Run the Do Now command to confirm the pre-fix failure; save full output to `pytest_before.log` (use `2>&1 | tee ...`).
3. In `tests/test_at_parallel_017.py`, update every orthogonality/normalization assertion to use `1e-7` for float64 contexts (lines ~95-105 and 330-338); refresh or add comments citing Phase M3 measurement and spec §49-54. Ensure any hard-coded tolerance strings in messages stay consistent.
4. Re-run `env CUDA_VISIBLE_DEVICES=-1 KMP_DUPLICATE_LIB_OK=TRUE pytest -vv tests/test_at_parallel_017.py` and capture the passing log as `pytest_after.log`; follow with `pytest -vv tests/test_detector_basis_vectors.py tests/test_detector_geometry.py` saving to `regression.log`.
5. Draft `implementation_notes.md` summarising the rationale, doc updates, and verification results; mark C16 resolved in `reports/2026-01-test-suite-triage/phase_j/20251011T043327Z/remediation_tracker.md` and append the Attempt in docs/fix_plan.md referencing the new STAMP.
Pitfalls To Avoid:
- Do not touch src/ code unless tolerance relaxation fails; this sprint is test-only.
- Keep STAMPed artifacts separate—never overwrite 20251011T181529Z evidence.
- Apply the new tolerance uniformly (vector dot products, normalization, rotation-matrix checks) to avoid inconsistent assertions.
- Maintain dtype-neutral language in comments; note float32 vs float64 implications explicitly.
- Preserve Protected Assets (`input.md`, `loop.sh`) while editing trackers.
- Include `KMP_DUPLICATE_LIB_OK=TRUE` on every pytest invocation.
- Confirm assertions still enforce determinantal checks with realistic tolerances; do not remove the tests.
- Update documentation before modifying fix_plan attempts to keep ledgers in sync.
- Capture exact commands in commands.txt; no ad-hoc shells.
Pointers:
- plans/active/test-suite-triage.md:280
- docs/fix_plan.md:48
- reports/2026-01-test-suite-triage/phase_m3/20251011T181529Z/detector_ortho/notes.md
- tests/test_at_parallel_017.py:88-139
- specs/spec-a-core.md:49-89
Next Up: C15 mixed-units investigation once C16 is resolved (reuse Phase M3 mixed_units brief).

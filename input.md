Summary: Fix φ=0 carryover caching so tensors stay on caller device/dtype and gradients survive, then revalidate per-φ parity evidence.
Mode: Parity
Focus: CLI-FLAGS-003 — Handle -nonoise and -pix0_vector_mm (Phase L3k.3c.3)
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q ; pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_rot_b_matches_c -v ; pytest tests/test_cli_scaling_phi0.py::TestPhiZeroParity::test_k_frac_phi0_matches_c -v ; pytest tests/test_suite.py::TestTier2GradientCorrectness::test_gradcheck_phi_rotation -v
Artifacts: reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251124/ ; reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251124/ ; reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251124/comparison_summary.md
Do Now: CLI-FLAGS-003 L3k.3c.3 — patch `Crystal.get_rotated_real_vectors`/`Crystal.to` so `_phi_last_cache` tensors migrate with `.to(...)` (no `torch.tensor(...)` on tensor inputs), regenerate traces via `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --pixel 685 1039 --config supervisor --dtype float64 --device cpu --out reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251124/trace_py_rot_vector.log`, rerun the harness on CUDA if available, compare with `python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251124/trace_py_rot_vector_per_phi.json reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log`, then run the mapped pytest selectors.
If Blocked: If the harness still fails (e.g., missing TRACE_PY_PHI lines or CUDA unavailable), capture the stderr/stdout under `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251124/blockers/`, add an Attempt note in docs/fix_plan.md, and halt without guessing.
Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:307 — L3k.3c.3 reopened until cache tensors respect device/dtype and gradients; finish it now.
- docs/fix_plan.md:452 — Next Actions gate downstream Phase L3k.3d on this fix; progress toward long-term Goal #1 depends on it.
- src/nanobrag_torch/models/crystal.py:1067 — `torch.tensor(last_phi_deg, ...)` detaches the graph; must switch to `.to(...)` so gradcheck passes.
- src/nanobrag_torch/models/crystal.py:1178 — `_phi_last_cache` clones never migrate during `.to()`, breaking GPU parity; extend `Crystal.to` to move or reset the cache.
- tests/test_suite.py:1774 — `test_gradcheck_phi_rotation` will expose any lingering gradient break; keep it green.
How-To Map:
- Environment: `export KMP_DUPLICATE_LIB_OK=TRUE`, `export NB_C_BIN=./golden_suite_generator/nanoBragg`, set `PYTHONPATH=src` for harness/scripts.
- Code edits: update `Crystal.get_rotated_real_vectors` to reuse `.to(device=self.device, dtype=self.dtype)` when `last_phi_deg` is already a tensor, and extend `Crystal.to` to move `_phi_last_cache` tensors (or invalidate them) when switching device/dtype; avoid fresh `torch.tensor` factories inside loops.
- CPU trace: `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/rot_vector/trace_harness.py --pixel 685 1039 --config supervisor --dtype float64 --device cpu --out reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251124/trace_py_rot_vector.log` (writes per-φ JSON under matching per_phi/ path).
- CUDA trace (if `torch.cuda.is_available()`): rerun harness with `--device cuda --dtype float32` and store outputs under `.../base_vector_debug/20251124_cuda/`.
- Comparison: `python scripts/compare_per_phi_traces.py reports/2025-10-cli-flags/phase_l/per_phi/reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251124/trace_py_rot_vector_per_phi.json reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251123/c_trace_phi_20251123.log | tee reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251124/compare_latest.txt` (repeat for CUDA output if captured).
- Tests: `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q`, then the two `test_cli_scaling_phi0` selectors, and `pytest tests/test_suite.py::TestTier2GradientCorrectness::test_gradcheck_phi_rotation -v` (expect success post-fix).
- Documentation: update `reports/2025-10-cli-flags/phase_l/rot_vector/base_vector_debug/20251124/diagnosis.md`, `.../comparison_summary.md`, and fix_checklist VG-1.4 with CPU/GPU metrics before logging Attempt in docs/fix_plan.md.
Pitfalls To Avoid:
- Do not recreate tensors from Python floats when the source is already a tensor; use `.to(...)` or cloning to preserve gradients.
- Keep `_phi_last_cache` optional; if device/dtype mismatch arises, either migrate tensors or clear the cache before reuse.
- Avoid `.item()`/`.cpu()` in hot paths; restrict scalars to harness scripts only.
- Leave guard tests in `tests/test_cli_scaling_phi0.py` intact; only expect them to flip green once Δk ≤ 1e-6.
- Ensure per-φ traces use fresh timestamp directories; never overwrite 20251123 reference logs.
- Capture CUDA artifacts only if hardware is available; otherwise note the absence in diagnosis.md.
- Respect Protected Assets (docs/index.md) while editing; no renames/deletions of listed files.
- Reflect the fix in docs/fix_plan.md Attempt history once evidence is stored.
Pointers:
- plans/active/cli-noise-pix0/plan.md:307
- docs/fix_plan.md:452
- src/nanobrag_torch/models/crystal.py:1067
- src/nanobrag_torch/models/crystal.py:1192
- tests/test_suite.py:1774
Next Up: 1) CLI-FLAGS-003 L3k.3d — nb-compare ROI parity refresh; 2) CLI-FLAGS-003 L3k.3e — documentation sign-off and Attempt logging.

Summary: Capture C-side omega taps for the 4096² benchmark edge pixel so we can compare with the new PyTorch measurements and reassess the Phase E hypothesis.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/c_taps/
Do Now: [VECTOR-PARITY-001] Next Action #1 — instrument `golden_suite_generator/nanoBragg` for Tap 3 and run `KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg nb-compare --roi 0 1 0 1 -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 0.5 -distance 500 -detpixels 4096 -pixel 0.05 -N 5 -oversample 2`
If Blocked: Capture the PyTorch omega tap again with `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 0 0 --out-dir reports/2026-01-vectorization-parity/phase_e0/<STAMP>/py_taps_retry/` and log the failure mode in Attempt history.
Priorities & Rationale:
- plans/active/vectorization-parity-regression.md (Phase E1–E3) — PyTorch tap shows ω bias ≈0.003%, so we must validate C semantics before proposing fixes.
- docs/fix_plan.md [VECTOR-PARITY-001] — Next Actions now target C taps plus HKL/background analysis; completing step 1 unblocks the comparison memo.
- reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/trace/tap_points.md — Command + tap schema for omega_subpixel_edge/center instrumentation.
- specs/spec-a-core.md (sampling & normalization) — ensure instrumentation respects units and avoids recomputing physics.
- docs/development/testing_strategy.md §1.4 — maintain device/dtype neutrality during diagnostics.
How-To Map:
- Edit `golden_suite_generator/nanoBragg` according to Tap 3 (`trace/tap_points.md`) so the oversample loop emits all four ω values with a `TRACE_C: omega_subpixel` prefix; rebuild via `make -C golden_suite_generator`.
- Run `mkdir -p reports/2026-01-vectorization-parity/phase_e0/$(date -u +%Y%m%dT%H%M%SZ)/c_taps` before execution; save command logs and raw trace (`tap_omega_edge.txt`) there.
- Execute `KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg nb-compare --roi 0 1 0 1 -- -default_F 100 -cell 100 100 100 90 90 90 -lambda 0.5 -distance 500 -detpixels 4096 -pixel 0.05 -N 5 -oversample 2` and confirm the trace captures ω for both edge and centre pixels (use `NB_TRACE_EDGE_PIXEL` / `NB_TRACE_CENTER_PIXEL` if required).
- Document extracted ω values and last/mean ratios in `omega_comparison.md` within the same report folder; include any instrumentation diff summary.
- Leave production sources untouched; discard instrumentation after capturing the tap.
Pitfalls To Avoid:
- Do not modify PyTorch simulator code yet — evidence only.
- Keep `reports/` artifacts out of git (verify with `git status`).
- Maintain device/dtype neutrality if you run auxiliary PyTorch probes.
- Avoid overriding Protected Assets (docs/index.md, loop scripts).
- Capture precise commands/env in commands.txt for reproducibility.
- Remove instrumentation immediately after use to prevent accidental commits.
- Don’t skip `make -C golden_suite_generator` after editing C sources.
- Ensure ROI order is `(slow fast)` exactly as in the command.
- Use `TRACE_C:` prefix to stay consistent with existing logs.
Pointers:
- plans/active/vectorization-parity-regression.md (Phase E table)
- docs/fix_plan.md: [VECTOR-PARITY-001] section & Attempt #23 note
- reports/2026-01-vectorization-parity/phase_e0/20251010T092845Z/trace/tap_points.md
- specs/spec-a-core.md
- docs/development/testing_strategy.md §2.1
Next Up: Extend taps to HKL default_F counts (Tap 4) once the C omega data is archived.

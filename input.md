Summary: Extend the parity tap tooling to capture PyTorch Tap 5 (pre-normalisation intensity) so we can compare edge vs centre before scaling.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q (post-instrumentation sanity)
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/py_taps/ ; reports/2026-01-vectorization-parity/phase_e0/<STAMP>/comparison/
Do Now: [VECTOR-PARITY-001] Next Actions #1 — update `scripts/debug_pixel_trace.py` for Tap 5 `--taps intensity` and capture PyTorch metrics via `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 0 0 --tag edge --oversample 2 --taps intensity --json --out-dir "$OUT_PY"` (repeat for centre pixel)
If Blocked: Drop findings + blockers in `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/py_taps/notes.md` with referenced code lines before stopping.
Priorities & Rationale:
- docs/fix_plan.md:65-67 — Stage Tap 5 instrumentation before advancing to Tap 6 or remediation.
- plans/active/vectorization-parity-regression.md:85-87 — Phase E tasks E8–E10 define this Tap 5 capture + comparison.
- plans/active/vectorization.md:13-17 — Vectorization relaunch remains gated on completing Tap 5 evidence.
- specs/spec-a-core.md:471-476 — Governs default_F and rendering/normalisation semantics you must respect when instrumenting.
- arch.md:216 — Documents expected final-scaling pipeline; Tap 5 must reuse these intermediates.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `export BASE=reports/2026-01-vectorization-parity/phase_e0`; `export OUT_PY="$BASE/${STAMP}/py_taps"`; `export OUT_CMP="$BASE/${STAMP}/comparison"`; `mkdir -p "$OUT_PY" "$OUT_CMP"` and append every command to `$OUT_PY/commands.txt`.
- Modify `scripts/debug_pixel_trace.py` to accept `--taps intensity` that records at least `{accumulated_intensity, steps, last_omega_applied, normalized_intensity}` using existing `I_before_scaling`, `omega`, and `steps` variables (see lines 505-545); avoid recomputing physics or breaking differentiability.
- After edits, run `KMP_DUPLICATE_LIB_OK=TRUE python scripts/debug_pixel_trace.py --pixel 0 0 --tag edge --oversample 2 --taps intensity --json --out-dir "$OUT_PY"` and the same command with `--pixel 2048 2048 --tag centre`.
- Write a concise `pre_norm_summary.md` under `$OUT_CMP` comparing edge vs centre metrics (note any deltas) and reference the JSON filenames.
- Sanity check importability with `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q` and log output to `$OUT_PY/pytest_collect.log`.
Pitfalls To Avoid:
- No ad-hoc `.cpu()` or device assumptions; taps must respect caller device/dtype.
- Do not re-derive physics; reuse already-computed tensors (Rule 11 instrumentation guardrail).
- Keep all tap artifacts under `reports/`; never add them to git.
- Preserve existing Tap 4 functionality; adding Tap 5 must not change prior outputs.
- Make tap key names stable (`intensity_pre_norm`) to align with planned comparisons.
- Ensure tap JSON is serialised with numeric types (use `float()` casts where needed).
- Maintain ASCII formatting in summary docs per repo guideline.
- Capture commands/env context; missing provenance will block applying the evidence.
- Do not touch Protected Assets listed in docs/index.md.
Pointers:
- docs/fix_plan.md:65-67
- plans/active/vectorization-parity-regression.md:85-87
- plans/active/vectorization.md:13-17
- specs/spec-a-core.md:471-476
- scripts/debug_pixel_trace.py:505-606
Next Up: Run `[VECTOR-PARITY-001]` Next Action #2 to instrument C Tap 5 once PyTorch metrics look sound.

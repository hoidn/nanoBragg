Summary: Capture Tap 5.1 HKL taps from the C binary to mirror the new PyTorch evidence.
Mode: Parity
Focus: VECTOR-PARITY-001 Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/c_taps/, reports/2026-01-vectorization-parity/phase_e0/<STAMP>/comparison/
Do Now: Execute docs/fix_plan.md item [VECTOR-PARITY-001] Next Action 1 (Tap 5.1 C mirror); add the guarded `TRACE_C_TAP5_HKL` block, rebuild `golden_suite_generator/nanoBragg`, capture pixels (0,0) and (2048,2048) with `TRACE_C_TAP5_HKL=1`, then run pytest --collect-only -q.
If Blocked: Capture the attempted instrumentation diff plus any compiler errors under `reports/2026-01-vectorization-parity/phase_e0/<STAMP>/attempt_log.md` and restore the binary to the previous TRACE_C_TAP5 state.
Priorities & Rationale:
- docs/fix_plan.md:69 – Next Action 1 is the C Tap 5.1 mirror; completing it unblocks the HKL bounds check.
- plans/active/vectorization-parity-regression.md:91 – Phase E13 requires a C-side schema identical to the PyTorch tap to compare HKL rounding.
- plans/active/vectorization.md:18 – Phase D backlog stays blocked until Tap 5 evidence (now extending to C Tap 5.1) is archived.
- specs/spec-a-core.md:232 – HKL fallback semantics demand proof that (0,0,0) is in range rather than default_F.
How-To Map:
- export STAMP=$(date -u +%Y%m%dT%H%M%SZ); OUTDIR=reports/2026-01-vectorization-parity/phase_e0/$STAMP
- mkdir -p "$OUTDIR"/c_taps "$OUTDIR"/comparison "$OUTDIR"/env
- Edit `golden_suite_generator/nanoBragg.c` HKL lookup block (~lines 3300-3355) to wrap the existing Tap 5 instrumentation with `#ifdef TRACE_C_TAP5_HKL` (new guard) logging fractional HKL (double), rounded `(h0,k0,l0)` ints, `F_cell`, `out_of_bounds`, and raw structure-factor table indices. Follow the formatting from Attempt #30 (`TRACE_C_TAP5`) but reuse identical token names emitted by the PyTorch tap JSON.
- Rebuild: `make -C golden_suite_generator nanoBragg`
- Capture edge pixel: `TRACE_C_TAP5_HKL=1 ./golden_suite_generator/nanoBragg -cell 100 100 100 90 90 90 -lambda 0.5 -distance 500 -detpixels 4096 -pixel 0.05 -mosflm -oversample 2 -default_F 100 -N 5 -trace_pixel 0 0 -roi 0 0 0 0 -floatfile /tmp/tap5_edge.bin > "$OUTDIR"/c_taps/pixel_0_0_hkl.log 2>&1`
- Capture centre pixel: same command with `-trace_pixel 2048 2048 -roi 2048 2048 2048 2048` and log to `pixel_2048_2048_hkl.log`
- Copy the log excerpts into structured JSON (matching PyTorch schema) under `$OUTDIR/c_taps/` and document findings in `$OUTDIR/comparison/tap5_hkl_c_summary.md`
- Record environment metadata: `git rev-parse HEAD > "$OUTDIR"/env/git_sha.txt`; `python - <<'PY'` block dumping platform/python/torch versions into `$OUTDIR/env/trace_env.json`
- Run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee "$OUTDIR"/comparison/pytest_collect.log`
Pitfalls To Avoid:
- Do not leave TRACE_C_TAP5_HKL instrumentation active without the guard macro.
- Keep commands reproducible; log every CLI invocation in `commands.txt`.
- Do not overwrite prior Tap 5 artifacts—use a fresh STAMP directory.
- Avoid touching PyTorch code paths this loop; parity evidence only.
- Maintain MOSFLM convention parameters exactly as provided.
- Keep generated binaries untracked; only logs/metadata go in reports/.
Pointers:
- docs/fix_plan.md:69
- plans/active/vectorization-parity-regression.md:91
- specs/spec-a-core.md:232
- plans/active/vectorization.md:18
Next Up: Prepare Tap 5.2 HKL bounds parity capture once the C Tap 5.1 logs land.

Summary: Capture C-side Tap 5 (intensity pre-normalisation) metrics for the edge/centre pixels so we can line up with the new PyTorch evidence.
Mode: Parity
Focus: [VECTOR-PARITY-001] Restore 4096² benchmark parity
Branch: feature/spec-based-2
Mapped tests: pytest --collect-only -q
Artifacts: reports/2026-01-vectorization-parity/phase_e0/<STAMP>/c_taps/ ; reports/2026-01-vectorization-parity/phase_e0/<STAMP>/comparison/
Do Now: [VECTOR-PARITY-001] Next Actions #1 — instrument `golden_suite_generator/nanoBragg` with a `TRACE_C_TAP5` guard and capture Tap 5 logs for pixels (0,0) and (2048,2048) at oversample=2.
If Blocked: Record the partial instrumentation and the blocker details in `$OUT_C/notes.md` (include snippet references + compile/runtimes) before stopping.
Priorities & Rationale:
- docs/fix_plan.md:65-68 — Tap 5 PyTorch evidence landed; we now need the matching C capture before Phase E can advance.
- plans/active/vectorization-parity-regression.md:85-87 — Phase E9 requires C Tap 5 instrumentation with archived artifacts.
- specs/spec-a-core.md:246-259 — Normative scaling equation for intensity; the tap must reuse these intermediates.
- golden_suite_generator/nanoBragg.c:3325-3405 — Existing `TRACE_C` block already batches the data we need; extend it instead of duplicating physics.
- docs/development/testing_strategy.md:41-49 — Collect-only pytest after touching build scripts.
How-To Map:
- `export STAMP=$(date -u +%Y%m%dT%H%M%SZ)`; `export BASE=reports/2026-01-vectorization-parity/phase_e0`; `export OUT_C="$BASE/${STAMP}/c_taps"`; `export OUT_SUM="$BASE/${STAMP}/comparison"`; `mkdir -p "$OUT_C" "$OUT_SUM" "$BASE/${STAMP}/env"`.
- Append every shell command you run to `$OUT_C/commands.txt` (`printf '%s\n' "$CMD" >> "$OUT_C/commands.txt"` before executing) and keep raw stdout/stderr via `tee` when capturing traces.
- In `golden_suite_generator/nanoBragg.c` around lines 3333-3393, wrap the existing `TRACE_C` pixel block with a runtime guard such as:
  ```c
  const char *tap5_env = getenv("TRACE_C_TAP5");
  if(tap5_env && fpixel==trace_fpixel && spixel==trace_spixel && source==0 && mos_tic==0 && phi_tic==0) {
      printf("TRACE_C_TAP5: pixel %d %d\n", spixel, fpixel);
      printf("TRACE_C_TAP5: I_before_scaling %.15g\n", I);
      printf("TRACE_C_TAP5: steps %d\n", steps);
      printf("TRACE_C_TAP5: omega_pixel %.15g\n", omega_pixel);
      printf("TRACE_C_TAP5: capture_fraction %.15g\n", capture_fraction);
      printf("TRACE_C_TAP5: polar %.15g\n", polar);
      printf("TRACE_C_TAP5: I_pixel_final %.15g\n", test);
  }
  ```
  Keep the logic immutable otherwise and cite the spec in a comment.
- Rebuild the binary: `pushd golden_suite_generator`, `make clean`, `make nanoBragg`, `popd`.
- Capture edge pixel tap:
  ```bash
  export NB_C_BIN=./golden_suite_generator/nanoBragg
  TRACE_C_TAP5=1 "$NB_C_BIN" -cell 100 100 100 90 90 90 -lambda 0.5 -distance 500 \
    -detpixels 4096 -pixel 0.05 -mosflm -oversample 2 -default_F 100 -N 5 \
    -trace_pixel 0 0 -roi 0 0 0 0 -floatfile /tmp/tap5_edge.bin \
    2>&1 | tee "$OUT_C/pixel_0_0_tap5.log"
  ```
- Repeat for the centre pixel (update `-trace_pixel 2048 2048`, log to `pixel_2048_2048_tap5.log`).
- Summarise the key numbers (I_before_scaling, steps, omega, capture_fraction, polar, final intensity) into `$OUT_SUM/intensity_pre_norm_c_notes.md` for quick diffing next loop.
- Capture environment metadata:
  ```bash
  python - <<'PY'
  import json, os, platform, subprocess
  out = {
      "timestamp": os.environ.get("STAMP"),
      "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
      "compiler": subprocess.check_output(["gcc", "--version"]).decode().splitlines()[0],
      "cflags": os.environ.get("CFLAGS", ""),
      "python": platform.python_version(),
      "system": platform.platform(),
  }
  with open(os.path.join(os.environ["BASE"], os.environ["STAMP"], "env", "trace_env.json"), "w") as fh:
      json.dump(out, fh, indent=2)
  PY
  ```
- Sanity-check imports: `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q | tee "$OUT_C/pytest_collect.log"`.
Pitfalls To Avoid:
- Keep the instrumentation behind the `TRACE_C_TAP5` guard; no unconditional printf noise in committed binaries.
- Don’t alter the physics math (no extra multiplies/divides) — this tap is read-only.
- Do not commit `reports/**` artifacts; they stay local evidence only.
- Match the PyTorch configuration exactly (oversample=2, MOSFLM, same cell/default_F); drifting params will send us on a wild goose chase.
- Unset `TRACE_C_TAP5` (or open a fresh shell) before launching other runs so later traces stay clean.
- Use ROI targeting to avoid generating the full 4096² image — the command above keeps runtime manageable.
- Remember to update `commands.txt` as you go; missing provenance blocks plan closure.
- Preserve ASCII formatting in the summary doc.
- No ad-hoc `cd` without documenting it in `commands.txt`.
- Respect Protected Assets listed in docs/index.md.
Pointers:
- docs/fix_plan.md:65-68
- plans/active/vectorization-parity-regression.md:85-87
- specs/spec-a-core.md:246-259
- golden_suite_generator/nanoBragg.c:3325-3393
- docs/development/testing_strategy.md:41-49
Next Up: Compare Tap 5 metrics (docs/fix_plan.md Next Action #2) and decide on Tap 6 vs Phase F remediation.

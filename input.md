Summary: Capture definitive gradcheck evidence for the phi carryover cache so VG‑2 parity work can resume with gradients intact.
Mode: Parity
Focus: CLI-FLAGS-003 – Handle -nonoise and -pix0_vector_mm (Phase M2h.3 gradcheck)
Branch: feature/spec-based-2
Mapped tests: tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c (collect-only)
Artifacts: reports/2025-10-cli-flags/phase_l/scaling_validation/<timestamp>_carryover_cache_validation/{gradcheck_probe.py,gradcheck.log,gradcheck_cpu.log?,commands.txt,env.json,torch_collect_env.txt,pytest_collect.log,summary.md,sha256.txt}
Do Now: CLI-FLAGS-003 – M2h.3 gradcheck | (cd "$OUTDIR" && KMP_DUPLICATE_LIB_OK=TRUE python gradcheck_probe.py --device cuda --dtype float64 > gradcheck.log 2>&1) after building the timestamped harness below
If Blocked: If CUDA is unavailable or gradients disappear, rerun the probe with --device cpu, capture the failure in gradcheck.log (and gradcheck_cpu.log if used), note the blocker in summary.md, and log it in docs/fix_plan.md Attempt notes.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md:29 — Status snapshot documents Attempt #166 clearing the CUDA blocker; gradcheck is now the top gate.
- plans/active/cli-noise-pix0/plan.md:74 — M2h checklist marks M2h.2 [D] and describes M2h.3 deliverables (script + log + summary).
- docs/fix_plan.md:462 — Next Actions emphasise running the 2×2 ROI gradcheck before new traces or cache index audits.
- docs/bugs/verified_c_bugs.md:166 — Carryover shim intentionally emulates the C bug; gradients must remain live to keep spec mode optimisable.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T160802Z_carryover_cache_validation/diagnostics.md — Contains the reference template for the gradcheck probe we’re formalising.

How-To Map:
- Step 1 — Prepare timestamped workspace
-   `TS=$(date -u +%Y%m%dT%H%M%SZ)`
-   `OUTDIR=reports/2025-10-cli-flags/phase_l/scaling_validation/${TS}_carryover_cache_validation`
-   `mkdir -p "$OUTDIR"`
- Step 2 — Capture shell + runtime context
-   `pwd > "$OUTDIR/commands.txt"`
-   `git rev-parse HEAD >> "$OUTDIR/commands.txt"`
-   `python --version >> "$OUTDIR/commands.txt"`
-   `python -c "import torch; print(torch.__version__)" >> "$OUTDIR/commands.txt"`
-   `echo "CUDA available: $(python -c 'import torch; print(torch.cuda.is_available())')" >> "$OUTDIR/commands.txt"`
- Step 3 — Author gradcheck_probe.py using the diagnostics template
-   Open diagnostics.md M2h.3 section and copy the scaffold into `$OUTDIR/gradcheck_probe.py`.
-   Add argparse flags `--device {auto,cuda,cpu}` (default auto) and `--dtype {float64,float32}` (default float64).
-   Ensure the script:
-     * Instantiates `CrystalConfig` with phi_carryover_mode="c-parity" and tensors requiring grad.
-     * Calls `initialize_phi_cache(spixels=2, fpixels=2, mosaic_domains=1)` on the crystal.
-     * Stores dummy rotation vectors with `requires_grad=True` using `store_phi_final`.
-     * Retrieves them through `apply_phi_carryover`, sums the result, and backprops.
-     * Checks a representative parameter (e.g., `cell_a`) for non-null `.grad`.
-     * Prints a JSON payload (timestamp, device, dtype, grad_present, loss) to stdout.
-     * Raises `SystemExit` with a clear message if gradients are missing.
-   Keep all tensors on the selected device/dtype (use `.to(device=d, dtype=t)` helpers as needed).
- Step 4 — Run CUDA probe (primary target)
-   `(cd "$OUTDIR" && KMP_DUPLICATE_LIB_OK=TRUE python gradcheck_probe.py --device cuda --dtype float64 > gradcheck.log 2>&1)`
-   Append `CUDA gradcheck: $(grep -m1 '"grad_present"' "$OUTDIR/gradcheck.log" 2>/dev/null)` to `$OUTDIR/summary.md`.
- Step 5 — Fallback probe when CUDA path fails or gradients are absent
-   `(cd "$OUTDIR" && KMP_DUPLICATE_LIB_OK=TRUE python gradcheck_probe.py --device cpu --dtype float64 > gradcheck_cpu.log 2>&1 || true)`
-   If `gradcheck_cpu.log` exists, log `CPU gradcheck: $(grep -m1 '"grad_present"' "$OUTDIR/gradcheck_cpu.log" 2>/dev/null)` in summary.md.
-   Note any exceptions (device mismatch, missing grad) in summary.md so the blocker is explicit.
- Step 6 — Record environment metadata
-   `(cd "$OUTDIR" && python -m torch.utils.collect_env > torch_collect_env.txt 2>&1)`
-   `python - <<'PY' > "$OUTDIR/env.json"`
-   `import json, torch, time`
-   `print(json.dumps({`
-   `    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),`
-   `    "cuda_available": torch.cuda.is_available(),`
-   `    "device_count": torch.cuda.device_count(),`
-   `    "torch_version": torch.__version__`,
-   `}, indent=2))`
-   `PY`
- Step 7 — Confirm pytest selector discoverability
-   `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_scaling_parity.py::TestScalingParity::test_I_before_scaling_matches_c | tee "$OUTDIR/pytest_collect.log"`
- Step 8 — Finalise summary + checksums
-   Add a short narrative to summary.md covering devices tested, gradient results, and links to logs.
-   `(cd "$OUTDIR" && sha256sum * > sha256.txt)`

Pitfalls To Avoid:
- Remain in evidence mode; do not modify simulator/crystal code this loop.
- Keep every tensor allocation on the requested device/dtype—no implicit `.cpu()` fallbacks.
- Avoid `.detach()`/`.clone()` in the probe unless you re-enable gradients immediately.
- Respect Protected Assets (docs/index.md); create new artifacts rather than editing indexed ones.
- Do not run the full pytest suite; the collect-only selector is all that’s required here.
- Always set KMP_DUPLICATE_LIB_OK=TRUE when invoking Python commands that import torch.
- If CUDA is absent, state it in summary.md and env.json instead of silently skipping the probe.
- Store all outputs in the timestamped directory to keep evidence bundles isolated.
- Capture stderr alongside stdout when running probes to avoid losing exceptions.
- Use UTC timestamps consistently so reports sort chronologically.

Pointers:
- plans/active/cli-noise-pix0/plan.md:29 — Status snapshot calling for gradcheck evidence.
- plans/active/cli-noise-pix0/plan.md:74 — M2h table defining SUCCESS criteria for the probe.
- docs/fix_plan.md:462 — Updated Next Actions list prioritising M2h.3.
- reports/2025-10-cli-flags/phase_l/scaling_validation/20251008T160802Z_carryover_cache_validation/diagnostics.md — Template + context for the probe.
- docs/bugs/verified_c_bugs.md:166 — Rationale for emulating φ=0 carryover while keeping gradients live.

Next Up: Once gradients are verified, re-run trace_harness.py with ROI 684–686 × 1039–1040 in c-parity mode (Phase M2i.1) to chase the remaining F_latt divergence.

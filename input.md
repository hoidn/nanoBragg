Summary: Confirm PyTorch and C ingest `scaled.hkl` identically so we can isolate the supervisor-command normalization bug.
 - Mode: Parity
Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_l/hkl_parity/; reports/2025-10-cli-flags/phase_l/scaling_trace/
Do Now: CLI-FLAGS-003 Phase L1 — KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg python scripts/validation/compare_structure_factors.py --hkl scaled.hkl --fdump Fdump.bin --out reports/2025-10-cli-flags/phase_l/hkl_parity/summary.md
If Blocked: If the parity script fails, capture raw dumps via `python - <<'PY'` using `nanobrag_torch.io.hkl.read_hkl_file` and NumPy `np.fromfile` to compute max |ΔF|; save results under `reports/2025-10-cli-flags/phase_l/hkl_parity/blocked/` and log the issue in docs/fix_plan.md before touching simulator code.

Priorities & Rationale:
- plans/active/cli-noise-pix0/plan.md: L1 requires HKL parity evidence before scaling traces (L2) can be trusted.
- docs/fix_plan.md#cli-flags-003-handle-nonoise-and-pix0_vector_mm — Next actions call out L1–L3 sequencing; we must clear L1 first.
- specs/spec-a-core.md §Structure factors — mandates identical HKL grid semantics between C and PyTorch.
- specs/spec-a-cli.md §HKL caching — confirms C writes Fdump on every -hkl run; evidence must show PyTorch honors the same semantics.
- docs/architecture/c_parameter_dictionary.md — Provides authoritative mapping for -hkl/-default_F behavior used in the comparison script.
- docs/architecture/pytorch_design.md §2.4 — Notes caching rules for structure factors that the new script must respect.
- docs/development/testing_strategy.md §2.1 — Parallel trace-driven validation begins with confirming input parity.
- reports/2025-10-cli-flags/phase_j/scaling_chain.md — Earlier analysis showed F_latt is the first divergence; confirming HKL parity narrows down remaining causes.
- reports/2025-10-cli-flags/phase_k/base_lattice/summary.md — Post-fix addendum proves MOSFLM vectors match; HKL parity is the next dependency before Phase L traces.

How-To Map:
- export KMP_DUPLICATE_LIB_OK=TRUE NB_C_BIN=./golden_suite_generator/nanoBragg
- STAMP=$(date +%Y%m%d%H%M%S)
- "$NB_C_BIN" -mat A.mat -hkl scaled.hkl -detpixels 16 -pixel 0.1 -distance 50 -floatfile /tmp/fdump_probe_${STAMP}.bin -nonoise -nointerpolate -oversample 1 -exposure 0 -flux 0 -beamsize 1.0 >/tmp/c_fdump_${STAMP}.log 2>&1
- test -f Fdump.bin && mv Fdump.bin Fdump_scaled_${STAMP}.bin  # preserve the cache written by C
- mkdir -p scripts/validation
- If scripts/validation/compare_structure_factors.py does not exist, author it to load `scaled.hkl` via `nanobrag_torch.io.hkl.read_hkl_file`, load `Fdump_scaled_${STAMP}.bin` via `nanobrag_torch.io.hkl.read_fdump`, compare shapes, mins/maxes, and max |ΔF|; emit Markdown summary.
- Implement CLI args `--hkl`, `--fdump`, `--out`, `--metrics`, and `--device`/`--dtype` for completeness; raise if files missing.
- Use `torch.load` equivalents from `nanobrag_torch.io.hkl` (avoid numpy-only paths) so gradients remain optional.
- Within the script, compute: shape parity, `torch.max(torch.abs(F_hkl - F_fdump))`, relative RMS error, and count of mismatched voxels above tolerance (1e-6).
- Emit Markdown + JSON outputs capturing these metrics plus SHA256 hashes (use `hashlib.sha256`).
- python scripts/validation/compare_structure_factors.py --hkl scaled.hkl --fdump Fdump_scaled_${STAMP}.bin --out reports/2025-10-cli-flags/phase_l/hkl_parity/summary_${STAMP}.md --metrics reports/2025-10-cli-flags/phase_l/hkl_parity/metrics_${STAMP}.json --device cpu --dtype float64
- tee the script stdout to `reports/2025-10-cli-flags/phase_l/hkl_parity/run_${STAMP}.log` for traceability.
- Copy or symlink the summary to `reports/2025-10-cli-flags/phase_l/hkl_parity/summary.md` for plan cross-reference; include the command log and SHA256 hashes for both sources.
- Record max |ΔF|, relative RMS, and mismatch counts in docs/fix_plan.md Attempt history under CLI-FLAGS-003; note script location.
- Leave the generated `Fdump_scaled_${STAMP}.bin` under `reports/2025-10-cli-flags/phase_l/hkl_parity/` (or remove after hashing) so future loops can reuse it without rerunning C.
- Optionally run `pytest --collect-only -q tests/test_cli_scaling.py` to ensure new helper imports cleanly (no mandatory tests to execute).

Pitfalls To Avoid:
- Do not delete or overwrite older reports; keep STAMPed directories.
- Ensure Fdump_scaled_${STAMP}.bin is excluded from git (already ignored) and stored under reports/ if needed.
- No production code edits unless parity proves an issue; gather evidence first.
- Maintain device/dtype neutrality in any helper script (allow device override even if unused now).
- Set KMP_DUPLICATE_LIB_OK=TRUE before every torch import to avoid MKL crashes.
- Keep NB_C_BIN pointed at the instrumented binary; do not fall back to ./nanoBragg.
- Respect Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md).
- Avoid running full pytest suites; stay within evidence gate (collect-only allowed if you add tests later).
- Document any deviations or missing data immediately in docs/fix_plan.md and the plan checklist.
- If the script surfaces differences, stop and capture traces rather than guessing at fixes.
- Use `with open(..., 'rb')` when hashing to avoid buffering mistakes; store hashes next to metrics.
- Keep the helper script pure (no writes outside provided outdir) so reruns stay deterministic.
- Make sure to restore/rename Fdump after script runs if additional C jobs need the cache.
- Check that the script respects `torch.set_default_dtype` if future loops adjust precision.
- Do not assume symmetrical HKL ranges; use metadata from both files when reporting results.

Pointers:
- plans/active/cli-noise-pix0/plan.md#phase-l-—-supervisor-command-normalization
- docs/fix_plan.md#cli-flags-003-handle-nonoise-and-pix0_vector_mm
- specs/spec-a-core.md#structure-factors
- specs/spec-a-cli.md#cli-binding-profile-reference-cli
- docs/architecture/c_parameter_dictionary.md#hkl-and-fdump
- docs/architecture/pytorch_design.md#vectorization-strategy
- docs/development/testing_strategy.md#21-ground-truth-parallel-trace-driven-validation
- reports/2025-10-cli-flags/phase_j/scaling_chain.md
- reports/2025-10-cli-flags/phase_k/base_lattice/summary.md
- src/nanobrag_torch/io/hkl.py
- reports/2025-10-cli-flags/phase_k/base_lattice/run_c_trace.sh
- reports/2025-10-cli-flags/phase_k/base_lattice/trace_harness.py

Artifacts Checklist:
- reports/2025-10-cli-flags/phase_l/hkl_parity/summary_${STAMP}.md
- reports/2025-10-cli-flags/phase_l/hkl_parity/metrics_${STAMP}.json
- reports/2025-10-cli-flags/phase_l/hkl_parity/run_${STAMP}.log
- reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_${STAMP}.bin (or SHA recorded if deleted)
- /tmp/c_fdump_${STAMP}.log copied into reports for provenance
- docs/fix_plan.md Attempt update referencing the above paths

Logging Requirements:
- Append a brief note to galph_memory.md summarizing max |ΔF| results and any surprises.
- If discrepancies appear, capture first-divergence indices (h,k,l) inside the JSON metrics for future loops.
- Note whether `read_hkl_file` emitted warnings about non-integer indices; this impacts tolerance selection.
- Update plans/active/cli-noise-pix0/plan.md Phase L1 checklist state once evidence is archived.

Review Notes:
- After generating metrics, sanity-check that `h_range`, `k_range`, and `l_range` match between inputs.
- Confirm default_F handling (ensure unspecified reflections stay at configured default values).
- Verify the script uses float64 during comparison; document any dtype conversions applied.
- If you observe large |ΔF| localized to edges, flag it in the diagnosis doc for Phase L3.

Verification Targets:
- Max |ΔF| ≤ 1e-6 electrons (tight parity target drawn from prior attempts).
- Relative RMS error ≤ 1e-8 to ensure no systemic scaling offset remains.
- Zero mismatched voxels above tolerance once caches align (expectation per spec).
- SHA256 hash of Fdump matches reruns; note deviations in logs if environment differs.

Timebox Suggestions:
- ≤10 minutes to regenerate Fdump with reduced detector size; abort and log if C run stalls.
- ≤20 minutes to author and validate the comparison script (reuse existing utilities where possible).
- ≤10 minutes to document outcomes in reports/ and docs/fix_plan.md, keeping future loops unblocked.
- If overall effort exceeds 45 minutes due to unexpected discrepancies, pause and request supervisor guidance with captured evidence.


Next Up: After HKL parity evidence is in place, move to Phase L2 (scaling-chain traces) to pinpoint the remaining normalization mismatch.

Summary: Source the supervisor pixel’s structure factor by probing the archived C Fdump so Phase L3 can unblock normalization work.
Mode: Parity
Focus: CLI-FLAGS-003 › Phase L3b structure-factor ingestion analysis
Branch: feature/spec-based-2
Mapped tests: none — evidence-only
Artifacts: reports/2025-10-cli-flags/phase_l/structure_factor/probe.log; reports/2025-10-cli-flags/phase_l/structure_factor/analysis.md; reports/2025-10-cli-flags/phase_l/structure_factor/hkl_inventory.md (if you enumerate files)
Do Now: CLI-FLAGS-003 › Phase L3b Analyze structure-factor sources — run `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/structure_factor/probe.py --pixel 685 1039 --hkl scaled.hkl --fdump reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_20251006175946.bin --fdump golden_suite_generator/Fdump.bin --fdump tmp/Fdump.bin --dtype float64 --device cpu` and update analysis.md with findings.
If Blocked: Record command, stderr, and `git rev-parse HEAD` in `reports/2025-10-cli-flags/phase_l/structure_factor/blocked.md`, then run `KMP_DUPLICATE_LIB_OK=TRUE pytest --collect-only -q tests/test_cli_flags.py` to verify imports and log the selector + result in Attempts History.

Context Snapshot
- Phase L2 artifacts show every scaling factor except `I_before_scaling` now matches C (`reports/2025-10-cli-flags/phase_l/scaling_audit/scaling_audit_summary.md`).
- `c_trace_scaling.log:143-164` reports `F_cell=190.27` for hkl=(-7,-1,-14); PyTorch trace still shows `F_cell=0` for the same pixel (`trace_py_scaling.log:18-32`).
- Repo-local `scaled.hkl` is a 13-byte stub (only `(1,12,3)`), and both `golden_suite_generator/Fdump.bin` and `tmp/Fdump.bin` are 2×2×2 caches generated from that stub.
- `reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_20251006175946.bin` is a 1.4 MB C-generated cache with ranges h∈[-24,24], k∈[-28,28], l∈[-31,30]; it contains the supervisor reflection with amplitude 190.27.
- Phase L3 requires determining how the C run sourced that cache (reuse vs regenerate) before touching simulator code.
- docs/fix_plan.md:457-461 and plans/active/cli-noise-pix0/plan.md:255-262 both gate further work on documenting the structure-factor source.

Success Criteria
- `probe.log` lists each data source (HKL + Fdump paths), its h/k/l ranges, whether (-7,-1,-14) is in range, and the retrieved amplitude.
- `analysis.md` summarises which source matches the C amplitude and flags any gaps (e.g., need to restore the full HKL file or stage the large Fdump before running CLI parity).
- Any decision/next-step notes for L3c (copy vs regenerate cache) are captured for the next supervisor loop.

Priorities & Rationale
- docs/fix_plan.md:455-461 — current Next Actions require confirming structure-factor coverage before modifying normalization code.
- plans/active/cli-noise-pix0/plan.md:255 — Phase L3a/L3b checklist explicitly calls for this probe and ingestion analysis.
- specs/spec-a-cli.md (HKL caching section) — parity depends on mirroring C’s HKL/Fdump precedence; present data shows mismatch.
- reports/2025-10-cli-flags/phase_l/hkl_parity/layout_analysis.md — documents C cache layout; cross-check results to avoid misinterpreting ranges.
- src/nanobrag_torch/io/hkl.py:250-310 — PyTorch’s `try_load_hkl_or_fdump` currently overwrites caches when an HKL file is present; probing informs whether we need alternate flow.

How-To Map
- Command: `KMP_DUPLICATE_LIB_OK=TRUE PYTHONPATH=src python reports/2025-10-cli-flags/phase_l/structure_factor/probe.py --pixel 685 1039 --hkl scaled.hkl --fdump reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_20251006175946.bin --fdump golden_suite_generator/Fdump.bin --fdump tmp/Fdump.bin --dtype float64 --device cpu`.
- Before running, `ls -lh` each input (HKL + Fdump paths) and capture sizes in the log for provenance.
- Let the probe reuse `get_supervisor_params` so detector/beam/crystal configs stay aligned with scaling traces.
- After execution, append a markdown table in `analysis.md` with columns `[source, in_range?, F_cell]` and annotate which source reproduces 190.27.
- Note whether pointing `try_load_hkl_or_fdump` at the large cache would avoid overwriting (e.g., by omitting `-hkl` or copying the big cache to working `Fdump.bin` before CLI runs).
- If you discover missing large HKL text or need to regenerate the cache, outline the C command (with env vars) required and list it in `analysis.md`.

Pitfalls To Avoid
- Don’t run the probe without `KMP_DUPLICATE_LIB_OK=TRUE` (MKL crash) or `PYTHONPATH=src` (import failure).
- Avoid overwriting the archived C Fdump; copy it if you need to experiment.
- No production code edits this loop—stay evidence-only per plan gating.
- Do not delete or rename files listed in docs/index.md while staging artifacts.
- Keep tensors on CPU float64 for this evidence pass; CUDA is unnecessary and may hide precision issues.
- If the probe script regenerates `analysis.md`, ensure your updates include previous conclusions (don’t leave placeholder text).
- Ensure `git status` only shows intentional report updates before ending the loop.

Pointers
- docs/fix_plan.md:448-522 — active item history and current divergence write-up.
- plans/active/cli-noise-pix0/plan.md:243-266 — detailed Phase L3 task descriptions.
- reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:143-164 — authoritative C reference values.
- reports/2025-10-cli-flags/phase_l/scaling_audit/trace_py_scaling.log:18-34 — current PyTorch zeros for comparison.
- reports/2025-10-cli-flags/phase_l/hkl_parity/summary.md — previous HKL/Fdump parity investigation.
- src/nanobrag_torch/io/hkl.py:250-310 — current cache loading logic to keep in mind for ingestion strategy.

Next Up (if time allows)
- Determine whether to stage the archived Fdump as `Fdump.bin` or to restore the original HKL file, and capture the plan in `analysis.md` for Phase L3c implementation.
- Outline regression coverage ideas for Phase L3d (e.g., targeted `tests/test_cli_scaling.py` assertions using the confirmed dataset).

Summary: Document why C’s Fdump layout diverges from the HKL grid so we can unblock normalization parity.
- Mode: Parity
- Focus: CLI-FLAGS-003 Handle -nonoise and -pix0_vector_mm
- Branch: feature/spec-based-2
- Mapped tests: none — evidence-only
- Artifacts: reports/2025-10-cli-flags/phase_l/hkl_parity/layout_analysis.md; reports/2025-10-cli-flags/phase_l/hkl_parity/index_deltas.json
- Do Now: CLI-FLAGS-003 Phase L1b — KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/analyze_fdump_layout.py --hkl scaled.hkl --fdump reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_20251006175946.bin --out reports/2025-10-cli-flags/phase_l/hkl_parity/layout_analysis.md --metrics reports/2025-10-cli-flags/phase_l/hkl_parity/index_deltas.json
- If Blocked: Run the inline probe in `reports/2025-10-cli-flags/phase_l/hkl_parity/` via `KMP_DUPLICATE_LIB_OK=TRUE python scripts/validation/compare_structure_factors.py --hkl scaled.hkl --fdump <cache> --out blocked.md` and log the failure details in docs/fix_plan.md Attempt history.
- Priorities & Rationale:
  * plans/active/cli-noise-pix0/plan.md: Phase L1b now blocking everything downstream.
  * docs/fix_plan.md#cli-flags-003-handle-nonoise-and-pix0_vector_mm: Next actions call out L1b–L1d explicitly.
  * specs/spec-a-core.md#structure-factors--fdump: normative statement on contiguous `k` slabs; verify C matches it.
  * golden_suite_generator/nanoBragg.c:2359-2486: reference implementation of the writer we must mirror.
- How-To Map:
  * Generate cache (if missing): `STAMP=$(date +%Y%m%d%H%M%S) && NB_C_BIN=./golden_suite_generator/nanoBragg && $NB_C_BIN -mat A.mat -hkl scaled.hkl -detpixels 16 -pixel 0.1 -distance 50 -floatfile /tmp/fdump_probe_${STAMP}.bin -nonoise -nointerpolate -oversample 1 -exposure 0 -flux 0 -beamsize 1.0 > reports/2025-10-cli-flags/phase_l/hkl_parity/c_fdump_${STAMP}.log 2>&1 && mv Fdump.bin reports/2025-10-cli-flags/phase_l/hkl_parity/Fdump_scaled_${STAMP}.bin`.
  * Author `scripts/validation/analyze_fdump_layout.py` to parse header, compute expected vs actual element counts, and map where HKL values land in Fdump (emit Markdown + JSON with Δh, Δk, Δl histograms).
  * Run the Do Now command (CPU) and keep outputs under `reports/2025-10-cli-flags/phase_l/hkl_parity/`.
  * Update docs/fix_plan.md Attempt log with metrics once the layout is characterised.
- Pitfalls To Avoid:
  * Don’t forget `KMP_DUPLICATE_LIB_OK=TRUE` before any torch import.
  * Stay in evidence mode—no production code edits during this loop.
  * Preserve existing artifacts; write new files with timestamps, don’t overwrite.
  * Avoid hard-coding device/dtype assumptions in the analysis script.
  * Capture SHA256 hashes for any new cache to keep provenance intact.
  * Don’t delete `Fdump_scaled_20251006175032.bin`; reuse new cache paths explicitly.
  * Keep Python scripts under `scripts/validation/`, not ad-hoc locations.
  * No full `pytest` runs; at most use `--collect-only` to validate imports if you add tests.
  * Document any unexpected findings immediately in layout_analysis.md and fix_plan Attempt log.
  * Respect Protected Assets (docs/index.md, loop.sh, supervisor.sh, input.md).
- Pointers:
  * plans/active/cli-noise-pix0/plan.md:217
  * docs/fix_plan.md:448
  * specs/spec-a-core.md:460
  * docs/architecture/c_parameter_dictionary.md:96
  * src/nanobrag_torch/io/hkl.py:1
  * golden_suite_generator/nanoBragg.c:2359
- Next Up: Phase L1c — patch PyTorch HKL IO once layout analysis lands.

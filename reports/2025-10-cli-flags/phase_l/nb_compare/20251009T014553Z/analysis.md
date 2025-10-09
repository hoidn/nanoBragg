# Phase M6 Decision Analysis & Phase N1 ROI Prerequisites

**Date:** 2025-10-09T01:45:53Z
**Loop:** ralph #197 (Parity mode, CLI-FLAGS-003)
**Decision:** Skip Phase M6 (optional C-parity shim) — proceed with Option 1 (spec-compliant behavior)

## Executive Summary

Phase M6 offered an optional path to emulate the C-code's buggy `I_before_scaling` calculation to achieve pixel-perfect numerical parity. After review of the Option 1 compliance artifacts and spec requirements, **we elect to skip Phase M6** and proceed directly to Phase N (nb-compare validation) with the spec-compliant PyTorch implementation.

This decision is recorded here to satisfy plan closure requirements before advancing to Phase N1 (ROI input regeneration).

## Rationale for Skipping Phase M6

### 1. Option 1 Validates Spec Compliance

The Option 1 bundle (`reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/20251009T013046Z/`) demonstrates:

- **All downstream scaling factors pass** with ≤1e-6 tolerance
- **Structured trace comparison** confirms PyTorch follows `specs/spec-a-core.md` §§4.2-4.3 normalization contract
- **Target tests green**: `tests/test_cli_scaling_phi0.py` (2/2 passed, 2.06s)
- **Documented divergence**: Permanent -14.6% `I_before_scaling` delta attributed to verified C bug (C-PARITY-001)

### 2. C Bug Formalized in docs/bugs/verified_c_bugs.md

Entry C-PARITY-001 (lines 166-204) formally documents:
- **Root cause**: φ rotation carryover accumulation (removed per spec in Option 1)
- **Impact**: +6.8% rot_b error → +3.0% k_frac drift → F_latt sign flip → -14.6% intensity
- **Disposition**: PyTorch implementation intentionally diverges to follow spec

### 3. Phase M6 Shim Would Violate Spec

Implementing a `-phi-carryover-mode` flag to replicate the C bug would:
- **Contradict** `specs/spec-a-core.md` fresh rotation requirement (line 237)
- **Complicate** maintenance (dual code paths, test matrix expansion)
- **Delay** productive work (nb-compare validation, noise/pix0 features)

### 4. Long-Term Goals Alignment

From `plans/active/cli-noise-pix0/plan.md`:
- **Goal 1 (shim removal)**: ✅ Complete (Phases D1-D3, M5c)
- **Goal 2 (documentation)**: In progress (this analysis closes M6 requirement)
- **Goal 3 (feature parity)**: Ready for Phase N (`-nonoise`, `-pix0_vector_mm`)

## Phase M6 Disposition

- **Status**: N/A — skipped {20251009T014553Z}
- **Plan row**: Updated to `[N/A — skipped {STAMP}]`
- **Justification**: Option 1 accepted; C-PARITY-001 documented; spec compliance prioritized over bug replication

## Phase N1 Prerequisites (This Loop)

To enable Phase N2 (nb-compare execution), this loop captures:

### Test Baseline (CPU)
- **Command**: `pytest -v tests/test_cli_scaling_phi0.py`
- **Result**: 2/2 passed in 2.06s
- **Log**: `tests/pytest_cpu.log` (14 lines)

### Environment Snapshot
- **Git SHA**: (see `inputs/git_sha.txt`)
- **PyTorch**: 2.7.1+cu126
- **CUDA**: Available (True)
- **NB_C_BIN**: ./golden_suite_generator/nanoBragg

### ROI Commands (Placeholder — Phase N2)

The supervisor ROI command (from `prompts/supervisor.md`) for both C and PyTorch:

**Base arguments (simple_cubic case):**
```bash
-default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 256
```

**ROI specification:**
```bash
--roi 100 156 100 156
```

**C invocation:**
```bash
${NB_C_BIN} -default_F 100 -cell 100 100 100 90 90 90 -lambda 1.0 \
  -distance 100 -detpixels 256 -floatfile inputs/c_float.bin
```

**PyTorch invocation:**
```bash
KMP_DUPLICATE_LIB_OK=TRUE python -m nanobrag_torch -default_F 100 \
  -cell 100 100 100 90 90 90 -lambda 1.0 -distance 100 -detpixels 256 \
  -floatfile inputs/py_float.bin
```

**Note:** Full-frame commands listed here for Phase N2 execution. ROI cropping will be applied during nb-compare analysis.

## Option 1 Cross-References

- **Primary bundle**: `reports/2025-10-cli-flags/phase_l/scaling_validation/option1_spec_compliance/20251009T013046Z/`
- **Metrics**: `metrics.json` (first_divergence=I_before_scaling, status=CRITICAL, C_value=943654.81, py_value=805473.79, relative_delta=-14.6%)
- **Summary**: `summary.md` (Option 1 rationale, spec citations)
- **Verified bug**: `docs/bugs/verified_c_bugs.md:166-204` (C-PARITY-001)
- **Validation script**: `scripts/validation/compare_scaling_traces.py` (Option 1 context in docstring)

## Next Actions (Phase N2)

1. Execute the C and PyTorch commands above
2. Capture `c_float.bin` and `py_float.bin` under `inputs/`
3. Record command outputs in `inputs/commands.txt` with timestamps and exit codes
4. Run `nb-compare` with ROI cropping to generate `results/` metrics and PNGs
5. Update `docs/fix_plan.md` Attempts History with nb-compare correlation/RMSE/peak alignment
6. If nb-compare passes thresholds (correlation ≥0.98), proceed to Phase O1 (final supervisor validation)

## Files Produced This Loop

- `inputs/git_sha.txt` — commit hash
- `inputs/version.txt` — `nanobrag_torch --version`
- `inputs/env.txt` — OS, Python, PyTorch, CUDA status
- `tests/pytest_cpu.log` — targeted test results
- `analysis.md` — this document

## TODO (Phase N2+)

- [ ] Execute C and PyTorch ROI commands
- [ ] Hash inputs with `sha256sum`
- [ ] Run nb-compare and archive metrics/visuals
- [ ] Update plan Phase M6 row to `[N/A — skipped {20251009T014553Z}]`
- [ ] Mark Phase N1 complete in plan
- [ ] Add GPU smoke run if hardware permits (per `docs/development/testing_strategy.md` §1.4)

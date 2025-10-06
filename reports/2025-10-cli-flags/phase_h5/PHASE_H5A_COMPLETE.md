# Phase H5a: EVIDENCE COMPLETE - NO IMPLEMENTATION CHANGES NEEDED

**Date:** 2025-10-06
**Status:** ✅ COMPLETE (evidence-only)
**Outcome:** PyTorch implementation is already correct

## Summary

Phase H5a was an evidence-gathering task to understand C-code behavior when both `-pix0_vector_mm` override and custom detector vectors are supplied. The evidence conclusively shows that **C ignores the override** when custom vectors are present.

**Critical Finding:** PyTorch's current implementation (which skips override when custom vectors present) **already matches C behavior correctly**. No code changes are needed.

## Evidence

Ran the supervisor command twice:
1. **WITH** `-pix0_vector_mm -216.336293 215.205512 -230.200866`
2. **WITHOUT** the `-pix0_vector_mm` flag

### Results: IDENTICAL

| Quantity | WITH Override | WITHOUT Override | Difference |
|----------|--------------|------------------|------------|
| pix0_vector[0] (m) | -0.216475836204836 | -0.216475836204836 | 0.0 |
| pix0_vector[1] (m) | 0.216343050492215 | 0.216343050492215 | 0.0 |
| pix0_vector[2] (m) | -0.230192414300537 | -0.230192414300537 | 0.0 |
| Fbeam (m) | 0.217889 | 0.217889 | 0.0 |
| Sbeam (m) | 0.215043 | 0.215043 | 0.0 |

The **only difference** in 267 lines of output was the filename (`img.bin` vs `img_no_override.bin`).

## Implications

1. **C-code precedence:** When custom detector vectors are present, C computes pix0 from Xbeam/Ybeam and ignores `-pix0_vector_mm`

2. **PyTorch status:** Current implementation (Phase H3b2, commit d6f158c) correctly skips override when custom vectors are present - **matches C exactly**

3. **Phase H5b/H5c/H5d:** All **CANCELLED** - no implementation work needed

4. **Root cause of 1.14 mm pix0 delta:** Must be traced to a different issue (likely polarization or normalization problems identified in Phases I/J/K)

## Next Actions

**NO geometry code changes.** Proceed directly to Phase I polarization work and Phase K normalization fixes.

Optional enhancement: Add CLI warning when both `-pix0_vector_mm` and custom vectors are supplied, noting the override will be silently ignored (matches C behavior).

## Artifacts

- C trace WITH override: `reports/2025-10-cli-flags/phase_h5/c_traces/with_override.log`
- C trace WITHOUT override: `reports/2025-10-cli-flags/phase_h5/c_traces/without_override.log`
- Diff: `reports/2025-10-cli-flags/phase_h5/c_traces/diff.log`
- Full analysis: `reports/2025-10-cli-flags/phase_h5/c_precedence.md`
- This summary: `reports/2025-10-cli-flags/phase_h5/PHASE_H5A_COMPLETE.md`
- Attempt log: `docs/fix_plan.md` [CLI-FLAGS-003] Attempt #29

## References

- Plan: `plans/active/cli-noise-pix0/plan.md` Phase H5
- Supervisor directive: `input.md` (Do Now: CLI-FLAGS-003 Phase H5a)
- Prior phase: Phase H3b2 (commit d6f158c) - implemented override skip logic

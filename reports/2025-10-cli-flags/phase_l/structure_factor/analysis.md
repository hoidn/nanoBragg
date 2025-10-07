# Structure-Factor Coverage Analysis

**Date:** 2025-10-07T07:23:29.479460Z
**Task:** CLI-FLAGS-003 Phase L3a
**Goal:** Verify structure-factor source for supervisor pixel

## Target Reflection

- **Miller index:** h=-7, k=-1, l=-14
- **C reference F_cell:** 190.27
- **Source:** `reports/2025-10-cli-flags/phase_l/scaling_audit/c_trace_scaling.log:143-164`

## Data Sources Tested

See `probe.log` for detailed output from:
- `scaled.hkl` (HKL text file)
- Fdump binaries (if provided via --fdump)

## Findings

[Review probe.log output and fill in conclusions here]

### HKL File Coverage

- Grid ranges: [see log]
- Target in range: [yes/no]
- Retrieved F_cell: [value]
- Delta from C: [value]

### Fdump Coverage

[Repeat for each Fdump tested]

## Hypothesis

[Based on the coverage analysis, explain where C derives F_cell=190.27]

## Next Actions (Phase L3b)

[Recommendations for HKL/Fdump ingestion strategy]

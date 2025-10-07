# CLI HKL Ingestion Audit — Phase L3c

**Date**: 2025-10-07
**SHA**: ce51e1cb4f3b5ef43eb5fbde465dc7635df36810
**Purpose**: Audit CLI HKL tensor ingestion to verify dtype/device handling and metadata extraction

## Executive Summary

The CLI successfully parses and loads HKL data from `scaled.hkl` with:
- **Grid Shape**: (49, 57, 62) - matches expected coverage from Phase L3b
- **Dtype**: torch.float32 (CPU default per DTYPE-DEFAULT-001)
- **Device**: cpu
- **Metadata**: All 9 expected keys present (h_min/max/range, k_min/max/range, l_min/max/range)

## Key Findings

1. **HKL Data Successfully Loaded**
   - Grid dimensions (49×57×62) match Phase L3b probe results
   - h∈[-24,24], k∈[-28,28], l∈[-31,30] coverage confirmed
   - 168,546 reflections (49×57×62) available

2. **Metadata Extraction Working**
   - All required metadata keys extracted: `h_min`, `h_max`, `h_range`, `k_min`, `k_max`, `k_range`, `l_min`, `l_max`, `l_range`
   - Ranges match expected values from Fdump header

3. **Dtype/Device Handling**
   - Default float32 dtype applied (as expected per DTYPE-DEFAULT-001 plan)
   - CPU device (default, no `-device cuda` specified)
   - No silent dtype coercion detected

## Test Coverage Validation

**Selector**: `tests/test_cli_scaling.py`
- **Collection**: 2 tests collected successfully
  - `TestMOSFLMCellVectors::test_mosflm_cell_vectors`
  - `TestFlattSquareMatchesC::test_f_latt_square_matches_c`
- **Status**: pytest --collect-only passed (no import errors)

## Environment

```json
{
  "git_sha": "ce51e1cb4f3b5ef43eb5fbde465dc7635df36810",
  "python": "3.13.7",
  "torch": "2.8.0+cu128",
  "cuda_available": true
}
```

## Comparison with Phase L3b Probe

| Metric | Phase L3b Probe | CLI Audit | Match |
|--------|----------------|-----------|-------|
| Grid Shape | (49, 57, 62) | (49, 57, 62) | ✅ |
| h range | [-24, 24] (49) | [-24, 24] (49) | ✅ |
| k range | [-28, 28] (57) | [-28, 28] (57) | ✅ |
| l range | [-31, 30] (62) | [-31, 30] (62) | ✅ |
| Target (-7,-1,-14) | IN RANGE | IN RANGE | ✅ |
| F_cell for target | 190.27 | (not queried) | - |

## Discrepancy Analysis

**Question**: If CLI ingestion loads the HKL grid correctly, why does the harness report F_cell=0 for (-7,-1,-14)?

**Hypothesis**: The issue is NOT in CLI parsing/loading (which works correctly as shown), but rather:
1. **Harness attachment**: The harness script may not be attaching `hkl_data` to the Crystal instance correctly
2. **Lookup logic**: The structure factor lookup in `Crystal.get_structure_factor` may have an indexing bug
3. **Configuration handoff**: The loaded HKL data may not be passed to the Simulator/Crystal correctly

## Next Actions (Phase L3c continuation)

1. **Inspect `src/nanobrag_torch/__main__.py`**: Trace how `config["hkl_data"]` from `parse_and_validate_args` flows into Crystal/Simulator construction
2. **Review harness attachment**: Compare harness script attachment pattern with CLI→Simulator flow
3. **Add debug probe**: Inject a temporary print in `Crystal.get_structure_factor` to log lookups for hkl≈(-7,-1,-14)
4. **Test structure factor query**: Write a minimal script that:
   - Loads config via CLI path
   - Constructs Crystal with loaded HKL data
   - Directly queries `crystal.get_structure_factor(torch.tensor([-7,-1,-14]))`
   - Compares result to expected F=190.27

## Artifacts

- **Raw output**: `reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_audit_raw.txt`
- **Environment**: `reports/2025-10-cli-flags/phase_l/structure_factor/cli_hkl_env.json`
- **Test collection**: `reports/2025-10-cli-flags/phase_l/structure_factor/collect_cli_scaling_post_audit.log`

## Conclusion

✅ **CLI HKL ingestion is working correctly**. The audit confirms:
- Grid loaded with correct shape and metadata
- Dtype/device handling per spec
- Target reflection (-7,-1,-14) is IN RANGE of loaded grid

❌ **Root cause of F_cell=0 discrepancy is downstream** from CLI parsing, likely in:
- Harness/Simulator construction
- Crystal initialization with HKL data
- Structure factor lookup logic

Phase L3c evidence gathering complete. Ready to proceed with code inspection and targeted debugging per next actions above.

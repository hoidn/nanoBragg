# Phase G2 - MOSFLM Orientation Ingestion

**Date:** 2025-10-17
**Task:** Teach Crystal to ingest MOSFLM orientation from CLI `-mat` flag
**Status:** ✅ Complete

## Implementation Summary

Modified `src/nanobrag_torch/models/crystal.py` to detect and use MOSFLM A* orientation vectors when provided in `CrystalConfig`, following Core Rules 12-13.

### Changes Made

1. **Crystal.compute_cell_tensors() modification** (lines 545-603)
   - Added conditional check for `mosflm_a_star`, `mosflm_b_star`, `mosflm_c_star` in config
   - If present, convert numpy arrays to tensors with proper device/dtype
   - Use MOSFLM vectors as initial reciprocal vectors instead of computing from cell parameters
   - Maintain same Core Rule 12-13 pipeline (misset → real-from-reciprocal → reciprocal-from-real)

### Core Rules Compliance

**Core Rule 12 (Misset Pipeline):**
- MOSFLM orientation vectors are used as the "base" reciprocal vectors
- Misset rotation still applied to these vectors (lines 611-635)
- Real vectors computed from (possibly misset-rotated) reciprocal vectors

**Core Rule 13 (Metric Duality):**
- Real vectors computed from reciprocal: `a = (b* × c*) × V`
- Reciprocal vectors recomputed from real: `a* = (b × c) / V_actual`
- V_actual used (not formula volume) for perfect duality (a·a* = 1.0 within 1e-12)

### Validation

#### Unit Tests
- All 26 mapped tests pass (`test_cli_flags.py`, `test_at_geo_003.py`)
- All 35 crystal geometry tests pass
- Metric duality validated: a·a* = b·b* = c·c* = 1.000000000000

#### Integration Test
Created validation script demonstrating:
- CLI correctly parses `-mat A.mat` and stores vectors in config
- Crystal correctly ingests vectors from config
- Core Rule 12-13 pipeline produces correct metric duality
- Device/dtype neutrality maintained (tensors coerced via `.to()`)

## Test Commands

```bash
# Mapped tests from plan
env AUTHORITATIVE_CMDS_DOC=./docs/development/testing_strategy.md \
    KMP_DUPLICATE_LIB_OK=TRUE \
    pytest tests/test_cli_flags.py tests/test_at_geo_003.py -v

# Crystal geometry tests
env KMP_DUPLICATE_LIB_OK=TRUE pytest tests/ -k "crystal" -v

# Manual validation
python /tmp/test_mosflm_exact.py
```

## Metrics

- **Tests:** 26/26 passed (mapped tests), 35/35 passed (crystal tests)
- **Runtime:** 2.51s (mapped tests), 7.50s (crystal tests)
- **Metric Duality:** Perfect (1.000000000000 for all axes)
- **Code Coverage:** MOSFLM orientation path fully exercised

## Artifacts

- Implementation: `src/nanobrag_torch/models/crystal.py:545-603`
- Test cases: Existing test suite coverage via conditional logic
- Validation scripts: `/tmp/test_mosflm_exact.py`

## Next Actions

Per plan Phase G3:
1. Generate trace verification comparing PyTorch lattice vectors with C reference
2. Rerun supervisor parity command (`prompts/supervisor.md`)
3. Document correlation metrics in `phase_g/parity_after_orientation_fix/`

## Notes

- No breaking changes - backward compatible (falls back to canonical orientation when MOSFLM vectors not provided)
- Differentiability preserved (no `.item()`, `.detach()`, or device hard-coding)
- PyTorch device/dtype neutrality maintained (`.to()` coercion)
- Ready for Phase F3 parity rerun once this lands

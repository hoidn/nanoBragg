# Phase B Summary: CLI vs API Callchain Analysis

**Initiative:** CLI-DEFAULTS-001
**Phase:** B (Callchain & State Capture)
**Timestamp:** 2025-10-10T16:09:02Z
**Status:** ✅ Complete (static analysis)

## Analysis Question

**Why does the CLI default_F run emit zeros while the direct API run yields intensities?**

## Key Findings

### ✅ Configuration Flow is Architecturally Sound

Both CLI and API paths correctly propagate `default_F=100` through all layers:

**CLI Path:**
```
-default_F 100 (argparse)
  → config['default_F'] = 100 (__main__.py:444)
  → CrystalConfig(default_F=100) (__main__.py:864)
  → Crystal.config.default_F = 100 (crystal.py:61)
  → get_structure_factor() returns 100.0 (crystal.py:227)
```

**API Path:**
```
CrystalConfig(default_F=100.0) (debug_default_f.py:26)
  → Crystal.config.default_F = 100 (crystal.py:61)
  → get_structure_factor() returns 100.0 (crystal.py:227)
```

### 🔴 Most Likely Root Cause (80% confidence)

**HKL Data Assignment Timing Issue**

**Location:** `src/nanobrag_torch/__main__.py:1089-1098`

The CLI path performs HKL data assignment **after** Crystal instantiation:

```python
# Line 1087: Crystal created
crystal = Crystal(crystal_config, beam_config=beam_config)

# Lines 1090-1098: HKL data conditionally assigned
if 'hkl_data' in config and config['hkl_data'] is not None:
    hkl_array, hkl_metadata = config['hkl_data']
    if hkl_array is not None:
        crystal.hkl_data = hkl_array.clone().detach().to(device=device, dtype=dtype)
        crystal.hkl_metadata = hkl_metadata
```

**Hypothesis:** The conditional `if 'hkl_data' in config and config['hkl_data'] is not None:` may be **incorrectly evaluating to True** even when no `-hkl` file is provided, causing `crystal.hkl_data` to be set to an empty/zero tensor instead of remaining `None`.

**Evidence from Phase A:**
- CLI produces all zeros despite `default_F=100` being visible in `-show_config` output
- API works correctly by never touching `hkl_data` (leaves it as `None`)

### Alternative Hypotheses (Lower Confidence)

#### Hypothesis 2: Device/Dtype Mismatch (15% confidence)
**Location:** `crystal.py:227`

```python
return torch.full_like(h, float(self.config.default_F), device=self.device, dtype=self.dtype)
```

If `h` is on a different device than `self.device`, this could fail silently or return zeros.

#### Hypothesis 3: Compiled Physics Function Boundary (5% confidence)
**Location:** `simulator.py:688`

The structure factor callable may not be correctly captured across the `torch.compile` boundary in the CLI path.

## First Tap to Confirm Divergence

**Tap 4: HKL Data Post-Assignment Check**

Add immediately after line 1098 in `__main__.py`:

```python
print(f"DEBUG_TAP4: crystal.hkl_data is None = {crystal.hkl_data is None}")
print(f"DEBUG_TAP4: crystal.config.default_F = {crystal.config.default_F}")
if crystal.hkl_data is not None:
    print(f"DEBUG_TAP4: ❌ UNEXPECTED - hkl_data should be None for default_F-only run!")
    print(f"DEBUG_TAP4: hkl_data type = {type(crystal.hkl_data)}, shape = {crystal.hkl_data.shape if hasattr(crystal.hkl_data, 'shape') else 'N/A'}")
```

**Expected CLI output (if hypothesis is correct):**
```
DEBUG_TAP4: crystal.hkl_data is None = False  ← ❌ DIVERGENCE!
DEBUG_TAP4: crystal.config.default_F = 100.0
DEBUG_TAP4: ❌ UNEXPECTED - hkl_data should be None for default_F-only run!
DEBUG_TAP4: hkl_data type = <class 'torch.Tensor'>, shape = torch.Size([...])
```

**Expected API output:**
```
DEBUG_TAP4: crystal.hkl_data is None = True  ← ✅ CORRECT
DEBUG_TAP4: crystal.config.default_F = 100.0
```

## Recommended Next Steps (Phase C)

### C1: Instrument and Confirm Divergence

1. Add Tap 4 to both CLI and API paths
2. Run minimal test case
3. If Tap 4 shows `hkl_data is not None` in CLI:
   - **Root cause confirmed**: HKL assignment logic bug
   - **Fix:** Modify condition at line 1090 to ensure it only executes when HKL file was actually loaded

### C2: Root Cause Analysis

If Tap 4 confirms divergence, inspect:

- `parse_and_validate_args()` lines 442-448: How is `config['hkl_data']` set when no `-hkl` flag?
- Possible bug: `config['hkl_data'] = None` vs. not setting the key at all
- Python `if 'key' in dict and dict['key'] is not None:` will be True if key exists with value None!

**Suspected fix:**
```python
# Current (BUGGY):
if 'hkl_data' in config and config['hkl_data'] is not None:

# Should be:
if config.get('hkl_data') is not None:
```

### C3: Validation Plan

After fix:
1. Run `pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F`
2. Verify non-zero output in floatfile
3. Compare CLI vs API outputs with `nb-compare` tool
4. Run full AT-CLI suite to ensure no regressions

## Deliverables Produced

All Phase B artifacts stored under:
`reports/2026-01-test-suite-triage/phase_d/20251010T160902Z/cli-defaults/phase_b/`

- ✅ `analysis.md` — Analysis question and scope
- ✅ `callchain/static.md` — CLI callchain (entry → sink)
- ✅ `api_callchain/static.md` — API callchain (entry → sink)
- ✅ `trace/tap_points.md` — 7 proposed numeric tap points
- ✅ `env/trace_env.json` — Environment metadata
- ✅ `summary.md` — This document

## Open Questions

1. **Why does `config['hkl_data']` exist in the config dict even when no `-hkl` flag is provided?**
   - Need to trace `parse_and_validate_args()` line 442-443

2. **Does `try_load_hkl_or_fdump()` return `(None, None)` or not set the key?**
   - If it returns `(None, None)`, the assignment logic will incorrectly trigger

3. **Is there implicit Fdump.bin loading happening?**
   - Check if `Path('Fdump.bin').exists()` is True in test environment

## Exit Criteria Status

- [x] Identified most likely divergence point (HKL assignment logic)
- [x] File:line anchors for both CLI and API paths
- [x] Proposed 7 tap points with instrumentation code
- [x] Concrete hypothesis testable in Phase C
- [x] All required artifacts delivered

**Ready for Phase C remediation planning.**

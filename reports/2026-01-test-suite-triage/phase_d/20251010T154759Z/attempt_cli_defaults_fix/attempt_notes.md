# Attempt Notes: CLI-DEFAULTS-001 Investigation

**Timestamp:** 2025-10-10T15:47:59Z
**Focus:** [CLI-DEFAULTS-001] Minimal -default_F CLI invocation
**Test:** `pytest -v tests/test_at_cli_002.py::TestAT_CLI_002::test_minimal_render_with_default_F`
**Status:** Investigation completed; root cause not identified; escalating for deeper analysis

---

## Problem Statement

The test `test_minimal_render_with_default_F` fails because running the `nanobrag_torch` CLI with `-default_F 100` (no HKL file) produces all-zero output instead of non-zero intensities.

**Failing command:**
```bash
python -m nanobrag_torch -cell 100 100 100 90 90 90 -default_F 100 \
  -detpixels 32 -pixel 0.1 -distance 100 -lambda 6.2 -N 5 \
  -floatfile /tmp/test_output.bin
```

**Expected:** Non-zero intensities in output file
**Actual:** All zeros (min=0.0, max=0.0, mean=0.0)

---

## Investigation Findings

### 1. Structure Factor Logic is Correct ✓

Reviewed `src/nanobrag_torch/models/crystal.py:210-227` - the `get_structure_factor()` method correctly implements the fallback logic:

```python
def get_structure_factor(self, h, k, l):
    """Look up or interpolate the structure factor for given h,k,l indices."""

    # If no HKL data loaded, return default_F for all reflections
    if self.hkl_data is None:
        return torch.full_like(h, float(self.config.default_F),
                              device=self.device, dtype=self.dtype)
```

**Verification:** Created `debug_default_f.py` to test this method in isolation. It correctly returns `default_F=100.0` for all input Miller indices.

### 2. Configuration is Set Correctly ✓

CLI output with `-show_config` flag confirms:
- `default_F = 100.0` ✓
- `hkl_data = None` ✓
- `fluence = 1.259320e+29` (default from C code) ✓
- `Sources: 1 sources` ✓

All configuration values are correctly parsed and passed to the model classes.

### 3. Paradox: Debug Script Works, CLI Doesn't ⚠️

**KEY FINDING:** Created a minimal debug script (`debug_default_f.py`) that directly instantiates the same classes used by the CLI:

```python
crystal_config = CrystalConfig(
    cell_a=100, cell_b=100, cell_c=100,
    cell_alpha=90, cell_beta=90, cell_gamma=90,
    N_cells=(5, 5, 5),
    default_F=100.0,  # Same as CLI
    # ... rest of config identical to CLI
)
detector = Detector(detector_config)
crystal = Crystal(crystal_config, beam_config=beam_config)
simulator = Simulator(crystal, detector, beam_config=beam_config,
                     device=torch.device('cpu'), dtype=torch.float32)
intensity = simulator.run()
```

**Debug script output:**
```
Intensity statistics:
  Shape: torch.Size([32, 32])
  Min: 0.000000e+00
  Max: 1.546525e+02
  Mean: 1.199073e+00
  Non-zero pixels: 73

✓  Got non-zero intensity
```

**CLI output with identical parameters:** All zeros

**Implications:**
- The core physics classes (`Crystal`, `Detector`, `Simulator`) work correctly
- The `Crystal.get_structure_factor()` method correctly returns `default_F`
- The issue must be in **how the CLI invokes or configures these classes differently from the debug script**

### 4. Source Generation Working ✓

CLI output shows `Sources: 1 sources`, which is correct for the default parameters (no divergence/dispersion specified).

Verified in `src/nanobrag_torch/utils/auto_selection.py:68-69` that when no divergence/dispersion params are provided, it returns `count=1, range=0.0, step=0.0`.

---

## Hypotheses Considered

### Hypothesis 1: Ewald Sphere Filtering Too Strict
- **Status:** Possible but contradicted by debug script success
- **Reasoning:** If Ewald sphere condition was rejecting all reflections, the debug script would also fail
- **Next step:** Compare Ewald sphere evaluation between CLI and debug script paths

### Hypothesis 2: Multi-Source Path Issue
- **Status:** Unlikely (only 1 source generated)
- **Reasoning:** Both CLI and debug script use 1 source, so multi-source code path shouldn't differ
- **Next step:** Verify source generation and iteration logic

### Hypothesis 3: Configuration Object Differences
- **Status:** Need to verify
- **Reasoning:** Perhaps CLI creates config objects with different defaults or device/dtype settings
- **Next step:** Add instrumentation to compare actual config objects used by CLI vs debug script

### Hypothesis 4: Simulator Pipeline Differences
- **Status:** Most likely culprit
- **Reasoning:** Both use same classes but different invocation paths; issue must be in:
  - How `simulator.run()` is called
  - Pre-processing or post-processing in CLI path
  - Device/dtype handling differences
- **Next step:** Instrument `Simulator.run()` to trace execution in both paths

---

## Blocking Issues

1. **Root cause not identified despite verifying:**
   - Structure factor logic ✓
   - Configuration parsing ✓
   - Source generation ✓
   - Debug script works with same classes ✓

2. **Time spent:** Multiple investigation cycles without finding definitive cause

3. **Need:** Deeper instrumentation or different debugging approach

---

## Recommendations for Next Iteration

1. **Add detailed tracing to Simulator.run():**
   - Log number of reflections generated
   - Log number of reflections passing Ewald sphere condition
   - Log intermediate intensity contributions
   - Compare traces between CLI and debug script

2. **Instrument the CLI invocation path:**
   - Add logging in `__main__.py` after model creation
   - Verify device/dtype of all tensors
   - Compare actual Crystal/Detector/Simulator state with debug script

3. **Consider alternative approaches:**
   - Run debug script through exact same code path as CLI
   - Or modify CLI to use exact same invocation pattern as debug script
   - Eliminate differences one by one

4. **Review fluence/scaling logic:**
   - Verify fluence calculation is same in both paths
   - Check if any normalization or scaling differs

---

## Files Modified/Created

- `debug_default_f.py` - Minimal reproduction script (works correctly)
- No implementation changes made (root cause not found)

---

## Next Steps

Per input.md guidance: "If Blocked: Re-run the same selector and capture `float_stats.txt` (min/max/sum all zero) plus hypothesis notes in `attempt_notes.md`, then push the artifacts so we can escalate causes."

**Status:** Blocked ✗
**Escalation:** Required - need deeper analysis or different debugging approach
**Artifacts:** Documented in `reports/2026-01-test-suite-triage/phase_d/20251010T154759Z/attempt_cli_defaults_fix/`

# Numeric Tap Points for Steps Computation and Usage
**Initiative:** cli-flags-o-blocker
**Purpose:** Instrumentation plan to verify steps calculation and normalization flow
**Timestamp:** 2025-10-08

---

## Overview

This document proposes instrumentation tap points to trace the `steps` variable from computation through normalization. These taps are designed to be **minimally invasive** and can be enabled via environment variable or debug flag.

---

## Tap Point Definitions

### TAP-1: CLI Argument Capture
**Location:** `src/nanobrag_torch/__main__.py:620`
**Purpose:** Verify `phi_steps` value from command line

```python
# Line 620
config['phi_steps'] = args.phisteps if args.phisteps else 1

# PROPOSED TAP:
if os.environ.get('NB_TRACE_STEPS'):
    print(f"TAP-1[CLI_ARGS]: phisteps={args.phisteps} → config['phi_steps']={config['phi_steps']}")
```

**Expected Output (supervisor command):**
```
TAP-1[CLI_ARGS]: phisteps=10 → config['phi_steps']=10
```

---

### TAP-2: CrystalConfig Construction
**Location:** `src/nanobrag_torch/__main__.py:837`
**Purpose:** Verify `phi_steps` propagation to CrystalConfig

```python
# Line 827-847
crystal_config = CrystalConfig(
    cell_a=config['cell_params'][0],
    # ... other params ...
    phi_steps=config.get('phi_steps', 1),  # Line 837
    # ...
)

# PROPOSED TAP (after line 847):
if os.environ.get('NB_TRACE_STEPS'):
    print(f"TAP-2[CRYSTAL_CONFIG]: phi_steps={crystal_config.phi_steps}, "
          f"mosaic_domains={crystal_config.mosaic_domains}")
```

**Expected Output (supervisor command):**
```
TAP-2[CRYSTAL_CONFIG]: phi_steps=10, mosaic_domains=1
```

---

### TAP-3: Simulator Initialization
**Location:** `src/nanobrag_torch/simulator.py:~460` (in `Simulator.__init__`)
**Purpose:** Verify config values at simulator creation

```python
# Inside Simulator.__init__ (after storing crystal reference)
# PROPOSED TAP:
if os.environ.get('NB_TRACE_STEPS'):
    print(f"TAP-3[SIMULATOR_INIT]: crystal.config.phi_steps={self.crystal.config.phi_steps}, "
          f"crystal.config.mosaic_domains={self.crystal.config.mosaic_domains}")
```

**Expected Output (supervisor command):**
```
TAP-3[SIMULATOR_INIT]: crystal.config.phi_steps=10, crystal.config.mosaic_domains=1
```

---

### TAP-4: Steps Computation
**Location:** `src/nanobrag_torch/simulator.py:859-863`
**Purpose:** Trace full steps calculation with all components

```python
# Lines 859-863 (existing code)
phi_steps = self.crystal.config.phi_steps
mosaic_domains = self.crystal.config.mosaic_domains
source_norm = n_sources

steps = source_norm * phi_steps * mosaic_domains * oversample * oversample

# PROPOSED TAP (after line 863):
if os.environ.get('NB_TRACE_STEPS') or self.trace_pixel or self.printout:
    print(f"TAP-4[STEPS_CALC]: n_sources={source_norm}, phi_steps={phi_steps}, "
          f"mosaic_domains={mosaic_domains}, oversample={oversample}, "
          f"steps={steps}")
```

**Expected Output (supervisor command):**
```
TAP-4[STEPS_CALC]: n_sources=1, phi_steps=10, mosaic_domains=1, oversample=1, steps=10
```

---

### TAP-5: Normalization Application
**Location:** `src/nanobrag_torch/simulator.py:1127`
**Purpose:** Verify `/steps` division with before/after intensity values

```python
# Line 1127 (existing code)
physical_intensity = (
    normalized_intensity
    / steps
    * self.r_e_sqr
    * self.fluence
)

# PROPOSED TAP (after line 1130):
if os.environ.get('NB_TRACE_STEPS') or self.trace_pixel or self.printout:
    norm_sum = normalized_intensity.sum().item()
    phys_sum = physical_intensity.sum().item()
    print(f"TAP-5[NORMALIZE]: steps={steps}, "
          f"pre_norm_sum={norm_sum:.6e}, post_norm_sum={phys_sum:.6e}, "
          f"ratio={norm_sum/phys_sum if phys_sum > 0 else 0:.2f}")
```

**Expected Output (supervisor command):**
```
TAP-5[NORMALIZE]: steps=10, pre_norm_sum=8.207749e+09, post_norm_sum=8.207749e+08, ratio=10.00
```

**Validation:** `ratio` should equal `steps` within floating-point tolerance (<1% error).

---

### TAP-6: Final Intensity Statistics
**Location:** `src/nanobrag_torch/__main__.py:1117`
**Purpose:** Log final intensity statistics for comparison with C reference

```python
# Line 1117 (existing code)
stats = simulator.compute_statistics(intensity)
print(f"\nStatistics:")
print(f"  Max intensity: {stats['max_I']:.3e} at pixel ({stats['max_I_slow']}, {stats['max_I_fast']})")
print(f"  Mean: {stats['mean']:.3e}")
print(f"  RMS: {stats['RMS']:.3e}")
print(f"  RMSD: {stats['RMSD']:.3e}")

# PROPOSED TAP (after line 1122):
if os.environ.get('NB_TRACE_STEPS'):
    total_sum = intensity.sum().item()
    print(f"TAP-6[FINAL_STATS]: total_sum={total_sum:.6e}, "
          f"max={stats['max_I']:.6e}, mean={stats['mean']:.6e}")
```

**Expected Output (supervisor command):**
```
TAP-6[FINAL_STATS]: total_sum=8.207749e+08, max=5.874164e+07, mean=1.319216e+02
```

---

## Instrumentation Activation

### Environment Variable Method (Recommended)
```bash
# Enable all taps for a single run
NB_TRACE_STEPS=1 nanoBragg -mat A.mat -hkl scaled.hkl [args...]
```

**Advantages:**
- Non-invasive (no code changes in production paths)
- Can be enabled/disabled per-run
- Compatible with existing `-trace_pixel` and `-printout` flags

### Debug Flag Method (Alternative)
Add a new CLI flag:
```python
parser.add_argument('-trace_steps', action='store_true',
                    help='Trace steps computation and normalization flow')
```

Then check `args.trace_steps` or `self.debug_config.get('trace_steps')` in tap conditions.

---

## Validation Checklist

After running with instrumentation:

1. **TAP-1 → TAP-2 consistency:**
   - [ ] `config['phi_steps']` matches `crystal_config.phi_steps`

2. **TAP-2 → TAP-3 consistency:**
   - [ ] `crystal_config` values match `simulator.crystal.config` values

3. **TAP-4 steps calculation:**
   - [ ] `steps = n_sources × phi_steps × mosaic_domains × oversample²`
   - [ ] For supervisor command: `steps = 1 × 10 × 1 × 1 × 1 = 10`

4. **TAP-5 normalization:**
   - [ ] `ratio = pre_norm_sum / post_norm_sum`
   - [ ] `ratio ≈ steps` (within 1% tolerance)

5. **TAP-6 final statistics:**
   - [ ] `total_sum` matches sum of returned `intensity` tensor
   - [ ] Matches C reference within C-PARITY-001 tolerance (±15% expected due to C bug)

---

## Example Instrumented Output

**Command:**
```bash
NB_TRACE_STEPS=1 nanoBragg -mat A.mat -hkl scaled.hkl -lambda 0.9768 \
  -Na 36 -Nb 47 -Nc 29 -distance 231.27466 -pixel 0.172 \
  -detpixels_x 2463 -detpixels_y 2527 -phi 0 -osc 0.1 -phisteps 10 \
  -mosaic_dom 1 -oversample 1 -floatfile out.bin
```

**Expected Trace:**
```
TAP-1[CLI_ARGS]: phisteps=10 → config['phi_steps']=10
TAP-2[CRYSTAL_CONFIG]: phi_steps=10, mosaic_domains=1
TAP-3[SIMULATOR_INIT]: crystal.config.phi_steps=10, crystal.config.mosaic_domains=1
Running simulation...
  Detector: 2463x2527 pixels
  Crystal: 139.5x182.3x179.0 Å
  Wavelength: 0.98 Å
  Device: cpu, Dtype: torch.float32
TAP-4[STEPS_CALC]: n_sources=1, phi_steps=10, mosaic_domains=1, oversample=1, steps=10
TAP-5[NORMALIZE]: steps=10, pre_norm_sum=8.207749e+09, post_norm_sum=8.207749e+08, ratio=10.00
Statistics:
  Max intensity: 5.874e+07 at pixel (1039, 685)
  Mean: 1.319e+02
  RMS: 4.201e+04
  RMSD: 4.201e+04
TAP-6[FINAL_STATS]: total_sum=8.207749e+08, max=5.874164e+07, mean=1.319216e+02
Wrote float image to out.bin
Simulation complete.
```

**Validation:**
- ✓ `steps = 10` (matches command `-phisteps 10`)
- ✓ `ratio = 10.00` (pre_norm / post_norm = steps)
- ✓ `total_sum = 8.207749e+08` (matches supervisor bundle `py_sum=820,774,912`)
- ✓ `max = 5.874164e+07` (matches supervisor bundle max_I)

---

## Implementation Priority

**High Priority (Implement First):**
- TAP-4 (steps calculation) — Most critical for debugging
- TAP-5 (normalization application) — Verifies division happens

**Medium Priority (Add if TAP-4/5 insufficient):**
- TAP-2 (config construction) — Validates config propagation
- TAP-6 (final statistics) — Useful for sum ratio validation

**Low Priority (Add only if needed):**
- TAP-1 (CLI argument capture) — Rarely needed (args are logged in commands.txt)
- TAP-3 (simulator init) — Redundant with TAP-2 in most cases

---

## Cleanup After Analysis

Once the blocker is resolved and the analysis is complete:

1. **Keep TAP-4 and TAP-5** as optional debug output (gated by `NB_TRACE_STEPS` or `-trace_steps`)
2. **Remove temporary TAP-1/2/3/6** unless they prove useful for general debugging
3. **Document the kept taps** in `docs/debugging/debugging.md` under "Normalization Tracing"

---

## Notes

- All taps use `print()` to stderr for easy grep filtering: `2>&1 | grep "TAP-"`
- Tap output is intentionally **terse** (single line per tap) to avoid log bloat
- For detailed per-pixel tracing, use existing `-trace_pixel` flag (already implemented in simulator.py)

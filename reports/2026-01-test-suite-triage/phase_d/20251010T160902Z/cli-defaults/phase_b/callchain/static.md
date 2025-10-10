# CLI Callchain (Static Analysis)

## Entry Point
- Function: `main()`
- File:Line: `src/nanobrag_torch/__main__.py:832`
- Purpose: Main CLI entry point that parses arguments and orchestrates simulation

## Config Flow

### Flag Parsing
- Function: `parse_and_validate_args()`
- File:Line: `src/nanobrag_torch/__main__.py:393`
- Key variables:
  - `args.default_F` set to: **0.0 by default** (line 104)
  - `config['default_F']` set at line: **444**
  - `config['hkl_data']` set at line: **443** (value: None if no -hkl file)

```python
# Line 443-444 in parse_and_validate_args()
config['hkl_data'] = None
config['default_F'] = args.default_F
```

### Config Object Creation
- CrystalConfig instantiation: `__main__.py:849-869`
  - **default_F parameter passed: YES** (line 864)
  - Value: Traced from `config.get('default_F', 0.0)` -> 100.0 from CLI flag

```python
# Lines 849-869 in main()
crystal_config = CrystalConfig(
    cell_a=config['cell_params'][0],
    cell_b=config['cell_params'][1],
    cell_c=config['cell_params'][2],
    cell_alpha=config['cell_params'][3],
    cell_beta=config['cell_params'][4],
    cell_gamma=config['cell_params'][5],
    N_cells=(config.get('Na', 1), config.get('Nb', 1), config.get('Nc', 1)),
    phi_start_deg=config.get('phi_deg', 0.0),
    osc_range_deg=config.get('osc_deg', 0.0),
    phi_steps=config.get('phi_steps', 1),
    mosaic_spread_deg=config.get('mosaic_spread_deg', 0.0),
    mosaic_domains=config.get('mosaic_domains', 1),
    shape=CrystalShape[config.get('crystal_shape', 'SQUARE')],
    fudge=config.get('fudge', 1.0),
    default_F=config.get('default_F', 0.0),  # <-- LINE 864: default_F passed to CrystalConfig
    mosflm_a_star=config.get('mosflm_a_star'),
    mosflm_b_star=config.get('mosflm_b_star'),
    mosflm_c_star=config.get('mosflm_c_star')
)
```

## Model Instantiation
- Crystal: `__main__.py:1087`
  - Receives default_F: **YES** (via `crystal_config.default_F`)
  - hkl_data value: **None** (when no -hkl file provided)

```python
# Line 1087
crystal = Crystal(crystal_config, beam_config=beam_config)
```

- Detector: `__main__.py:1086`
- Simulator: `__main__.py:1113`

```python
# Lines 1086-1114
detector = Detector(detector_config)
crystal = Crystal(crystal_config, beam_config=beam_config)

# Set HKL data if available
if 'hkl_data' in config and config['hkl_data'] is not None:
    hkl_array, hkl_metadata = config['hkl_data']
    # Check if we actually got data (not just (None, None))
    if hkl_array is not None:
        if isinstance(hkl_array, torch.Tensor):
            crystal.hkl_data = hkl_array.clone().detach().to(device=device, dtype=dtype)
        else:
            crystal.hkl_data = torch.tensor(hkl_array, device=device, dtype=dtype)
        crystal.hkl_metadata = hkl_metadata

# ... later ...

simulator = Simulator(crystal, detector, beam_config=beam_config,
                    device=device, dtype=dtype, debug_config=debug_config)
```

## Core Pipeline
- simulator.run() call: `__main__.py:1136`
- Expected to delegate to: `simulator.py:700`

```python
# Line 1136
intensity = simulator.run()
```

## Output Sink
- floatfile write: `__main__.py:1147-1151`
- Data source: `intensity` tensor from simulator.run()

```python
# Lines 1147-1151
if config.get('floatfile'):
    # Write raw float image
    data = intensity.cpu().numpy().astype(np.float32)
    data.tofile(config['floatfile'])
    print(f"Wrote float image to {config['floatfile']}")
```

## Critical Path for default_F

**COMPLETE FLOW FROM CLI TO CRYSTAL:**

1. **CLI flag**: `-default_F 100`
   - Parsed at: `__main__.py:104` (argparse definition with default=0.0)
   - Stored in `args.default_F = 100`

2. **Parsed at**: `__main__.py:444`
   ```python
   config['default_F'] = args.default_F  # = 100
   ```

3. **Stored in config dict**: line 444
   - `config` is a plain Python dict
   - Value is a float: 100.0

4. **Passed to CrystalConfig**: line 864
   ```python
   crystal_config = CrystalConfig(
       # ...
       default_F=config.get('default_F', 0.0),  # = 100.0
       # ...
   )
   ```
   - CrystalConfig is defined in `config.py:96-165`
   - Field: `default_F: float = 0.0` (line 145)

5. **Received by Crystal**: `models/crystal.py:40`
   ```python
   def __init__(
       self, config: Optional[CrystalConfig] = None,
       beam_config: Optional[BeamConfig] = None,
       device=None, dtype=torch.float32
   ):
       # ...
       self.config = config if config is not None else CrystalConfig()
   ```
   - Crystal stores entire `config` object
   - `self.config.default_F` is accessible

6. **Used in get_structure_factor()**: `models/crystal.py:210-246`
   ```python
   def get_structure_factor(
       self, h: torch.Tensor, k: torch.Tensor, l: torch.Tensor
   ) -> torch.Tensor:
       # If no HKL data loaded, return default_F for all reflections
       if self.hkl_data is None:
           return torch.full_like(h, float(self.config.default_F),
                                  device=self.device, dtype=self.dtype)

       # ... rest of function for HKL lookup
   ```

## Potential Divergence Points

### 🔴 RED FLAG #1: HKL Data Loading Bypasses default_F
**File:Line:** `__main__.py:1089-1098`

**Issue:** When `-hkl` is provided, the HKL loading logic may not pass `default_F` correctly:

```python
# Line 1089-1098
if 'hkl_data' in config and config['hkl_data'] is not None:
    hkl_array, hkl_metadata = config['hkl_data']
    # Check if we actually got data (not just (None, None))
    if hkl_array is not None:
        if isinstance(hkl_array, torch.Tensor):
            crystal.hkl_data = hkl_array.clone().detach().to(device=device, dtype=dtype)
        else:
            crystal.hkl_data = torch.tensor(hkl_array, device=device, dtype=dtype)
        crystal.hkl_metadata = hkl_metadata
```

**Why This Matters:** The HKL loading in `parse_and_validate_args` (lines 445-448):
```python
if args.hkl:
    config['hkl_data'] = read_hkl_file(args.hkl, default_F=args.default_F)
elif Path('Fdump.bin').exists():
    config['hkl_data'] = try_load_hkl_or_fdump(None, fdump_path="Fdump.bin", default_F=args.default_F)
```

This sets `crystal.hkl_data` AFTER the Crystal is constructed. However, Crystal already has `self.config.default_F` set correctly!

### 🔴 RED FLAG #2: Crystal Constructor Doesn't Store default_F as Instance Variable
**File:Line:** `models/crystal.py:40-61`

**Issue:** Crystal.__init__ stores the entire config object but doesn't create a direct `self.default_F` attribute:

```python
def __init__(
    self, config: Optional[CrystalConfig] = None,
    beam_config: Optional[BeamConfig] = None,
    device=None, dtype=torch.float32
):
    # ...
    self.config = config if config is not None else CrystalConfig()
    # NO: self.default_F = config.default_F
```

This means `default_F` is only accessible via `self.config.default_F`. Let's check if `get_structure_factor` uses this correctly...

### ✅ VERIFIED: get_structure_factor Uses config.default_F
**File:Line:** `models/crystal.py:227`

```python
def get_structure_factor(
    self, h: torch.Tensor, k: torch.Tensor, l: torch.Tensor
) -> torch.Tensor:
    # If no HKL data loaded, return default_F for all reflections
    if self.hkl_data is None:
        return torch.full_like(h, float(self.config.default_F),
                               device=self.device, dtype=self.dtype)
```

**This looks correct!** When `hkl_data is None`, it returns `self.config.default_F`.

### 🔴 RED FLAG #3: HKL Metadata Check May Be Too Strict
**File:Line:** `models/crystal.py:230-231`

```python
# Get metadata
if self.hkl_metadata is None:
    return torch.full_like(h, float(self.config.default_F), device=self.device, dtype=self.dtype)
```

This is AFTER the `hkl_data is None` check. If `hkl_data` is not None but `hkl_metadata` is None, it still returns default_F. This seems correct as a fallback.

### 🟡 YELLOW FLAG #4: Physics Computation Gets Crystal Via Method Reference
**File:Line:** `simulator.py:688`

```python
# In Simulator._compute_physics_for_position()
return self._compiled_compute_physics(
    # ...
    crystal_get_structure_factor=self.crystal.get_structure_factor,
    # ...
)
```

The pure function `compute_physics_for_position` receives `crystal_get_structure_factor` as a callable parameter (line 35):

```python
def compute_physics_for_position(
    # ...
    crystal_get_structure_factor: Callable[[torch.Tensor, torch.Tensor, torch.Tensor], torch.Tensor] = None,
    # ...
):
    # ...
    F_cell = crystal_get_structure_factor(h0, k0, l0)  # Line 206
```

**This looks correct** - it's calling the bound method with the correct closure over `self.config.default_F`.

## Summary of Findings

### Expected Behavior (CLI Path)

1. `-default_F 100` is parsed → `args.default_F = 100`
2. `config['default_F'] = 100` set in parse_and_validate_args
3. `CrystalConfig(default_F=100)` created
4. `Crystal(crystal_config)` stores `self.config.default_F = 100`
5. When `simulator.run()` calls `crystal.get_structure_factor(h, k, l)`:
   - If `self.hkl_data is None`: returns `torch.full_like(h, 100.0, ...)`
   - If `self.hkl_data is not None`: performs lookup with default_F as fallback

### ⚠️ CRITICAL HYPOTHESIS

**The bug is likely NOT in the default_F flow itself, but rather:**

1. **Device/dtype mismatch:** The `torch.full_like(h, float(self.config.default_F), ...)` may not respect the device/dtype of `h` if `h` is not on the correct device yet.

2. **Empty HKL data:** Check if `hkl_data` is being set to an empty tensor instead of `None`, causing the lookup path to run but return zeros.

3. **Rotation/indexing bug:** The physics computation may be computing Miller indices that are all out of bounds, causing all lookups to return `default_F=0` from a stale config.

4. **Config object replacement:** The `crystal_config` passed to `Crystal()` at line 1087 may not be the same object that was created at line 849. Check if there's a copy or a new CrystalConfig created somewhere.

### 🔍 NEXT DEBUGGING STEPS

1. **Add trace logging to Crystal.get_structure_factor:**
   - Log when `hkl_data is None` branch is taken
   - Log the actual value of `self.config.default_F`
   - Log the shape and device of returned tensor

2. **Add trace logging to parse_and_validate_args:**
   - Log the value of `config['default_F']` before returning
   - Log whether `config['hkl_data']` is None or not

3. **Add trace logging to CrystalConfig creation:**
   - Log the `default_F` parameter value in `__main__.py:849`

4. **Compare with direct API test:**
   - The direct API test (test_at_cli_002.py?) likely creates Crystal directly with explicit config
   - CLI path has extra layers of parsing and config transformation
   - Focus on differences in how Crystal is instantiated

### 🎯 MOST LIKELY ROOT CAUSE

**The CLI path produces zeros because:**

Based on the test case at `tests/test_at_cli_002.py:36-47`, the CLI command is:
```python
cmd = [
    sys.executable, '-m', 'nanobrag_torch',
    '-cell', '100', '100', '100', '90', '90', '90',
    '-default_F', '100',
    '-detpixels', '32',
    '-pixel', '0.1',
    '-distance', '100',
    '-lambda', '6.2',
    '-N', '5',
    '-floatfile', floatfile,
    '-intfile', intfile
]
```

The test expects non-zero output (line 59):
```python
assert np.any(float_data > 0), "Float image should have non-zero values"
```

**HYPOTHESIS:** The issue is likely in one of these areas:

1. **CrystalConfig.default_F is not being propagated to Crystal instance**
   - Check if Crystal.__init__ is receiving the config correctly
   - Verify self.config.default_F is set

2. **get_structure_factor is not being called at all**
   - Verify simulator.run() actually invokes the physics computation
   - Check if there's an early-exit condition that skips computation

3. **The returned tensor from get_structure_factor has wrong shape/device**
   - torch.full_like may not work correctly if h has unexpected properties
   - Device mismatch could cause silent failures

4. **Crystal is being replaced or re-initialized after default_F is set**
   - Check for any code between line 1087 (Crystal creation) and 1136 (simulator.run)
   - Verify no property setters or resets occur

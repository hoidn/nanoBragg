# API Callchain (Static Analysis)

## Entry Point
- Script: `debug_default_f.py`
- Purpose: Direct API instantiation control (working case that produces non-zero output)

## Config Creation (Direct)

### CrystalConfig
- Created at line: **22-33**
- default_F parameter: **100.0** (explicit, line 26)
- N_cells: **(5, 5, 5)** (line 25)
- hkl_data: **Not set** (remains None - no file loaded)
- Cell parameters: 100×100×100 Å, 90°×90°×90° (lines 23-24)
- Phi parameters: phi_start=0.0, osc_range=0.0, phi_steps=1 (lines 27-29)
- Mosaic: spread=0.0, domains=1 (lines 30-31)
- Shape: CrystalShape.SQUARE (line 32)

### DetectorConfig
- Created at line: **36-41**
- Key params:
  - distance_mm=100.0 (line 37)
  - pixel_size_mm=0.1 (line 38)
  - spixels=32, fpixels=32 (lines 39-40)
  - beam_center: Auto-calculated by `DetectorConfig.__post_init__` (config.py:236-316)
    - For 32×32 detector with MOSFLM convention: (32*0.1 + 0.1)/2 = 1.65 mm
  - detector_pivot: BEAM (auto-selected via config.py:280)

### BeamConfig
- Created at line: **44-47**
- wavelength_A=6.2 (line 45)
- dmin=0.0 (line 46)
- fluence=1.25932e+29 (default from config.py:518)

## Model Instantiation

### Detector
- Created at line: **54**
- Constructor: `Detector(detector_config)`
- Device: cpu (default)
- Dtype: float32 (default)
- Basis vectors: MOSFLM convention (detector.py:121-133)
  - fdet_vec = [0.0, 0.0, 1.0] (fast along +Z)
  - sdet_vec = [0.0, -1.0, 0.0] (slow along -Y)
  - odet_vec = [1.0, 0.0, 0.0] (normal along +X)

### Crystal
- Created at line: **55**
- Constructor: `Crystal(crystal_config, beam_config=beam_config)`
- Device: cpu (default)
- Dtype: float32 (default)
- **hkl_data verified: None** (line 58 prints this)
- **default_F from config: 100.0** (line 59 prints this)
- No HKL file loading occurs

### Test: get_structure_factor method
- Direct test at lines: **63-69**
- Input: h=[1.0, 2.0, 0.0], k=[0.0, 1.0, 3.0], l=[0.0, 0.0, 1.0]
- Expected output: All values = 100.0 (default_F)
- This confirms get_structure_factor returns default_F when hkl_data is None

### Simulator
- Created at line: **73-74**
- Constructor: `Simulator(crystal, detector, beam_config=beam_config, device=torch.device('cpu'), dtype=torch.float32)`
- Device: **cpu** (explicit)
- Dtype: **float32** (explicit)

## Core Pipeline

### simulator.run() call
- Line: **77**
- Returns: intensity tensor (shape determined by detector size)

### Output Handling
- Intensity statistics printed: lines **79-84**
- Result: **Non-zero output**
  - Max: 154.7 (documented in Phase A)
  - Non-zero pixels: Multiple (confirmed by line 84 check)
- Success check: line **86-89** (reports "✓  Got non-zero intensity")

## Key Differences from CLI Path

### 1. **Direct CrystalConfig() call vs. main() orchestration**
   - API path: Direct instantiation at line 22 with all parameters in constructor
   - CLI path: Config created through parse_and_validate_args() → build_configs()
   - Impact: No intermediate validation/transformation steps

### 2. **No intermediate parse_and_validate_args() step**
   - API path: No argument parsing or validation
   - CLI path: Extensive validation in __main__.py:parse_and_validate_args()
   - Impact: Skips any CLI-specific normalization/coercion

### 3. **Explicit default_F parameter passing**
   - API path: `default_F=100.0` passed directly in CrystalConfig constructor (line 26)
   - CLI path: default_F set via `-default_F 100` flag → parsed → validated → assigned
   - **CRITICAL**: Direct assignment vs. parsed/validated assignment
   - Both end up as `config.default_F = 100.0`, but through different code paths

### 4. **No HKL file loading**
   - API path: hkl_data remains None throughout (never loaded)
   - CLI path: Could load HKL file via `-hkl` flag
   - Impact: get_structure_factor() always returns default_F (crystal.py:226-227)

### 5. **Simplified BeamConfig**
   - API path: Only wavelength_A and dmin set (lines 44-47)
   - CLI path: May set additional beam parameters (flux, exposure, source points)
   - Impact: Uses default fluence value (1.25932e+29)

### 6. **Direct device/dtype specification**
   - API path: Explicit `device=torch.device('cpu')` and `dtype=torch.float32` (line 73-74)
   - CLI path: Device/dtype selected via CLI flags or defaults
   - Impact: No device selection logic, uses explicit values

### 7. **No main() function call**
   - API path: Direct script execution (no main() function)
   - CLI path: Executes via main() function with argparse
   - Impact: Skips all CLI setup/teardown logic

## Execution Flow Summary

```
debug_default_f.py entry
  ↓
CrystalConfig(default_F=100.0, N_cells=(5,5,5), ...)
  ↓
DetectorConfig(spixels=32, fpixels=32, distance_mm=100, ...)
  ↓
BeamConfig(wavelength_A=6.2, ...)
  ↓
Detector(config) → basis vectors initialized
  ↓
Crystal(config, beam_config) → hkl_data = None, default_F = 100.0
  ↓
Simulator(crystal, detector, beam_config, device=cpu, dtype=float32)
  ↓
simulator.run() → Non-zero intensity (max=154.7)
  ↓
Success: "✓  Got non-zero intensity"
```

## Critical Observations

### Why This Works (Produces Non-Zero Output)
1. **default_F is explicitly set**: Line 26 ensures `config.default_F = 100.0`
2. **No HKL file loading**: Avoids any file I/O that could overwrite default_F
3. **Direct config passing**: Crystal constructor receives config with default_F intact
4. **get_structure_factor() returns default_F**: When hkl_data is None, returns 100.0 for all reflections
5. **Simulator processes non-zero structure factors**: Generates non-zero intensities

### Data Flow for default_F
```
Line 26: CrystalConfig(default_F=100.0)
  ↓
Line 55: Crystal.__init__(config) → self.config.default_F = 100.0
  ↓
Line 66: crystal.get_structure_factor(h,k,l)
  ↓
crystal.py:226-227: if self.hkl_data is None: return torch.full_like(h, float(self.config.default_F), ...)
  ↓
Returns: tensor([100.0, 100.0, 100.0]) for all queries
  ↓
simulator.run() uses these non-zero F values → Non-zero intensity
```

## Next Steps for CLI Debugging

### Hypothesis: CLI Path Loses default_F
Based on this working API path, the CLI bug likely occurs in one of these steps:
1. **Argument parsing**: Does argparse correctly capture `-default_F 100`?
2. **Config construction**: Does build_configs() correctly pass default_F to CrystalConfig?
3. **Config validation**: Does parse_and_validate_args() accidentally overwrite/clear default_F?
4. **Crystal instantiation**: Does the CLI path create Crystal differently?

### Recommended Investigation
1. Add trace logging to __main__.py:build_configs() to verify default_F propagation
2. Compare CrystalConfig objects from API vs. CLI paths (dump all attributes)
3. Check if any CLI-specific logic modifies config.default_F after construction
4. Verify that Crystal.__init__() receives the same config in both paths

### Key Files to Examine
- `/home/ollie/Documents/tmp/nanoBragg/src/nanobrag_torch/__main__.py` (CLI orchestration)
- Lines around argument parsing for `-default_F` flag
- Lines in build_configs() that construct CrystalConfig
- Any validation/normalization that touches default_F

# Phase 2 — Fix Implementation & Validation (Self-Contained Checklist)

**Overall Goal**: Implement the identified fix for the detector geometry correlation issue and validate that tilted configurations achieve >0.999 correlation with the C reference.

**Prerequisites**: Phase 1 complete with root cause identified and documented in `docs/findings.md`.

**Update each task's State as you go**: `[ ]` → `[P]` (In Progress) → `[D]` (Done)

---

## Section 1: Fix Design & Planning

### 1.A Document fix design — State: [ ]

**Why**: Ensure fix is well-understood before implementation.  
**How**: Create detailed technical design based on Phase 1 findings.

```markdown
# Create/update docs/fix-design.md with:
## Identified Issue
[Specific technical problem from Phase 1]

## Root Cause
[Exact code location and algorithmic difference]

## Proposed Fix
[Step-by-step description of changes needed]

## Risk Analysis
- Potential side effects
- Configurations that might be affected
- Mitigation strategies

## Validation Plan
- Specific tests to verify fix
- Expected correlation improvements
- Regression tests needed
```

### 1.B Create fix implementation branch — State: [ ]

**Why**: Isolate changes for clean testing and potential rollback.  
**How**: Create feature branch from current state.

```bash
git checkout -b fix/detector-correlation-tilted
git status  # Ensure clean working directory
```

---

## Section 2: Core Fix Implementation

### 2.A Implement detector.py fixes — State: [ ]

**Why**: Apply the specific algorithmic fix identified in Phase 1.  
**How**: Modify the Detector class based on root cause analysis.

**Example Fix A: SAMPLE Pivot Order of Operations**
```python
# In src/nanobrag_torch/models/detector.py
def _calculate_pix0_vector(self):
    """Calculate the origin of pixel (0,0) in lab coordinates."""
    
    if self.config.detector_pivot == DetectorPivot.SAMPLE:
        # FIX: Calculate pix0 using UNROTATED basis vectors
        # Step 1: Create local unrotated basis vectors
        fdet_initial = torch.tensor([0.0, 0.0, 1.0], dtype=self.dtype, device=self.device)
        sdet_initial = torch.tensor([0.0, -1.0, 0.0], dtype=self.dtype, device=self.device)
        odet_initial = torch.tensor([1.0, 0.0, 0.0], dtype=self.dtype, device=self.device)
        
        # Step 2: Calculate pix0 with unrotated vectors
        Fclose = (self.config.beam_center_f + 0.5) * self.pixel_size
        Sclose = (self.config.beam_center_s + 0.5) * self.pixel_size
        pix0_initial = (
            -Fclose * fdet_initial 
            - Sclose * sdet_initial 
            + self.distance * odet_initial
        )
        
        # Step 3: Apply same rotations as basis vectors
        rotation_matrix = self._get_full_rotation_matrix()
        self.pix0_vector = torch.matmul(rotation_matrix, pix0_initial)
```

**Example Fix B: Rotation Matrix Composition Order**
```python
# In src/nanobrag_torch/utils/geometry.py
def angles_to_rotation_matrix(rotx, roty, rotz):
    """Apply rotations in correct order: Rz @ Ry @ Rx."""
    Rx = rotation_matrix_x(rotx)
    Ry = rotation_matrix_y(roty)
    Rz = rotation_matrix_z(rotz)
    
    # FIX: Ensure correct composition order
    return Rz @ Ry @ Rx  # Not Rx @ Ry @ Rz
```

### 2.B Update configuration handling if needed — State: [ ]

**Why**: Ensure parameters are correctly interpreted.  
**How**: Fix any parameter mapping issues identified.

```python
# In src/nanobrag_torch/config.py if needed
@property
def twotheta_axis(self):
    """Get twotheta rotation axis for current convention."""
    if self.detector_convention == DetectorConvention.MOSFLM:
        # FIX: Ensure correct axis for MOSFLM
        return torch.tensor([0.0, 0.0, -1.0], dtype=self.dtype, device=self.device)
    else:  # XDS
        return torch.tensor([0.0, 1.0, 0.0], dtype=self.dtype, device=self.device)
```

### 2.C Add trace validation to implementation — State: [ ]

**Why**: Verify fix produces correct intermediate values.  
**How**: Add debug output to validate calculations.

```python
# Temporary debug code in detector.py
if os.environ.get('DEBUG_TRACE'):
    print(f"TRACE_PY:pix0_vector={self.pix0_vector[0]:.15g} {self.pix0_vector[1]:.15g} {self.pix0_vector[2]:.15g}")
    print(f"TRACE_PY:fdet_vec={self.fdet_vec[0]:.15g} {self.fdet_vec[1]:.15g} {self.fdet_vec[2]:.15g}")
```

---

## Section 3: Initial Validation

### 3.A Run quick correlation check — State: [ ]

**Why**: Verify fix improves correlation before full testing.  
**How**: Run verification script on tilted configuration.

```bash
# Quick test of tilted configuration
cd /Users/ollie/Documents/nanoBragg
KMP_DUPLICATE_LIB_OK=TRUE python scripts/verify_detector_geometry.py \
  > results/correlation_metrics/fix_initial_test.txt 2>&1

# Check improvement
grep "tilted.*correlation" results/correlation_metrics/fix_initial_test.txt
# Should show correlation > 0.95 (ideally > 0.999)
```

### 3.B Regenerate pixel traces — State: [ ]

**Why**: Confirm traces now match between C and PyTorch.  
**How**: Generate new traces and compare.

```bash
# Generate new Python trace with fix
DEBUG_TRACE=1 python scripts/debug_tilted_trace.py \
  > initiatives/detector-correlation-fix/traces/py_pixel_377_644_fixed.trace 2>&1

# Compare with C trace
diff -u traces/c_pixel_377_644.trace traces/py_pixel_377_644_fixed.trace | head -20
# Should show minimal or no differences
```

### 3.C Document initial results — State: [ ]

**Why**: Track improvement metrics.  
**How**: Update findings with fix results.

```bash
echo "## Fix Implementation Results" >> docs/findings.md
echo "Initial correlation after fix: $(grep correlation results/correlation_metrics/fix_initial_test.txt)" >> docs/findings.md
echo "Trace divergence: $(wc -l < traces/divergence_after_fix.txt) lines" >> docs/findings.md
```

---

## Section 4: Comprehensive Testing

### 4.A Run full test suite — State: [ ]

**Why**: Ensure no regression in existing functionality.  
**How**: Execute complete test battery.

```bash
# Run all detector tests
pytest tests/test_detector_geometry.py -v > results/test_detector_geometry.txt 2>&1
pytest tests/test_detector_pivots.py -v > results/test_detector_pivots.txt 2>&1

# Run golden suite validation
pytest tests/test_suite.py::TestTier1TranslationCorrectness -v > results/test_tier1.txt 2>&1

# Check for failures
grep -E "FAILED|ERROR" results/test_*.txt
```

### 4.B Test gradient flow — State: [ ]

**Why**: Ensure fix preserves differentiability.  
**How**: Run gradient check tests.

```python
# Create/run gradient test
import torch
from nanobrag_torch.models.detector import Detector
from nanobrag_torch.config import DetectorConfig

config = DetectorConfig(
    distance_mm=torch.tensor(100.0, requires_grad=True),
    detector_rotx_deg=torch.tensor(5.0, requires_grad=True),
    detector_twotheta_deg=torch.tensor(20.0, requires_grad=True),
)

detector = Detector(config)
pixel_coords = detector.get_pixel_coords(torch.tensor([[512.0, 512.0]]))

# Check gradient flow
loss = pixel_coords.sum()
loss.backward()

assert config.distance_mm.grad is not None, "Gradient flow broken!"
print(f"✅ Gradient flow preserved: distance.grad = {config.distance_mm.grad}")
```

### 4.C Run progressive rotation validation — State: [ ]

**Why**: Verify fix works for all rotation combinations.  
**How**: Test correlation across rotation parameter space.

```bash
# Run comprehensive rotation tests
python scripts/progressive_rotation_test.py --validate-fix \
  > results/correlation_metrics/progressive_validation.txt

# All configurations should achieve > 0.95 correlation
grep "correlation" results/correlation_metrics/progressive_validation.txt
```

---

## Section 5: Performance & Optimization

### 5.A Benchmark performance impact — State: [ ]

**Why**: Ensure fix doesn't significantly degrade performance.  
**How**: Time before/after comparisons.

```python
# Create benchmark script
import time
import torch
from nanobrag_torch.simulator import Simulator

# Benchmark configuration
n_iterations = 100
config = create_tilted_config()

# Time the simulation
start = time.time()
for _ in range(n_iterations):
    sim = Simulator(detector_config, crystal_config, beam_config)
    image = sim.simulate()
elapsed = time.time() - start

print(f"Average time per simulation: {elapsed/n_iterations:.3f}s")
# Should be within 5% of baseline performance
```

### 5.B Remove debug code — State: [ ]

**Why**: Clean up temporary debugging additions.  
**How**: Remove trace statements and debug flags.

```bash
# Remove debug traces
grep -r "DEBUG_TRACE\|TRACE_PY" src/ --include="*.py"
# Remove any found debug code

# Remove C debug printfs if added
grep "DEBUG:" golden_suite_generator/nanoBragg.c
# Remove temporary debug statements
```

---

## Section 6: Final Validation

### 6.A Generate final correlation report — State: [ ]

**Why**: Document achieved correlation improvements.  
**How**: Run complete verification and save results.

```bash
# Run final verification
KMP_DUPLICATE_LIB_OK=TRUE python scripts/verify_detector_geometry.py

# Save correlation metrics
cp reports/detector_verification/correlation_metrics.json \
   initiatives/detector-correlation-fix/results/correlation_metrics/final_metrics.json

# Document in findings
echo "## Final Correlation Results" >> docs/findings.md
echo "Baseline: $(jq .baseline.correlation results/correlation_metrics/final_metrics.json)" >> docs/findings.md  
echo "Tilted: $(jq .tilted.correlation results/correlation_metrics/final_metrics.json)" >> docs/findings.md
```

### 6.B Visual validation — State: [ ]

**Why**: Confirm visual agreement between PyTorch and C images.  
**How**: Generate comparison plots.

```bash
# Plots should show excellent alignment
ls -la reports/detector_verification/*.png

# Open comparison images
open reports/detector_verification/detector_geometry_comparison.png
open reports/detector_verification/parallel_c_comparison.png
```

---

## Phase 2 Acceptance Gate

Before proceeding to Phase 3, ensure:

✅ Tilted detector correlation > 0.95 (target > 0.999)  
✅ Baseline correlation maintained > 0.99  
✅ All existing tests pass  
✅ Gradient flow preserved  
✅ Performance impact < 5%  
✅ Visual inspection shows good alignment  

## Quick Command Reference

```bash
# Test fix quickly
KMP_DUPLICATE_LIB_OK=TRUE python scripts/verify_detector_geometry.py

# Run full test suite
pytest tests/test_detector_geometry.py tests/test_detector_pivots.py -v

# Generate traces for validation
DEBUG_TRACE=1 python scripts/debug_tilted_trace.py

# Check correlation metrics
jq . reports/detector_verification/correlation_metrics.json
```

---

**Next Phase**: Once fix is validated, proceed to `phase3-checklist.md` for documentation and finalization.
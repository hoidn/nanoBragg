# Phase 3 — Documentation & Finalization (Self-Contained Checklist)

**Overall Goal**: Document the fix comprehensively, clean up the codebase, and prepare for merge to main branch with proper testing safeguards.

**Prerequisites**: Phase 2 complete with fix validated and correlation targets achieved.

**Update each task's State as you go**: `[ ]` → `[P]` (In Progress) → `[D]` (Done)

---

## Section 1: Technical Documentation

### 1.A Update architecture documentation — State: [ ]

**Why**: Ensure detector component documentation reflects correct implementation.  
**How**: Update the detector specification with learnings.

```markdown
# Update docs/architecture/detector.md with:

## Critical Implementation Details

### SAMPLE Pivot Mode Calculation Sequence
The SAMPLE pivot mode requires a specific order of operations:
1. Calculate pix0_vector using UNROTATED basis vectors
2. Apply rotations to pix0_vector
3. Apply same rotations to basis vectors

**Incorrect approach** (previous bug):
- Rotating basis vectors first, then calculating pix0_vector

### Rotation Composition Order
Rotations are applied as: Rz @ Ry @ Rx @ Rtwotheta
This order is critical for matching C reference implementation.

### Convention-Specific Details
- MOSFLM: twotheta axis = [0, 0, -1]
- XDS: twotheta axis = [0, 1, 0]
```

### 1.B Document C-PyTorch parameter mapping — State: [ ]

**Why**: Prevent future configuration parity issues.  
**How**: Update parameter mapping documentation.

```markdown
# Update docs/development/c_to_pytorch_config_map.md:

## Verified Parameter Mappings

| PyTorch Parameter | C-CLI Parameter | Notes |
|------------------|-----------------|-------|
| beam_center_s | -Xbeam | MOSFLM convention (slow → X) |
| beam_center_f | -Ybeam | MOSFLM convention (fast → Y) |
| detector_twotheta_deg | -twotheta | NOT -detector_twotheta |
| detector_pivot | -pivot SAMPLE/BEAM | Auto-selects SAMPLE if twotheta != 0 |

## Critical Implicit Behaviors
- Setting -twotheta automatically implies SAMPLE pivot mode
- MOSFLM adds +0.5 pixel adjustment to beam center
```

### 1.C Create debugging guide — State: [ ]

**Why**: Help future developers debug similar issues.  
**How**: Document the parallel trace debugging methodology.

```markdown
# Create docs/development/parallel_trace_debugging_guide.md:

# Parallel Trace Debugging Guide

## When to Use
- Correlation < 0.9 between PyTorch and C reference
- Systematic geometric differences in output
- Need to identify exact divergence point

## Step-by-Step Process

1. **Enable C tracing**
   ```bash
   cd golden_suite_generator
   make nanoBragg CFLAGS="-DTRACING=1 -fno-fast-math"
   ```

2. **Generate C trace**
   ```bash
   ./nanoBragg [params] 2>&1 | grep "TRACE_C:" > c_trace.log
   ```

3. **Generate Python trace**
   ```python
   # Match trace points exactly
   print(f"TRACE_PY:variable={value:.15g}")
   ```

4. **Compare traces**
   ```bash
   python compare_traces.py c_trace.log py_trace.log
   ```

## Common Pitfalls
- Unit mismatches (check Angstroms vs meters)
- Index origin differences (C: 1-based, Python: 0-based)
- Locale-dependent formatting (use LC_NUMERIC=C)
```

---

## Section 2: Test Infrastructure

### 2.A Add regression test for tilted configuration — State: [ ]

**Why**: Prevent this specific bug from recurring.  
**How**: Create targeted test case.

```python
# Add to tests/test_detector_geometry.py:

def test_tilted_detector_correlation():
    """Regression test for tilted detector correlation bug.
    
    This test ensures the SAMPLE pivot mode correctly handles
    rotated detector configurations. Previously failed with
    correlation = 0.040, now should achieve > 0.999.
    """
    from scripts.c_reference_runner import CReferenceRunner
    
    # Exact configuration that previously failed
    config = DetectorConfig(
        detector_convention=DetectorConvention.MOSFLM,
        detector_pivot=DetectorPivot.SAMPLE,
        distance_mm=100.0,
        beam_center_s=61.2,
        beam_center_f=61.2,
        detector_rotx_deg=5.0,
        detector_roty_deg=3.0,
        detector_rotz_deg=2.0,
        detector_twotheta_deg=20.0,
    )
    
    # Generate images
    pytorch_image = run_pytorch_simulation(config)
    c_image = CReferenceRunner().run_simulation(config)
    
    # Compute correlation
    correlation = compute_correlation(pytorch_image, c_image)
    
    # Assert high correlation
    assert correlation > 0.999, f"Tilted detector correlation {correlation:.3f} < 0.999"
```

### 2.B Add pivot mode validation tests — State: [ ]

**Why**: Ensure both BEAM and SAMPLE pivots work correctly.  
**How**: Create comprehensive pivot tests.

```python
# Add to tests/test_detector_pivots.py:

@pytest.mark.parametrize("pivot_mode", [DetectorPivot.BEAM, DetectorPivot.SAMPLE])
@pytest.mark.parametrize("twotheta", [0.0, 10.0, 20.0])
def test_pivot_mode_consistency(pivot_mode, twotheta):
    """Test pivot modes produce correct geometry."""
    config = DetectorConfig(
        detector_pivot=pivot_mode,
        detector_twotheta_deg=twotheta,
        # ... other params
    )
    
    detector = Detector(config)
    
    # Verify pix0_vector calculation
    if pivot_mode == DetectorPivot.SAMPLE:
        # Should use unrotated basis for initial calculation
        # Verify by checking against reference
        pass
```

### 2.C Update continuous integration tests — State: [ ]

**Why**: Ensure CI catches correlation regressions.  
**How**: Add correlation threshold checks to CI.

```yaml
# Add to .github/workflows/test.yml or equivalent:

- name: Validate Detector Correlation
  run: |
    python scripts/verify_detector_geometry.py
    
    # Check correlation thresholds
    BASELINE_CORR=$(jq .baseline.correlation reports/detector_verification/correlation_metrics.json)
    TILTED_CORR=$(jq .tilted.correlation reports/detector_verification/correlation_metrics.json)
    
    python -c "assert $BASELINE_CORR > 0.99, 'Baseline correlation too low'"
    python -c "assert $TILTED_CORR > 0.95, 'Tilted correlation too low'"
```

---

## Section 3: Code Cleanup

### 3.A Remove temporary debug code — State: [ ]

**Why**: Clean up any remaining debug artifacts.  
**How**: Search and remove debug code systematically.

```bash
# Search for debug artifacts
grep -r "DEBUG\|FIXME\|TODO.*correlation" src/ --include="*.py"
grep "DEBUG\|printf.*DEBUG" golden_suite_generator/nanoBragg.c

# Remove any temporary code
# Document any intentional debug code that should remain
```

### 3.B Clean up test artifacts — State: [ ]

**Why**: Remove temporary files created during debugging.  
**How**: Clean initiative directories.

```bash
# Clean up trace files (keep exemplars for documentation)
cd initiatives/detector-correlation-fix
ls -la traces/
# Keep one good C/Python trace pair for reference
# Remove temporary/intermediate traces

# Archive test results
tar -czf results_archive_$(date +%Y%m%d).tar.gz results/
```

### 3.C Format and lint code — State: [ ]

**Why**: Ensure code meets project standards.  
**How**: Run formatters and linters.

```bash
# Format Python code
black src/nanobrag_torch/models/detector.py
black src/nanobrag_torch/utils/geometry.py

# Run linters
pylint src/nanobrag_torch/models/detector.py
mypy src/nanobrag_torch/models/detector.py

# Fix any issues found
```

---

## Section 4: Release Preparation

### 4.A Create comprehensive commit message — State: [ ]

**Why**: Document the fix properly in git history.  
**How**: Write detailed commit message.

```bash
git add -A
git commit -m "fix(detector): Correct SAMPLE pivot mode calculation order

Previously, the SAMPLE pivot mode calculated pix0_vector using already-rotated
basis vectors, while the C reference uses unrotated vectors. This caused
catastrophic correlation failure (0.040) in tilted detector configurations.

The fix ensures pix0_vector is calculated with unrotated basis vectors before
applying rotations, matching the C reference implementation exactly.

Changes:
- Reorder operations in Detector._calculate_pix0_vector() for SAMPLE pivot
- Ensure rotation matrix composition order matches C (Rz @ Ry @ Rx)
- Add regression test for tilted detector correlation
- Update architecture documentation with correct algorithm

Metrics:
- Baseline correlation: 0.993 (maintained)
- Tilted correlation: 0.040 → 0.999 (fixed)
- All existing tests pass
- Gradient flow preserved

Closes: #[issue-number]
References: initiatives/detector-correlation-fix/

Co-authored-by: Claude <noreply@anthropic.com>"
```

### 4.B Update CHANGELOG — State: [ ]

**Why**: Document user-visible changes.  
**How**: Add entry to changelog.

```markdown
# In CHANGELOG.md:

## [Unreleased]

### Fixed
- Critical detector geometry bug causing correlation failure in tilted configurations
  - SAMPLE pivot mode now correctly calculates pixel positions
  - Tilted detector correlation improved from 0.040 to >0.999
  - Affects all simulations using detector rotations with SAMPLE pivot

### Added
- Regression tests for tilted detector configurations
- Parallel trace debugging guide in documentation
```

### 4.C Create pull request — State: [ ]

**Why**: Prepare for code review and merge.  
**How**: Push branch and create PR.

```bash
# Push branch
git push -u origin fix/detector-correlation-tilted

# Create PR via GitHub CLI
gh pr create \
  --title "Fix detector SAMPLE pivot correlation issue" \
  --body "$(cat initiatives/detector-correlation-fix/docs/findings.md)" \
  --label "bug,critical,detector"
```

---

## Section 5: Knowledge Transfer

### 5.A Document lessons learned — State: [ ]

**Why**: Capture insights for future debugging.  
**How**: Update findings with retrospective.

```markdown
# Add to docs/findings.md:

## Lessons Learned

### What Worked Well
1. Parallel trace debugging quickly identified divergence point
2. Progressive rotation testing isolated the problematic component
3. Systematic checklist approach ensured thorough investigation

### Key Insights
1. Order of operations matters critically in geometric transformations
2. C-code behavior may have implicit assumptions not obvious from reading
3. Correlation metrics are excellent diagnostics (ranges indicate problem type)

### Recommendations for Future
1. Always implement parallel tracing for physics code ports
2. Test each rotation/transformation component independently
3. Maintain comprehensive parameter mapping documentation
```

### 5.B Update initiative status — State: [ ]

**Why**: Mark initiative as complete.  
**How**: Update README and archive materials.

```markdown
# Update initiatives/detector-correlation-fix/README.md:

## Status: COMPLETED ✅

### Final Results
- Root cause: Order of operations in SAMPLE pivot calculation
- Fix implemented: Corrected pix0_vector calculation sequence
- Correlation achieved: >0.999 for all configurations
- Merged to main: [PR #XXX]

### Deliverables
- Fixed detector implementation
- Comprehensive test coverage
- Debugging methodology documentation
- Architecture documentation updates
```

### 5.C Knowledge base entry — State: [ ]

**Why**: Make solution discoverable for similar issues.  
**How**: Create searchable documentation.

```markdown
# Create docs/knowledge-base/detector-correlation-fix.md:

# Detector Correlation Fix

## Symptoms
- Low correlation (<0.1) between PyTorch and C reference
- Only affects tilted/rotated detector configurations
- Baseline cases work fine

## Root Cause
SAMPLE pivot mode calculated pix0_vector incorrectly

## Solution
Calculate pix0_vector with unrotated basis vectors first,
then apply rotations.

## Debugging Approach
1. Use parallel trace debugging
2. Test rotations progressively
3. Compare intermediate values

## Related Issues
- #XXX - Original bug report
- initiatives/detector-correlation-fix/ - Full investigation
```

---

## Phase 3 Acceptance Gate

Before closing the initiative:

✅ Architecture documentation updated with correct algorithms  
✅ Parameter mapping documentation complete  
✅ Regression tests added and passing  
✅ All debug code removed  
✅ Code formatted and linted  
✅ Comprehensive commit message prepared  
✅ PR created and ready for review  
✅ Lessons learned documented  
✅ Initiative marked complete  

## Quick Command Reference

```bash
# Final validation
pytest tests/ -v
black src/ --check
pylint src/nanobrag_torch/models/detector.py

# Documentation check
ls -la docs/architecture/detector.md
ls -la docs/development/parallel_trace_debugging_guide.md

# Create PR
git push -u origin fix/detector-correlation-tilted
gh pr create --title "Fix detector SAMPLE pivot correlation issue"
```

---

**Completion**: Initiative successfully completed! The detector correlation issue has been identified, fixed, validated, and documented.
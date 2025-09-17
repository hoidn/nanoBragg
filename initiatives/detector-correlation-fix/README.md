# Detector Correlation Fix Initiative

**Status**: ACTIVE  
**Started**: 2025-01-09  
**Priority**: CRITICAL  
**Owner**: Engineering Team  

## Problem Statement

The PyTorch detector implementation shows catastrophic correlation failure (0.040) for tilted detector configurations compared to the C reference implementation, while achieving excellent correlation (0.993) for baseline (simple_cubic) cases. This represents a ~208 pixel displacement error that makes the tilted configuration unusable.

### Key Metrics
- **Baseline correlation**: 0.993 ✅
- **Tilted correlation**: 0.040 ❌  
- **Target correlation**: >0.999

## Root Cause Hypothesis

Based on analysis of previous debugging sessions and code review, the issue appears to be a subtle convention mismatch in how rotations are applied, rather than the previously suspected SAMPLE pivot algorithm bug (which has been fixed). Potential causes include:

1. Rotation matrix composition order differences
2. Coordinate system convention mismatches
3. Twotheta rotation axis interpretation differences
4. Rotation application sequence variations

## Initiative Structure

```
detector-correlation-fix/
├── README.md                     # This file - initiative overview
├── INVESTIGATION_PLAN.md          # Detailed test plan with priorities
├── docs/
│   ├── findings.md               # Document discoveries as we go
│   ├── test-results.md           # Test execution results
│   └── fix-design.md             # Design doc for the fix
├── scripts/
│   ├── test_rotation_matrices.py # Rotation convention tests
│   ├── test_twotheta_rotation.py # Twotheta application tests
│   ├── verify_basis_vectors.py   # Basis vector convention tests
│   └── progressive_rotation_test.py # Incremental rotation tests
├── traces/
│   ├── c_pixel_377_644.trace    # C reference traces
│   └── py_pixel_377_644.trace   # Python traces
└── results/
    ├── parameter_verification/   # Priority 1.1 results
    ├── trace_comparison/         # Priority 1.2 results
    ├── rotation_analysis/        # Priority 2 results
    └── correlation_metrics/      # Final validation results
```

## Approach

### Phase 1: Diagnosis (Days 1-2)
1. **Parameter Verification** - Ensure C code receives correct parameters
2. **Pixel Trace Comparison** - Find exact divergence point
3. **Rotation Convention Analysis** - Compare matrix construction methods
4. **Coordinate System Audit** - Verify basis vectors and transformations

### Phase 2: Fix Implementation (Days 3-4)
1. **Apply Identified Fix** - Update code based on findings
2. **Validation Testing** - Ensure correlation targets are met
3. **Regression Testing** - Verify no breakage of working cases
4. **Documentation** - Update architecture docs with learnings

## Success Criteria

### Must Have
- [ ] Tilted detector correlation > 0.95
- [ ] Baseline correlation maintained > 0.99
- [ ] All existing tests pass
- [ ] Root cause documented

### Should Have  
- [ ] Tilted detector correlation > 0.999
- [ ] Pixel displacement < 1 pixel
- [ ] Performance impact < 5%
- [ ] Comprehensive test coverage added

### Nice to Have
- [ ] Automated regression tests for all rotation combinations
- [ ] Visual debugging tools for future issues
- [ ] Performance optimizations identified

## Dependencies

- **Builds on**: `parallel-trace-validation` initiative (tools and methodology)
- **Requires**: Access to C reference implementation
- **Blocks**: Production deployment of PyTorch port

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Root cause is deeper than hypothesized | Medium | High | Escalation path defined in INVESTIGATION_PLAN.md |
| Fix breaks other configurations | Low | High | Comprehensive regression test suite |
| Performance degradation | Low | Medium | Profile before/after fix |

## Timeline

- **Day 1**: Priority 1-2 diagnostics
- **Day 2**: Priority 3-4 analysis  
- **Day 3**: Fix implementation
- **Day 4**: Validation and documentation
- **Buffer**: 2 days for unexpected complications

## Communication

- Daily updates in this README
- Test results documented in `docs/test-results.md`
- Final report in `docs/findings.md`

## Related Documentation

- [Investigation Plan](./INVESTIGATION_PLAN.md) - Detailed test procedures
- [Previous Debugging Session](../../docs/development/detector_rotation_debugging_session.md)
- [Parallel Trace Initiative](../parallel-trace-validation/docs/rd-plan.md)
- [Detector Architecture](../../docs/architecture/detector.md)

---

## Daily Log

### 2025-01-09
- Initiative created
- Investigation plan drafted
- Initial hypothesis: Convention mismatch rather than algorithmic bug
- Next: Execute Priority 1 tests
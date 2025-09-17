# Configuration Consistency Initiative

**Status**: 🟡 Planning  
**Priority**: HIGH  
**Estimated Duration**: 1 week (3.5 hours implementation + testing + documentation)  
**ROI**: 250:1 to 500:1 (prevents months of debugging)  

## Executive Summary

This initiative implements a three-layer defense system to prevent configuration mismatches between C and PyTorch implementations. Based on the postmortem of the "convention switching" issue that cost 3-6 months of debugging, this minimal intervention would have detected the problem in minutes.

## Problem Statement

The nanoBragg project suffered from a critical hidden behavior where the C implementation silently switched from MOSFLM to CUSTOM convention when certain parameters were present (e.g., `-twotheta_axis`), even with default values. This caused:

- 3-6 months of debugging effort
- Correlation dropping from 0.99 to 0.31
- Multiple failed debugging sessions
- Test infrastructure inadvertently triggering the wrong mode

**Root Cause**: No systematic way to verify both implementations were in the same configuration mode.

## Solution: Three-Layer Defense System

### Layer 1: Configuration Echo (1 hour)
- Both implementations output their active configuration
- Zero infrastructure needed
- Immediate visibility into mismatches

### Layer 2: Critical Test (30 minutes)
- Single test that explicit defaults equal implicit defaults
- Would have caught the exact nanoBragg issue
- Runs in CI on every commit

### Layer 3: Pre-Flight Warning (2 hours)
- Comparison check before running simulations
- Warns or fails on configuration mismatches
- Integrates with existing verification scripts

## Success Metrics

- [ ] Configuration mismatches detected within 5 seconds of run
- [ ] Zero false positives in mismatch detection
- [ ] Test suite catches explicit/implicit default violations
- [ ] Documentation prevents future hidden behavior issues
- [ ] ROI demonstrated through prevented debugging time

## Timeline

**Week 1**:
- Day 1: Implement Layer 1 (Configuration Echo)
- Day 2: Implement Layer 2 (Critical Test)
- Day 3: Implement Layer 3 (Pre-Flight Warning)
- Day 4: Documentation updates
- Day 5: Testing and validation

## Deliverables

1. **Code Changes**:
   - C implementation configuration echo
   - PyTorch implementation configuration echo
   - Critical test for default equivalence
   - Pre-flight warning system

2. **Documentation**:
   - Updated CLAUDE.md with configuration checking
   - Configuration mismatch troubleshooting guide
   - Test documentation for maintenance

3. **Process Improvements**:
   - CI integration for configuration tests
   - Developer guidelines for configuration changes

## Risk Assessment

**Low Risk**:
- Minimal code changes (< 50 lines total)
- Non-breaking additions (only adds output)
- Can be rolled back easily

**High Impact**:
- Prevents entire class of configuration bugs
- Saves months of potential debugging
- Improves developer confidence

## Related Documents

- [Implementation Plan](./docs/implementation_plan.md)
- [Technical Specification](./docs/technical_spec.md)
- [Testing Strategy](./docs/testing_strategy.md)
- [Documentation Updates](./docs/documentation_updates.md)
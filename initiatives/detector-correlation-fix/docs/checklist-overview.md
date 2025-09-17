# Detector Correlation Fix - Phase Checklist Overview

## Initiative Structure

This initiative uses a proven three-phase approach with self-contained checklists based on successful patterns from the parallel-trace-validation initiative.

### Checklist Design Principles

1. **State Tracking**: `[ ]` → `[P]` → `[D]` progression for visibility
2. **Context Priming**: Every task includes Why/How explanations
3. **Copy-Paste Ready**: All commands and code snippets are executable
4. **Acceptance Gates**: Clear, quantitative success criteria
5. **Self-Contained**: Each phase can be executed independently

---

## Phase Structure

### [Phase 1: Diagnosis & Root Cause Analysis](./phase1-checklist.md)
**Duration**: Days 1-2  
**Goal**: Identify exact source of 0.040 correlation failure

**Key Activities**:
- Environment setup and build verification
- Parameter verification (Priority 1.1)
- Single pixel trace comparison (Priority 1.2)
- Rotation convention analysis (Priority 2)
- Progressive rotation testing (Priority 4.1)

**Deliverables**:
- Root cause identification
- Trace divergence point documented
- Convention differences mapped
- Findings documented in `docs/findings.md`

---

### [Phase 2: Fix Implementation & Validation](./phase2-checklist.md)
**Duration**: Day 3  
**Goal**: Implement fix and achieve >0.999 correlation

**Key Activities**:
- Fix design documentation
- Core implementation in `detector.py`
- Initial validation and trace verification
- Comprehensive testing suite
- Performance benchmarking

**Deliverables**:
- Working fix implementation
- Correlation >0.999 achieved
- All tests passing
- Performance validated

---

### [Phase 3: Documentation & Finalization](./phase3-checklist.md)
**Duration**: Day 4  
**Goal**: Document, clean up, and prepare for merge

**Key Activities**:
- Architecture documentation updates
- Test infrastructure enhancement
- Code cleanup and formatting
- Release preparation
- Knowledge transfer

**Deliverables**:
- Complete documentation
- Regression tests added
- Pull request created
- Lessons learned captured

---

## Execution Guide

### Starting the Initiative

1. **Review the investigation plan**: Read `INVESTIGATION_PLAN.md` for context
2. **Set up workspace**: Create a feature branch
3. **Begin Phase 1**: Open `phase1-checklist.md` and start with Section 1

### Working Through Checklists

1. **Update task states**: Mark `[P]` when starting, `[D]` when done
2. **Document findings**: Update `docs/findings.md` as you discover issues
3. **Save outputs**: Store results in appropriate `results/` subdirectories
4. **Check acceptance gates**: Don't proceed until phase criteria are met

### Quick Start Commands

```bash
# Set up environment
export LC_NUMERIC=C KMP_DUPLICATE_LIB_OK=TRUE
cd /Users/ollie/Documents/nanoBragg

# Start Phase 1
cd initiatives/detector-correlation-fix
cat docs/phase1-checklist.md

# Run initial verification
python scripts/verify_detector_geometry.py

# Check current correlation
jq . reports/detector_verification/correlation_metrics.json
```

---

## Success Metrics

### Phase Completion Criteria

**Phase 1 Complete When**:
- [ ] Root cause identified with specific code location
- [ ] Trace divergence documented with line numbers
- [ ] All diagnostic tests completed

**Phase 2 Complete When**:
- [ ] Tilted correlation > 0.95 (target > 0.999)
- [ ] All tests passing
- [ ] Performance impact < 5%

**Phase 3 Complete When**:
- [ ] Documentation complete
- [ ] PR created and reviewed
- [ ] Knowledge captured for future

### Overall Success Criteria

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Baseline Correlation | 0.993 | >0.99 | ✅ |
| Tilted Correlation | 0.040 | >0.999 | ⏳ |
| Test Coverage | Good | Comprehensive | ⏳ |
| Documentation | Partial | Complete | ⏳ |

---

## Resources & References

### Key Scripts
- `scripts/verify_detector_geometry.py` - Primary validation tool
- `scripts/test_rotation_matrices.py` - Rotation convention testing
- `scripts/test_twotheta_rotation.py` - Twotheta verification
- `scripts/verify_basis_vectors.py` - Basis vector validation

### Documentation
- `docs/architecture/detector.md` - Detector component specification
- `docs/development/c_to_pytorch_config_map.md` - Parameter mappings
- `docs/development/detector_rotation_debugging_session.md` - Previous debugging

### Tools
- `archive/parallel_trace_debugger/` - Trace comparison utilities
- `scripts/c_reference_runner.py` - C code execution wrapper
- `golden_suite_generator/nanoBragg` - C reference implementation

---

## Contact & Support

For questions about this initiative:
1. Check existing documentation in `docs/`
2. Review previous debugging sessions
3. Consult the parallel-trace-validation initiative for methodology

This structured approach has proven successful in identifying and fixing complex physics implementation issues through systematic investigation and validation.
# Configuration Consistency Implementation Checklist

## Week 1: Immediate High-Impact Implementation

### Day 1-2: Configuration Echo Protocol
- [ ] Create `src/nanobrag_torch/validation/` directory
- [ ] Implement `config_echo.py` with `ConfigurationEcho` class
  - [ ] `generate_echo()` method for PyTorch
  - [ ] `detect_active_mode()` logic
  - [ ] `list_active_behaviors()` enumeration
  - [ ] `detect_gotchas()` warning system
- [ ] Write unit tests for echo generation
- [ ] Document echo format specification

### Day 2-3: C Output Parser
- [ ] Create `scripts/c_output_parser.py`
  - [ ] Parse "convention selected" messages
  - [ ] Extract beam center values
  - [ ] Identify trigger parameters
  - [ ] Generate C echo format
- [ ] Test parser with various C output samples
- [ ] Handle edge cases (missing output, malformed data)

### Day 3-4: Quick Validation Script
- [ ] Create `scripts/validate_config_consistency.py`
  - [ ] Command-line interface
  - [ ] Echo comparison logic
  - [ ] Clear error messages with fixes
  - [ ] Exit codes for CI/CD integration
- [ ] Add to PATH or create alias for easy access
- [ ] Test with known good/bad configurations

### Day 4-5: Documentation Updates (Critical)
- [ ] Update `CLAUDE.md` with configuration gotchas section at TOP
  - [ ] Add warning box about convention switching
  - [ ] Include quick validation command
  - [ ] Add TL;DR section
- [ ] Create `docs/debugging/DEBUGGING_DECISION_TREE.md`
  - [ ] Mermaid flowchart for debugging process
  - [ ] Start with configuration check
  - [ ] Branch based on validation results
- [ ] Update main `README.md` with configuration validation mention

### Day 5: Week 1 Testing & Review
- [ ] Run validation on all existing test cases
- [ ] Verify catches known configuration issues
- [ ] Performance benchmark (should be <1 second)
- [ ] Team review and feedback

## Week 2: Systematic Prevention

### Day 6-7: Configuration Contracts
- [ ] Create `config/contracts/` directory structure
- [ ] Write `detector_contract.yaml`
  - [ ] Define critical equivalences
  - [ ] Document parameter triggers
  - [ ] Specify behavioral expectations
- [ ] Create `beam_contract.yaml`
- [ ] Create `crystal_contract.yaml`
- [ ] Document contract schema

### Day 7-8: Contract Validator
- [ ] Implement `src/nanobrag_torch/validation/contract_validator.py`
  - [ ] YAML contract loader
  - [ ] Equivalence checker
  - [ ] Behavioral validator
  - [ ] Detailed failure reporting
- [ ] Write comprehensive unit tests
- [ ] Test against known violations

### Day 8-9: Test Infrastructure Updates
- [ ] Fix `scripts/c_reference_utils.py`
  - [ ] Don't pass `-twotheta_axis` for MOSFLM defaults
  - [ ] Add configuration echo to output
  - [ ] Log exact command being run
- [ ] Update `scripts/verify_detector_geometry.py`
  - [ ] Add configuration validation step
  - [ ] Report mode mismatches prominently
  - [ ] Suggest fixes for common issues

### Day 9-10: Contract Integration
- [ ] Add contract validation to test suite
- [ ] Create `tests/test_config_contracts.py`
  - [ ] Test all defined contracts
  - [ ] Verify equivalences hold
  - [ ] Check trigger documentation
- [ ] Document how to add new contracts
- [ ] Week 2 review and testing

## Week 3: Robust Testing & Integration

### Day 11-12: Enhanced Pre-Flight Checks
- [ ] Create `scripts/preflight_check_v2.py`
  - [ ] Configuration echo comparison
  - [ ] Contract validation
  - [ ] Unit consistency checks
  - [ ] Test infrastructure validation
  - [ ] Comprehensive reporting
- [ ] Add `--fix` option to auto-correct issues
- [ ] Create `--explain` mode for education

### Day 12-13: CI/CD Integration
- [ ] Create `.github/workflows/config_consistency.yml`
  - [ ] Run on all PRs
  - [ ] Validate configuration echoes
  - [ ] Check contract compliance
  - [ ] Run pre-flight checks
- [ ] Add badge to README
- [ ] Configure as required check for merging

### Day 13-14: Comprehensive Testing
- [ ] Create test matrix for all parameter combinations
- [ ] Verify validation catches all known issues
- [ ] Test false positive rate (<1%)
- [ ] Performance testing under load
- [ ] Edge case validation

### Day 14-15: Documentation & Training
- [ ] Create `docs/architecture/configuration_consistency.md`
  - [ ] Architecture overview
  - [ ] Component descriptions
  - [ ] Usage examples
  - [ ] Troubleshooting guide
- [ ] Update developer onboarding docs
- [ ] Create workshop materials
- [ ] Record demo video

### Day 15: Final Review & Launch
- [ ] Team review of implementation
- [ ] Address feedback
- [ ] Create rollback plan
- [ ] Announce to team
- [ ] Monitor for issues

## Post-Launch (Week 4+)

### Monitoring & Iteration
- [ ] Track validation success rate
- [ ] Collect developer feedback
- [ ] Monitor false positive rate
- [ ] Measure time saved in debugging

### Documentation Maintenance
- [ ] Update contracts as parameters evolve
- [ ] Keep CLAUDE.md warnings current
- [ ] Maintain debugging decision tree
- [ ] Document new gotchas as discovered

### Expansion Opportunities
- [ ] Add configuration diff visualization
- [ ] Implement provenance tracking (if needed)
- [ ] Create configuration migration tools
- [ ] Share pattern with other projects

## Success Criteria Validation

### Technical Metrics
- [ ] Configuration mismatches detected in <30 seconds ✓
- [ ] 100% of convention switches logged ✓
- [ ] Zero false positives in validation ✓
- [ ] <1% performance overhead ✓

### Developer Experience
- [ ] Clear, actionable error messages ✓
- [ ] One-command validation ✓
- [ ] Integrated into normal workflow ✓
- [ ] Well-documented ✓

### Business Impact
- [ ] 90% reduction in config debugging time
- [ ] Zero production config mismatches
- [ ] Improved developer onboarding
- [ ] Pattern reusable across projects

## Rollback Plan

If issues arise:
1. Disable CI/CD checks (comment out workflow)
2. Make validation optional (add `--skip-validation` flag)
3. Revert CLAUDE.md changes if too disruptive
4. Keep echo protocol for debugging only

## Dependencies

### Technical
- Python 3.8+ (for walrus operator in scripts)
- PyYAML (for contract parsing)
- pytest (for contract tests)

### Documentation
- Access to update CLAUDE.md
- Permission to create new docs
- CI/CD workflow permissions

### Team
- Code review from senior developer
- Documentation review from tech writer
- Training session scheduling

---

**Checklist Owner**: Engineering Lead  
**Daily Standup Updates**: Required during implementation  
**Blockers Escalation**: Within 4 hours
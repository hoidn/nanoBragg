feat(geometry): Phase 4 - Complete differentiable triclinic cell parameters with full validation suite

This commit completes the General Triclinic Cell Parameters initiative by adding
comprehensive gradient verification, optimization tests, and documentation.

## Key Additions

### Gradient Testing Infrastructure (`tests/test_gradients.py`)
- Individual parameter gradcheck tests for all 6 cell parameters (a, b, c, α, β, γ)
- Joint parameter gradient verification testing all parameters simultaneously
- Second-order gradient tests (gradgradcheck) for optimization stability
- End-to-end gradient flow verification through full simulation pipeline

### Property-Based Testing
- Random cell generation for exhaustive testing (50+ configurations)
- Metric duality verification (a*·a=1, a*·b=0, etc.)
- Volume consistency checks across different formulations
- Gradient stability tests across parameter space

### Optimization Recovery Tests
- Demonstrates practical gradient usage for parameter refinement
- Multiple scenarios: cubic→triclinic, large→small cells, small perturbations
- All optimization scenarios converge successfully within tolerance

### Documentation
- Tutorial notebook: `docs/tutorials/cell_parameter_refinement.ipynb`
  - Complete example of cell parameter optimization
  - Visualization of convergence and results
- Migration guide: `docs/migration_guide.md`
  - Instructions for transitioning from hard-coded to dynamic geometry
  - Common patterns and troubleshooting
- Performance analysis: `docs/performance.md`
  - Benchmarking results comparing cubic vs triclinic
  - Memory usage and optimization recommendations
- API documentation updates in Crystal and CrystalConfig classes

### Code Quality
- All code formatted with black
- Comprehensive test coverage
- Full test suite passes

## Technical Details

The gradient tests use strict numerical tolerances:
- eps=1e-6 for finite difference approximation
- atol=1e-6, rtol=1e-4 for gradient comparison
- All tests pass on CPU with float64 precision

## Impact

This completes the four-phase implementation of general triclinic cell support:
- Phase 1: Golden data generation ✅
- Phase 2: Core geometry engine ✅
- Phase 3: Simulator integration ✅
- Phase 4: Differentiability verification ✅

The nanoBragg PyTorch implementation now fully supports:
- All crystal systems (triclinic through cubic)
- Gradient-based optimization of unit cell parameters
- Full differentiability for machine learning applications

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
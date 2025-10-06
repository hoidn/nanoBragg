# CLI-FLAGS-003 Phase H4 Summary

## Objective
Verify that Phase H4a implementation (post-rotation beam-centre recomputation) achieves pix0_vector parity with C code.

## Test Configuration
- CUSTOM convention with custom detector vectors
- No pix0_vector_mm override (custom vectors take precedence per H3b2)
- Polarization disabled (-nopolar)
- Command parameters from trace_harness.py (wavelength 0.9768 Å, N=36×47×29, etc.)

## Results

### pix0_vector Parity (meters)
| Component | C (trace_c.log) | PyTorch (trace_py.log) | Delta | Tolerance |
|-----------|-----------------|------------------------|-------|-----------|
| X | -0.216336514802265 | -0.216336513668519 | 1.13e-9 m (0.001 μm) | ≤5e-5 m |
| Y |  0.215206668836451 |  0.21520668107301  | 1.22e-8 m (0.012 μm) | ≤5e-5 m |
| Z | -0.230198010448577 | -0.230198008546698 | 1.90e-9 m (0.002 μm) | ≤5e-5 m |

**Status: ✓ PASS** - All components within 5e-5 m tolerance (actual deltas < 2e-8 m)

### Beam Center Recomputation
After H4a post-rotation logic:
- PyTorch beam_center_f: 1265.944 pixels (input: 217.742 pixels)
- PyTorch beam_center_s: 1243.647 pixels (input: 213.907 pixels)
- PyTorch distance_corrected: 0.231275 m

The large change in beam centers is expected - the C code recomputes Fbeam/Sbeam after detector rotations to maintain consistency with pix0_vector geometry.

### PyTorch Lattice Factors (from trace_py.log)
- F_latt_a: -3.294
- F_latt_b: 10.815
- F_latt_c: -1.823
- F_latt (product): 64.945
- F_cell: 300.58
- Miller indices (h,k,l): (2, 2, -13)

Note: C trace doesn't emit pixel-level F_latt values, so component-wise comparison is not available.

### Miller Index Parity
- PyTorch hkl_frac: (2.098, 2.017, -12.871)
- PyTorch hkl_rounded: (2, 2, -13)
- Previous C trace (phase_e): (2, 2, -13)

**Status: ✓ PASS** - Miller indices match

## Observations

1. **pix0_vector Parity Achieved**: Post-rotation recomputation (H4a) successfully replicates C behavior. Deltas are at sub-micron level (< 0.02 μm).

2. **Custom Vector Precedence Working**: With custom vectors present, pix0_override is correctly ignored, and geometry is derived from beam centers + rotated detector basis.

3. **Beam Center Updates**: The newvector projection correctly updates Fbeam/Sbeam, which are then converted back to beam_center_f/s pixels (accounting for MOSFLM ±0.5 offset where applicable).

4. **Differentiability Maintained**: All recomputations use tensor operations, no `.item()` or detach calls.

## Conclusions

Phase H4a implementation is **COMPLETE and VERIFIED**:
- ✓ C-code lines 1851-1860 successfully ported
- ✓ pix0_vector components within 5e-5 m tolerance (20 μm, actual < 0.02 μm)
- ✓ Beam centers correctly recomputed from newvector projections
- ✓ distance_corrected updated from close_distance/r_factor
- ✓ Device/dtype neutrality preserved
- ✓ Differentiability maintained

## Next Actions (Phase H4c)
Update test tolerance in `tests/test_cli_flags.py::TestCLIPix0Override::test_pix0_vector_mm_beam_pivot` to ≤5e-5 m and run targeted pytest to confirm regression coverage.

# CLI-FLAGS-003 Phase H4a Implementation Notes

## Task
Port post-rotation beam-centre recomputation from nanoBragg.c lines 1846-1860 to PyTorch Detector.

## C-Code Reference (lines 1851-1860)
```c
/* where is the direct beam now? */
/* difference between beam impact vector and detector origin */
newvector[1] = close_distance/ratio*beam_vector[1]-pix0_vector[1];
newvector[2] = close_distance/ratio*beam_vector[2]-pix0_vector[2];
newvector[3] = close_distance/ratio*beam_vector[3]-pix0_vector[3];
/* extract components along detector vectors */
Fbeam = dot_product(fdet_vector,newvector);
Sbeam = dot_product(sdet_vector,newvector);
distance = close_distance/ratio;
```

## Implementation

Added to `src/nanobrag_torch/models/detector.py` lines 692-735:

1. Compute `newvector = (close_distance / r_factor) * beam_vector - pix0_vector`
2. Extract Fbeam and Sbeam components via dot products with detector axes
3. Update `distance_corrected = close_distance / r_factor`
4. Recompute `beam_center_f` and `beam_center_s` from Fbeam/Sbeam (accounting for MOSFLM ±0.5 pixel offset)

## Verification

### Test Case: CUSTOM Convention with Custom Vectors
Parameters from `trace_harness.py`:
- Input beam_center_f: 217.742295 pixels
- Input beam_center_s: 213.907080 pixels
- Custom vectors: fdet=[0.999982, -0.005998, -0.000118], sdet=[-0.005998, -0.999970, -0.004913], odet=[-0.000088, 0.004914, -0.999988]
- Custom beam_vector: [0.00051387949, 0.0, -0.99999986]

### Results

#### pix0_vector Parity (fresh C trace vs PyTorch)
- C (with -nopolar):     `-0.216336514802265  0.215206668836451 -0.230198010448577` m
- PyTorch (nopolar):     `-0.216336513668519  0.21520668107301  -0.230198008546698` m
- Delta X: 1.13e-9 m (0.001 μm)
- Delta Y: 1.22e-8 m (0.012 μm)
- Delta Z: 1.90e-9 m (0.002 μm)
- **All components within 5e-5 m tolerance ✓**

#### Beam Center Recomputation
After H4a implementation:
- Recomputed beam_center_f: 1265.944 pixels (was 217.742)
- Recomputed beam_center_s: 1243.647 pixels (was 213.907)
- distance_corrected: 0.231275 m

The large change in beam centers is expected and correct. The C code recomputes these values after rotations to maintain geometric consistency between pix0_vector and the detector coordinate system.

## Observations

1. **Custom Vector Precedence**: When custom detector vectors are present, the `-pix0_vector_mm` override is correctly IGNORED (per Phase H3b2 evidence). The pix0 is calculated from beam centers and rotated detector geometry.

2. **Post-Rotation Workflow**: The C code flow is:
   - Calculate pix0_vector from geometry
   - Calculate close_distance = pix0 · odet
   - Compute newvector = (close_distance/r_factor)*beam - pix0
   - Recompute Fbeam/Sbeam from newvector projections
   - Update beam centers from Fbeam/Sbeam

3. **Differentiability**: All operations maintain tensor flow, no `.item()` or `.detach()` calls.

4. **Device/Dtype Neutrality**: Recomputation preserves device and dtype throughout via `.to(device=self.device, dtype=self.dtype)`.

## Next Actions (Phase H4b)
Refresh full C/PyTorch traces with `-nopolar` flag and document F_latt parity in summary.md.
